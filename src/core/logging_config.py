# ==============================================
# 로깅 설정 모듈 (PyInstaller 호환)
# ==============================================
"""
로깅 설정

콘솔과 파일에 로그를 출력합니다.

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Config import (조건부 - PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    # 첫 번째 시도: 같은 폴더에서 import
    from config import get_config
except ImportError:
    try:
        # 두 번째 시도: core 패키지에서 import
        from core.config import get_config
    except ImportError:
        # 세 번째 시도: src.core 패키지에서 import
        from src.core.config import get_config


def setup_logging():
    """
    로깅 설정 초기화
    
    기능:
    1. 콘솔 핸들러 - 터미널에 로그 출력
    2. 파일 핸들러 - logs/app.log에 로그 저장 (로테이션)
    3. 외부 라이브러리 로그 레벨 조정
    """
    # 설정 로드
    config = get_config()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로그 디렉토리 생성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # logs/app.log에서 logs 폴더 추출
    log_dir = os.path.dirname(config.log_file_path)
    
    # 디렉토리가 있고, 존재하지 않으면 생성
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"📁 로그 디렉토리 생성: {log_dir}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로그 포맷 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 형식: 2026-01-27 10:30:45 | INFO    | module.name | 메시지
    log_format = (
        '%(asctime)s | '       # 시간
        '%(levelname)-7s | '   # 로그 레벨 (7자리 왼쪽 정렬)
        '%(name)s | '          # 모듈 이름
        '%(message)s'          # 메시지
    )
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Formatter 생성
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 루트 로거 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    root_logger = logging.getLogger()
    
    # 로그 레벨 설정 (INFO, DEBUG, WARNING, ERROR)
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 콘솔 핸들러 (터미널 출력)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 파일 핸들러 (로그 파일 저장 + 로테이션)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로테이션: 파일 크기가 max_bytes를 넘으면
    #          자동으로 app.log.1, app.log.2... 생성
    file_handler = RotatingFileHandler(
        filename=config.log_file_path,        # 로그 파일 경로
        maxBytes=config.log_max_bytes,        # 최대 크기 (10MB)
        backupCount=config.log_backup_count,  # 백업 개수 (5개)
        encoding='utf-8'                      # UTF-8 인코딩
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 초기 로그 출력
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    root_logger.info("=" * 70)
    root_logger.info(
        f"로깅 시스템 초기화 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    root_logger.info(f"로그 레벨: {config.log_level}")
    root_logger.info(f"로그 파일: {config.log_file_path}")
    root_logger.info("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 외부 라이브러리 로그 레벨 조정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # pymodbus와 sqlalchemy는 로그를 너무 많이 출력하므로
    # WARNING 레벨로 제한 (중요한 것만 출력)
    logging.getLogger('pymodbus').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 로깅 테스트
    
    실행: python src/core/logging_config.py
    """
    # 로깅 초기화
    setup_logging()
    
    # 테스트 로거
    logger = logging.getLogger(__name__)
    
    print("\n" + "=" * 70)
    print("로깅 테스트")
    print("=" * 70 + "\n")
    
    # 다양한 레벨 테스트
    logger.debug("🔍 DEBUG 메시지 - 상세한 디버깅 정보")
    logger.info("ℹ️  INFO 메시지 - 일반 정보")
    logger.warning("⚠️  WARNING 메시지 - 경고")
    logger.error("❌ ERROR 메시지 - 오류")
    logger.critical("🔥 CRITICAL 메시지 - 치명적 오류")
    
    print("\n" + "=" * 70)
    print("✅ 테스트 완료")
    print("💡 logs/app.log 파일을 확인하세요")
    print("=" * 70)