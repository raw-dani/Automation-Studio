"""
Properties Panel - Panel untuk mengkonfigurasi parameter action yang dipilih.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class PropertiesPanel(QWidget):
    """Panel untuk mengedit parameter action node."""
    
    params_changed = Signal(str, dict)  # step_id, params
    save_requested = Signal()
    type_changed = Signal(str, str)  # step_id, new_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step_id = ""
        self.current_params = {}
        self.current_action_type = ""
        self.setWindowTitle("Properties")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("Properties")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)
        
        # No selection label
        self.no_selection_label = QLabel("Select a node to edit its properties")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #999; padding: 20px;")
        layout.addWidget(self.no_selection_label)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(4)
        self.form_layout.setContentsMargins(8, 8, 8, 8)
        
        scroll.setWidget(self.form_widget)
        self.form_widget.hide()
        layout.addWidget(scroll)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; padding: 8px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.save_btn.clicked.connect(lambda: self.save_requested.emit())
        layout.addWidget(self.save_btn)
    
    def show_action_properties(self, step_id: str, params: dict, action_type: str = ""):
        """Tampilkan form untuk mengedit parameter action."""
        self.current_step_id = step_id
        self.current_params = dict(params)
        self.current_action_type = action_type or params.get("type", "")
        
        self.no_selection_label.hide()
        self.form_widget.show()
        
        # Clear form
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add type dropdown at top
        type_widget = QWidget()
        type_layout = QHBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "click", "input_text", "select", "select2", "select_dropdown",
            "wait", "upload_file", "loop", "if_else", "navigate"
        ])
        if self.current_action_type in [
            "click", "input_text", "select", "select2", "select_dropdown",
            "wait", "upload_file", "loop", "if_else", "navigate"
        ]:
            self.type_combo.setCurrentText(self.current_action_type)
        self.type_combo.currentTextChanged.connect(self._on_type_change)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        self.form_layout.addRow("", type_widget)
        
        # Add fields based on params
        for key, value in params.items():
            if key != "type":
                self._add_field(key, value)
        
        # Add label field
        self._add_field("label", params.get("label", ""))
    
    def _on_type_change(self, new_type: str):
        """Handle perubahan tipe action."""
        old_type = self.current_action_type
        self.current_action_type = new_type
        
        # Remove 'type' from params if present
        if "type" in self.current_params:
            del self.current_params["type"]
        
        # Emit signal untuk update node di editor
        self.type_changed.emit(self.current_step_id, new_type)
        
        # Rebuild form dengan field yang sesuai untuk type baru
        self._rebuild_form_for_type(new_type)
    
    def _rebuild_form_for_type(self, action_type: str):
        """Rebuild form dengan field yang sesuai untuk action type."""
        # Clear current form
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add type dropdown
        type_widget = QWidget()
        type_layout = QHBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "click", "input_text", "select", "select2", "select_dropdown",
            "wait", "upload_file", "loop", "if_else", "navigate"
        ])
        self.type_combo.setCurrentText(action_type)
        self.type_combo.currentTextChanged.connect(self._on_type_change)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        self.form_layout.addRow("", type_widget)
        
        # Add fields based on action type
        if action_type == "click":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("wait_after", self.current_params.get("wait_after", 500))
            self._add_field("force", self.current_params.get("force", False))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        elif action_type == "input_text":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("value", self.current_params.get("value", ""))
            self._add_field("clear_first", self.current_params.get("clear_first", True))
            self._add_field("type_delay", self.current_params.get("type_delay", 50))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("wait_after", self.current_params.get("wait_after", 500))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        elif action_type == "select":
            self._add_field("options", self.current_params.get("options", []))
            self._add_field("selected", self.current_params.get("selected", ""))
            self._add_field("variable_name", self.current_params.get("variable_name", ""))
        
        elif action_type == "select2":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("search_selector", self.current_params.get("search_selector", ""))
            self._add_field("value", self.current_params.get("value", ""))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("wait_after", self.current_params.get("wait_after", 500))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
            self._add_field("clear_first", self.current_params.get("clear_first", True))
        
        elif action_type == "select_dropdown":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("select_by", self.current_params.get("select_by", "label"))
            self._add_field("select_value", self.current_params.get("select_value", ""))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("wait_after", self.current_params.get("wait_after", 500))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        elif action_type == "wait":
            self._add_field("wait_type", self.current_params.get("wait_type", "fixed"))
            self._add_field("duration", self.current_params.get("duration", 1000))
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        elif action_type == "upload_file":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("file_path", self.current_params.get("file_path", ""))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        elif action_type == "loop":
            self._add_field("loop_type", self.current_params.get("loop_type", "count"))
            self._add_field("count", self.current_params.get("count", 1))
            self._add_field("data_key", self.current_params.get("data_key", ""))
            self._add_field("condition", self.current_params.get("condition", ""))
            self._add_field("max_iterations", self.current_params.get("max_iterations", 100))
        
        elif action_type == "if_else":
            self._add_field("condition", self.current_params.get("condition", ""))
            self._add_field("variable_name", self.current_params.get("variable_name", ""))
            self._add_field("expected_value", self.current_params.get("expected_value", ""))
        
        elif action_type == "navigate":
            self._add_field("url", self.current_params.get("url", ""))
            self._add_field("wait_until", self.current_params.get("wait_until", "domcontentloaded"))
            self._add_field("timeout", self.current_params.get("timeout", 30000))
        
        # Always add label at the end
        self._add_field("label", self.current_params.get("label", ""))
    
    def _add_field(self, key: str, value):
        """Tambah field ke form."""
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            widget.toggled.connect(lambda checked, k=key: self._on_param_change(k, checked))
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(value)
            widget.valueChanged.connect(lambda v, k=key: self._on_param_change(k, v))
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-999999, 999999)
            widget.setDecimals(3)
            widget.setValue(value)
            widget.valueChanged.connect(lambda v, k=key: self._on_param_change(k, v))
        elif isinstance(value, list):
            widget = QLineEdit(", ".join(str(v) for v in value))
            widget.textChanged.connect(lambda v, k=key: self._on_list_param_change(k, v))
        elif isinstance(value, str) and key in ("selector_type", "select_by", "wait_type", "loop_type"):
            widget = QComboBox()
            options = {
                "selector_type": ["css", "xpath", "text"],
                "select_by": ["label", "value", "index"],
                "wait_type": ["fixed", "until_visible", "until_hidden", "until_selector"],
                "loop_type": ["count", "data_source", "while"],
            }.get(key, [value])
            widget.addItems(options)
            if value in options:
                widget.setCurrentText(value)
            widget.currentTextChanged.connect(lambda v, k=key: self._on_param_change(k, v))
        else:
            widget = QLineEdit(str(value))
            widget.textChanged.connect(lambda v, k=key: self._on_param_change(k, v))
        
        # Label
        label = key.replace("_", " ").title()
        self.form_layout.addRow(f"{label}:", widget)
    
    def _on_list_param_change(self, key: str, value: str):
        """Handle perubahan parameter list (comma-separated)."""
        items = [item.strip() for item in value.split(",") if item.strip()]
        self.current_params[key] = items
        self.params_changed.emit(self.current_step_id, self.current_params)
    
    def _on_param_change(self, key: str, value):
        """Handle perubahan parameter."""
        self.current_params[key] = value
        self.params_changed.emit(self.current_step_id, self.current_params)
    
    def clear(self):
        """Bersihkan form."""
        self.current_step_id = ""
        self.current_params = {}
        self.no_selection_label.show()
        self.form_widget.hide()