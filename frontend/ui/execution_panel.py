"""
Execution Panel - Panel untuk mengontrol eksekusi workflow (Start/Stop/Pause).
Dilengkapi: step list, resume, headless toggle, slow_mo slider, browser selector, step-by-step mode.
"""

import asyncio
import json
import socket
import urllib.request
import urllib.error
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QLineEdit, QCheckBox, QSlider,
    QComboBox, QListWidget, QListWidgetItem, QScrollArea,
    QFrame, QSplitter, QSizePolicy, QAbstractItemView, QMessageBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter

from backend.core.engine import ExecutionEngine
from backend.core.workflow_parser import Workflow


# Status icons as unicode
STATUS_ICONS = {
    "waiting": "○",
    "running": "▶",
    "success": "✓",
    "failed": "✗",
    "skipped": "→",
    "retrying": "↻",
}

STATUS_COLORS = {
    "waiting": "#999",
    "running": "#2196F3",
    "success": "#4CAF50",
    "failed": "#f44336",
    "skipped": "#FF9800",
    "retrying": "#9C27B0",
}


class StepListItem(QListWidgetItem):
    """Item untuk menampilkan step dalam list dengan status."""

    def __init__(self, step_id: str, label: str, step_type: str, depth: int = 0, parent=None):
        super().__init__(parent)
        self.step_id = step_id
        self._label = label or f"{step_type}: {step_id}"
        self._step_type = step_type
        self._depth = depth
        self._status = "waiting"
        self._message = ""
        self._update_display()

    def set_status(self, status: str, message: str = ""):
        """Update status dan tampilan."""
        self._status = status
        self._message = message
        self._update_display()

    def _update_display(self):
        """Update text dan warna berdasarkan status."""
        icon = STATUS_ICONS.get(self._status, "○")
        color = STATUS_COLORS.get(self._status, "#999")
        type_short = self._step_type[:6]

        # Indentasi untuk nested steps (loop, if_else, parallel_group)
        indent = "  " * self._depth if self._depth > 0 else ""
        prefix = "└ " if self._depth > 0 else ""
        parent_indicator = " 📁" if self._depth == 0 and self._step_type in ("loop", "if_else", "parallel_group") else ""

        self.setText(f"{icon} [{type_short}] {indent}{prefix}{self._label}{parent_indicator}")
        self.setForeground(QColor(color))

        # Tooltip dengan detail
        tooltip = (
            f"Step: {self.step_id}\n"
            f"Type: {self._step_type}\n"
            f"Status: {self._status}\n"
            f"Label: {self._label}"
        )
        if self._message:
            tooltip += f"\nMessage: {self._message}"
        self.setToolTip(tooltip)


class ExecutionPanel(QWidget):
    """Panel kontrol untuk menjalankan workflow."""

    log_received = Signal(dict)
    progress_received = Signal(dict)
    execution_started = Signal()
    execution_stopped = Signal()
    save_requested = Signal(str)
    before_run = Signal()
    step_highlight_requested = Signal(str)  # Emit step_id to highlight in editor

    def __init__(self, engine: ExecutionEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.current_workflow: Optional[Workflow] = None
        self.url_label = ""  # URL dari workflow (untuk sinkronisasi)
        self.license_manager = None
        self.usage_tracker = None
        self._step_items: dict[str, StepListItem] = {}  # step_id -> StepListItem
        self._execution_count = 0
        self._step_by_step_mode = False
        self._waiting_for_step_continue = False
        self.setWindowTitle("Execution")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        title = QLabel("Execution")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)

        # ==================== TOP SECTION: Workflow Info ====================
        info_group = QGroupBox("Workflow")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(6, 10, 6, 6)
        info_layout.setSpacing(2)

        self.workflow_name_label = QLabel("No workflow loaded")
        self.workflow_name_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        info_layout.addWidget(self.workflow_name_label)

        self.workflow_info_label = QLabel("")
        self.workflow_info_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(self.workflow_info_label)

        # License info + URL input
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("License:"))
        self.license_info_label = QLabel("🔓 Free")
        self.license_info_label.setStyleSheet("color: #ffc107; font-weight: bold; font-size: 11px;")
        url_row.addWidget(self.license_info_label)
        url_row.addSpacing(12)
        url_row.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/login")
        url_row.addWidget(self.url_input, 1)
        self.save_url_btn = QPushButton("Save")
        self.save_url_btn.setFixedWidth(50)
        self.save_url_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; color: white; padding: 4px 8px;
                border-radius: 3px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #1976D2; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.save_url_btn.clicked.connect(self._save_properties)
        url_row.addWidget(self.save_url_btn)
        info_layout.addLayout(url_row)

        # Save feedback
        self.save_feedback_label = QLabel("")
        self.save_feedback_label.setAlignment(Qt.AlignCenter)
        self.save_feedback_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
        info_layout.addWidget(self.save_feedback_label)

        layout.addWidget(info_group)

        # ==================== CONTROL BUTTONS ====================
        btn_group = QGroupBox("Controls")
        btn_layout = QVBoxLayout(btn_group)
        btn_layout.setContentsMargins(6, 10, 6, 6)
        btn_layout.setSpacing(4)

        # Row 1: Start, Pause, Stop
        row1 = QHBoxLayout()

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.start_btn.clicked.connect(self._start_execution)
        row1.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background: #F57C00; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.pause_btn.clicked.connect(self._toggle_pause)
        row1.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #f44336; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background: #d32f2f; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_execution)
        row1.addWidget(self.stop_btn)

        btn_layout.addLayout(row1)

        # Row 2: Force Close + Step-by-Step + Resume
        row2 = QHBoxLayout()

        self.force_close_btn = QPushButton("✕ Force Close")
        self.force_close_btn.setEnabled(False)
        self.force_close_btn.setStyleSheet("""
            QPushButton {
                background: #B71C1C; color: white; padding: 6px;
                border-radius: 4px; font-weight: bold; font-size: 10px;
            }
            QPushButton:hover { background: #7F0000; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.force_close_btn.clicked.connect(self._force_close_browser)
        row2.addWidget(self.force_close_btn)

        self.step_by_step_cb = QCheckBox("Step-by-Step")
        self.step_by_step_cb.setStyleSheet("font-size: 10px;")
        self.step_by_step_cb.toggled.connect(self._on_step_by_step_toggled)
        row2.addWidget(self.step_by_step_cb)

        self.continue_btn = QPushButton("Continue ▶")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #9C27B0; color: white; padding: 6px;
                border-radius: 4px; font-weight: bold; font-size: 10px;
            }
            QPushButton:hover { background: #7B1FA2; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.continue_btn.clicked.connect(self._continue_step)
        row2.addWidget(self.continue_btn)

        btn_layout.addLayout(row2)

        layout.addWidget(btn_group)

        # ==================== SETTINGS SECTION ====================
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(6, 10, 6, 6)
        settings_layout.setSpacing(4)

        # Row: Session Mode + Headless + Browser + Screenshot
        settings_row1 = QHBoxLayout()

        settings_row1.addWidget(QLabel("Session:"))
        self.session_mode_combo = QComboBox()
        self.session_mode_combo.addItems(["default", "persistent", "connect"])
        self.session_mode_combo.setCurrentText("persistent")
        self.session_mode_combo.setFixedWidth(100)
        self.session_mode_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        self.session_mode_combo.setToolTip(
            "Mode sesi browser:\n"
            "- default: Buat browser baru setiap eksekusi\n"
            "- persistent: Gunakan folder sesi yang sama (login tersimpan)\n"
            "- connect: Hubungkan ke browser yang sudah berjalan (CDP)"
        )
        self.session_mode_combo.currentTextChanged.connect(self._on_session_mode_changed)
        settings_row1.addWidget(self.session_mode_combo)

        self.headless_cb = QCheckBox("Headless")
        self.headless_cb.setStyleSheet("font-size: 10px;")
        self.headless_cb.setToolTip("Jalankan browser tanpa tampilan (background)")
        settings_row1.addWidget(self.headless_cb)

        settings_row1.addWidget(QLabel("Browser:"))
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chromium", "Firefox", "WebKit"])
        self.browser_combo.setCurrentText("Chromium")
        self.browser_combo.setFixedWidth(90)
        self.browser_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        self.browser_combo.setToolTip("Mesin browser yang digunakan untuk otomasi")
        settings_row1.addWidget(self.browser_combo)

        self.screenshot_step_cb = QCheckBox("Screenshot/Step")
        self.screenshot_step_cb.setStyleSheet("font-size: 10px;")
        self.screenshot_step_cb.setToolTip("Ambil screenshot setiap kali step selesai")
        settings_row1.addWidget(self.screenshot_step_cb)

        settings_row1.addStretch()
        settings_layout.addLayout(settings_row1)

        # Row: Session details (persistent user_data_dir / connect ws_endpoint)
        self.session_details_row = QHBoxLayout()
        self.user_data_dir_label = QLabel("User Data Dir:")
        self.session_details_row.addWidget(self.user_data_dir_label)
        self.user_data_dir_input = QLineEdit("browser_session")
        self.user_data_dir_input.setPlaceholderText("Folder session browser")
        self.user_data_dir_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.session_details_row.addWidget(self.user_data_dir_input)

        self.cdp_endpoint_label = QLabel("CDP Endpoint:")
        self.session_details_row.addWidget(self.cdp_endpoint_label)
        self.cdp_endpoint_input = QLineEdit("http://localhost:9222")
        self.cdp_endpoint_input.setPlaceholderText("http://localhost:9222")
        self.cdp_endpoint_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.session_details_row.addWidget(self.cdp_endpoint_input)

        settings_layout.addLayout(self.session_details_row)

        # Row: Detect Browser + Selected browser info
        self.browser_detect_row = QHBoxLayout()

        self.detect_browser_btn = QPushButton("🔍 Detect Browsers")
        self.detect_browser_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; color: white; padding: 5px 12px;
                border-radius: 3px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #1976D2; }
        """)
        self.detect_browser_btn.clicked.connect(self._detect_browsers)
        self.browser_detect_row.addWidget(self.detect_browser_btn)

        self.detected_browser_label = QLabel("No browser detected")
        self.detected_browser_label.setStyleSheet("color: #999; font-size: 10px;")
        self.browser_detect_row.addWidget(self.detected_browser_label)

        self.browser_detect_row.addStretch()
        settings_layout.addLayout(self.browser_detect_row)

        # Update visibility based on default mode
        self._on_session_mode_changed("persistent")

        # Row: Slow Mo Slider
        slow_mo_row = QHBoxLayout()
        slow_mo_row.addWidget(QLabel("Speed:"))
        self.slow_mo_slider = QSlider(Qt.Horizontal)
        self.slow_mo_slider.setRange(0, 3000)
        self.slow_mo_slider.setValue(100)
        self.slow_mo_slider.setTickPosition(QSlider.TicksBelow)
        self.slow_mo_slider.setTickInterval(500)
        self.slow_mo_slider.setFixedWidth(150)
        slow_mo_row.addWidget(self.slow_mo_slider)

        self.slow_mo_label = QLabel("100ms")
        self.slow_mo_label.setFixedWidth(45)
        self.slow_mo_label.setStyleSheet("font-size: 10px; color: #666;")
        self.slow_mo_slider.valueChanged.connect(
            lambda v: self.slow_mo_label.setText(f"{v}ms")
        )
        slow_mo_row.addWidget(self.slow_mo_label)

        slow_mo_row.addWidget(QLabel("(0=fast, 3000=slow)"))
        slow_mo_row.addStretch()
        settings_layout.addLayout(slow_mo_row)

        # Row: Resume + Retry + Skip + Rows
        settings_row2 = QHBoxLayout()

        self.resume_from_cb = QCheckBox("Resume")
        self.resume_from_cb.setStyleSheet("font-size: 10px;")
        self.resume_from_cb.setEnabled(False)
        settings_row2.addWidget(self.resume_from_cb)

        settings_row2.addWidget(QLabel("Retry:"))
        self.retry_combo = QComboBox()
        self.retry_combo.addItems(["0", "1", "2", "3", "5", "10"])
        self.retry_combo.setCurrentText("3")
        self.retry_combo.setFixedWidth(50)
        self.retry_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        settings_row2.addWidget(self.retry_combo)

        self.skip_failed_rows_cb = QCheckBox("Skip failed")
        self.skip_failed_rows_cb.setStyleSheet("font-size: 10px;")
        self.skip_failed_rows_cb.setToolTip(
            "Jika aktif, baris yang gagal akan dilewati dan eksekusi dilanjutkan ke baris berikutnya.\n"
            "Failed rows akan dikumpulkan dan bisa di-retry setelah eksekusi selesai."
        )
        settings_row2.addWidget(self.skip_failed_rows_cb)

        self.skip_action_combo = QComboBox()
        self.skip_action_combo.addItems(["None", "Navigate", "Click"])
        self.skip_action_combo.setCurrentText("None")
        self.skip_action_combo.setFixedWidth(80)
        self.skip_action_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        self.skip_action_combo.setToolTip(
            "Aksi setelah skip baris gagal:\n"
            "- None: lanjut ke baris berikutnya\n"
            "- Navigate: buka URL tertentu\n"
            "- Click: klik elemen tertentu"
        )
        settings_row2.addWidget(self.skip_action_combo)

        self.skip_action_target = QLineEdit()
        self.skip_action_target.setFixedWidth(140)
        self.skip_action_target.setPlaceholderText("URL atau selector")
        self.skip_action_target.setStyleSheet("font-size: 10px; padding: 2px;")
        self.skip_action_target.setToolTip("URL untuk Navigate, atau CSS selector untuk Click")
        self.skip_action_target.hide()
        settings_row2.addWidget(self.skip_action_target)

        def on_skip_action_changed(text):
            self.skip_action_target.setVisible(text != "None")

        self.skip_action_combo.currentTextChanged.connect(on_skip_action_changed)

        settings_row2.addSpacing(12)
        settings_row2.addWidget(QLabel("Rows:"))
        self.row_range_combo = QComboBox()
        self.row_range_combo.addItems(["All", "Single", "Custom"])
        self.row_range_combo.setCurrentText("All")
        self.row_range_combo.setFixedWidth(80)
        self.row_range_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        self.row_range_combo.setToolTip(
            "Pilih baris data yang akan diproses:\n"
            "- All: Semua baris\n"
            "- Single: Hanya 1 baris tertentu\n"
            "- Custom: Pilih baris tertentu, contoh: 3,7,14 atau 1-5 atau 1-3,7,10-12"
        )
        settings_row2.addWidget(self.row_range_combo)

        self.row_single_input = QSpinBox()
        self.row_single_input.setRange(1, 999999)
        self.row_single_input.setValue(1)
        self.row_single_input.setFixedWidth(60)
        self.row_single_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.row_single_input.setToolTip("Nomor baris yang akan diproses (1-based)")
        self.row_single_input.hide()
        settings_row2.addWidget(self.row_single_input)

        self.row_range_input = QLineEdit("1-5")
        self.row_range_input.setFixedWidth(80)
        self.row_range_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.row_range_input.setPlaceholderText("3,7,14 atau 1-5")
        self.row_range_input.setToolTip(
            "Format baris yang akan diproses (1-based):\n"
            "- Baris tertentu: 3,7,14\n"
            "- Rentang: 1-5\n"
            "- Campuran: 1-3,7,10-12"
        )
        self.row_range_input.hide()
        settings_row2.addWidget(self.row_range_input)

        def on_row_range_changed(text):
            is_single = text == "Single"
            is_custom = text == "Custom"
            self.row_single_input.setVisible(is_single)
            self.row_range_input.setVisible(is_custom)

        self.row_range_combo.currentTextChanged.connect(on_row_range_changed)
        settings_layout.addLayout(settings_row2)

        # Wrap settings in scroll area for proportional height
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMinimumHeight(180)
        scroll_area.setMaximumHeight(320)
        scroll_area.setWidget(settings_group)
        layout.addWidget(scroll_area)

        # ==================== PROGRESS SECTION ====================
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(6, 10, 6, 6)
        progress_layout.setSpacing(2)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd; border-radius: 4px;
                text-align: center; font-size: 10px; font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status row
        status_row = QHBoxLayout()

        self.status_icon_label = QLabel("●")
        self.status_icon_label.setStyleSheet("color: #999; font-size: 14px;")
        status_row.addWidget(self.status_icon_label)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        status_row.addWidget(self.status_label)

        status_row.addStretch()

        self.step_count_label = QLabel("0/0")
        self.step_count_label.setStyleSheet("color: #999; font-size: 10px;")
        status_row.addWidget(self.step_count_label)

        progress_layout.addLayout(status_row)

        # Current step + ETA
        detail_row = QHBoxLayout()
        self.step_label = QLabel("")
        self.step_label.setStyleSheet("color: #999; font-size: 10px;")
        detail_row.addWidget(self.step_label, 1)

        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: #999; font-size: 10px;")
        self.eta_label.setAlignment(Qt.AlignRight)
        detail_row.addWidget(self.eta_label)

        progress_layout.addLayout(detail_row)

        layout.addWidget(progress_group)

        # ==================== STEP LIST ====================
        step_list_group = QGroupBox("Steps")
        step_list_layout = QVBoxLayout(step_list_group)
        step_list_layout.setContentsMargins(6, 10, 6, 6)
        step_list_layout.setSpacing(2)

        self.step_list = QListWidget()
        self.step_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.step_list.setStyleSheet("""
            QListWidget {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 3px 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background: #e3f2fd;
            }
            QListWidget::item:selected {
                background: #bbdefb;
            }
        """)
        self.step_list.itemDoubleClicked.connect(self._on_step_double_clicked)
        step_list_layout.addWidget(self.step_list)

        # Clear highlight button
        clear_hl_btn = QPushButton("Clear Highlights")
        clear_hl_btn.setStyleSheet("""
            QPushButton {
                background: #607D8B; color: white; border: none;
                border-radius: 3px; padding: 3px 8px; font-size: 9px;
            }
            QPushButton:hover { background: #546E7A; }
        """)
        clear_hl_btn.clicked.connect(self._clear_step_highlights)
        step_list_layout.addWidget(clear_hl_btn)

        layout.addWidget(step_list_group)

        # ==================== STATE ====================
        self._start_time: Optional[datetime] = None
        self._step_times: dict[str, float] = {}
        self._has_checkpoint = False

    # ==================== PUBLIC METHODS ====================

    def set_license_manager(self, license_manager, usage_tracker):
        """Set license manager untuk cek kuota."""
        self.license_manager = license_manager
        self.usage_tracker = usage_tracker
        self._update_license_info()

    def _update_license_info(self):
        """Update license info di toolbar."""
        if not hasattr(self, 'license_info_label'):
            return

        if not self.license_manager or not self.usage_tracker:
            return

        if self.license_manager.is_licensed():
            self.license_info_label.setText("🔒 Licensed")
            self.license_info_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 11px;")
            self.license_info_label.setToolTip("Lisensi aktif - tanpa batasan")
        else:
            remaining = self.usage_tracker.get_remaining_quota()
            self.license_info_label.setText(f"🔓 Free ({remaining})")
            self.license_info_label.setStyleSheet("color: #ffc107; font-weight: bold; font-size: 11px;")
            self.license_info_label.setToolTip(f"Mode Free: {remaining} data tersisa hari ini")

    def set_workflow(self, workflow: Optional[Workflow]):
        """Set workflow yang akan dijalankan dan populate step list."""
        self.current_workflow = workflow
        self._step_items.clear()
        self.step_list.clear()
        self._step_by_step_mode = False
        self._waiting_for_step_continue = False
        self.continue_btn.setEnabled(False)

        if workflow:
            self.workflow_name_label.setText(workflow.name)
            self.workflow_info_label.setText(
                f"v{workflow.version} · {len(workflow.steps)} steps · ID: {workflow.id}"
            )

            if workflow.url:
                self.url_input.setText(workflow.url)
                self.url_label = workflow.url
            else:
                self.url_input.setText("")

            # Populate step list dengan depth dari _flatten_steps
            for step in self._flatten_steps(workflow.steps):
                depth = getattr(step, "_depth", 0)
                item = StepListItem(step.id, step.label, step.type, depth=depth)
                self.step_list.addItem(item)
                self._step_items[step.id] = item

            self.status_label.setText(f"Ready: {len(workflow.steps)} steps")
            self.step_count_label.setText(f"0/{len(workflow.steps)}")
            self.status_icon_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
            self.status_icon_label.setText("●")
            self.progress_bar.setValue(0)
        else:
            self.workflow_name_label.setText("No workflow loaded")
            self.workflow_info_label.setText("")
            self.url_input.setText("")
            self.status_label.setText("Ready")
            self.step_count_label.setText("0/0")
            self.status_icon_label.setStyleSheet("color: #999; font-size: 14px;")
            self.status_icon_label.setText("●")

    def run_workflow(self):
        """Public method untuk start dari external (e.g. shortcut F5)."""
        if self.start_btn.isEnabled():
            self._start_execution()

    def stop_workflow(self):
        """Public method untuk stop dari external (e.g. shortcut Shift+F5)."""
        if self.stop_btn.isEnabled():
            self._stop_execution()

    def toggle_pause(self):
        """Public method untuk toggle pause dari external (e.g. shortcut F6)."""
        if self.pause_btn.isEnabled():
            self._toggle_pause()

    def show_save_feedback(self, success: bool, message: str):
        """Show save success or error feedback."""
        if success:
            self.save_feedback_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px; font-weight: bold;")
        else:
            self.save_feedback_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px; font-weight: bold;")
        self.save_feedback_label.setText(message)
        # Auto-clear after 3 seconds
        QTimer.singleShot(3000, lambda: self.save_feedback_label.clear() if self.save_feedback_label.text() == message else None)

    # ==================== INTERNAL METHODS ====================

    def _flatten_steps(self, steps: list, depth: int = 0) -> list:
        """Flatten steps termasuk children untuk display di list."""
        result = []
        for step in steps:
            result.append(step)
            if step.children:
                for child in step.children:
                    child._depth = depth + 1
                    result.append(child)
            if hasattr(step, 'steps') and step.steps:
                for child in step.steps:
                    child._depth = depth + 1
                    result.append(child)
        return result

    def _start_execution(self):
        """Mulai eksekusi workflow."""
        if not self.current_workflow:
            self.status_label.setText("No workflow loaded")
            return

        # Cek kuota untuk free mode
        if self.license_manager and self.usage_tracker:
            if not self.license_manager.is_licensed():
                if self.usage_tracker.is_quota_exceeded():
                    QMessageBox.warning(
                        self,
                        "Free Mode Limit",
                        "Kuota harian 10 data telah tercapai.\n"
                        "Aktifkan lisensi untuk pemrosesan tanpa batas.\n\n"
                        "Menu: License → Activate License"
                    )
                    return

        # Reset step list statuses
        for item in self._step_items.values():
            item.set_status("waiting")

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.force_close_btn.setEnabled(True)
        self._start_time = datetime.now()
        self._step_times.clear()
        self._execution_count += 1

        self.status_icon_label.setStyleSheet("color: #2196F3; font-size: 14px;")
        self.status_icon_label.setText("▶")
        self.status_label.setText("Running...")
        self.step_label.setText("Initializing...")
        self.eta_label.setText("")

        # Apply settings to engine config
        engine_config = self.engine.config.setdefault("engine", {})
        engine_config["headless"] = self.headless_cb.isChecked()
        engine_config["browser"] = self.browser_combo.currentText().lower()
        engine_config["slow_mo"] = self.slow_mo_slider.value()

        # Update monitoring config
        monitoring_config = self.engine.config.setdefault("monitoring", {})
        monitoring_config["screenshot_on_step"] = self.screenshot_step_cb.isChecked()

        # Update retry config
        execution_config = self.engine.config.setdefault("execution", {})
        execution_config["max_retries"] = int(self.retry_combo.currentText())
        execution_config["skip_failed_rows"] = self.skip_failed_rows_cb.isChecked()
        execution_config["skip_action"] = {
            "mode": self.skip_action_combo.currentText().lower(),
            "target": self.skip_action_target.text().strip(),
        }

        # Update session config
        session_config = self.engine.config.setdefault("session", {})
        session_config["mode"] = self.session_mode_combo.currentText()
        session_config.setdefault("persistent", {})["user_data_dir"] = self.user_data_dir_input.text().strip()
        session_config.setdefault("connect", {})["ws_endpoint"] = self.cdp_endpoint_input.text().strip()

        # Update row range config
        execution_config = self.engine.config.setdefault("execution", {})
        row_mode = self.row_range_combo.currentText().lower()
        if row_mode == "single":
            execution_config["row_range"] = {"mode": "single", "row": self.row_single_input.value()}
        elif row_mode == "custom":
            execution_config["row_range"] = {"mode": "range", "range_str": self.row_range_input.text().strip()}
        else:
            execution_config["row_range"] = {"mode": "all"}

        self._has_checkpoint = False

        # Run in background
        self._execution_timer = QTimer()
        self._execution_timer.timeout.connect(self._run_async)
        self._execution_timer.start(100)

        self.execution_started.emit()

    def _run_async(self):
        """Run async execution."""
        self._execution_timer.stop()

        if not self.current_workflow:
            self.status_label.setText("Failed: no workflow")
            self._reset_buttons()
            return

        # Reload workflow
        self.before_run.emit()

        start_url = self.url_input.text().strip()

        # Check for resume
        resume_from = None
        if self.resume_from_cb.isChecked() and self.resume_from_cb.isEnabled():
            resume_from = self._find_last_checkpoint()

        # Check for step-by-step
        if self._step_by_step_mode:
            self._setup_step_by_step_worker()

        # Create worker
        self._worker = ExecutionWorker(
            self.engine, self.current_workflow,
            start_url=start_url,
            resume_from=resume_from,
        )
        self._worker.finished.connect(self._on_execution_finished)
        self._worker.progress_update.connect(self._update_progress)
        self._worker.log_update.connect(self._update_log)
        self._worker.step_started.connect(self._on_step_started)
        self._worker.step_completed.connect(self._on_step_completed)
        self._worker.start()

    def _setup_step_by_step_worker(self):
        """Setup custom progress callback for step-by-step mode."""
        original_callback = getattr(self.engine, '_on_progress', None)

        def step_by_step_callback(progress):
            if original_callback:
                original_callback(progress)

            # Pause before each step
            status = progress.get("status", "")
            if status == "running":
                self._waiting_for_step_continue = True
                self.continue_btn.setEnabled(True)
                self.step_label.setText(f"Step-by-step: click Continue for next step")
                self.status_label.setText("Waiting (Step-by-Step)")

                # Pause engine
                self.engine.pause()

        self.engine.set_progress_callback(step_by_step_callback)

    def _continue_step(self):
        """Continue to next step in step-by-step mode."""
        self._waiting_for_step_continue = False
        self.continue_btn.setEnabled(False)
        self.engine.resume()
        self.status_label.setText("Running...")

    def _detect_browsers(self):
        """Scan for browsers with remote debugging enabled via CDP."""
        browsers = []
        common_ports = [9222, 9223, 9229, 9221, 9224, 9225, 9226, 9227, 9228, 9333]
        errors = []

        for port in common_ports:
            # First check if port is open at socket level
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect(("127.0.0.1", port))
                sock.close()
            except (socket.timeout, ConnectionRefusedError, OSError):
                sock.close()
                continue

            # Port is open — try the CDP HTTP endpoint
            try:
                url = "http://127.0.0.1:{}/json/version".format(port)
                req = urllib.request.Request(url, headers={
                    "User-Agent": "AutomationStudio",
                    "Accept": "application/json",
                })
                with urllib.request.urlopen(req, timeout=3) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    data = json.loads(raw)
                    browser_str = data.get("Browser", "")
                    if not browser_str:
                        browser_str = data.get("User-Agent", "")
                    if browser_str:
                        if "Chrome" in browser_str and "Edg" in browser_str:
                            btype = "Edge"
                        elif "Chrome" in browser_str or "Chromium" in browser_str:
                            btype = "Chromium"
                        elif "Firefox" in browser_str:
                            btype = "Firefox"
                        else:
                            btype = "Browser"
                        browsers.append({
                            "type": btype,
                            "port": port,
                            "ws_endpoint": "http://127.0.0.1:{}".format(port),
                            "browser": browser_str,
                        })
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    browsers.append({
                        "type": "Browser (auth required)",
                        "port": port,
                        "ws_endpoint": "http://127.0.0.1:{}".format(port),
                        "browser": "unknown (auth)",
                    })
                continue
            except Exception as e:
                errors.append("port {}: {}".format(port, str(e)[:80]))
                continue

        if browsers:
            self.detected_browser_label.setText(
                "Found: " + ", ".join(
                    "{}:{}".format(b["type"], b["port"]) for b in browsers
                )
            )
            first = browsers[0]
            self.cdp_endpoint_input.setText(first["ws_endpoint"])
            self.session_mode_combo.setCurrentText("connect")
            self._on_session_mode_changed("connect")
        elif errors:
            self.detected_browser_label.setText(
                "CDP ports are open but HTTP failed:\n" + "\n".join(errors[:3])
            )
        else:
            self.detected_browser_label.setText(
                "No CDP browser found.\n"
                "Launch Chrome with:\n"
                "  cmd /c start chrome.exe --remote-debugging-port=9222"
            )

    def _on_session_mode_changed(self, mode: str):
        """Handle session mode change - show/hide relevant config fields."""
        is_default = mode == "default"
        is_persistent = mode == "persistent"
        is_connect = mode == "connect"

        self.user_data_dir_label.setVisible(is_persistent)
        self.user_data_dir_input.setVisible(is_persistent)
        self.cdp_endpoint_label.setVisible(is_connect)
        self.cdp_endpoint_input.setVisible(is_connect)

    def _on_step_by_step_toggled(self, checked: bool):
        """Handle step-by-step mode toggle."""
        self._step_by_step_mode = checked
        if checked:
            self.continue_btn.setEnabled(True)
            self.continue_btn.setText("▶ Continue")
        else:
            self.continue_btn.setEnabled(False)
            self.continue_btn.setText("Continue ▶")
            self._waiting_for_step_continue = False
            if self.engine.is_paused:
                self.engine.resume()

    def _on_step_started(self, step_id: str):
        """Handle step dimulai."""
        if step_id in self._step_items:
            self._step_items[step_id].set_status("running")
            self._step_times[step_id] = datetime.now().timestamp()

        # Scroll to this item
        items = self.step_list.findItems(step_id, Qt.MatchContains)
        if items:
            self.step_list.scrollToItem(items[0])
            self.step_list.setCurrentItem(items[0])

        # Emit signal for workflow editor to highlight
        self.step_highlight_requested.emit(step_id)

        # Update step label
        item = self._step_items.get(step_id)
        if item:
            label = item._label[:50]
            self.step_label.setText(f"▶ {label}")

    def _on_step_completed(self, step_id: str, status: str, message: str = ""):
        """Handle step selesai."""
        if step_id in self._step_items:
            self._step_items[step_id].set_status(status, message)

        # Update counter
        success = sum(1 for item in self._step_items.values() if item._status == "success")
        failed = sum(1 for item in self._step_items.values() if item._status == "failed")
        total = len(self._step_items)
        self.step_count_label.setText(f"{success+failed}/{total}")

    def _find_last_checkpoint(self) -> Optional[str]:
        """Cari step terakhir yang sukses dari checkpoint."""
        checkpoint_dir = self.engine.config.get("paths", {}).get("checkpoints", "checkpoints")
        import os, json
        if not os.path.exists(checkpoint_dir):
            return None

        try:
            # Cari file checkpoint terbaru
            checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.endswith(".json")]
            if not checkpoint_files:
                return None

            latest = max(checkpoint_files, key=lambda f: os.path.getmtime(os.path.join(checkpoint_dir, f)))
            with open(os.path.join(checkpoint_dir, latest), "r") as f:
                checkpoint = json.load(f)
            last_step = checkpoint.get("last_completed_step")
            if last_step:
                self.status_label.setText(f"Found checkpoint: resume from {last_step}")
                return last_step
        except Exception:
            pass
        return None

    def _toggle_pause(self):
        """Toggle pause/resume."""
        if self.engine.is_paused:
            self.engine.resume()
            self.pause_btn.setText("⏸ Pause")
            self.status_label.setText("Running...")
            self.status_icon_label.setStyleSheet("color: #2196F3; font-size: 14px;")
            self.status_icon_label.setText("▶")
        else:
            self.engine.pause()
            self.pause_btn.setText("▶ Resume")
            self.status_label.setText("Paused")
            self.status_icon_label.setStyleSheet("color: #FF9800; font-size: 14px;")
            self.status_icon_label.setText("⏸")

    def _stop_execution(self):
        """Hentikan eksekusi."""
        self.engine.stop()
        self._reset_buttons()
        self.status_label.setText("Stopped")
        self.status_icon_label.setStyleSheet("color: #607D8B; font-size: 14px;")
        self.status_icon_label.setText("⏹")
        self.eta_label.setText("")
        self._waiting_for_step_continue = False
        self.continue_btn.setEnabled(False)
        self.execution_stopped.emit()

    def _force_close_browser(self):
        """Force close browser dan hentikan eksekusi."""
        self.engine.stop()
        if hasattr(self, '_worker') and self._worker:
            self._worker.terminate()
        self._reset_buttons()
        self.status_label.setText("Force Closed")
        self.status_icon_label.setStyleSheet("color: #B71C1C; font-size: 14px;")
        self.status_icon_label.setText("✕")
        self.eta_label.setText("")
        self._waiting_for_step_continue = False
        self.continue_btn.setEnabled(False)
        self.execution_stopped.emit()

    def _update_progress(self, progress: dict):
        """Update progress bar."""
        percentage = progress.get("percentage", 0)
        self.progress_bar.setValue(int(percentage))

        status = progress.get("status", "")
        if status == "running":
            self.status_icon_label.setStyleSheet("color: #2196F3; font-size: 14px;")
            self.status_icon_label.setText("▶")
        elif status == "retrying":
            self.status_icon_label.setStyleSheet("color: #9C27B0; font-size: 14px;")
            self.status_icon_label.setText("↻")

        # Calculate ETA
        if self._start_time and percentage > 0:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            if percentage > 5:
                eta_seconds = (elapsed / percentage) * (100 - percentage)
                if eta_seconds > 0:
                    self.eta_label.setText(f"ETA: {self._format_duration(int(eta_seconds))}")

        self.progress_received.emit(progress)

    def _format_duration(self, seconds: int) -> str:
        """Format seconds to mm:ss."""
        mins = seconds // 60
        secs = seconds % 60
        if mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def _update_log(self, log: dict):
        """Forward log."""
        self.log_received.emit(log)

    def _on_execution_finished(self, result: dict):
        """Handle execution selesai."""
        self._reset_buttons()

        status = result.get("status", "unknown")
        success_count = result.get("success_count", 0)
        failed_count = result.get("failed_count", 0)
        total = result.get("total_steps", 0)
        duration = result.get("duration_seconds", 0)

        # Update license status after execution
        self._update_license_info()

        # Update step list for any remaining steps
        for step_result in result.get("results", []):
            step_id = step_result.get("step_id", "")
            step_status = step_result.get("status", "failed")
            step_msg = step_result.get("message", "")
            if step_id in self._step_items:
                self._step_items[step_id].set_status(step_status, step_msg)

        if status == "success":
            self.status_label.setText(f"✓ Completed Successfully ({self._format_duration(int(duration))})")
            self.status_icon_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
            self.status_icon_label.setText("✓")
            self.progress_bar.setValue(100)
            self._has_checkpoint = False
        elif status == "completed_with_errors":
            self.status_label.setText(f"⚠ Completed with {failed_count} error(s)")
            self.status_icon_label.setStyleSheet("color: #FF9800; font-size: 14px;")
            self.status_icon_label.setText("⚠")
            self._has_checkpoint = True
        elif status == "stopped":
            self.status_label.setText("⏹ Stopped by user")
            self.status_icon_label.setStyleSheet("color: #607D8B; font-size: 14px;")
            self.status_icon_label.setText("⏹")
        else:
            self.status_label.setText(f"✗ Failed: {status}")
            self.status_icon_label.setStyleSheet("color: #f44336; font-size: 14px;")
            self.status_icon_label.setText("✗")
            self._has_checkpoint = True

        # Enable resume if there's a checkpoint
        self.resume_from_cb.setEnabled(self._has_checkpoint)
        if self._has_checkpoint:
            self.resume_from_cb.setText("✓ Resume from checkpoint available")
            self.resume_from_cb.setStyleSheet("font-size: 10px; color: #FF9800; font-weight: bold;")
        else:
            self.resume_from_cb.setText("Resume from checkpoint")
            self.resume_from_cb.setStyleSheet("font-size: 10px;")
            self.resume_from_cb.setChecked(False)

        # Update step count dengan detail
        self.step_count_label.setText(f"{success_count+failed_count}/{total}")

        # Statistik akhir eksekusi
        skipped_count = result.get("skipped_count", 0)
        stats_text = f"✅ {success_count} sukses"
        if failed_count:
            stats_text += f" • ❌ {failed_count} gagal"
        if skipped_count:
            stats_text += f" • ⏭ {skipped_count} skip"
        stats_text += f" • ⏱ {self._format_duration(int(duration))}"

        self.eta_label.setText(stats_text)
        self.eta_label.setToolTip(
            f"Total Steps: {total}\n"
            f"Success: {success_count}\n"
            f"Failed: {failed_count}\n"
            f"Skipped: {skipped_count}\n"
            f"Duration: {self._format_duration(int(duration))}"
        )

        self._waiting_for_step_continue = False
        self.continue_btn.setEnabled(False)
        self.execution_stopped.emit()

        # Show failed rows dialog if any
        failed_rows = result.get("failed_rows", [])
        if failed_rows:
            self._show_failed_rows_dialog(failed_rows)

    def _reset_buttons(self):
        """Reset button states."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause")
        self.stop_btn.setEnabled(False)
        self.force_close_btn.setEnabled(False)

    def _save_properties(self):
        """Save workflow properties."""
        url = self.url_input.text().strip()
        self.save_feedback_label.clear()
        self.save_requested.emit(url)

    def _on_step_double_clicked(self, item: QListWidgetItem):
        """Double-click step untuk highlight di editor."""
        if isinstance(item, StepListItem):
            self.step_highlight_requested.emit(item.step_id)

    def _clear_step_highlights(self):
        """Clear all step highlights."""
        self.step_highlight_requested.emit("")

    def _show_failed_rows_dialog(self, failed_rows: list[dict]):
        """Tampilkan dialog daftar baris yang gagal dan opsi retry."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Failed Rows ({len(failed_rows)})")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel(
            f"{len(failed_rows)} baris gagal diproses.\n"
            "Anda bisa melewatkan baris ini atau mencoba input ulang."
        )
        info_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(info_label)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        
        content = "No. | Error Step | Error Message | Data (ringkas)\n"
        content += "-" * 80 + "\n"
        for i, row in enumerate(failed_rows, 1):
            row_number = row.get("row_number", i)
            error_step = row.get("error_step", "unknown")
            error_msg = row.get("error_message", "unknown")[:60]
            data = row.get("data", {})
            data_str = ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])[:60]
            content += f"{row_number} | {error_step} | {error_msg} | {data_str}\n"
        
        text.setText(content)
        layout.addWidget(text)
        
        btn_row = QHBoxLayout()
        
        retry_btn = QPushButton("Retry Failed Rows")
        retry_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; padding: 8px 16px;
                border-radius: 4px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background: #F57C00; }
        """)
        retry_btn.clicked.connect(lambda: self._retry_failed_rows(failed_rows, dialog))
        btn_row.addWidget(retry_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #607D8B; color: white; padding: 8px 16px;
                border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { background: #546E7A; }
        """)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        
        layout.addLayout(btn_row)
        dialog.exec()

    def _retry_failed_rows(self, failed_rows: list[dict], dialog: QDialog):
        """Retry hanya baris yang gagal."""
        dialog.accept()
        
        if not failed_rows:
            return
        
        row_numbers = [r.get("row_number") for r in failed_rows if r.get("row_number")]
        if not row_numbers:
            QMessageBox.warning(self, "Retry Failed", "Tidak ada nomor baris yang valid untuk retry.")
            return
        
        # Set row range ke baris yang gagal
        row_range_str = ",".join(str(n) for n in sorted(row_numbers))
        self.row_range_combo.setCurrentText("Custom")
        self.row_range_input.setText(row_range_str)
        self.row_range_input.setVisible(True)
        
        # Set skip_failed_rows tetap aktif agar retry bisa skip jika masih gagal
        self.skip_failed_rows_cb.setChecked(True)
        
        # Jalankan lagi
        self._start_execution()


class ExecutionWorker(QThread):
    """Worker thread untuk menjalankan workflow async."""

    finished = Signal(dict)
    progress_update = Signal(dict)
    log_update = Signal(dict)
    step_started = Signal(str)
    step_completed = Signal(str, str, str)  # step_id, status, message

    def __init__(self, engine: ExecutionEngine,
                 workflow: Optional[Workflow] = None,
                 start_url: str = "",
                 resume_from: Optional[str] = None):
        super().__init__()
        self.engine = engine
        self.workflow = workflow
        self.start_url = start_url
        self.resume_from = resume_from

        # Connect engine callbacks
        self.engine.set_progress_callback(lambda p: self.progress_update.emit(p))
        self.engine.set_log_callback(lambda l: self.log_update.emit(l))

    def run(self):
        """Run workflow execution."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if self.workflow:
                result = loop.run_until_complete(
                    self.engine.run(
                        self.workflow,
                        start_url=self.start_url,
                        resume_from=self.resume_from,
                    )
                )

                # Emit step completed for each result
                for step_result in result.get("results", []):
                    self.step_completed.emit(
                        step_result.get("step_id", ""),
                        step_result.get("status", "failed"),
                        step_result.get("message", ""),
                    )
            else:
                result = {"status": "no_workflow", "message": "No workflow loaded"}
        except Exception as e:
            result = {"status": "error", "message": str(e)}
        finally:
            loop.close()

        self.finished.emit(result)