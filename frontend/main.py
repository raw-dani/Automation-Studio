"""
Automation Studio - Frontend Entry Point
Aplikasi desktop Automation Studio dengan PySide6.

Usage:
    python frontend/main.py
    python frontend/main.py --config config.yaml
"""

import sys
import os

# Tambahkan root project ke path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from frontend.ui.main_window import MainWindow


def load_config(config_path: str = "config.yaml") -> dict:
    """Load konfigurasi dari file YAML."""
    import yaml
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(app_dir, config_path)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    """Main entry point untuk frontend."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automation Studio Desktop")
    parser.add_argument("--config", default="config.yaml", help="Path ke config file")
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Automation Studio")
    app.setOrganizationName("Automation Studio")
    
    # Set global style
    app.setStyle("Fusion")
    
    # Set stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 4px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #2196F3;
        }
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        QTabBar::tab {
            padding: 6px 12px;
            margin: 2px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #2196F3;
        }
        QScrollArea {
            border: none;
        }
        QSplitter::handle {
            background: #e0e0e0;
            width: 2px;
        }
    """)
    
    # Create main window
    window = MainWindow(config)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()