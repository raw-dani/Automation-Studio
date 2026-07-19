"""
Workflow Editor - Canvas untuk drag & drop workflow nodes.
"""

import uuid
from typing import Optional
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
)
from PySide6.QtCore import (
    Qt, Signal, QRectF, QPointF, QLineF
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QLinearGradient, QTransform
)

from backend.core.workflow_parser import Workflow, WorkflowStep


# Colors
COLORS = {
    "click": {"bg": "#E3F2FD", "border": "#2196F3", "text": "#1565C0"},
    "input_text": {"bg": "#F3E5F5", "border": "#9C27B0", "text": "#7B1FA2"},
    "select": {"bg": "#E0F7FA", "border": "#00BCD4", "text": "#006064"},
    "select2": {"bg": "#E0F7FA", "border": "#00BCD4", "text": "#006064"},
    "select_dropdown": {"bg": "#FFF3E0", "border": "#FF9800", "text": "#E65100"},
    "upload_file": {"bg": "#E8F5E9", "border": "#4CAF50", "text": "#2E7D32"},
    "wait": {"bg": "#FFF8E1", "border": "#FFC107", "text": "#F57F17"},
    "loop": {"bg": "#FBE9E7", "border": "#FF5722", "text": "#BF360C"},
    "if_else": {"bg": "#E8EAF6", "border": "#3F51B5", "text": "#283593"},
    "navigate": {"bg": "#F3E5F5", "border": "#9C27B0", "text": "#7B1FA2"},
    "default": {"bg": "#ECEFF1", "border": "#607D8B", "text": "#37474F"},
}


class ActionNode(QGraphicsObject):
    """Node graphics item untuk satu action dalam workflow."""
    
    node_selected = Signal(str, dict)  # step_id, params
    node_moved = Signal(str, QPointF)
    
    def __init__(self, step_id: str, action_type: str, label: str = "",
                 params: dict = None, parent=None):
        super().__init__(parent)
        self.step_id = step_id
        self.action_type = action_type
        self.label = label or action_type
        self.params = params or {}
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Node dimensions
        self.width = 180
        self.height = 60
        
        # Get colors
        colors = COLORS.get(action_type, COLORS["default"])
        self.bg_color = QColor(colors["bg"])
        self.border_color = QColor(colors["border"])
        self.text_color = QColor(colors["text"])
        
        self._create_ui()
    
    def _create_ui(self):
        """Buat tampilan node."""
        # Background
        self.bg_rect = QGraphicsRectItem(0, 0, self.width, self.height, self)
        self.bg_rect.setBrush(QBrush(self.bg_color))
        self.bg_rect.setPen(QPen(self.border_color, 2))
        
        # Type label
        self.type_text = QGraphicsTextItem(self)
        self.type_text.setPlainText(f"[{self.action_type}]")
        self.type_text.setDefaultTextColor(self.text_color)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.type_text.setFont(font)
        self.type_text.setPos(8, 4)
        
        # Label
        self.label_text = QGraphicsTextItem(self)
        self.label_text.setPlainText(self.label)
        self.label_text.setDefaultTextColor(self.text_color)
        label_font = QFont()
        label_font.setPointSize(10)
        self.label_text.setFont(label_font)
        self.label_text.setPos(8, 22)
        
        # Index badge (set later)
        self.index_text = QGraphicsTextItem(self)
        self.index_text.setDefaultTextColor(QColor("#999"))
        index_font = QFont()
        index_font.setPointSize(8)
        self.index_text.setFont(index_font)
        self.index_text.setPos(self.width - 25, 4)
    
    def set_index(self, index: int):
        """Set nomor urut node."""
        self.index_text.setPlainText(f"#{index}")
    
    def update_label(self, label: str):
        """Update label node."""
        self.label = label
        self.label_text.setPlainText(label or self.action_type)
    
    def update_params(self, params: dict):
        """Update parameter node."""
        self.params = params
        if "label" in params:
            self.update_label(params["label"])
    
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget):
        pass  # All painting done by child items
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.node_moved.emit(self.step_id, value)
        return super().itemChange(change, value)
    
    def mouseDoubleClickEvent(self, event):
        """Double click to select and show properties."""
        self.node_selected.emit(self.step_id, self.params)
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """Single click to select."""
        super().mousePressEvent(event)
        if self.isSelected():
            self.node_selected.emit(self.step_id, self.params)


class ConnectionLine(QGraphicsLineItem):
    """Garis penghubung antar node."""
    
    def __init__(self, start_node: ActionNode, end_node: ActionNode, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        
        self.setPen(QPen(QColor("#90A4AE"), 2, Qt.DashLine))
        self.setZValue(-1)
        
        self._update_position()
    
    def _update_position(self):
        """Update posisi garis mengikuti node."""
        if self.start_node and self.end_node:
            start_pos = self.start_node.pos() + QPointF(self.start_node.width, 30)
            end_pos = self.end_node.pos() + QPointF(0, 30)
            self.setLine(QLineF(start_pos, end_pos))
    
    def update_position(self):
        self._update_position()


class WorkflowEditor(QGraphicsView):
    """
    Canvas editor untuk workflow nodes.
    Mendukung drag & drop, selection, zoom, dan koneksi antar node.
    """
    
    node_selected = Signal(str, dict)  # step_id, params
    node_deselected = Signal()
    nodes_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Data
        self.nodes: dict[str, ActionNode] = {}
        self.node_order: list[str] = []
        self.connections: list[ConnectionLine] = []
        self.node_counter = 0
        
        # Setup view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        
        # Grid background
        self.setBackgroundBrush(QBrush(QColor("#FAFAFA")))
        
        # Zoom
        self._zoom = 1.0
        self._min_zoom = 0.3
        self._max_zoom = 3.0
        
        # Selection tracking
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
        # Draw grid
        self._draw_grid()
    
    def _draw_grid(self):
        """Draw grid background."""
        grid_pen = QPen(QColor("#E0E0E0"), 1)
        for x in range(0, 3000, 50):
            self.scene.addLine(x, 0, x, 2000, grid_pen)
        for y in range(0, 2000, 50):
            self.scene.addLine(0, y, 3000, y, grid_pen)
    
    def add_action_node(self, action_type: str, params: dict = None,
                        pos: QPointF = None) -> str:
        """Tambah node action baru."""
        step_id = f"step_{self.node_counter + 1}"
        self.node_counter += 1
        
        label = params.get("label", action_type.replace("_", " ").title()) if params else action_type.replace("_", " ").title()
        
        node = ActionNode(step_id, action_type, label, params or {})
        node.set_index(self.node_counter)
        
        # Position
        if pos:
            node.setPos(pos)
        else:
            x = 100 + (self.node_counter % 3) * 250
            y = 100 + (self.node_counter // 3) * 120
            node.setPos(x, y)
        
        # Connect signals
        node.node_selected.connect(self._on_node_selected)
        node.node_moved.connect(self._update_connections)
        
        self.scene.addItem(node)
        self.nodes[step_id] = node
        self.node_order.append(step_id)
        
        # Auto-connect to previous node
        self._auto_connect(node)
        
        self.nodes_changed.emit()
        return step_id
    
    def _auto_connect(self, new_node: ActionNode):
        """Auto-connect node baru ke node sebelumnya."""
        prev_node = None
        for node_id, node in self.nodes.items():
            if node == new_node:
                break
            prev_node = node
        
        if prev_node:
            connection = ConnectionLine(prev_node, new_node)
            self.scene.addItem(connection)
            self.connections.append(connection)
    
    def _update_connections(self):
        """Update semua garis koneksi."""
        for conn in self.connections:
            conn.update_position()
    
    def _on_node_selected(self, step_id: str, params: dict):
        """Handle node selection."""
        self.node_selected.emit(step_id, params)
    
    def _on_selection_changed(self):
        """Handle selection change."""
        selected = self.scene.selectedItems()
        if not selected:
            self.node_deselected.emit()
    
    def load_workflow(self, workflow: Workflow):
        """Load workflow ke editor."""
        self.clear()
        
        for i, step in enumerate(workflow.steps):
            step_id = step.id or f"step_{i+1}"
            self.node_counter = max(self.node_counter, i + 1)
            
            node = ActionNode(step_id, step.type, step.label, step.params)
            node.set_index(i + 1)
            node.setPos(100, 100 + i * 120)
            
            node.node_selected.connect(self._on_node_selected)
            node.node_moved.connect(self._update_connections)
            
            self.scene.addItem(node)
            self.nodes[step_id] = node
            self.node_order.append(step_id)
            
            # Connect to previous
            if i > 0:
                prev_id = self.node_order[-2]
                prev_node = self.nodes[prev_id]
                connection = ConnectionLine(prev_node, node)
                self.scene.addItem(connection)
                self.connections.append(connection)
        
        self.nodes_changed.emit()
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def to_workflow_data(self) -> dict:
        """Konversi editor state ke dictionary workflow."""
        steps = []
        for i, step_id in enumerate(self.node_order):
            if step_id not in self.nodes:
                continue
            node = self.nodes[step_id]
            step = {
                "id": step_id,
                "type": node.action_type,
                "label": node.label,
                "params": node.params,
                "on_error": "stop",
                "retry": {"max_retries": 3, "delay": 2000},
            }
            steps.append(step)
        
        return {
            "id": f"workflow_{uuid.uuid4().hex[:8]}",
            "name": "My Workflow",
            "version": "1.0",
            "data_source": None,
            "steps": steps,
            "monitoring": {
                "screenshot_on_error": True,
                "screenshot_on_step": False,
                "log_level": "INFO",
            },
        }
    
    def update_node_params(self, step_id: str, params: dict):
        """Update parameter node yang dipilih."""
        if step_id in self.nodes:
            self.nodes[step_id].update_params(params)
    
    def change_node_type(self, step_id: str, new_type: str):
        """Ubah tipe action node."""
        if step_id not in self.nodes:
            return
        
        node = self.nodes[step_id]
        old_type = node.action_type
        
        if old_type == new_type:
            return
        
        # Update node type
        node.action_type = new_type
        node.type_text.setPlainText(f"[{new_type}]")
        
        # Update colors based on new type
        colors = COLORS.get(new_type, COLORS["default"])
        node.bg_color = QColor(colors["bg"])
        node.border_color = QColor(colors["border"])
        node.text_color = QColor(colors["text"])
        node.bg_rect.setBrush(QBrush(node.bg_color))
        node.bg_rect.setPen(QPen(node.border_color, 2))
        node.type_text.setDefaultTextColor(node.text_color)
        node.label_text.setDefaultTextColor(node.text_color)
        
        # Update params with default params for new type
        from backend.core.action_registry import ActionRegistry
        registry = ActionRegistry()
        action = registry.get(new_type)
        if action:
            default_params = action.default_params.copy()
            default_params["label"] = node.label
            node.params = default_params
            node.label_text.setPlainText(node.label)
        
        self.nodes_changed.emit()
    
    def delete_selected(self):
        """Hapus node yang dipilih."""
        for item in self.scene.selectedItems():
            if isinstance(item, ActionNode):
                # Remove connections
                self.connections = [c for c in self.connections
                                    if c.start_node != item and c.end_node != item]
                # Remove node
                step_id = item.step_id
                if step_id in self.nodes:
                    del self.nodes[step_id]
                if step_id in self.node_order:
                    self.node_order.remove(step_id)
                self.scene.removeItem(item)
        
        # Re-index
        for i, step_id in enumerate(self.node_order):
            if step_id in self.nodes:
                self.nodes[step_id].set_index(i + 1)
        
        self.nodes_changed.emit()
    
    def move_node_up(self, step_id: str) -> bool:
        """Pindah node ke atas dalam urutan eksekusi."""
        if step_id not in self.node_order:
            return False
        
        idx = self.node_order.index(step_id)
        if idx <= 0:
            return False
        
        self.node_order[idx], self.node_order[idx - 1] = self.node_order[idx - 1], self.node_order[idx]
        self._reorder_connections()
        self._reindex_nodes()
        self.nodes_changed.emit()
        return True
    
    def move_node_down(self, step_id: str) -> bool:
        """Pindah node ke bawah dalam urutan eksekusi."""
        if step_id not in self.node_order:
            return False
        
        idx = self.node_order.index(step_id)
        if idx >= len(self.node_order) - 1:
            return False
        
        self.node_order[idx], self.node_order[idx + 1] = self.node_order[idx + 1], self.node_order[idx]
        self._reorder_connections()
        self._reindex_nodes()
        self.nodes_changed.emit()
        return True
    
    def _reorder_connections(self):
        """Perbarui garis koneksi sesuai urutan node_order."""
        for i in range(len(self.connections)):
            if i + 1 < len(self.node_order):
                start_id = self.node_order[i]
                end_id = self.node_order[i + 1]
                if start_id in self.nodes and end_id in self.nodes:
                    self.connections[i].start_node = self.nodes[start_id]
                    self.connections[i].end_node = self.nodes[end_id]
        self._update_connections()
    
    def _reindex_nodes(self):
        """Perbarui nomor urut node sesuai node_order."""
        for i, step_id in enumerate(self.node_order):
            if step_id in self.nodes:
                self.nodes[step_id].set_index(i + 1)
    
    def clear(self):
        """Bersihkan semua node."""
        self.scene.clear()
        self.nodes.clear()
        self.node_order.clear()
        self.connections.clear()
        self.node_counter = 0
        self._draw_grid()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.delete_selected()
            event.accept()
            return
        
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, ActionNode):
                if event.modifiers() == Qt.ControlModifier:
                    if event.key() == Qt.Key_Up:
                        self.move_node_up(item.step_id)
                        event.accept()
                        return
                    elif event.key() == Qt.Key_Down:
                        self.move_node_down(item.step_id)
                        event.accept()
                        return
        
        super().keyPressEvent(event)
    
    def zoom_in(self):
        """Zoom in."""
        self._zoom = min(self._zoom * 1.2, self._max_zoom)
        transform = QTransform()
        transform.scale(self._zoom, self._zoom)
        self.setTransform(transform)
    
    def zoom_out(self):
        """Zoom out."""
        self._zoom = max(self._zoom / 1.2, self._min_zoom)
        transform = QTransform()
        transform.scale(self._zoom, self._zoom)
        self.setTransform(transform)
    
    def zoom_fit(self):
        """Fit to screen."""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self._zoom = self.transform().m11()
    
    def wheelEvent(self, event):
        """Zoom dengan scroll wheel."""
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def dragEnterEvent(self, event):
        """Accept drag events."""
        if event.mimeData().hasText() and event.mimeData().text().startswith("action:"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("action:"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """Handle drop dari action palette."""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("action:"):
                action_type = text[7:]  # Remove "action:" prefix
                pos = self.mapToScene(event.position().toPoint())
                self.add_action_node(action_type, {}, pos)
                event.acceptProposedAction()
                return
        super().dropEvent(event)