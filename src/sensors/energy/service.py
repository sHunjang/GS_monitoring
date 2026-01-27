# ==============================================
# 전력량 센서 Service 모듈 (PyInstaller 호환)
# ==============================================
"""
전력량 센서 서비스

역할:
1. Reader를 사용하여 센서 데이터 읽기
2. 데이터 검증
3. DB에 저장

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
from datetime import datetime
from typing import Optional, Dict


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Reader import
try:
    from reader import EnergyReader
except ImportError:
    try:
        from sensors.energy.reader import EnergyReader
    except ImportError:
        from src.sensors.energy.reader import EnergyReader

# Database import
try:
    from database import insert_single_phase_data, insert_three_phase_data
except ImportError:
    try:
        from core.database import insert_single_phase_data, insert_three_phase_data
    except ImportError:
        from src.core.database import insert_single_phase_data, insert_three_phase_data


logger = logging.getLogger(__name__)


class EnergyService:
    """
    전력량 센서 서비스
    
    기능:
    1. 센서 데이터 수집 (Reader 사용)
    2. 데이터 검증
    3. DB 저장 (센서 타입에 맞는 테이블)
    
    사용 예:
        service = EnergyService(device_id="Energy_1", slave_id=11)
        success = service.collect_and_save()
    """
    
    def __init__(self, device_id: str, slave_id: int = 1):
        """
        초기화
        
        Args:
            device_id: 장치 ID (예: "Energy_1", "Energy_2")
            slave_id: Modbus Slave ID
                     1~29: 단상 센서
                     30 이상: 3상 센서
        """
        self.device_id = device_id
        self.slave_id = slave_id
        
        # Reader 생성
        self.reader = EnergyReader(device_id=device_id, slave_id=slave_id)
        
        # 센서 타입 (Reader에서 자동 감지됨)
        self.sensor_type = self.reader.sensor_type
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
    
    def collect_and_save(self) -> bool:
        """
        센서 데이터 수집 후 DB 저장
        
        프로세스:
        1. 센서 데이터 읽기
        2. 데이터 검증
        3. DB 저장 (단상/3상 구분)
        
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. 센서 데이터 읽기
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            raw_data = self.reader.read_data()
            
            if not raw_data:
                self.logger.error(f"[{self.device_id}] 센서 데이터 읽기 실패")
                return False
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 2. 데이터 검증
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if not self._validate_data(raw_data):
                self.logger.error(f"[{self.device_id}] 데이터 검증 실패")
                return False
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 3. DB 저장
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        """
        데이터 검증
        
        필수 필드가 모두 있고, 값이 유효한지 확인
        
        Args:
            data: 센서 데이터 딕셔너리
        
        Returns:
            bool: 유효하면 True
        """
        # 필수 필드 목록
        required = ['power', 'power_factor', 'energy_total']
        
        # 필수 필드 존재 여부 확인
        for field in required:
            if field not in data or data[field] is None:
                self.logger.error(
                    f"[{self.device_id}] 필수 필드 누락: {field}"
                )
                return False
        
        # 값 범위 검증 (선택사항)
        # 전력이 음수거나 비정상적으로 큰 경우 경고
        if data['power'] < 0:
            self.logger.warning(
                f"[{self.device_id}] 전력 음수: {data['power']} kW"
            )
        
        if data['power'] > 1000:  # 1MW 이상
            self.logger.warning(
                f"[{self.device_id}] 전력 비정상적으로 큼: {data['power']} kW"
            )
        
        # 역률 범위 확인 (0~1)
        if not (0 <= data['power_factor'] <= 1):
            self.logger.warning(
                f"[{self.device_id}] 역률 범위 초과: {data['power_factor']}"
            )
        
        return True
    
    def _save_data(self, data: Dict[str, float]) -> bool:
        """
        DB 저장
        
        센서 타입에 따라 적절한 테이블에 저장
        - 단상 센서: energy_data_single
        - 3상 센서: energy_data_three_phase
        
        Args:
            data: 검증된 센서 데이터
        
        Returns:
            bool: 저장 성공 시 True
        """
        # 현재 시각
        timestamp = datetime.now()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 단상 센서 (DDS238-2)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self.sensor_type == 'dds238':
            return insert_single_phase_data(
                device_id=self.device_id,
                power=data['power'],
                power_factor=data['power_factor'],
                energy_total=data['energy_total'],
                timestamp=timestamp
            )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3상 센서 (TAC4300)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif self.sensor_type == 'tac4300':
            return insert_three_phase_data(
                device_id=self.device_id,
                power=data['power'],
                power_factor=data['power_factor'],
                energy_total=data['energy_total'],
                timestamp=timestamp
            )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 알 수 없는 센서 타입
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        else:
            self.logger.error(
                f"[{self.device_id}] 알 수 없는 센서 타입: {self.sensor_type}"
            )
            return False


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 서비스 테스트
    
    실행: python src/sensors/energy/service.py
    """
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("전력량 센서 Service 테스트")
    print("=" * 70)
    
    # 단상 센서 서비스 테스트
    print("\n[단상 센서 - Slave ID 11]")
    service1 = EnergyService(device_id="Energy_TEST_1", slave_id=11)
    
    print("데이터 수집 및 저장 시도...")
    success1 = service1.collect_and_save()
    
    if success1:
        print("✓ 성공")
    else:
        print("✗ 실패")
    
    # 3상 센서 서비스 테스트
    print("\n[3상 센서 - Slave ID 31]")
    service2 = EnergyService(device_id="Energy_TEST_3", slave_id=31)
    
    print("데이터 수집 및 저장 시도...")
    success2 = service2.collect_and_save()
    
    if success2:
        print("✓ 성공")
    else:
        print("✗ 실패")
    
    print("\n" + "=" * 70)