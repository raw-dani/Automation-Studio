"""
Properties Panel - Panel untuk mengkonfigurasi parameter action yang dipilih.
Dilengkapi: action header card, field descriptions, modified indicator, reset button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFrame,
    QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


# Color scheme for action types (mirror dari workflow_editor)
ACTION_COLORS = {
    "click": "#2196F3",
    "http_submit": "#4CAF50",
    "input_text": "#9C27B0",
    "select": "#00BCD4",
    "select2": "#00BCD4",
    "select_dropdown": "#FF9800",
    "radio_select": "#FF5722",
    "upload_file": "#4CAF50",
    "wait": "#FFC107",
    "loop": "#FF5722",
    "if_else": "#3F51B5",
    "parallel_group": "#009688",
    "navigate": "#9C27B0",
    "default": "#607D8B",
}

# Ikon per action type
ACTION_ICONS = {
    "click": "🖱️",
    "wait": "⏳",
    "navigate": "🧭",
    "input_text": "✏️",
    "input_date": "📅",
    "select": "📋",
    "select2": "📋",
    "select_dropdown": "📑",
    "radio_select": "🔘",
    "upload_file": "📤",
    "http_submit": "🌐",
    "loop": "🔄",
    "if_else": "🔀",
    "parallel_group": "⚡",
    "ocr": "👁️",
    "image_detect": "🖼️",
    "extract": "📊",
    "transform": "🔧",
}

# Deskripsi singkat per action type
ACTION_DESCRIPTIONS = {
    "click": "Klik elemen pada halaman web",
    "wait": "Tunggu selama durasi tertentu atau hingga kondisi terpenuhi",
    "navigate": "Navigasi browser ke URL tertentu",
    "input_text": "Isi teks ke input field",
    "input_date": "Isi tanggal ke input field dengan format tertentu",
    "select": "Pilih opsi dari dropdown/combobox",
    "select2": "Pilih opsi menggunakan komponen Select2",
    "select_dropdown": "Pilih opsi dari dropdown menu",
    "radio_select": "Pilih radio button",
    "upload_file": "Upload file ke halaman web",
    "http_submit": "Submit data melalui HTTP request",
    "loop": "Ulangi langkah-langkah di dalamnya",
    "if_else": "Percabangan kondisi (then/else)",
    "parallel_group": "Jalankan langkah-langkah secara paralel",
    "ocr": "Deteksi teks menggunakan OCR",
    "image_detect": "Deteksi gambar/elemen visual",
    "extract": "Ekstrak data dari halaman",
    "transform": "Transformasi data",
}

# Deskripsi per field parameter
FIELD_DESCRIPTIONS = {
    "selector": "CSS selector atau XPath untuk menemukan elemen target",
    "selector_type": "Jenis selector yang digunakan (css, xpath, atau text)",
    "value": "Nilai/teks yang akan diinput atau dipilih",
    "label": "Label yang ditampilkan untuk step ini di workflow",
    "url": "URL halaman yang akan dinavigasi",
    "wait_until": "Kondisi yang harus terpenuhi sebelum melanjutkan",
    "timeout": "Waktu maksimum (ms) menunggu elemen muncul",
    "wait_before": "Jeda (ms) sebelum action dijalankan",
    "wait_after": "Jeda (ms) setelah action selesai",
    "force": "Paksa klik meskipun elemen tidak terlihat",
    "clear_first": "Bersihkan field sebelum mengisi nilai baru",
    "type_delay": "Jeda (ms) antara setiap karakter yang diketik",
    "date_format": "Format tanggal yang digunakan (contoh: dd/MM/yyyy)",
    "select_by": "Cara memilih opsi (label, value, atau index)",
    "select_value": "Nilai opsi yang akan dipilih",
    "file_path": "Path lengkap file yang akan diupload",
    "form_selector": "Selector untuk form yang akan disubmit",
    "submit_selector": "Selector untuk tombol submit",
    "loop_type": "Jenis loop (count, data_source, atau while)",
    "count": "Jumlah iterasi untuk loop",
    "data_key": "Key data source yang akan di-loop",
    "condition": "Kondisi untuk loop while atau if_else",
    "max_iterations": "Batas maksimum iterasi untuk mencegah infinite loop",
    "variable_name": "Nama variabel untuk menyimpan hasil",
    "expected_value": "Nilai yang diharapkan untuk kondisi if_else",
    "options": "Daftar opsi yang tersedia (dipisahkan koma)",
    "selected": "Opsi yang sudah dipilih",
    "search_selector": "Selector untuk field pencarian Select2",
    "stagger_delay": "Jeda (ms) antara setiap child step paralel",
    "on_error": "Strategi penanganan error (stop, skip, retry)",
    "duration": "Durasi tunggu (ms) untuk wait action",
    "wait_type": "Jenis wait (fixed, until_visible, until_hidden, until_selector)",
}


class ChildStepItem(QFrame):
    """Widget untuk menampilkan satu child step di dalam parallel_group."""

    edit_clicked = Signal(int)  # index
    remove_clicked = Signal(int)  # index
    move_up_clicked = Signal(int)  # index
    move_down_clicked = Signal(int)  # index
    params_edited = Signal(int, dict)  # index, updated_child_dict
    save_requested = Signal(int)  # index - explicit save from inline edit
    cancel_requested = Signal(int)  # index

    def __init__(self, step_id: str, action_type: str, label: str, params: dict, index: int, parent=None):
        super().__init__(parent)
        self.step_id = step_id
        self.action_type = action_type
        self.step_index = index
        self._child_data = {
            "id": step_id,
            "type": action_type,
            "label": label,
            "params": dict(params),
        }

        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(64)
        self.setStyleSheet("""
            ChildStepItem {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin: 2px 0px;
            }
            ChildStepItem:hover {
                background: #f1f5f9;
                border: 1px solid #009688;
            }
            ChildStepItem[editing="true"] {
                background: #fffde7;
                border: 2px solid #009688;
            }
        """)
        self.setProperty("editing", "false")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 6, 6, 6)
        self.main_layout.setSpacing(4)

        # Build view mode
        self._view_widget = QWidget()
        self._build_view_mode()
        self.main_layout.addWidget(self._view_widget)

        # Build edit mode (hidden by default)
        self._edit_widget = QWidget()
        self._edit_widget.setStyleSheet("background: #fffde7; border: 1px solid #009688; border-radius: 4px;")
        self._build_edit_mode()
        self._edit_widget.hide()
        self.main_layout.addWidget(self._edit_widget)

        self._apply_view_data()

    def _border_color(self):
        return ACTION_COLORS.get(self.action_type, ACTION_COLORS["default"])

    def _build_view_mode(self):
        layout = QHBoxLayout(self._view_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        border_color = self._border_color()

        color_indicator = QFrame()
        color_indicator.setFixedWidth(4)
        color_indicator.setFixedHeight(48)
        color_indicator.setStyleSheet(f"""
            QFrame {{
                background: {border_color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(color_indicator)

        index_label = QLabel(f"#{self.step_index}")
        index_label.setFixedWidth(24)
        index_label.setAlignment(Qt.AlignCenter)
        index_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        layout.addWidget(index_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self._type_label = QLabel()
        type_font = QFont()
        type_font.setBold(True)
        type_font.setPointSize(9)
        self._type_label.setFont(type_font)
        self._type_label.setStyleSheet(f"color: {border_color};")
        text_layout.addWidget(self._type_label)

        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("color: #94a3b8; font-size: 8px;")
        text_layout.addWidget(self._summary_label)

        layout.addLayout(text_layout, 1)

        btn_style = """
            QPushButton {
                background: transparent;
                border: 1px solid #d1d5db;
                border-radius: 3px;
                font-size: 8px;
                font-weight: bold;
                padding: 1px 3px;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
            }
            QPushButton:hover { background: #e5e7eb; }
        """

        btn_up = QPushButton("▲")
        btn_up.setStyleSheet(btn_style)
        btn_up.setToolTip("Move up")
        btn_up.clicked.connect(lambda: self.move_up_clicked.emit(self.step_index - 1))
        layout.addWidget(btn_up)

        btn_down = QPushButton("▼")
        btn_down.setStyleSheet(btn_style)
        btn_down.setToolTip("Move down")
        btn_down.clicked.connect(lambda: self.move_down_clicked.emit(self.step_index - 1))
        layout.addWidget(btn_down)

        btn_edit = QPushButton("✎")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {border_color};
                border-radius: 5px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{ background: {border_color}50; }}
        """)
        btn_edit.setToolTip("Edit child params (click to edit type, selector, value)")
        btn_edit.clicked.connect(lambda: self.enter_edit_mode())
        layout.addWidget(btn_edit)

        btn_del = QPushButton("✕")
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ef4444;
                border-radius: 3px;
                font-size: 8px;
                font-weight: bold;
                padding: 1px 3px;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
                color: #ef4444;
            }
            QPushButton:hover { background: #fef2f2; }
        """)
        btn_del.setToolTip("Remove child step")
        btn_del.clicked.connect(lambda: self.remove_clicked.emit(self.step_index - 1))
        layout.addWidget(btn_del)

    def _build_edit_mode(self):
        layout = QVBoxLayout(self._edit_widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Type selector
        self._edit_type_combo = QComboBox()
        self._edit_type_combo.addItems([
            "click", "http_submit", "input_text", "input_date", "select", "select2", "select_dropdown", "radio_select",
            "wait", "upload_file", "navigate",
        ])
        self._edit_type_combo.setCurrentText(self.action_type)
        self._edit_type_combo.setFixedWidth(110)
        self._edit_type_combo.setStyleSheet("font-size: 10px; padding: 2px;")
        self._edit_type_combo.currentTextChanged.connect(self._on_edit_type_changed)
        top_row.addWidget(self._edit_type_combo)

        # Label
        self._edit_label_input = QLineEdit()
        self._edit_label_input.setPlaceholderText("Label")
        self._edit_label_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self._edit_label_input.textChanged.connect(self._on_edit_label_changed)
        top_row.addWidget(self._edit_label_input, 1)

        btn_save = QPushButton("💾")
        btn_save.setToolTip("Save")
        btn_save.setStyleSheet("""
            QPushButton {
                background: transparent; border: 1px solid #4CAF50;
                border-radius: 3px; font-size: 10px; font-weight: bold;
                padding: 1px 4px; min-width: 22px; max-width: 22px;
                min-height: 22px; max-height: 22px;
            }
            QPushButton:hover { background: #4CAF5020; }
        """)
        btn_save.clicked.connect(self._commit_edit)
        top_row.addWidget(btn_save)

        btn_cancel = QPushButton("✕")
        btn_cancel.setToolTip("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; border: 1px solid #ef4444;
                border-radius: 3px; font-size: 10px; font-weight: bold;
                padding: 1px 4px; min-width: 22px; max-width: 22px;
                min-height: 22px; max-height: 22px; color: #ef4444;
            }
            QPushButton:hover { background: #fef2f2; }
        """)
        btn_cancel.clicked.connect(self._cancel_edit)
        top_row.addWidget(btn_cancel)

        layout.addLayout(top_row)

        # Selector row
        selector_row = QHBoxLayout()
        selector_row.setSpacing(6)
        selector_row.addWidget(QLabel("Selector:"))
        self._edit_selector_input = QLineEdit()
        self._edit_selector_input.setPlaceholderText("CSS / XPath selector")
        self._edit_selector_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self._edit_selector_input.textChanged.connect(self._on_edit_selector_changed)
        selector_row.addWidget(self._edit_selector_input, 1)
        layout.addLayout(selector_row)

        # Value row
        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        value_row.addWidget(QLabel("Value:"))
        self._edit_value_input = QLineEdit()
        self._edit_value_input.setPlaceholderText("Value / text / option")
        self._edit_value_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self._edit_value_input.textChanged.connect(self._on_edit_value_changed)
        value_row.addWidget(self._edit_value_input, 1)
        layout.addLayout(value_row)

    def _apply_view_data(self):
        border_color = self._border_color()
        self._type_label.setText(f"[{self.action_type}] {self._child_data['label'] or self.action_type}")
        self._type_label.setStyleSheet(f"color: {border_color};")

        params = self._child_data.get("params", {})
        summary_parts = []
        if "selector" in params:
            sel = str(params["selector"])
            summary_parts.append(f"sel: {sel[:25]}..." if len(sel) > 25 else f"sel: {sel}")
        if "value" in params:
            val = str(params["value"])
            summary_parts.append(f"val: {val[:20]}..." if len(val) > 20 else f"val: {val}")
        if "skip_if_empty" in params and params["skip_if_empty"]:
            summary_parts.append("skip_empty")
        if "use_fill" in params and params["use_fill"]:
            summary_parts.append("use_fill")
        if summary_parts:
            self._summary_label.setText(" | ".join(summary_parts))
        else:
            self._summary_label.setText("")

    def enter_edit_mode(self):
        self.setProperty("editing", "true")
        self.style().unpolish(self)
        self.style().polish(self)

        params = self._child_data.get("params", {})
        self._edit_type_combo.setCurrentText(self.action_type)
        self._edit_label_input.setText(self._child_data.get("label", ""))
        self._edit_selector_input.setText(params.get("selector", ""))
        self._edit_value_input.setText(params.get("value", ""))

        self._view_widget.hide()
        self._edit_widget.show()
        self._edit_widget.raise_()
        self.setFixedHeight(140)
        self.main_layout.activate()
        self.updateGeometry()

    def exit_edit_mode(self, canceled=False):
        self.setProperty("editing", "false")
        self.style().unpolish(self)
        self.style().polish(self)

        if not canceled:
            self._apply_view_data()

        self._edit_widget.hide()
        self._view_widget.show()
        self.setFixedHeight(64)

    def _commit_edit(self):
        new_type = self._edit_type_combo.currentText()
        new_label = self._edit_label_input.text().strip()
        new_selector = self._edit_selector_input.text().strip()
        new_value = self._edit_value_input.text().strip()

        self.action_type = new_type
        self._child_data["type"] = new_type
        self._child_data["label"] = new_label or new_type

        child_params = self._child_data.get("params", {})
        if new_selector:
            child_params["selector"] = new_selector
        elif "selector" in child_params:
            del child_params["selector"]
        if new_value:
            child_params["value"] = new_value
        elif "value" in child_params:
            del child_params["value"]
        self._child_data["params"] = child_params

        self.exit_edit_mode(canceled=False)
        self.params_edited.emit(self.step_index - 1, dict(self._child_data))

    def _cancel_edit(self):
        self._edit_type_combo.setCurrentText(self.action_type)
        self._edit_label_input.setText(self._child_data.get("label", ""))
        params = self._child_data.get("params", {})
        self._edit_selector_input.setText(params.get("selector", ""))
        self._edit_value_input.setText(params.get("value", ""))
        self.exit_edit_mode(canceled=True)

    def _on_edit_type_changed(self, new_type: str):
        self._child_data["type"] = new_type

    def _on_edit_label_changed(self, text: str):
        self._child_data["label"] = text

    def _on_edit_selector_changed(self, text: str):
        if "params" not in self._child_data:
            self._child_data["params"] = {}
        self._child_data["params"]["selector"] = text

    def _on_edit_value_changed(self, text: str):
        if "params" not in self._child_data:
            self._child_data["params"] = {}
        self._child_data["params"]["value"] = text

    def update_child_data(self, child_data: dict):
        """Update child data from external source."""
        self._child_data = dict(child_data)
        self.action_type = self._child_data.get("type", "click")
        self._edit_type_combo.setCurrentText(self.action_type)
        self._edit_label_input.setText(self._child_data.get("label", ""))
        self._apply_view_data()


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
        self.current_children = []  # Untuk parallel_group child steps
        self._child_item_widgets = []
        self._is_modified = False
        self._building_form = False  # Flag untuk mencegah _mark_modified saat build form
        self.setWindowTitle("Properties")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ==================== TITLE ====================
        title = QLabel("Properties")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)

        # ==================== ACTION HEADER CARD ====================
        self.action_header = QFrame()
        self.action_header.setObjectName("actionHeader")
        self.action_header.setStyleSheet("""
            #actionHeader {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                margin: 0 4px;
            }
        """)
        header_layout = QVBoxLayout(self.action_header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(4)

        # Row: icon + type + step_id
        header_top = QHBoxLayout()
        header_top.setSpacing(8)

        self.header_icon = QLabel("🔹")
        self.header_icon.setStyleSheet("font-size: 20px;")
        header_top.addWidget(self.header_icon)

        self.header_type = QLabel("-")
        type_font = QFont()
        type_font.setBold(True)
        type_font.setPointSize(12)
        self.header_type.setFont(type_font)
        self.header_type.setStyleSheet("color: #1E293B;")
        header_top.addWidget(self.header_type)

        header_top.addStretch()

        self.header_step_id = QLabel("")
        self.header_step_id.setStyleSheet("""
            color: #94A3B8; font-size: 8px;
            background: #F1F5F9; padding: 2px 6px; border-radius: 4px;
        """)
        header_top.addWidget(self.header_step_id)

        header_layout.addLayout(header_top)

        # Description
        self.header_desc = QLabel("")
        self.header_desc.setWordWrap(True)
        self.header_desc.setStyleSheet("color: #64748B; font-size: 10px;")
        header_layout.addWidget(self.header_desc)

        # Modified indicator
        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("""
            color: #F59E0B; font-weight: bold; font-size: 9px;
        """)
        header_layout.addWidget(self.modified_label)

        self.action_header.hide()
        layout.addWidget(self.action_header)

        # ==================== NO SELECTION ====================
        self.no_selection_label = QLabel("Select a node to edit its properties")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #999; padding: 20px;")
        layout.addWidget(self.no_selection_label)

        # ==================== SCROLL AREA ====================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(4)
        self.form_layout.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(self.form_widget)
        self.form_widget.hide()
        layout.addWidget(scroll, 1)

        # ==================== BOTTOM BUTTONS ====================
        bottom_buttons = QHBoxLayout()
        bottom_buttons.setSpacing(4)

        # Reset button
        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1px solid #E2E8F0; border-radius: 4px;
                padding: 6px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:disabled { background: #F8FAFC; color: #CBD5E1; }
        """)
        self.reset_btn.setToolTip("Reset ke default params")
        self.reset_btn.clicked.connect(self._reset_params)
        bottom_buttons.addWidget(self.reset_btn)

        # Save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; padding: 6px 10px;
                border-radius: 4px; font-weight: bold; font-size: 10px;
            }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.save_btn.clicked.connect(lambda: self.save_requested.emit())
        bottom_buttons.addWidget(self.save_btn, 1)

        layout.addLayout(bottom_buttons)

        # Disable tombol sampai ada node yang dipilih
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

    # ==================== PUBLIC API ====================

    def show_action_properties(self, step_id: str, params: dict, action_type: str = "",
                               children: list = None):
        """Tampilkan form untuk mengedit parameter action."""
        self.current_step_id = step_id
        self.current_params = dict(params) if params is not None else {}
        self.current_action_type = action_type or self.current_params.get("type", "")
        self.current_children = children or []
        self._is_modified = False

        self.no_selection_label.hide()
        self.form_widget.show()
        self.form_widget.update()

        # Update action header
        self._update_action_header()

        # Clear form
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build form based on action type
        base_type = self.current_action_type or self.current_params.get("type", "")
        if not base_type:
            base_type = "click"

        # Set flag building form agar _mark_modified tidak terpicu saat build
        self._building_form = True
        self._rebuild_form_for_type(base_type)

        # Override with actual values from params
        for key, value in (params or {}).items():
            if key != "type":
                self.current_params[key] = value

        self._building_form = False
        self.modified_label.setText("")
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

        self.form_widget.updateGeometry()

    def _update_action_header(self):
        """Update action header card."""
        action_type = self.current_action_type or "default"
        color = ACTION_COLORS.get(action_type, ACTION_COLORS["default"])
        icon = ACTION_ICONS.get(action_type, "🔹")
        desc = ACTION_DESCRIPTIONS.get(action_type, "")

        self.header_icon.setText(icon)
        self.header_type.setText(action_type.replace("_", " ").title())
        self.header_type.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        self.header_desc.setText(desc)
        self.header_step_id.setText(f"ID: {self.current_step_id}")
        self.modified_label.setText("")

        self.action_header.show()

    def _mark_modified(self):
        """Tandai panel sebagai modified."""
        self._is_modified = True
        self.modified_label.setText("● Unsaved changes")
        self.save_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)

    def _reset_params(self):
        """Reset params ke default dari action registry."""
        from backend.core.action_registry import ActionRegistry
        from backend.actions.click_action import ClickAction
        from backend.actions.input_text_action import InputTextAction
        from backend.actions.input_date_action import InputDateAction
        from backend.actions.wait_action import WaitAction
        from backend.actions.select_dropdown_action import SelectDropdownAction
        from backend.actions.radio_select_action import RadioSelectAction
        from backend.actions.upload_file_action import UploadFileAction
        from backend.actions.http_submit_action import HttpSubmitAction
        from backend.actions.loop_action import LoopAction
        from backend.actions.if_else_action import IfElseAction
        from backend.actions.parallel_group_action import ParallelGroupAction
        from backend.actions.select_action import SelectAction
        from backend.actions.select2_action import Select2Action
        from backend.actions.navigate_action import NavigateAction
        registry = ActionRegistry()
        registry.register(ClickAction())
        registry.register(InputTextAction())
        registry.register(InputDateAction())
        registry.register(WaitAction())
        registry.register(SelectDropdownAction())
        registry.register(RadioSelectAction())
        registry.register(UploadFileAction())
        registry.register(HttpSubmitAction())
        registry.register(LoopAction())
        registry.register(IfElseAction())
        registry.register(ParallelGroupAction())
        registry.register(SelectAction())
        registry.register(Select2Action())
        registry.register(NavigateAction())
        action = registry.get(self.current_action_type)
        if action:
            self.current_params = action.default_params.copy()
            self.params_changed.emit(self.current_step_id, self.current_params)
            self._rebuild_form_for_type(self.current_action_type)
            self._mark_modified()

    def _on_type_change(self, new_type: str):
        """Handle perubahan tipe action."""
        self.current_action_type = new_type

        if "type" in self.current_params:
            del self.current_params["type"]

        self.type_changed.emit(self.current_step_id, new_type)
        self._rebuild_form_for_type(new_type)
        self._update_action_header()
        self._mark_modified()

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
            "click", "http_submit", "input_text", "input_date", "select", "select2", "select_dropdown", "radio_select",
            "wait", "upload_file", "loop", "if_else", "navigate", "parallel_group"
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

        elif action_type == "http_submit":
            self._add_field("form_selector", self.current_params.get("form_selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("submit_selector", self.current_params.get("submit_selector", ""))
            self._add_field("timeout", self.current_params.get("timeout", 10000))
            self._add_field("wait_after", self.current_params.get("wait_after", 0))

        elif action_type == "input_text":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("value", self.current_params.get("value", ""))
            self._add_field("clear_first", self.current_params.get("clear_first", True))
            self._add_field("type_delay", self.current_params.get("type_delay", 50))
            self._add_field("wait_before", self.current_params.get("wait_before", 500))
            self._add_field("wait_after", self.current_params.get("wait_after", 500))
            self._add_field("timeout", self.current_params.get("timeout", 30000))

        elif action_type == "input_date":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("value", self.current_params.get("value", ""))
            self._add_field("date_format", self.current_params.get("date_format", "dd|MM|yyyy->dd/MM/yyyy"))
            self._add_field("clear_first", self.current_params.get("clear_first", True))
            self._add_field("wait_before", self.current_params.get("wait_before", 0))
            self._add_field("wait_after", self.current_params.get("wait_after", 0))
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
            self._add_field("timeout", self.current_params.get("timeout", 10000))

        elif action_type == "radio_select":
            self._add_field("selector", self.current_params.get("selector", ""))
            self._add_field("selector_type", self.current_params.get("selector_type", "css"))
            self._add_field("value", self.current_params.get("value", ""))
            self._add_field("select_by", self.current_params.get("select_by", "label"))
            self._add_field("wait_before", self.current_params.get("wait_before", 0))
            self._add_field("wait_after", self.current_params.get("wait_after", 0))
            self._add_field("timeout", self.current_params.get("timeout", 10000))

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

            if self.current_children:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background: #e2e8f0; max-height: 1px; margin: 8px 0;")
                self.form_layout.addRow("", sep)

                children_header = QLabel("  🔄 Child Steps (Sequential)")
                children_header.setStyleSheet("""
                    color: #FF5722; font-weight: bold; font-size: 11px;
                    padding: 6px 0; border-bottom: 2px solid #FF5722;
                """)
                self.form_layout.addRow("", children_header)

                info_label = QLabel(f"  {len(self.current_children)} steps akan dijalankan berurutan")
                info_label.setStyleSheet("color: #64748b; font-size: 9px; padding: 2px 0 6px 0;")
                self.form_layout.addRow("", info_label)

                children_widget = QWidget()
                children_layout = QVBoxLayout(children_widget)
                children_layout.setContentsMargins(0, 4, 0, 4)
                children_layout.setSpacing(4)

                self._child_item_widgets = []
                for i, child in enumerate(self.current_children):
                    child_step_id = child.get("id", f"child_{i+1}")
                    child_type = child.get("type", "unknown")
                    child_label = child.get("label", child_type)
                    child_params = child.get("params", {})

                    child_item = ChildStepItem(
                        child_step_id, child_type, child_label, child_params, i + 1
                    )
                    child_item.edit_clicked.connect(lambda idx: self.edit_child_step(idx))
                    child_item.remove_clicked.connect(lambda idx: self.remove_child_step(idx))
                    child_item.move_up_clicked.connect(lambda idx: self.move_child_up(idx))
                    child_item.move_down_clicked.connect(lambda idx: self.move_child_down(idx))
                    child_item.params_edited.connect(lambda idx, data: self._on_child_params_edited(idx, data))
                    children_layout.addWidget(child_item)
                    self._child_item_widgets.append(child_item)

                add_child_btn = QPushButton("+ Add Child Step")
                add_child_btn.setStyleSheet("""
                    QPushButton {
                        background: #FF5722;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background: #E64A19; }
                """)
                add_child_btn.clicked.connect(self.add_child_step)
                children_layout.addWidget(add_child_btn)

                children_layout.addStretch()
                self.form_layout.addRow("", children_widget)
            else:
                empty_label = QLabel("  (Belum ada child steps)")
                empty_label.setStyleSheet("color: #94a3b8; font-size: 9px; padding: 8px;")
                self.form_layout.addRow("", empty_label)

        elif action_type == "if_else":
            self._add_field("condition", self.current_params.get("condition", ""))
            self._add_field("variable_name", self.current_params.get("variable_name", ""))
            self._add_field("expected_value", self.current_params.get("expected_value", ""))

        elif action_type == "navigate":
            self._add_field("url", self.current_params.get("url", ""))
            self._add_field("wait_until", self.current_params.get("wait_until", "domcontentloaded"))
            self._add_field("timeout", self.current_params.get("timeout", 30000))

        elif action_type == "parallel_group":
            # === PARALLEL GROUP: Tampilan khusus dengan child steps ===
            self._add_field("timeout", self.current_params.get("timeout", 30000))
            self._add_field("stagger_delay", self.current_params.get("stagger_delay", 200))
            self._add_field("on_error", self.current_params.get("on_error", "skip"))

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background: #e2e8f0; max-height: 1px; margin: 8px 0;")
            self.form_layout.addRow("", sep)

            # Children section header
            children_header = QLabel("  ⚡ Child Steps (Concurrent)")
            children_header.setStyleSheet("""
                color: #009688; font-weight: bold; font-size: 11px;
                padding: 6px 0; border-bottom: 2px solid #009688;
            """)
            self.form_layout.addRow("", children_header)

            # Info label
            info_label = QLabel(f"  {len(self.current_children)} steps akan dijalankan paralel")
            info_label.setStyleSheet("color: #64748b; font-size: 9px; padding: 2px 0 6px 0;")
            self.form_layout.addRow("", info_label)

            # List of child steps
            if self.current_children:
                children_widget = QWidget()
                children_layout = QVBoxLayout(children_widget)
                children_layout.setContentsMargins(0, 4, 0, 4)
                children_layout.setSpacing(4)

                self._child_item_widgets = []
                for i, child in enumerate(self.current_children):
                    child_step_id = child.get("id", f"child_{i+1}")
                    child_type = child.get("type", "unknown")
                    child_label = child.get("label", child_type)
                    child_params = child.get("params", {})

                    child_item = ChildStepItem(
                        child_step_id, child_type, child_label, child_params, i + 1
                    )
                    child_item.edit_clicked.connect(lambda idx: self.edit_child_step(idx))
                    child_item.remove_clicked.connect(lambda idx: self.remove_child_step(idx))
                    child_item.move_up_clicked.connect(lambda idx: self.move_child_up(idx))
                    child_item.move_down_clicked.connect(lambda idx: self.move_child_down(idx))
                    child_item.params_edited.connect(lambda idx, data: self._on_child_params_edited(idx, data))
                    children_layout.addWidget(child_item)
                    self._child_item_widgets.append(child_item)

                # Add Child Step button
                add_child_btn = QPushButton("+ Add Child Step")
                add_child_btn.setStyleSheet("""
                    QPushButton {
                        background: #009688;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background: #00897b; }
                """)
                add_child_btn.clicked.connect(self.add_child_step)
                children_layout.addWidget(add_child_btn)

                children_layout.addStretch()
                self.form_layout.addRow("", children_widget)
            else:
                empty_label = QLabel("  (Belum ada child steps - tambahkan via workflow editor)")
                empty_label.setStyleSheet("color: #94a3b8; font-size: 9px; padding: 8px;")
                self.form_layout.addRow("", empty_label)

        # Always add label at the end
        self._add_field("label", self.current_params.get("label", ""))

    def _add_field(self, key: str, value):
        """Tambah field ke form dengan deskripsi tooltip."""
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

        # Tooltip deskripsi
        desc = FIELD_DESCRIPTIONS.get(key, "")
        if desc:
            widget.setToolTip(desc)
            # Tambahkan placeholder untuk QLineEdit
            if isinstance(widget, QLineEdit):
                widget.setPlaceholderText(desc)

        self.form_layout.addRow(f"{label}:", widget)

    def _on_list_param_change(self, key: str, value: str):
        """Handle perubahan parameter list (comma-separated)."""
        items = [item.strip() for item in value.split(",") if item.strip()]
        self.current_params[key] = items
        self.params_changed.emit(self.current_step_id, self.current_params)
        if not self._building_form:
            self._mark_modified()

    def _on_param_change(self, key: str, value):
        """Handle perubahan parameter."""
        self.current_params[key] = value
        self.params_changed.emit(self.current_step_id, self.current_params)
        if not self._building_form:
            self._mark_modified()

    def add_child_step(self):
        """Tambah child step baru ke loop atau parallel_group."""
        from backend.core.action_registry import ActionRegistry
        from backend.actions.click_action import ClickAction
        from backend.actions.input_text_action import InputTextAction
        from backend.actions.wait_action import WaitAction
        from backend.actions.select_dropdown_action import SelectDropdownAction
        from backend.actions.select_action import SelectAction
        from backend.actions.select2_action import Select2Action
        from backend.actions.radio_select_action import RadioSelectAction
        from backend.actions.upload_file_action import UploadFileAction
        from backend.actions.http_submit_action import HttpSubmitAction
        from backend.actions.loop_action import LoopAction
        from backend.actions.if_else_action import IfElseAction
        from backend.actions.parallel_group_action import ParallelGroupAction
        from backend.actions.navigate_action import NavigateAction
        registry = ActionRegistry()
        registry.register(ClickAction())
        registry.register(InputTextAction())
        registry.register(WaitAction())
        registry.register(SelectDropdownAction())
        registry.register(SelectAction())
        registry.register(Select2Action())
        registry.register(RadioSelectAction())
        registry.register(UploadFileAction())
        registry.register(HttpSubmitAction())
        registry.register(LoopAction())
        registry.register(IfElseAction())
        registry.register(ParallelGroupAction())
        registry.register(NavigateAction())
        actions = registry.get_action_descriptions()
        first_action = actions[0]["name"] if actions else "click"

        new_child = {
            "id": f"child_{len(self.current_children) + 1}",
            "type": first_action,
            "label": first_action.replace("_", " ").title(),
            "params": {"label": first_action.replace("_", " ").title()},
        }
        self.current_children.append(new_child)
        self.current_params["steps"] = self.current_children
        self.params_changed.emit(self.current_step_id, self.current_params)
        self._rebuild_form_for_type(self.current_action_type)
        self._mark_modified()

    def remove_child_step(self, index: int):
        """Hapus child step dari loop atau parallel_group."""
        if 0 <= index < len(self.current_children):
            del self.current_children[index]
            self.current_params["steps"] = self.current_children
            self.params_changed.emit(self.current_step_id, self.current_params)
            self._rebuild_form_for_type(self.current_action_type)
            self._mark_modified()

    def move_child_up(self, index: int):
        """Pindah child step ke atas."""
        if index > 0 and index < len(self.current_children):
            self.current_children[index], self.current_children[index - 1] = \
                self.current_children[index - 1], self.current_children[index]
            self.current_params["steps"] = self.current_children
            self.params_changed.emit(self.current_step_id, self.current_params)
            self._rebuild_form_for_type(self.current_action_type)
            self._mark_modified()

    def move_child_down(self, index: int):
        """Pindah child step ke bawah."""
        if 0 <= index < len(self.current_children) - 1:
            self.current_children[index], self.current_children[index + 1] = \
                self.current_children[index + 1], self.current_children[index]
            self.current_params["steps"] = self.current_children
            self.params_changed.emit(self.current_step_id, self.current_params)
            self._rebuild_form_for_type(self.current_action_type)
            self._mark_modified()

    def edit_child_step(self, index: int):
        """Edit child step - masukkan inline edit mode di ChildStepItem."""
        if 0 <= index < len(self.current_children):
            child_item = self._child_item_widgets[index]
            if isinstance(child_item, ChildStepItem):
                child_item.enter_edit_mode()

    def _on_child_params_edited(self, index: int, child_data: dict):
        """Handle inline edit dari ChildStepItem."""
        if 0 <= index < len(self.current_children):
            self.current_children[index] = child_data
            self.current_params["steps"] = self.current_children
            self.params_changed.emit(self.current_step_id, self.current_params)
            self._mark_modified()

    def clear(self):
        """Bersihkan form."""
        self.current_step_id = ""
        self.current_params = {}
        self.current_action_type = ""
        self.current_children = []
        self._child_item_widgets = []
        self._is_modified = False
        self.no_selection_label.show()
        self.form_widget.hide()
        self.action_header.hide()
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)