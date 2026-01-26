# ==============================================
# 환경 센서 데이터 읽기 모듈 (온도+습도+조도)
# ==============================================
"""
지원 센서: 온습도+조도 통합 센서
프로토콜: ASCII 기반 시리얼 통신

🔧 ModbusManager와 통합 (2026-01-23):
- ModbusSerialClient가 관리하는 포트 사용
- ModbusManager의 Lock으로 충돌 방지
- 포트를 별도로 열지 않음
"""

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from core.modbus_manager import ModbusManager


logger = logging.getLogger(__name__)


class EnvironmentReader:
    """
    환경 센서 데이터 읽기 클래스
    
    🔧 핵심:
    - ModbusManager의 serial 객체 사용
    - Lock으로 순차 접근 보장
    - 포트를 별도로 열지 않음
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 프로토콜 상수
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    STX = 0x02
    ETX = 0x03
    CMD_READ = 0x52
    CMD_X = 0x58
    CMD_Z = 0x5A
    PARAM_TEMP = 0x54
    PARAM_HUMI = 0x48
    PARAM_ILLU = 0x4C
    RESPONSE_LENGTH = 28
    
    def __init__(
        self,
        device_id: str,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        sensor_id: int = 0,
        timeout: float = 2.0
    ):
        """초기화"""
        self.device_id = device_id
        self.port = port
        self.baudrate = baudrate
        self.sensor_id = sensor_id
        self.timeout = timeout
        
        # 🔧 ModbusManager 참조
        self.modbus_manager = ModbusManager.get_instance()
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
        
        # 초기화 로그
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"환경 센서 Reader 초기화: {device_id}")
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"  포트       : {port}")
        self.logger.info(f"  통신 속도  : {baudrate} bps")
        self.logger.info(f"  센서 ID    : {sensor_id} (ASCII: 0x{0x30 + sensor_id:02X})")
        self.logger.info(f"  타임아웃   : {timeout}초")
        self.logger.info(f"  🔧 ModbusManager 포트 공유")
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    def connect(self) -> bool:
        """
        연결 확인
        
        🔧 실제로는 ModbusManager가 관리하므로 확인만
        """
        if not self.modbus_manager.is_connected():
            self.logger.error(f"[{self.device_id}] ❌ Modbus 포트가 열려있지 않음")
            return False
        
        self.logger.info(
            f"[{self.device_id}] ♻️  Modbus 포트 공유 "
            f"(센서 ID: {self.sensor_id})"
        )
        return True
    
    def disconnect(self):
        """연결 해제 (실제로는 아무것도 안 함)"""
        self.logger.debug(f"[{self.device_id}] 포트 참조 해제")
    
    def _calculate_bcc(self, data: bytes) -> int:
        """BCC 계산"""
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc
    
    def _build_request_frame(self) -> bytes:
        """요청 프레임 생성"""
        frame = bytearray([
            self.STX,
            0x30 + self.sensor_id,
            self.CMD_READ,
            self.CMD_X,
            self.CMD_Z,
            self.PARAM_TEMP,
            self.PARAM_HUMI,
            self.PARAM_ILLU,
            self.ETX
        ])
        
        bcc = self._calculate_bcc(frame)
        frame.append(bcc)
        
        self.logger.debug(f"[{self.device_id}] 📤 요청: {frame.hex(' ').upper()}")
        
        return bytes(frame)
    
    def _parse_response(self, response: bytes) -> Optional[Dict[str, Any]]:
        """응답 프레임 파싱"""
        try:
            if len(response) < self.RESPONSE_LENGTH:
                self.logger.error(
                    f"[{self.device_id}] ❌ 응답 길이 부족: {len(response)} bytes"
                )
                return None
            
            self.logger.debug(f"[{self.device_id}] 📥 응답: {response.hex(' ').upper()}")
            
            # STX/ETX 검증
            if response[0] != self.STX or response[-2] != self.ETX:
                self.logger.error(f"[{self.device_id}] ❌ 프레임 오류")
                return None
            
            # 데이터 파싱
            idx = 9
            
            # 온도
            if response[idx] != self.PARAM_TEMP:
                return None
            temp_str = response[idx + 1:idx + 6].decode('ascii')
            temp_value = int(temp_str) * 0.001
            idx += 6
            
            # 습도
            if response[idx] != self.PARAM_HUMI:
                return None
            humi_str = response[idx + 1:idx + 5].decode('ascii')
            humi_value = int(humi_str) * 0.1
            idx += 5
            
            # 조도
            if response[idx] != self.PARAM_ILLU:
                return None
            illu_str = response[idx + 1:idx + 6].decode('ascii')
            illu_value = int(illu_str)
            
            self.logger.debug(
                f"[{self.device_id}] ✅ "
                f"T={temp_value:.3f}°C, "
                f"H={humi_value:.1f}%, "
                f"L={illu_value} lux"
            )
            
            return {
                'device_id': self.device_id,
                'timestamp': datetime.now().isoformat(),
                'temperature': round(temp_value, 3),
                'humidity': round(humi_value, 1),
                'illuminance': illu_value,
                'raw_response': response.hex(' ').upper()
            }
        
        except Exception as e:
            self.logger.error(f"[{self.device_id}] ❌ 파싱 오류: {e}", exc_info=True)
            return None
    
    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        센서 데이터 읽기
        
        🔧 ModbusManager의 포트와 Lock 사용
        """
        if not self.modbus_manager.is_connected():
            self.logger.warning(f"[{self.device_id}] ⚠️ Modbus 연결 안 됨")
            return None
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🔧 ModbusManager의 Lock 획득 (충돌 방지)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        with self.modbus_manager.get_lock():
            try:
                # 🔧 ModbusClient 내부의 serial 객체 접근
                serial_port = self.modbus_manager.client.socket
                
                if not serial_port or not serial_port.is_open:
                    self.logger.error(f"[{self.device_id}] ❌ 시리얼 포트 닫혀있음")
                    return None
                
                # 버퍼 초기화
                serial_port.reset_input_buffer()
                serial_port.reset_output_buffer()
                
                # 요청 전송
                request = self._build_request_frame()
                serial_port.write(request)
                
                # 센서 처리 대기
                time.sleep(0.1)
                
                # 응답 읽기
                response = serial_port.read(50)
                if not response:
                    self.logger.error(f"[{self.device_id}] ❌ 응답 없음")
                    return None
                
                # 응답 파싱
                return self._parse_response(response)
            
            except Exception as e:
                self.logger.error(
                    f"[{self.device_id}] ❌ 읽기 오류: {e}",
                    exc_info=True
                )
                return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    import logging
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-7s | %(message)s'
    )
    
    print("=" * 70)
    print("환경 센서 Reader 테스트 (ModbusManager 포트 공유)")
    print("=" * 70)
    
    # 환경 센서 생성
    reader1 = EnvironmentReader(
        device_id="Env_1",
        port="COM11",
        sensor_id=0
    )
    
    reader2 = EnvironmentReader(
        device_id="Env_2",
        port="COM11",
        sensor_id=1
    )
    
    # 연결 확인
    reader1.connect()
    reader2.connect()
    
    print("\n🔍 데이터 읽기 시작 (각 센서 3회)...\n")
    
    try:
        for i in range(3):
            print(f"━━━━━━━━━━ 읽기 #{i+1} ━━━━━━━━━━")
            
            # Sensor 1
            data1 = reader1.read_data()
            if data1:
                print(
                    f"[Env_1] ✅ "
                    f"T={data1['temperature']}°C, "
                    f"H={data1['humidity']}%, "
                    f"L={data1['illuminance']} lux"
                )
            else:
                print(f"[Env_1] ❌ 실패")
            
            # Sensor 2
            data2 = reader2.read_data()
            if data2:
                print(
                    f"[Env_2] ✅ "
                    f"T={data2['temperature']}°C, "
                    f"H={data2['humidity']}%, "
                    f"L={data2['illuminance']} lux"
                )
            else:
                print(f"[Env_2] ❌ 실패")
            
            print()
            
            if i < 2:
                time.sleep(2)
    
    finally:
        reader1.disconnect()
        reader2.disconnect()
    
    print("=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)
