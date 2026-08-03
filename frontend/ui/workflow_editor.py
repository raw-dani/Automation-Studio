"""
Workflow Editor - Tree/list view untuk menampilkan struktur workflow secara detail.
Mendukung nested children untuk loop, parallel_group, if_else.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
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


class WorkflowEditor(QWidget):
    """Editor workflow berbasis tree/list, bukan canvas."""

    node_selected = Signal(str, dict, str)  # step_id, params, action_type
    node_deselected = Signal()
    nodes_changed = Signal()
    undo_available = Signal(bool)
    redo_available = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow = None
        self.current_file = None

        self._undo_stack = []
        self._redo_stack = []
        self._max_history = 20

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 8, 8, 4)
        toolbar.setSpacing(6)

        title = QLabel("Workflow Structure")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #37474F;")
        toolbar.addWidget(title)

        toolbar.addStretch()

        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo)
        toolbar.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("Redo")
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self.redo)
        toolbar.addWidget(self.redo_btn)

        zoom_fit_btn = QPushButton("Expand All")
        zoom_fit_btn.clicked.connect(self._expand_all)
        toolbar.addWidget(zoom_fit_btn)

        zoom_fit_btn2 = QPushButton("Collapse All")
        zoom_fit_btn2.clicked.connect(self._collapse_all)
        toolbar.addWidget(zoom_fit_btn2)

        layout.addLayout(toolbar)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["#", "Step", "Type", "Selector / Value", "Status"])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 220)
        self.tree.setColumnWidth(2, 140)
        self.tree.setColumnWidth(3, 260)
        self.tree.setColumnWidth(4, 110)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.DropOnly)
        self.tree.setDefaultDropAction(Qt.CopyAction)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #FAFAFA;
                alternate-background-color: #F5F5F5;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #E0E0E0;
            }
            QTreeWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
            }
            QTreeWidget::item:hover {
                background: #F0F0F0;
            }
        """)
        layout.addWidget(self.tree)

    # ==================== DRAG & DROP ====================

    def dragEnterEvent(self, event):
        """Accept drag if it contains text (action name)."""
        mime = event.mimeData()
        if mime.hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Accept drag move."""
        mime = event.mimeData()
        if mime.hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop - add action node from palette."""
        mime = event.mimeData()
        if mime.hasText():
            action_type = mime.text().strip()
            if action_type and self.workflow:
                self.add_action_node(action_type)
                event.acceptProposedAction()
                return
        event.ignore()

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
            item.setText(2, step.type or "unknown")
            item.setText(3, self._summarize_params(step.params))
            item.setText(4, "")
            item.setData(0, Qt.UserRole, step.id)
            item.setData(1, Qt.UserRole, step.type)

            font = QFont()
            font.setBold(depth == 0)
            font.setPointSize(10 if depth == 0 else 9)
            for col in range(5):
                item.setFont(col, font)

            style = f"background: {bg}; color: {text}; border-left: 4px solid {border};"
            item.setBackground(0, QBrush(QColor(bg)))
            item.setBackground(1, QBrush(QColor(bg)))
            item.setForeground(0, QBrush(QColor(text)))
            item.setForeground(1, QBrush(QColor(text)))

            if depth == 0:
                item.setBackground(2, QBrush(QColor(bg)))
                item.setForeground(2, QBrush(QColor(text)))
                item.setBackground(3, QBrush(QColor(bg)))
                item.setForeground(3, QBrush(QColor(text)))
                item.setBackground(4, QBrush(QColor(bg)))
                item.setForeground(4, QBrush(QColor(text)))

            for child in step.children:
                add_step(item, child, depth + 1)

            return item

        for step in workflow.steps:
            add_step(self.tree.invisibleRootItem(), step)

        self.tree.expandAll()
        self._restore_selection(selected_id)
        self.nodes_changed.emit()

    def _get_selected_step_id(self):
        """Dapatkan step_id yang sedang dipilih."""
        selected = self.tree.selectedItems()
        if selected:
            return selected[0].data(0, Qt.UserRole)
        return None

    def _restore_selection(self, step_id):
        """Kembalikan seleksi tree ke step_id yang diberikan."""
        if not step_id:
            return
        found = self._find_item_by_id(self.tree.invisibleRootItem(), step_id)
        if found:
            found.setSelected(True)
            self.tree.scrollToItem(found)

    def _find_item_by_id(self, parent_item, step_id):
        """Cari QTreeWidgetItem berdasarkan step_id secara rekursif."""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            if item.data(0, Qt.UserRole) == step_id:
                return item
            result = self._find_item_by_id(item, step_id)
            if result:
                return result
        return None

    def _summarize_params(self, params: dict) -> str:
        """Buat ringkasan parameter untuk ditampilkan di kolom."""
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

    def _on_selection_changed(self):
        """Handle selection change."""
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

    def _find_step(self, steps, step_id, _visited=None):
        """Cari step secara rekursif dengan safety check untuk mencegah infinite recursion."""
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

    def _on_context_menu(self, pos):
        """Handle context menu."""
        item = self.tree.itemAt(pos)
        if not item:
            return

        step_id = item.data(0, Qt.UserRole)
        action_type = item.data(1, Qt.UserRole)

        menu = QMenu()
        menu.addSection(f"Step: {step_id} ({action_type})")
        edit_action = menu.addAction("Edit Properties")
        delete_action = menu.addAction("Delete Step")
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")

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
        """Edit step properties."""
        step = self._find_step(self.workflow.steps, step_id)
        if step:
            self.node_selected.emit(step_id, dict(step.params), step.type)

    def _delete_step(self, step_id):
        """Delete step from workflow."""
        pass

    def _move_step(self, step_id, direction):
        """Move step up or down."""
        pass

    def _capture_state(self):
        """Capture current workflow state for undo/redo."""
        if len(self._undo_stack) >= self._max_history:
            self._undo_stack.pop(0)
        data = self.to_workflow_data()
        self._undo_stack.append(data)
        self._redo_stack.clear()
        self._update_undo_redo_signals()

    def _update_undo_redo_signals(self):
        """Emit signals untuk update undo/redo button state."""
        self.undo_available.emit(len(self._undo_stack) > 0)
        self.redo_available.emit(len(self._redo_stack) > 0)
        self.undo_btn.setEnabled(len(self._undo_stack) > 0)
        self.redo_btn.setEnabled(len(self._redo_stack) > 0)

    def to_workflow_data(self) -> dict:
        """Konversi tree state ke dictionary workflow."""
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
        """Serialkan child steps termasuk nested children."""
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

    def undo(self):
        """Undo last action."""
        if not self._undo_stack:
            return
        current = self.to_workflow_data()
        self._redo_stack.append(current)
        state = self._undo_stack.pop()
        self._load_workflow_data(state)
        self._update_undo_redo_signals()
        self.nodes_changed.emit()

    def redo(self):
        """Redo last undone action."""
        if not self._redo_stack:
            return
        current = self.to_workflow_data()
        self._undo_stack.append(current)
        state = self._redo_stack.pop()
        self._load_workflow_data(state)
        self._update_undo_redo_signals()
        self.nodes_changed.emit()

    def _load_workflow_data(self, data: dict):
        """Load workflow dari dictionary."""
        from backend.core.workflow_parser import WorkflowParser
        parser = WorkflowParser()
        try:
            workflow = parser.parse(data)
            self.load_workflow(workflow)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Workflow Error", f"Gagal memuat workflow:\n{str(e)}")
            print(f"Failed to load workflow data: {e}")

    def update_node_params(self, step_id: str, params: dict):
        """Update parameter node yang dipilih."""
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
        """Perbarui teks QTreeWidgetItem untuk step tertentu tanpa rebuild penuh."""
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
                    item.setText(2, s.type)
                    item.setText(3, self._summarize_params(s.params))

                    colors = WORKFLOW_COLORS.get(s.type, WORKFLOW_COLORS["default"])
                    bg, border, text = colors
                    for col in range(5):
                        item.setBackground(col, QBrush(QColor(bg)))
                        item.setForeground(col, QBrush(QColor(text)))
                    break
                if s.children:
                    update_item(item, s)

        update_item(self.tree.invisibleRootItem(), step)

    def _add_tree_item(self, step, parent_item=None):
        """Tambah QTreeWidgetItem untuk step baru tanpa rebuild penuh."""
        if parent_item is None:
            parent_item = self.tree.invisibleRootItem()

        idx = self._next_tree_index()
        colors = WORKFLOW_COLORS.get(step.type, WORKFLOW_COLORS["default"])
        bg, border, text = colors

        item = QTreeWidgetItem(parent_item)
        item.setText(0, str(idx))
        item.setText(1, step.label or step.id)
        item.setText(2, step.type or "unknown")
        item.setText(3, self._summarize_params(step.params))
        item.setText(4, "")
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

        for child in step.children:
            self._add_tree_item(child, item)

        return item

    def _next_tree_index(self):
        """Dapatkan indeks berikutnya yang tersedia di tree."""
        count = [0]

        def walk(parent):
            for i in range(parent.childCount()):
                walk(parent.child(i))
                count[0] += 1

        walk(self.tree.invisibleRootItem())
        return count[0]

    def change_node_type(self, step_id: str, new_type: str):
        """Ubah tipe action node."""
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

    def add_action_node(self, action_type: str, params: dict = None, label: str = "", step_id: str = None):
        """Tambah step baru ke workflow."""
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
            id=step_id or f"step_{len(self.workflow.steps) + 1}",
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

    def delete_selected(self):
        """Hapus node yang dipilih."""
        selected = self.tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        step_id = item.data(0, Qt.UserRole)
        self._delete_step(step_id)

    def move_node_up(self, step_id: str) -> bool:
        """Pindah node ke atas."""
        return self._move_step(step_id, -1)

    def move_node_down(self, step_id: str) -> bool:
        """Pindah node ke bawah."""
        return self._move_step(step_id, 1)

    def _expand_all(self):
        """Expand all items."""
        self.tree.expandAll()

    def _collapse_all(self):
        """Collapse all items."""
        self.tree.collapseAll()

    def select_all(self):
        """Select semua item di tree."""
        self.tree.selectAll()

    def clear(self):
        """Bersihkan editor."""
        self.workflow = None
        self.tree.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_undo_redo_signals()
