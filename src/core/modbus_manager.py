# ==============================================
# Modbus 연결 관리자 (PyInstaller 호환)
# ==============================================
"""
Modbus 연결 관리자

역할:
- Modbus RTU 클라이언트 관리
- 여러 전력 센서가 하나의 연결을 공유
- 환경 센서와 Lock 공유

PyInstaller 대응:
- 조건부 import 사용
- sys.path 조작 제거
"""

import logging
import threading
from typing import Optional

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Config import (조건부 - PyInstaller 호환)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


logger = logging.getLogger(__name__)


class ModbusManager:
    """
    Modbus 연결 관리자 (싱글톤 패턴)
    
    기능:
    1. 하나의 Modbus 클라이언트를 여러 센서가 공유
    2. Lock으로 동시 접근 방지 (환경 센서와도 공유)
    3. 자동 재연결
    
    사용 예:
        manager = ModbusManager.get_instance()
        with manager.get_lock():
            result = manager.client.read_holding_registers(...)
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 싱글톤 패턴을 위한 클래스 변수
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _instance = None              # 싱글톤 인스턴스
    _lock = threading.Lock()      # 인스턴스 생성용 Lock
    _shared_lock = threading.Lock()  # 포트 접근용 Lock (전역 공유)
    
    def __init__(self):
        """
        초기화 (직접 호출 금지)
        
        대신 get_instance() 사용
        """
        # 중복 생성 방지
        if ModbusManager._instance is not None:
            raise Exception(
                "ModbusManager는 싱글톤입니다. "
                "get_instance()를 사용하세요."
            )
        
        # 설정 로드
        self.config = get_config()
        
        # Modbus 클라이언트 (초기값 None)
        self.client: Optional[ModbusSerialClient] = None
        
        # 초기화 로그
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("ModbusManager 초기화")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"  포트: {self.config.energy_serial_port}")
        logger.info(f"  속도: {self.config.energy_serial_baudrate} bps")
        logger.info(f"  🔧 환경 센서와 Lock 공유")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 자동 연결 시도
        self.connect()
    
    @classmethod
    def get_instance(cls):
        """
        싱글톤 인스턴스 반환
        
        프로그램 전체에서 하나의 ModbusManager만 사용
        
        Returns:
            ModbusManager: 싱글톤 인스턴스
        """
        # 인스턴스가 없으면 생성
        if cls._instance is None:
            # Lock으로 동시 생성 방지
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = ModbusManager()
        
        return cls._instance
    
    @classmethod
    def get_shared_lock(cls) -> threading.Lock:
        """
        공유 Lock 반환
        
        이 Lock을 환경 센서도 사용하여 포트 충돌 방지
        
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
            # 이미 연결되어 있으면 성공 반환
            if self.client and self.client.is_socket_open():
                logger.debug("이미 연결되어 있음")
                return True
            
            logger.info(
                f"Modbus RTU 연결 중: {self.config.energy_serial_port}"
            )
            
            # Modbus 클라이언트 생성
            self.client = ModbusSerialClient(
                port=self.config.energy_serial_port,      # 시리얼 포트
                baudrate=self.config.energy_serial_baudrate,  # 통신 속도
                timeout=self.config.energy_serial_timeout,    # 타임아웃
                stopbits=1,           # 정지 비트
                bytesize=8,           # 데이터 비트
                parity='N'            # 패리티 (None)
            )
            
            # 연결 시도
            if not self.client.connect():
                raise ConnectionError("Modbus 연결 실패")
            
            logger.info(
                f"✓ Modbus RTU 연결 성공: {self.config.energy_serial_port}"
            )
            return True
        
        except Exception as e:
            logger.error(f"✗ Modbus RTU 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """
        Modbus 연결 해제
        
        프로그램 종료 시 호출
        """
        if self.client:
            self.client.close()
            logger.info("Modbus RTU 연결 종료")
        self.client = None
    
    def get_lock(self):
        """
        포트 접근용 Lock 반환
        
        환경 센서와 같은 Lock 공유
        
        사용 예:
            with manager.get_lock():
                result = manager.client.read_holding_registers(...)
        
        Returns:
            threading.Lock: Context Manager로 사용 가능한 Lock
        """
        return self._shared_lock
    
    def is_connected(self) -> bool:
        """
        연결 상태 확인
        
        Returns:
            bool: 연결되어 있으면 True
        """
        return self.client is not None and self.client.is_socket_open()
    
    def reconnect(self) -> bool:
        """
        재연결 시도
        
        연결이 끊겼을 때 다시 연결
        
        Returns:
            bool: 재연결 성공 시 True
        """
        logger.info("Modbus 재연결 시도...")
        self.disconnect()
        return self.connect()


# ==============================================
# 테스트 코드
# ==============================================

if __name__ == "__main__":
    """
    이 파일을 직접 실행하면 Modbus 연결 테스트
    
    실행: python src/core/modbus_manager.py
    """
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
        """
        Modbus 읽기 테스트
        
        여러 스레드가 동시에 실행되어도
        Lock으로 순차 접근 보장
        """
        with manager.get_lock():
            print(f"[Slave {slave_id}] 읽기 시작")
            try:
                # 레지스터 읽기
                result = manager.client.read_holding_registers(
                    address=0,      # 시작 주소
                    count=2,        # 읽을 개수
                    slave=slave_id  # Slave ID
                )
                
                # 결과 확인
                if not result.isError():
                    print(f"[Slave {slave_id}] 완료: {result.registers}")
                else:
                    print(f"[Slave {slave_id}] 에러: {result}")
            except Exception as e:
                print(f"[Slave {slave_id}] 예외: {e}")
    
    # 여러 Slave ID 동시 테스트
    print("\n멀티스레드 테스트 (Slave ID: 11, 12, 31, 32)")
    print("-" * 70)
    
    threads = []
    for sid in [11, 12, 31, 32]:
        # 스레드 생성
        t = threading.Thread(target=test_read, args=(sid,))
        threads.append(t)
        t.start()
        # 시차를 두고 시작 (0.1초)
        time.sleep(0.1)
    
    # 모든 스레드 종료 대기
    for t in threads:
        t.join()
    
    print("\n" + "=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)