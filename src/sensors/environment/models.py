# ==============================================
# 환경 센서 데이터 모델
# ==============================================
"""
환경 센서 데이터 모델 (온도+습도+조도)

테이블 구조:
    env_data: 환경 센서 통합 테이블
    
컬럼:
    - id: Primary Key
    - device_id: 장치 ID
    - timestamp: 측정 시각
    - temperature: 온도 (°C)
    - humidity: 습도 (%)
    - illuminance: 조도 (lux)
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class EnvironmentData(Base):
    """
    환경 센서 데이터 모델
    
    테이블: env_data
    
    센서 사양:
    - 온도: -40°C ~ +80°C (소수점 3자리)
    - 습도: 0 ~ 100% (소수점 1자리)
    - 조도: 0 ~ 99999 lux (정수)
    """
    
    __tablename__ = 'env_data'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 컬럼 정의
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    temperature = Column(Float, nullable=False)      # 온도 (°C)
    humidity = Column(Float, nullable=False)         # 습도 (%)
    illuminance = Column(Float, nullable=False)      # 조도 (lux)
    
    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"<EnvironmentData("
            f"{self.device_id}, "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"T={self.temperature:.3f}°C, "
            f"H={self.humidity:.1f}%, "
            f"L={self.illuminance:.0f}lux"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'illuminance': self.illuminance
        }


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    print("=" * 70)
    print("환경 센서 데이터 모델")
    print("=" * 70)
    
    # 모델 테스트
    print("\n[환경 센서 모델]")
    env = EnvironmentData(
        device_id="Env_1",
        timestamp=datetime.now(),
        temperature=10.206,     # °C
        humidity=16.8,          # %
        illuminance=48          # lux
    )
    print(f"  객체: {env}")
    print(f"  딕셔너리: {env.to_dict()}")
