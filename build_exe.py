"""
Build script untuk membuat executable (.exe) Automation Studio menggunakan PyInstaller.

Usage:
    python build_exe.py              # Build GUI version
    python build_exe.py --cli        # Build CLI only version
    python build_exe.py --api        # Build API server version
"""

import os
import sys
import shutil
import argparse


def _copy_runtime_files(dist_dir: str):
    """Salin file/folder pendukung yang dibutuhkan saat runtime."""
    # Buat folder dasar jika belum ada
    for folder in ["workflows", "data", "logs", "screenshots"]:
        os.makedirs(os.path.join(dist_dir, folder), exist_ok=True)

    # Salin config.yaml ke root folder distribusi
    src_config = "config.yaml"
    dst_config = os.path.join(dist_dir, "config.yaml")
    if os.path.exists(src_config):
        shutil.copy2(src_config, dst_config)


def build_gui():
    """Build GUI executable."""
    print("Building Automation Studio GUI...")
    
    # Clean previous build
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", "AutomationStudio",
        "--windowed",  # No console window
        "--icon", "NONE",  # TODO: Add icon file
        "--add-data", "config.yaml;.",
        "--add-data", "workflows;workflows",
        "--add-data", "data;data",
        "--add-data", "logs;logs",
        "--add-data", "screenshots;screenshots",
        "--hidden-import", "backend.core.engine",
        "--hidden-import", "backend.core.workflow_parser",
        "--hidden-import", "backend.core.action_registry",
        "--hidden-import", "backend.actions.base_action",
        "--hidden-import", "backend.actions.click_action",
        "--hidden-import", "backend.actions.input_text_action",
        "--hidden-import", "backend.actions.wait_action",
        "--hidden-import", "backend.actions.select_dropdown_action",
        "--hidden-import", "backend.actions.upload_file_action",
        "--hidden-import", "backend.actions.loop_action",
        "--hidden-import", "backend.actions.if_else_action",
        "--hidden-import", "backend.data_sources.base_source",
        "--hidden-import", "backend.data_sources.excel_source",
        "--hidden-import", "backend.data_sources.csv_source",
        "--hidden-import", "backend.data_sources.database_source",
        "--hidden-import", "backend.data_sources.api_source",
        "--hidden-import", "backend.monitoring.logger",
        "--hidden-import", "backend.monitoring.screenshot",
        "--hidden-import", "backend.monitoring.progress_tracker",
        "--hidden-import", "backend.monitoring.resume_handler",
        "--hidden-import", "backend.detectors.base_detector",
        "--hidden-import", "backend.detectors.ocr_detector",
        "--hidden-import", "backend.detectors.image_detector",
        "--hidden-import", "backend.license.license_manager",
        "--hidden-import", "backend.license.usage_tracker",
        "--hidden-import", "backend.license.fingerprint",
        "--hidden-import", "backend.core.workflow_builder",
        "--hidden-import", "backend.actions.navigate_action",
        "--hidden-import", "backend.actions.select_action",
        "--hidden-import", "backend.actions.select2_action",
        "--hidden-import", "backend.actions.http_submit_action",
        "--hidden-import", "frontend.ui.auto_generate_dialog",
        "--hidden-import", "yaml",
        "--hidden-import", "loguru",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "cv2",
        "--hidden-import", "pytesseract",
        "--hidden-import", "PIL",
        "--hidden-import", "pyautogui",
        "--collect-all", "PySide6",
        "frontend/main.py",
    ]
    
    os.system(" ".join(cmd))

    dist_dir = os.path.join("dist", "AutomationStudio")
    _copy_runtime_files(dist_dir)
    print("\nBuild complete! Executable located at: dist/AutomationStudio/AutomationStudio.exe")


def build_cli():
    """Build CLI executable."""
    print("Building Automation Studio CLI...")
    
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    cmd = [
        "pyinstaller",
        "--name", "AutomationStudio_CLI",
        "--console",
        "--add-data", "config.yaml;.",
        "--add-data", "workflows;workflows",
        "--add-data", "data;data",
        "--add-data", "logs;logs",
        "--add-data", "screenshots;screenshots",
        "--hidden-import", "yaml",
        "--hidden-import", "loguru",
        "main.py",
    ]
    
    os.system(" ".join(cmd))

    dist_dir = os.path.join("dist", "AutomationStudio_CLI")
    _copy_runtime_files(dist_dir)
    print("\nBuild complete! Executable located at: dist/AutomationStudio_CLI/AutomationStudio_CLI.exe")


def build_api():
    """Build API server executable."""
    print("Building Automation Studio API Server...")
    
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    cmd = [
        "pyinstaller",
        "--name", "AutomationStudio_API",
        "--console",
        "--add-data", "config.yaml;.",
        "--add-data", "workflows;workflows",
        "--add-data", "data;data",
        "--add-data", "logs;logs",
        "--add-data", "screenshots;screenshots",
        "--hidden-import", "yaml",
        "--hidden-import", "loguru",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "backend/api/routes.py",
    ]
    
    os.system(" ".join(cmd))

    dist_dir = os.path.join("dist", "AutomationStudio_API")
    _copy_runtime_files(dist_dir)
    print("\nBuild complete! Executable located at: dist/AutomationStudio_API/AutomationStudio_API.exe")


def main():
    parser = argparse.ArgumentParser(description="Build Automation Studio executable")
    parser.add_argument("--cli", action="store_true", help="Build CLI version")
    parser.add_argument("--api", action="store_true", help="Build API server version")
    args = parser.parse_args()
    
    if args.cli:
        build_cli()
    elif args.api:
        build_api()
    else:
        build_gui()


if __name__ == "__main__":
    main()