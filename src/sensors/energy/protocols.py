# ==============================================
# 전력량 센서 프로토콜 정의
# ==============================================
# 역할: DDS238-2(단상), TAC4300(3상) Modbus 레지스터 맵

"""
전력량 센서 Modbus 프로토콜

각 센서 모델별로 레지스터 주소가 다르므로
센서 타입에 맞는 프로토콜을 사용해야 합니다.

지원 센서:
    1. DDS238-2 (단상): Slave ID 11, 12
    2. TAC4300 (3상 4선): Slave ID 31, 32
"""


# ==============================================
# DDS238-2 (단상) 프로토콜
# ==============================================

DDS238_PROTOCOL = {
    # 전력량 (kWh)
    'energy_total': {
        'address': 0,           # 0x0000
        'count': 2,             # LONG (32bit)
        'type': 'LONG',
        'unit': 'kWh',
        'scale': 0.01,          # raw × 0.01 = kWh
        'description': '적산전력량'
    },
    
    # 전력 (W)
    'power': {
        'address': 14,          # 0x000E
        'count': 1,             # INT (16bit)
        'type': 'INT',
        'unit': 'W',
        'scale': 1.0,           # raw × 1.0 = W
        'description': '유효전력'
    },
    
    # 역률
    'power_factor': {
        'address': 16,          # 0x0010
        'count': 1,             # INT (16bit)
        'type': 'INT',
        'unit': '',
        'scale': 0.001,         # raw × 0.001 = 역률
        'description': '역률'
    }
}


# ==============================================
# TAC4300 (3상 4선) 프로토콜
# ==============================================

TAC4300_PROTOCOL = {
    # 전력 (kW)
    'power': {
        'address': 44,          # 0x002C
        'count': 2,             # LONG (32bit)
        'type': 'LONG',
        'unit': 'kW',
        'scale': 0.001,         # raw × 0.001 = kW
        'description': '총 유효전력'
    },
    
    # 역률
    'power_factor': {
        'address': 50,          # 0x0032
        'count': 1,             # INT (16bit)
        'type': 'INT',
        'unit': '',
        'scale': 0.001,         # raw × 0.001 = 역률
        'description': '역률'
    },
    
    # 전력량 (kWh)
    'energy_total': {
        'address': 1028,        # 0x0404
        'count': 2,             # LONG (32bit)
        'type': 'LONG',
        'unit': 'kWh',
        'scale': 0.01,          # raw × 0.01 = kWh
        'description': '적산전력량'
    }
}


# ==============================================
# 프로토콜 매핑
# ==============================================

PROTOCOLS = {
    'dds238': DDS238_PROTOCOL,      # 단상
    'tac4300': TAC4300_PROTOCOL,    # 3상
}


def get_protocol(sensor_type: str) -> dict:
    """
    센서 타입에 맞는 프로토콜 반환
    
    Args:
        sensor_type: 'dds238' 또는 'tac4300'
    
    Returns:
        dict: 프로토콜 딕셔너리
    
    Raises:
        ValueError: 지원하지 않는 센서 타입
    """
    sensor_type = sensor_type.lower()
    
    if sensor_type not in PROTOCOLS:
        raise ValueError(f"지원하지 않는 센서 타입: {sensor_type}")
    
    return PROTOCOLS[sensor_type]


def get_sensor_type_from_slave_id(slave_id: int) -> str:
    """
    Slave ID로 센서 타입 자동 감지
    
    규칙:
        - 1~29: DDS238-2 (단상)
        - 30 이상: TAC4300 (3상)
    
    Args:
        slave_id: Modbus Slave ID
    
    Returns:
        str: 'dds238' 또는 'tac4300'
    """
    if slave_id >= 30:
        return 'tac4300'
    else:
        return 'dds238'


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    print("=" * 70)
    print("전력량 센서 프로토콜")
    print("=" * 70)
    
    # DDS238-2
    print("\n[DDS238-2 단상]")
    for name, config in DDS238_PROTOCOL.items():
        print(f"  {name}: 주소={config['address']} (0x{config['address']:04X}), "
              f"{config['count']}개, {config['type']}, ×{config['scale']} {config['unit']}")
    
    # TAC4300
    print("\n[TAC4300 3상]")
    for name, config in TAC4300_PROTOCOL.items():
        print(f"  {name}: 주소={config['address']} (0x{config['address']:04X}), "
              f"{config['count']}개, {config['type']}, ×{config['scale']} {config['unit']}")
    
    # Slave ID 자동 감지
    print("\n[Slave ID 자동 감지]")
    for sid in [11, 12, 31, 32]:
        sensor_type = get_sensor_type_from_slave_id(sid)
        print(f"  Slave ID {sid} → {sensor_type.upper()}")
