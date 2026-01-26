# ==============================================
# 환경 센서 Service 모듈
# ==============================================
"""
환경 센서 서비스 (온도+습도+조도)

역할:
- 센서 데이터 읽기 (Reader 사용)
- 데이터 검증
- DB 저장
- 통계 정보 관리
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sensors.environment.reader import EnvironmentReader
from core.database import insert_environment_data


class EnvironmentService:
    """
    환경 센서 서비스
    
    기능:
    1. 센서 데이터 수집
    2. 데이터 검증
    3. DB 저장
    4. 통계 정보 제공
    """
    
    def __init__(
        self,
        device_id: str,
        port: str = "COM11",
        sensor_id: int = 0
    ):
        """
        초기화
        
        Args:
            device_id: 장치 ID (예: "Env_1", "Env_2")
            port: 시리얼 포트 (예: "COM11", "/dev/ttyUSB0")
            sensor_id: 센서 주소 (0~9)
        """
        self.device_id = device_id
        self.port = port
        self.sensor_id = sensor_id
        
        # Reader 생성
        self.reader = EnvironmentReader(
            device_id=device_id,
            port=port,
            sensor_id=sensor_id
        )
        
        # 연결 상태
        self.connected = False
        
        # 통계 정보
        self.total_collections = 0
        self.successful_collections = 0
        self.failed_collections = 0
        self.last_collection_time = None
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
    
    def connect(self) -> bool:
        """
        시리얼 포트 연결
        
        Returns:
            bool: 연결 성공 시 True
        """
        if self.connected:
            return True
        
        success = self.reader.connect()
        self.connected = success
        return success
    
    def disconnect(self):
        """시리얼 포트 연결 해제"""
        if self.connected:
            self.reader.disconnect()
            self.connected = False
    
    def collect_and_save(self) -> bool:
        """
        센서 데이터 수집 후 DB 저장
        
        Returns:
            bool: 성공 시 True
        """
        # 통계: 총 수집 시도 횟수 증가
        self.total_collections += 1
        self.last_collection_time = datetime.now()
        
        try:
            # 연결 확인
            if not self.connected:
                if not self.connect():
                    self.logger.error(f"[{self.device_id}] 시리얼 포트 연결 실패")
                    self.failed_collections += 1
                    return False
            
            # 센서 데이터 읽기
            raw_data = self.reader.read_data()
            
            if not raw_data:
                self.logger.error(f"[{self.device_id}] 센서 데이터 읽기 실패")
                self.failed_collections += 1
                return False
            
            # 데이터 검증
            if not self._validate_data(raw_data):
                self.logger.error(f"[{self.device_id}] 데이터 검증 실패")
                self.failed_collections += 1
                return False
            
            # DB 저장
            success = self._save_data(raw_data)
            
            if success:
                self.successful_collections += 1
                self.logger.info(
                    f"[{self.device_id}] ✓ 데이터 저장: "
                    f"T={raw_data['temperature']:.3f}°C, "
                    f"H={raw_data['humidity']:.1f}%, "
                    f"L={raw_data['illuminance']} lux"
                )
            else:
                self.failed_collections += 1
            
            return success
        
        except Exception as e:
            self.failed_collections += 1
            self.logger.error(f"[{self.device_id}] 오류: {e}")
            return False
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        데이터 검증
        
        Args:
            data: 센서 데이터
        
        Returns:
            bool: 유효하면 True
        """
        required = ['temperature', 'humidity', 'illuminance']
        
        for field in required:
            if field not in data or data[field] is None:
                self.logger.error(f"[{self.device_id}] 필수 필드 누락: {field}")
                return False
        
        # 범위 검증
        temp = data['temperature']
        humi = data['humidity']
        illu = data['illuminance']
        
        if not (-40 <= temp <= 80):
            self.logger.warning(f"[{self.device_id}] 온도 범위 초과: {temp}°C")
        
        if not (0 <= humi <= 100):
            self.logger.warning(f"[{self.device_id}] 습도 범위 초과: {humi}%")
        
        if not (0 <= illu <= 99999):
            self.logger.warning(f"[{self.device_id}] 조도 범위 초과: {illu} lux")
        
        return True
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """
        DB 저장
        
        Args:
            data: 검증된 센서 데이터
        
        Returns:
            bool: 저장 성공 시 True
        """
        timestamp = datetime.now()
        
        return insert_environment_data(
            device_id=self.device_id,
            temperature=data['temperature'],
            humidity=data['humidity'],
            illuminance=data['illuminance'],
            timestamp=timestamp
        )
    
    def get_statistics(self) -> dict:
        """
        수집 통계 정보 반환
        
        Returns:
            dict: 통계 정보
        """
        success_rate = 0.0
        if self.total_collections > 0:
            success_rate = (self.successful_collections / self.total_collections) * 100
        
        return {
            'device_id': self.device_id,
            'port': self.port,
            'sensor_id': self.sensor_id,
            'total_collections': self.total_collections,
            'successful_collections': self.successful_collections,
            'failed_collections': self.failed_collections,
            'success_rate': success_rate,
            'last_collection_time': (
                self.last_collection_time.isoformat()
                if self.last_collection_time else None
            )
        }
    
    def print_statistics(self):
        """통계 정보 출력"""
        stats = self.get_statistics()
        
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"[{self.device_id}] 수집 통계")
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"  포트          : {stats['port']}")
        self.logger.info(f"  센서 ID       : {stats['sensor_id']}")
        self.logger.info(f"  총 수집 시도  : {stats['total_collections']}회")
        self.logger.info(f"  성공          : {stats['successful_collections']}회")
        self.logger.info(f"  실패          : {stats['failed_collections']}회")
        self.logger.info(f"  성공률        : {stats['success_rate']:.1f}%")
        if stats['last_collection_time']:
            self.logger.info(f"  마지막 수집   : {stats['last_collection_time']}")
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("환경 센서 Service 테스트")
    print("=" * 70)
    
    service = EnvironmentService(
        device_id="Env_1",
        port="COM11",
        sensor_id=0
    )
    
    for i in range(3):
        print(f"\n수집 #{i+1}:")
        success = service.collect_and_save()
        print(f"결과: {'✅ 성공' if success else '❌ 실패'}")
    
    print("\n[통계 정보]")
    service.print_statistics()
    
    service.disconnect()
    print("\n테스트 완료")
