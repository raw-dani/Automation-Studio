"""
Action Palette - Sidebar berisi daftar action yang bisa didrag ke workflow editor.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QPushButton, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QDrag, QPixmap, QPainter, QColor

from backend.core.action_registry import ActionRegistry


class ActionItem(QFrame):
    """Modern card-style widget untuk satu action di palette."""
    
    def __init__(self, action_name: str, description: str, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(64)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Color indicator
        self.color_indicator = QFrame()
        self.color_indicator.setFixedWidth(4)
        self.color_indicator.setFixedHeight(40)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Action name
        name_label = QLabel(action_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #1a1a2e;")
        
        # Description
        desc_label = QLabel(description[:45] + ("..." if len(description) > 45 else ""))
        desc_label.setStyleSheet("color: #6b7280; font-size: 10px;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        
        layout.addWidget(self.color_indicator)
        layout.addLayout(text_layout, 1)
        
        # Modern stylesheet
        self.setStyleSheet("""
            ActionItem {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            ActionItem:hover {
                background: #f8fafc;
                border: 1px solid #3b82f6;
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
            painter.setOpacity(0.85)
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
    
    def set_color(self, color: str):
        """Set color indicator."""
        self.color_indicator.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: 2px;
            }}
        """)


class ActionPalette(QWidget):
    """Sidebar yang menampilkan daftar action yang tersedia."""
    
    action_dragged = Signal(str, dict)  # action_name, default_params
    node_moved_up = Signal()
    node_moved_down = Signal()
    
    def __init__(self, action_registry: ActionRegistry, parent=None):
        super().__init__(parent)
        self.action_registry = action_registry
        self.setWindowTitle("Actions")
        self.setMinimumWidth(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title with modern styling
        title_container = QFrame()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(4, 0, 4, 0)
        title_layout.setSpacing(8)
        
        title = QLabel("Actions")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        title.setStyleSheet("color: #1a1a2e;")
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addWidget(title_container)
        
        # Scroll area for actions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.actions_widget = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(6)
        
        scroll.setWidget(self.actions_widget)
        layout.addWidget(scroll)
        
        # Reorder controls
        reorder_container = QFrame()
        reorder_layout = QHBoxLayout(reorder_container)
        reorder_layout.setContentsMargins(0, 4, 0, 0)
        reorder_layout.setSpacing(6)
        
        self.move_up_btn = QPushButton("↑ Up")
        self.move_up_btn.setFixedHeight(32)
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 11px;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
            QPushButton:disabled { background: #f9fafb; color: #9ca3af; border-color: #e5e7eb; }
        """)
        self.move_up_btn.clicked.connect(lambda: self.node_moved_up.emit())
        reorder_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓ Down")
        self.move_down_btn.setFixedHeight(32)
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #374151;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 11px;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
            QPushButton:disabled { background: #f9fafb; color: #9ca3af; border-color: #e5e7eb; }
        """)
        self.move_down_btn.clicked.connect(lambda: self.node_moved_down.emit())
        reorder_layout.addWidget(self.move_down_btn)
        
        layout.addWidget(reorder_container)
        
        # Populate actions
        self._create_action_groups()
    
    def _create_action_groups(self):
        """Buat grup untuk setiap kategori action."""
        categories = {
            "Navigation": ["click", "wait", "navigate"],
            "Input": ["input_text", "select", "select2", "select_dropdown", "upload_file"],
            "Logic": ["loop", "if_else"],
        }
        
        # Category colors
        category_colors = {
            "Navigation": "#3b82f6",
            "Input": "#8b5cf6",
            "Logic": "#f59e0b",
        }
        
        for category, action_names in categories.items():
            # Category label
            category_label = QLabel(category)
            category_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            category_label.setStyleSheet(f"""
                color: {category_colors.get(category, '#6b7280')};
                padding: 4px 8px;
                margin-top: 4px;
            """)
            self.actions_layout.addWidget(category_label)
            
            # Action items
            for action_name in action_names:
                action = self.action_registry.get(action_name)
                if action:
                    item = ActionItem(action.name, action.description)
                    item.set_color(category_colors.get(category, "#6b7280"))
                    item.mousePressEvent = lambda e, a=action: self._on_action_click(e, a)
                    self.actions_layout.addWidget(item)
            
            # Add spacing between categories
            self.actions_layout.addSpacing(6)
    
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