"""
Monitoring Panel - Panel untuk melihat log, screenshot, dan progress.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QSplitter, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextCursor


LOG_COLORS = {
    "INFO": QColor("#2196F3"),
    "SUCCESS": QColor("#4CAF50"),
    "WARNING": QColor("#FF9800"),
    "ERROR": QColor("#f44336"),
    "DEBUG": QColor("#999"),
}


class MonitoringPanel(QWidget):
    """Panel untuk monitoring eksekusi workflow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitoring")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("Monitoring")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Log tab
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(4, 4, 4, 4)
        
        # Log toolbar
        log_toolbar = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear")
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_toolbar.addWidget(self.clear_log_btn)
        log_toolbar.addStretch()
        log_layout.addLayout(log_toolbar)
        
        # Log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.document().setMaximumBlockCount(1000)
        log_layout.addWidget(self.log_text)
        
        self.tabs.addTab(self.log_widget, "Log")
        
        # Screenshots tab
        self.screenshot_widget = QWidget()
        screenshot_layout = QVBoxLayout(self.screenshot_widget)
        screenshot_layout.setContentsMargins(4, 4, 4, 4)
        
        self.screenshot_list = QListWidget()
        self.screenshot_list.itemDoubleClicked.connect(self._open_screenshot)
        screenshot_layout.addWidget(self.screenshot_list)
        
        self.refresh_screenshot_btn = QPushButton("Refresh")
        self.refresh_screenshot_btn.clicked.connect(self._refresh_screenshots)
        screenshot_layout.addWidget(self.refresh_screenshot_btn)
        
        self.tabs.addTab(self.screenshot_widget, "Screenshots")
        
        # Summary tab
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        summary_layout.setContentsMargins(4, 4, 4, 4)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Consolas", 9))
        summary_layout.addWidget(self.summary_text)
        
        self.tabs.addTab(self.summary_widget, "Summary")
        
        layout.addWidget(self.tabs)
    
    def add_log(self, log_data: dict):
        """Tambah entry log ke display."""
        level = log_data.get("level", "INFO")
        message = log_data.get("message", "")
        timestamp = log_data.get("timestamp", "")
        step_id = log_data.get("step_id", "")
        
        # Format log line
        time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
        step_str = f"[{step_id}] " if step_id else ""
        log_line = f"{time_str} | {level:8s} | {step_str}{message}\n"
        
        # Set color
        color = LOG_COLORS.get(level, QColor("#333"))
        
        # Append to log
        self.log_text.setTextColor(color)
        self.log_text.insertPlainText(log_line)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        
        # Auto-refresh screenshots when a new screenshot is saved
        if "Screenshot saved:" in message:
            self._refresh_screenshots()
    
    def update_progress(self, progress: dict):
        """Update summary dengan progress terbaru."""
        summary = (
            f"Status: {progress.get('status', 'N/A')}\n"
            f"Progress: {progress.get('percentage', 0):.1f}%\n"
            f"Step: {progress.get('step_id', 'N/A')}\n"
            f"Completed: {progress.get('completed_steps', 0)}/{progress.get('total_steps', 0)}\n"
            f"Failed: {progress.get('failed_steps', 0)}\n"
            f"Skipped: {progress.get('skipped_steps', 0)}\n"
        )
        self.summary_text.setPlainText(summary)
    
    def _clear_log(self):
        """Bersihkan log."""
        self.log_text.clear()
    
    def _refresh_screenshots(self):
        """Refresh daftar screenshot."""
        import os
        screenshots_dir = "screenshots"
        
        self.screenshot_list.clear()
        
        if not os.path.exists(screenshots_dir):
            return
        
        for f in sorted(os.listdir(screenshots_dir), reverse=True):
            if f.endswith((".png", ".jpg", ".jpeg")):
                item = QListWidgetItem(f)
                item.setToolTip(os.path.join(screenshots_dir, f))
                self.screenshot_list.addItem(item)
    
    def _open_screenshot(self, item: QListWidgetItem):
        """Buka screenshot dengan aplikasi default."""
        import subprocess
        import os
        
        filepath = item.toolTip()
        if os.path.exists(filepath):
            os.startfile(filepath)
    
    def clear(self):
        """Bersihkan semua monitoring."""
        self.log_text.clear()
        self.summary_text.clear()
        self.screenshot_list.clear()
    
    def toggleViewAction(self):
        """Return action untuk toggle visibility."""
        from PySide6.QtGui import QAction
        action = QAction("Monitoring Panel", self)
        action.setCheckable(True)
        action.setChecked(self.isVisible())
        action.triggered.connect(self.setVisible)
        return action