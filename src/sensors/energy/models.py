# ==============================================
# 전력량 센서 데이터 모델 (PyInstaller 호환)
# ==============================================
"""
전력량 센서 데이터 모델

테이블 구조:
    1. energy_data_single: 단상 센서 (DDS238-2)
    2. energy_data_three_phase: 3상 센서 (TAC4300)
    
공통 컬럼:
    - id: Primary Key
    - device_id: 장치 ID
    - timestamp: 측정 시각
    - power: 전력 (kW)
    - power_factor: 역률
    - energy_total: 적산전력량 (kWh)

PyInstaller 대응:
- sys.path 조작 제거
- import는 없으므로 수정 불필요
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base 클래스 생성
Base = declarative_base()


class EnergySinglePhase(Base):
    """
    단상 전력량 센서 데이터 모델 (DDS238-2)
    
    테이블명: energy_data_single
    
    센서 사양:
    - 정격 전압: 230V
    - 정격 전류: 5A~60A
    - 전력 측정 범위: 0~13.8kW
    - 정확도: Class 1
    """
    
    __tablename__ = 'energy_data_single'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 컬럼 정의
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Primary Key (자동 증가)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 장치 ID (인덱스)
    device_id = Column(String(50), nullable=False, index=True)
    
    # 측정 시각 (인덱스)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    
    # 전력 (kW)
    power = Column(Float, nullable=False)
    
    # 역률 (0~1)
    power_factor = Column(Float, nullable=False)
    
    # 적산전력량 (kWh)
    energy_total = Column(Float, nullable=False)
    
    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"<EnergySinglePhase("
            f"{self.device_id}, "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"P={self.power:.3f}kW, "
            f"PF={self.power_factor:.3f}, "
            f"E={self.energy_total:.2f}kWh"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'power': self.power,
            'power_factor': self.power_factor,
            'energy_total': self.energy_total
        }


class EnergyThreePhase(Base):
    """
    3상 4선 전력량 센서 데이터 모델 (TAC4300)
    
    테이블명: energy_data_three_phase
    
    센서 사양:
    - 정격 전압: 3상 230V/400V
    - 정격 전류: 5A
    - CT 비율: 최대 9999:5
    - 정확도: Class 0.5S
    """
    
    __tablename__ = 'energy_data_three_phase'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 컬럼 정의
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Primary Key (자동 증가)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 장치 ID (인덱스)
    device_id = Column(String(50), nullable=False, index=True)
    
    # 측정 시각 (인덱스)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    
    # 총 유효전력 (kW)
    # R상 + S상 + T상 합계
    power = Column(Float, nullable=False)
    
    # 역률 (0~1)
    # 3상 평균 역률
    power_factor = Column(Float, nullable=False)
    
    # 적산전력량 (kWh)
    # 3상 합계
    energy_total = Column(Float, nullable=False)
    
    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"<EnergyThreePhase("
            f"{self.device_id}, "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"P={self.power:.3f}kW, "
            f"PF={self.power_factor:.3f}, "
            f"E={self.energy_total:.2f}kWh"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'power': self.power,
            'power_factor': self.power_factor,
            'energy_total': self.energy_total
        }


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 모델 테스트
    
    실행: python src/sensors/energy/models.py
    """
    print("=" * 70)
    print("전력량 센서 데이터 모델")
    print("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 단상 모델 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[단상 센서 모델]")
    single = EnergySinglePhase(
        device_id="Energy_1",
        timestamp=datetime.now(),
        power=1.234,         # kW
        power_factor=0.95,   # 역률
        energy_total=123.45  # kWh
    )
    print(f"  객체: {single}")
    print(f"  딕셔너리: {single.to_dict()}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3상 모델 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[3상 센서 모델]")
    three_phase = EnergyThreePhase(
        device_id="Energy_3",
        timestamp=datetime.now(),
        power=12.345,        # kW
        power_factor=0.98,   # 역률
        energy_total=567.89  # kWh
    )
    print(f"  객체: {three_phase}")
    print(f"  딕셔너리: {three_phase.to_dict()}")
    
    print("\n" + "=" * 70)