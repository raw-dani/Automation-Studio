"""
License Dialog - Dialog untuk aktivasi dan status lisensi.
"""

import hashlib
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame, QGridLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from backend.license.fingerprint import get_fingerprint


class LicenseDialog(QDialog):
    """Dialog untuk aktivasi dan manajemen lisensi."""

    license_activated = Signal()
    license_deactivated = Signal()

    def __init__(self, license_manager, usage_tracker, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.usage_tracker = usage_tracker
        self.setWindowTitle("License Management")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self._update_status()

    def _init_ui(self):
        """Inisialisasi UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("License Management")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        # Status section
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)

        self.status_icon = QLabel("🔓")
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(self.status_icon)

        self.status_text = QLabel("Checking...")
        self.status_text.setAlignment(Qt.AlignCenter)
        self.status_text.setWordWrap(True)
        self.status_text.setStyleSheet("font-size: 12px; color: #495057;")
        status_layout.addWidget(self.status_text)

        layout.addWidget(self.status_frame)

        # License Key input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("License Key:"))

        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.license_key_input.setFixedWidth(250)
        self.license_key_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)
        input_layout.addWidget(self.license_key_input)

        layout.addLayout(input_layout)

        # Hardware fingerprint
        fp_layout = QHBoxLayout()
        fp_layout.addWidget(QLabel("Fingerprint:"))
        self.fingerprint_label = QLabel(get_fingerprint()[:32] + "...")
        self.fingerprint_label.setStyleSheet("""
            QLabel {
                font-family: Consolas, monospace;
                font-size: 10px;
                color: #6c757d;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        fp_layout.addWidget(self.fingerprint_label, 1)
        layout.addLayout(fp_layout)

        # Info text
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(80)
        self.info_text.setStyleSheet("""
            QTextEdit {
                background: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #004085;
            }
        """)
        layout.addWidget(self.info_text)

        # Buttons
        btn_layout = QHBoxLayout()

        self.activate_btn = QPushButton("Activate")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.activate_btn.clicked.connect(self._activate_license)
        btn_layout.addWidget(self.activate_btn)

        self.deactivate_btn = QPushButton("Deactivate")
        self.deactivate_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        self.deactivate_btn.clicked.connect(self._deactivate_license)
        btn_layout.addWidget(self.deactivate_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.refresh_btn.clicked.connect(self._update_status)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #e2e6ea;
                color: #333;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover { background: #dae0e5; }
        """)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _update_status(self):
        """Update status lisensi."""
        status = self.license_manager.get_status()

        if status.get("licensed"):
            self.status_icon.setText("🔒")
            self.status_icon.setStyleSheet("font-size: 32px; color: #28a745;")
            self.status_text.setText("✅ Licensed\nMode: Unlimited (no data limit)")
            self.status_text.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
            self.info_text.setHtml(
                "<b>Lisensi Aktif</b><br>"
                "Aplikasi berjalan dalam mode Licensed tanpa batasan data.<br>"
                "1 lisensi = 1 komputer (hardware binding)."
            )
            self.activate_btn.setEnabled(False)
            self.deactivate_btn.setEnabled(True)
        else:
            self.status_icon.setText("🔓")
            self.status_icon.setStyleSheet("font-size: 32px; color: #ffc107;")
            remaining = self.usage_tracker.get_remaining_quota()
            self.status_text.setText(
                f"⚠️ Free Mode\n"
                f"Sisa kuota hari ini: {remaining}/10 data"
            )
            self.status_text.setStyleSheet("font-size: 12px; color: #ffc107; font-weight: bold;")
            self.info_text.setHtml(
                "<b>Mode Gratis</b><br>"
                "Aplikasi berjalan dalam mode Free dengan batasan 10 data/hari.<br>"
                "Aktifkan lisensi untuk menghapus batasan.<br>"
                "Dapatkan lisensi di: <a href='https://id.gmteknologi.com'>https://id.gmteknologi.com</a>"
            )
            self.activate_btn.setEnabled(True)
            self.deactivate_btn.setEnabled(False)

    def _activate_license(self):
        """Aktivasi lisensi."""
        license_key = self.license_key_input.text().strip()
        if not license_key:
            QMessageBox.warning(self, "Warning", "Masukkan license key terlebih dahulu.")
            return

        result = self.license_manager.activate(license_key)
        if result.get("success"):
            QMessageBox.information(self, "Success", result.get("message", "License activated"))
            self.license_activated.emit()
            self._update_status()
        else:
            QMessageBox.critical(self, "Error", result.get("message", "Activation failed"))

    def _deactivate_license(self):
        """Deaktivasi lisensi."""
        reply = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Apakah Anda yakin ingin menonaktifkan lisensi?\n"
            "Lisensi akan dilepaskan dari komputer ini.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            result = self.license_manager.deactivate()
            if result.get("success"):
                QMessageBox.information(self, "Success", result.get("message", "License deactivated"))
                self.license_deactivated.emit()
                self._update_status()
            else:
                QMessageBox.warning(self, "Warning", result.get("message", "Deactivation failed"))