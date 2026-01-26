# ==============================================
# UI 테마 설정 (다크 모드)
# ==============================================
"""
Material Design 기반 다크 모드 테마

색상 체계:
    - 배경: 어두운 회색 계열
    - 강조: 파란색 (전력), 초록색 (환경)
    - 텍스트: 밝은 회색/흰색
    - 카드: 약간 밝은 회색 (그림자 효과)
"""

from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt


class Theme:
    """다크 모드 테마 정의"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 색상 (Material Design Dark)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 배경색
    BG_PRIMARY = '#1a1a2e'      # 메인 배경 (진한 네이비)
    BG_SECONDARY = '#16213e'    # 사이드바/카드 배경
    BG_TERTIARY = '#0f3460'     # 호버/선택 배경
    
    # 강조색
    PRIMARY = '#00adb5'         # 메인 강조 (청록색)
    SECONDARY = '#ff6b6b'       # 경고/오류 (빨강)
    SUCCESS = '#4caf50'         # 성공 (초록)
    WARNING = '#ff9800'         # 주의 (주황)
    
    # 텍스트색
    TEXT_PRIMARY = '#eeeeee'    # 메인 텍스트 (밝은 회색)
    TEXT_SECONDARY = '#9e9e9e'  # 보조 텍스트 (회색)
    TEXT_DISABLED = '#616161'   # 비활성 텍스트
    
    # 센서 타입별 색상
    ENERGY_COLOR = '#00adb5'    # 전력 (청록색)
    ENV_COLOR = '#4caf50'       # 환경 (초록색)
    
    # 차트 색상
    CHART_LINE = '#00adb5'      # 차트 선
    CHART_GRID = '#2d2d44'      # 그리드 선
    CHART_AXIS = '#616161'      # 축 색상
    
    # 경계선
    BORDER = '#2d2d44'          # 테두리
    DIVIDER = '#1f1f2e'         # 구분선
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 폰트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    FONT_FAMILY = 'Segoe UI'    # Windows 기본 폰트
    # Mac: 'SF Pro Display', Linux: 'Ubuntu'
    
    @staticmethod
    def font(size=10, bold=False):
        """폰트 생성
        
        Args:
            size: 폰트 크기 (pt)
            bold: 굵게 여부
        
        Returns:
            QFont: 폰트 객체
        """
        font = QFont(Theme.FONT_FAMILY, size)
        if bold:
            font.setBold(True)
        return font
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 스타일시트 (CSS)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @staticmethod
    def get_main_stylesheet():
        """메인 윈도우 스타일시트
        
        Returns:
            str: CSS 스타일시트
        """
        return f"""
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 메인 윈도우 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QMainWindow {{
            background-color: {Theme.BG_PRIMARY};
        }}
        
        QWidget {{
            background-color: {Theme.BG_PRIMARY};
            color: {Theme.TEXT_PRIMARY};
            font-family: {Theme.FONT_FAMILY};
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 카드 (QGroupBox) */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QGroupBox {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 12px;
            margin-top: 12px;
            padding: 20px;
            font-size: 14px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            color: {Theme.PRIMARY};
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 콤보박스 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QComboBox {{
            background-color: {Theme.BG_TERTIARY};
            border: 2px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            color: {Theme.TEXT_PRIMARY};
            font-size: 13px;
        }}
        
        QComboBox:hover {{
            border: 2px solid {Theme.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {Theme.TEXT_SECONDARY};
            margin-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            selection-background-color: {Theme.PRIMARY};
            color: {Theme.TEXT_PRIMARY};
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 버튼 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QPushButton {{
            background-color: {Theme.PRIMARY};
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            color: white;
            font-size: 13px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: #00c4cc;
        }}
        
        QPushButton:pressed {{
            background-color: #009ba3;
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 레이블 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QLabel {{
            color: {Theme.TEXT_PRIMARY};
            background-color: transparent;
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 테이블 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QTableWidget {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            gridline-color: {Theme.DIVIDER};
            color: {Theme.TEXT_PRIMARY};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {Theme.PRIMARY};
        }}
        
        QHeaderView::section {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: none;
            padding: 10px;
            font-weight: bold;
        }}
        
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        /* 스크롤바 */
        /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
        QScrollBar:vertical {{
            background-color: {Theme.BG_PRIMARY};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {Theme.BORDER};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {Theme.PRIMARY};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        """
    
    @staticmethod
    def get_card_style(bg_color=None):
        """카드 스타일 (그림자 효과)
        
        Args:
            bg_color: 배경색 (기본값: BG_SECONDARY)
        
        Returns:
            str: CSS 스타일
        """
        if bg_color is None:
            bg_color = Theme.BG_SECONDARY
        
        return f"""
        background-color: {bg_color};
        border: 1px solid {Theme.BORDER};
        border-radius: 12px;
        padding: 20px;
        """
    
    @staticmethod
    def get_header_style():
        """헤더 스타일
        
        Returns:
            str: CSS 스타일
        """
        return f"""
        background-color: {Theme.BG_SECONDARY};
        border-bottom: 2px solid {Theme.PRIMARY};
        padding: 15px 20px;
        """
    
    @staticmethod
    def get_status_style(status='normal'):
        """상태 표시 스타일
        
        Args:
            status: 'normal', 'warning', 'error'
        
        Returns:
            str: CSS 스타일
        """
        colors = {
            'normal': Theme.SUCCESS,
            'warning': Theme.WARNING,
            'error': Theme.SECONDARY,
        }
        
        color = colors.get(status, Theme.SUCCESS)
        
        return f"""
        background-color: {color};
        color: white;
        border-radius: 6px;
        padding: 5px 15px;
        font-weight: bold;
        """
