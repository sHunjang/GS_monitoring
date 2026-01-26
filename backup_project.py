#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 정리 및 백업 스크립트

기능:
1. 불필요한 파일/폴더 삭제
2. 프로젝트 백업 (timestamp 기반)
3. .gitignore 업데이트
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT.parent / f"sensor-monitoring-system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 삭제할 파일 목록
FILES_TO_DELETE = [
    "build.spec",
    "logs/app.log",
    "src/main_ui.py",
    "src/core/app_context.py",
    "src/core/collector_manager.py",
]

# 삭제할 폴더 목록
FOLDERS_TO_DELETE = [
    "src/sensors/_template",
    "resources/icons",
    "resources/images",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 백업 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def backup_project():
    """프로젝트 전체 백업"""
    print("=" * 70)
    print("📦 프로젝트 백업 시작")
    print("=" * 70)
    
    if BACKUP_DIR.exists():
        print(f"⚠️  백업 폴더가 이미 존재합니다: {BACKUP_DIR}")
        response = input("덮어쓰시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("백업 취소")
            return False
        shutil.rmtree(BACKUP_DIR)
    
    # 제외할 폴더 설정
    ignore_patterns = shutil.ignore_patterns(
        '__pycache__',
        '*.pyc',
        '.git',
        'venv',
        'env',
        '.venv',
        'node_modules',
        'dist',
        'build',
        '*.egg-info'
    )
    
    print(f"복사 중: {PROJECT_ROOT} → {BACKUP_DIR}")
    shutil.copytree(PROJECT_ROOT, BACKUP_DIR, ignore=ignore_patterns)
    
    print(f"✅ 백업 완료: {BACKUP_DIR}")
    print()
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 정리 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def delete_files():
    """불필요한 파일 삭제"""
    print("=" * 70)
    print("🗑️  불필요한 파일 삭제")
    print("=" * 70)
    
    deleted_count = 0
    
    for file_path in FILES_TO_DELETE:
        full_path = PROJECT_ROOT / file_path
        
        if full_path.exists():
            print(f"❌ 삭제: {file_path}")
            full_path.unlink()
            deleted_count += 1
        else:
            print(f"⏭️  없음: {file_path}")
    
    print(f"\n✅ {deleted_count}개 파일 삭제 완료")
    print()


def delete_folders():
    """불필요한 폴더 삭제"""
    print("=" * 70)
    print("🗑️  불필요한 폴더 삭제")
    print("=" * 70)
    
    deleted_count = 0
    
    for folder_path in FOLDERS_TO_DELETE:
        full_path = PROJECT_ROOT / folder_path
        
        if full_path.exists():
            print(f"❌ 삭제: {folder_path}/")
            shutil.rmtree(full_path)
            deleted_count += 1
        else:
            print(f"⏭️  없음: {folder_path}/")
    
    print(f"\n✅ {deleted_count}개 폴더 삭제 완료")
    print()


def update_gitignore():
    """
    .gitignore 업데이트
    """
    print("=" * 70)
    print("📝 .gitignore 업데이트")
    print("=" * 70)
    
    gitignore_path = PROJECT_ROOT / ".gitignore"
    
    # 추가할 내용
    additional_lines = [
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# 로그 파일",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "logs/",
        "*.log",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# 빌드 결과물",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "dist/",
        "build/",
        "*.spec",
        "*.exe",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# 데이터베이스",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "*.db",
        "*.sqlite",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# 환경 설정 (보안)",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ".env",
        ".env.local",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# Python",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "venv/",
        "env/",
        ".venv/",
        "ENV/",
        "*.egg-info/",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# IDE",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        "",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "# OS",
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
    ]
    
    # 기존 내용 읽기
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    else:
        existing_content = ""
    
    # 새 내용 추가
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(existing_content)
        f.write('\n'.join(additional_lines))
        f.write('\n')
    
    print("✅ .gitignore 업데이트 완료")
    print()


def create_summary():
    """정리 완료 후 요약 출력"""
    print("=" * 70)
    print("📊 프로젝트 구조 요약")
    print("=" * 70)
    
    # 주요 디렉토리 파일 개수 계산
    src_files = len(list((PROJECT_ROOT / "src").rglob("*.py")))
    docs_files = len(list((PROJECT_ROOT / "docs").rglob("*.md")))
    
    print(f"✅ 정리 완료!")
    print()
    print(f"📁 src/          : {src_files}개 Python 파일")
    print(f"📁 docs/         : {docs_files}개 문서")
    print(f"📁 database/     : SQL 스크립트")
    print(f"📁 scripts/      : 유틸리티 스크립트")
    print()
    print(f"💾 백업 위치     : {BACKUP_DIR}")
    print()
    print("=" * 70)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """메인 함수"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "프로젝트 정리 및 백업" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # 1. 백업
    if not backup_project():
        return
    
    # 2. 파일 삭제
    delete_files()
    
    # 3. 폴더 삭제
    delete_folders()
    
    # 4. .gitignore 업데이트
    update_gitignore()
    
    # 5. 요약
    create_summary()
    
    print("🎉 모든 작업이 완료되었습니다!")
    print()


if __name__ == "__main__":
    main()
