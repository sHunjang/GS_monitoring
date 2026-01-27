# ==============================================
# 전력량 센서 프로토콜 정의 (PyInstaller 호환)
# ==============================================
"""
전력량 센서 Modbus 프로토콜

각 센서 모델별로 레지스터 주소가 다르므로
센서 타입에 맞는 프로토콜을 사용해야 합니다.

지원 센서:
    1. DDS238-2 (단상): Slave ID 1~29
    2. TAC4300 (3상 4선): Slave ID 30 이상

PyInstaller 대응:
- sys.path 조작 제거
- import 없음
"""


# ==============================================
# DDS238-2 (단상) 프로토콜
# ==============================================

DDS238_PROTOCOL = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력량 (적산전력량, kWh)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'energy_total': {
        'address': 0,           # 0x0000 (시작 주소)
        'count': 2,             # LONG (32bit, 2개 레지스터)
        'type': 'LONG',         # 데이터 타입
        'unit': 'kWh',          # 단위
        'scale': 0.01,          # raw × 0.01 = kWh
        'description': '적산전력량'
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력 (순시전력, W)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'power': {
        'address': 14,          # 0x000E
        'count': 1,             # INT (16bit, 1개 레지스터)
        'type': 'INT',          # 데이터 타입
        'unit': 'W',            # 단위
        'scale': 1.0,           # raw × 1.0 = W (나중에 kW로 변환)
        'description': '유효전력'
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 역률 (Power Factor)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'power_factor': {
        'address': 16,          # 0x0010
        'count': 1,             # INT (16bit, 1개 레지스터)
        'type': 'INT',          # 데이터 타입
        'unit': '',             # 단위 없음 (0~1)
        'scale': 0.001,         # raw × 0.001 = 역률
        'description': '역률'
    }
}


# ==============================================
# TAC4300 (3상 4선) 프로토콜
# ==============================================

TAC4300_PROTOCOL = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력 (총 유효전력, kW)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'power': {
        'address': 44,          # 0x002C
        'count': 2,             # LONG (32bit, 2개 레지스터)
        'type': 'LONG',         # 데이터 타입
        'unit': 'kW',           # 단위
        'scale': 0.001,         # raw × 0.001 = kW
        'description': '총 유효전력 (R+S+T상)'
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 역률 (평균 역률)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'power_factor': {
        'address': 50,          # 0x0032
        'count': 1,             # INT (16bit, 1개 레지스터)
        'type': 'INT',          # 데이터 타입
        'unit': '',             # 단위 없음 (0~1)
        'scale': 0.001,         # raw × 0.001 = 역률
        'description': '역률 (3상 평균)'
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전력량 (적산전력량, kWh)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    'energy_total': {
        'address': 1028,        # 0x0404
        'count': 2,             # LONG (32bit, 2개 레지스터)
        'type': 'LONG',         # 데이터 타입
        'unit': 'kWh',          # 단위
        'scale': 0.01,          # raw × 0.01 = kWh
        'description': '적산전력량 (3상 합계)'
    }
}


# ==============================================
# 프로토콜 매핑
# ==============================================

PROTOCOLS = {
    'dds238': DDS238_PROTOCOL,      # 단상 센서
    'tac4300': TAC4300_PROTOCOL,    # 3상 센서
}


def get_protocol(sensor_type: str) -> dict:
    """
    센서 타입에 맞는 프로토콜 반환
    
    Args:
        sensor_type: 'dds238' 또는 'tac4300'
    
    Returns:
        dict: 프로토콜 딕셔너리
            {
                'power': {...},
                'power_factor': {...},
                'energy_total': {...}
            }
    
    Raises:
        ValueError: 지원하지 않는 센서 타입
    
    Example:
        >>> protocol = get_protocol('dds238')
        >>> print(protocol['power']['address'])
        14
    """
    # 소문자로 변환
    sensor_type = sensor_type.lower()
    
    # 프로토콜 존재 확인
    if sensor_type not in PROTOCOLS:
        raise ValueError(
            f"지원하지 않는 센서 타입: {sensor_type}\n"
            f"지원 타입: {list(PROTOCOLS.keys())}"
        )
    
    return PROTOCOLS[sensor_type]


def get_sensor_type_from_slave_id(slave_id: int) -> str:
    """
    Slave ID로 센서 타입 자동 감지
    
    규칙:
        - 1~29: DDS238-2 (단상)
        - 30 이상: TAC4300 (3상)
    
    Args:
        slave_id: Modbus Slave ID (1~247)
    
    Returns:
        str: 'dds238' 또는 'tac4300'
    
    Example:
        >>> get_sensor_type_from_slave_id(11)
        'dds238'
        >>> get_sensor_type_from_slave_id(31)
        'tac4300'
    """
    if slave_id >= 30:
        return 'tac4300'  # 3상 센서
    else:
        return 'dds238'   # 단상 센서


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 프로토콜 정보 출력
    
    실행: python src/sensors/energy/protocols.py
    """
    print("=" * 70)
    print("전력량 센서 프로토콜")
    print("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DDS238-2 프로토콜 출력
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[DDS238-2 단상 센서]")
    for name, config in DDS238_PROTOCOL.items():
        print(
            f"  {name:20s}: "
            f"주소={config['address']:4d} (0x{config['address']:04X}), "
            f"{config['count']}개, "
            f"{config['type']:4s}, "
            f"×{config['scale']:.3f} {config['unit']}"
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAC4300 프로토콜 출력
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[TAC4300 3상 센서]")
    for name, config in TAC4300_PROTOCOL.items():
        print(
            f"  {name:20s}: "
            f"주소={config['address']:4d} (0x{config['address']:04X}), "
            f"{config['count']}개, "
            f"{config['type']:4s}, "
            f"×{config['scale']:.3f} {config['unit']}"
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Slave ID 자동 감지 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[Slave ID 자동 감지]")
    for sid in range(11, 40):
        sensor_type = get_sensor_type_from_slave_id(sid)
        sensor_name = "단상 (DDS238)" if sensor_type == 'dds238' else "3상 (TAC4300)"
        print(f"  Slave ID {sid:2d} → {sensor_type:8s} ({sensor_name})")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 프로토콜 조회 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[프로토콜 조회 테스트]")
    try:
        protocol = get_protocol('dds238')
        print(f"  ✓ DDS238 프로토콜 로드 성공")
        print(f"    레지스터 개수: {len(protocol)}개")
    except Exception as e:
        print(f"  ✗ 오류: {e}")
    
    print("\n" + "=" * 70)