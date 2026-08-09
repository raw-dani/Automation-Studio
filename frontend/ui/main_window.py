"""
Main Window - Jendela utama aplikasi Automation Studio.
Menggunakan layout splitter dengan panel-panel yang terintegrasi.
"""

import sys
import os
import json
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QLabel, QApplication, QTabWidget, QDialog,
    QTextBrowser, QVBoxLayout as QVBoxLayoutDlg,
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QSettings
from PySide6.QtGui import QAction, QIcon, QFont, QKeySequence

from frontend.ui.workflow_editor import WorkflowEditor
from frontend.ui.action_palette import ActionPalette
from frontend.ui.properties_panel import PropertiesPanel
from frontend.ui.data_source_manager import DataSourceManager
from frontend.ui.execution_panel import ExecutionPanel
from frontend.ui.monitoring_panel import MonitoringPanel

from backend.core.workflow_parser import WorkflowParser, Workflow
from backend.core.action_registry import ActionRegistry
from backend.core.engine import ExecutionEngine
from backend.actions.click_action import ClickAction
from backend.actions.input_text_action import InputTextAction
from backend.actions.input_date_action import InputDateAction
from backend.actions.wait_action import WaitAction
from backend.actions.select_dropdown_action import SelectDropdownAction
from backend.actions.upload_file_action import UploadFileAction
from backend.actions.loop_action import LoopAction
from backend.actions.if_else_action import IfElseAction
from backend.actions.navigate_action import NavigateAction
from backend.actions.select_action import SelectAction
from backend.actions.select2_action import Select2Action
from backend.actions.parallel_group_action import ParallelGroupAction
from backend.actions.radio_select_action import RadioSelectAction
from backend.actions.http_submit_action import HttpSubmitAction
from backend.license.license_manager import LicenseManager
from backend.license.usage_tracker import UsageTracker


RECENT_FILES_MAX = 5
SETTINGS_ORG = "AutomationStudio"
SETTINGS_APP = "MainWindow"


class ShortcutsDialog(QDialog):
    """Dialog untuk menampilkan daftar shortcut keyboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayoutDlg(self)

        browser = QTextBrowser()
        browser.setStyleSheet("""
            QTextBrowser {
                background: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 4px;
                font-family: Consolas, monospace; font-size: 11px;
            }
        """)
        browser.setHtml("""
        <h2 style='color: #4CAF50;'>Keyboard Shortcuts</h2>
        <hr style='border-color: #333;'>
        <table width='100%' cellpadding='6'>
        <tr><td><b>Ctrl+N</b></td><td>New Workflow</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open Workflow</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Workflow</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>
        <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
        <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
        <tr><td><b>Delete</b></td><td>Delete Selected Node</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit</td></tr>
        <tr><td><b>F5</b></td><td>Run Workflow</td></tr>
        <tr><td><b>Shift+F5</b></td><td>Stop Workflow</td></tr>
        <tr><td><b>F6</b></td><td>Pause/Resume Workflow</td></tr>
        <tr><td><b>F7</b></td><td>Validate Workflow</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Duplicate Selected Node</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select All Nodes</td></tr>
        <tr><td><b>Ctrl+W</b></td><td>Close Workflow</td></tr>
        <tr><td><b>F1</b></td><td>Help / Shortcuts</td></tr>
        </table>
        """)
        layout.addWidget(browser)

        from PySide6.QtWidgets import QDialogButtonBox
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class MainWindow(QMainWindow):
    """Jendela utama Automation Studio."""

    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.current_workflow: Optional[Workflow] = None
        self.current_file: Optional[str] = None
        self.current_data_source: dict = {}
        self._modified = False  # Track unsaved changes
        self._recent_files = []  # List of recent file paths

        # Setup backend
        self.action_registry = self._create_action_registry()
        self.engine = ExecutionEngine(self.action_registry, self.config)
        self.parser = WorkflowParser()

        # Setup license system
        license_config = self.config.get("license", {})
        self.license_manager = LicenseManager(license_config)
        usage_config = license_config.get("free_mode", {})
        self.usage_tracker = UsageTracker(usage_config.get("daily_data_limit", 10))

        # Load settings
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._load_settings()

        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._init_shortcuts()

        # Tampilkan empty state di awal
        self.workflow_editor.clear()

        # Connect signals
        self._connect_signals()

        # Restore window geometry
        self._restore_geometry()

        # Auto-verify license on startup
        self.license_manager.auto_verify_on_startup()
        self._update_license_status()

    def _create_action_registry(self) -> ActionRegistry:
        """Buat dan daftarkan semua action."""
        registry = ActionRegistry()
        registry.register(ClickAction())
        registry.register(InputTextAction())
        registry.register(InputDateAction())
        registry.register(WaitAction())
        registry.register(SelectDropdownAction())
        registry.register(SelectAction())
        registry.register(Select2Action())
        registry.register(RadioSelectAction())
        registry.register(UploadFileAction())
        registry.register(HttpSubmitAction())
        registry.register(LoopAction())
        registry.register(IfElseAction())
        registry.register(NavigateAction())
        registry.register(ParallelGroupAction())
        return registry

    def _init_ui(self):
        """Inisialisasi UI layout."""
        self.setWindowTitle("Automation Studio")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main horizontal layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter utama
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left panel: Action Palette
        self.action_palette = ActionPalette(self.action_registry)
        self.action_palette.setMinimumWidth(200)
        self.action_palette.setMaximumWidth(300)

        # Center: Workflow Editor
        self.workflow_editor = WorkflowEditor()

        # Right panel: tabbed (Properties | Data Source | Execution | Monitoring)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.right_tabs = QTabWidget()
        self.right_tabs.setDocumentMode(True)
        self.right_tabs.setTabPosition(QTabWidget.North)

        self.properties_panel = PropertiesPanel()
        self.data_source_manager = DataSourceManager()
        self.execution_panel = ExecutionPanel(self.engine)
        self.monitoring_panel = MonitoringPanel()

        self.right_tabs.addTab(self.properties_panel, "Properties")
        self.right_tabs.addTab(self.data_source_manager, "Data Source")
        self.right_tabs.addTab(self.execution_panel, "Execution")
        self.right_tabs.addTab(self.monitoring_panel, "Monitoring")
        self.right_tabs.setCurrentWidget(self.properties_panel)

        right_layout.addWidget(self.right_tabs)

        # Add to main splitter
        self.main_splitter.addWidget(self.action_palette)
        self.main_splitter.addWidget(self.workflow_editor)
        self.main_splitter.addWidget(right_panel)

        # Set default sizes
        self.main_splitter.setSizes([220, 700, 420])

        main_layout.addWidget(self.main_splitter)

    def _init_menu(self):
        """Inisialisasi menu bar."""
        menubar = self.menuBar()

        # ==================== FILE MENU ====================
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Workflow", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_workflow)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Workflow...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_workflow)
        file_menu.addAction(open_action)

        # Recent files submenu
        self.recent_menu = QMenu("Open &Recent", self)
        self._update_recent_menu()
        file_menu.addMenu(self.recent_menu)

        file_menu.addSeparator()

        close_action = QAction("&Close Workflow", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_workflow)
        file_menu.addAction(close_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_workflow)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_workflow_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        export_json_action = QAction("Export as &JSON...", self)
        export_json_action.triggered.connect(self.export_workflow_json)
        export_menu.addAction(export_json_action)
        export_txt_action = QAction("Export as &Text...", self)
        export_txt_action.triggered.connect(self.export_workflow_txt)
        export_menu.addAction(export_txt_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ==================== EDIT MENU ====================
        edit_menu = menubar.addMenu("&Edit")

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self.workflow_editor.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.setEnabled(False)
        self.redo_action.triggered.connect(self.workflow_editor.redo)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("&Delete Selected", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.workflow_editor.delete_selected)
        edit_menu.addAction(delete_action)

        duplicate_action = QAction("&Duplicate Node", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self._duplicate_selected_node)
        edit_menu.addAction(duplicate_action)

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.workflow_editor.select_all)
        edit_menu.addAction(select_all_action)

        # ==================== LICENSE MENU ====================
        license_menu = menubar.addMenu("&License")

        license_status_action = QAction("License Status", self)
        license_status_action.triggered.connect(self._show_license_status)
        license_menu.addAction(license_status_action)

        license_activate_action = QAction("Activate License", self)
        license_activate_action.triggered.connect(self._activate_license)
        license_menu.addAction(license_activate_action)

        license_deactivate_action = QAction("Deactivate License", self)
        license_deactivate_action.triggered.connect(self._deactivate_license)
        license_menu.addAction(license_deactivate_action)

        # ==================== VIEW MENU ====================
        view_menu = menubar.addMenu("&View")

        view_menu.addAction(self.action_palette.toggleViewAction())

        # Toggle properties panel
        self.properties_toggle_action = QAction("Properties Panel", self)
        self.properties_toggle_action.setCheckable(True)
        self.properties_toggle_action.setChecked(True)
        self.properties_toggle_action.triggered.connect(
            lambda checked: self.properties_panel.setVisible(checked)
        )
        view_menu.addAction(self.properties_toggle_action)

        # Toggle bottom tabs
        self.bottom_tabs_toggle_action = QAction("Right Panel Tabs", self)
        self.bottom_tabs_toggle_action.setCheckable(True)
        self.bottom_tabs_toggle_action.setChecked(True)
        self.bottom_tabs_toggle_action.triggered.connect(
            lambda checked: self.right_tabs.setVisible(checked)
        )
        view_menu.addAction(self.bottom_tabs_toggle_action)

        view_menu.addSeparator()

        self.monitoring_toggle_action = QAction("Monitoring Panel", self)
        self.monitoring_toggle_action.setCheckable(True)
        self.monitoring_toggle_action.setChecked(True)
        self.monitoring_toggle_action.triggered.connect(self._toggle_monitoring_tab)
        view_menu.addAction(self.monitoring_toggle_action)

        self.right_tabs.currentChanged.connect(self._update_monitoring_toggle)

        # ==================== RUN MENU ====================
        run_menu = menubar.addMenu("&Run")

        run_action = QAction("&Run Workflow", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.execution_panel.run_workflow)
        run_menu.addAction(run_action)

        stop_action = QAction("&Stop Workflow", self)
        stop_action.setShortcut("Shift+F5")
        stop_action.triggered.connect(self.execution_panel.stop_workflow)
        run_menu.addAction(stop_action)

        pause_action = QAction("&Pause/Resume", self)
        pause_action.setShortcut("F6")
        pause_action.triggered.connect(self.execution_panel.toggle_pause)
        run_menu.addAction(pause_action)

        run_menu.addSeparator()

        validate_action = QAction("&Validate Workflow", self)
        validate_action.setShortcut("F7")
        validate_action.triggered.connect(self.validate_workflow)
        run_menu.addAction(validate_action)

        # ==================== HELP MENU ====================
        help_menu = menubar.addMenu("&Help")

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        doc_action = QAction("&Documentation", self)
        doc_action.triggered.connect(self.show_documentation)
        help_menu.addAction(doc_action)

        changelog_action = QAction("&Change Log", self)
        changelog_action.triggered.connect(self.show_changelog)
        help_menu.addAction(changelog_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        """Inisialisasi toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar { spacing: 4px; padding: 2px; }
            QToolButton { padding: 4px 8px; border-radius: 4px; }
            QToolButton:hover { background: #e3f2fd; }
        """)
        self.addToolBar(toolbar)

        # Helper to create styled toolbar buttons
        def make_btn(text, tip, icon_char, callback):
            btn = QAction(text, self)
            btn.setToolTip(tip)
            btn.triggered.connect(callback)
            return btn

        # File operations
        toolbar.addAction(make_btn("📄", "New Workflow (Ctrl+N)", "N", self.new_workflow))
        toolbar.addAction(make_btn("📂", "Open Workflow (Ctrl+O)", "O", self.open_workflow))
        toolbar.addAction(make_btn("💾", "Save Workflow (Ctrl+S)", "S", self.save_workflow))

        toolbar.addSeparator()

        # Edit
        toolbar.addAction(make_btn("↩", "Undo (Ctrl+Z)", "Z", self.workflow_editor.undo))
        toolbar.addAction(make_btn("↪", "Redo (Ctrl+Y)", "Y", self.workflow_editor.redo))

        toolbar.addSeparator()

        # Validate
        toolbar.addAction(make_btn("✓", "Validate Workflow (F7)", "V", self.validate_workflow))

        toolbar.addSeparator()

        # Run controls
        toolbar.addAction(make_btn("▶", "Run Workflow (F5)", "R", self.execution_panel.run_workflow))
        toolbar.addAction(make_btn("⏸", "Pause/Resume (F6)", "P", self.execution_panel.toggle_pause))
        toolbar.addAction(make_btn("⏹", "Stop Workflow (Shift+F5)", "S", self.execution_panel.stop_workflow))

        toolbar.addSeparator()

        # Zoom controls removed for tree view

    def _init_statusbar(self):
        """Inisialisasi status bar dengan informasi tambahan."""
        # Main status label (left)
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label, 1)

        # Step count (center)
        self.step_count_label = QLabel("Steps: 0")
        self.step_count_label.setStyleSheet("color: #2196F3; font-weight: bold; padding: 0 8px;")
        self.step_count_label.setToolTip("Total step di level atas (belum termasuk nested)")
        self.statusBar().addPermanentWidget(self.step_count_label)

        # Data source indicator
        self.data_source_label = QLabel("")
        self.data_source_label.setStyleSheet("color: #9C27B0; font-weight: bold; padding: 0 8px;")
        self.data_source_label.setToolTip("Data source yang digunakan workflow ini")
        self.statusBar().addPermanentWidget(self.data_source_label)

        # Modified indicator
        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 0 8px;")
        self.statusBar().addPermanentWidget(self.modified_label)

        # License status indicator
        self.license_label = QLabel("🔓 Free")
        self.license_label.setStyleSheet("color: #ffc107; font-weight: bold; padding: 0 8px;")
        self.license_label.setToolTip("License status")
        self.statusBar().addPermanentWidget(self.license_label)

        # Workflow info (right)
        self.workflow_info_label = QLabel("No workflow loaded")
        self.workflow_info_label.setStyleSheet("color: #666; padding: 0 8px;")
        self.statusBar().addPermanentWidget(self.workflow_info_label)

    def _init_shortcuts(self):
        """Inisialisasi shortcut keyboard tambahan."""
        # Some shortcuts are already set via QAction.setShortcut()
        # Additional shortcuts can be added here if needed
        pass

    def _connect_signals(self):
        """Connect signals antar panel."""
        # Action palette -> Workflow editor
        self.action_palette.action_dragged.connect(
            self.workflow_editor.add_action_node
        )
        self.action_palette.node_moved_up.connect(
            self._move_selected_node_up
        )
        self.action_palette.node_moved_down.connect(
            self._move_selected_node_down
        )

        # Workflow editor -> Properties panel
        self.workflow_editor.node_selected.connect(
            self._on_node_selected_for_properties
        )
        self.workflow_editor.node_deselected.connect(
            self.properties_panel.clear
        )

        # Properties panel -> Workflow editor
        self.properties_panel.params_changed.connect(
            self.workflow_editor.update_node_params
        )
        self.properties_panel.type_changed.connect(
            self.workflow_editor.change_node_type
        )

        # Execution panel -> Engine
        self.execution_panel.log_received.connect(
            self.monitoring_panel.add_log
        )
        self.execution_panel.progress_received.connect(
            self.monitoring_panel.update_progress
        )
        self.execution_panel.save_requested.connect(
            self._on_save_properties_requested
        )
        self.execution_panel.before_run.connect(
            self._reload_current_workflow
        )

        # License system integration
        self.execution_panel.set_license_manager(self.license_manager, self.usage_tracker)
        self.engine.set_license_manager(self.license_manager, self.usage_tracker)

        # Properties panel -> Save
        self.properties_panel.save_requested.connect(
            self._on_properties_save_requested
        )

        # Engine -> Monitoring
        self.engine.set_log_callback(
            lambda log: self.monitoring_panel.add_log(log)
        )
        self.engine.set_progress_callback(
            lambda prog: self.monitoring_panel.update_progress(prog)
        )

        # Connect workflow changes to execution panel
        self.workflow_editor.nodes_changed.connect(
            self._on_workflow_changed
        )

        # Data source manager -> workflow
        self.data_source_manager.data_source_changed.connect(
            self._on_data_source_changed
        )

        # Undo/Redo state tracking
        self.workflow_editor.undo_available.connect(self.undo_action.setEnabled)
        self.workflow_editor.redo_available.connect(self.redo_action.setEnabled)

        # Empty state actions
        self.workflow_editor.new_workflow_requested.connect(self.new_workflow)
        self.workflow_editor.open_workflow_requested.connect(self.open_workflow)

    # ==================== WORKFLOW METHODS ====================

    def _mark_modified(self):
        """Tandai workflow sebagai modified (belum disimpan)."""
        self._modified = True
        self.modified_label.setText("● Modified")
        self.modified_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 0 8px;")
        self._update_title()

    def _mark_saved(self):
        """Tandai workflow sebagai sudah disimpan."""
        self._modified = False
        self.modified_label.setText("")
        self._update_title()

    def _update_title(self):
        """Update window title berdasarkan status."""
        name = self.current_workflow.name if self.current_workflow else "New Workflow"
        modified = " *" if self._modified else ""
        self.setWindowTitle(f"Automation Studio - {name}{modified}")

    def _update_license_status(self):
        """Update license status di status bar."""
        if self.license_manager.is_licensed():
            self.license_label.setText("🔒 Licensed")
            self.license_label.setStyleSheet("color: #28a745; font-weight: bold; padding: 0 8px;")
            self.license_label.setToolTip("Lisensi aktif - tanpa batasan")
        else:
            remaining = self.usage_tracker.get_remaining_quota()
            self.license_label.setText(f"🔓 Free ({remaining}/10)")
            self.license_label.setStyleSheet("color: #ffc107; font-weight: bold; padding: 0 8px;")
            self.license_label.setToolTip(f"Mode Free: {remaining} data tersisa hari ini")

    def _on_workflow_changed(self):
        """Sync editor state ke execution panel."""
        try:
            data = self.workflow_editor.to_workflow_data()
            if data:
                data["data_source"] = self.current_data_source
                if data.get("steps"):
                    workflow = self.parser.parse(data)
                    self.execution_panel.set_workflow(workflow)
                    self.current_workflow = workflow
                    self._mark_modified()

                    # Update step count
                    step_count = len(workflow.steps)
                    self.step_count_label.setText(f"Steps: {step_count}")
                else:
                    # Workflow kosong - pertahankan current_workflow yang ada
                    # agar action masih bisa ditambahkan ke editor.
                    if self.current_workflow:
                        self.current_workflow.steps = []
                        self.current_workflow.data_source = self.current_data_source
                        self.execution_panel.set_workflow(self.current_workflow)
                    else:
                        self.execution_panel.set_workflow(None)
                    self.step_count_label.setText("Steps: 0")
        except Exception:
            pass

    def _on_data_source_changed(self, config: dict):
        """Handle data source config change."""
        self.current_data_source = config
        if self.current_workflow:
            self.current_workflow.data_source = config
            self._mark_modified()

        # Update data source indicator di status bar
        ds_type = config.get("type", "none") if config else "none"
        if ds_type and ds_type != "none":
            self.data_source_label.setText(f"📊 {ds_type.upper()}")
        else:
            self.data_source_label.setText("")

    def _on_node_selected_for_properties(self, step_id: str, params: dict, action_type: str = ""):
        """Handle node selection untuk properties panel."""
        self.properties_panel.show_action_properties(step_id, params, action_type)

    def _move_selected_node_up(self):
        """Move selected node up in execution order."""
        selected_items = self.workflow_editor.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            step_id = item.data(0, Qt.UserRole)
            if step_id:
                self.workflow_editor.move_node_up(step_id)

    def _move_selected_node_down(self):
        """Move selected node down in execution order."""
        selected_items = self.workflow_editor.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            step_id = item.data(0, Qt.UserRole)
            if step_id:
                self.workflow_editor.move_node_down(step_id)

    def _duplicate_selected_node(self):
        """Duplicate node yang dipilih."""
        selected_items = self.workflow_editor.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            step_id = item.data(0, Qt.UserRole)
            action_type = item.data(1, Qt.UserRole)
            if step_id and action_type:
                params = {}
                if self.workflow_editor.workflow:
                    step = self.workflow_editor._find_step(self.workflow_editor.workflow.steps, step_id)
                    if step:
                        params = dict(step.params)
                self.workflow_editor.add_action_node(
                    action_type,
                    params,
                    label=f"{params.get('label', action_type)} (copy)"
                )

    # ==================== RECENT FILES ====================

    def _add_recent_file(self, filepath: str):
        """Tambah file ke daftar recent."""
        if filepath in self._recent_files:
            self._recent_files.remove(filepath)
        self._recent_files.insert(0, filepath)
        if len(self._recent_files) > RECENT_FILES_MAX:
            self._recent_files = self._recent_files[:RECENT_FILES_MAX]
        self._update_recent_menu()
        self._save_settings()

    def _update_recent_menu(self):
        """Update menu recent files."""
        self.recent_menu.clear()
        if not self._recent_files:
            empty_action = self.recent_menu.addAction("(No recent files)")
            empty_action.setEnabled(False)
            return

        for i, filepath in enumerate(self._recent_files):
            if os.path.exists(filepath):
                name = os.path.basename(filepath)
                action = self.recent_menu.addAction(f"&{i+1} {name}")
                action.setToolTip(filepath)
                action.triggered.connect(lambda checked, fp=filepath: self._open_recent_file(fp))
            else:
                # File no longer exists, remove from list
                self._recent_files.remove(filepath)

        self.recent_menu.addSeparator()
        clear_action = self.recent_menu.addAction("Clear Recent Files")
        clear_action.triggered.connect(self._clear_recent_files)

    def _open_recent_file(self, filepath: str):
        """Buka file dari recent list."""
        if os.path.exists(filepath):
            self._load_workflow_file(filepath)
        else:
            QMessageBox.warning(self, "File Not Found",
                f"File tidak ditemukan:\n{filepath}\n\nFile akan dihapus dari recent list.")
            self._recent_files.remove(filepath)
            self._update_recent_menu()

    def _clear_recent_files(self):
        """Hapus semua recent files."""
        self._recent_files.clear()
        self._update_recent_menu()
        self._save_settings()

    # ==================== SETTINGS PERSISTENCE ====================

    def _load_settings(self):
        """Load recent files from settings."""
        recent = self._settings.value("recent_files", [])
        if isinstance(recent, list):
            self._recent_files = [f for f in recent if os.path.exists(f)]

    def _save_settings(self):
        """Save settings."""
        self._settings.setValue("recent_files", self._recent_files)

    def _restore_geometry(self):
        """Restore window geometry and state."""
        geometry = self._settings.value("geometry")
        state = self._settings.value("windowState")
        splitter_sizes = self._settings.value("splitterSizes")

        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        if splitter_sizes and isinstance(splitter_sizes, list):
            self.main_splitter.setSizes([int(s) for s in splitter_sizes])

    def _save_geometry(self):
        """Save window geometry and state."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        self._settings.setValue("splitterSizes", self.main_splitter.sizes())

    # ==================== FILE OPERATIONS ====================

    def _on_properties_save_requested(self):
        """Handle save request from properties panel."""
        if not self.current_workflow or not self.current_file:
            self.status_label.setText("No workflow to save")
            QMessageBox.warning(self, "No Workflow", "No workflow loaded or file path set.\nPlease create or open a workflow first.")
            return

        try:
            editor_data = self.workflow_editor.to_workflow_data()
            if not editor_data.get("steps"):
                self.status_label.setText("Nothing to save")
                return

            # Preserve workflow metadata from current_workflow
            editor_data["id"] = self.current_workflow.id
            editor_data["name"] = self.current_workflow.name
            editor_data["version"] = self.current_workflow.version
            editor_data["url"] = self.current_workflow.url
            editor_data["data_source"] = self.current_workflow.data_source
            editor_data["monitoring"] = self.current_workflow.monitoring
            editor_data["created_at"] = self.current_workflow.created_at

            workflow = self.parser.parse(editor_data)
            self.parser.save(workflow, self.current_file)

            self.current_workflow = workflow
            self._mark_saved()
            self.status_label.setText(f"Saved: {self.current_file}")
            QMessageBox.information(self, "Success", "Workflow saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{str(e)}")

    def _reload_current_workflow(self):
        """Reload workflow from current file to get latest changes."""
        if not self.current_file:
            return

        try:
            workflow = self.parser.load(self.current_file)
            self.current_workflow = workflow
            self.current_data_source = workflow.data_source or {}
            self.execution_panel.set_workflow(workflow)
            self.data_source_manager.set_config(self.current_data_source)
            self._mark_saved()
        except Exception:
            pass

    def _on_save_properties_requested(self, url: str):
        """Handle save properties request from execution panel."""
        if not self.current_workflow:
            self.status_label.setText("No workflow to save")
            self.execution_panel.show_save_feedback(False, "No workflow to save")
            return

        self.current_workflow.url = url

        if self.current_file:
            try:
                editor_data = self.workflow_editor.to_workflow_data()
                if editor_data and editor_data.get("steps"):
                    editor_data["data_source"] = self.current_data_source
                    parsed = self.parser.parse(editor_data)
                    self.current_workflow.steps = parsed.steps
                    self.current_workflow.name = parsed.name
                    self.current_workflow.id = parsed.id
                    self.current_workflow.data_source = parsed.data_source

                self.parser.save(self.current_workflow, self.current_file)
                self._mark_saved()
                self.status_label.setText(f"Saved: {self.current_file}")
                self.execution_panel.show_save_feedback(True, "Saved successfully!")
            except Exception as e:
                self.execution_panel.show_save_feedback(False, f"Save failed: {str(e)}")
        else:
            self.save_workflow_as()

    def _load_workflow_file(self, file_path: str):
        """Internal method to load a workflow file."""
        try:
            workflow = self.parser.load(file_path)
            self.current_workflow = workflow
            self.current_file = file_path
            self.current_data_source = workflow.data_source or {}

            self.workflow_editor.load_workflow(workflow)
            self.execution_panel.set_workflow(workflow)
            self.data_source_manager.set_config(self.current_data_source)
            self._mark_saved()

            # Update title dengan nama file
            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"Automation Studio - {workflow.name} ({file_name})")
            self.workflow_info_label.setText(f"{workflow.name} (v{workflow.version})")
            self.step_count_label.setText(f"Steps: {len(workflow.steps)}")
            self.status_label.setText(f"Loaded: {file_path}")

            # Update data source indicator
            ds_type = self.current_data_source.get("type", "none") if self.current_data_source else "none"
            if ds_type and ds_type != "none":
                self.data_source_label.setText(f"📊 {ds_type.upper()}")
            else:
                self.data_source_label.setText("")

            self._add_recent_file(file_path)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membuka workflow:\n{str(e)}")

    def new_workflow(self):
        """Buat workflow baru."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Create new workflow anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Buat Workflow kosong yang valid (bukan None) agar action bisa ditambahkan
        now = datetime.now().isoformat()
        new_workflow = Workflow(
            id="workflow_new",
            name="New Workflow",
            version="1.0",
            url="",
            data_source={},
            steps=[],  # Parser memvalidasi minimal 1 step, jadi jangan pakai parse() di sini
            monitoring={
                "screenshot_on_error": True,
                "screenshot_on_step": False,
                "log_level": "INFO"
            },
            created_at=now,
            updated_at=now,
        )

        self.current_workflow = new_workflow
        self.current_file = None
        self.current_data_source = {}

        # Load workflow kosong ke editor (bukan clear() agar workflow tidak None)
        self.workflow_editor.load_workflow(new_workflow)
        self.execution_panel.set_workflow(new_workflow)
        self.properties_panel.clear()
        self.monitoring_panel.clear()
        self.data_source_manager.set_config({})
        self._mark_saved()
        self.setWindowTitle("Automation Studio - New Workflow")
        self.workflow_info_label.setText("New workflow")
        self.step_count_label.setText("Steps: 0")
        self.data_source_label.setText("")
        self.status_label.setText("New workflow created")

    def open_workflow(self):
        """Buka workflow dari file."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Open another workflow anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Workflow", "workflows", "JSON Files (*.json)"
        )

        if not file_path:
            return

        self._load_workflow_file(file_path)

    def close_workflow(self):
        """Close current workflow."""
        if not self.current_workflow:
            return

        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.new_workflow()

    def save_workflow(self):
        """Simpan workflow ke file."""
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self.save_workflow_as()

    def save_workflow_as(self):
        """Simpan workflow dengan nama baru."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Workflow", "workflows", "JSON Files (*.json)"
        )

        if file_path:
            self._do_save(file_path)
            self.current_file = file_path
            self._add_recent_file(file_path)

    def _do_save(self, file_path: str):
        """Internal save."""
        try:
            workflow_data = self.workflow_editor.to_workflow_data()

            # Preserve workflow metadata if available
            if self.current_workflow:
                workflow_data["id"] = self.current_workflow.id
                workflow_data["name"] = self.current_workflow.name
                workflow_data["version"] = self.current_workflow.version
                workflow_data["url"] = self.current_workflow.url
                workflow_data["data_source"] = self.current_workflow.data_source
                workflow_data["monitoring"] = self.current_workflow.monitoring
                workflow_data["created_at"] = self.current_workflow.created_at

            workflow = self.parser.parse(workflow_data)
            self.parser.save(workflow, file_path)

            self.current_workflow = workflow
            self.current_file = file_path
            self._mark_saved()
            self.setWindowTitle(f"Automation Studio - {workflow.name}")
            self.workflow_info_label.setText(f"{workflow.name} (v{workflow.version})")
            self.status_label.setText(f"Saved: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{str(e)}")

    def export_workflow_json(self):
        """Export workflow sebagai file JSON."""
        if not self.current_workflow:
            QMessageBox.warning(self, "No Workflow", "No workflow to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Workflow as JSON", "workflows", "JSON Files (*.json)"
        )

        if file_path:
            try:
                self.parser.save(self.current_workflow, file_path)
                self.status_label.setText(f"Exported: {file_path}")
                QMessageBox.information(self, "Export Success",
                    f"Workflow exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_workflow_txt(self):
        """Export workflow sebagai text report."""
        if not self.current_workflow:
            QMessageBox.warning(self, "No Workflow", "No workflow to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Workflow as Text", "workflows", "Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Workflow: {self.current_workflow.name}\n")
                    f.write(f"Version: {self.current_workflow.version}\n")
                    f.write(f"ID: {self.current_workflow.id}\n")
                    f.write(f"Steps: {len(self.current_workflow.steps)}\n")
                    f.write("=" * 60 + "\n\n")

                    for i, step in enumerate(self.current_workflow.steps):
                        f.write(f"Step {i+1}: [{step.type}] {step.label or step.id}\n")
                        f.write(f"  ID: {step.id}\n")
                        for key, value in step.params.items():
                            f.write(f"  {key}: {value}\n")
                        if step.children:
                            f.write(f"  Children: {len(step.children)} steps\n")
                            for j, child in enumerate(step.children):
                                f.write(f"    {j+1}. [{child.type}] {child.label or child.id}\n")
                        f.write("\n")

                self.status_label.setText(f"Exported: {file_path}")
                QMessageBox.information(self, "Export Success",
                    f"Workflow exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def validate_workflow(self):
        """Validasi workflow saat ini."""
        try:
            workflow_data = self.workflow_editor.to_workflow_data()
            workflow = self.parser.parse(workflow_data)

            steps_count = len(workflow.steps)

            # Hitung total steps termasuk nested
            total_steps = steps_count

            def count_nested(steps):
                nonlocal total_steps
                for s in steps:
                    if s.children:
                        total_steps += len(s.children)
                        count_nested(s.children)

            count_nested(workflow.steps)

            # Data source info
            ds_info = ""
            if workflow.data_source and workflow.data_source.get("type"):
                ds_info = f"\nData Source: {workflow.data_source['type'].upper()}"

            QMessageBox.information(
                self, "Validation",
                f"✅ Workflow valid!\n\n"
                f"Name: {workflow.name}\n"
                f"Version: {workflow.version}\n"
                f"Steps (top-level): {steps_count}\n"
                f"Total Steps (incl. nested): {total_steps}"
                f"{ds_info}"
            )
            self.status_label.setText(f"Validation OK: {total_steps} total steps")

        except Exception as e:
            QMessageBox.warning(self, "Validation Error", str(e))
            self.status_label.setText("Validation failed")

    # ==================== VIEW TOGGLE ====================

    def _toggle_monitoring_tab(self):
        """Switch to monitoring tab when toggled from View menu."""
        if self.monitoring_toggle_action.isChecked():
            self.right_tabs.setCurrentWidget(self.monitoring_panel)
            self.right_tabs.setVisible(True)
        else:
            self.right_tabs.setCurrentWidget(self.data_source_manager)

    def _update_monitoring_toggle(self, index: int):
        """Update toggle action state based on active tab."""
        self.monitoring_toggle_action.setChecked(
            self.right_tabs.widget(index) == self.monitoring_panel
        )

    # ==================== HELP / ABOUT ====================

    def show_shortcuts(self):
        """Tampilkan dialog keyboard shortcuts."""
        dialog = ShortcutsDialog(self)
        dialog.exec()

    def show_documentation(self):
        """Buka dokumentasi."""
        doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                "USER_GUIDE.md")
        if os.path.exists(doc_path):
            os.startfile(doc_path)
        else:
            QMessageBox.information(self, "Documentation",
                "Documentation file not found.\n\n"
                "Please refer to USER_GUIDE.md or PROJECT_PLAN.md in the project root.")

    def show_changelog(self):
        """Tampilkan change log."""
        changelog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                      "CHANGE_LOG.md")
        if os.path.exists(changelog_path):
            os.startfile(changelog_path)
        else:
            QMessageBox.information(self, "Change Log",
                "No change log file found.")

    def show_about(self):
        """Tampilkan dialog About."""
        QMessageBox.about(
            self, "About Automation Studio",
            "Automation Studio v1.0.0\n\n"
            "Aplikasi otomasi modular berbasis Python.\n\n"
            "Teknologi:\n"
            "- Python + Playwright\n"
            "- PySide6 (Qt for Python)\n"
            "- OpenCV + Tesseract OCR\n\n"
            "© 2026 Automation Studio"
        )

    # ==================== LICENSE METHODS ====================

    def _show_license_status(self):
        """Tampilkan dialog status lisensi."""
        from frontend.ui.license_dialog import LicenseDialog
        dialog = LicenseDialog(self.license_manager, self.usage_tracker, self)
        dialog.exec()
        self._update_license_status()

    def _activate_license(self):
        """Buka dialog aktivasi lisensi."""
        from frontend.ui.license_dialog import LicenseDialog
        dialog = LicenseDialog(self.license_manager, self.usage_tracker, self)
        dialog.license_activated.connect(self._on_license_activated)
        dialog.exec()
        self._update_license_status()

    def _deactivate_license(self):
        """Deaktivasi lisensi."""
        result = self.license_manager.deactivate()
        if result.get("success"):
            QMessageBox.information(self, "Success", result.get("message", "License deactivated"))
            self._update_license_status()
        else:
            QMessageBox.warning(self, "Warning", result.get("message", "Deactivation failed"))

    def _on_license_activated(self):
        """Handle license activated."""
        self._update_license_status()
        QMessageBox.information(self, "Success", "Lisensi berhasil diaktifkan!")

    # ==================== CLOSE EVENT ====================

    def closeEvent(self, event):
        """Handle close event dengan prompt unsaved changes."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save_workflow()
                # If save failed, don't close
                if self._modified:
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        self.engine.stop()
        self._save_geometry()
        self._save_settings()
        event.accept()
