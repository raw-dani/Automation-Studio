"""
Data Source Manager - Panel untuk mengelola koneksi data source.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class DataSourceManager(QWidget):
    """Panel untuk mengkonfigurasi data source workflow."""
    
    data_source_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = {}
        self.setWindowTitle("Data Source")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("Data Source")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)
        
        # Type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["None", "Excel", "CSV"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Config group
        self.config_group = QGroupBox("Configuration")
        self.config_layout = QVBoxLayout(self.config_group)
        
        # File path
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select file...")
        self.file_path.textChanged.connect(self._on_config_changed)
        file_layout.addWidget(self.file_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        self.config_layout.addLayout(file_layout)
        
        # Sheet (for Excel)
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Sheet:"))
        self.sheet_input = QLineEdit("Sheet1")
        self.sheet_input.textChanged.connect(self._on_config_changed)
        sheet_layout.addWidget(self.sheet_input)
        self.config_layout.addLayout(sheet_layout)
        
        # Delimiter (for CSV)
        delim_layout = QHBoxLayout()
        delim_layout.addWidget(QLabel("Delimiter:"))
        self.delimiter_input = QLineEdit(",")
        self.delimiter_input.textChanged.connect(self._on_config_changed)
        delim_layout.addWidget(self.delimiter_input)
        self.config_layout.addLayout(delim_layout)
        
        self.config_group.hide()
        layout.addWidget(self.config_group)
        
        # Preview button
        self.preview_btn = QPushButton("Preview Data")
        self.preview_btn.clicked.connect(self._preview_data)
        self.preview_btn.setEnabled(False)
        layout.addWidget(self.preview_btn)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(150)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table)
        
        layout.addStretch()
    
    def _on_type_changed(self, type_name: str):
        """Handle perubahan tipe data source."""
        if type_name == "None":
            self.config_group.hide()
            self.preview_btn.setEnabled(False)
            self.current_config = {}
        else:
            self.config_group.show()
            self.preview_btn.setEnabled(True)
            
            # Show/hide specific fields
            is_excel = type_name == "Excel"
            self.sheet_input.setVisible(is_excel)
            self.sheet_input.parent().findChildren(QLabel)[0].setVisible(is_excel)
            self.delimiter_input.setVisible(not is_excel)
            self.delimiter_input.parent().findChildren(QLabel)[0].setVisible(not is_excel)
        
        self._on_config_changed()
    
    def _on_config_changed(self):
        """Update config saat ada perubahan."""
        type_name = self.type_combo.currentText()
        if type_name == "None":
            self.current_config = {}
        else:
            self.current_config = {
                "type": type_name.lower(),
                "config": {
                    "file_path": self.file_path.text(),
                }
            }
            if type_name == "Excel":
                self.current_config["config"]["sheet"] = self.sheet_input.text()
            else:
                self.current_config["config"]["delimiter"] = self.delimiter_input.text()
        
        self.data_source_changed.emit(self.current_config)
    
    def _browse_file(self):
        """Browse file Excel/CSV."""
        type_name = self.type_combo.currentText()
        if type_name == "Excel":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Excel File", "data", "Excel Files (*.xlsx *.xls)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select CSV File", "data", "CSV Files (*.csv)"
            )
        
        if file_path:
            self.file_path.setText(file_path)
    
    def _preview_data(self):
        """Preview data dari data source."""
        type_name = self.type_combo.currentText()
        if type_name == "None":
            return
        
        try:
            if type_name == "Excel":
                from backend.data_sources.excel_source import ExcelDataSource
                source = ExcelDataSource()
                config = {
                    "file_path": self.file_path.text(),
                    "sheet": self.sheet_input.text(),
                }
            else:
                from backend.data_sources.csv_source import CsvDataSource
                source = CsvDataSource()
                config = {
                    "file_path": self.file_path.text(),
                    "delimiter": self.delimiter_input.text(),
                }
            
            rows = source.get_preview(config, max_rows=10)
            
            if not rows:
                QMessageBox.information(self, "Preview", "No data found.")
                return
            
            # Fill table
            headers = list(rows[0].keys())
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            self.preview_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, header in enumerate(headers):
                    self.preview_table.setItem(i, j, QTableWidgetItem(str(row.get(header, ""))))
            
            self.preview_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", str(e))
    
    def get_config(self) -> dict:
        """Dapatkan konfigurasi data source."""
        return self.current_config
    
    def set_config(self, config: dict):
        """Set konfigurasi dari workflow."""
        if not config:
            return
        
        self.type_combo.setCurrentText(config.get("type", "None").title())
        file_config = config.get("config", {})
        self.file_path.setText(file_config.get("file_path", ""))
        self.sheet_input.setText(file_config.get("sheet", "Sheet1"))
        self.delimiter_input.setText(file_config.get("delimiter", ","))