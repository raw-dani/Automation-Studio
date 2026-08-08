"""
Workflow Editor - Tree/list view untuk menampilkan struktur workflow secara detail.
Mendukung nested children untuk loop, parallel_group, if_else.
Dilengkapi empty state (belum ada workflow) dan workflow info bar.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QStackedWidget,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QEvent
from PySide6.QtGui import QFont, QColor, QBrush, QIcon

from backend.core.workflow_parser import Workflow, WorkflowStep


WORKFLOW_COLORS = {
    "wait": ("#FFF8E1", "#FFC107", "#F57F17"),
    "click": ("#E3F2FD", "#2196F3", "#1565C0"),
    "input_text": ("#F3E5F5", "#9C27B0", "#7B1FA2"),
    "select": ("#E0F7FA", "#00BCD4", "#006064"),
    "select2": ("#E0F7FA", "#00BCD4", "#006064"),
    "select_dropdown": ("#FFF3E0", "#FF9800", "#E65100"),
    "radio_select": ("#FBE9E7", "#FF5722", "#BF360C"),
    "upload_file": ("#E8F5E9", "#4CAF50", "#2E7D32"),
    "loop": ("#FBE9E7", "#FF5722", "#BF360C"),
    "if_else": ("#E8EAF6", "#3F51B5", "#283593"),
    "parallel_group": ("#E0F2F1", "#009688", "#004D40"),
    "navigate": ("#F3E5F5", "#9C27B0", "#7B1FA2"),
    "default": ("#ECEFF1", "#607D8B", "#37474F"),
}

# Deskripsi singkat per tipe action
ACTION_DESCRIPTIONS = {
    "click": "Klik elemen pada halaman",
    "wait": "Tunggu selama durasi tertentu",
    "navigate": "Navigasi ke URL tertentu",
    "input_text": "Isi teks ke input field",
    "input_date": "Isi tanggal ke input field",
    "select": "Pilih opsi dari dropdown/combobox",
    "select2": "Pilih opsi menggunakan Select2",
    "select_dropdown": "Pilih opsi dari dropdown menu",
    "radio_select": "Pilih radio button",
    "upload_file": "Upload file ke halaman",
    "http_submit": "Submit data melalui HTTP",
    "loop": "Ulangi langkah-langkah di dalamnya",
    "if_else": "Percabangan kondisi (then/else)",
    "parallel_group": "Jalankan langkah-langkah paralel",
    "ocr": "Deteksi teks menggunakan OCR",
    "image_detect": "Deteksi gambar/elemen visual",
    "extract": "Ekstrak data dari halaman",
    "transform": "Transformasi data",
}

# Ikon per tipe action
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


class WorkflowTreeWidget(QTreeWidget):
    """
    QTreeWidget khusus yang menerima drag & drop action dari palette.
    """

    action_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.DropOnly)
        self.setDefaultDropAction(Qt.CopyAction)
        self.drag_drop_enabled = True

    def dragEnterEvent(self, event):
        if self.drag_drop_enabled and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self.drag_drop_enabled and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not self.drag_drop_enabled:
            event.ignore()
            return

        mime = event.mimeData()
        if mime.hasText():
            action_type = mime.text().strip()
            if action_type:
                self._pending_action_type = action_type
                self._pending_drop_pos = event.position()
                self.action_dropped.emit(action_type)
                event.acceptProposedAction()
                return
        event.ignore()


class EmptyStatePage(QWidget):
    """
    Halaman placeholder saat belum ada workflow yang dibuka.
    Menampilkan info untuk membuat workflow baru atau membuka file.
    """

    new_workflow_requested = Signal()
    open_workflow_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyStatePage")
        self.setStyleSheet("""
            #emptyStatePage { background: #F8FAFC; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)
        layout.addStretch()

        # ==================== ICON ====================
        icon_label = QLabel("⚙️")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)

        # ==================== TITLE ====================
        title = QLabel("No Workflow Loaded")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setStyleSheet("color: #1E293B;")
        layout.addWidget(title)

        # ==================== DESCRIPTION ====================
        desc = QLabel(
            "Mulai dengan membuat workflow baru atau buka file workflow yang sudah ada.\n"
            "Workflow akan ditampilkan sebagai struktur bertingkat yang mudah dipahami."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(desc)

        layout.addSpacing(16)

        # ==================== ACTION BUTTONS ====================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        # New workflow button
        new_btn = QPushButton("➕  Create New Workflow")
        new_btn.setFixedHeight(40)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6; color: white;
                border: none; border-radius: 8px;
                font-weight: bold; font-size: 12px;
                padding: 0 20px;
            }
            QPushButton:hover { background: #2563EB; }
            QPushButton:pressed { background: #1D4ED8; }
        """)
        new_btn.clicked.connect(self.new_workflow_requested.emit)
        btn_layout.addWidget(new_btn)

        # Open workflow button
        open_btn = QPushButton("📂  Open Workflow File")
        open_btn.setFixedHeight(40)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #1E293B;
                border: 2px solid #CBD5E1; border-radius: 8px;
                font-weight: bold; font-size: 12px;
                padding: 0 20px;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }
            QPushButton:pressed { background: #E2E8F0; }
        """)
        open_btn.clicked.connect(self.open_workflow_requested.emit)
        btn_layout.addWidget(open_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

        # ==================== HINT FOOTER ====================
        hint = QLabel("💡 Tips: Setelah membuat workflow, drag action dari sidebar kiri ke editor.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #94A3B8; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)


class WorkflowInfoBar(QFrame):
    """
    Bar informasi ringkas tentang workflow yang sedang dibuka.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workflowInfoBar")
        self.setStyleSheet("""
            #workflowInfoBar {
                background: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # ==================== WORKFLOW NAME ====================
        self.name_icon = QLabel("📋")
        self.name_icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.name_icon)

        self.name_label = QLabel("-")
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #1E293B;")
        self.name_label.setToolTip("Workflow name")
        layout.addWidget(self.name_label)

        # ==================== VERSION ====================
        self.version_badge = QLabel("v1.0")
        self.version_badge.setStyleSheet("""
            QLabel {
                background: #F1F5F9; color: #475569;
                border-radius: 8px; padding: 2px 8px;
                font-size: 9px; font-weight: bold;
            }
        """)
        layout.addWidget(self.version_badge)

        layout.addStretch()

        # ==================== STATS ====================
        self.step_count_label = QLabel("0 steps")
        self.step_count_label.setStyleSheet(
            "color: #3B82F6; font-weight: bold; font-size: 10px;"
        )
        self.step_count_label.setToolTip("Total steps di workflow")
        layout.addWidget(self.step_count_label)

        self.nested_count_label = QLabel("0 nested")
        self.nested_count_label.setStyleSheet(
            "color: #F59E0B; font-weight: bold; font-size: 10px;"
        )
        self.nested_count_label.setToolTip("Total step bersarang (nested)")
        layout.addWidget(self.nested_count_label)

        self.url_label = QLabel("")
        self.url_label.setStyleSheet("color: #94A3B8; font-size: 9px;")
        self.url_label.setToolTip("Target URL")
        layout.addWidget(self.url_label)

    def set_workflow_info(self, workflow: Workflow):
        """Update info bar berdasarkan workflow."""
        self.name_label.setText(workflow.name or "Untitled Workflow")
        self.version_badge.setText(f"v{workflow.version}")
        self.url_label.setText(workflow.url if workflow.url else "")

        # Hitung statistik
        total_steps = 0
        nested_steps = 0

        def count_steps(steps, depth=0):
            nonlocal total_steps, nested_steps
            for s in steps:
                total_steps += 1
                if s.children:
                    nested_steps += 1
                    count_steps(s.children, depth + 1)

        count_steps(workflow.steps)

        self.step_count_label.setText(f"{total_steps} steps")
        self.nested_count_label.setText(f"{nested_steps} nested")

    def clear(self):
        """Reset info bar."""
        self.name_label.setText("-")
        self.version_badge.setText("v1.0")
        self.step_count_label.setText("0 steps")
        self.nested_count_label.setText("0 nested")
        self.url_label.setText("")


class WorkflowEditor(QWidget):
    """
    Editor workflow berbasis tree/list dengan:
    - Empty state page saat belum ada workflow.
    - Info bar + tree view saat workflow sudah dibuka.
    """

    node_selected = Signal(str, dict, str)  # step_id, params, action_type
    node_deselected = Signal()
    nodes_changed = Signal()
    undo_available = Signal(bool)
    redo_available = Signal(bool)

    # Signals untuk empty state actions
    new_workflow_requested = Signal()
    open_workflow_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow = None
        self.current_file = None

        self._undo_stack = []
        self._redo_stack = []
        self._max_history = 20

        self._init_ui()

        # Connect tree drop signal ke handler
        self.tree.action_dropped.connect(self._on_tree_action_dropped)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ==================== STACKED WIDGET ====================
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # ---- Page 0: Empty State ----
        self.empty_state = EmptyStatePage()
        self.empty_state.new_workflow_requested.connect(
            self.new_workflow_requested.emit
        )
        self.empty_state.open_workflow_requested.connect(
            self.open_workflow_requested.emit
        )
        self.stack.addWidget(self.empty_state)

        # ---- Page 1: Loaded Workflow ----
        self.loaded_page = QWidget()
        loaded_layout = QVBoxLayout(self.loaded_page)
        loaded_layout.setContentsMargins(0, 0, 0, 0)
        loaded_layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 6, 8, 4)
        toolbar.setSpacing(6)

        title = QLabel("Workflow Structure")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #37474F;")
        toolbar.addWidget(title)

        toolbar.addStretch()

        self.undo_btn = QPushButton("↩ Undo")
        self.undo_btn.setEnabled(False)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1px solid #E2E8F0; border-radius: 4px;
                padding: 3px 8px; font-size: 10px;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:disabled { background: #F8FAFC; color: #CBD5E1; }
        """)
        self.undo_btn.clicked.connect(self.undo)
        toolbar.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("↪ Redo")
        self.redo_btn.setEnabled(False)
        self.redo_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1px solid #E2E8F0; border-radius: 4px;
                padding: 3px 8px; font-size: 10px;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:disabled { background: #F8FAFC; color: #CBD5E1; }
        """)
        self.redo_btn.clicked.connect(self.redo)
        toolbar.addWidget(self.redo_btn)

        toolbar.addSpacing(4)

        expand_btn = QPushButton("⤢ Expand")
        expand_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B;
                border: none; border-radius: 4px;
                padding: 3px 6px; font-size: 10px;
            }
            QPushButton:hover { background: #F1F5F9; color: #1E293B; }
        """)
        expand_btn.clicked.connect(self._expand_all)
        toolbar.addWidget(expand_btn)

        collapse_btn = QPushButton("⤡ Collapse")
        collapse_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B;
                border: none; border-radius: 4px;
                padding: 3px 6px; font-size: 10px;
            }
            QPushButton:hover { background: #F1F5F9; color: #1E293B; }
        """)
        collapse_btn.clicked.connect(self._collapse_all)
        toolbar.addWidget(collapse_btn)

        loaded_layout.addLayout(toolbar)

        # Workflow info bar
        self.info_bar = WorkflowInfoBar()
        loaded_layout.addWidget(self.info_bar)

        # Tree
        self.tree = WorkflowTreeWidget()
        self.tree.setHeaderLabels(["#", "Step", "Type", "Detail", "Info"])
        self.tree.setColumnWidth(0, 40)
        self.tree.setColumnWidth(1, 180)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 260)
        self.tree.setColumnWidth(4, 90)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #FAFAFA;
                alternate-background-color: #F5F5F5;
                font-size: 11px;
                border: none;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #E0E0E0;
            }
            QTreeWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
            }
            QTreeWidget::item:hover {
                background: #F0F0F0;
            }
            QHeaderView::section {
                background: #F8FAFC;
                padding: 5px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: bold;
                font-size: 10px;
                color: #475569;
            }
        """)
        loaded_layout.addWidget(self.tree, 1)

        self.stack.addWidget(self.loaded_page)

        # Default ke empty state
        self.stack.setCurrentWidget(self.empty_state)

    # ==================== STATE MANAGEMENT ====================

    def _show_empty_state(self):
        """Tampilkan empty state page."""
        self.stack.setCurrentWidget(self.empty_state)

    def _show_loaded_state(self):
        """Tampilkan loaded state page."""
        self.stack.setCurrentWidget(self.loaded_page)

    # ==================== DRAG & DROP ====================

    def _on_tree_action_dropped(self, action_type: str):
        """
        Handler ketika action di-drop ke tree.
        """
        if not self.workflow:
            return
        self.add_action_node(action_type)

    # ==================== WORKFLOW LOADING ====================

    def load_workflow(self, workflow: Workflow):
        """Load workflow ke tree view."""
        self.workflow = workflow
        selected_id = self._get_selected_step_id()
        self.tree.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_undo_redo_signals()

        global_idx = [0]

        def add_step(parent_item, step, depth=0):
            idx = global_idx[0]
            global_idx[0] += 1

            colors = WORKFLOW_COLORS.get(step.type, WORKFLOW_COLORS["default"])
            bg, border, text = colors

            item = QTreeWidgetItem(parent_item)
            item.setText(0, str(idx))
            item.setText(1, step.label or step.id)
            item.setText(2, f"{ACTION_ICONS.get(step.type, '🔹')} {step.type}")
            item.setText(3, self._summarize_params(step.params))

            # Info column: nested / loop / condition
            info_parts = []
            if step.children:
                child_count = len(step.children)
                info_parts.append(f"{child_count} child")
            if step.type == "loop" and step.params.get("loop_type"):
                info_parts.append(f"loop={step.params['loop_type']}")
            if step.on_error:
                info_parts.append(f"on_error={step.on_error}")
            item.setText(4, " | ".join(info_parts) if info_parts else "")

            item.setData(0, Qt.UserRole, step.id)
            item.setData(1, Qt.UserRole, step.type)

            font = QFont()
            font.setBold(depth == 0)
            font.setPointSize(10 if depth == 0 else 9)
            for col in range(5):
                item.setFont(col, font)

            # Styling
            for col in range(5):
                item.setBackground(col, QBrush(QColor(bg)))
                item.setForeground(col, QBrush(QColor(text)))

            # Tooltip informatif
            tooltip_lines = [
                f"<b>{ACTION_ICONS.get(step.type, '🔹')} {step.label or step.id}</b>",
                f"<span style='color:#64748B'>Type:</span> {step.type}",
                f"<span style='color:#64748B'>ID:</span> {step.id}",
            ]
            # Deskripsi action
            desc = ACTION_DESCRIPTIONS.get(step.type, "")
            if desc:
                tooltip_lines.append(f"<span style='color:#64748B'>Deskripsi:</span> {desc}")

            # Parameter summary
            param_summary = self._summarize_params(step.params, full=True)
            if param_summary and param_summary != "-":
                tooltip_lines.append(f"<span style='color:#64748B'>Params:</span> {param_summary}")

            if step.children:
                tooltip_lines.append(
                    f"<span style='color:#F59E0B'>Berisi {len(step.children)} step bersarang.</span>"
                )

            item.setToolTip(0, "<br>".join(tooltip_lines))
            for col in range(1, 5):
                item.setToolTip(col, item.toolTip(0))

            for child in step.children:
                add_step(item, child, depth + 1)

            return item

        for step in workflow.steps:
            add_step(self.tree.invisibleRootItem(), step)

        self.tree.expandAll()
        self.info_bar.set_workflow_info(workflow)
        self._restore_selection(selected_id)
        self._show_loaded_state()
        self.nodes_changed.emit()

    def clear(self):
        """Bersihkan editor dan kembali ke empty state."""
        self.workflow = None
        self.tree.clear()
        self.info_bar.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_undo_redo_signals()
        self._show_empty_state()

    # ==================== SELECTION & HELPERS ====================

    def _get_selected_step_id(self):
        selected = self.tree.selectedItems()
        if selected:
            return selected[0].data(0, Qt.UserRole)
        return None

    def _restore_selection(self, step_id):
        if not step_id:
            return
        found = self._find_item_by_id(self.tree.invisibleRootItem(), step_id)
        if found:
            found.setSelected(True)
            self.tree.scrollToItem(found)

    def _find_item_by_id(self, parent_item, step_id):
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            if item.data(0, Qt.UserRole) == step_id:
                return item
            result = self._find_item_by_id(item, step_id)
            if result:
                return result
        return None

    def _find_step(self, steps, step_id, _visited=None):
        """Cari step secara rekursif dengan safety check."""
        if _visited is None:
            _visited = set()

        for step in steps:
            step_key = id(step)
            if step_key in _visited:
                continue
            _visited.add(step_key)

            if step.id == step_id:
                return step
            if step.children:
                found = self._find_step(step.children, step_id, _visited)
                if found:
                    return found
        return None

    def _summarize_params(self, params: dict, full: bool = False) -> str:
        """Buat ringkasan parameter. Jika full=True, tampilkan semua parameter."""
        if not params:
            return "-"

        if full:
            parts = []
            for key, value in params.items():
                if value == "" or value is None:
                    continue
                parts.append(f"{key}={value}")
            return " | ".join(parts) if parts else "-"

        parts = []
        if "selector" in params:
            sel = str(params["selector"])
            parts.append(sel[:40] + "..." if len(sel) > 40 else sel)
        if "value" in params:
            val = str(params["value"])
            parts.append(val[:25] + "..." if len(val) > 25 else val)
        if "select_value" in params:
            val = str(params["select_value"])
            parts.append(f"label={val[:20]}")
        if "url" in params:
            url = str(params["url"])
            parts.append(url[:35] + "..." if len(url) > 35 else url)
        if "loop_type" in params:
            parts.append(f"loop={params['loop_type']}")
        if "duration" in params:
            parts.append(f"{params['duration']}ms")
        if "timeout" in params:
            parts.append(f"timeout={params['timeout']}ms")
        return " | ".join(parts) if parts else "-"

    # ==================== SELECTION HANDLER ====================

    def _on_selection_changed(self):
        selected = self.tree.selectedItems()
        if not selected:
            self.node_deselected.emit()
            return

        item = selected[0]
        step_id = item.data(0, Qt.UserRole)
        action_type = item.data(1, Qt.UserRole)
        params = {}

        if self.workflow:
            step = self._find_step(self.workflow.steps, step_id)
            if step:
                params = dict(step.params)

        self.node_selected.emit(step_id, params, action_type)

    # ==================== CONTEXT MENU ====================

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        step_id = item.data(0, Qt.UserRole)
        action_type = item.data(1, Qt.UserRole)

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: white; border: 1px solid #E2E8F0;
                border-radius: 6px; padding: 4px;
                font-size: 11px;
            }
            QMenu::item { padding: 5px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #E3F2FD; color: #1565C0; }
            QMenu::separator { height: 1px; background: #E2E8F0; margin: 4px 8px; }
        """)
        menu.addSection(f"⚙️  {step_id} ({action_type})")
        edit_action = menu.addAction("✏️  Edit Properties")
        delete_action = menu.addAction("🗑️  Delete Step")
        move_up_action = menu.addAction("⬆️  Move Up")
        move_down_action = menu.addAction("⬇️  Move Down")

        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._edit_step(step_id)
        elif action == delete_action:
            self._delete_step(step_id)
        elif action == move_up_action:
            self._move_step(step_id, -1)
        elif action == move_down_action:
            self._move_step(step_id, 1)

    def _edit_step(self, step_id):
        step = self._find_step(self.workflow.steps, step_id)
        if step:
            self.node_selected.emit(step_id, dict(step.params), step.type)

    def _delete_step(self, step_id):
        if not self.workflow:
            return
        self._capture_state()

        def remove_from(steps):
            for i, step in enumerate(steps):
                if step.id == step_id:
                    del steps[i]
                    return True
                if step.children and remove_from(step.children):
                    return True
            return False

        removed = remove_from(self.workflow.steps)
        if removed:
            self.load_workflow(self.workflow)
            self.nodes_changed.emit()

    def _move_step(self, step_id, direction):
        if not self.workflow:
            return False
        self._capture_state()

        def move_in(steps):
            for i, step in enumerate(steps):
                if step.id == step_id:
                    new_idx = i + direction
                    if 0 <= new_idx < len(steps):
                        steps[i], steps[new_idx] = steps[new_idx], steps[i]
                        return True
                    return False
                if step.children and move_in(step.children):
                    return True
            return False

        moved = move_in(self.workflow.steps)
        if moved:
            self.load_workflow(self.workflow)
            self.nodes_changed.emit()
        return moved

    # ==================== UNDO / REDO ====================

    def _capture_state(self):
        if len(self._undo_stack) >= self._max_history:
            self._undo_stack.pop(0)
        data = self.to_workflow_data()
        self._undo_stack.append(data)
        self._redo_stack.clear()
        self._update_undo_redo_signals()

    def _update_undo_redo_signals(self):
        self.undo_available.emit(len(self._undo_stack) > 0)
        self.redo_available.emit(len(self._redo_stack) > 0)
        self.undo_btn.setEnabled(len(self._undo_stack) > 0)
        self.redo_btn.setEnabled(len(self._redo_stack) > 0)

    def undo(self):
        if not self._undo_stack:
            return
        current = self.to_workflow_data()
        self._redo_stack.append(current)
        state = self._undo_stack.pop()
        self._load_workflow_data(state)
        self._update_undo_redo_signals()
        self.nodes_changed.emit()

    def redo(self):
        if not self._redo_stack:
            return
        current = self.to_workflow_data()
        self._undo_stack.append(current)
        state = self._redo_stack.pop()
        self._load_workflow_data(state)
        self._update_undo_redo_signals()
        self.nodes_changed.emit()

    def _load_workflow_data(self, data: dict):
        from backend.core.workflow_parser import WorkflowParser
        parser = WorkflowParser()
        try:
            workflow = parser.parse(data)
            self.load_workflow(workflow)
        except Exception as e:
            QMessageBox.critical(self, "Workflow Error", f"Gagal memuat workflow:\n{str(e)}")
            print(f"Failed to load workflow data: {e}")

    # ==================== SERIALIZATION ====================

    def to_workflow_data(self) -> dict:
        if not self.workflow:
            return {}

        steps = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            step_id = item.data(0, Qt.UserRole)
            step = self._find_step(self.workflow.steps, step_id)
            if not step:
                continue

            step_dict = {
                "id": step.id,
                "type": step.type,
                "label": step.label,
                "params": dict(step.params),
                "on_error": step.on_error,
                "retry": dict(step.retry) if step.retry else {"max_retries": 3, "delay": 2000},
            }

            if step.children:
                step_dict["steps"] = self._serialize_children(step.children)

            steps.append(step_dict)

        return {
            "id": self.workflow.id,
            "name": self.workflow.name,
            "version": self.workflow.version,
            "url": getattr(self.workflow, 'url', ''),
            "data_source": getattr(self.workflow, 'data_source', None),
            "steps": steps,
            "monitoring": getattr(self.workflow, 'monitoring', {}),
            "created_at": getattr(self.workflow, 'created_at', ''),
            "updated_at": getattr(self.workflow, 'updated_at', ''),
        }

    def _serialize_children(self, children):
        result = []
        for c in children:
            child_dict = {
                "id": c.id,
                "type": c.type,
                "label": c.label,
                "params": dict(c.params),
                "on_error": c.on_error,
                "retry": dict(c.retry) if c.retry else {"max_retries": 3, "delay": 2000},
            }
            if c.children:
                child_dict["steps"] = self._serialize_children(c.children)
            result.append(child_dict)
        return result

    # ==================== NODE UPDATE ====================

    def update_node_params(self, step_id: str, params: dict):
        if not self.workflow:
            return
        self._capture_state()

        step = self._find_step(self.workflow.steps, step_id)
        if step:
            step.params = params
            if "label" in params:
                step.label = params["label"]

            if "steps" in params:
                new_children = []
                for child_data in params.get("steps", []):
                    new_children.append(WorkflowStep(
                        id=child_data.get("id", f"child_{len(new_children) + 1}"),
                        type=child_data.get("type", "unknown"),
                        label=child_data.get("label", ""),
                        params=child_data.get("params", {}),
                        on_error=child_data.get("on_error", "skip"),
                        retry=child_data.get("retry", {"max_retries": 3, "delay": 2000}),
                    ))
                step.children = new_children

        self._update_tree_item(step_id)
        self.nodes_changed.emit()

    def _update_tree_item(self, step_id: str):
        """Perbarui item tree tanpa rebuild penuh."""
        if not self.workflow:
            return
        step = self._find_step(self.workflow.steps, step_id)
        if not step:
            return

        def update_item(parent_item, s):
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                item_id = item.data(0, Qt.UserRole)
                if item_id == s.id:
                    item.setText(1, s.label or s.id)
                    item.setText(2, f"{ACTION_ICONS.get(s.type, '🔹')} {s.type}")
                    item.setText(3, self._summarize_params(s.params))

                    info_parts = []
                    if s.children:
                        info_parts.append(f"{len(s.children)} child")
                    if s.type == "loop" and s.params.get("loop_type"):
                        info_parts.append(f"loop={s.params['loop_type']}")
                    if s.on_error:
                        info_parts.append(f"on_error={s.on_error}")
                    item.setText(4, " | ".join(info_parts) if info_parts else "")

                    colors = WORKFLOW_COLORS.get(s.type, WORKFLOW_COLORS["default"])
                    bg, border, text = colors
                    for col in range(5):
                        item.setBackground(col, QBrush(QColor(bg)))
                        item.setForeground(col, QBrush(QColor(text)))
                    break
                if s.children:
                    update_item(item, s)

        update_item(self.tree.invisibleRootItem(), step)
        self.info_bar.set_workflow_info(self.workflow)

    def _add_tree_item(self, step, parent_item=None):
        """Tambah item tree untuk step baru tanpa rebuild penuh."""
        if parent_item is None:
            parent_item = self.tree.invisibleRootItem()

        idx = self._next_tree_index()
        colors = WORKFLOW_COLORS.get(step.type, WORKFLOW_COLORS["default"])
        bg, border, text = colors

        item = QTreeWidgetItem(parent_item)
        item.setText(0, str(idx))
        item.setText(1, step.label or step.id)
        item.setText(2, f"{ACTION_ICONS.get(step.type, '🔹')} {step.type}")
        item.setText(3, self._summarize_params(step.params))
        item.setText(4, "")

        if step.children:
            item.setText(4, f"{len(step.children)} child")

        item.setData(0, Qt.UserRole, step.id)
        item.setData(1, Qt.UserRole, step.type)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        for col in range(5):
            item.setFont(col, font)

        for col in range(5):
            item.setBackground(col, QBrush(QColor(bg)))
            item.setForeground(col, QBrush(QColor(text)))

        # Tooltip
        desc = ACTION_DESCRIPTIONS.get(step.type, "")
        tooltip_lines = [
            f"<b>{ACTION_ICONS.get(step.type, '🔹')} {step.label or step.id}</b>",
            f"<span style='color:#64748B'>Type:</span> {step.type}",
            f"<span style='color:#64748B'>ID:</span> {step.id}",
        ]
        if desc:
            tooltip_lines.append(f"<span style='color:#64748B'>Deskripsi:</span> {desc}")
        item.setToolTip(0, "<br>".join(tooltip_lines))
        for col in range(1, 5):
            item.setToolTip(col, item.toolTip(0))

        for child in step.children:
            self._add_tree_item(child, item)

        self.info_bar.set_workflow_info(self.workflow)
        return item

    def _next_tree_index(self):
        count = [0]

        def walk(parent):
            for i in range(parent.childCount()):
                walk(parent.child(i))
                count[0] += 1

        walk(self.tree.invisibleRootItem())
        return count[0]

    # ==================== NODE TYPE CHANGE ====================

    def change_node_type(self, step_id: str, new_type: str):
        if not self.workflow:
            return
        self._capture_state()

        step = self._find_step(self.workflow.steps, step_id)
        if step:
            step.type = new_type
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
        action = registry.get(new_type)
        if action:
            step.params = action.default_params.copy()
            step.label = step.label or new_type.replace("_", " ").title()

        self._update_tree_item(step_id)
        self.nodes_changed.emit()

    # ==================== ADD NODE ====================

    def _generate_unique_step_id(self, base: str = "step") -> str:
        existing_ids = set()

        def collect(steps):
            for s in steps:
                existing_ids.add(s.id)
                if s.children:
                    collect(s.children)

        if self.workflow:
            collect(self.workflow.steps)

        counter = 1
        while True:
            candidate = f"{base}_{counter}"
            if candidate not in existing_ids:
                return candidate
            counter += 1

    def add_action_node(self, action_type: str, params: dict = None, label: str = "", step_id: str = None):
        if not self.workflow:
            return None
        self._capture_state()

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
        action = registry.get(action_type)
        default_params = action.default_params.copy() if action else {}
        if params:
            default_params.update(params)

        new_step = WorkflowStep(
            id=step_id or self._generate_unique_step_id(action_type),
            type=action_type,
            label=label or action_type.replace("_", " ").title(),
            params=default_params,
            on_error="stop",
            retry={"max_retries": 3, "delay": 2000},
        )
        self.workflow.steps.append(new_step)

        # Tambah item tree tanpa rebuild penuh
        self._add_tree_item(new_step)
        self.nodes_changed.emit()
        return new_step.id

    # ==================== DELETE / MOVE / SELECT ====================

    def delete_selected(self):
        selected = self.tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        step_id = item.data(0, Qt.UserRole)
        self._delete_step(step_id)

    def move_node_up(self, step_id: str) -> bool:
        return self._move_step(step_id, -1)

    def move_node_down(self, step_id: str) -> bool:
        return self._move_step(step_id, 1)

    def _expand_all(self):
        self.tree.expandAll()

    def _collapse_all(self):
        self.tree.collapseAll()

    def select_all(self):
        self.tree.selectAll()