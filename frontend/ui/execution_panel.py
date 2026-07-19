"""
Execution Panel - Panel untuk mengontrol eksekusi workflow (Start/Stop/Pause).
"""

import asyncio
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QLineEdit,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont

from backend.core.engine import ExecutionEngine
from backend.core.workflow_parser import Workflow


class ExecutionPanel(QWidget):
    """Panel kontrol untuk menjalankan workflow."""
    
    log_received = Signal(dict)
    progress_received = Signal(dict)
    execution_started = Signal()
    execution_stopped = Signal()
    save_requested = Signal(str)
    before_run = Signal()
    
    def __init__(self, engine: ExecutionEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.current_workflow = None
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
        
        # URL label
        self.url_label = QLabel("")
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setStyleSheet("color: #1565C0; font-size: 11px; padding: 4px;")
        self.url_label.setWordWrap(True)
        layout.addWidget(self.url_label)
        
        # URL input
        url_input_layout = QHBoxLayout()
        url_input_layout.addWidget(QLabel("Start URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/login")
        url_input_layout.addWidget(self.url_input)
        layout.addLayout(url_input_layout)
        
        # Save button
        self.save_url_btn = QPushButton("Save")
        self.save_url_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; color: white; padding: 6px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #1976D2; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.save_url_btn.clicked.connect(self._save_properties)
        layout.addWidget(self.save_url_btn)
        
        # Save feedback label
        self.save_feedback_label = QLabel("")
        self.save_feedback_label.setAlignment(Qt.AlignCenter)
        self.save_feedback_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 4px;")
        self.save_feedback_label.setWordWrap(True)
        layout.addWidget(self.save_feedback_label)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.start_btn.clicked.connect(self._start_execution)
        btn_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #F57C00; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.pause_btn.clicked.connect(self._toggle_pause)
        btn_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #f44336; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #d32f2f; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_execution)
        btn_layout.addWidget(self.stop_btn)
        
        self.force_close_btn = QPushButton("Force Close Browser")
        self.force_close_btn.setEnabled(False)
        self.force_close_btn.setStyleSheet("""
            QPushButton {
                background: #B71C1C; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #7F0000; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.force_close_btn.clicked.connect(self._force_close_browser)
        btn_layout.addWidget(self.force_close_btn)
        
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd; border-radius: 4px;
                text-align: center; height: 24px;
            }
            QProgressBar::chunk {
                background: #4CAF50; border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Current step
        self.step_label = QLabel("")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(self.step_label)
        
        layout.addStretch()
    
    def _start_execution(self):
        """Mulai eksekusi workflow."""
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.force_close_btn.setEnabled(True)
        self.status_label.setText("Running...")
        
        # Run in background using QTimer
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
        
        # Reload workflow from file before running
        self.before_run.emit()
        
        start_url = self.url_input.text().strip()
        
        # Create and start async worker
        self._worker = ExecutionWorker(self.engine, self.current_workflow, start_url=start_url)
        self._worker.finished.connect(self._on_execution_finished)
        self._worker.progress_update.connect(self._update_progress)
        self._worker.log_update.connect(self._update_log)
        self._worker.start()
    
    def set_workflow(self, workflow: Optional[Workflow]):
        """Set workflow yang akan dijalankan."""
        self.current_workflow = workflow
        if workflow:
            self.status_label.setText(f"Ready: {workflow.name} ({len(workflow.steps)} steps)")
            if workflow.url:
                self.url_label.setText(f"URL: {workflow.url}")
            else:
                self.url_label.setText("")
        else:
            self.status_label.setText("Ready")
            self.url_label.setText("")
    
    def _toggle_pause(self):
        """Toggle pause/resume."""
        if self.engine.is_paused:
            self.engine.resume()
            self.pause_btn.setText("Pause")
            self.status_label.setText("Running...")
        else:
            self.engine.pause()
            self.pause_btn.setText("Resume")
            self.status_label.setText("Paused")
    
    def _stop_execution(self):
        """Hentikan eksekusi."""
        self.engine.stop()
        self._reset_buttons()
        self.status_label.setText("Stopped")
        self.execution_stopped.emit()
    
    def _force_close_browser(self):
        """Force close browser dan hentikan eksekusi."""
        self.engine.stop()
        if hasattr(self, '_worker') and self._worker:
            self._worker.terminate()
        self._reset_buttons()
        self.status_label.setText("Force Closed")
        self.execution_stopped.emit()
    
    def _update_progress(self, progress: dict):
        """Update progress bar."""
        self.progress_bar.setValue(int(progress.get("percentage", 0)))
        self.step_label.setText(f"Step: {progress.get('step_id', '')} - {progress.get('status', '')}")
        self.progress_received.emit(progress)
    
    def _update_log(self, log: dict):
        """Forward log."""
        self.log_received.emit(log)
    
    def _on_execution_finished(self, result: dict):
        """Handle execution selesai."""
        self._reset_buttons()
        
        status = result.get("status", "unknown")
        if status == "success":
            self.status_label.setText("Completed Successfully")
            self.progress_bar.setValue(100)
        elif status == "completed_with_errors":
            self.status_label.setText("Completed with Errors")
        else:
            self.status_label.setText(f"Failed: {status}")
        
        self.execution_stopped.emit()
    
    def _reset_buttons(self):
        """Reset button states."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.stop_btn.setEnabled(False)
        self.force_close_btn.setEnabled(False)
    
    def _save_properties(self):
        """Save workflow properties."""
        url = self.url_input.text().strip()
        self.save_feedback_label.clear()
        self.save_requested.emit(url)
    
    def show_save_feedback(self, success: bool, message: str):
        """Show save success or error feedback."""
        if success:
            self.save_feedback_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 4px; font-weight: bold;")
        else:
            self.save_feedback_label.setStyleSheet("color: #f44336; font-size: 11px; padding: 4px; font-weight: bold;")
        self.save_feedback_label.setText(message)


class ExecutionWorker(QThread):
    """Worker thread untuk menjalankan workflow async."""
    
    finished = Signal(dict)
    progress_update = Signal(dict)
    log_update = Signal(dict)
    
    def __init__(self, engine: ExecutionEngine, workflow: Optional[Workflow] = None, start_url: str = ""):
        super().__init__()
        self.engine = engine
        self.workflow = workflow
        self.start_url = start_url
        
        # Connect engine callbacks
        self.engine.set_progress_callback(lambda p: self.progress_update.emit(p))
        self.engine.set_log_callback(lambda l: self.log_update.emit(l))
    
    def run(self):
        """Run workflow execution."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if self.workflow:
                result = loop.run_until_complete(self.engine.run(self.workflow, start_url=self.start_url))
            else:
                result = {"status": "no_workflow", "message": "No workflow loaded"}
        except Exception as e:
            result = {"status": "error", "message": str(e)}
        finally:
            loop.close()
        
        self.finished.emit(result)