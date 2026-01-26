# ==============================================
# 전력량 센서 Reader 모듈 (공유 클라이언트 버전)
# ==============================================

"""
전력량 센서 데이터 읽기 (공유 Modbus 클라이언트)

ModbusManager를 사용하여 하나의 연결을 공유합니다.
"""

import logging
from typing import Dict, Optional

from pymodbus.exceptions import ModbusException

from sensors.energy.protocols import get_protocol, get_sensor_type_from_slave_id
from core.modbus_manager import ModbusManager


class EnergyReader:
    """
    전력량 센서 데이터 읽기 클래스 (공유 Modbus)
    
    사용 예:
        reader = EnergyReader(device_id="Energy_1", slave_id=11)
        data = reader.read_data()
    """
    
    def __init__(self, device_id: str, slave_id: int = 1):
        """초기화"""
        self.device_id = device_id
        self.slave_id = slave_id
        
        # 센서 타입 자동 감지
        self.sensor_type = get_sensor_type_from_slave_id(slave_id)
        
        # 프로토콜 로드
        self.protocol = get_protocol(self.sensor_type)
        
        # 공유 Modbus 클라이언트
        self.modbus_manager = ModbusManager.get_instance()
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
        
        # 로그 출력
        self.logger.debug(f"전력량 센서 Reader 초기화: {device_id}")
        self.logger.debug(f"  - 센서 타입: {self.sensor_type.upper()}")
        self.logger.debug(f"  - Slave ID: {slave_id} (0x{slave_id:02X})")
    
    def read_data(self) -> Optional[Dict[str, float]]:
        """
        센서 데이터 읽기
        
        Returns:
            dict: {
                'power': float,
                'power_factor': float,
                'energy_total': float
            }
        """
        if not self.modbus_manager.is_connected():
            self.logger.warning("Modbus 연결되지 않음")
            return None
        
        result = {}
        
        # Lock을 사용하여 순차적 접근 보장
        with self.modbus_manager.get_lock():
            # 프로토콜의 각 레지스터 읽기
            for register_name, config in self.protocol.items():
                try:
                    value = self._read_register(
                        address=config['address'],
                        count=config['count'],
                        data_type=config['type'],
                        scale=config['scale']
                    )
                    
                    if value is not None:
                        result[register_name] = value
                        self.logger.debug(
                            f"✓ {register_name} = {value} {config['unit']}"
                        )
                
                except Exception as e:
                    self.logger.error(
                        f"레지스터 읽기 실패: {register_name} "
                        f"(주소 0x{config['address']:04X})"
                    )
        
        # 단상 센서인 경우 W → kW 변환
        if len(result) > 0:
            if self.sensor_type == 'dds238' and 'power' in result:
                result['power'] = result['power'] / 1000.0
                self.logger.debug(f"  전력 W→kW 변환: {result['power']:.3f} kW")
            
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
        """Modbus 레지스터 읽기 및 변환"""
        try:
            # Modbus 읽기 (이미 Lock 내부에서 실행됨)
            result = self.modbus_manager.client.read_holding_registers(
                address=address,
                count=count,
                slave=self.slave_id
            )
            
            if result.isError():
                self.logger.error(f"Modbus 응답 에러: {result}")
                return None
            
            registers = result.registers
            
            # INT (16bit)
            if data_type == 'INT':
                raw_value = registers[0]
                if raw_value >= 0x8000:
                    raw_value -= 0x10000
            
            # LONG (32bit)
            elif data_type == 'LONG':
                raw_value = (registers[0] << 16) | registers[1]
                if raw_value >= 0x80000000:
                    raw_value -= 0x100000000
            
            else:
                return None
            
            # 스케일 적용
            return raw_value * scale
        
        except Exception as e:
            self.logger.error(f"Modbus 통신 오류: {e}")
            return None
