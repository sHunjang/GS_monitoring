# ==============================================
# 전력량 센서 데이터 모델
# ==============================================
# 역할: 단상/3상 테이블 ORM 모델 정의

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
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EnergySinglePhase(Base):
    """
    단상 전력량 센서 데이터 모델 (DDS238-2)
    
    테이블: energy_data_single
    """
    
    __tablename__ = 'energy_data_single'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    power = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=False)
    energy_total = Column(Float, nullable=False)
    
    def __repr__(self) -> str:
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
    
    테이블: energy_data_three_phase
    """
    
    __tablename__ = 'energy_data_three_phase'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    power = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=False)
    energy_total = Column(Float, nullable=False)
    
    def __repr__(self) -> str:
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
    print("=" * 70)
    print("전력량 센서 데이터 모델")
    print("=" * 70)
    
    # 단상 모델 테스트
    print("\n[단상 센서 모델]")
    single = EnergySinglePhase(
        device_id="Energy_1",
        timestamp=datetime.now(),
        power=1.234,         # kW
        power_factor=0.95,
        energy_total=123.45  # kWh
    )
    print(f"  객체: {single}")
    print(f"  딕셔너리: {single.to_dict()}")
    
    # 3상 모델 테스트
    print("\n[3상 센서 모델]")
    three_phase = EnergyThreePhase(
        device_id="Energy_3",
        timestamp=datetime.now(),
        power=12.345,        # kW
        power_factor=0.98,
        energy_total=567.89  # kWh
    )
    print(f"  객체: {three_phase}")
    print(f"  딕셔너리: {three_phase.to_dict()}")
