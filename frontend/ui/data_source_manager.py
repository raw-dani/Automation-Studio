"""
Data Source Manager - Panel untuk mengelola koneksi data source.
Dilengkapi: Database, API, encoding, column mapping, variable helper, row count.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
    QFormLayout, QSpinBox, QCheckBox, QTextEdit, QSplitter,
    QScrollArea, QFrame, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QClipboard


class DataSourceManager(QWidget):
    """Panel untuk mengkonfigurasi data source workflow."""

    data_source_changed = Signal(dict)
    variable_copied = Signal(str)  # Emit when user copies a variable reference

    # Supported data source types with their display names
    SOURCE_TYPES = [
        ("None", "No Data Source"),
        ("Excel", "Excel (.xlsx/.xls)"),
        ("CSV", "CSV (.csv)"),
        ("Database", "Database (MySQL/PostgreSQL/SQLite)"),
        ("API", "REST API"),
    ]

    # Deskripsi per tipe data source
    SOURCE_DESCRIPTIONS = {
        "None": "Tidak menggunakan data source. Workflow akan berjalan tanpa data eksternal.",
        "Excel": "Baca data dari file Excel (.xlsx/.xls). Pilih sheet dan kolom yang akan digunakan.",
        "CSV": "Baca data dari file CSV. Tentukan delimiter dan encoding yang sesuai.",
        "Database": "Hubungkan ke database (MySQL, PostgreSQL, SQLite, MSSQL) dan jalankan query.",
        "API": "Ambil data dari REST API. Dukung GET, POST, PUT, DELETE dan pagination.",
    }

    # Deskripsi per field
    FIELD_DESCRIPTIONS = {
        "file_path": "Path lengkap file Excel/CSV yang akan dibaca",
        "sheet": "Nama sheet di file Excel yang akan dibaca",
        "delimiter": "Karakter pemisah antar kolom di file CSV (default: koma)",
        "encoding": "Encoding karakter file CSV (default: utf-8)",
        "driver": "Jenis database yang digunakan",
        "host": "Alamat server database (localhost untuk lokal)",
        "port": "Port koneksi database",
        "database": "Nama database yang akan diakses",
        "username": "Username untuk autentikasi database",
        "password": "Password untuk autentikasi database",
        "query": "SQL query untuk mengambil data (contoh: SELECT * FROM table)",
        "method": "HTTP method untuk request API",
        "url": "URL endpoint API",
        "headers": "HTTP headers dalam format JSON (contoh: {\"Authorization\": \"Bearer token\"})",
        "body": "Request body dalam format JSON (untuk POST/PUT)",
        "pagination": "Aktifkan pagination untuk mengambil semua halaman data",
        "page_param": "Nama parameter query untuk nomor halaman",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = {}
        self._preview_data_rows = []
        self._loading_config = False  # Flag untuk set_config dari workflow
        self.setWindowTitle("Data Source")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ==================== TITLE ====================
        title = QLabel("Data Source")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)

        # ==================== TYPE SELECTOR ====================
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        for value, display in self.SOURCE_TYPES:
            self.type_combo.addItem(display, value)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # ==================== TYPE DESCRIPTION ====================
        self.type_desc_label = QLabel("")
        self.type_desc_label.setWordWrap(True)
        self.type_desc_label.setStyleSheet("""
            color: #64748B; font-size: 9px;
            background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 4px; padding: 6px 8px;
        """)
        layout.addWidget(self.type_desc_label)

        # ==================== EXCEL / CSV CONFIG ====================
        self.file_group = QGroupBox("File Configuration")
        self.file_layout = QVBoxLayout(self.file_group)
        self.file_layout.setContentsMargins(6, 10, 6, 6)
        self.file_layout.setSpacing(4)

        # File path row
        file_row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select file...")
        self.file_path.setToolTip(self.FIELD_DESCRIPTIONS["file_path"])
        self.file_path.textChanged.connect(self._on_config_changed)
        file_row.addWidget(self.file_path)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #1976D2; }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self.browse_btn)

        self.file_layout.addLayout(file_row)

        # Excel options row
        self.excel_options = QWidget()
        excel_layout = QHBoxLayout(self.excel_options)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        excel_layout.addWidget(QLabel("Sheet:"))
        self.sheet_input = QLineEdit("Sheet1")
        self.sheet_input.setToolTip(self.FIELD_DESCRIPTIONS["sheet"])
        self.sheet_input.textChanged.connect(self._on_config_changed)
        excel_layout.addWidget(self.sheet_input)
        self.file_layout.addWidget(self.excel_options)

        # CSV options row
        self.csv_options = QWidget()
        csv_layout = QHBoxLayout(self.csv_options)
        csv_layout.setContentsMargins(0, 0, 0, 0)

        csv_layout.addWidget(QLabel("Delimiter:"))
        self.delimiter_input = QLineEdit(",")
        self.delimiter_input.setFixedWidth(40)
        self.delimiter_input.setToolTip(self.FIELD_DESCRIPTIONS["delimiter"])
        self.delimiter_input.textChanged.connect(self._on_config_changed)
        csv_layout.addWidget(self.delimiter_input)

        csv_layout.addWidget(QLabel("Encoding:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "latin-1", "ISO-8859-1", "cp1252", "utf-16"])
        self.encoding_combo.setCurrentText("utf-8")
        self.encoding_combo.setToolTip(self.FIELD_DESCRIPTIONS["encoding"])
        self.encoding_combo.currentTextChanged.connect(self._on_config_changed)
        csv_layout.addWidget(self.encoding_combo)

        self.file_layout.addWidget(self.csv_options)

        layout.addWidget(self.file_group)

        # ==================== DATABASE CONFIG ====================
        self.db_group = QGroupBox("Database Configuration")
        self.db_layout = QFormLayout(self.db_group)
        self.db_layout.setContentsMargins(6, 10, 6, 6)
        self.db_layout.setSpacing(4)

        self.db_driver_combo = QComboBox()
        self.db_driver_combo.addItems(["sqlite", "mysql", "postgresql", "mssql"])
        self.db_driver_combo.setToolTip(self.FIELD_DESCRIPTIONS["driver"])
        self.db_driver_combo.currentTextChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Driver:", self.db_driver_combo)

        self.db_host_input = QLineEdit("localhost")
        self.db_host_input.setToolTip(self.FIELD_DESCRIPTIONS["host"])
        self.db_host_input.textChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Host:", self.db_host_input)

        self.db_port_input = QSpinBox()
        self.db_port_input.setRange(1, 65535)
        self.db_port_input.setValue(3306)
        self.db_port_input.setToolTip(self.FIELD_DESCRIPTIONS["port"])
        self.db_port_input.valueChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Port:", self.db_port_input)

        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText("database_name")
        self.db_name_input.setToolTip(self.FIELD_DESCRIPTIONS["database"])
        self.db_name_input.textChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Database:", self.db_name_input)

        self.db_user_input = QLineEdit()
        self.db_user_input.setPlaceholderText("username")
        self.db_user_input.setToolTip(self.FIELD_DESCRIPTIONS["username"])
        self.db_user_input.textChanged.connect(self._on_config_changed)
        self.db_layout.addRow("User:", self.db_user_input)

        self.db_pass_input = QLineEdit()
        self.db_pass_input.setPlaceholderText("password")
        self.db_pass_input.setEchoMode(QLineEdit.Password)
        self.db_pass_input.setToolTip(self.FIELD_DESCRIPTIONS["password"])
        self.db_pass_input.textChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Password:", self.db_pass_input)

        self.db_query_input = QTextEdit()
        self.db_query_input.setPlaceholderText("SELECT * FROM table_name LIMIT 10")
        self.db_query_input.setMaximumHeight(60)
        self.db_query_input.setToolTip(self.FIELD_DESCRIPTIONS["query"])
        self.db_query_input.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        self.db_query_input.textChanged.connect(self._on_config_changed)
        self.db_layout.addRow("Query:", self.db_query_input)

        self.db_test_btn = QPushButton("Test Connection")
        self.db_test_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #F57C00; }
        """)
        self.db_test_btn.clicked.connect(self._test_db_connection)
        self.db_layout.addRow("", self.db_test_btn)

        layout.addWidget(self.db_group)

        # ==================== API CONFIG ====================
        self.api_group = QGroupBox("API Configuration")
        self.api_layout = QFormLayout(self.api_group)
        self.api_layout.setContentsMargins(6, 10, 6, 6)
        self.api_layout.setSpacing(4)

        self.api_method_combo = QComboBox()
        self.api_method_combo.addItems(["GET", "POST", "PUT", "DELETE"])
        self.api_method_combo.setToolTip(self.FIELD_DESCRIPTIONS["method"])
        self.api_method_combo.currentTextChanged.connect(self._on_config_changed)
        self.api_layout.addRow("Method:", self.api_method_combo)

        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.example.com/data")
        self.api_url_input.setToolTip(self.FIELD_DESCRIPTIONS["url"])
        self.api_url_input.textChanged.connect(self._on_config_changed)
        self.api_layout.addRow("URL:", self.api_url_input)

        self.api_headers_input = QTextEdit()
        self.api_headers_input.setPlaceholderText(
            '{\n  "Authorization": "Bearer token",\n  "Content-Type": "application/json"\n}'
        )
        self.api_headers_input.setMaximumHeight(60)
        self.api_headers_input.setToolTip(self.FIELD_DESCRIPTIONS["headers"])
        self.api_headers_input.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        self.api_headers_input.textChanged.connect(self._on_config_changed)
        self.api_layout.addRow("Headers:", self.api_headers_input)

        self.api_body_input = QTextEdit()
        self.api_body_input.setPlaceholderText('{"key": "value"}')
        self.api_body_input.setMaximumHeight(60)
        self.api_body_input.setToolTip(self.FIELD_DESCRIPTIONS["body"])
        self.api_body_input.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        self.api_body_input.textChanged.connect(self._on_config_changed)
        self.api_layout.addRow("Body:", self.api_body_input)

        self.api_pagination_cb = QCheckBox("Enable pagination")
        self.api_pagination_cb.setToolTip(self.FIELD_DESCRIPTIONS["pagination"])
        self.api_pagination_cb.toggled.connect(self._on_config_changed)
        self.api_layout.addRow("", self.api_pagination_cb)

        self.api_page_param = QLineEdit("page")
        self.api_page_param.setPlaceholderText("page parameter name")
        self.api_page_param.setToolTip(self.FIELD_DESCRIPTIONS["page_param"])
        self.api_page_param.setEnabled(False)
        self.api_pagination_cb.toggled.connect(self.api_page_param.setEnabled)
        self.api_page_param.textChanged.connect(self._on_config_changed)
        self.api_layout.addRow("Page Param:", self.api_page_param)

        self.api_test_btn = QPushButton("Test API")
        self.api_test_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #F57C00; }
        """)
        self.api_test_btn.clicked.connect(self._test_api_connection)
        self.api_layout.addRow("", self.api_test_btn)

        layout.addWidget(self.api_group)

        # ==================== CONFIG STATUS ====================
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            color: #94A3B8; font-size: 9px;
            background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 4px; padding: 4px 8px;
        """)
        layout.addWidget(self.status_label)

        # ==================== PREVIEW SECTION ====================
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(6, 10, 6, 6)
        preview_layout.setSpacing(4)

        # Preview toolbar
        preview_toolbar = QHBoxLayout()

        self.preview_btn = QPushButton("▶ Preview Data")
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.preview_btn.clicked.connect(self._preview_data)
        self.preview_btn.setEnabled(False)
        preview_toolbar.addWidget(self.preview_btn)

        self.row_count_label = QLabel("")
        self.row_count_label.setStyleSheet("color: #666; font-size: 10px;")
        preview_toolbar.addWidget(self.row_count_label)

        preview_toolbar.addStretch()

        self.copy_variable_btn = QPushButton("Copy Variable Ref")
        self.copy_variable_btn.setStyleSheet("""
            QPushButton {
                background: #9C27B0; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 9px;
            }
            QPushButton:hover { background: #7B1FA2; }
        """)
        self.copy_variable_btn.clicked.connect(self._copy_variable_reference)
        self.copy_variable_btn.setEnabled(False)
        preview_toolbar.addWidget(self.copy_variable_btn)

        preview_layout.addLayout(preview_toolbar)

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 10px;
            }
            QTableWidget::item {
                padding: 2px 4px;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 4px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        preview_layout.addWidget(self.preview_table)

        # Variable reference helper
        self.variable_help_group = QGroupBox("Variable References")
        var_help_layout = QVBoxLayout(self.variable_help_group)
        var_help_layout.setContentsMargins(6, 10, 6, 6)
        var_help_layout.setSpacing(2)

        self.variable_help_text = QTextEdit()
        self.variable_help_text.setReadOnly(True)
        self.variable_help_text.setMaximumHeight(80)
        self.variable_help_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 4px;
                font-family: Consolas, monospace; font-size: 10px;
            }
        """)
        self.variable_help_text.setHtml(
            '<span style="color:#999;">Click "Preview Data" to see available variables.<br>'
            'Use <span style="color:#4CAF50;">{{data.column_name}}</span> in workflow params.</span>'
        )
        var_help_layout.addWidget(self.variable_help_text)

        preview_layout.addWidget(self.variable_help_group)

        layout.addWidget(preview_group)

        layout.addStretch()

        # Hide all config groups initially
        self._hide_all_configs()
        self._update_type_description()

    # ==================== UI HELPERS ====================

    def _update_type_description(self):
        """Update deskripsi tipe data source."""
        type_value = self.type_combo.currentData()
        desc = self.SOURCE_DESCRIPTIONS.get(type_value, "")
        self.type_desc_label.setText(desc)

    def _update_status(self, message: str, is_error: bool = False):
        """Update status label."""
        color = "#EF4444" if is_error else "#10B981"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            color: {color}; font-size: 9px;
            background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 4px; padding: 4px 8px;
        """)

    def _hide_all_configs(self):
        """Hide all config groups."""
        self.file_group.hide()
        self.db_group.hide()
        self.api_group.hide()

    def _on_type_changed(self, index: int):
        """Handle perubahan tipe data source."""
        type_value = self.type_combo.currentData()
        self._hide_all_configs()
        self._update_type_description()

        if type_value == "None":
            self.preview_btn.setEnabled(False)
            self.current_config = {}
            self._clear_preview()
            self._update_status("Belum ada data source. Pilih tipe untuk mulai.")
        else:
            self.preview_btn.setEnabled(True)

            if type_value == "Excel":
                self.file_group.show()
                self.file_group.setTitle("Excel Configuration")
                self.excel_options.setVisible(True)
                self.csv_options.setVisible(False)
                self.browse_btn.setText("Browse Excel")
                self.file_path.setPlaceholderText("Select Excel file (.xlsx/.xls)...")
                self._update_status("Pilih file Excel dan tentukan sheet yang akan dibaca.")

            elif type_value == "CSV":
                self.file_group.show()
                self.file_group.setTitle("CSV Configuration")
                self.excel_options.setVisible(False)
                self.csv_options.setVisible(True)
                self.browse_btn.setText("Browse CSV")
                self.file_path.setPlaceholderText("Select CSV file (.csv)...")
                self._update_status("Pilih file CSV dan tentukan delimiter serta encoding.")

            elif type_value == "Database":
                self.db_group.show()
                self._update_status("Isi konfigurasi database dan query untuk mengambil data.")

            elif type_value == "API":
                self.api_group.show()
                self._update_status("Isi URL API dan method untuk mengambil data.")

        self._on_config_changed()

    def _on_config_changed(self):
        """Update config saat ada perubahan."""
        type_value = self.type_combo.currentData()

        if type_value == "None":
            self.current_config = {}
        elif type_value == "Excel":
            self.current_config = {
                "type": "excel",
                "config": {
                    "file_path": self.file_path.text(),
                    "sheet": self.sheet_input.text(),
                }
            }
        elif type_value == "CSV":
            self.current_config = {
                "type": "csv",
                "config": {
                    "file_path": self.file_path.text(),
                    "delimiter": self.delimiter_input.text(),
                    "encoding": self.encoding_combo.currentText(),
                }
            }
        elif type_value == "Database":
            self.current_config = {
                "type": "database",
                "config": {
                    "driver": self.db_driver_combo.currentText(),
                    "host": self.db_host_input.text(),
                    "port": self.db_port_input.value(),
                    "database": self.db_name_input.text(),
                    "username": self.db_user_input.text(),
                    "password": self.db_pass_input.text(),
                    "query": self.db_query_input.toPlainText(),
                }
            }
        elif type_value == "API":
            headers_text = self.api_headers_input.toPlainText().strip()
            try:
                import json
                headers = json.loads(headers_text) if headers_text else {}
            except json.JSONDecodeError:
                headers = {}

            self.current_config = {
                "type": "api",
                "config": {
                    "method": self.api_method_combo.currentText(),
                    "url": self.api_url_input.text(),
                    "headers": headers,
                    "body": self.api_body_input.toPlainText(),
                    "pagination": {
                        "enabled": self.api_pagination_cb.isChecked(),
                        "page_param": self.api_page_param.text(),
                    }
                }
            }

        # Update status berdasarkan kelengkapan config
        self._update_config_status()
        self.data_source_changed.emit(self.current_config)

    def _update_config_status(self):
        """Update status berdasarkan kelengkapan konfigurasi."""
        type_value = self.type_combo.currentData()
        config = self.current_config.get("config", {})

        if type_value == "None":
            return

        missing = []
        if type_value in ("Excel", "CSV"):
            if not config.get("file_path"):
                missing.append("file")
        elif type_value == "Database":
            if not config.get("database"):
                missing.append("database name")
            if not config.get("query"):
                missing.append("query")
        elif type_value == "API":
            if not config.get("url"):
                missing.append("URL")

        if missing:
            self._update_status(
                f"⚠️ Konfigurasi belum lengkap. Perlu: {', '.join(missing)}.",
                is_error=True
            )
        else:
            self._update_status("✅ Konfigurasi lengkap. Klik 'Preview Data' untuk melihat data.")

    # ==================== FILE BROWSING ====================

    def _browse_file(self):
        """Browse file Excel/CSV."""
        type_value = self.type_combo.currentData()

        if type_value == "Excel":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Excel File", "data",
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select CSV File", "data",
                "CSV Files (*.csv);;All Files (*)"
            )

        if file_path:
            self.file_path.setText(file_path)

    # ==================== DATABASE TEST ====================

    def _test_db_connection(self):
        """Test database connection."""
        try:
            from backend.data_sources.database_source import DatabaseDataSource
            source = DatabaseDataSource()

            config = self.current_config.get("config", {})
            errors = source.validate_config(config)
            if errors:
                QMessageBox.warning(self, "Validation Error",
                    "\n".join(errors))
                return

            # Try to connect
            rows = source.get_preview(config, max_rows=5)
            if rows is not None:
                QMessageBox.information(self, "Connection OK",
                    f"Database connection successful!\n"
                    f"Query returned {len(rows)} rows (preview).")
                self._update_status("✅ Koneksi database berhasil.")
            else:
                QMessageBox.information(self, "Connection OK",
                    "Database connection successful!")
                self._update_status("✅ Koneksi database berhasil.")

        except ImportError as e:
            QMessageBox.warning(self, "Import Error",
                f"Database driver not installed:\n{str(e)}\n\n"
                f"Install with: pip install sqlalchemy databases")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed",
                f"Failed to connect:\n{str(e)}")
            self._update_status(f"❌ Koneksi gagal: {str(e)}", is_error=True)

    # ==================== API TEST ====================

    def _test_api_connection(self):
        """Test API connection."""
        try:
            import httpx
            import json

            config = self.current_config.get("config", {})
            url = config.get("url", "")
            if not url:
                QMessageBox.warning(self, "Validation Error",
                    "API URL is required.")
                return

            method = config.get("method", "GET").lower()
            headers = config.get("headers", {})
            body = config.get("body", "")

            # Make request
            with httpx.Client(timeout=10) as client:
                if method == "get":
                    response = client.get(url, headers=headers)
                elif method == "post":
                    response = client.post(url, headers=headers, content=body)
                elif method == "put":
                    response = client.put(url, headers=headers, content=body)
                elif method == "delete":
                    response = client.delete(url, headers=headers)
                else:
                    QMessageBox.warning(self, "Error", f"Unknown method: {method}")
                    return

                QMessageBox.information(self, "API Test Result",
                    f"Status: {response.status_code}\n"
                    f"Time: {response.elapsed.total_seconds():.2f}s\n\n"
                    f"Response (first 500 chars):\n{response.text[:500]}")

                if response.status_code < 400:
                    self._update_status(f"✅ API berhasil. Status: {response.status_code}")
                else:
                    self._update_status(f"❌ API error. Status: {response.status_code}", is_error=True)

        except ImportError:
            QMessageBox.warning(self, "Import Error",
                "httpx library not installed.\nInstall with: pip install httpx")
        except Exception as e:
            QMessageBox.critical(self, "API Test Failed",
                f"Error:\n{str(e)}")
            self._update_status(f"❌ API gagal: {str(e)}", is_error=True)

    # ==================== DATA PREVIEW ====================

    def _preview_data(self):
        """Preview data dari data source."""
        type_value = self.type_combo.currentData()
        if type_value == "None":
            return

        try:
            config = self.current_config.get("config", {})

            if type_value == "Excel":
                from backend.data_sources.excel_source import ExcelDataSource
                source = ExcelDataSource()
            elif type_value == "CSV":
                from backend.data_sources.csv_source import CsvDataSource
                source = CsvDataSource()
            elif type_value == "Database":
                from backend.data_sources.database_source import DatabaseDataSource
                source = DatabaseDataSource()
            elif type_value == "API":
                from backend.data_sources.api_source import ApiDataSource
                source = ApiDataSource()
            else:
                return

            errors = source.validate_config(config)
            if errors:
                QMessageBox.warning(self, "Validation Error",
                    "\n".join(errors))
                self._update_status(f"❌ Validasi gagal: {', '.join(errors)}", is_error=True)
                return

            rows = source.get_preview(config, max_rows=20)

            if not rows:
                QMessageBox.information(self, "Preview", "No data found.")
                self._clear_preview()
                self._update_status("⚠️ Tidak ada data ditemukan.", is_error=True)
                return

            self._preview_data_rows = rows

            # Fill table
            headers = list(rows[0].keys())
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            self.preview_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, header in enumerate(headers):
                    value = str(row.get(header, ""))
                    item = QTableWidgetItem(value)
                    item.setToolTip(f"{{{{data.{header}}}}} = {value}")
                    self.preview_table.setItem(i, j, item)

            self.preview_table.resizeColumnsToContents()

            # Update row count
            self.row_count_label.setText(f"{len(rows)} rows • {len(headers)} columns")

            # Enable variable copy
            self.copy_variable_btn.setEnabled(True)

            # Update variable reference helper
            self._update_variable_help(headers)

            # Auto-adjust max height
            row_height = 22
            max_height = min(len(rows) * row_height + 30, 200)
            self.preview_table.setMaximumHeight(max_height)

            self._update_status(f"✅ Preview berhasil: {len(rows)} baris, {len(headers)} kolom.")

        except Exception as e:
            QMessageBox.warning(self, "Preview Error", str(e))
            self._update_status(f"❌ Preview gagal: {str(e)}", is_error=True)

    def _clear_preview(self):
        """Clear preview table."""
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)
        self.row_count_label.setText("")
        self.copy_variable_btn.setEnabled(False)
        self._preview_data_rows = []
        self.variable_help_text.setHtml(
            '<span style="color:#999;">Click "Preview Data" to see available variables.<br>'
            'Use <span style="color:#4CAF50;">{{data.column_name}}</span> in workflow params.</span>'
        )

    def _update_variable_help(self, headers: list):
        """Update variable reference helper with column names."""
        html = '<span style="color:#4CAF50; font-weight:bold;">Available Variables:</span><br>'
        for header in headers:
            html += f'<span style="color:#2196F3;">{{{{data.{header}}}}}</span>'
            html += f'  <span style="color:#999;">// {header}</span><br>'
        self.variable_help_text.setHtml(html)

    def _copy_variable_reference(self):
        """Copy selected column variable reference to clipboard."""
        selected = self.preview_table.selectedItems()
        if selected:
            col = selected[0].column()
            header = self.preview_table.horizontalHeaderItem(col).text()
            var_ref = f"{{{{data.{header}}}}}"
            clipboard = QApplication.clipboard()
            clipboard.setText(var_ref)
            self.variable_copied.emit(var_ref)

            # Visual feedback
            self.copy_variable_btn.setText(f"✓ Copied!")
            self.copy_variable_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50; color: white; border: none;
                    border-radius: 3px; padding: 4px 10px; font-size: 9px;
                }
            """)
            QTimer.singleShot(2000, self._reset_copy_button)
        else:
            QMessageBox.information(self, "Copy Variable",
                "Select a column first, then click Copy.\n\n"
                "Or click a cell in the preview table.")

    def _reset_copy_button(self):
        """Reset copy button text."""
        self.copy_variable_btn.setText("Copy Variable Ref")
        self.copy_variable_btn.setStyleSheet("""
            QPushButton {
                background: #9C27B0; color: white; border: none;
                border-radius: 3px; padding: 4px 10px; font-size: 9px;
            }
            QPushButton:hover { background: #7B1FA2; }
        """)

    # ==================== PUBLIC API ====================

    def get_config(self) -> dict:
        """Dapatkan konfigurasi data source."""
        return self.current_config

    def set_config(self, config: dict):
        """
        Set konfigurasi dari workflow yang dibuka.

        Method ini mengisi form UI sesuai config dan emit signal
        data_source_changed agar workflow tersinkron.
        """
        if not self._loading_config:
            self._loading_config = True

        try:
            if not config:
                # Reset ke None
                self.type_combo.setCurrentIndex(0)
                return

            type_name = config.get("type", "none").lower()
            file_config = config.get("config", {})

            # Find matching type in combo
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i).lower() == type_name:
                    self.type_combo.setCurrentIndex(i)
                    break

            if type_name == "excel":
                self.file_path.setText(file_config.get("file_path", ""))
                self.sheet_input.setText(file_config.get("sheet", "Sheet1"))

            elif type_name == "csv":
                self.file_path.setText(file_config.get("file_path", ""))
                self.delimiter_input.setText(file_config.get("delimiter", ","))
                self.encoding_combo.setCurrentText(file_config.get("encoding", "utf-8"))

            elif type_name == "database":
                self.db_driver_combo.setCurrentText(file_config.get("driver", "mysql"))
                self.db_host_input.setText(file_config.get("host", "localhost"))
                self.db_port_input.setValue(file_config.get("port", 3306))
                self.db_name_input.setText(file_config.get("database", ""))
                self.db_user_input.setText(file_config.get("username", ""))
                self.db_pass_input.setText(file_config.get("password", ""))
                self.db_query_input.setPlainText(file_config.get("query", ""))

            elif type_name == "api":
                self.api_method_combo.setCurrentText(file_config.get("method", "GET"))
                self.api_url_input.setText(file_config.get("url", ""))
                import json
                headers = file_config.get("headers", {})
                self.api_headers_input.setPlainText(
                    json.dumps(headers, indent=2) if headers else ""
                )
                self.api_body_input.setPlainText(file_config.get("body", ""))
                pagination = file_config.get("pagination", {})
                self.api_pagination_cb.setChecked(pagination.get("enabled", False))
                self.api_page_param.setText(pagination.get("page_param", "page"))

            # Emit signal agar workflow tersinkron dengan config yang baru di-set
            self._on_config_changed()

            # Auto preview if all config is present
            if type_name in ("excel", "csv") and file_config.get("file_path"):
                QTimer.singleShot(500, self._preview_data)

        finally:
            self._loading_config = False
