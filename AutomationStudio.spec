# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\EIKON\\Documents\\APP\\Automation Studio\\config.yaml', '.'), ('C:\\Users\\EIKON\\Documents\\APP\\Automation Studio\\workflows', 'workflows'), ('C:\\Users\\EIKON\\Documents\\APP\\Automation Studio\\data', 'data'), ('C:\\Users\\EIKON\\Documents\\APP\\Automation Studio\\logs', 'logs'), ('C:\\Users\\EIKON\\Documents\\APP\\Automation Studio\\screenshots', 'screenshots')]
binaries = []
hiddenimports = ['backend.core.engine', 'backend.core.workflow_parser', 'backend.core.action_registry', 'backend.actions.base_action', 'backend.actions.click_action', 'backend.actions.input_text_action', 'backend.actions.batch_input_action', 'backend.actions.wait_action', 'backend.actions.select_dropdown_action', 'backend.actions.upload_file_action', 'backend.actions.loop_action', 'backend.actions.if_else_action', 'backend.data_sources.base_source', 'backend.data_sources.excel_source', 'backend.data_sources.csv_source', 'backend.data_sources.database_source', 'backend.data_sources.api_source', 'backend.monitoring.logger', 'backend.monitoring.screenshot', 'backend.monitoring.progress_tracker', 'backend.monitoring.resume_handler', 'backend.detectors.base_detector', 'backend.detectors.ocr_detector', 'backend.detectors.image_detector', 'backend.license.license_manager', 'backend.license.usage_tracker', 'backend.license.fingerprint', 'backend.core.workflow_builder', 'backend.actions.navigate_action', 'backend.actions.select_action', 'backend.actions.select2_action', 'backend.actions.http_submit_action', 'frontend.ui.auto_generate_dialog', 'yaml', 'loguru', 'pandas', 'openpyxl', 'cv2', 'pytesseract', 'PIL', 'pyautogui', 'playwright', 'requests', 'numpy', 'httpx', 'sqlalchemy', 'uvicorn', 'fastapi', 'pydantic', 'PIL.Image', 'PIL.ImageQt', 'winreg', 'backend.actions.input_date_action', 'backend.actions.radio_select_action', 'backend.actions.parallel_group_action', 'backend.api.schemas']
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['frontend\\main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutomationStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutomationStudio',
)
