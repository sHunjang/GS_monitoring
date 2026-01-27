# ==============================================
# 데이터베이스 연결 및 Operations (PyInstaller 호환)
# ==============================================
"""
데이터베이스 연결 및 작업 함수

PyInstaller 대응:
    - 조건부 import로 경로 문제 해결
    - 명시적 모델 import로 동적 import 제거
"""

import os
import sys
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Config import (조건부 - PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PyInstaller 빌드 시와 일반 실행 시 모두 작동하도록
# 여러 경로를 순차적으로 시도
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 모델 import (명시적 - PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 기존 문제: database.py에서 함수 내부에서 동적으로 import했음
# 해결: 파일 상단에서 명시적으로 import

try:
    # 첫 번째 시도: sensors 패키지에서 직접 import
    from sensors.energy.models import EnergySinglePhase, EnergyThreePhase
    from sensors.environment.models import EnvironmentData
    print("✅ 모델 import 성공 (패키지)")
except ImportError:
    try:
        # 두 번째 시도: 상대 경로로 import
        import importlib
        
        # 전력 센서 모델
        energy_module = importlib.import_module('sensors.energy.models')
        EnergySinglePhase = energy_module.EnergySinglePhase
        EnergyThreePhase = energy_module.EnergyThreePhase
        
        # 환경 센서 모델
        env_module = importlib.import_module('sensors.environment.models')
        EnvironmentData = env_module.EnvironmentData
        
        print("✅ 모델 import 성공 (동적)")
    except Exception as e:
        # import 실패 시 에러 메시지 출력
        print(f"⚠️  모델 import 실패: {e}")
        print("💡 센서 데이터 저장 기능이 제한될 수 있습니다")
        # 더미 클래스 생성 (프로그램이 죽지 않도록)
        class EnergySinglePhase:
            pass
        class EnergyThreePhase:
            pass
        class EnvironmentData:
            pass


logger = logging.getLogger(__name__)

# 설정 로드
config = get_config()


# ==============================================
# 데이터베이스 엔진 생성
# ==============================================

# PostgreSQL 연결 문자열 생성
# 형식: postgresql://사용자:비밀번호@호스트:포트/데이터베이스명
DATABASE_URL = (
    f"postgresql://{config.db_user}:{config.db_password}"
    f"@{config.db_host}:{config.db_port}/{config.db_name}"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=False,              # SQL 쿼리 로그 출력 안 함
    pool_size=5,             # 커넥션 풀 크기
    max_overflow=10,         # 최대 추가 연결 수
    pool_pre_ping=True       # 연결 전 DB 상태 확인
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False,        # 자동 커밋 비활성화
    autoflush=False,         # 자동 flush 비활성화
    bind=engine              # 엔진 바인딩
)


# ==============================================
# 세션 관리
# ==============================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 생성 (Context Manager)
    
    사용 예:
        with get_db_session() as session:
            session.add(data)
            # 자동으로 commit 또는 rollback
    
    Yields:
        Session: SQLAlchemy 세션
    """
    # 세션 생성
    session = SessionLocal()
    try:
        # 세션을 사용자에게 전달
        yield session
        # 정상 종료 시 커밋
        session.commit()
    except Exception as e:
        # 오류 발생 시 롤백
        session.rollback()
        logger.error(f"데이터베이스 오류: {e}")
        # 오류를 다시 발생시켜 호출자가 처리하도록
        raise
    finally:
        # 항상 세션 닫기
        session.close()


# ==============================================
# 연결 테스트
# ==============================================

def test_db_connection() -> bool:
    """
    데이터베이스 연결 테스트
    
    프로그램 시작 시 DB 연결 가능 여부 확인용
    
    Returns:
        bool: 연결 성공하면 True, 실패하면 False
    """
    try:
        # 연결 생성 후 간단한 쿼리 실행
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # 성공 로그
        logger.info(
            f"✓ 데이터베이스 연결 성공: "
            f"{config.db_host}:{config.db_port}/{config.db_name}"
        )
        return True
    
    except SQLAlchemyError as e:
        # 실패 로그
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
        bool: 저장 성공하면 True
    """
    try:
        # 타임스탬프가 없으면 현재 시각 사용
        if timestamp is None:
            timestamp = datetime.now()
        
        # 모델 객체 생성
        data = EnergySinglePhase(
            device_id=device_id,
            timestamp=timestamp,
            power=power,
            power_factor=power_factor,
            energy_total=energy_total
        )
        
        # DB에 저장
        with get_db_session() as session:
            session.add(data)
        
        # 디버그 로그
        logger.debug(
            f"[{device_id}] 단상 데이터 저장: "
            f"P={power:.3f}kW, PF={power_factor:.3f}, E={energy_total:.2f}kWh"
        )
        return True
    
    except Exception as e:
        # 오류 로그
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
        bool: 저장 성공하면 True
    """
    try:
        # 타임스탬프가 없으면 현재 시각 사용
        if timestamp is None:
            timestamp = datetime.now()
        
        # 모델 객체 생성
        data = EnergyThreePhase(
            device_id=device_id,
            timestamp=timestamp,
            power=power,
            power_factor=power_factor,
            energy_total=energy_total
        )
        
        # DB에 저장
        with get_db_session() as session:
            session.add(data)
        
        # 디버그 로그
        logger.debug(
            f"[{device_id}] 3상 데이터 저장: "
            f"P={power:.3f}kW, PF={power_factor:.3f}, E={energy_total:.2f}kWh"
        )
        return True
    
    except Exception as e:
        # 오류 로그
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
        timestamp: 측정 시각 (None이면 현재 시각)
    
    Returns:
        bool: 저장 성공하면 True
    """
    try:
        # 타임스탬프가 없으면 현재 시각 사용
        if timestamp is None:
            timestamp = datetime.now()
        
        # 모델 객체 생성
        data = EnvironmentData(
            device_id=device_id,
            timestamp=timestamp,
            temperature=temperature,
            humidity=humidity,
            illuminance=illuminance
        )
        
        # DB에 저장
        with get_db_session() as session:
            session.add(data)
        
        # 디버그 로그
        logger.debug(
            f"[{device_id}] 환경 데이터 저장: "
            f"{temperature:.1f}°C, {humidity:.1f}%, {illuminance:.0f}lux"
        )
        return True
    
    except Exception as e:
        # 오류 로그
        logger.error(f"[{device_id}] 환경 데이터 저장 실패: {e}")
        return False


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 DB 연결 테스트
    
    실행: python src/core/database.py
    """
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