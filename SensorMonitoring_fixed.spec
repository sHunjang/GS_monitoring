# -*- mode: python ; coding: utf-8 -*-
"""
센서 모니터링 시스템 PyInstaller 빌드 스펙 파일

사용법:
    pyinstaller SensorMonitoring_fixed.spec

빌드 후 할 일:
    1. dist/SensorMonitoring/ 폴더가 생성됨
    2. .env 파일을 dist/SensorMonitoring/에 복사
    3. SensorMonitoring.exe 실행
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 숨겨진 import 수집
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

hiddenimports = []

# 1. sensors 패키지
hiddenimports += collect_submodules('sensors')
hiddenimports += collect_submodules('sensors.energy')
hiddenimports += collect_submodules('sensors.environment')

# 2. core 패키지
hiddenimports += collect_submodules('core')

# 3. ui 패키지
hiddenimports += collect_submodules('ui')

# 4. services 패키지
hiddenimports += collect_submodules('services')

# 5. 필수 라이브러리
hiddenimports += [
    # Modbus
    'pymodbus.client',
    'pymodbus.client.serial',
    'pymodbus.exceptions',
    
    # PostgreSQL
    'sqlalchemy.dialects.postgresql',
    'sqlalchemy.dialects.postgresql.psycopg2',
    'psycopg2',
    
    # 시리얼 통신
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    
    # PyQt5
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'PyQt5.QtGui',
    
    # PyQtGraph (차트)
    'pyqtgraph',
    'pyqtgraph.graphicsItems',
    'pyqtgraph.Qt',
    
    # Pandas (데이터 처리)
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas._libs.tslibs.base',
    
    # Excel 내보내기
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.styles',
    
    # 환경 변수
    'dotenv',
]

# 6. 모델 파일 명시적 포함
hiddenimports += [
    'sensors.energy.models',
    'sensors.environment.models',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.timedeltas',
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 파일 수집
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

datas = []

# src 폴더 전체를 포함
datas.append(('src', 'src'))

# PyQtGraph 데이터 파일 포함 (필요시)
try:
    import pyqtgraph
    pg_datas, pg_binaries, pg_hiddenimports = collect_all('pyqtgraph')
    datas += pg_datas
    hiddenimports += pg_hiddenimports
except:
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PYZ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SensorMonitoring',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # True: 콘솔 표시 (디버깅용), False: GUI만 표시
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLLECT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SensorMonitoring'
)