# ==============================================
# 전력량 센서 Collector 모듈
# ==============================================
# 역할: 주기적으로 센서 데이터 수집

"""
전력량 센서 데이터 수집기

백그라운드 스레드에서 주기적으로 센서 데이터를 수집합니다.
"""

import logging
import threading
import time
from typing import Optional

from sensors.energy.service import EnergyService


class EnergyCollector:
    """
    전력량 센서 데이터 수집기
    
    기능:
        1. 백그라운드 스레드에서 주기적 수집
        2. 수집 시작/중지 제어
    
    사용 예:
        collector = EnergyCollector(
            device_id="Energy_1",
            slave_id=11,
            interval=60
        )
        collector.start()
        # ... 실행 중 ...
        collector.stop()
    """
    
    def __init__(self, device_id: str, interval: int, slave_id: int):
        """
        초기화
        
        Args:
            device_id: 장치 ID
            interval: 수집 주기 (초)
            slave_id: Modbus Slave ID
        """
        self.device_id = device_id
        self.interval = interval
        self.slave_id = slave_id
        
        # Service 생성
        self.service = EnergyService(device_id=device_id, slave_id=slave_id)
        
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
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        
        self.logger.info(
            f"[{self.device_id}] 수집 시작 "
            f"(주기: {self.interval}초, Slave ID: {self.slave_id})"
        )
    
    def stop(self):
        """수집 중지"""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        self.logger.info(f"[{self.device_id}] 수집 중지")
    
    def _collect_loop(self):
        """수집 루프 (백그라운드 스레드)"""
        while self.running:
            try:
                # 데이터 수집 및 저장
                self.service.collect_and_save()
            
            except Exception as e:
                self.logger.error(f"[{self.device_id}] 수집 중 오류: {e}")
            
            # 다음 수집까지 대기
            time.sleep(self.interval)


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("전력량 센서 Collector 테스트")
    print("=" * 70)
    
    # 수집기 생성
    collector = EnergyCollector(
        device_id="Energy_1",
        slave_id=11,
        interval=10  # 테스트용 10초
    )
    
    # 수집 시작
    collector.start()
    
    print("\n10초마다 데이터 수집 중...")
    print("Ctrl+C로 중지\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n중지 신호 수신...")
        collector.stop()
        print("테스트 종료")
