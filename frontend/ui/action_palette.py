"""
Action Palette - Sidebar berisi daftar action compact berbasis icon list.
Fitur: search filter, double-click add, collapsible categories, badge counts, recently used, drag & drop.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QPushButton, QFrame, QLineEdit,
    QApplication, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QPoint, QEvent
from PySide6.QtGui import QFont, QDrag, QPixmap, QPainter, QColor, QIcon, QMouseEvent, QFontMetrics

from backend.core.action_registry import ActionRegistry


# ==================== ICON MAP ====================
ACTION_ICONS = {
    # Navigation
    "click": "🖱️",
    "wait": "⏳",
    "navigate": "🧭",
    # Input
    "input_text": "✏️",
    "input_date": "📅",
    "select": "📋",
    "select2": "📋",
    "select_dropdown": "📑",
    "radio_select": "🔘",
    "upload_file": "📤",
    "http_submit": "🌐",
    "batch_input": "🧹",
    "otp_challenge": "🔢",
    "login_otp": "🔑",
    # Logic
    "loop": "🔄",
    "if_else": "🔀",
    "parallel_group": "⚡",
    # Detection
    "ocr": "👁️",
    "image_detect": "🖼️",
    # Data
    "extract": "📊",
    "transform": "🔧",
}

# Category colors
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
    "Input": ["input_text", "input_date", "select", "select2", "select_dropdown", "radio_select", "upload_file", "http_submit", "batch_input", "otp_challenge"],
    "Logic": ["loop", "if_else", "parallel_group", "login_otp"],
    "Detection": ["ocr", "image_detect"],
    "Data": ["extract", "transform"],
}


class ActionItem(QFrame):
    """
    Compact list-style action item.
    Menampilkan icon + nama action dalam satu baris ringkas.
    """

    action_activated = Signal(str, dict, bool)  # action_name, params, is_double_click

    def __init__(self, action_name: str, description: str, category: str = "", parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self._description = description
        self._category = category
        self._badge_count = 0
        self._use_count = 0
        self._drag_start_pos = None
        self._drag_started = False

        self.setFrameShape(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self.setAcceptDrops(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Color dot (kecil)
        self.color_dot = QLabel("●")
        self.color_dot.setFixedWidth(12)
        self.color_dot.setStyleSheet(f"""
            color: {CATEGORY_COLORS.get(category, '#6b7280')};
            font-size: 8px;
        """)
        layout.addWidget(self.color_dot)

        # Icon
        icon_char = ACTION_ICONS.get(action_name, "🔹")
        self.icon_label = QLabel(icon_char)
        self.icon_label.setFixedWidth(20)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.icon_label)

        # Action name
        self.name_label = QLabel(action_name.replace("_", " "))
        name_font = QFont()
        name_font.setPointSize(9)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #1f2937;")
        self.name_label.setToolTip(description)  # Full description on hover
        layout.addWidget(self.name_label, 1)

        # Badge count (hidden by default)
        self.badge_label = QLabel("")
        self.badge_label.setFixedWidth(18)
        self.badge_label.setFixedHeight(14)
        self.badge_label.setAlignment(Qt.AlignCenter)
        self.badge_label.setStyleSheet("""
            QLabel {
                background: #3b82f6; color: white; border-radius: 7px;
                font-size: 7px; font-weight: bold;
            }
        """)
        self.badge_label.hide()
        layout.addWidget(self.badge_label)

        # Hover highlight
        self.setStyleSheet("""
            ActionItem {
                background: transparent;
                border-radius: 4px;
            }
            ActionItem:hover {
                background: #e5e7eb;
            }
        """)

    def enterEvent(self, event):
        """Highlight on hover."""
        self.setStyleSheet("""
            ActionItem {
                background: #e5e7eb;
                border-radius: 4px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Remove highlight on leave."""
        self.setStyleSheet("""
            ActionItem {
                background: transparent;
                border-radius: 4px;
            }
        """)
        super().leaveEvent(event)

    def set_badge_count(self, count: int):
        self._badge_count = count
        if count > 0:
            self.badge_label.setText(str(count))
            self.badge_label.show()
        else:
            self.badge_label.hide()

    def increment_use_count(self):
        self._use_count += 1

    def get_use_count(self) -> int:
        return self._use_count

    # ==================== DRAG & DROP ====================

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self._drag_started = False
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            self._drag_start_pos is not None
            and (event.buttons() & Qt.LeftButton)
            and not self._drag_started
        ):
            current_pos = event.position().toPoint()
            distance = (current_pos - self._drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self._drag_started = True
                self._start_drag(event)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        self._drag_started = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.action_activated.emit(self.action_name, {}, True)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def _start_drag(self, event: QMouseEvent):
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.action_name)
        drag.setMimeData(mime_data)

        # Compact drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)
        self.render(painter, QPoint(0, 0))
        painter.end()

        hot_spot = event.position().toPoint()
        drag.setHotSpot(hot_spot)
        drag.setPixmap(pixmap)
        drag.exec(Qt.CopyAction)

    def get_description(self) -> str:
        return self._description


class CategoryGroup(QWidget):
    """Collapsible category group with compact action items."""

    def __init__(self, category_name: str, color: str, parent=None):
        super().__init__(parent)
        self._category_name = category_name
        self._is_collapsed = False
        self._action_items: list[ActionItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Category header
        self.header = QPushButton()
        self.header.setFlat(True)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setFixedHeight(26)
        self.header.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 2px 6px;
                color: {color}; font-weight: bold; font-size: 9px;
                background: transparent; border: none;
            }}
            QPushButton:hover {{
                background: #f3f4f6;
                border-radius: 3px;
            }}
        """)
        self.header.setText(f"▼  {category_name}")
        self.header.clicked.connect(self._toggle_collapse)
        layout.addWidget(self.header)

        # Container for action items
        self.items_container = QFrame()
        self.items_container.setFrameShape(QFrame.NoFrame)
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(4, 0, 4, 0)
        self.items_layout.setSpacing(1)
        layout.addWidget(self.items_container)

        # Minimal spacer
        self.spacer = QFrame()
        self.spacer.setFixedHeight(2)
        layout.addWidget(self.spacer)

    def add_action(self, item: ActionItem):
        self._action_items.append(item)
        self.items_layout.addWidget(item)

    def get_action_items(self) -> list[ActionItem]:
        return self._action_items

    def _toggle_collapse(self):
        self._is_collapsed = not self._is_collapsed
        self.items_container.setVisible(not self._is_collapsed)
        self.header.setText(
            f"▶  {self._category_name}" if self._is_collapsed else f"▼  {self._category_name}"
        )

    def set_visible_by_filter(self, search_text: str):
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

        has_visible = visible_count > 0
        self.header.setVisible(has_visible)
        self.spacer.setVisible(has_visible)

        if search_text and has_visible and self._is_collapsed:
            self._toggle_collapse()

    def set_badge_counts(self, action_counts: dict[str, int]):
        for item in self._action_items:
            count = action_counts.get(item.action_name, 0)
            item.set_badge_count(count)


class ActionPalette(QWidget):
    """Sidebar compact dengan daftar action berbasis icon list."""

    action_dragged = Signal(str, dict)
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
        self.setMinimumWidth(180)
        self.setMaximumWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ==================== TITLE BAR ====================
        title_bar = QHBoxLayout()
        title_bar.setSpacing(4)

        title = QLabel("Actions")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title.setFont(title_font)
        title.setStyleSheet("color: #1a1a2e;")
        title_bar.addWidget(title)

        self.action_count_label = QLabel("0")
        self.action_count_label.setStyleSheet("""
            color: #9ca3af; font-size: 8px;
            background: #f3f4f6; padding: 1px 6px; border-radius: 6px;
        """)
        title_bar.addWidget(self.action_count_label)

        title_bar.addStretch()

        # Collapse all button
        collapse_btn = QPushButton("⊟")
        collapse_btn.setFixedSize(18, 18)
        collapse_btn.setToolTip("Collapse all categories")
        collapse_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #9ca3af; font-size: 10px;
            }
            QPushButton:hover { color: #374151; }
        """)
        collapse_btn.clicked.connect(self._collapse_all)
        title_bar.addWidget(collapse_btn)

        layout.addLayout(title_bar)

        # ==================== SEARCH BAR ====================
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
            }
            QFrame:focus-within {
                border-color: #3b82f6;
                background: #ffffff;
            }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(6, 2, 6, 2)
        search_layout.setSpacing(4)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 10px;")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none; background: transparent;
                font-size: 10px; color: #374151;
            }
            QLineEdit::placeholder { color: #9ca3af; }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)

        self.search_clear_btn = QPushButton("✕")
        self.search_clear_btn.setFixedSize(14, 14)
        self.search_clear_btn.setStyleSheet("""
            QPushButton {
                background: #d1d5db; color: white; border: none;
                border-radius: 7px; font-size: 7px;
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
                width: 4px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db; border-radius: 2px;
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
        layout.addWidget(scroll, 1)

        # ==================== BOTTOM BAR ====================
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(4)

        # Reorder buttons (compact)
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setFixedSize(26, 22)
        self.move_up_btn.setToolTip("Move selected node up")
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6; color: #374151;
                border-radius: 4px; font-weight: bold; font-size: 11px;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:disabled { background: #f9fafb; color: #d1d5db; border-color: #e5e7eb; }
        """)
        self.move_up_btn.clicked.connect(lambda: self.node_moved_up.emit())
        bottom_bar.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setFixedSize(26, 22)
        self.move_down_btn.setToolTip("Move selected node down")
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6; color: #374151;
                border-radius: 4px; font-weight: bold; font-size: 11px;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:disabled { background: #f9fafb; color: #d1d5db; border-color: #e5e7eb; }
        """)
        self.move_down_btn.clicked.connect(lambda: self.node_moved_down.emit())
        bottom_bar.addWidget(self.move_down_btn)

        bottom_bar.addStretch()

        # Recently used label (compact)
        self.recent_label = QLabel("")
        self.recent_label.setStyleSheet("color: #9ca3af; font-size: 8px;")
        bottom_bar.addWidget(self.recent_label)

        layout.addLayout(bottom_bar)

        # ==================== POPULATE ====================
        self._create_action_groups()
        self._update_action_count()

    # ==================== SEARCH ====================

    def _on_search_changed(self, text: str):
        for group in self._category_groups.values():
            group.set_visible_by_filter(text)

    def _clear_search(self):
        self.search_input.clear()
        self.search_input.setFocus()

    def _collapse_all(self):
        """Collapse semua kategori."""
        for group in self._category_groups.values():
            if not group._is_collapsed:
                group._toggle_collapse()

    # ==================== CATEGORY SETUP ====================

    def _create_action_groups(self):
        # Recently used section
        self.recent_group = CategoryGroup("Recently Used", "#ef4444")
        self.actions_layout.addWidget(self.recent_group)
        self._category_groups["Recently Used"] = self.recent_group

        available_categories = {}
        for category, action_names in CATEGORY_ACTIONS.items():
            valid_actions = [name for name in action_names if self.action_registry.get(name)]
            if valid_actions:
                available_categories[category] = valid_actions

        for category, action_names in available_categories.items():
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

        # Spacer
        self.actions_layout.addStretch()

    def _on_action_activated(self, action_name: str, params: dict, is_double_click: bool):
        self._track_recently_used(action_name)
        if action_name in self._all_action_items:
            self._all_action_items[action_name].increment_use_count()
        self.action_dragged.emit(action_name, params)

    # ==================== RECENTLY USED ====================

    def _track_recently_used(self, action_name: str):
        if action_name in self._recently_used:
            self._recently_used.remove(action_name)
        self._recently_used.insert(0, action_name)
        if len(self._recently_used) > self._max_recent:
            self._recently_used = self._recently_used[:self._max_recent]
        self._update_recently_used()

    def _update_recently_used(self):
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

            recent_text = " | ".join(self._recently_used[:3])
            self.recent_label.setText(f"Recent: {recent_text}")
        else:
            self.recent_group.setVisible(False)
            self.recent_label.setText("")

    # ==================== BADGE COUNTS ====================

    def update_action_counts(self, action_counts: dict[str, int]):
        for group in self._category_groups.values():
            group.set_badge_counts(action_counts)
        self._update_action_count()

    def _update_action_count(self):
        total = len(self._all_action_items)
        self.action_count_label.setText(str(total))

    # ==================== PUBLIC API ====================

    def toggleViewAction(self):
        from PySide6.QtGui import QAction
        action = QAction("Action Palette", self)
        action.setCheckable(True)
        action.setChecked(self.isVisible())
        action.triggered.connect(self.setVisible)
        return action

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()