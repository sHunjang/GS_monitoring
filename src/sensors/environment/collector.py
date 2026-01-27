# ==============================================
# 환경 센서 Collector 모듈 (PyInstaller 호환)
# ==============================================
"""
환경 센서 데이터 수집기 (온도+습도+조도)

역할:
- 백그라운드 스레드에서 주기적 수집
- 수집 시작/중지 제어
- 통계 정보 제공

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
import threading
import time
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Service import
try:
    from service import EnvironmentService
except ImportError:
    try:
        from sensors.environment.service import EnvironmentService
    except ImportError:
        from src.sensors.environment.service import EnvironmentService


logger = logging.getLogger(__name__)


class EnvironmentCollector:
    """
    환경 센서 데이터 수집기
    
    기능:
    1. 백그라운드 스레드에서 주기적 수집
    2. 수집 시작/중지 제어
    3. 통계 정보 제공
    
    사용 예:
        collector = EnvironmentCollector(
            device_id="Env_1",
            port="COM11",
            sensor_id=0,
            interval=60
        )
        collector.start()  # 수집 시작
        # ... 실행 중 ...
        collector.stop()   # 수집 중지
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
        self.running = False                    # 실행 상태 플래그
        self.thread: Optional[threading.Thread] = None  # 수집 스레드
        
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
    
    def start(self):
        """
        수집 시작
        
        백그라운드 스레드를 생성하여 주기적으로 데이터 수집
        """
        # 이미 실행 중이면 무시
        if self.running:
            self.logger.warning(f"[{self.device_id}] 이미 실행 중입니다.")
            return
        
        # 실행 플래그 설정
        self.running = True
        
        # 백그라운드 스레드 생성
        self.thread = threading.Thread(
            target=self._collect_loop,
            name=f"EnvironmentCollector-{self.device_id}",
            daemon=True  # 메인 스레드 종료 시 함께 종료
        )
        self.thread.start()
        
        # 시작 로그
        self.logger.info(
            f"[{self.device_id}] 수집 시작 "
            f"(주기: {self.interval}초, 포트: {self.port}, 센서 ID: {self.sensor_id})"
        )
    
    def stop(self):
        """
        수집 중지
        
        실행 중인 스레드를 안전하게 종료
        """
        # 실행 중이 아니면 무시
        if not self.running:
            return
        
        # 실행 플래그 해제
        self.running = False
        
        # 스레드 종료 대기 (최대 5초)
        if self.thread:
            self.thread.join(timeout=5)
        
        # 연결 해제
        self.service.disconnect()
        
        # 중지 로그
        self.logger.info(f"[{self.device_id}] 수집 중지")
    
    def _collect_loop(self):
        """
        수집 루프 (백그라운드 스레드에서 실행)
        
        interval 주기마다 데이터 수집 반복
        """
        self.logger.debug(f"[{self.device_id}] 수집 루프 시작")
        
        # running이 True인 동안 계속 실행
        while self.running:
            try:
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 데이터 수집 및 저장
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                self.service.collect_and_save()
            
            except Exception as e:
                # 오류 발생 시 로그만 출력하고 계속 실행
                self.logger.error(
                    f"[{self.device_id}] 수집 중 오류: {e}",
                    exc_info=True  # 스택 트레이스 출력
                )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 다음 수집까지 대기
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    """
    이 파일을 직접 실행하면 Collector 테스트
    
    실행: python src/sensors/environment/collector.py
    """
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("환경 센서 Collector 테스트")
    print("=" * 70)
    
    collector = EnvironmentCollector(
        device_id="Env_TEST",
        port="COM11",
        sensor_id=0,
        interval=10  # 테스트용 10초
    )
    
    collector.start()
    
    print("\n10초마다 데이터 수집 중...")
    print("30초 후 통계 출력 및 종료")
    print("또는 Ctrl+C로 중지\n")
    
    try:
        # 30초 동안 실행
        time.sleep(30)
        
        # 통계 출력
        print("\n" + "=" * 70)
        print("통계 정보")
        print("=" * 70)
        collector.print_statistics()
    
    except KeyboardInterrupt:
        # Ctrl+C 입력 시
        print("\n\n중지 신호 수신...")
    
    finally:
        # 수집 중지
        collector.stop()
        print("\n테스트 완료")