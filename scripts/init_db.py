# ==============================================
# 데이터베이스 초기화 스크립트
# ==============================================

"""
PostgreSQL 데이터베이스 초기화

실행 방법:
    python scripts/init_db.py
"""

import sys
import os

# src 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from core.config import get_config

def main():
    print("=" * 70)
    print("데이터베이스 초기화")
    print("=" * 70)
    
    config = get_config()
    
    # DB 연결 URL
    db_url = (
        f"postgresql://{config.db_user}:{config.db_password}"
        f"@{config.db_host}:{config.db_port}/{config.db_name}"
    )
    
    print(f"\n연결 정보:")
    print(f"  Host: {config.db_host}:{config.db_port}")
    print(f"  Database: {config.db_name}")
    print(f"  User: {config.db_user}")
    
    # SQL 파일 읽기
    sql_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'init.sql')
    
    if not os.path.exists(sql_file):
        print(f"\n✗ SQL 파일을 찾을 수 없습니다: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # DB 연결 및 실행
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # 트랜잭션으로 실행
            conn.execute(text(sql_script))
            conn.commit()
        
        print("\n✓ 데이터베이스 초기화 완료!")
        print("\n생성된 테이블:")
        print("  - energy_data_single (단상)")
        print("  - energy_data_three_phase (3상)")
        print("  - env_data (환경)")
        print("  - system_events (로그)")
        print("\n" + "=" * 70)
    
    except Exception as e:
        print(f"\n✗ 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
