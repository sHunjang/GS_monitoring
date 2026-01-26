# ==============================================
# UI 데이터 서비스
# ==============================================
"""
GUI를 위한 데이터 조회 서비스
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 먼저 sys.path 설정 (import 전에!)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 그 다음에 나머지 import
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, and_


from src.core.database import get_db_session
from src.sensors.energy.models import EnergySinglePhase, EnergyThreePhase
from src.sensors.environment.models import EnvironmentData



logger = logging.getLogger(__name__)



class UIDataService:
    """UI 데이터 서비스"""
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력 센서 (Energy)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_energy_model(self, device_id: str):
        """
        장치 ID에 맞는 모델 클래스 반환
        
        Args:
            device_id: 'Energy_1', 'Energy_2', 'Energy_3', 'Energy_4'
        
        Returns:
            EnergySinglePhase or EnergyThreePhase
        """
        if device_id in ['Energy_1', 'Energy_2']:
            return EnergySinglePhase
        elif device_id in ['Energy_3', 'Energy_4']:
            return EnergyThreePhase
        else:
            return EnergySinglePhase
    
    def get_latest_energy(self, device_id: str) -> Optional[Dict[str, Any]]:
        """전력 센서 최신 데이터 조회"""
        try:
            with get_db_session() as session:
                Model = self._get_energy_model(device_id)
                
                data = (
                    session.query(Model)
                    .filter(Model.device_id == device_id)
                    .order_by(Model.timestamp.desc())
                    .first()
                )
                
                if not data:
                    self.logger.warning(f"[{device_id}] 데이터 없음")
                    return None
                
                time_diff = (datetime.now() - data.timestamp).total_seconds()
                if time_diff > 180:
                    status = '미연결'
                elif data.power is None:
                    status = '오류'
                else:
                    status = '정상'
                
                return {
                    'device_id': data.device_id,
                    'timestamp': data.timestamp,
                    'power': round(data.power, 3) if data.power else 0.0,
                    # 'voltage': round(data.voltage, 1) if data.voltage else 0.0,
                    # 'current': round(data.current, 2) if data.current else 0.0,
                    'power_factor': round(data.power_factor, 3) if data.power_factor else 0.0,
                    # 'frequency': round(data.frequency, 1) if data.frequency else 0.0,
                    'energy_total': round(data.energy_total, 2) if data.energy_total else 0.0,
                    'status': status,
                    'sensor_type': '단상' if Model == EnergySinglePhase else '3상'
                }
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 최신 데이터 조회 실패: {e}")
            return None
    
    def get_timeseries_energy(
        self,
        device_id: str,
        hours: int = 1,
        field: str = 'power'
    ) -> List[Dict[str, Any]]:
        """전력 센서 시계열 데이터 조회"""
        try:
            with get_db_session() as session:
                Model = self._get_energy_model(device_id)
                
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                query = (
                    session.query(
                        Model.timestamp,
                        getattr(Model, field)
                    )
                    .filter(
                        and_(
                            Model.device_id == device_id,
                            Model.timestamp >= start_time,
                            Model.timestamp <= end_time
                        )
                    )
                    .order_by(Model.timestamp)
                )
                
                results = query.all()
                
                timeseries = [
                    {
                        'timestamp': row[0],
                        'value': round(float(row[1]), 3) if row[1] is not None else 0.0
                    }
                    for row in results
                ]
                
                self.logger.debug(
                    f"[{device_id}] 시계열 데이터 조회: {len(timeseries)}개 ({hours}시간)"
                )
                
                return timeseries
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 시계열 데이터 조회 실패: {e}")
            return []
    
    def get_statistics_energy(
        self,
        device_id: str,
        hours: int = 24,
        field: str = 'power'
    ) -> Dict[str, float]:
        """전력 센서 통계 계산"""
        try:
            with get_db_session() as session:
                Model = self._get_energy_model(device_id)
                
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                field_col = getattr(Model, field)
                
                stats = (
                    session.query(
                        func.avg(field_col).label('avg'),
                        func.max(field_col).label('max'),
                        func.min(field_col).label('min'),
                        func.count(field_col).label('count')
                    )
                    .filter(
                        and_(
                            Model.device_id == device_id,
                            Model.timestamp >= start_time,
                            Model.timestamp <= end_time,
                            field_col.isnot(None)
                        )
                    )
                    .first()
                )
                
                latest_data = self.get_latest_energy(device_id)
                latest_value = latest_data.get(field, 0.0) if latest_data else 0.0
                
                return {
                    'avg': round(float(stats.avg), 3) if stats.avg else 0.0,
                    'max': round(float(stats.max), 3) if stats.max else 0.0,
                    'min': round(float(stats.min), 3) if stats.min else 0.0,
                    'latest': latest_value,
                    'count': stats.count or 0
                }
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 통계 계산 실패: {e}")
            return {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'latest': 0.0, 'count': 0}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 환경 센서 (Environment)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_latest_environment(self, device_id: str) -> Optional[Dict[str, Any]]:
        """환경 센서 최신 데이터 조회"""
        try:
            with get_db_session() as session:
                data = (
                    session.query(EnvironmentData)
                    .filter(EnvironmentData.device_id == device_id)
                    .order_by(EnvironmentData.timestamp.desc())
                    .first()
                )
                
                if not data:
                    self.logger.warning(f"[{device_id}] 데이터 없음")
                    return None
                
                time_diff = (datetime.now() - data.timestamp).total_seconds()
                if time_diff > 180:
                    status = '미연결'
                elif data.temperature is None:
                    status = '오류'
                else:
                    status = '정상'
                
                return {
                    'device_id': data.device_id,
                    'timestamp': data.timestamp,
                    'temperature': round(data.temperature, 1) if data.temperature else 0.0,
                    'humidity': round(data.humidity, 1) if data.humidity else 0.0,
                    'illuminance': data.illuminance if data.illuminance else 0,
                    'status': status
                }
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 최신 데이터 조회 실패: {e}")
            return None
    
    def get_timeseries_environment(
        self,
        device_id: str,
        hours: int = 1,
        field: str = 'temperature'
    ) -> List[Dict[str, Any]]:
        """환경 센서 시계열 데이터 조회"""
        try:
            with get_db_session() as session:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                query = (
                    session.query(
                        EnvironmentData.timestamp,
                        getattr(EnvironmentData, field)
                    )
                    .filter(
                        and_(
                            EnvironmentData.device_id == device_id,
                            EnvironmentData.timestamp >= start_time,
                            EnvironmentData.timestamp <= end_time
                        )
                    )
                    .order_by(EnvironmentData.timestamp)
                )
                
                results = query.all()
                
                timeseries = [
                    {
                        'timestamp': row[0],
                        'value': float(row[1]) if row[1] is not None else 0.0
                    }
                    for row in results
                ]
                
                return timeseries
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 시계열 데이터 조회 실패: {e}")
            return []
    
    def get_statistics_environment(
        self,
        device_id: str,
        hours: int = 24,
        field: str = 'temperature'
    ) -> Dict[str, float]:
        """환경 센서 통계 계산"""
        try:
            with get_db_session() as session:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                field_col = getattr(EnvironmentData, field)
                
                stats = (
                    session.query(
                        func.avg(field_col).label('avg'),
                        func.max(field_col).label('max'),
                        func.min(field_col).label('min'),
                        func.count(field_col).label('count')
                    )
                    .filter(
                        and_(
                            EnvironmentData.device_id == device_id,
                            EnvironmentData.timestamp >= start_time,
                            EnvironmentData.timestamp <= end_time,
                            field_col.isnot(None)
                        )
                    )
                    .first()
                )
                
                latest_data = self.get_latest_environment(device_id)
                latest_value = latest_data.get(field, 0.0) if latest_data else 0.0
                
                return {
                    'avg': round(float(stats.avg), 2) if stats.avg else 0.0,
                    'max': round(float(stats.max), 2) if stats.max else 0.0,
                    'min': round(float(stats.min), 2) if stats.min else 0.0,
                    'latest': latest_value,
                    'count': stats.count or 0
                }
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 통계 계산 실패: {e}")
            return {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'latest': 0.0, 'count': 0}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 센서 목록 조회
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_all_energy_devices(self) -> List[str]:
        """전력 센서 목록 조회"""
        try:
            with get_db_session() as session:
                single_devices = (
                    session.query(EnergySinglePhase.device_id)
                    .distinct()
                    .all()
                )
                three_devices = (
                    session.query(EnergyThreePhase.device_id)
                    .distinct()
                    .all()
                )
                
                devices = [d[0] for d in single_devices] + [d[0] for d in three_devices]
                return sorted(set(devices))
        
        except Exception as e:
            self.logger.error(f"전력 센서 목록 조회 실패: {e}")
            return []
    
    def get_all_environment_devices(self) -> List[str]:
        """환경 센서 목록 조회"""
        try:
            with get_db_session() as session:
                devices = (
                    session.query(EnvironmentData.device_id)
                    .distinct()
                    .order_by(EnvironmentData.device_id)
                    .all()
                )
                
                return [d[0] for d in devices]
        
        except Exception as e:
            self.logger.error(f"환경 센서 목록 조회 실패: {e}")
            return []
    
    def get_sensor_info(self, device_id: str) -> Dict[str, Any]:
        """센서 정보 조회"""
        if device_id.startswith('Energy_'):
            sensor_type = '단상' if device_id in ['Energy_1', 'Energy_2'] else '3상'
            
            return {
                'type': 'energy',
                'name': f'{device_id} ({sensor_type})',
                'fields': {
                    'power': {'label': '전력', 'unit': 'kW', 'color': '#1E88E5'},
                    # 'voltage': {'label': '전압', 'unit': 'V', 'color': '#FB8C00'},
                    # 'current': {'label': '전류', 'unit': 'A', 'color': '#E53935'},
                    'power_factor': {'label': '역률', 'unit': '', 'color': '#43A047'},
                    # 'frequency': {'label': '주파수', 'unit': 'Hz', 'color': '#8E24AA'},
                    'energy_total': {'label': '전력량', 'unit': 'kWh', 'color': '#00ACC1'}
                }
            }
        
        elif device_id.startswith('Env_'):
            return {
                'type': 'environment',
                'name': device_id,
                'fields': {
                    'temperature': {'label': '온도', 'unit': '°C', 'color': '#FF6F00'},
                    'humidity': {'label': '습도', 'unit': '%', 'color': '#00ACC1'},
                    'illuminance': {'label': '조도', 'unit': 'lux', 'color': '#FDD835'}
                }
            }
        
        else:
            return {'type': 'unknown', 'name': device_id, 'fields': {}}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 기간별 데이터 조회 (데이터 내보내기용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_data_by_date_range_energy(
        self,
        device_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        기간별 전력 센서 데이터 조회
        
        Args:
            device_id: 장치 ID (Energy_1, Energy_2, ...)
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            List[Dict]: 데이터 리스트
        """
        try:
            with get_db_session() as session:
                Model = self._get_energy_model(device_id)
                
                query = (
                    session.query(Model)
                    .filter(
                        and_(
                            Model.device_id == device_id,
                            Model.timestamp >= start_date,
                            Model.timestamp <= end_date
                        )
                    )
                    .order_by(Model.timestamp)
                )
                
                results = query.all()
                
                data_list = []
                for row in results:
                    data_list.append({
                        'timestamp': row.timestamp,
                        'device_id': row.device_id,
                        'power': round(row.power, 3) if row.power else 0.0,
                        # 'voltage': round(row.voltage, 1) if row.voltage else 0.0,
                        # 'current': round(row.current, 2) if row.current else 0.0,
                        'power_factor': round(row.power_factor, 3) if row.power_factor else 0.0,
                        'frequency': round(row.frequency, 1) if row.frequency else 0.0,
                        'energy_total': round(row.energy_total, 2) if row.energy_total else 0.0,
                    })
                
                self.logger.info(
                    f"[{device_id}] 기간별 데이터 조회: {len(data_list)}개 "
                    f"({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"
                )
                
                return data_list
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 기간별 데이터 조회 실패: {e}")
            return []
    
    def get_data_by_date_range_environment(
        self,
        device_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        기간별 환경 센서 데이터 조회
        
        Args:
            device_id: 장치 ID (Env_1, Env_2, ...)
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            List[Dict]: 데이터 리스트
        """
        try:
            with get_db_session() as session:
                query = (
                    session.query(EnvironmentData)
                    .filter(
                        and_(
                            EnvironmentData.device_id == device_id,
                            EnvironmentData.timestamp >= start_date,
                            EnvironmentData.timestamp <= end_date
                        )
                    )
                    .order_by(EnvironmentData.timestamp)
                )
                
                results = query.all()
                
                data_list = []
                for row in results:
                    data_list.append({
                        'timestamp': row.timestamp,
                        'device_id': row.device_id,
                        'temperature': round(row.temperature, 1) if row.temperature else 0.0,
                        'humidity': round(row.humidity, 1) if row.humidity else 0.0,
                        'illuminance': row.illuminance if row.illuminance else 0,
                    })
                
                self.logger.info(
                    f"[{device_id}] 기간별 데이터 조회: {len(data_list)}개 "
                    f"({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"
                )
                
                return data_list
        
        except Exception as e:
            self.logger.error(f"[{device_id}] 기간별 데이터 조회 실패: {e}")
            return []



# ==============================================
# 테스트 코드
# ==============================================


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(message)s'
    )
    
    print("=" * 70)
    print("UI 데이터 서비스 테스트")
    print("=" * 70)
    
    service = UIDataService()
    
    # 센서 목록
    print("\n[센서 목록]")
    energy_devices = service.get_all_energy_devices()
    env_devices = service.get_all_environment_devices()
    
    print(f"전력 센서: {energy_devices}")
    print(f"환경 센서: {env_devices}")
    
    # 최신 데이터
    if energy_devices:
        print("\n[전력 센서 최신 데이터]")
        latest = service.get_latest_energy(energy_devices[0])
        if latest:
            print(f"장치: {latest['device_id']}")
            print(f"전력: {latest['power']} kW")
            print(f"상태: {latest['status']}")
    
    if env_devices:
        print("\n[환경 센서 최신 데이터]")
        latest = service.get_latest_environment(env_devices[0])
        if latest:
            print(f"장치: {latest['device_id']}")
            print(f"온도: {latest['temperature']} °C")
            print(f"상태: {latest['status']}")
    
    # 기간별 데이터 조회 테스트
    if energy_devices:
        print("\n[전력 센서 기간별 데이터]")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        data = service.get_data_by_date_range_energy(
            energy_devices[0],
            start_date,
            end_date
        )
        print(f"7일간 데이터: {len(data)}개")
    
    print("\n" + "=" * 70)
    print("✅ 테스트 완료")
