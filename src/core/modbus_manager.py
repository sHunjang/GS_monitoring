# ==============================================
# Modbus 연결 관리자
# ==============================================
"""
Modbus 연결 관리자

역할:
- Modbus RTU 클라이언트 관리
- 여러 전력 센서가 하나의 연결을 공유
- 환경 센서와 Lock 공유

🔧 SerialBusManager와 통합:
- ModbusSerialClient가 포트를 독점 관리
- Lock만 SerialBusManager와 공유하여 환경 센서와 충돌 방지
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import get_config  # 수정!

import logging
import threading
from typing import Optional

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

# from core.config import get_config


logger = logging.getLogger(__name__)


class ModbusManager:
    """
    Modbus 연결 관리자 (싱글톤)
    
    기능:
    1. 하나의 Modbus 클라이언트를 여러 센서가 공유
    2. Lock으로 동시 접근 방지 (환경 센서와 공유)
    3. 자동 재연결
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔧 전역 Lock (환경 센서와 공유용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _shared_lock = threading.Lock()
    
    def __init__(self):
        """초기화 (싱글톤이므로 직접 호출 금지)"""
        if ModbusManager._instance is not None:
            raise Exception("ModbusManager는 싱글톤입니다. get_instance()를 사용하세요.")
        
        self.config = get_config()
        self.client: Optional[ModbusSerialClient] = None
        
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("ModbusManager 초기화")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"  포트: {self.config.energy_serial_port}")
        logger.info(f"  🔧 환경 센서와 Lock 공유")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 자동 연결
        self.connect()
    
    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ModbusManager()
        return cls._instance
    
    @classmethod
    def get_shared_lock(cls) -> threading.Lock:
        """
        공유 Lock 반환
        
        🔧 이 Lock을 환경 센서도 사용하여 충돌 방지
        
        Returns:
            threading.Lock: 전역 공유 Lock
        """
        return cls._shared_lock
    
    def connect(self) -> bool:
        """
        Modbus 연결
        
        Returns:
            bool: 연결 성공 시 True
        """
        try:
            if self.client and self.client.is_socket_open():
                logger.debug("이미 연결되어 있음")
                return True
            
            logger.info(f"Modbus RTU 연결 중: {self.config.energy_serial_port}")
            
            # Modbus 클라이언트 생성
            self.client = ModbusSerialClient(
                port=self.config.energy_serial_port,
                baudrate=self.config.energy_serial_baudrate,
                timeout=self.config.energy_serial_timeout,
                stopbits=1,
                bytesize=8,
                parity='N'
            )
            
            # 연결
            if not self.client.connect():
                raise ConnectionError("Modbus 연결 실패")
            
            logger.info(f"✓ Modbus RTU 연결 성공: {self.config.energy_serial_port}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Modbus RTU 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """Modbus 연결 해제"""
        if self.client:
            self.client.close()
            logger.info("Modbus RTU 연결 종료")
        self.client = None
    
    def get_lock(self):
        """
        버스 접근용 Lock 반환
        
        🔧 환경 센서와 같은 Lock 공유
        
        Returns:
            threading.Lock: Context Manager로 사용
        """
        return self._shared_lock
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.client is not None and self.client.is_socket_open()
    
    def reconnect(self) -> bool:
        """재연결 시도"""
        logger.info("Modbus 재연결 시도...")
        self.disconnect()
        return self.connect()


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
    )
    
    print("=" * 70)
    print("Modbus Manager 테스트")
    print("=" * 70)
    
    # 싱글톤 인스턴스 생성
    manager = ModbusManager.get_instance()
    
    # 연결 상태 확인
    print(f"\n연결 상태: {manager.is_connected()}")
    
    # 멀티스레드 테스트
    def test_read(slave_id):
        """Modbus 읽기 테스트"""
        with manager.get_lock():
            print(f"[Slave {slave_id}] 읽기 시작")
            try:
                result = manager.client.read_holding_registers(
                    address=0,
                    count=2,
                    slave=slave_id
                )
                if not result.isError():
                    print(f"[Slave {slave_id}] 완료: {result.registers}")
                else:
                    print(f"[Slave {slave_id}] 에러: {result}")
            except Exception as e:
                print(f"[Slave {slave_id}] 예외: {e}")
    
    # 여러 Slave ID 동시 테스트
    threads = []
    for sid in [11, 12, 31, 32]:
        t = threading.Thread(target=test_read, args=(sid,))
        threads.append(t)
        t.start()
        time.sleep(0.1)  # 시차를 두고 시작
    
    for t in threads:
        t.join()
    
    print("\n✅ 테스트 완료")
