# ==============================================
# 전력량 센서 Service 모듈
# ==============================================

import logging
from datetime import datetime
from typing import Optional, Dict

from sensors.energy.reader import EnergyReader
from core.database import insert_single_phase_data, insert_three_phase_data


class EnergyService:
    """전력량 센서 서비스"""
    
    def __init__(self, device_id: str, slave_id: int = 1):
        self.device_id = device_id
        self.slave_id = slave_id
        self.reader = EnergyReader(device_id=device_id, slave_id=slave_id)
        self.sensor_type = self.reader.sensor_type
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
    
    def collect_and_save(self) -> bool:
        """센서 데이터 수집 후 DB 저장"""
        try:
            # 1. 센서 데이터 읽기 (connect/disconnect 불필요)
            raw_data = self.reader.read_data()
            
            if not raw_data:
                self.logger.error(f"[{self.device_id}] 센서 데이터 읽기 실패")
                return False
            
            # 2. 데이터 검증
            if not self._validate_data(raw_data):
                self.logger.error(f"[{self.device_id}] 데이터 검증 실패")
                return False
            
            # 3. DB 저장
            success = self._save_data(raw_data)
            
            if success:
                self.logger.info(
                    f"[{self.device_id}] ✓ 데이터 저장: "
                    f"P={raw_data['power']:.3f}kW, "
                    f"PF={raw_data['power_factor']:.3f}, "
                    f"E={raw_data['energy_total']:.2f}kWh"
                )
            
            return success
        
        except Exception as e:
            self.logger.error(f"[{self.device_id}] 오류: {e}")
            return False
    
    def _validate_data(self, data: Dict[str, float]) -> bool:
        """데이터 검증"""
        required = ['power', 'power_factor', 'energy_total']
        
        for field in required:
            if field not in data or data[field] is None:
                return False
        
        return True
    
    def _save_data(self, data: Dict[str, float]) -> bool:
        """DB 저장"""
        timestamp = datetime.now()
        
        if self.sensor_type == 'dds238':
            return insert_single_phase_data(
                device_id=self.device_id,
                power=data['power'],
                power_factor=data['power_factor'],
                energy_total=data['energy_total'],
                timestamp=timestamp
            )
        elif self.sensor_type == 'tac4300':
            return insert_three_phase_data(
                device_id=self.device_id,
                power=data['power'],
                power_factor=data['power_factor'],
                energy_total=data['energy_total'],
                timestamp=timestamp
            )
        else:
            return False
