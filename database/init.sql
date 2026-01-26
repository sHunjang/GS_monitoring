-- ==============================================
-- 센서 모니터링 시스템 데이터베이스 초기화
-- ==============================================
-- 프로젝트: 고성 센서 모니터링 시스템
-- 작성일: 2026-01-22

-- ==============================================
-- 1. 단상 전력량 센서 테이블 (DDS238-2)
-- ==============================================

DROP TABLE IF EXISTS energy_data_single CASCADE;

CREATE TABLE energy_data_single (
    -- 기본 키
    id BIGSERIAL PRIMARY KEY,
    
    -- 장치 ID (예: "Energy_1", "Energy_2")
    device_id VARCHAR(50) NOT NULL,
    
    -- 측정 시각
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 전력 (kW)
    power FLOAT NOT NULL,
    
    -- 역률 (0~1)
    power_factor FLOAT NOT NULL,
    
    -- 전력량 (kWh)
    energy_total FLOAT NOT NULL
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX idx_single_device_time ON energy_data_single(device_id, timestamp DESC);
CREATE INDEX idx_single_timestamp ON energy_data_single(timestamp DESC);

-- 테이블 및 컬럼 설명
COMMENT ON TABLE energy_data_single IS '단상 전력량 센서 데이터 (DDS238-2)';
COMMENT ON COLUMN energy_data_single.id IS '고유 ID';
COMMENT ON COLUMN energy_data_single.device_id IS '센서 장치 ID';
COMMENT ON COLUMN energy_data_single.timestamp IS '측정 시각';
COMMENT ON COLUMN energy_data_single.power IS '전력 (kW)';
COMMENT ON COLUMN energy_data_single.power_factor IS '역률 (0~1)';
COMMENT ON COLUMN energy_data_single.energy_total IS '적산전력량 (kWh)';


-- ==============================================
-- 2. 3상 4선 전력량 센서 테이블 (TAC4300)
-- ==============================================

DROP TABLE IF EXISTS energy_data_three_phase CASCADE;

CREATE TABLE energy_data_three_phase (
    -- 기본 키
    id BIGSERIAL PRIMARY KEY,
    
    -- 장치 ID (예: "Energy_3", "Energy_4")
    device_id VARCHAR(50) NOT NULL,
    
    -- 측정 시각
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 전력 (kW)
    power FLOAT NOT NULL,
    
    -- 역률 (0~1)
    power_factor FLOAT NOT NULL,
    
    -- 전력량 (kWh)
    energy_total FLOAT NOT NULL
);

-- 인덱스 생성
CREATE INDEX idx_three_phase_device_time ON energy_data_three_phase(device_id, timestamp DESC);
CREATE INDEX idx_three_phase_timestamp ON energy_data_three_phase(timestamp DESC);

-- 테이블 및 컬럼 설명
COMMENT ON TABLE energy_data_three_phase IS '3상 4선 전력량 센서 데이터 (TAC4300)';
COMMENT ON COLUMN energy_data_three_phase.id IS '고유 ID';
COMMENT ON COLUMN energy_data_three_phase.device_id IS '센서 장치 ID';
COMMENT ON COLUMN energy_data_three_phase.timestamp IS '측정 시각';
COMMENT ON COLUMN energy_data_three_phase.power IS '총 유효전력 (kW)';
COMMENT ON COLUMN energy_data_three_phase.power_factor IS '역률 (0~1)';
COMMENT ON COLUMN energy_data_three_phase.energy_total IS '적산전력량 (kWh)';


-- ==============================================
-- 3. 환경 센서 테이블 (온도/습도/조도)
-- ==============================================

DROP TABLE IF EXISTS env_data CASCADE;

CREATE TABLE env_data (
    -- 기본 키
    id BIGSERIAL PRIMARY KEY,
    
    -- 장치 ID
    device_id VARCHAR(50) NOT NULL,
    
    -- 측정 시각
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 온도 (°C)
    temperature FLOAT NOT NULL,
    
    -- 습도 (%)
    humidity FLOAT NOT NULL,
    
    -- 조도 (lux)
    illuminance FLOAT NOT NULL
);

-- 인덱스 생성
CREATE INDEX idx_env_device_time ON env_data(device_id, timestamp DESC);
CREATE INDEX idx_env_timestamp ON env_data(timestamp DESC);

-- 테이블 및 컬럼 설명
COMMENT ON TABLE env_data IS '환경 센서 데이터 (온도/습도/조도)';
COMMENT ON COLUMN env_data.id IS '고유 ID';
COMMENT ON COLUMN env_data.device_id IS '센서 장치 ID';
COMMENT ON COLUMN env_data.timestamp IS '측정 시각';
COMMENT ON COLUMN env_data.temperature IS '온도 (°C)';
COMMENT ON COLUMN env_data.humidity IS '습도 (%)';
COMMENT ON COLUMN env_data.illuminance IS '조도 (lux)';


-- ==============================================
-- 4. 시스템 이벤트 로그 테이블
-- ==============================================

DROP TABLE IF EXISTS system_events CASCADE;

CREATE TABLE system_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(20) NOT NULL,
    device_id VARCHAR(50),
    message TEXT NOT NULL
);

CREATE INDEX idx_events_timestamp ON system_events(timestamp DESC);

COMMENT ON TABLE system_events IS '시스템 이벤트 및 에러 로그';
COMMENT ON COLUMN system_events.id IS '고유 ID';
COMMENT ON COLUMN system_events.timestamp IS '발생 시각';
COMMENT ON COLUMN system_events.event_type IS '이벤트 타입 (info/warning/error)';
COMMENT ON COLUMN system_events.device_id IS '관련 장치 ID';
COMMENT ON COLUMN system_events.message IS '이벤트 메시지';


-- ==============================================
-- 초기화 완료 메시지
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '데이터베이스 초기화 완료!';
    RAISE NOTICE '생성된 테이블:';
    RAISE NOTICE '  - energy_data_single (단상)';
    RAISE NOTICE '  - energy_data_three_phase (3상)';
    RAISE NOTICE '  - env_data (환경)';
    RAISE NOTICE '  - system_events (로그)';
    RAISE NOTICE '========================================';
END $$;
