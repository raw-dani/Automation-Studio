"""
Action Palette - Sidebar berisi daftar action yang bisa didrag ke workflow editor.
Dilengkapi: search filter, double-click add, collapsible categories, action badges, recently used, tooltips.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QPushButton, QFrame, QLineEdit,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve, QMimeData, QPoint
from PySide6.QtGui import QFont, QDrag, QPixmap, QPainter, QColor, QIcon, QMouseEvent

from backend.core.action_registry import ActionRegistry


# Category colors (same as before)
CATEGORY_COLORS = {
    "Navigation": "#3b82f6",
    "Input": "#8b5cf6",
    "Logic": "#f59e0b",
    "Detection": "#ef4444",
    "Data": "#10b981",
}

# Map category to action types
CATEGORY_ACTIONS = {
    "Navigation": ["click", "wait", "navigate"],
    "Input": ["input_text", "input_date", "select", "select2", "select_dropdown", "radio_select", "upload_file", "http_submit"],
    "Logic": ["loop", "if_else", "parallel_group"],
    "Detection": ["ocr", "image_detect"],
    "Data": ["extract", "transform"],
}


class ActionItem(QFrame):
    """Modern card-style widget untuk satu action di palette."""

    # Signal: action_name, default_params, is_double_click
    action_activated = Signal(str, dict, bool)

    def __init__(self, action_name: str, description: str, category: str = "", parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self._description = description
        self._category = category
        self._badge_count = 0
        self._use_count = 0

        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(64)
        self.setAcceptDrops(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Color indicator
        self.color_indicator = QFrame()
        self.color_indicator.setFixedWidth(4)
        self.color_indicator.setFixedHeight(40)
        self.color_indicator.setStyleSheet(f"""
            QFrame {{
                background: {CATEGORY_COLORS.get(category, '#6b7280')};
                border-radius: 2px;
            }}
        """)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Action name + badge
        name_row = QHBoxLayout()
        name_row.setSpacing(6)

        name_label = QLabel(action_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #1a1a2e;")
        name_row.addWidget(name_label)

        # Badge count (hidden by default)
        self.badge_label = QLabel("0")
        self.badge_label.setFixedWidth(20)
        self.badge_label.setFixedHeight(16)
        self.badge_label.setAlignment(Qt.AlignCenter)
        self.badge_label.setStyleSheet("""
            QLabel {
                background: #3b82f6; color: white; border-radius: 8px;
                font-size: 8px; font-weight: bold;
            }
        """)
        self.badge_label.hide()
        name_row.addWidget(self.badge_label)

        name_row.addStretch()
        text_layout.addLayout(name_row)

        # Description
        self.desc_label = QLabel(description[:45] + ("..." if len(description) > 45 else ""))
        self.desc_label.setStyleSheet("color: #6b7280; font-size: 10px;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setToolTip(description)  # Full description on hover
        text_layout.addWidget(self.desc_label)

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

    def set_badge_count(self, count: int):
        """Set badge count (how many of this action are in the workflow)."""
        self._badge_count = count
        if count > 0:
            self.badge_label.setText(str(count))
            self.badge_label.show()
        else:
            self.badge_label.hide()

    def increment_use_count(self):
        """Increment use count for recently used tracking."""
        self._use_count += 1

    def get_use_count(self) -> int:
        return self._use_count

    def mousePressEvent(self, event: QMouseEvent):
        """Start drag operation."""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = self._get_mime_data()
            drag.setMimeData(mime_data)

            # Create drag pixmap with shadow effect
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setOpacity(0.8)
            self.render(painter, QPoint(0, 0))
            painter.end()

            # Set hot spot to cursor position
            hot_spot = event.pos()
            drag.setHotSpot(hot_spot)
            drag.setPixmap(pixmap)

            drag.exec(Qt.CopyAction)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click to add action directly to editor."""
        if event.button() == Qt.LeftButton:
            self.action_activated.emit(self.action_name, {}, True)

    def _get_mime_data(self) -> QMimeData:
        """Create mime data for drag operation."""
        mime_data = QMimeData()
        mime_data.setText(self.action_name)
        return mime_data

    def get_description(self) -> str:
        """Get action description."""
        return self._description


class CategoryGroup(QWidget):
    """Collapsible category group with action items."""

    def __init__(self, category_name: str, color: str, parent=None):
        super().__init__(parent)
        self._category_name = category_name
        self._is_collapsed = False
        self._action_items: list[ActionItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Category header (clickable to collapse/expand)
        self.header = QPushButton()
        self.header.setFlat(True)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setFixedHeight(32)
        self.header.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 4px 8px;
                color: {color}; font-weight: bold; font-size: 10px;
                background: transparent; border: none;
            }}
            QPushButton:hover {{
                background: #f3f4f6;
                border-radius: 4px;
            }}
        """)
        self.header.setText(f"▼  {category_name}")
        self.header.clicked.connect(self._toggle_collapse)
        layout.addWidget(self.header)

        # Container for action items
        self.items_container = QFrame()
        self.items_container.setFrameShape(QFrame.NoFrame)
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        layout.addWidget(self.items_container)

        # Spacer after category
        self.spacer = QFrame()
        self.spacer.setFixedHeight(4)
        layout.addWidget(self.spacer)

    def add_action(self, item: ActionItem):
        """Add action item to this category."""
        self._action_items.append(item)
        self.items_layout.addWidget(item)

    def get_action_items(self) -> list[ActionItem]:
        return self._action_items

    def _toggle_collapse(self):
        """Toggle collapse/expand."""
        self._is_collapsed = not self._is_collapsed
        self.items_container.setVisible(not self._is_collapsed)
        self.header.setText(
            f"▶  {self._category_name}" if self._is_collapsed else f"▼  {self._category_name}"
        )

    def set_visible_by_filter(self, search_text: str):
        """Show/hide items based on search filter."""
        visible_count = 0
        for item in self._action_items:
            match = (
                search_text == "" or
                search_text.lower() in item.action_name.lower() or
                search_text.lower() in item._description.lower()
            )
            item.setVisible(match)
            if match:
                visible_count += 1

        # Show category header only if at least one item matches
        has_visible = visible_count > 0
        self.header.setVisible(has_visible)
        self.spacer.setVisible(has_visible)

        # Auto-expand if search active and items match
        if search_text and has_visible and self._is_collapsed:
            self._toggle_collapse()
        elif not search_text and not self._is_collapsed:
            # Keep as is
            pass

    def set_badge_counts(self, action_counts: dict[str, int]):
        """Update badge counts for all items."""
        for item in self._action_items:
            count = action_counts.get(item.action_name, 0)
            item.set_badge_count(count)


class ActionPalette(QWidget):
    """Sidebar yang menampilkan daftar action yang tersedia."""

    action_dragged = Signal(str, dict)  # action_name, default_params
    node_moved_up = Signal()
    node_moved_down = Signal()

    def __init__(self, action_registry: ActionRegistry, parent=None):
        super().__init__(parent)
        self.action_registry = action_registry
        self._category_groups: dict[str, CategoryGroup] = {}
        self._all_action_items: dict[str, ActionItem] = {}
        self._recently_used: list[str] = []
        self._max_recent = 5
        self.setWindowTitle("Actions")
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ==================== TITLE ====================
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

        # Action count badge
        self.action_count_label = QLabel("0 actions")
        self.action_count_label.setStyleSheet("color: #9ca3af; font-size: 9px;")

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.action_count_label)
        layout.addWidget(title_container)

        # ==================== SEARCH BAR ====================
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 2px;
            }
            QFrame:focus-within {
                border-color: #3b82f6;
                background: #ffffff;
            }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 12px;")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search actions...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none; background: transparent;
                font-size: 11px; color: #374151;
            }
            QLineEdit::placeholder { color: #9ca3af; }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)

        # Clear button
        self.search_clear_btn = QPushButton("✕")
        self.search_clear_btn.setFixedSize(16, 16)
        self.search_clear_btn.setStyleSheet("""
            QPushButton {
                background: #d1d5db; color: white; border: none;
                border-radius: 8px; font-size: 8px;
            }
            QPushButton:hover { background: #9ca3af; }
        """)
        self.search_clear_btn.clicked.connect(self._clear_search)
        self.search_clear_btn.hide()
        self.search_input.textChanged.connect(
            lambda: self.search_clear_btn.setVisible(bool(self.search_input.text()))
        )

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_clear_btn)
        layout.addWidget(search_container)

        # ==================== SCROLL AREA ====================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                width: 6px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db; border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.actions_widget = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(0)

        scroll.setWidget(self.actions_widget)
        layout.addWidget(scroll)

        # ==================== REORDER + RECENTLY USED ====================
        bottom_container = QFrame()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(4)

        # Reorder buttons
        reorder_layout = QHBoxLayout()
        reorder_layout.setSpacing(6)

        self.move_up_btn = QPushButton("↑ Up")
        self.move_up_btn.setFixedHeight(32)
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6; color: #374151;
                padding: 6px 12px; border-radius: 6px;
                font-weight: 500; font-size: 11px;
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
                background: #f3f4f6; color: #374151;
                padding: 6px 12px; border-radius: 6px;
                font-weight: 500; font-size: 11px;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
            QPushButton:disabled { background: #f9fafb; color: #9ca3af; border-color: #e5e7eb; }
        """)
        self.move_down_btn.clicked.connect(lambda: self.node_moved_down.emit())
        reorder_layout.addWidget(self.move_down_btn)

        bottom_layout.addLayout(reorder_layout)

        # Recently used label
        self.recent_label = QLabel("")
        self.recent_label.setStyleSheet("color: #9ca3af; font-size: 9px; padding: 2px 4px;")
        bottom_layout.addWidget(self.recent_label)

        layout.addWidget(bottom_container)

        # ==================== POPULATE ====================
        self._create_action_groups()
        self._update_action_count()

    # ==================== SEARCH ====================

    def _on_search_changed(self, text: str):
        """Filter actions by search text."""
        for group in self._category_groups.values():
            group.set_visible_by_filter(text)

    def _clear_search(self):
        """Clear search input."""
        self.search_input.clear()
        self.search_input.setFocus()

    # ==================== CATEGORY SETUP ====================

    def _create_action_groups(self):
        """Buat grup untuk setiap kategori action."""
        # Add recently used section first (if any)
        self.recent_group = CategoryGroup("Recently Used", "#ef4444")
        self.actions_layout.addWidget(self.recent_group)
        self._category_groups["Recently Used"] = self.recent_group

        for category, action_names in CATEGORY_ACTIONS.items():
            color = CATEGORY_COLORS.get(category, "#6b7280")
            group = CategoryGroup(category, color)
            self.actions_layout.addWidget(group)
            self._category_groups[category] = group

            for action_name in action_names:
                action = self.action_registry.get(action_name)
                if action:
                    item = ActionItem(action.name, action.description, category)
                    item.action_activated.connect(self._on_action_activated)
                    group.add_action(item)
                    self._all_action_items[action_name] = item

        # Add spacer at bottom
        self.actions_layout.addStretch()

    def _on_action_activated(self, action_name: str, params: dict, is_double_click: bool):
        """Handle action activation (drag or double-click)."""
        # Track recently used
        self._track_recently_used(action_name)

        # Increment use count
        if action_name in self._all_action_items:
            self._all_action_items[action_name].increment_use_count()

        self.action_dragged.emit(action_name, params)

    # ==================== RECENTLY USED ====================

    def _track_recently_used(self, action_name: str):
        """Track recently used actions."""
        if action_name in self._recently_used:
            self._recently_used.remove(action_name)
        self._recently_used.insert(0, action_name)
        if len(self._recently_used) > self._max_recent:
            self._recently_used = self._recently_used[:self._max_recent]

        self._update_recently_used()

    def _update_recently_used(self):
        """Update recently used section."""
        # Clear recent group
        for item in self.recent_group.get_action_items():
            self.recent_group.items_layout.removeWidget(item)
            item.setParent(None)

        if self._recently_used:
            self.recent_group.setVisible(True)
            for action_name in self._recently_used:
                if action_name in self._all_action_items:
                    original = self._all_action_items[action_name]
                    recent_item = ActionItem(
                        original.action_name,
                        original.get_description(),
                        "Recently Used"
                    )
                    recent_item.action_activated.connect(self._on_action_activated)
                    self.recent_group.add_action(recent_item)

            # Update label
            recent_text = " | ".join(self._recently_used[:3])
            self.recent_label.setText(f"Recent: {recent_text}")
        else:
            self.recent_group.setVisible(False)
            self.recent_label.setText("")

    # ==================== BADGE COUNTS ====================

    def update_action_counts(self, action_counts: dict[str, int]):
        """Update badge counts for all action items based on workflow steps.

        Args:
            action_counts: Dict mapping action_name -> count in current workflow.
        """
        for group in self._category_groups.values():
            group.set_badge_counts(action_counts)

        self._update_action_count()

    def _update_action_count(self):
        """Update total action count label."""
        total = len(self._all_action_items)
        self.action_count_label.setText(f"{total} actions")

    # ==================== PUBLIC API ====================

    def toggleViewAction(self):
        """Return action untuk toggle visibility."""
        from PySide6.QtGui import QAction
        action = QAction("Action Palette", self)
        action.setCheckable(True)
        action.setChecked(self.isVisible())
        action.triggered.connect(self.setVisible)
        return action

    def focus_search(self):
        """Focus the search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()
