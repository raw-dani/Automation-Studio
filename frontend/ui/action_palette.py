"""
Action Palette - Sidebar berisi daftar action yang bisa didrag ke workflow editor.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QDrag, QPixmap, QPainter, QColor

from backend.core.action_registry import ActionRegistry


class ActionItem(QWidget):
    """Widget untuk satu item action di palette."""
    
    def __init__(self, action_name: str, description: str, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Action name
        name_label = QLabel(action_name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #2196F3;")
        
        # Description
        desc_label = QLabel(description[:50] + ("..." if len(description) > 50 else ""))
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        desc_label.setWordWrap(True)
        
        layout.addWidget(name_label)
        layout.addWidget(desc_label)
        
        self.setStyleSheet("""
            ActionItem {
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin: 2px 4px;
            }
            ActionItem:hover {
                background: #e3f2fd;
                border-color: #2196F3;
            }
        """)
    
    def mousePressEvent(self, event):
        """Start drag operation."""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = self._get_mime_data()
            drag.setMimeData(mime_data)
            
            # Create drag pixmap
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setOpacity(0.8)
            self.render(painter)
            painter.end()
            drag.setPixmap(pixmap)
            
            drag.exec(Qt.CopyAction)
    
    def _get_mime_data(self):
        """Create mime data with action info."""
        from PySide6.QtCore import QMimeData
        mime = QMimeData()
        mime.setText(f"action:{self.action_name}")
        return mime


class ActionPalette(QWidget):
    """Sidebar yang menampilkan daftar action yang tersedia."""
    
    action_dragged = Signal(str, dict)  # action_name, default_params
    node_moved_up = Signal()
    node_moved_down = Signal()
    
    def __init__(self, action_registry: ActionRegistry, parent=None):
        super().__init__(parent)
        self.action_registry = action_registry
        self.setWindowTitle("Actions")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Action Palette")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px;")
        layout.addWidget(title)
        
        # Group by category
        self._create_action_groups(layout)
        
        # Reorder controls
        reorder_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("Up")
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800; color: white; padding: 6px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #F57C00; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.move_up_btn.clicked.connect(lambda: self.node_moved_up.emit())
        reorder_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("Down")
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; color: white; padding: 6px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #1976D2; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.move_down_btn.clicked.connect(lambda: self.node_moved_down.emit())
        reorder_layout.addWidget(self.move_down_btn)
        
        layout.addLayout(reorder_layout)
        layout.addStretch()
    
    def _create_action_groups(self, layout):
        """Buat grup untuk setiap kategori action."""
        categories = {
            "Navigation": ["click", "wait", "navigate"],
            "Input": ["input_text", "select", "select2", "select_dropdown", "upload_file"],
            "Logic": ["loop", "if_else"],
        }
        
        for category, action_names in categories.items():
            group = QGroupBox(category)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(4, 8, 4, 4)
            group_layout.setSpacing(4)
            
            for action_name in action_names:
                action = self.action_registry.get(action_name)
                if action:
                    item = ActionItem(action.name, action.description)
                    item.mousePressEvent = lambda e, a=action: self._on_action_click(e, a)
                    group_layout.addWidget(item)
            
            group_layout.addStretch()
            layout.addWidget(group)
    
    def _on_action_click(self, event, action):
        """Handle klik pada action item."""
        if event.button() == Qt.LeftButton:
            self.action_dragged.emit(action.name, action.default_params)
    
    def toggleViewAction(self):
        """Return action untuk toggle visibility."""
        from PySide6.QtGui import QAction
        action = QAction("Action Palette", self)
        action.setCheckable(True)
        action.setChecked(self.isVisible())
        action.triggered.connect(self.setVisible)
        return action