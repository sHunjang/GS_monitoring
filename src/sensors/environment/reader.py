# ==============================================
# 환경 센서 데이터 읽기 모듈 (PyInstaller 호환)
# ==============================================
"""
지원 센서: 온습도+조도 통합 센서
프로토콜: ASCII 기반 시리얼 통신

역할:
- 환경 센서(온도, 습도, 조도) 데이터 읽기
- ModbusManager와 포트 공유
- Lock으로 충돌 방지

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ModbusManager import
try:
    from modbus_manager import ModbusManager
except ImportError:
    try:
        from core.modbus_manager import ModbusManager
    except ImportError:
        from src.core.modbus_manager import ModbusManager


logger = logging.getLogger(__name__)


class EnvironmentReader:
    """
    환경 센서 데이터 읽기 클래스
    
    기능:
    1. 온도, 습도, 조도 측정값 읽기
    2. ModbusManager의 serial 객체 사용
    3. Lock으로 순차 접근 보장
    
    프로토콜:
    - ASCII 기반 시리얼 통신
    - STX(0x02) + 데이터 + ETX(0x03) + BCC
    
    사용 예:
        reader = EnvironmentReader(device_id="Env_1", sensor_id=0)
        data = reader.read_data()
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 프로토콜 상수
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    STX = 0x02          # Start of Text
    ETX = 0x03          # End of Text
    CMD_READ = 0x52     # 'R' - Read 명령
    CMD_X = 0x58        # 'X' - 확장 명령
    CMD_Z = 0x5A        # 'Z' - 전체 읽기
    PARAM_TEMP = 0x54   # 'T' - Temperature
    PARAM_HUMI = 0x48   # 'H' - Humidity
    PARAM_ILLU = 0x4C   # 'L' - Light (Illuminance)
    RESPONSE_LENGTH = 28  # 응답 프레임 길이
    
    def __init__(
        self,
        device_id: str,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        sensor_id: int = 0,
        timeout: float = 2.0
    ):
        """
        초기화
        
        Args:
            device_id: 장치 ID (예: "Env_1", "Env_2")
            port: 시리얼 포트 (예: "COM11", "/dev/ttyUSB0")
            baudrate: 통신 속도 (기본값: 9600)
            sensor_id: 센서 주소 (0~9)
            timeout: 타임아웃 (초)
        """
        self.device_id = device_id
        self.port = port
        self.baudrate = baudrate
        self.sensor_id = sensor_id
        self.timeout = timeout
        
        # ModbusManager 참조 (포트 공유)
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
        
        실제로는 ModbusManager가 관리하므로 확인만
        
        Returns:
            bool: 연결되어 있으면 True
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
        """
        BCC (Block Check Character) 계산
        
        모든 바이트의 XOR 연산
        
        Args:
            data: BCC를 계산할 데이터
        
        Returns:
            int: BCC 값
        """
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc
    
    def _build_request_frame(self) -> bytes:
        """
        요청 프레임 생성
        
        프레임 구조:
        STX + 센서ID + CMD_READ + CMD_X + CMD_Z + 
        PARAM_TEMP + PARAM_HUMI + PARAM_ILLU + ETX + BCC
        
        Returns:
            bytes: 요청 프레임
        """
        # 프레임 생성 (BCC 제외)
        frame = bytearray([
            self.STX,                    # 0x02
            0x30 + self.sensor_id,       # '0'~'9' (0x30~0x39)
            self.CMD_READ,               # 'R'
            self.CMD_X,                  # 'X'
            self.CMD_Z,                  # 'Z'
            self.PARAM_TEMP,             # 'T'
            self.PARAM_HUMI,             # 'H'
            self.PARAM_ILLU,             # 'L'
            self.ETX                     # 0x03
        ])
        
        # BCC 계산 및 추가
        bcc = self._calculate_bcc(frame)
        frame.append(bcc)
        
        self.logger.debug(f"[{self.device_id}] 📤 요청: {frame.hex(' ').upper()}")
        
        return bytes(frame)
    
    def _parse_response(self, response: bytes) -> Optional[Dict[str, Any]]:
        """
        응답 프레임 파싱
        
        응답 구조:
        STX + 센서ID + ... + 온도(5) + 습도(4) + 조도(5) + ... + ETX + BCC
        
        Args:
            response: 응답 데이터
        
        Returns:
            dict: 파싱된 데이터 또는 None
        """
        try:
            # 길이 확인
            if len(response) < self.RESPONSE_LENGTH:
                self.logger.error(
                    f"[{self.device_id}] ❌ 응답 길이 부족: "
                    f"{len(response)} bytes (최소 {self.RESPONSE_LENGTH})"
                )
                return None
            
            self.logger.debug(f"[{self.device_id}] 📥 응답: {response.hex(' ').upper()}")
            
            # STX/ETX 검증
            if response[0] != self.STX or response[-2] != self.ETX:
                self.logger.error(f"[{self.device_id}] ❌ 프레임 오류 (STX/ETX)")
                return None
            
            # 데이터 파싱 (인덱스 9부터 시작)
            idx = 9
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 온도 파싱 (5자리: T + 4자리 숫자)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if response[idx] != self.PARAM_TEMP:
                return None
            temp_str = response[idx + 1:idx + 6].decode('ascii')  # "10206" 형태
            temp_value = int(temp_str) * 0.001  # 10.206°C
            idx += 6
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 습도 파싱 (5자리: H + 4자리 숫자)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if response[idx] != self.PARAM_HUMI:
                return None
            humi_str = response[idx + 1:idx + 5].decode('ascii')  # "0168" 형태
            humi_value = int(humi_str) * 0.1  # 16.8%
            idx += 5
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 조도 파싱 (6자리: L + 5자리 숫자)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if response[idx] != self.PARAM_ILLU:
                return None
            illu_str = response[idx + 1:idx + 6].decode('ascii')  # "00048" 형태
            illu_value = int(illu_str)  # 48 lux
            
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
            self.logger.error(
                f"[{self.device_id}] ❌ 파싱 오류: {e}",
                exc_info=True
            )
            return None
    
    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        센서 데이터 읽기
        
        ModbusManager의 포트와 Lock 사용
        
        Returns:
            dict: 센서 데이터 또는 None
        """
        if not self.modbus_manager.is_connected():
            self.logger.warning(f"[{self.device_id}] ⚠️ Modbus 연결 안 됨")
            return None
        
        # ModbusManager의 Lock 획득 (충돌 방지)
        with self.modbus_manager.get_lock():
            try:
                # ModbusClient 내부의 serial 객체 접근
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
                
                # 응답 읽기 (최대 50바이트)
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
        """Context Manager 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 종료"""
        self.disconnect()


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 환경 센서 읽기 테스트
    
    실행: python src/sensors/environment/reader.py
    """
    import logging
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-7s | %(message)s'
    )
    
    print("=" * 70)
    print("환경 센서 Reader 테스트 (ModbusManager 포트 공유)")
    print("=" * 70)
    
    # 환경 센서 생성
    reader = EnvironmentReader(
        device_id="Env_TEST",
        port="COM11",
        sensor_id=0
    )
    
    # 연결 확인
    reader.connect()
    
    print("\n🔍 데이터 읽기 시작 (3회)...\n")
    
    try:
        for i in range(3):
            print(f"━━━━━━━━━━ 읽기 #{i+1} ━━━━━━━━━━")
            
            data = reader.read_data()
            if data:
                print(
                    f"✅ 성공: "
                    f"T={data['temperature']}°C, "
                    f"H={data['humidity']}%, "
                    f"L={data['illuminance']} lux"
                )
            else:
                print(f"❌ 실패")
            
            print()
            
            if i < 2:
                time.sleep(2)
    
    finally:
        reader.disconnect()
    
    print("=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)