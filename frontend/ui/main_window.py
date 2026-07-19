"""
Main Window - Jendela utama aplikasi Automation Studio.
Menggunakan layout splitter dengan panel-panel yang terintegrasi.
"""

import sys
import os
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QLabel, QApplication, QTabWidget,
)
from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QFont

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
from backend.actions.wait_action import WaitAction
from backend.actions.select_dropdown_action import SelectDropdownAction
from backend.actions.upload_file_action import UploadFileAction
from backend.actions.loop_action import LoopAction
from backend.actions.if_else_action import IfElseAction
from backend.actions.navigate_action import NavigateAction
from backend.actions.select_action import SelectAction
from backend.actions.select2_action import Select2Action


class MainWindow(QMainWindow):
    """Jendela utama Automation Studio."""
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.current_workflow: Optional[Workflow] = None
        self.current_file: Optional[str] = None
        self.current_data_source: dict = {}
        
        # Setup backend
        self.action_registry = self._create_action_registry()
        self.engine = ExecutionEngine(self.action_registry, self.config)
        self.parser = WorkflowParser()
        
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        
        # Connect signals
        self._connect_signals()
    
    def _create_action_registry(self) -> ActionRegistry:
        """Buat dan daftarkan semua action."""
        registry = ActionRegistry()
        registry.register(ClickAction())
        registry.register(InputTextAction())
        registry.register(WaitAction())
        registry.register(SelectDropdownAction())
        registry.register(SelectAction())
        registry.register(Select2Action())
        registry.register(UploadFileAction())
        registry.register(LoopAction())
        registry.register(IfElseAction())
        registry.register(NavigateAction())
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
        
        # Right panel: Properties (top) + tabs (bottom)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.properties_panel = PropertiesPanel()
        
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setDocumentMode(True)
        self.bottom_tabs.setTabPosition(QTabWidget.South)
        
        self.data_source_manager = DataSourceManager()
        self.execution_panel = ExecutionPanel(self.engine)
        self.monitoring_panel = MonitoringPanel()
        
        self.bottom_tabs.addTab(self.data_source_manager, "Data Source")
        self.bottom_tabs.addTab(self.execution_panel, "Execution")
        self.bottom_tabs.addTab(self.monitoring_panel, "Monitoring")
        
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.properties_panel)
        right_splitter.addWidget(self.bottom_tabs)
        right_splitter.setSizes([420, 280])
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)
        
        right_layout.addWidget(right_splitter)
        
        # Add to main splitter
        self.main_splitter.addWidget(self.action_palette)
        self.main_splitter.addWidget(self.workflow_editor)
        self.main_splitter.addWidget(right_panel)
        
        # Set default sizes
        self.main_splitter.setSizes([220, 700, 400])
        
        main_layout.addWidget(self.main_splitter)
    
    def _init_menu(self):
        """Inisialisasi menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Workflow", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_workflow)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Workflow...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_workflow)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_workflow)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_workflow_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction("&Delete Selected", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.workflow_editor.delete_selected)
        edit_menu.addAction(delete_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        view_menu.addAction(self.action_palette.toggleViewAction())
        
        self.monitoring_toggle_action = QAction("Monitoring Panel", self)
        self.monitoring_toggle_action.setCheckable(True)
        self.monitoring_toggle_action.setChecked(True)
        self.monitoring_toggle_action.triggered.connect(self._toggle_monitoring_tab)
        view_menu.addAction(self.monitoring_toggle_action)
        
        self.bottom_tabs.currentChanged.connect(self._update_monitoring_toggle)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbar(self):
        """Inisialisasi toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # New
        new_btn = QAction("New", self)
        new_btn.setToolTip("New Workflow")
        new_btn.triggered.connect(self.new_workflow)
        toolbar.addAction(new_btn)
        
        # Open
        open_btn = QAction("Open", self)
        open_btn.setToolTip("Open Workflow")
        open_btn.triggered.connect(self.open_workflow)
        toolbar.addAction(open_btn)
        
        # Save
        save_btn = QAction("Save", self)
        save_btn.setToolTip("Save Workflow")
        save_btn.triggered.connect(self.save_workflow)
        toolbar.addAction(save_btn)
        
        toolbar.addSeparator()
        
        # Validate
        validate_btn = QAction("Validate", self)
        validate_btn.setToolTip("Validate Workflow")
        validate_btn.triggered.connect(self.validate_workflow)
        toolbar.addAction(validate_btn)
        
        toolbar.addSeparator()
        
        # Zoom
        zoom_in_btn = QAction("Zoom +", self)
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.triggered.connect(self.workflow_editor.zoom_in)
        toolbar.addAction(zoom_in_btn)
        
        zoom_out_btn = QAction("Zoom -", self)
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.triggered.connect(self.workflow_editor.zoom_out)
        toolbar.addAction(zoom_out_btn)
        
        zoom_fit_btn = QAction("Fit", self)
        zoom_fit_btn.setToolTip("Fit to Screen")
        zoom_fit_btn.triggered.connect(self.workflow_editor.zoom_fit)
        toolbar.addAction(zoom_fit_btn)
    
    def _init_statusbar(self):
        """Inisialisasi status bar."""
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label, 1)
        
        self.workflow_info_label = QLabel("No workflow loaded")
        self.statusBar().addPermanentWidget(self.workflow_info_label)
    
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
    
    def _on_workflow_changed(self):
        """Sync editor state ke execution panel."""
        try:
            data = self.workflow_editor.to_workflow_data()
            if data and data.get("steps"):
                data["data_source"] = self.current_data_source
                workflow = self.parser.parse(data)
                self.execution_panel.set_workflow(workflow)
                self.current_workflow = workflow
            else:
                self.execution_panel.set_workflow(None)
                self.current_workflow = None
        except Exception:
            pass
    
    def _on_data_source_changed(self, config: dict):
        """Handle data source config change."""
        self.current_data_source = config
        if self.current_workflow:
            self.current_workflow.data_source = config
    
    def _on_node_selected_for_properties(self, step_id: str, params: dict):
        """Handle node selection untuk properties panel, including action type."""
        action_type = params.get("type", "")
        self.properties_panel.show_action_properties(step_id, params, action_type)
    
    def _move_selected_node_up(self):
        """Move selected node up in execution order."""
        selected_items = self.workflow_editor.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if hasattr(item, 'step_id'):
                self.workflow_editor.move_node_up(item.step_id)
    
    def _move_selected_node_down(self):
        """Move selected node down in execution order."""
        selected_items = self.workflow_editor.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if hasattr(item, 'step_id'):
                self.workflow_editor.move_node_down(item.step_id)
    
    def _on_properties_save_requested(self):
        """Handle save request from properties panel."""
        if not self.current_workflow or not self.current_file:
            self.status_label.setText("No workflow to save")
            self.properties_panel.save_requested.emit()
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
                self.status_label.setText(f"Saved: {self.current_file}")
                self.execution_panel.show_save_feedback(True, "Saved successfully!")
            except Exception as e:
                self.execution_panel.show_save_feedback(False, f"Save failed: {str(e)}")
        else:
            self.save_workflow_as()
    
    def _toggle_monitoring_tab(self):
        """Switch to monitoring tab when toggled from View menu."""
        if self.monitoring_toggle_action.isChecked():
            self.bottom_tabs.setCurrentWidget(self.monitoring_panel)
            self.bottom_tabs.setVisible(True)
        else:
            self.bottom_tabs.setCurrentWidget(self.data_source_manager)
    
    def _update_monitoring_toggle(self, index: int):
        """Update toggle action state based on active tab."""
        self.monitoring_toggle_action.setChecked(
            self.bottom_tabs.widget(index) == self.monitoring_panel
        )
    
    def new_workflow(self):
        """Buat workflow baru."""
        self.current_workflow = None
        self.current_file = None
        self.current_data_source = {}
        self.workflow_editor.clear()
        self.properties_panel.clear()
        self.monitoring_panel.clear()
        self.data_source_manager.set_config({})
        self.setWindowTitle("Automation Studio - New Workflow")
        self.workflow_info_label.setText("New workflow")
        self.status_label.setText("New workflow created")
    
    def open_workflow(self):
        """Buka workflow dari file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Workflow", "workflows", "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            workflow = self.parser.load(file_path)
            self.current_workflow = workflow
            self.current_file = file_path
            self.current_data_source = workflow.data_source or {}
            
            self.workflow_editor.load_workflow(workflow)
            self.execution_panel.set_workflow(workflow)
            self.data_source_manager.set_config(self.current_data_source)
            self.setWindowTitle(f"Automation Studio - {workflow.name}")
            self.workflow_info_label.setText(f"{workflow.name} (v{workflow.version})")
            self.status_label.setText(f"Loaded: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membuka workflow:\n{str(e)}")
    
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
            self.setWindowTitle(f"Automation Studio - {workflow.name}")
            self.status_label.setText(f"Saved: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{str(e)}")
    
    def validate_workflow(self):
        """Validasi workflow saat ini."""
        try:
            workflow_data = self.workflow_editor.to_workflow_data()
            workflow = self.parser.parse(workflow_data)
            
            steps_count = len(workflow.steps)
            QMessageBox.information(
                self, "Validation",
                f"Workflow valid!\n\nName: {workflow.name}\nSteps: {steps_count}"
            )
            self.status_label.setText(f"Validation OK: {steps_count} steps")
            
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", str(e))
            self.status_label.setText("Validation failed")
    
    def show_about(self):
        """Tampilkan dialog About."""
        QMessageBox.about(
            self, "About Automation Studio",
            "Automation Studio v1.0.0\n\n"
            "Aplikasi otomasi modular berbasis Python.\n\n"
            "Teknologi:\n"
            "- Python + Playwright\n"
            "- PySide6 (Qt for Python)\n"
            "- OpenCV + Tesseract OCR"
        )
    
    def closeEvent(self, event):
        """Handle close event."""
        # TODO: Cek jika ada perubahan yang belum disimpan
        self.engine.stop()
        event.accept()