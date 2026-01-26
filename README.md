# 🔌 센서 모니터링 시스템

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

고성 전력 및 환경 센서 통합 모니터링 시스템

실시간으로 전력량과 환경 데이터(온도, 습도, 조도)를 수집하고 시각화하는 PyQt5 기반 데스크톱 애플리케이션입니다.

---

## 📋 목차

- [주요 기능](#-주요-기능)
- [시스템 아키텍처](#-시스템-아키텍처)
- [지원 센서](#-지원-센서)
- [기술 스택](#-기술-스택)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [프로젝트 구조](#-프로젝트-구조)
- [환경 설정](#-환경-설정)
- [배포](#-배포)
- [문서](#-문서)
- [라이선스](#-라이선스)

---

## ✨ 주요 기능

### 🎯 핵심 기능

- **실시간 모니터링**: PyQt5 기반 직관적인 대시보드로 센서 데이터 실시간 확인
- **멀티 센서 지원**: 전력 센서와 환경 센서를 하나의 시스템에서 통합 관리
- **자동 데이터 수집**: 설정 가능한 주기로 백그라운드 자동 수집
- **데이터베이스 저장**: PostgreSQL에 안정적으로 데이터 저장 및 이력 관리
- **포트 공유 관리**: RS-485 버스의 포트 충돌 방지 및 순차 접근 보장

### 📊 모니터링 대시보드

- 전력량 실시간 그래프 (pyqtgraph)
- 환경 데이터 차트 (온도, 습도, 조도)
- 센서 상태 모니터링
- 알람 및 이상치 감지

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│            PyQt5 Main Window (UI)              │
│     ┌─────────────┐    ┌──────────────┐       │
│     │  전력 대시보드 │    │ 환경 대시보드 │       │
│     └─────────────┘    └──────────────┘       │
└──────────────┬──────────────────┬──────────────┘
               │                  │
               ▼                  ▼
    ┌──────────────────┐ ┌──────────────────┐
    │ Energy Collector │ │  Env Collector   │
    │  (Background)    │ │  (Background)    │
    └────────┬─────────┘ └─────────┬────────┘
             │                     │
             └──────────┬──────────┘
                        ▼
              ┌──────────────────┐
              │ SerialBusManager │
              │   (Port Sharing) │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   RS-485 Bus     │
              │  (COM Port)      │
              └────────┬─────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   [전력센서1]      [전력센서2]     [환경센서1]
   (Modbus RTU)   (Modbus RTU)   (ASCII Protocol)
```

### 핵심 설계

- **포트 공유**: `SerialBusManager`가 threading.Lock으로 포트 충돌 방지
- **비동기 수집**: 백그라운드 스레드에서 독립적으로 데이터 수집
- **UI 분리**: 메인 스레드는 UI 렌더링에만 집중
- **확장성**: 센서 추가/삭제가 `.env` 파일만으로 가능

---

## 🔧 지원 센서

### ⚡ 전력 센서 (Modbus RTU)

| 모델 | 타입 | Slave ID 범위 | 프로토콜 |
|------|------|---------------|----------|
| DDS238 | 단상 전력계 | < 30 | Modbus RTU |
| TAC4300 | 3상 전력계 | ≥ 30 | Modbus RTU |

**측정 항목**: 전압, 전류, 전력, 누적 전력량

### 🌡️ 환경 센서 (ASCII Protocol)

| 측정값 | 단위 | 범위 |
|--------|------|------|
| 온도 | °C | -40 ~ 80 |
| 습도 | % | 0 ~ 100 |
| 조도 | lux | 0 ~ 10000 |

**통신**: RS-485 ASCII 프로토콜 (센서 ID: 0x30, 0x31, 0x32, ...)

---

## 🛠️ 기술 스택

### Frontend
- **PyQt5**: 크로스 플랫폼 GUI 프레임워크
- **pyqtgraph**: 고성능 실시간 그래프
- **PyQt6-Charts**: 데이터 시각화

### Backend
- **Python 3.8+**: 메인 언어
- **SQLAlchemy 2.0**: ORM
- **PostgreSQL**: 데이터베이스
- **Pydantic**: 설정 관리 및 검증

### 통신
- **pymodbus**: Modbus RTU 프로토콜
- **pyserial**: 시리얼 통신

### 데이터 처리
- **pandas**: 데이터 분석
- **numpy**: 수치 연산

### 로깅
- **loguru**: 고급 로깅 시스템

---

## 📦 설치 방법

### 1. 사전 요구사항

- Python 3.8 이상
- PostgreSQL 12 이상
- RS-485 to USB 컨버터 (하드웨어)

### 2. 저장소 클론

\`\`\`bash
git clone https://github.com/yourusername/sensor-monitoring-system.git
cd sensor-monitoring-system
\`\`\`

### 3. 가상 환경 생성 및 활성화

\`\`\`bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
\`\`\`

### 4. 의존성 설치

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 5. 환경 변수 설정

\`\`\`bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일을 편집기로 열어 설정 수정
notepad .env  # Windows
nano .env     # Linux/Mac
\`\`\`

**필수 설정 항목**:
- 데이터베이스 연결 정보
- 시리얼 포트 번호
- 센서 ID 목록

### 6. 데이터베이스 초기화

\`\`\`bash
python scripts/init_db.py
\`\`\`

---

## 🚀 사용 방법

### GUI 모드 실행

\`\`\`bash
python src/main_gui.py
\`\`\`

### CLI 모드 실행 (백그라운드 수집만)

\`\`\`bash
python src/main.py
\`\`\`

### 종료 방법

- **GUI**: 창 닫기 버튼 클릭
- **CLI**: `Ctrl + C`

---

## 📂 프로젝트 구조

\`\`\`
sensor-monitoring-system/
│
├── database/                # 데이터베이스 관련
│   ├── init.sql            # 초기 스키마
│   └── migrations/         # 마이그레이션 파일
│
├── docs/                   # 문서
│   ├── ADD_SENSOR.md       # 센서 추가 가이드
│   ├── DEPLOYMENT.md       # 배포 가이드
│   └── SETUP.md            # 설치 가이드
│
├── logs/                   # 로그 파일
│   └── app.log
│
├── resources/              # 리소스 (아이콘, 이미지 등)
│
├── scripts/                # 유틸리티 스크립트
│   ├── build.py           # 빌드 스크립트
│   └── init_db.py         # DB 초기화
│
├── src/                    # 소스 코드
│   ├── main.py            # CLI 진입점
│   ├── main_gui.py        # GUI 진입점
│   │
│   ├── core/              # 핵심 모듈
│   │   ├── config.py      # 설정 관리
│   │   ├── database.py    # DB 연결
│   │   ├── logging_config.py  # 로깅 설정
│   │   └── modbus_manager.py  # Modbus 관리
│   │
│   ├── sensors/           # 센서 모듈
│   │   ├── energy/        # 전력 센서
│   │   │   ├── collector.py
│   │   │   ├── models.py
│   │   │   ├── protocols.py
│   │   │   ├── reader.py
│   │   │   └── service.py
│   │   │
│   │   └── environment/   # 환경 센서
│   │       ├── collector.py
│   │       ├── models.py
│   │       ├── reader.py
│   │       └── service.py
│   │
│   ├── services/          # 비즈니스 로직
│   │   └── ui_data_service.py
│   │
│   └── ui/                # UI 컴포넌트
│       ├── main_window.py
│       └── theme.py
│
├── .env.example           # 환경 변수 템플릿
├── .gitignore
├── requirements.txt       # Python 의존성
├── SensorMonitoring.spec  # PyInstaller 설정
└── README.md
\`\`\`

---

## ⚙️ 환경 설정

### .env 파일 예시

\`\`\`env
# 애플리케이션 정보
APP_NAME=센서 모니터링 시스템
APP_VERSION=1.0.0

# 데이터베이스
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sensor_monitoring
DB_USER=postgres
DB_PASSWORD=yourpassword

# 전력 센서 (Modbus RTU)
ENERGY_SERIAL_PORT=COM3
ENERGY_SERIAL_BAUDRATE=9600
ENERGY_SLAVE_IDS=11,12,31,32  # 쉼표로 구분

# 환경 센서 (ASCII Protocol)
ENV_SERIAL_PORT=COM3          # 전력 센서와 포트 공유
ENV_SERIAL_BAUDRATE=9600
ENV_SENSOR_IDS=0,1,2          # 쉼표로 구분

# 수집 주기 (초)
COLLECTION_INTERVAL=5
\`\`\`

### 센서 추가 방법

1. `.env` 파일 열기
2. 해당 센서 타입의 ID 목록에 추가
   - 전력 센서: `ENERGY_SLAVE_IDS`에 Slave ID 추가
   - 환경 센서: `ENV_SENSOR_IDS`에 센서 ID 추가
3. 프로그램 재시작

**예시**: 전력 센서 1개 추가 (Slave ID 33)
\`\`\`env
# 변경 전
ENERGY_SLAVE_IDS=11,12,31,32

# 변경 후
ENERGY_SLAVE_IDS=11,12,31,32,33
\`\`\`

자세한 내용은 [docs/ADD_SENSOR.md](docs/ADD_SENSOR.md) 참조

---

## 📦 배포

### Windows EXE 파일 생성

PyInstaller를 사용하여 독립 실행 파일을 생성할 수 있습니다.

\`\`\`bash
# spec 파일로 빌드
pyinstaller SensorMonitoring.spec

# 클린 빌드
pyinstaller --clean SensorMonitoring.spec
\`\`\`

**빌드 결과물**: \`dist/SensorMonitoring/SensorMonitoring.exe\`

### 배포 시 주의사항

1. **환경 변수 파일**: \`.env\` 파일은 사용자가 직접 생성해야 함
   - 배포 시 \`.env.example\`만 포함
   - 사용자에게 설정 가이드 제공

2. **데이터베이스**: PostgreSQL이 설치되어 있어야 함

3. **하드웨어**: RS-485 to USB 컨버터 드라이버 설치 필요

자세한 내용은 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) 참조

---

## 📚 문서

- [설치 가이드](docs/SETUP.md): 상세 설치 방법
- [센서 추가](docs/ADD_SENSOR.md): 새 센서 등록 방법
- [배포 가이드](docs/DEPLOYMENT.md): EXE 파일 배포 방법

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!

1. Fork the Project
2. Create your Feature Branch (\`git checkout -b feature/AmazingFeature\`)
3. Commit your Changes (\`git commit -m 'Add some AmazingFeature'\`)
4. Push to the Branch (\`git push origin feature/AmazingFeature\`)
5. Open a Pull Request

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 👤 작성자

**SoloWins - AI Developer**

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 📌 버전 히스토리

### v1.0.0 (2026-01-26)
- ✨ 초기 릴리스
- ✅ 전력 센서 통합 (Modbus RTU)
- ✅ 환경 센서 통합 (ASCII Protocol)
- ✅ PyQt5 기반 실시간 대시보드
- ✅ PostgreSQL 데이터 저장
- ✅ PyInstaller 배포 지원

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 라이브러리를 사용합니다:

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크
- [pymodbus](https://github.com/pymodbus-dev/pymodbus) - Modbus 통신
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [loguru](https://github.com/Delgan/loguru) - 로깅 시스템
