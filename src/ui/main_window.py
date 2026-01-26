# ==============================================
# 메인 윈도우 (최종 버전)
# ==============================================
"""
센서 모니터링 GUI


기능:
    - 사이드바: 센서 트리 네비게이션 + 다중 선택
    - 차트: 여러 센서 동시 비교
    - 데이터 내보내기: CSV/Excel + 기간 선택
    - 기본값: Energy_1~4 누적전력량 표시
    - 자동 새로고침: 데이터 수집 후 자동 갱신 (수집 주기 + 3초)
"""


import sys
from pathlib import Path
import os
from dotenv import load_dotenv


# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QTreeWidget,
    QTreeWidgetItem, QCheckBox, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QSplitter
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg
from datetime import datetime, timedelta
import pandas as pd


from src.services.ui_data_service import UIDataService


# .env 파일 로드 (환경변수 가져오기)
load_dotenv()



class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        """초기화 메서드"""
        super().__init__()
        
        # 데이터베이스 접근 서비스 초기화
        self.service = UIDataService()
        
        # .env 파일에서 데이터 수집 주기 가져오기 (기본값: 60초)
        self.collection_interval = int(os.getenv('COLLECTION_INTERVAL', 60))
        
        # UI 갱신 주기 = 데이터 수집 주기 + 3초 (DB 저장 대기 시간)
        # 예: 60초마다 데이터 수집 → 63초마다 UI 갱신
        self.ui_refresh_interval = self.collection_interval + 3
        
        # 다음 자동 갱신까지 남은 시간 추적용 변수
        self.seconds_until_refresh = self.ui_refresh_interval
        
        # 현재 선택된 센서들 저장 (센서ID: 측정필드)
        self.selected_sensors = {}
        
        # 차트에 표시할 시간 범위 (기본: 1시간)
        self.current_hours = 1
        
        # 센서별 차트 선 색상 정의
        self.chart_colors = [
            '#1E88E5',  # 파랑
            '#E53935',  # 빨강
            '#43A047',  # 초록
            '#FB8C00',  # 주황
            '#8E24AA',  # 보라
            '#00ACC1',  # 청록
        ]
        
        # UI 생성
        self.init_ui()
        
        # 기본 센서 선택 (Energy_1~4 누적전력량)
        self.set_default_selection()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 자동 새로고침 타이머 설정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터 수집(60초) → DB 저장(1~2초) → UI 갱신(63초)
        # 이렇게 하면 DB에 데이터가 확실히 저장된 후 차트가 갱신됨!
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)  # 63초마다 update_data() 자동 호출
        self.timer.start(self.ui_refresh_interval * 1000)  # 밀리초 단위로 변환
        
        # 시간 표시 및 카운트다운 타이머 (1초마다 실행)
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_label)
        self.time_timer.start(1000)
        
        # 타이머 시작 확인 로그
        print(f"✅ 자동 새로고침 타이머 시작")
        print(f"   - 데이터 수집 주기: {self.collection_interval}초")
        print(f"   - UI 갱신 주기: {self.ui_refresh_interval}초 (여유 3초)")
        print(f"   - 타이머 활성화: {self.timer.isActive()}\n")
    
    def init_ui(self):
        """UI 초기화 및 레이아웃 구성"""
        # 윈도우 타이틀 및 크기 설정
        self.setWindowTitle('📊 고성 센서 모니터링 시스템 v1.0')
        self.setGeometry(100, 100, 1600, 900)
        
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 (가로 방향)
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 스플리터 (사용자가 크기 조절 가능)
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 센서 선택 사이드바
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)
        
        # 오른쪽: 메인 컨텐츠 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 헤더 (타이틀, 상태, 시간 표시)
        header_layout = self.create_header()
        right_layout.addLayout(header_layout)
        
        # 컨트롤 바 (시간 범위, 새로고침, 내보내기)
        control_bar = self.create_control_bar()
        right_layout.addWidget(control_bar)
        
        # 선택된 센서 표시 레이블
        self.selected_label = QLabel('선택된 센서: 없음')
        self.selected_label.setFont(QFont('Arial', 10))
        self.selected_label.setStyleSheet('color: #666; padding: 5px;')
        right_layout.addWidget(self.selected_label)
        
        # 시계열 차트
        chart_group = self.create_chart()
        right_layout.addWidget(chart_group)
        
        # 통계 테이블
        stats_group = self.create_stats_table()
        right_layout.addWidget(stats_group)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # 스플리터 비율 설정 (사이드바 300px, 메인 1200px)
        splitter.setSizes([300, 1200])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
    
    def create_header(self):
        """헤더 영역 생성 (타이틀, 갱신 정보, 상태, 시간)"""
        header_layout = QHBoxLayout()
        
        # 타이틀
        title = QLabel('📊 센서 모니터링 시스템')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        header_layout.addWidget(title)
        
        # 공간 확보
        header_layout.addStretch()
        
        # 다음 자동 갱신까지 남은 시간 표시
        self.next_refresh_label = QLabel(f'다음 갱신: {self.ui_refresh_interval}초 후')
        self.next_refresh_label.setFont(QFont('Arial', 9))
        self.next_refresh_label.setStyleSheet('color: #999;')
        header_layout.addWidget(self.next_refresh_label)
        
        # 마지막 갱신 시간 표시
        self.last_update_label = QLabel('마지막 갱신: --')
        self.last_update_label.setFont(QFont('Arial', 9))
        self.last_update_label.setStyleSheet('color: #666;')
        header_layout.addWidget(self.last_update_label)
        
        # 시스템 상태 표시
        self.status_label = QLabel('🟢 정상')
        self.status_label.setFont(QFont('Arial', 12))
        header_layout.addWidget(self.status_label)
        
        # 현재 시간 표시
        self.time_label = QLabel(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.time_label.setFont(QFont('Arial', 10))
        header_layout.addWidget(self.time_label)
        
        return header_layout
    
    def create_sidebar(self):
        """사이드바 생성 (센서 트리 + 측정 항목 선택)"""
        sidebar = QGroupBox('센서 선택')
        sidebar.setMaximumWidth(300)
        sidebar.setMinimumWidth(250)
        
        layout = QVBoxLayout()
        
        # 안내 문구
        info_label = QLabel('📌 센서를 체크하여 선택하세요\n(여러 개 선택 가능)')
        info_label.setFont(QFont('Arial', 9))
        info_label.setStyleSheet('color: #666; padding: 5px;')
        layout.addWidget(info_label)
        
        # 센서 트리 위젯
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)  # 헤더 숨김
        self.tree.setFont(QFont('Arial', 10))
        layout.addWidget(self.tree)
        
        # 측정 항목 선택 그룹
        field_group = QGroupBox('측정 항목')
        field_layout = QVBoxLayout()
        
        # 라디오 버튼 그룹 생성
        self.field_group_buttons = QButtonGroup()
        self.field_radios = {}
        
        # 측정 항목 목록
        fields = [
            ('power', '⚡ 전력 (kW)'),
            ('power_factor', '📊 역률'),
            ('energy_total', '📈 누적전력량 (kWh)'),
            ('temperature', '🌡️ 온도 (°C)'),
            ('humidity', '💧 습도 (%)'),
            ('illuminance', '💡 조도 (lux)'),
        ]
        
        # 각 측정 항목에 대한 라디오 버튼 생성
        for idx, (field_key, label) in enumerate(fields):
            radio = QRadioButton(label)
            radio.setFont(QFont('Arial', 9))
            self.field_radios[field_key] = radio
            self.field_group_buttons.addButton(radio, idx)
            field_layout.addWidget(radio)
            
            # 기본 선택: 누적전력량
            if field_key == 'energy_total':
                radio.setChecked(True)
        
        field_group.setLayout(field_layout)
        layout.addWidget(field_group)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        
        # 적용 버튼
        apply_btn = QPushButton('✓ 적용')
        apply_btn.setFont(QFont('Arial', 10, QFont.Bold))
        apply_btn.clicked.connect(self.on_apply_selection)
        btn_layout.addWidget(apply_btn)
        
        # 초기화 버튼
        clear_btn = QPushButton('✗ 초기화')
        clear_btn.setFont(QFont('Arial', 10))
        clear_btn.clicked.connect(self.on_clear_selection)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        sidebar.setLayout(layout)
        
        # 센서 트리 구축
        self.build_sensor_tree()
        
        return sidebar
    
    def build_sensor_tree(self):
        """센서 트리 구조 생성"""
        self.tree.clear()
        
        # 1. 전력 센서 카테고리
        energy_root = QTreeWidgetItem(self.tree, ['⚡ 전력 센서'])
        energy_root.setFont(0, QFont('Arial', 10, QFont.Bold))
        energy_root.setExpanded(True)  # 기본으로 펼침
        
        # 전력 센서 목록 가져오기
        energy_devices = self.service.get_all_energy_devices()
        for device in energy_devices:
            item = QTreeWidgetItem(energy_root, [device])
            item.setCheckState(0, Qt.Unchecked)  # 체크박스 추가
            # 센서 정보를 데이터로 저장
            item.setData(0, Qt.UserRole, {'type': 'energy', 'device': device})
        
        # 2. 환경 센서 카테고리
        env_root = QTreeWidgetItem(self.tree, ['🌡️ 환경 센서'])
        env_root.setFont(0, QFont('Arial', 10, QFont.Bold))
        env_root.setExpanded(True)
        
        # 환경 센서 목록 가져오기
        env_devices = self.service.get_all_environment_devices()
        for device in env_devices:
            item = QTreeWidgetItem(env_root, [device])
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, {'type': 'environment', 'device': device})
    
    def create_control_bar(self):
        """컨트롤 바 생성 (시간 범위, 자동 갱신, 내보내기)"""
        control_group = QGroupBox('설정')
        control_layout = QHBoxLayout()
        
        # 1. 시간 범위 선택
        time_label = QLabel('⏱️ 시간 범위:')
        time_label.setFont(QFont('Arial', 10))
        control_layout.addWidget(time_label)
        
        # 시간 범위 버튼 그룹
        self.time_buttons = QButtonGroup()
        time_ranges = [
            (1, '1시간'),
            (6, '6시간'),
            (24, '24시간'),
            (168, '7일'),
        ]
        
        for idx, (hours, label) in enumerate(time_ranges):
            btn = QPushButton(label)
            btn.setFont(QFont('Arial', 9))
            btn.setCheckable(True)  # 토글 가능
            btn.clicked.connect(lambda checked, h=hours: self.on_time_range_changed(h))
            self.time_buttons.addButton(btn, idx)
            control_layout.addWidget(btn)
            
            # 기본 선택: 1시간
            if hours == 1:
                btn.setChecked(True)
        
        control_layout.addStretch()
        
        # 2. 자동 새로고침 주기 표시
        # 사용자에게 실제 갱신 주기를 명확히 알림
        auto_refresh_label = QLabel(
            f'🔄 자동 새로고침: {self.ui_refresh_interval}초 '
            f'(수집 {self.collection_interval}초 + 여유 3초)'
        )
        auto_refresh_label.setFont(QFont('Arial', 9))
        auto_refresh_label.setStyleSheet('color: #666;')
        control_layout.addWidget(auto_refresh_label)
        
        # 3. 데이터 내보내기
        export_label = QLabel('📥 내보내기:')
        export_label.setFont(QFont('Arial', 10))
        control_layout.addWidget(export_label)
        
        # CSV 내보내기 버튼
        csv_btn = QPushButton('CSV')
        csv_btn.setFont(QFont('Arial', 9))
        csv_btn.clicked.connect(lambda: self.export_data('csv'))
        control_layout.addWidget(csv_btn)
        
        # Excel 내보내기 버튼
        excel_btn = QPushButton('Excel')
        excel_btn.setFont(QFont('Arial', 9))
        excel_btn.clicked.connect(lambda: self.export_data('excel'))
        control_layout.addWidget(excel_btn)
        
        # 수동 새로고침 버튼
        refresh_btn = QPushButton('🔄 새로고침')
        refresh_btn.setFont(QFont('Arial', 9, QFont.Bold))
        refresh_btn.clicked.connect(self.update_data)
        control_layout.addWidget(refresh_btn)
        
        control_group.setLayout(control_layout)
        return control_group
    
    def create_chart(self):
        """시계열 차트 생성"""
        chart_group = QGroupBox(f'📈 시계열 차트 (최근 {self.current_hours}시간)')
        chart_layout = QVBoxLayout()
        
        # PyQtGraph 차트 위젯 생성
        self.chart = pg.PlotWidget()
        self.chart.setBackground('w')  # 흰색 배경
        self.chart.showGrid(x=True, y=True, alpha=0.3)  # 그리드 표시
        
        # 축 레이블 설정
        self.chart.setLabel('left', '값')
        self.chart.setLabel('bottom', '시간')
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # X축 설정: 'x1+e9' 표시 제거
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        bottom_axis = self.chart.getPlotItem().getAxis('bottom')
        bottom_axis.enableAutoSIPrefix(False)  # 자동 SI 접두사 비활성화 (x1+e9 제거)
        bottom_axis.setPen(pg.mkPen(color='#333', width=1))
        
        # Y축 설정
        left_axis = self.chart.getPlotItem().getAxis('left')
        left_axis.setPen(pg.mkPen(color='#333', width=1))
        
        # # 축 선 스타일 설정
        # self.chart.getPlotItem().getAxis('bottom').setPen(pg.mkPen(color='#333', width=1))
        # self.chart.getPlotItem().getAxis('left').setPen(pg.mkPen(color='#333', width=1))
        
        # 범례 추가 (센서 이름 표시)
        self.chart.addLegend()
        
        chart_layout.addWidget(self.chart)
        chart_group.setLayout(chart_layout)
        
        return chart_group
    
    
    def generate_time_ticks(self, timestamps):
        """X축 시간 눈금 생성 - 시간 범위에 따라 적절한 형식으로 표시"""
        if not timestamps:
            return []
        
        ticks = []
        start_ts = min(timestamps)
        end_ts = max(timestamps)
        duration = end_ts - start_ts
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 시간 범위에 따라 눈금 간격 및 표시 형식 결정
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if duration <= 3600:  # 1시간
            interval = 600  # 10분 간격
            time_format = '%H:%M'  # 예: 14:30
        elif duration <= 21600:  # 6시간
            interval = 3600  # 1시간 간격
            time_format = '%H:%M'  # 예: 14:00
        elif duration <= 86400:  # 24시간
            interval = 7200  # 2시간 간격
            time_format = '%H:%M'  # 예: 14:00
        else:  # 7일
            interval = 86400  # 1일 간격
            time_format = '%m-%d'  # 예: 01-26 (날짜만)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 눈금 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        current_ts = start_ts
        while current_ts <= end_ts:
            dt = datetime.fromtimestamp(current_ts)
            time_str = dt.strftime(time_format)
            ticks.append((current_ts, time_str))
            current_ts += interval
        
        # 마지막 눈금 추가
        if ticks and ticks[-1][0] != end_ts:
            dt = datetime.fromtimestamp(end_ts)
            time_str = dt.strftime(time_format)
            ticks.append((end_ts, time_str))
        
        return ticks

    
    
    def create_stats_table(self):
        """통계 테이블 생성"""
        stats_group = QGroupBox('📊 통계 (최근 24시간)')
        stats_layout = QVBoxLayout()
        
        # 테이블 위젯 생성
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels([
            '센서', '최신', '평균', '최대', '최소', '데이터 개수'
        ])
        # 열 너비 자동 조정
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_table)
        
        stats_group.setLayout(stats_layout)
        return stats_group
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 초기 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def set_default_selection(self):
        """기본값 설정: Energy_1~4 누적전력량 자동 선택"""
        # 누적전력량 라디오 버튼이 이미 선택되어 있음
        
        # 기본으로 선택할 센서 목록
        energy_devices = ['Energy_1', 'Energy_2', 'Energy_3', 'Energy_4']
        
        # 센서 트리에서 해당 센서들 체크
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            # '전력' 카테고리 찾기
            if '전력' in category.text(0):
                for j in range(category.childCount()):
                    item = category.child(j)
                    data = item.data(0, Qt.UserRole)
                    # Energy_1~4인 경우 체크
                    if data and data['device'] in energy_devices:
                        item.setCheckState(0, Qt.Checked)
        
        # 선택된 센서 정보 저장
        self.selected_sensors = {
            'Energy_1': 'energy_total',
            'Energy_2': 'energy_total',
            'Energy_3': 'energy_total',
            'Energy_4': 'energy_total',
        }
        
        # 선택 정보 레이블 업데이트
        self.selected_label.setText(
            '선택된 센서: Energy_1, Energy_2, Energy_3, Energy_4 | 측정 항목: 누적전력량'
        )
        
        # 초기 데이터 로드
        self.update_data()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 타이머 콜백
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def update_time_label(self):
        """시간 레이블 및 카운트다운 업데이트 (1초마다 호출)"""
        # 현재 시간 표시
        self.time_label.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 다음 갱신까지 카운트다운
        self.seconds_until_refresh -= 1
        if self.seconds_until_refresh < 0:
            # 카운트다운이 끝나면 UI 갱신 주기로 리셋
            self.seconds_until_refresh = self.ui_refresh_interval
        
        # 카운트다운 레이블 업데이트
        self.next_refresh_label.setText(f'다음 갱신: {self.seconds_until_refresh}초 후')
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 이벤트 핸들러
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def on_apply_selection(self):
        """적용 버튼 클릭 이벤트 - 사용자가 선택한 센서와 측정 항목 적용"""
        # 선택된 측정 항목 가져오기
        selected_field = None
        for field_key, radio in self.field_radios.items():
            if radio.isChecked():
                selected_field = field_key
                break
        
        # 측정 항목 미선택 시 경고
        if not selected_field:
            QMessageBox.warning(self, '경고', '측정 항목을 선택하세요.')
            return
        
        # 체크된 센서들 수집
        self.selected_sensors = {}
        
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            for j in range(category.childCount()):
                item = category.child(j)
                # 체크된 항목만 처리
                if item.checkState(0) == Qt.Checked:
                    data = item.data(0, Qt.UserRole)
                    device = data['device']
                    sensor_type = data['type']
                    
                    # 센서 타입과 측정 항목의 호환성 검사
                    if sensor_type == 'energy' and selected_field in ['power', 'power_factor', 'energy_total']:
                        self.selected_sensors[device] = selected_field
                    elif sensor_type == 'environment' and selected_field in ['temperature', 'humidity', 'illuminance']:
                        self.selected_sensors[device] = selected_field
        
        # 센서 미선택 시 경고
        if not self.selected_sensors:
            QMessageBox.warning(
                self,
                '경고',
                '센서를 선택하거나\n해당 센서 타입에 맞는 측정 항목을 선택하세요.'
            )
            return
        
        # 선택 정보 표시 업데이트
        sensor_names = ', '.join(self.selected_sensors.keys())
        field_name = self.field_radios[selected_field].text().split(' ')[1]
        self.selected_label.setText(f'선택된 센서: {sensor_names} | 측정 항목: {field_name}')
        
        # 데이터 갱신 (수동)
        self.update_data()
    
    def on_clear_selection(self):
        """초기화 버튼 클릭 이벤트 - 모든 선택 초기화"""
        # 모든 센서 체크 해제
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            for j in range(category.childCount()):
                item = category.child(j)
                item.setCheckState(0, Qt.Unchecked)
        
        # 선택 정보 초기화
        self.selected_sensors = {}
        self.selected_label.setText('선택된 센서: 없음')
        
        # 차트 초기화
        self.chart.clear()
        self.chart.addLegend()
        
        # 테이블 초기화
        self.stats_table.setRowCount(0)
    
    def on_time_range_changed(self, hours):
        """시간 범위 변경 이벤트 - 차트 표시 기간 변경"""
        self.current_hours = hours
        
        # 차트 제목 업데이트
        parent = self.chart.parent()
        if parent:
            parent.setTitle(f'📈 시계열 차트 (최근 {hours}시간)')
        
        # 데이터 갱신 (수동)
        if self.selected_sensors:
            self.update_data()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터 갱신 (자동 + 수동)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def update_data(self):
        """데이터 갱신 (차트 + 통계 테이블)
        
        호출되는 경우:
        1. 자동: 타이머에 의해 63초마다 자동 호출 (수집 60초 + 여유 3초)
        2. 수동: 사용자가 '새로고침' 버튼 클릭
        3. 수동: 사용자가 센서 선택 후 '적용' 버튼 클릭
        4. 수동: 사용자가 시간 범위 변경
        
        동작 순서:
        1. 선택된 센서가 있는지 확인
        2. 차트 초기화 (기존 그래프 삭제)
        3. DB에서 최신 데이터 조회
        4. 차트에 그래프 그리기
        5. 통계 테이블 업데이트
        6. 갱신 시간 표시
        """
        # 선택된 센서가 없으면 종료
        if not self.selected_sensors:
            return
        
        # 갱신 시작 표시
        self.status_label.setText('🔄 갱신 중...')
        
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. 차트 초기화
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            self.chart.clear()  # 기존 그래프 모두 삭제
            self.chart.addLegend()  # 범례 다시 추가
            
            # 모든 센서의 타임스탬프 수집 (X축 범위 계산용)
            all_timestamps = []
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 2. 각 센서별로 데이터 가져오기 및 그리기
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            for idx, (device, field) in enumerate(self.selected_sensors.items()):
                # 센서별 색상 지정
                color = self.chart_colors[idx % len(self.chart_colors)]
                
                # 센서 타입에 따라 다른 메서드 호출
                if device.startswith('Energy_'):
                    # 전력 센서 데이터 가져오기
                    timeseries = self.service.get_timeseries_energy(
                        device,
                        hours=self.current_hours,
                        field=field
                    )
                else:
                    # 환경 센서 데이터 가져오기
                    timeseries = self.service.get_timeseries_environment(
                        device,
                        hours=self.current_hours,
                        field=field
                    )
                
                # 차트에 그리기
                if timeseries:
                    # 타임스탬프를 Unix timestamp로 변환
                    timestamps = [data['timestamp'].timestamp() for data in timeseries]
                    values = [data['value'] for data in timeseries]
                    
                    if timestamps:
                        # 전체 타임스탬프 목록에 추가
                        all_timestamps.extend(timestamps)
                        
                        # 선 그래프 그리기
                        pen = pg.mkPen(color=color, width=2)
                        self.chart.plot(
                            timestamps,
                            values,
                            pen=pen,
                            name=device  # 범례에 표시될 이름
                        )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 3. X축 눈금 및 범위 설정
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if all_timestamps:
                # 시간 눈금 생성 (10분, 1시간, 2시간, 1일 간격)
                axis = self.chart.getPlotItem().getAxis('bottom')
                axis.setTicks([self.generate_time_ticks(all_timestamps)])
                
                # X축 범위 설정 (여백 5% 추가)
                min_ts = min(all_timestamps)
                max_ts = max(all_timestamps)
                time_range = max_ts - min_ts
                padding = time_range * 0.05 if time_range > 0 else 1
                self.chart.setXRange(min_ts - padding, max_ts + padding, padding=0)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 4. 통계 테이블 업데이트
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            self.update_stats_table_multi()
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 5. 카운트다운 리셋
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            self.seconds_until_refresh = self.ui_refresh_interval
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 6. 갱신 완료 표시
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            now = datetime.now()
            self.last_update_label.setText(f'마지막 갱신: {now.strftime("%H:%M:%S")}')
            self.status_label.setText('🟢 정상')
        
        except Exception as e:
            # 에러 발생 시 표시
            self.status_label.setText(f'🔴 오류')
            print(f"\n[ERROR] 데이터 갱신 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_time_ticks(self, timestamps):
        """X축 시간 눈금 생성 - 시간 범위에 따라 적절한 간격으로 눈금 표시"""
        if not timestamps:
            return []
        
        ticks = []
        start_ts = min(timestamps)
        end_ts = max(timestamps)
        duration = end_ts - start_ts
        
        # 시간 범위에 따라 눈금 간격 조정
        if duration <= 3600:  # 1시간 이하
            interval = 600  # 10분 간격
        elif duration <= 21600:  # 6시간 이하
            interval = 3600  # 1시간 간격
        elif duration <= 86400:  # 24시간 이하
            interval = 7200  # 2시간 간격
        else:  # 7일
            interval = 86400  # 1일 간격
        
        # 눈금 생성
        current_ts = start_ts
        while current_ts <= end_ts:
            dt = datetime.fromtimestamp(current_ts)
            # 표시 형식 선택
            if duration <= 86400:
                time_str = dt.strftime('%H:%M')  # 시:분
            else:
                time_str = dt.strftime('%m/%d')  # 월/일
            ticks.append((current_ts, time_str))
            current_ts += interval
        
        # 마지막 눈금 추가
        if ticks and ticks[-1][0] != end_ts:
            dt = datetime.fromtimestamp(end_ts)
            if duration <= 86400:
                time_str = dt.strftime('%H:%M')
            else:
                time_str = dt.strftime('%m/%d')
            ticks.append((end_ts, time_str))
        
        return ticks
    
    def update_stats_table_multi(self):
        """통계 테이블 업데이트 - 최근 24시간 데이터의 최신/평균/최대/최소 표시"""
        # 행 개수 설정 (선택된 센서 수만큼)
        self.stats_table.setRowCount(len(self.selected_sensors))
        
        # 각 센서별 통계 데이터 추가
        for row, (device, field) in enumerate(self.selected_sensors.items()):
            # 센서 타입에 따라 통계 데이터 가져오기
            if device.startswith('Energy_'):
                stats = self.service.get_statistics_energy(device, hours=24, field=field)
            else:
                stats = self.service.get_statistics_environment(device, hours=24, field=field)
            
            # 측정 항목의 단위 가져오기
            unit = self.get_unit(field)
            
            # 테이블 셀 데이터 구성
            items = [
                device,
                f"{stats['latest']} {unit}",
                f"{stats['avg']} {unit}",
                f"{stats['max']} {unit}",
                f"{stats['min']} {unit}",
                f"{stats['count']}개"
            ]
            
            # 테이블에 데이터 추가
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)  # 중앙 정렬
                self.stats_table.setItem(row, col, item)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터 내보내기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def export_data(self, format_type):
        """데이터 내보내기 (CSV/Excel) - 기간 선택 후 파일로 저장"""
        # 선택된 센서가 없으면 경고
        if not self.selected_sensors:
            QMessageBox.warning(self, '경고', '내보낼 센서를 선택하세요.')
            return
        
        # 기간 선택 다이얼로그
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle('내보내기 기간 선택')
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # 안내 문구
        label = QLabel('내보낼 데이터 기간을 선택하세요:')
        label.setFont(QFont('Arial', 10))
        layout.addWidget(label)
        
        # 기간 선택 라디오 버튼
        period_group = QButtonGroup()
        periods = [
            (30, '1개월'),
            (180, '6개월'),
            (None, '전체 데이터'),
        ]
        
        for idx, (days, label_text) in enumerate(periods):
            radio = QRadioButton(label_text)
            radio.setFont(QFont('Arial', 9))
            period_group.addButton(radio, idx)
            layout.addWidget(radio)
            if idx == 0:
                radio.setChecked(True)  # 기본 선택: 1개월
        
        # 확인/취소 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        # 다이얼로그 취소 시 종료
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # 선택된 기간 가져오기
        selected_idx = period_group.checkedId()
        selected_days = periods[selected_idx][0]
        
        # 시작/종료 날짜 계산
        end_date = datetime.now()
        if selected_days:
            start_date = end_date - timedelta(days=selected_days)
        else:
            start_date = datetime(2000, 1, 1)  # 전체 데이터
        
        # 파일 저장 다이얼로그
        if format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'CSV 저장',
                f'sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                'CSV Files (*.csv)'
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'Excel 저장',
                f'sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                'Excel Files (*.xlsx)'
            )
        
        # 파일 경로 미선택 시 종료
        if not file_path:
            return
        
        try:
            # 데이터 수집
            all_data = []
            
            # 각 센서별 데이터 가져오기
            for device, field in self.selected_sensors.items():
                if device.startswith('Energy_'):
                    data = self.service.get_data_by_date_range_energy(
                        device,
                        start_date,
                        end_date
                    )
                else:
                    data = self.service.get_data_by_date_range_environment(
                        device,
                        start_date,
                        end_date
                    )
                
                # DataFrame 형식으로 변환
                for record in data:
                    all_data.append({
                        '센서': device,
                        '시간': record['timestamp'],
                        '측정 항목': field,
                        '값': record.get(field, 0),
                        '단위': self.get_unit(field)
                    })
            
            # Pandas DataFrame 생성
            df = pd.DataFrame(all_data)
            
            # 파일 저장
            if format_type == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(file_path, index=False)
            
            # 완료 메시지
            QMessageBox.information(
                self,
                '완료',
                f'데이터가 저장되었습니다.\n\n파일: {file_path}\n레코드 수: {len(all_data)}개'
            )
        
        except Exception as e:
            # 에러 메시지
            QMessageBox.critical(self, '오류', f'데이터 저장 실패:\n{str(e)}')
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 유틸리티
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_unit(self, field):
        """측정 항목에 맞는 단위 반환"""
        units = {
            'power': 'kW',
            'power_factor': '',
            'energy_total': 'kWh',
            'temperature': '°C',
            'humidity': '%',
            'illuminance': 'lux'
        }
        return units.get(field, '')
