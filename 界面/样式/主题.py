# -*- coding: utf-8 -*-
"""
主题样式定义

定义应用程序的颜色常量和QSS样式表，
实现明亮、清新的视觉风格。
"""


class 颜色:
    """颜色常量定义"""
    
    # 主色调
    主色 = "#3B82F6"      # 蓝色 - 主要强调色
    主色悬停 = "#2563EB"  # 蓝色悬停状态
    主色按下 = "#1D4ED8"  # 蓝色按下状态
    
    # 状态颜色
    成功 = "#10B981"      # 绿色 - 正常/成功状态
    警告 = "#F59E0B"      # 黄色 - 警告状态
    错误 = "#EF4444"      # 红色 - 错误状态
    
    # 背景颜色
    背景 = "#F8FAFC"      # 浅灰背景 - 主窗口背景
    卡片背景 = "#FFFFFF"  # 白色 - 卡片和面板背景
    选中背景 = "#EFF6FF"  # 浅蓝色 - 选中项背景
    悬停背景 = "#F1F5F9"  # 浅灰色 - 悬停背景
    
    # 边框颜色
    边框 = "#E2E8F0"      # 边框灰
    边框聚焦 = "#3B82F6"  # 聚焦时边框色
    
    # 文字颜色
    文字 = "#334155"      # 深灰文字 - 正文
    标题 = "#1E293B"      # 深色标题
    次要文字 = "#64748B"  # 次要文字
    禁用文字 = "#94A3B8"  # 禁用状态文字
    
    # 按钮颜色
    按钮禁用 = "#CBD5E1"  # 禁用按钮背景


# QSS样式表 - 明亮主题
LIGHT_THEME_QSS = """
/* ==================== 主窗口 ==================== */
QMainWindow {
    background-color: #F8FAFC;
}

QWidget {
    font-family: "Microsoft YaHei", "微软雅黑", "Source Han Sans SC", sans-serif;
    font-size: 13px;
    color: #334155;
}

/* ==================== 导航栏 ==================== */
QListWidget#导航栏 {
    background-color: #FFFFFF;
    border: none;
    border-right: 1px solid #E2E8F0;
    font-size: 13px;
    outline: none;
}

QListWidget#导航栏::item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 4px 8px;
}

QListWidget#导航栏::item:selected {
    background-color: #EFF6FF;
    color: #3B82F6;
}

QListWidget#导航栏::item:hover:!selected {
    background-color: #F1F5F9;
}

/* ==================== 按钮 ==================== */
QPushButton {
    background-color: #3B82F6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2563EB;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #CBD5E1;
    color: #94A3B8;
}

/* 次要按钮 */
QPushButton[class="secondary"] {
    background-color: #FFFFFF;
    color: #334155;
    border: 1px solid #E2E8F0;
}

QPushButton[class="secondary"]:hover {
    background-color: #F1F5F9;
    border-color: #CBD5E1;
}

/* 危险按钮 */
QPushButton[class="danger"] {
    background-color: #EF4444;
}

QPushButton[class="danger"]:hover {
    background-color: #DC2626;
}

/* 成功按钮 */
QPushButton[class="success"] {
    background-color: #10B981;
}

QPushButton[class="success"]:hover {
    background-color: #059669;
}

/* ==================== 卡片容器 ==================== */
QFrame[class="card"] {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

QFrame[class="card-hover"]:hover {
    border-color: #CBD5E1;
}

/* ==================== 标签 ==================== */
QLabel {
    color: #334155;
    font-size: 13px;
    background: transparent;
}

QLabel[class="title"] {
    font-size: 16px;
    font-weight: bold;
    color: #1E293B;
}

QLabel[class="subtitle"] {
    font-size: 14px;
    font-weight: 500;
    color: #1E293B;
}

QLabel[class="secondary"] {
    color: #64748B;
    font-size: 12px;
}

/* 状态标签 */
QLabel[class="status-success"] {
    color: #10B981;
}

QLabel[class="status-warning"] {
    color: #F59E0B;
}

QLabel[class="status-error"] {
    color: #EF4444;
}

/* ==================== 进度条 ==================== */
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E2E8F0;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #10B981;
    border-radius: 4px;
}

/* ==================== 输入框 ==================== */
QLineEdit {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #FFFFFF;
    selection-background-color: #3B82F6;
}

QLineEdit:focus {
    border-color: #3B82F6;
}

QLineEdit:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
}

/* ==================== 数字输入框 ==================== */
QSpinBox, QDoubleSpinBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
    background-color: #FFFFFF;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3B82F6;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    border: none;
    width: 16px;
}

/* ==================== 下拉框 ==================== */
QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #FFFFFF;
    min-width: 100px;
}

QComboBox:focus {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    background-color: #FFFFFF;
    selection-background-color: #EFF6FF;
    selection-color: #3B82F6;
}

/* ==================== 复选框 ==================== */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #CBD5E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
}

QCheckBox::indicator:hover {
    border-color: #3B82F6;
}

/* ==================== 滑块 ==================== */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #E2E8F0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #3B82F6;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #2563EB;
}

QSlider::sub-page:horizontal {
    background-color: #3B82F6;
    border-radius: 3px;
}

/* ==================== 文本编辑框 ==================== */
QTextEdit, QPlainTextEdit {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
    background-color: #FFFFFF;
    selection-background-color: #3B82F6;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #3B82F6;
}

/* ==================== 滚动条 ==================== */
QScrollBar:vertical {
    border: none;
    background-color: #F1F5F9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #F1F5F9;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ==================== 状态栏 ==================== */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
    color: #64748B;
    font-size: 12px;
}

/* ==================== 工具提示 ==================== */
QToolTip {
    background-color: #1E293B;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ==================== 分组框 ==================== */
QGroupBox {
    font-weight: 500;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #1E293B;
}

/* ==================== 表格 ==================== */
QTableWidget {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #3B82F6;
}

QHeaderView::section {
    background-color: #F8FAFC;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 10px;
    font-weight: 500;
    color: #1E293B;
}

/* ==================== 标签页 ==================== */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #F1F5F9;
    border: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #3B82F6;
}

QTabBar::tab:hover:!selected {
    background-color: #E2E8F0;
}
"""


def 获取状态颜色(状态类型: str) -> str:
    """
    根据状态类型返回对应的颜色值
    
    参数:
        状态类型: "正常", "警告", "错误"
    
    返回:
        对应的颜色十六进制值
    """
    颜色映射 = {
        "正常": 颜色.成功,
        "警告": 颜色.警告,
        "错误": 颜色.错误,
    }
    return 颜色映射.get(状态类型, 颜色.文字)


def 获取状态样式(状态类型: str) -> str:
    """
    根据状态类型返回对应的QSS样式类名
    
    参数:
        状态类型: "正常", "警告", "错误"
    
    返回:
        对应的样式类名
    """
    样式映射 = {
        "正常": "status-success",
        "警告": "status-warning",
        "错误": "status-error",
    }
    return 样式映射.get(状态类型, "")
