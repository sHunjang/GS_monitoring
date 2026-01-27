# ==============================================
# 센서 모니터링 시스템 메인 모듈 (PyInstaller 호환)
# ==============================================
"""
고성 센서 모니터링 시스템 메인 프로그램

주요 기능:
    1. 백그라운드에서 센서 데이터 수집 (설정 가능한 주기)
    2. PyQt5 기반 실시간 모니터링 UI
    3. 전력 센서 + 환경 센서 통합 관리

센서 타입:
    - 전력 센서: Modbus RTU (RS-485)
      * 단상 전력계 (DDS238): Slave ID < 30
      * 3상 전력계 (TAC4300): Slave ID >= 30
    
    - 환경 센서: ASCII Protocol (RS-485)
      * 온도 + 습도 + 조도 측정
      * 센서 ID: 0, 1, 2, ... (ASCII: 0x30, 0x31, 0x32, ...)

아키텍처:
    - ModbusManager: 같은 RS-485 버스 공유 관리
    - threading.Lock: 포트 충돌 방지
    - 순차 접근 보장으로 데이터 무결성 유지

실행:
    python src/main.py
    
중지:
    - Ctrl + C (터미널)
    - UI 창 닫기 버튼 클릭

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
- 모든 모듈 명시적 import
"""

import signal
import sys
import logging
import time
import threading

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건부 import (PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Config import
try:
    from config import get_config
except ImportError:
    try:
        from core.config import get_config
    except ImportError:
        from src.core.config import get_config

# Logging import
try:
    from logging_config import setup_logging
except ImportError:
    try:
        from core.logging_config import setup_logging
    except ImportError:
        from src.core.logging_config import setup_logging

# Database import
try:
    from database import test_db_connection
except ImportError:
    try:
        from core.database import test_db_connection
    except ImportError:
        from src.core.database import test_db_connection

# Collector imports
try:
    from sensors.energy.collector import EnergyCollector
    from sensors.environment.collector import EnvironmentCollector
except ImportError:
    try:
        import importlib
        
        # 동적 import
        energy_collector_module = importlib.import_module('sensors.energy.collector')
        env_collector_module = importlib.import_module('sensors.environment.collector')
        
        EnergyCollector = energy_collector_module.EnergyCollector
        EnvironmentCollector = env_collector_module.EnvironmentCollector
    except:
        # import 실패 시 더미 클래스
        class EnergyCollector:
            def __init__(self, *args, **kwargs):
                pass
            def start(self):
                pass
            def stop(self):
                pass
        
        class EnvironmentCollector:
            def __init__(self, *args, **kwargs):
                pass
            def start(self):
                pass
            def stop(self):
                pass

# UI import
try:
    from main_window import MainWindow
except ImportError:
    try:
        from ui.main_window import MainWindow
    except ImportError:
        from src.ui.main_window import MainWindow


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전역 변수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

collectors = []  # 모든 센서 수집기를 담는 리스트
logger = logging.getLogger(__name__)  # 로거
running = True  # 프로그램 실행 플래그
app = None  # PyQt 애플리케이션 객체
window = None  # PyQt 메인 윈도우 객체


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시그널 핸들러
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def signal_handler(sig, frame):
    """
    시그널 핸들러 (Ctrl+C 처리)
    
    사용자가 Ctrl+C를 누르면 호출되어 프로그램을 안전하게 종료합니다.
    
    Args:
        sig: 시그널 번호
        frame: 현재 스택 프레임
    """
    global running
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("⏹️  프로그램 종료 신호 수신 (Ctrl+C)")
    logger.info("=" * 70)
    
    # 실행 플래그 종료
    running = False
    
    # 모든 센서 수집기 중지
    logger.info("센서 수집기 중지 중...")
    for collector in collectors:
        try:
            collector.stop()
        except Exception as e:
            logger.error(f"수집기 중지 실패: {e}")
    
    # UI 종료
    if app:
        app.quit()
    
    logger.info("=" * 70)
    logger.info("✓ 프로그램 종료 완료")
    logger.info("=" * 70)
    
    sys.exit(0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시작 배너
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_banner(config):
    """
    시작 배너 출력
    
    프로그램 시작 시 현재 설정을 보기 좋게 출력합니다.
    
    Args:
        config: Config 객체
    """
    logger.info("=" * 70)
    logger.info(f"  {config.app_name} v{config.app_version}")
    logger.info("=" * 70)
    
    # 데이터베이스 정보
    logger.info(f"📦 데이터베이스: {config.db_host}:{config.db_port}/{config.db_name}")
    
    # 수집 주기
    logger.info(f"⏱️  수집 주기: {config.collection_interval}초")
    
    # 시리얼 버스 정보
    logger.info("")
    logger.info("🔌 시리얼 버스:")
    logger.info(f"  - RS-485 버스: {config.energy_serial_port}")
    logger.info(f"  - 전력 센서: Modbus RTU")
    logger.info(f"  - 환경 센서: ASCII 프로토콜")
    logger.info(f"  - 🔧 ModbusManager 통합 (포트 공유)")
    
    # 실행 모드
    logger.info("")
    logger.info("🚀 실행 모드:")
    logger.info("   - 백그라운드: 센서 데이터 수집")
    logger.info("   - UI: 실시간 모니터링 대시보드")
    logger.info("=" * 70)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 센서 수집기 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_collectors(config):
    """
    센서 수집기 설정 및 등록
    
    .env 파일의 설정을 기반으로 모든 센서 수집기를 생성하고 등록합니다.
    
    Args:
        config: Config 객체
    
    동작:
        1. 전력 센서 수집기 생성 (ENERGY_SLAVE_IDS 개수만큼)
        2. 환경 센서 수집기 생성 (ENV_SENSOR_IDS 개수만큼)
        3. 전역 collectors 리스트에 추가
    
    Example:
        .env 파일:
            ENERGY_SLAVE_IDS=11,12,31,32  # 4개 전력 센서
            ENV_SENSOR_IDS=0,1            # 2개 환경 센서
        
        결과:
            collectors = [
                EnergyCollector("Energy_1", slave_id=11),
                EnergyCollector("Energy_2", slave_id=12),
                EnergyCollector("Energy_3", slave_id=31),
                EnergyCollector("Energy_4", slave_id=32),
                EnvironmentCollector("Env_1", sensor_id=0),
                EnvironmentCollector("Env_2", sensor_id=1),
            ]
    """
    logger.info("=" * 70)
    logger.info("⚙️  센서 수집기 설정")
    logger.info("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 전력 센서 등록
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if config.energy_slave_ids:
        logger.info(f"\n⚡ [전력량 센서] {len(config.energy_slave_ids)}개")
        logger.info(f"  - 포트: {config.energy_serial_port}")
        logger.info(f"  - Baudrate: {config.energy_serial_baudrate} bps")
        logger.info(f"  - Slave IDs: {config.energy_slave_ids}")
        logger.info("")
        
        # 각 Slave ID마다 수집기 생성
        for idx, slave_id in enumerate(config.energy_slave_ids, start=1):
            # 장치 ID 생성 (Energy_1, Energy_2, ...)
            device_id = f"Energy_{idx}"
            
            # 수집기 객체 생성
            collector = EnergyCollector(
                device_id=device_id,
                slave_id=slave_id,
                interval=config.collection_interval
            )
            
            # 전역 리스트에 추가
            collectors.append(collector)
            
            # 센서 타입 판별 (Slave ID로 단상/3상 구분)
            sensor_type = "단상 (DDS238)" if slave_id < 30 else "3상 (TAC4300)"
            
            logger.info(f"  ✓ {device_id} - Slave ID {slave_id:2d} - {sensor_type}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. 환경 센서 등록 (.env에서 자동 관리)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if config.env_sensor_ids:
        logger.info(f"\n🌡️  [환경 센서] {len(config.env_sensor_ids)}개 (온도+습도+조도)")
        logger.info(f"  - 포트: {config.env_serial_port}")
        logger.info(f"  - Baudrate: {config.env_serial_baudrate} bps")
        logger.info(f"  - Sensor IDs: {config.env_sensor_ids}")
        logger.info(f"  - 🔧 전력 센서와 포트 공유 (ModbusManager)")
        logger.info("")
        
        # 각 Sensor ID마다 수집기 생성
        for idx, sensor_id in enumerate(config.env_sensor_ids, start=1):
            # 장치 ID 생성 (Env_1, Env_2, ...)
            device_id = f"Env_{idx}"
            
            # 수집기 객체 생성
            env_collector = EnvironmentCollector(
                device_id=device_id,
                port=config.env_serial_port,  # 전력 센서와 같은 포트 사용
                sensor_id=sensor_id,
                interval=config.collection_interval
            )
            
            # 전역 리스트에 추가
            collectors.append(env_collector)
            
            # ASCII 헥스 코드 계산 (0x30 + sensor_id)
            ascii_hex = 0x30 + sensor_id
            
            logger.info(f"  ✓ {device_id} - Sensor ID {sensor_id} (ASCII: 0x{ascii_hex:02X})")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. 등록 완료 로그
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("")
    logger.info(f"✓ 총 {len(collectors)}개 센서 등록 완료")
    logger.info("=" * 70)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 수집 시작
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def start_data_collection():
    """
    데이터 수집 시작 (백그라운드 스레드)
    
    모든 등록된 센서 수집기를 시작합니다.
    포트 충돌을 방지하기 위해 각 수집기를 0.5초 간격으로 시작합니다.
    
    동작:
        1. 각 수집기의 start() 메서드 호출
        2. 0.5초 대기 (포트 충돌 방지)
        3. 다음 수집기 시작
    """
    global running
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 센서 데이터 수집 시작")
    logger.info("=" * 70)
    
    # 모든 수집기 순차적으로 시작
    for idx, collector in enumerate(collectors):
        # 수집기 시작
        collector.start()
        logger.info(f"  ✓ {collector.device_id} 수집 시작")
        
        # 마지막 수집기가 아니면 0.5초 대기
        # (포트 충돌 방지 및 순차 시작)
        if idx < len(collectors) - 1:
            time.sleep(0.5)
    
    logger.info("")
    logger.info(f"✓ {len(collectors)}개 센서 수집 시작 완료")
    logger.info("=" * 70)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI 시작
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def start_ui(config):
    """
    UI 시작 (메인 스레드)
    
    PyQt5 기반 모니터링 대시보드를 실행합니다.
    UI 창을 닫으면 모든 센서 수집기도 자동으로 중지됩니다.
    
    Args:
        config: Config 객체
    
    동작:
        1. QApplication 생성
        2. MainWindow 생성 및 표시
        3. closeEvent 오버라이드 (창 닫기 시 수집기 중지)
        4. 이벤트 루프 실행
    """
    global app, window
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🖥️  UI 시작")
    logger.info("=" * 70)
    
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. PyQt 애플리케이션 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        app = QApplication(sys.argv)
        app.setApplicationName(config.app_name)
        app.setApplicationVersion(config.app_version)
        
        # High DPI 지원 (4K 모니터 등)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 메인 윈도우 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        window = MainWindow()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 윈도우 닫기 이벤트 오버라이드
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 원래 closeEvent 저장
        original_close_event = window.closeEvent
        
        def custom_close_event(event):
            """
            윈도우 닫기 시 센서 수집기도 함께 중지
            
            Args:
                event: QCloseEvent
            """
            global running
            
            logger.info("UI 창 닫기 - 프로그램 종료 중...")
            running = False
            
            # 모든 수집기 중지
            for collector in collectors:
                try:
                    collector.stop()
                except Exception as e:
                    logger.error(f"수집기 중지 실패: {e}")
            
            # 원래 닫기 이벤트 호출
            original_close_event(event)
            
            # 프로그램 종료
            sys.exit(0)
        
        # closeEvent 오버라이드
        window.closeEvent = custom_close_event
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 윈도우 표시
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        window.show()
        
        logger.info("✓ UI 시작 완료")
        logger.info("=" * 70)
        logger.info("")
        logger.info("💡 종료 방법:")
        logger.info("   - UI 창 닫기 버튼 클릭")
        logger.info("   - Ctrl + C (터미널)")
        logger.info("=" * 70)
        logger.info("")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 이벤트 루프 실행 (메인 스레드 블로킹)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"UI 시작 실패: {e}")
        
        import traceback
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"  {line}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """
    메인 함수
    
    프로그램의 진입점입니다.
    
    실행 순서:
        1. 로깅 시스템 초기화
        2. 환경 변수 로드 (.env 파일)
        3. 시작 배너 출력
        4. 데이터베이스 연결 테스트
        5. 센서 수집기 설정
        6. 시그널 핸들러 등록 (Ctrl+C)
        7. 데이터 수집 시작 (백그라운드 스레드)
        8. UI 시작 (메인 스레드)
    """
    global running
    
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 로깅 시스템 초기화
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        setup_logging()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 환경 변수 로드
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        config = get_config()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 시작 배너 출력
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print_banner(config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 데이터베이스 연결 테스트
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("📦 데이터베이스 연결 확인 중...")
        
        if not test_db_connection():
            logger.error("")
            logger.error("=" * 70)
            logger.error("❌ 데이터베이스 연결 실패!")
            logger.error("=" * 70)
            logger.error("확인 사항:")
            logger.error("  1. PostgreSQL이 실행 중인지 확인")
            logger.error("  2. .env 파일의 DB 설정 확인")
            logger.error("  3. database/init_db.py 실행 여부 확인")
            logger.error("=" * 70)
            sys.exit(1)
        
        logger.info("")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 센서 수집기 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        setup_collectors(config)
        
        # 센서가 없으면 경고
        if len(collectors) == 0:
            logger.warning("⚠️  등록된 센서가 없습니다.")
            logger.warning("⚠️  UI만 실행됩니다.")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. 시그널 핸들러 등록 (Ctrl+C)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        signal.signal(signal.SIGINT, signal_handler)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. 데이터 수집 시작 (백그라운드 스레드)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if len(collectors) > 0:
            # 데이터 수집용 별도 스레드 생성
            collection_thread = threading.Thread(
                target=start_data_collection,
                daemon=True  # 메인 스레드 종료 시 함께 종료
            )
            collection_thread.start()
            
            # 수집이 시작될 때까지 잠깐 대기
            time.sleep(1)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 8. UI 시작 (메인 스레드)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        start_ui(config)
    
    except KeyboardInterrupt:
        # Ctrl+C 입력 시
        signal_handler(signal.SIGINT, None)
    
    except Exception as e:
        # 예상치 못한 오류 발생 시
        logger.error("")
        logger.error("=" * 70)
        logger.error(f"❌ 예상치 못한 오류 발생: {e}")
        logger.error("=" * 70)
        
        # 상세 오류 출력
        import traceback
        logger.error("상세 오류:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"  {line}")
        
        logger.error("=" * 70)
        
        # 수집기 중지
        for collector in collectors:
            try:
                collector.stop()
            except:
                pass
        
        sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프로그램 진입점
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    main()