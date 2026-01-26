# ==============================================
# 로깅 설정 모듈
# ==============================================

"""
로깅 설정

콘솔과 파일에 로그를 출력합니다.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

from core.config import get_config


def setup_logging():
    """로깅 설정 초기화"""
    config = get_config()
    
    # 로그 디렉토리 생성
    log_dir = os.path.dirname(config.log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 포맷
    log_format = (
        '%(asctime)s | '
        '%(levelname)-7s | '
        '%(name)s | '
        '%(message)s'
    )
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (로테이션)
    file_handler = RotatingFileHandler(
        filename=config.log_file_path,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 초기 로그
    root_logger.info("=" * 70)
    root_logger.info(f"로깅 시스템 초기화 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root_logger.info(f"로그 레벨: {config.log_level}")
    root_logger.info(f"로그 파일: {config.log_file_path}")
    root_logger.info("=" * 70)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('pymodbus').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
