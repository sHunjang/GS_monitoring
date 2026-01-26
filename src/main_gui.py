# ==============================================
# GUI 실행 파일
# ==============================================
"""
센서 모니터링 GUI 실행

실행:
    python src/main_gui.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
