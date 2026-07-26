"""
Monitoring Panel - Panel untuk melihat log, screenshot, dan progress.
Dilengkapi: filter log, search, thumbnail screenshot, execution time, export log, progress bar.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QSplitter, QScrollArea, QLineEdit, QComboBox, QProgressBar,
    QFrame, QFileDialog, QMessageBox, QSizePolicy, QDialog,
    QGridLayout, QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QTextCursor, QPixmap, QIcon, QTextCharFormat

import os
import json
from datetime import datetime


LOG_COLORS = {
    "INFO": QColor("#2196F3"),
    "SUCCESS": QColor("#4CAF50"),
    "WARNING": QColor("#FF9800"),
    "ERROR": QColor("#f44336"),
    "DEBUG": QColor("#999"),
}

LOG_LEVELS = ["ALL", "INFO", "SUCCESS", "WARNING", "ERROR", "DEBUG"]


class ScreenshotPreviewDialog(QDialog):
    """Dialog untuk preview screenshot dengan ukuran lebih besar."""

    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Screenshot Preview - {os.path.basename(filepath)}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            scaled = pixmap.scaled(760, 520, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("(Cannot load image)")
        layout.addWidget(self.image_label)

        # Info
        info_label = QLabel(f"File: {os.path.basename(filepath)}")
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 4px;")
        layout.addWidget(info_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Open)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Open).clicked.connect(lambda: self._open_file(filepath))
        layout.addWidget(buttons)

    def _open_file(self, filepath: str):
        """Buka file dengan aplikasi default."""
        if os.path.exists(filepath):
            os.startfile(filepath)


class LogFilterWidget(QWidget):
    """Widget untuk filter dan search log."""

    filter_changed = Signal(str, str)  # level, search_text

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(6)

        # Level filter
        layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(LOG_LEVELS)
        self.level_combo.setCurrentText("ALL")
        self.level_combo.setFixedWidth(90)
        self.level_combo.currentTextChanged.connect(self._emit_filter)
        layout.addWidget(self.level_combo)

        # Search
        layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search log messages...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._emit_filter)
        layout.addWidget(self.search_input)

        layout.addStretch()

        # Export button
        self.export_btn = QPushButton("Export Log")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #607D8B; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #546E7A; }
        """)
        layout.addWidget(self.export_btn)

    def _emit_filter(self):
        self.filter_changed.emit(self.level_combo.currentText(), self.search_input.text())


class MonitoringPanel(QWidget):
    """Panel untuk monitoring eksekusi workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitoring")

        # Internal state
        self._all_logs = []  # Store all logs for filtering
        self._execution_start_time = None
        self._execution_end_time = None
        self._total_steps = 0
        self._completed_steps = 0
        self._failed_steps = 0
        self._skipped_steps = 0
        self._current_status = "idle"

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

        # ==================== LOG TAB ====================
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(4, 4, 4, 4)
        log_layout.setSpacing(4)

        # Log toolbar
        log_toolbar = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear")
        self.clear_log_btn.setStyleSheet("""
            QPushButton { background: #f44336; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #d32f2f; }
        """)
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_toolbar.addWidget(self.clear_log_btn)

        self.log_count_label = QLabel("0 entries")
        self.log_count_label.setStyleSheet("color: #999; font-size: 10px;")
        log_toolbar.addWidget(self.log_count_label)
        log_toolbar.addStretch()
        log_layout.addLayout(log_toolbar)

        # Filter widget
        self.log_filter = LogFilterWidget()
        self.log_filter.filter_changed.connect(self._apply_log_filter)
        self.log_filter.export_btn.clicked.connect(self._export_log)
        log_layout.addWidget(self.log_filter)

        # Log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.document().setMaximumBlockCount(5000)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.log_text)

        self.tabs.addTab(self.log_widget, "Log")

        # ==================== SCREENSHOTS TAB ====================
        self.screenshot_widget = QWidget()
        screenshot_layout = QVBoxLayout(self.screenshot_widget)
        screenshot_layout.setContentsMargins(4, 4, 4, 4)
        screenshot_layout.setSpacing(4)

        # Screenshot toolbar
        ss_toolbar = QHBoxLayout()
        self.refresh_screenshot_btn = QPushButton("Refresh")
        self.refresh_screenshot_btn.setStyleSheet("""
            QPushButton { background: #2196F3; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #1976D2; }
        """)
        self.refresh_screenshot_btn.clicked.connect(self._refresh_screenshots)
        ss_toolbar.addWidget(self.refresh_screenshot_btn)

        self.ss_count_label = QLabel("0 screenshots")
        self.ss_count_label.setStyleSheet("color: #999; font-size: 10px;")
        ss_toolbar.addWidget(self.ss_count_label)
        ss_toolbar.addStretch()

        # Delete all button
        self.delete_all_ss_btn = QPushButton("Delete All")
        self.delete_all_ss_btn.setStyleSheet("""
            QPushButton { background: #f44336; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #d32f2f; }
        """)
        self.delete_all_ss_btn.clicked.connect(self._delete_all_screenshots)
        ss_toolbar.addWidget(self.delete_all_ss_btn)
        screenshot_layout.addLayout(ss_toolbar)

        # Screenshot list with thumbnails
        self.screenshot_list = QListWidget()
        self.screenshot_list.setIconSize(QSize(120, 80))
        self.screenshot_list.setViewMode(QListWidget.ListMode)
        self.screenshot_list.setSpacing(4)
        self.screenshot_list.itemDoubleClicked.connect(self._open_screenshot)
        self.screenshot_list.setStyleSheet("""
            QListWidget {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background: #e3f2fd;
            }
        """)
        screenshot_layout.addWidget(self.screenshot_list)

        # Preview area (small thumbnail)
        self.ss_preview_label = QLabel()
        self.ss_preview_label.setAlignment(Qt.AlignCenter)
        self.ss_preview_label.setFixedHeight(160)
        self.ss_preview_label.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                color: #999;
                font-size: 10px;
            }
        """)
        self.ss_preview_label.setText("Double-click a screenshot to preview\nor click to select")
        screenshot_layout.addWidget(self.ss_preview_label)

        # Connect selection change to preview
        self.screenshot_list.currentItemChanged.connect(self._on_screenshot_selected)

        self.tabs.addTab(self.screenshot_widget, "Screenshots")

        # ==================== SUMMARY TAB ====================
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        summary_layout.setContentsMargins(4, 4, 4, 4)
        summary_layout.setSpacing(4)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 6px;
                text-align: center;
                background: #f0f0f0;
                font-weight: bold;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 5px;
            }
        """)
        summary_layout.addWidget(self.progress_bar)

        # Stats grid
        stats_widget = QWidget()
        stats_widget.setStyleSheet("""
            QWidget { background: #fafafa; border: 1px solid #e0e0e0;
                border-radius: 6px; padding: 8px; }
        """)
        stats_grid = QGridLayout(stats_widget)
        stats_grid.setSpacing(8)

        # Status
        stats_grid.addWidget(QLabel("Status:"), 0, 0)
        self.status_value = QLabel("Idle")
        self.status_value.setStyleSheet("font-weight: bold; color: #666;")
        stats_grid.addWidget(self.status_value, 0, 1)

        # Duration
        stats_grid.addWidget(QLabel("Duration:"), 0, 2)
        self.duration_value = QLabel("00:00:00")
        self.duration_value.setStyleSheet("font-weight: bold; color: #666;")
        stats_grid.addWidget(self.duration_value, 0, 3)

        # Progress
        stats_grid.addWidget(QLabel("Progress:"), 1, 0)
        self.progress_value = QLabel("0%")
        self.progress_value.setStyleSheet("font-weight: bold; color: #2196F3;")
        stats_grid.addWidget(self.progress_value, 1, 1)

        # Total steps
        stats_grid.addWidget(QLabel("Total Steps:"), 1, 2)
        self.total_steps_value = QLabel("0")
        self.total_steps_value.setStyleSheet("font-weight: bold; color: #666;")
        stats_grid.addWidget(self.total_steps_value, 1, 3)

        # Completed
        stats_grid.addWidget(QLabel("Completed:"), 2, 0)
        self.completed_value = QLabel("0")
        self.completed_value.setStyleSheet("font-weight: bold; color: #4CAF50;")
        stats_grid.addWidget(self.completed_value, 2, 1)

        # Failed
        stats_grid.addWidget(QLabel("Failed:"), 2, 2)
        self.failed_value = QLabel("0")
        self.failed_value.setStyleSheet("font-weight: bold; color: #f44336;")
        stats_grid.addWidget(self.failed_value, 2, 3)

        # Skipped
        stats_grid.addWidget(QLabel("Skipped:"), 3, 0)
        self.skipped_value = QLabel("0")
        self.skipped_value.setStyleSheet("font-weight: bold; color: #FF9800;")
        stats_grid.addWidget(self.skipped_value, 3, 1)

        summary_layout.addWidget(stats_widget)

        # Summary text (detailed log)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Consolas", 9))
        self.summary_text.setMaximumHeight(200)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 4px;
            }
        """)
        summary_layout.addWidget(self.summary_text)

        # Reset button
        self.reset_summary_btn = QPushButton("Reset Summary")
        self.reset_summary_btn.setStyleSheet("""
            QPushButton { background: #607D8B; color: white; border: none;
                border-radius: 3px; padding: 6px; font-size: 10px;
            }
            QPushButton:hover { background: #546E7A; }
        """)
        self.reset_summary_btn.clicked.connect(self._reset_summary)
        summary_layout.addWidget(self.reset_summary_btn)

        self.tabs.addTab(self.summary_widget, "Summary")

        layout.addWidget(self.tabs)

        # Timer for duration update
        self._duration_timer = QTimer()
        self._duration_timer.timeout.connect(self._update_duration_display)
        self._duration_timer.setInterval(1000)

    # ==================== LOG METHODS ====================

    def add_log(self, log_data: dict):
        """Tambah entry log ke display."""
        self._all_logs.append(log_data)

        level = log_data.get("level", "INFO")
        message = log_data.get("message", "")
        timestamp = log_data.get("timestamp", "")
        step_id = log_data.get("step_id", "")

        # Format log line
        time_str = ""
        if "T" in timestamp:
            try:
                time_str = timestamp.split("T")[1][:8]
            except IndexError:
                time_str = timestamp
        else:
            time_str = timestamp

        step_str = f"[{step_id}] " if step_id else ""
        log_line = f"{time_str} | {level:8s} | {step_str}{message}\n"

        # Apply current filter
        current_level = self.log_filter.level_combo.currentText()
        current_search = self.log_filter.search_input.text().lower()

        if current_level != "ALL" and level != current_level:
            return  # Skip, filtered out

        if current_search and current_search not in message.lower():
            return  # Skip, search filtered out

        # Set color
        color = LOG_COLORS.get(level, QColor("#d4d4d4"))
        self._append_colored_text(log_line, color)

        # Update count
        visible_count = self.log_text.document().blockCount()
        self.log_count_label.setText(f"{visible_count} visible / {len(self._all_logs)} total")

        # Auto-scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

        # Auto-refresh screenshots
        if "Screenshot saved:" in message:
            self._refresh_screenshots()

    def _append_colored_text(self, text: str, color: QColor):
        """Append text dengan warna tertentu."""
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, fmt)

    def _apply_log_filter(self, level: str, search_text: str):
        """Apply filter ke semua log."""
        self.log_text.clear()

        for log_data in self._all_logs:
            log_level = log_data.get("level", "INFO")
            message = log_data.get("message", "")
            timestamp = log_data.get("timestamp", "")
            step_id = log_data.get("step_id", "")

            # Level filter
            if level != "ALL" and log_level != level:
                continue

            # Search filter
            if search_text and search_text.lower() not in message.lower():
                continue

            # Format
            time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
            step_str = f"[{step_id}] " if step_id else ""
            log_line = f"{time_str} | {log_level:8s} | {step_str}{message}\n"

            color = LOG_COLORS.get(log_level, QColor("#d4d4d4"))
            self._append_colored_text(log_line, color)

        visible_count = self.log_text.document().blockCount()
        self.log_count_label.setText(f"{visible_count} visible / {len(self._all_logs)} total")

    def _export_log(self):
        """Export log ke file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Log", "logs/execution_log.txt",
            "Text Files (*.txt);;JSON Lines (*.jsonl);;All Files (*)"
        )
        if not filepath:
            return

        try:
            if filepath.endswith(".jsonl"):
                with open(filepath, "w", encoding="utf-8") as f:
                    for log_data in self._all_logs:
                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    for log_data in self._all_logs:
                        level = log_data.get("level", "INFO")
                        message = log_data.get("message", "")
                        timestamp = log_data.get("timestamp", "")
                        step_id = log_data.get("step_id", "")
                        time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
                        f.write(f"{time_str} | {level:8s} | {message}\n")

            QMessageBox.information(self, "Export Success",
                f"Log exported to:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed",
                f"Failed to export log:\n{str(e)}")

    def _clear_log(self):
        """Bersihkan log."""
        self._all_logs.clear()
        self.log_text.clear()
        self.log_count_label.setText("0 entries")

    # ==================== SCREENSHOT METHODS ====================

    def _refresh_screenshots(self):
        """Refresh daftar screenshot dengan thumbnail."""
        screenshots_dir = "screenshots"

        self.screenshot_list.clear()

        if not os.path.exists(screenshots_dir):
            self.ss_count_label.setText("0 screenshots")
            return

        count = 0
        for f in sorted(os.listdir(screenshots_dir), reverse=True):
            if f.endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(screenshots_dir, f)
                item = QListWidgetItem(f)
                item.setToolTip(filepath)

                # Create thumbnail
                pixmap = QPixmap(filepath)
                if not pixmap.isNull():
                    thumb = pixmap.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(thumb))

                # Set file size info
                try:
                    size = os.path.getsize(filepath)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    item.setToolTip(f"{filepath}\nSize: {size_str}")
                except OSError:
                    pass

                self.screenshot_list.addItem(item)
                count += 1

        self.ss_count_label.setText(f"{count} screenshots")

    def _on_screenshot_selected(self, current, previous):
        """Tampilkan preview saat screenshot dipilih."""
        if current is None:
            self.ss_preview_label.setText("Double-click a screenshot to preview\nor click to select")
            return

        filepath = current.toolTip().split("\n")[0]  # Get first line (path)
        if os.path.exists(filepath):
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                scaled = pixmap.scaled(400, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.ss_preview_label.setPixmap(scaled)
                self.ss_preview_label.setFixedHeight(160)
                return

        self.ss_preview_label.setText(f"(Cannot load: {os.path.basename(filepath)})")

    def _open_screenshot(self, item: QListWidgetItem):
        """Buka screenshot dengan dialog preview."""
        tooltip = item.toolTip()
        filepath = tooltip.split("\n")[0]  # Get first line (path)

        if os.path.exists(filepath):
            dialog = ScreenshotPreviewDialog(filepath, self)
            dialog.exec()

    def _delete_all_screenshots(self):
        """Hapus semua screenshot."""
        reply = QMessageBox.question(
            self, "Delete All Screenshots",
            "Are you sure you want to delete all screenshots?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            screenshots_dir = "screenshots"
            if os.path.exists(screenshots_dir):
                deleted = 0
                for f in os.listdir(screenshots_dir):
                    if f.endswith((".png", ".jpg", ".jpeg")):
                        try:
                            os.remove(os.path.join(screenshots_dir, f))
                            deleted += 1
                        except OSError:
                            pass
                self._refresh_screenshots()
                QMessageBox.information(self, "Deleted",
                    f"Deleted {deleted} screenshot(s).")

    # ==================== SUMMARY / PROGRESS METHODS ====================

    def update_progress(self, progress: dict):
        """Update summary dengan progress terbaru."""
        status = progress.get("status", "N/A")
        percentage = progress.get("percentage", 0)
        step_id = progress.get("step_id", "")
        completed = progress.get("completed_steps", 0)
        total = progress.get("total_steps", 0)
        failed = progress.get("failed_steps", 0)
        skipped = progress.get("skipped_steps", 0)

        # Update state
        self._current_status = status
        self._total_steps = total
        self._completed_steps = completed
        self._failed_steps = failed
        self._skipped_steps = skipped

        # Track execution time
        if status == "running" and self._execution_start_time is None:
            self._execution_start_time = datetime.now()
            self._duration_timer.start()
        elif status in ("success", "failed", "completed_with_errors", "stopped"):
            if self._execution_end_time is None:
                self._execution_end_time = datetime.now()
            self._duration_timer.stop()

        # Update progress bar
        self.progress_bar.setValue(int(percentage))
        self.progress_value.setText(f"{percentage:.1f}%")

        # Update status
        status_color = {
            "running": "#2196F3",
            "success": "#4CAF50",
            "failed": "#f44336",
            "completed_with_errors": "#FF9800",
            "stopped": "#607D8B",
            "idle": "#666",
        }.get(status, "#666")
        self.status_value.setText(status.upper())
        self.status_value.setStyleSheet(f"font-weight: bold; color: {status_color};")

        # Update counts
        self.total_steps_value.setText(str(total))
        self.completed_value.setText(str(completed))
        self.failed_value.setText(str(failed))
        self.skipped_value.setText(str(skipped))

        # Update summary text
        summary_text = (
            f"Time: {self.duration_value.text()}\n"
            f"Status: {status}\n"
            f"Progress: {percentage:.1f}%\n"
            f"Step: {step_id}\n"
            f"Completed: {completed}/{total}\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}\n"
        )
        if status in ("success", "failed", "completed_with_errors"):
            if self._execution_start_time and self._execution_end_time:
                duration = (self._execution_end_time - self._execution_start_time).total_seconds()
                summary_text += f"\nTotal Duration: {self._format_duration(duration)}\n"

        self.summary_text.setPlainText(summary_text)

    def _update_duration_display(self):
        """Update display durasi setiap detik."""
        if self._execution_start_time:
            now = self._execution_end_time or datetime.now()
            duration = (now - self._execution_start_time).total_seconds()
            self.duration_value.setText(self._format_duration(duration))

    def _format_duration(self, seconds: float) -> str:
        """Format detik ke HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _reset_summary(self):
        """Reset semua data summary."""
        self._execution_start_time = None
        self._execution_end_time = None
        self._total_steps = 0
        self._completed_steps = 0
        self._failed_steps = 0
        self._skipped_steps = 0
        self._current_status = "idle"
        self._duration_timer.stop()

        self.progress_bar.setValue(0)
        self.progress_value.setText("0%")
        self.status_value.setText("IDLE")
        self.status_value.setStyleSheet("font-weight: bold; color: #666;")
        self.duration_value.setText("00:00:00")
        self.total_steps_value.setText("0")
        self.completed_value.setText("0")
        self.failed_value.setText("0")
        self.skipped_value.setText("0")
        self.summary_text.clear()

    def clear(self):
        """Bersihkan semua monitoring."""
        self._all_logs.clear()
        self.log_text.clear()
        self.log_count_label.setText("0 entries")
        self.summary_text.clear()
        self.screenshot_list.clear()
        self.ss_count_label.setText("0 screenshots")
        self.ss_preview_label.setText("Double-click a screenshot to preview\nor click to select")
        self._reset_summary()

    def toggleViewAction(self):
        """Return action untuk toggle visibility."""
        from PySide6.QtGui import QAction
        action = QAction("Monitoring Panel", self)
        action.setCheckable(True)
        action.setChecked(self.isVisible())
        action.triggered.connect(self.setVisible)
        return action
