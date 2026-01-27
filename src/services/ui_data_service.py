# ==============================================
# UI 데이터 서비스 (PyInstaller 호환)
# ==============================================
"""
UI에서 사용할 데이터 조회 서비스

역할:
- 데이터베이스에서 최신 데이터 조회
- 시계열 데이터 조회
- 통계 데이터 계산
- UI에서 표시할 형태로 가공

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Database import
try:
    from database import get_db_session
except ImportError:
    try:
        from core.database import get_db_session
    except ImportError:
        from src.core.database import get_db_session

# Models import
try:
    from sensors.energy.models import EnergySinglePhase, EnergyThreePhase
    from sensors.environment.models import EnvironmentData
except ImportError:
    try:
        import importlib
        
        energy_models = importlib.import_module('sensors.energy.models')
        env_models = importlib.import_module('sensors.environment.models')
        
        EnergySinglePhase = energy_models.EnergySinglePhase
        EnergyThreePhase = energy_models.EnergyThreePhase
        EnvironmentData = env_models.EnvironmentData
    except:
        class EnergySinglePhase:
            pass
        class EnergyThreePhase:
            pass
        class EnvironmentData:
            pass


logger = logging.getLogger(__name__)


class UIDataService:
    """
    UI 데이터 서비스
    
    기능:
    1. 센서 목록 조회
    2. 최신 데이터 조회
    3. 시계열 데이터 조회
    4. 통계 데이터 계산
    5. 기간별 데이터 조회
    """
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 센서 목록 조회
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_all_energy_devices(self) -> List[str]:
        """
        모든 전력 센서 목록 조회
        
        Returns:
            list: 센서 ID 목록 (예: ['Energy_1', 'Energy_2', ...])
        """
        try:
            with get_db_session() as session:
                # 단상 센서
                single_devices = (
                    session.query(EnergySinglePhase.device_id)
                    .distinct()
                    .all()
                )
                
                # 3상 센서
                three_devices = (
                    session.query(EnergyThreePhase.device_id)
                    .distinct()
                    .all()
                )
                
                # 중복 제거 및 정렬
                devices = set()
                for (device_id,) in single_devices:
                    devices.add(device_id)
                for (device_id,) in three_devices:
                    devices.add(device_id)
                
                # Energy_1, Energy_2, ... 순서로 정렬
                sorted_devices = sorted(
                    list(devices),
                    key=lambda x: int(x.split('_')[1]) if '_' in x else 0
                )
                
                return sorted_devices
        
        except Exception as e:
            self.logger.error(f"전력 센서 목록 조회 실패: {e}")
            return []
    
    def get_all_environment_devices(self) -> List[str]:
        """
        모든 환경 센서 목록 조회
        
        Returns:
            list: 센서 ID 목록 (예: ['Env_1', 'Env_2', ...])
        """
        try:
            with get_db_session() as session:
                devices = (
                    session.query(EnvironmentData.device_id)
                    .distinct()
                    .all()
                )
                
                # Env_1, Env_2, ... 순서로 정렬
                sorted_devices = sorted(
                    [device_id for (device_id,) in devices],
                    key=lambda x: int(x.split('_')[1]) if '_' in x else 0
                )
                
                return sorted_devices
        
        except Exception as e:
            self.logger.error(f"환경 센서 목록 조회 실패: {e}")
            return []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 시계열 데이터 조회
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_timeseries_energy(
        self,
        device_id: str,
        hours: int = 1,
        field: str = 'power'
    ) -> List[Dict]:
        """
        전력 센서 시계열 데이터 조회
        
        Args:
            device_id: 장치 ID
            hours: 조회 시간 (시간 단위)
            field: 측정 필드 ('power', 'power_factor', 'energy_total')
        
        Returns:
            list: [{'timestamp': datetime, 'value': float}, ...]
        """
        try:
            with get_db_session() as session:
                start_time = datetime.now() - timedelta(hours=hours)
                
                # 센서 타입 판별 (임시로 두 테이블 모두 조회)
                # 단상 센서 시도
                results = (
                    session.query(EnergySinglePhase)
                    .filter(EnergySinglePhase.device_id == device_id)
                    .filter(EnergySinglePhase.timestamp >= start_time)
                    .order_by(EnergySinglePhase.timestamp.asc())
                    .all()
                )
                
                # 데이터 없으면 3상 센서 시도
                if not results:
                    results = (
                        session.query(EnergyThreePhase)
                        .filter(EnergyThreePhase.device_id == device_id)
                        .filter(EnergyThreePhase.timestamp >= start_time)
                        .order_by(EnergyThreePhase.timestamp.asc())
                        .all()
                    )
                
                # 시계열 데이터 생성
                timeseries = []
                for record in results:
                    timeseries.append({
                        'timestamp': record.timestamp,
                        'value': getattr(record, field, 0)
                    })
                
                return timeseries
        
        except Exception as e:
            self.logger.error(f"전력 시계열 조회 실패: {e}")
            return []
    
    def get_timeseries_environment(
        self,
        device_id: str,
        hours: int = 1,
        field: str = 'temperature'
    ) -> List[Dict]:
        """
        환경 센서 시계열 데이터 조회
        
        Args:
            device_id: 장치 ID
            hours: 조회 시간
            field: 측정 필드 ('temperature', 'humidity', 'illuminance')
        
        Returns:
            list: [{'timestamp': datetime, 'value': float}, ...]
        """
        try:
            with get_db_session() as session:
                start_time = datetime.now() - timedelta(hours=hours)
                
                results = (
                    session.query(EnvironmentData)
                    .filter(EnvironmentData.device_id == device_id)
                    .filter(EnvironmentData.timestamp >= start_time)
                    .order_by(EnvironmentData.timestamp.asc())
                    .all()
                )
                
                timeseries = []
                for record in results:
                    timeseries.append({
                        'timestamp': record.timestamp,
                        'value': getattr(record, field, 0)
                    })
                
                return timeseries
        
        except Exception as e:
            self.logger.error(f"환경 시계열 조회 실패: {e}")
            return []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 통계 데이터 조회
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_statistics_energy(
        self,
        device_id: str,
        hours: int = 24,
        field: str = 'power'
    ) -> Dict:
        """
        전력 센서 통계 데이터 계산
        
        Args:
            device_id: 장치 ID
            hours: 통계 기간
            field: 측정 필드
        
        Returns:
            dict: {'latest': float, 'avg': float, 'max': float, 'min': float, 'count': int}
        """
        try:
            timeseries = self.get_timeseries_energy(device_id, hours, field)
            
            if not timeseries:
                return {
                    'latest': 0.0,
                    'avg': 0.0,
                    'max': 0.0,
                    'min': 0.0,
                    'count': 0
                }
            
            values = [data['value'] for data in timeseries]
            
            return {
                'latest': round(values[-1], 3),
                'avg': round(sum(values) / len(values), 3),
                'max': round(max(values), 3),
                'min': round(min(values), 3),
                'count': len(values)
            }
        
        except Exception as e:
            self.logger.error(f"전력 통계 계산 실패: {e}")
            return {
                'latest': 0.0,
                'avg': 0.0,
                'max': 0.0,
                'min': 0.0,
                'count': 0
            }
    
    def get_statistics_environment(
        self,
        device_id: str,
        hours: int = 24,
        field: str = 'temperature'
    ) -> Dict:
        """
        환경 센서 통계 데이터 계산
        
        Args:
            device_id: 장치 ID
            hours: 통계 기간
            field: 측정 필드
        
        Returns:
            dict: {'latest': float, 'avg': float, 'max': float, 'min': float, 'count': int}
        """
        try:
            timeseries = self.get_timeseries_environment(device_id, hours, field)
            
            if not timeseries:
                return {
                    'latest': 0.0,
                    'avg': 0.0,
                    'max': 0.0,
                    'min': 0.0,
                    'count': 0
                }
            
            values = [data['value'] for data in timeseries]
            
            return {
                'latest': round(values[-1], 3),
                'avg': round(sum(values) / len(values), 3),
                'max': round(max(values), 3),
                'min': round(min(values), 3),
                'count': len(values)
            }
        
        except Exception as e:
            self.logger.error(f"환경 통계 계산 실패: {e}")
            return {
                'latest': 0.0,
                'avg': 0.0,
                'max': 0.0,
                'min': 0.0,
                'count': 0
            }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 기간별 데이터 조회 (내보내기용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_data_by_date_range_energy(
        self,
        device_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        전력 센서 기간별 데이터 조회
        
        Args:
            device_id: 장치 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            list: [{'timestamp_formatted': str, 'power': float, ...}, ...]
        """
        try:
            with get_db_session() as session:
                # 단상 센서 시도
                results = (
                    session.query(EnergySinglePhase)
                    .filter(EnergySinglePhase.device_id == device_id)
                    .filter(EnergySinglePhase.timestamp >= start_date)
                    .filter(EnergySinglePhase.timestamp <= end_date)
                    .order_by(EnergySinglePhase.timestamp.asc())
                    .all()
                )
                
                # 데이터 없으면 3상 센서 시도
                if not results:
                    results = (
                        session.query(EnergyThreePhase)
                        .filter(EnergyThreePhase.device_id == device_id)
                        .filter(EnergyThreePhase.timestamp >= start_date)
                        .filter(EnergyThreePhase.timestamp <= end_date)
                        .order_by(EnergyThreePhase.timestamp.asc())
                        .all()
                    )
                
                data = []
                for record in results:
                    data.append({
                        'timestamp_formatted': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'power': record.power,
                        'power_factor': record.power_factor,
                        'energy_total': record.energy_total
                    })
                
                return data
        
        except Exception as e:
            self.logger.error(f"전력 기간 데이터 조회 실패: {e}")
            return []
    
    def get_data_by_date_range_environment(
        self,
        device_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        환경 센서 기간별 데이터 조회
        
        Args:
            device_id: 장치 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            list: [{'timestamp_formatted': str, 'temperature': float, ...}, ...]
        """
        try:
            with get_db_session() as session:
                results = (
                    session.query(EnvironmentData)
                    .filter(EnvironmentData.device_id == device_id)
                    .filter(EnvironmentData.timestamp >= start_date)
                    .filter(EnvironmentData.timestamp <= end_date)
                    .order_by(EnvironmentData.timestamp.asc())
                    .all()
                )
                
                data = []
                for record in results:
                    data.append({
                        'timestamp_formatted': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'temperature': record.temperature,
                        'humidity': record.humidity,
                        'illuminance': record.illuminance
                    })
                
                return data
        
        except Exception as e:
            self.logger.error(f"환경 기간 데이터 조회 실패: {e}")
            return []


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 데이터 조회 테스트
    
    실행: python src/services/ui_data_service.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("UI 데이터 서비스 테스트")
    print("=" * 70)
    
    service = UIDataService()
    
    # 센서 목록 조회
    print("\n[전력 센서 목록]")
    energy_devices = service.get_all_energy_devices()
    print(f"  {energy_devices}")
    
    print("\n[환경 센서 목록]")
    env_devices = service.get_all_environment_devices()
    print(f"  {env_devices}")
    
    # 시계열 데이터
    if energy_devices:
        print(f"\n[{energy_devices[0]} 시계열 데이터 (1시간)]")
        timeseries = service.get_timeseries_energy(energy_devices[0], 1, 'power')
        print(f"  데이터 개수: {len(timeseries)}개")
    
    # 통계 데이터
    if energy_devices:
        print(f"\n[{energy_devices[0]} 통계 (24시간)]")
        stats = service.get_statistics_energy(energy_devices[0], 24, 'power')
        print(f"  {stats}")
    
    print("\n" + "=" * 70)