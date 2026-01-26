# ==============================================
# 환경 센서 Collector 모듈
# ==============================================
"""
환경 센서 데이터 수집기 (온도+습도+조도)

역할:
- 백그라운드 스레드에서 주기적 수집
- 수집 시작/중지 제어
- 통계 정보 제공
"""

import logging
import threading
import time
from typing import Optional

from sensors.environment.service import EnvironmentService


class EnvironmentCollector:
    """
    환경 센서 데이터 수집기
    
    기능:
    1. 백그라운드 스레드에서 주기적 수집
    2. 수집 시작/중지 제어
    3. 통계 정보 제공
    """
    
    def __init__(
        self,
        device_id: str,
        port: str = "COM11",
        sensor_id: int = 0,
        interval: int = 60
    ):
        """
        초기화
        
        Args:
            device_id: 장치 ID (예: "Env_1", "Env_2")
            port: 시리얼 포트
            sensor_id: 센서 주소 (0~9)
            interval: 수집 주기 (초)
        """
        self.device_id = device_id
        self.port = port
        self.sensor_id = sensor_id
        self.interval = interval
        
        # Service 생성
        self.service = EnvironmentService(
            device_id=device_id,
            port=port,
            sensor_id=sensor_id
        )
        
        # 스레드 제어
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
    
    def start(self):
        """수집 시작"""
        if self.running:
            self.logger.warning(f"[{self.device_id}] 이미 실행 중입니다.")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._collect_loop,
            name=f"EnvironmentCollector-{self.device_id}",
            daemon=True
        )
        self.thread.start()
        
        self.logger.info(
            f"[{self.device_id}] 수집 시작 "
            f"(주기: {self.interval}초, 포트: {self.port}, 센서 ID: {self.sensor_id})"
        )
    
    def stop(self):
        """수집 중지"""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        self.service.disconnect()
        
        self.logger.info(f"[{self.device_id}] 수집 중지")
    
    def _collect_loop(self):
        """수집 루프 (백그라운드 스레드)"""
        self.logger.debug(f"[{self.device_id}] 수집 루프 시작")
        
        while self.running:
            try:
                # 데이터 수집 및 저장
                self.service.collect_and_save()
            
            except Exception as e:
                self.logger.error(f"[{self.device_id}] 수집 중 오류: {e}")
            
            # 다음 수집까지 대기
            time.sleep(self.interval)
        
        self.logger.debug(f"[{self.device_id}] 수집 루프 종료")
    
    def get_statistics(self) -> dict:
        """
        수집 통계 정보 반환
        
        Returns:
            dict: 통계 정보
        """
        return self.service.get_statistics()
    
    def print_statistics(self):
        """통계 정보 출력"""
        self.service.print_statistics()


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
    print("환경 센서 Collector 테스트")
    print("=" * 70)
    
    collector = EnvironmentCollector(
        device_id="Env_1",
        port="COM11",
        sensor_id=0,
        interval=10
    )
    
    collector.start()
    
    print("\n10초마다 데이터 수집 중...")
    print("30초 후 통계 출력 및 종료")
    print("Ctrl+C로 중지\n")
    
    try:
        time.sleep(30)
        
        print("\n" + "=" * 70)
        print("통계 정보")
        print("=" * 70)
        collector.print_statistics()
    
    except KeyboardInterrupt:
        print("\n\n중지 신호 수신...")
    
    finally:
        collector.stop()
        print("\n테스트 완료")
