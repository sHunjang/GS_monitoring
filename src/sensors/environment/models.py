# ==============================================
# 환경 센서 데이터 모델 (PyInstaller 호환)
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

PyInstaller 대응:
- sys.path 조작 제거
- import 없음
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class EnvironmentData(Base):
    """
    환경 센서 데이터 모델
    
    테이블명: env_data
    
    센서 사양:
    - 온도: -40°C ~ +80°C (정확도: ±0.3°C)
    - 습도: 0 ~ 100% (정확도: ±2%)
    - 조도: 0 ~ 99999 lux
    """
    
    __tablename__ = 'env_data'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 컬럼 정의
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Primary Key (자동 증가)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 장치 ID (인덱스)
    device_id = Column(String(50), nullable=False, index=True)
    
    # 측정 시각 (인덱스)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    
    # 온도 (°C, 소수점 3자리)
    temperature = Column(Float, nullable=False)
    
    # 습도 (%, 소수점 1자리)
    humidity = Column(Float, nullable=False)
    
    # 조도 (lux, 정수)
    illuminance = Column(Float, nullable=False)
    
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
    """
    이 파일을 직접 실행하면 모델 테스트
    
    실행: python src/sensors/environment/models.py
    """
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
    
    print("\n" + "=" * 70)