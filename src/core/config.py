# ==============================================
# 환경 변수 설정 모듈 (PyInstaller 호환)
# ==============================================
"""
.env 파일에서 환경 변수를 읽어서 애플리케이션 전역에서 사용

PyInstaller 대응:
    - exe 실행 시 .env 파일 위치 자동 탐색
    - sys.executable 기준 경로 사용
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 실행 환경 감지 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_base_path() -> Path:
    """
    실행 환경에 따른 기본 경로 반환
    
    - PyInstaller exe: exe 파일이 있는 폴더
    - 일반 Python: 프로젝트 루트 폴더
    """
    # PyInstaller로 빌드된 exe인지 확인
    if getattr(sys, 'frozen', False):
        # exe 실행 시: sys.executable = exe 파일 경로
        # exe 파일이 있는 폴더를 반환
        base = Path(sys.executable).parent
        print(f"🔧 PyInstaller 실행 모드: {base}")
        return base
    else:
        # 일반 Python 실행 시
        # 현재 파일(config.py) 기준으로 3단계 위 (프로젝트 루트)
        base = Path(__file__).parent.parent.parent
        print(f"🐍 Python 실행 모드: {base}")
        return base


def get_env_path() -> Path:
    """
    .env 파일 경로 반환
    
    - exe 실행: exe와 같은 폴더의 .env
    - Python 실행: 프로젝트 루트의 .env
    """
    base = get_base_path()
    env_path = base / '.env'
    
    # 디버깅용 출력
    print(f"🔍 .env 파일 경로: {env_path}")
    print(f"🔍 .env 파일 존재: {env_path.exists()}")
    
    return env_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# .env 파일 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

env_path = get_env_path()

if env_path.exists():
    # .env 파일이 있으면 로드
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드 완료")
else:
    # .env 파일이 없으면 경고 (기본값 사용)
    print(f"⚠️  .env 파일 없음 - 기본값 사용")
    print(f"💡 .env 파일을 exe와 같은 폴더에 배치하세요")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정 클래스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class Config:
    """
    애플리케이션 설정 클래스
    
    .env 파일의 환경 변수를 담는 컨테이너
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터베이스 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    db_host: str = "localhost"          # DB 서버 주소
    db_port: int = 5432                  # DB 포트
    db_name: str = "sensor_goseong"      # DB 이름
    db_user: str = "postgres"            # DB 사용자
    db_password: str = "1234"            # DB 비밀번호
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력량 센서 설정 (Modbus RTU)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    energy_serial_port: str = "COM7"     # 시리얼 포트
    energy_serial_baudrate: int = 9600   # 통신 속도
    energy_serial_timeout: int = 3       # 타임아웃 (초)
    energy_slave_ids: List[int] = field(default_factory=list)  # Slave ID 목록
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 환경 센서 설정 (ASCII Protocol)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    env_serial_port: str = "COM7"        # 시리얼 포트
    env_serial_baudrate: int = 9600      # 통신 속도
    env_serial_timeout: int = 1          # 타임아웃 (초)
    env_sensor_ids: List[int] = field(default_factory=list)  # 센서 ID 목록
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터 수집 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    collection_interval: int = 60        # 수집 주기 (초)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로깅 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    log_level: str = "INFO"              # 로그 레벨
    log_file_path: str = "logs/app.log"  # 로그 파일 경로
    log_max_bytes: int = 10485760        # 최대 크기 (10MB)
    log_backup_count: int = 5            # 백업 개수
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애플리케이션 정보
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    app_name: str = "고성 센서 모니터링 시스템"
    app_version: str = "1.0.0"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬퍼 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _parse_int_list(env_value: Optional[str]) -> List[int]:
    """
    콤마로 구분된 문자열을 정수 리스트로 변환
    
    예: "11,12,31,32" → [11, 12, 31, 32]
    """
    # 빈 값이면 빈 리스트 반환
    if not env_value or env_value.strip() == "":
        return []
    
    try:
        # 콤마로 분리 → 공백 제거 → 정수 변환
        return [int(x.strip()) for x in env_value.split(',') if x.strip()]
    except ValueError:
        # 파싱 실패 시 빈 리스트
        return []


def load_config() -> Config:
    """
    환경 변수에서 설정 로드
    
    .env 파일의 값을 읽어 Config 객체 생성
    환경 변수가 없으면 기본값 사용
    """
    return Config(
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터베이스 설정 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_port=int(os.getenv('DB_PORT', '5432')),
        db_name=os.getenv('DB_NAME', 'sensor_goseong'),
        db_user=os.getenv('DB_USER', 'postgres'),
        db_password=os.getenv('DB_PASSWORD', '1234'),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 전력량 센서 설정 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        energy_serial_port=os.getenv('ENERGY_SERIAL_PORT', 'COM7'),
        energy_serial_baudrate=int(os.getenv('ENERGY_SERIAL_BAUDRATE', '9600')),
        energy_serial_timeout=int(os.getenv('ENERGY_SERIAL_TIMEOUT', '3')),
        # "11,12,31,32" 형태를 [11,12,31,32]로 변환
        energy_slave_ids=_parse_int_list(os.getenv('ENERGY_SLAVE_IDS')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 환경 센서 설정 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        env_serial_port=os.getenv('ENV_SERIAL_PORT', 'COM7'),
        env_serial_baudrate=int(os.getenv('ENV_SERIAL_BAUDRATE', '9600')),
        env_serial_timeout=int(os.getenv('ENV_SERIAL_TIMEOUT', '1')),
        # "0,1" 형태를 [0,1]로 변환
        env_sensor_ids=_parse_int_list(os.getenv('ENV_SENSOR_IDS')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터 수집 설정 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        collection_interval=int(os.getenv('COLLECTION_INTERVAL', '60')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 로깅 설정 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        log_file_path=os.getenv('LOG_FILE_PATH', 'logs/app.log'),
        log_max_bytes=int(os.getenv('LOG_MAX_BYTES', '10485760')),
        log_backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 애플리케이션 정보 읽기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        app_name=os.getenv('APP_NAME', '고성 센서 모니터링 시스템'),
        app_version=os.getenv('APP_VERSION', '1.0.0'),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전역 설정 객체 (싱글톤 패턴)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 프로그램 전체에서 하나의 설정 객체만 사용
_config: Optional[Config] = None


def get_config() -> Config:
    """
    설정 객체 반환 (싱글톤 패턴)
    
    최초 호출 시에만 설정 로드
    이후에는 캐시된 객체 반환
    """
    global _config
    
    # 아직 로드 안 했으면 로드
    if _config is None:
        _config = load_config()
        # 로드 완료 메시지 출력
        print(f"✅ Config 로드 완료")
        print(f"  - DB: {_config.db_host}:{_config.db_port}/{_config.db_name}")
        print(f"  - 전력 센서: {len(_config.energy_slave_ids)}개")
        print(f"  - 환경 센서: {len(_config.env_sensor_ids)}개")
    
    return _config


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하위 호환성을 위한 별칭
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 기존 코드에서 'settings'를 사용하는 경우를 위한 별칭
settings = get_config()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 코드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 설정값을 출력
    
    실행: python src/core/config.py
    """
    config = get_config()
    
    print("=" * 70)
    print("환경 변수 설정")
    print("=" * 70)
    
    print("\n[데이터베이스]")
    print(f"  Host: {config.db_host}:{config.db_port}")
    print(f"  Database: {config.db_name}")
    print(f"  User: {config.db_user}")
    
    print("\n[전력량 센서]")
    print(f"  포트: {config.energy_serial_port}")
    print(f"  Slave IDs: {config.energy_slave_ids}")
    
    print("\n[환경 센서]")
    print(f"  포트: {config.env_serial_port}")
    print(f"  Sensor IDs: {config.env_sensor_ids}")
    
    print("\n=" * 70)