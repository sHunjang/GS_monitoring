# ==============================================
# 환경 변수 설정 모듈
# ==============================================
"""
.env 파일에서 환경 변수를 읽어서
애플리케이션 전역에서 사용할 수 있는 설정 객체를 제공합니다.

특징:
    - 싱글톤 패턴으로 전역 설정 객체 제공
    - .env 파일의 모든 설정을 자동으로 로드
    - 타입 안전성을 위한 dataclass 사용
    - 콤마로 구분된 리스트 자동 파싱
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
from typing import List, Optional
from dataclasses import dataclass

from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트의 .env 파일)
load_dotenv()


@dataclass
class Config:
    """
    애플리케이션 설정 클래스
    
    .env 파일의 모든 환경 변수를 담는 컨테이너입니다.
    dataclass를 사용하여 타입 안전성을 보장합니다.
    
    Attributes:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터베이스 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        db_host: PostgreSQL 서버 호스트 (기본값: localhost)
        db_port: PostgreSQL 서버 포트 (기본값: 5432)
        db_name: 데이터베이스 이름 (기본값: sensor_goseong)
        db_user: 데이터베이스 사용자 이름
        db_password: 데이터베이스 비밀번호
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 전력량 센서 (Modbus RTU)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        energy_serial_port: RS-485 시리얼 포트 (예: COM11, /dev/ttyUSB0)
        energy_serial_baudrate: 통신 속도 (기본값: 9600 bps)
        energy_serial_timeout: 통신 타임아웃 (기본값: 3초)
        energy_slave_ids: 전력 센서 Slave ID 목록 (예: [11, 12, 31, 32])
                         .env에서 "11,12,31,32" 형태로 입력하면 자동 파싱
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 환경 센서 (ASCII Protocol)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        env_serial_port: 환경 센서 시리얼 포트 (전력 센서와 공유 가능)
        env_serial_baudrate: 통신 속도 (기본값: 9600 bps)
        env_serial_timeout: 통신 타임아웃 (기본값: 1초)
        env_sensor_ids: 환경 센서 ID 목록 (예: [0, 1])
                       .env에서 "0,1" 형태로 입력하면 자동 파싱
                       센서 ID는 ASCII로 0x30 + sensor_id 형태로 전송됨
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터 수집
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        collection_interval: 센서 데이터 수집 주기 (초 단위, 기본값: 60초)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 로깅
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        log_file_path: 로그 파일 경로 (기본값: logs/app.log)
        log_max_bytes: 로그 파일 최대 크기 (기본값: 10MB)
        log_backup_count: 로그 파일 백업 개수 (기본값: 5개)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 애플리케이션 정보
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        app_name: 애플리케이션 이름
        app_version: 버전 번호
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터베이스
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "sensor_goseong"
    db_user: str = "postgres"
    db_password: str = "1234"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력량 센서 (Modbus RTU)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    energy_serial_port: str = "COM11"
    energy_serial_baudrate: int = 9600
    energy_serial_timeout: int = 3
    energy_slave_ids: List[int] = None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 환경 센서 (ASCII Protocol)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    env_serial_port: str = "COM11"
    env_serial_baudrate: int = 9600
    env_serial_timeout: int = 1
    env_sensor_ids: List[int] = None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터 수집
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    collection_interval: int = 60  # 초
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로깅
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    log_level: str = "INFO"
    log_file_path: str = "logs/app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애플리케이션 정보
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    app_name: str = "고성 센서 모니터링 시스템"
    app_version: str = "1.0.0"


def _parse_int_list(env_value: Optional[str]) -> List[int]:
    """
    환경 변수에서 정수 목록 파싱
    
    콤마로 구분된 문자열을 정수 리스트로 변환합니다.
    공백은 자동으로 제거됩니다.
    
    Args:
        env_value: 환경 변수 값 (예: "11,12,31,32" 또는 "11, 12, 31, 32")
    
    Returns:
        List[int]: 정수 목록 (예: [11, 12, 31, 32])
                  빈 값이거나 파싱 실패 시 빈 리스트 반환
    
    Example:
        >>> _parse_int_list("11,12,31,32")
        [11, 12, 31, 32]
        
        >>> _parse_int_list("11, 12, 31, 32")  # 공백 포함도 가능
        [11, 12, 31, 32]
        
        >>> _parse_int_list("")
        []
        
        >>> _parse_int_list(None)
        []
    """
    # 빈 값 체크
    if not env_value or env_value.strip() == "":
        return []
    
    try:
        # 콤마로 분리 → 공백 제거 → 정수 변환
        return [int(x.strip()) for x in env_value.split(',') if x.strip()]
    except ValueError:
        # 파싱 실패 시 빈 리스트 반환
        return []


def load_config() -> Config:
    """
    환경 변수에서 설정 로드
    
    .env 파일의 환경 변수를 읽어서 Config 객체를 생성합니다.
    환경 변수가 없으면 기본값이 사용됩니다.
    
    Returns:
        Config: 설정 객체
    
    Example:
        .env 파일:
            DB_HOST=192.168.1.100
            DB_PORT=5433
            ENERGY_SLAVE_IDS=11,12,31,32
            ENV_SENSOR_IDS=0,1,2
        
        코드:
            config = load_config()
            print(config.db_host)  # "192.168.1.100"
            print(config.energy_slave_ids)  # [11, 12, 31, 32]
    """
    return Config(
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터베이스 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_port=int(os.getenv('DB_PORT', '5432')),
        db_name=os.getenv('DB_NAME', 'sensor_goseong'),
        db_user=os.getenv('DB_USER', 'postgres'),
        db_password=os.getenv('DB_PASSWORD', '1234'),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 전력량 센서 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        energy_serial_port=os.getenv('ENERGY_SERIAL_PORT', 'COM11'),
        energy_serial_baudrate=int(os.getenv('ENERGY_SERIAL_BAUDRATE', '9600')),
        energy_serial_timeout=int(os.getenv('ENERGY_SERIAL_TIMEOUT', '3')),
        energy_slave_ids=_parse_int_list(os.getenv('ENERGY_SLAVE_IDS')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 환경 센서 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        env_serial_port=os.getenv('ENV_SERIAL_PORT', 'COM11'),
        env_serial_baudrate=int(os.getenv('ENV_SERIAL_BAUDRATE', '9600')),
        env_serial_timeout=int(os.getenv('ENV_SERIAL_TIMEOUT', '1')),
        env_sensor_ids=_parse_int_list(os.getenv('ENV_SENSOR_IDS')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터 수집 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        collection_interval=int(os.getenv('COLLECTION_INTERVAL', '60')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 로깅 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        log_file_path=os.getenv('LOG_FILE_PATH', 'logs/app.log'),
        log_max_bytes=int(os.getenv('LOG_MAX_BYTES', '10485760')),
        log_backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 애플리케이션 정보
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        app_name=os.getenv('APP_NAME', '고성 센서 모니터링 시스템'),
        app_version=os.getenv('APP_VERSION', '1.0.0'),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전역 설정 객체 (싱글톤 패턴)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프로그램 전체에서 하나의 설정 객체만 사용하기 위해
# 싱글톤 패턴을 적용합니다.
_config: Optional[Config] = None


def get_config() -> Config:
    """
    설정 객체 반환 (싱글톤 패턴)
    
    프로그램 실행 중 단 한 번만 설정을 로드하고,
    이후에는 캐시된 설정 객체를 반환합니다.
    
    Returns:
        Config: 설정 객체
    
    Example:
        >>> config = get_config()
        >>> print(config.db_host)
        localhost
        
        >>> config2 = get_config()  # 같은 객체
        >>> config is config2
        True
    """
    global _config
    
    # 최초 호출 시에만 설정 로드
    if _config is None:
        _config = load_config()
    
    return _config


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하위 호환성을 위한 별칭
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기존 코드에서 'settings'를 사용하는 경우를 위한 별칭
settings = get_config()


# ==============================================
# 테스트 코드
# ==============================================
if __name__ == "__main__":
    """
    설정이 올바르게 로드되는지 테스트합니다.
    
    실행:
        python src/core/config.py
    """
    print("=" * 70)
    print("환경 변수 설정 테스트")
    print("=" * 70)
    
    config = get_config()
    
    print("\n[데이터베이스]")
    print(f"  Host: {config.db_host}:{config.db_port}")
    print(f"  Database: {config.db_name}")
    print(f"  User: {config.db_user}")
    
    print("\n[전력량 센서]")
    print(f"  시리얼 포트: {config.energy_serial_port}")
    print(f"  Baudrate: {config.energy_serial_baudrate} bps")
    print(f"  Slave IDs: {config.energy_slave_ids}")
    print(f"  → {len(config.energy_slave_ids or [])}개 센서")
    
    print("\n[환경 센서]")
    print(f"  시리얼 포트: {config.env_serial_port}")
    print(f"  Baudrate: {config.env_serial_baudrate} bps")
    print(f"  Sensor IDs: {config.env_sensor_ids}")
    print(f"  → {len(config.env_sensor_ids or [])}개 센서")
    
    print("\n[데이터 수집]")
    print(f"  수집 주기: {config.collection_interval}초")
    
    print("\n[로깅]")
    print(f"  로그 레벨: {config.log_level}")
    print(f"  로그 파일: {config.log_file_path}")
    print(f"  최대 크기: {config.log_max_bytes / 1024 / 1024:.1f}MB")
    print(f"  백업 개수: {config.log_backup_count}개")
    
    print("\n[애플리케이션]")
    print(f"  이름: {config.app_name}")
    print(f"  버전: {config.app_version}")
    
    print("\n" + "=" * 70)
