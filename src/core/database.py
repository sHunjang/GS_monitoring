# ==============================================
# 데이터베이스 연결 및 Operations
# ==============================================
# 역할: PostgreSQL 연결 + CRUD 함수

"""
데이터베이스 연결 및 작업 함수

기능:
    1. PostgreSQL 연결 관리
    2. 세션 생성 (Context Manager)
    3. 데이터 삽입 함수
"""

import sys
from pathlib import Path
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import get_config  # 수정!

# 설정 로드
config = get_config()
logger = logging.getLogger(__name__)


# ==============================================
# 데이터베이스 엔진 생성
# ==============================================

DATABASE_URL = (
    f"postgresql://{config.db_user}:{config.db_password}"
    f"@{config.db_host}:{config.db_port}/{config.db_name}"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==============================================
# 세션 관리
# ==============================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 생성 (Context Manager)
    
    Yields:
        Session: SQLAlchemy 세션
    
    Example:
        >>> with get_db_session() as session:
        ...     session.add(data)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"데이터베이스 오류: {e}")
        raise
    finally:
        session.close()


# ==============================================
# 연결 테스트
# ==============================================

def test_db_connection() -> bool:
    """
    데이터베이스 연결 테스트
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info(
            f"✓ 데이터베이스 연결 성공: "
            f"{config.db_host}:{config.db_port}/{config.db_name}"
        )
        return True
    
    except SQLAlchemyError as e:
        logger.error(f"✗ 데이터베이스 연결 실패: {e}")
        return False


# ==============================================
# CRUD Operations - 단상 센서
# ==============================================

def insert_single_phase_data(
    device_id: str,
    power: float,
    power_factor: float,
    energy_total: float,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    단상 전력량 센서 데이터 삽입
    
    Args:
        device_id: 장치 ID (예: "Energy_1")
        power: 전력 (kW)
        power_factor: 역률 (0~1)
        energy_total: 적산전력량 (kWh)
        timestamp: 측정 시각 (None이면 현재 시각)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from sensors.energy.models import EnergySinglePhase
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data = EnergySinglePhase(
            device_id=device_id,
            timestamp=timestamp,
            power=power,
            power_factor=power_factor,
            energy_total=energy_total
        )
        
        with get_db_session() as session:
            session.add(data)
        
        logger.debug(
            f"[{device_id}] 단상 데이터 저장: "
            f"P={power:.3f}kW, PF={power_factor:.3f}, E={energy_total:.2f}kWh"
        )
        return True
    
    except Exception as e:
        logger.error(f"[{device_id}] 단상 데이터 저장 실패: {e}")
        return False


# ==============================================
# CRUD Operations - 3상 센서
# ==============================================

def insert_three_phase_data(
    device_id: str,
    power: float,
    power_factor: float,
    energy_total: float,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    3상 전력량 센서 데이터 삽입
    
    Args:
        device_id: 장치 ID (예: "Energy_3")
        power: 총 유효전력 (kW)
        power_factor: 역률 (0~1)
        energy_total: 적산전력량 (kWh)
        timestamp: 측정 시각 (None이면 현재 시각)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from sensors.energy.models import EnergyThreePhase
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data = EnergyThreePhase(
            device_id=device_id,
            timestamp=timestamp,
            power=power,
            power_factor=power_factor,
            energy_total=energy_total
        )
        
        with get_db_session() as session:
            session.add(data)
        
        logger.debug(
            f"[{device_id}] 3상 데이터 저장: "
            f"P={power:.3f}kW, PF={power_factor:.3f}, E={energy_total:.2f}kWh"
        )
        return True
    
    except Exception as e:
        logger.error(f"[{device_id}] 3상 데이터 저장 실패: {e}")
        return False


# ==============================================
# CRUD Operations - 환경 센서
# ==============================================

def insert_environment_data(
    device_id: str,
    temperature: float,
    humidity: float,
    illuminance: float,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    환경 센서 데이터 삽입
    
    Args:
        device_id: 장치 ID (예: "Env_1")
        temperature: 온도 (°C)
        humidity: 습도 (%)
        illuminance: 조도 (lux)
        timestamp: 측정 시각
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from sensors.environment.models import EnvironmentData
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data = EnvironmentData(
            device_id=device_id,
            timestamp=timestamp,
            temperature=temperature,
            humidity=humidity,
            illuminance=illuminance
        )
        
        with get_db_session() as session:
            session.add(data)
        
        logger.debug(
            f"[{device_id}] 환경 데이터 저장: "
            f"{temperature:.1f}°C, {humidity:.1f}%, {illuminance:.0f}lux"
        )
        return True
    
    except Exception as e:
        logger.error(f"[{device_id}] 환경 데이터 저장 실패: {e}")
        return False


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("데이터베이스 연결 테스트")
    print("=" * 70)
    
    if test_db_connection():
        print("✓ 연결 성공!")
        
        # 테스트 데이터 삽입
        print("\n테스트 데이터 삽입...")
        
        success1 = insert_single_phase_data(
            device_id="Energy_TEST_1",
            power=1.234,
            power_factor=0.95,
            energy_total=123.45
        )
        
        success2 = insert_three_phase_data(
            device_id="Energy_TEST_3",
            power=12.345,
            power_factor=0.98,
            energy_total=567.89
        )
        
        if success1 and success2:
            print("✓ 테스트 데이터 저장 성공!")
    else:
        print("✗ 연결 실패")
