# ==============================================
# 전력량 센서 Reader 모듈 (PyInstaller 호환)
# ==============================================
"""
전력량 센서 데이터 읽기 (공유 Modbus 클라이언트)

ModbusManager를 사용하여 하나의 연결을 공유합니다.

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
from typing import Dict, Optional

from pymodbus.exceptions import ModbusException


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# protocols import
try:
    from protocols import get_protocol, get_sensor_type_from_slave_id
except ImportError:
    try:
        from sensors.energy.protocols import get_protocol, get_sensor_type_from_slave_id
    except ImportError:
        from src.sensors.energy.protocols import get_protocol, get_sensor_type_from_slave_id

# ModbusManager import
try:
    from modbus_manager import ModbusManager
except ImportError:
    try:
        from core.modbus_manager import ModbusManager
    except ImportError:
        from src.core.modbus_manager import ModbusManager


logger = logging.getLogger(__name__)


class EnergyReader:
    """
    전력량 센서 데이터 읽기 클래스 (공유 Modbus)
    
    기능:
    1. ModbusManager를 통해 공유 연결 사용
    2. Slave ID로 센서 타입 자동 감지 (단상/3상)
    3. 프로토콜에 따라 레지스터 읽기
    
    사용 예:
        reader = EnergyReader(device_id="Energy_1", slave_id=11)
        data = reader.read_data()
        # {'power': 1.234, 'power_factor': 0.95, 'energy_total': 123.45}
    """
    
    def __init__(self, device_id: str, slave_id: int = 1):
        """
        초기화
        
        Args:
            device_id: 장치 ID (예: "Energy_1")
            slave_id: Modbus Slave ID
                     1~29: 단상 센서 (DDS238-2)
                     30 이상: 3상 센서 (TAC4300)
        """
        self.device_id = device_id
        self.slave_id = slave_id
        
        # 센서 타입 자동 감지
        # slave_id < 30 → 'dds238' (단상)
        # slave_id >= 30 → 'tac4300' (3상)
        self.sensor_type = get_sensor_type_from_slave_id(slave_id)
        
        # 프로토콜 로드 (레지스터 주소 매핑)
        self.protocol = get_protocol(self.sensor_type)
        
        # 공유 Modbus 클라이언트 (싱글톤)
        self.modbus_manager = ModbusManager.get_instance()
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
        
        # 초기화 로그
        self.logger.debug(f"전력량 센서 Reader 초기화: {device_id}")
        self.logger.debug(f"  - 센서 타입: {self.sensor_type.upper()}")
        self.logger.debug(f"  - Slave ID: {slave_id} (0x{slave_id:02X})")
    
    def read_data(self) -> Optional[Dict[str, float]]:
        """
        센서 데이터 읽기
        
        프로토콜에 정의된 모든 레지스터를 읽어서 반환
        
        Returns:
            dict: {
                'power': float,           # 전력 (kW)
                'power_factor': float,    # 역률 (0~1)
                'energy_total': float     # 적산전력량 (kWh)
            }
            None: 읽기 실패 시
        """
        # Modbus 연결 확인
        if not self.modbus_manager.is_connected():
            self.logger.warning("Modbus 연결되지 않음")
            return None
        
        result = {}
        
        # Lock을 사용하여 순차적 접근 보장
        # (다른 센서나 환경 센서와 충돌 방지)
        with self.modbus_manager.get_lock():
            # 프로토콜의 각 레지스터 읽기
            for register_name, config in self.protocol.items():
                try:
                    # 레지스터 읽기 및 스케일 적용
                    value = self._read_register(
                        address=config['address'],    # 레지스터 주소
                        count=config['count'],        # 읽을 개수 (1 or 2)
                        data_type=config['type'],     # INT or LONG
                        scale=config['scale']         # 스케일 계수
                    )
                    
                    if value is not None:
                        result[register_name] = value
                        self.logger.debug(
                            f"✓ {register_name} = {value} {config['unit']}"
                        )
                
                except Exception as e:
                    self.logger.error(
                        f"레지스터 읽기 실패: {register_name} "
                        f"(주소 0x{config['address']:04X}): {e}"
                    )
        
        # 읽기 성공 시
        if len(result) > 0:
            # 단상 센서인 경우 W → kW 변환
            if self.sensor_type == 'dds238' and 'power' in result:
                result['power'] = result['power'] / 1000.0
                self.logger.debug(
                    f"  전력 W→kW 변환: {result['power']:.3f} kW"
                )
            
            return result
        else:
            return None
    
    def _read_register(
        self,
        address: int,
        count: int,
        data_type: str,
        scale: float
    ) -> Optional[float]:
        """
        Modbus 레지스터 읽기 및 변환
        
        Args:
            address: 레지스터 시작 주소
            count: 읽을 레지스터 개수 (1 or 2)
            data_type: 데이터 타입 ('INT' or 'LONG')
            scale: 스케일 계수 (raw_value × scale = 실제값)
        
        Returns:
            float: 변환된 값
            None: 읽기 실패 시
        """
        try:
            # Modbus 읽기 (이미 Lock 내부에서 실행됨)
            result = self.modbus_manager.client.read_holding_registers(
                address=address,
                count=count,
                slave=self.slave_id
            )
            
            # 오류 확인
            if result.isError():
                self.logger.error(f"Modbus 응답 에러: {result}")
                return None
            
            registers = result.registers
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 데이터 타입에 따라 변환
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            # INT (16bit, signed)
            if data_type == 'INT':
                raw_value = registers[0]
                # 부호 처리 (2의 보수)
                if raw_value >= 0x8000:  # MSB가 1이면 음수
                    raw_value -= 0x10000
            
            # LONG (32bit, signed)
            elif data_type == 'LONG':
                # 상위 16비트 | 하위 16비트
                raw_value = (registers[0] << 16) | registers[1]
                # 부호 처리 (2의 보수)
                if raw_value >= 0x80000000:  # MSB가 1이면 음수
                    raw_value -= 0x100000000
            
            else:
                return None
            
            # 스케일 적용
            # 예: raw_value=1234, scale=0.001 → 1.234
            return raw_value * scale
        
        except Exception as e:
            self.logger.error(f"Modbus 통신 오류: {e}")
            return None


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 센서 읽기 테스트
    
    실행: python src/sensors/energy/reader.py
    """
    import logging
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("전력량 센서 Reader 테스트")
    print("=" * 70)
    
    # 단상 센서 테스트
    print("\n[단상 센서 - Slave ID 11]")
    reader1 = EnergyReader(device_id="Energy_1", slave_id=11)
    data1 = reader1.read_data()
    
    if data1:
        print(f"✓ 읽기 성공:")
        print(f"  전력: {data1['power']:.3f} kW")
        print(f"  역률: {data1['power_factor']:.3f}")
        print(f"  전력량: {data1['energy_total']:.2f} kWh")
    else:
        print("✗ 읽기 실패")
    
    # 3상 센서 테스트
    print("\n[3상 센서 - Slave ID 31]")
    reader2 = EnergyReader(device_id="Energy_3", slave_id=31)
    data2 = reader2.read_data()
    
    if data2:
        print(f"✓ 읽기 성공:")
        print(f"  전력: {data2['power']:.3f} kW")
        print(f"  역률: {data2['power_factor']:.3f}")
        print(f"  전력량: {data2['energy_total']:.2f} kWh")
    else:
        print("✗ 읽기 실패")
    
    print("\n" + "=" * 70)