"""
Automation Studio - Main Entry Point
Aplikasi otomasi modular berbasis Python.

Usage:
    python main.py --help
    python main.py run workflows/sample_workflow.json
    python main.py list
    python main.py validate workflows/sample_workflow.json
    python main.py preview-excel --file data/sample.xlsx --sheet Sheet1
    python main.py preview-csv --file data/sample.csv
"""

import sys
import os
import json
import asyncio
import argparse
from datetime import datetime

# Tambahkan root project ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from backend.core.engine import ExecutionEngine
from backend.core.action_registry import ActionRegistry
from backend.core.workflow_parser import WorkflowParser, WorkflowValidationError

# Actions
from backend.actions.click_action import ClickAction
from backend.actions.input_text_action import InputTextAction
from backend.actions.input_date_action import InputDateAction
from backend.actions.wait_action import WaitAction
from backend.actions.select_dropdown_action import SelectDropdownAction
from backend.actions.upload_file_action import UploadFileAction
from backend.actions.loop_action import LoopAction
from backend.actions.if_else_action import IfElseAction
from backend.actions.parallel_group_action import ParallelGroupAction
from backend.actions.radio_select_action import RadioSelectAction
from backend.actions.http_submit_action import HttpSubmitAction

# Data Sources
from backend.data_sources.excel_source import ExcelDataSource
from backend.data_sources.csv_source import CsvDataSource


def load_config(config_path: str = "config.yaml") -> dict:
    """Load konfigurasi dari file YAML."""
    import yaml
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file '{config_path}' tidak ditemukan. Menggunakan default config.")
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Config loaded from '{config_path}'")
    return config or {}


def setup_logging(config: dict) -> None:
    """Setup logging configuration."""
    log_level = config.get("execution", {}).get("log_level", "INFO")
    logs_dir = config.get("paths", {}).get("logs", "logs")
    
    os.makedirs(logs_dir, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=log_level,
        colorize=True,
    )
    
    # File handler
    log_file = os.path.join(logs_dir, f"automation_studio_{datetime.now().strftime('%Y%m%d')}.log")
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
    )
    
    logger.info(f"Logging initialized. Level: {log_level}, File: {log_file}")


def create_action_registry() -> ActionRegistry:
    """Membuat dan mendaftarkan semua action."""
    registry = ActionRegistry()
    
    # Phase 1: Basic actions
    registry.register(ClickAction())
    registry.register(InputTextAction())
    registry.register(InputDateAction())
    registry.register(WaitAction())
    
    # Phase 2: Additional actions
    registry.register(SelectDropdownAction())
    registry.register(RadioSelectAction())
    registry.register(UploadFileAction())
    registry.register(HttpSubmitAction())
    registry.register(LoopAction())
    registry.register(IfElseAction())
    registry.register(ParallelGroupAction())
    
    logger.info(f"Action registry initialized with {len(registry.get_all())} actions")
    logger.debug(f"Registered actions: {', '.join(registry.get_action_names())}")
    
    return registry


async def run_workflow(args, config: dict, registry: ActionRegistry) -> None:
    """Jalankan workflow."""
    parser = WorkflowParser()
    
    try:
        workflow = parser.load(args.workflow)
        logger.info(f"Workflow loaded: {workflow.name} (v{workflow.version})")
        logger.info(f"Steps: {len(workflow.steps)}")
        
        engine = ExecutionEngine(registry, config)
        
        # Setup progress callback
        def on_progress(progress: dict):
            bar_length = 30
            filled = int(bar_length * progress["percentage"] / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\rProgress: |{bar}| {progress['percentage']:.0f}% - {progress['status']}", end="")
            if progress["status"] in ("success", "failed"):
                print()
        
        engine.set_progress_callback(on_progress)
        
        # Setup log callback
        def on_log(log_data: dict):
            pass  # Log sudah ditangani oleh loguru
        
        engine.set_log_callback(on_log)
        
        # Jalankan workflow
        result = await engine.run(workflow)
        
        # Tampilkan hasil
        print(f"\n{'='*50}")
        print(f"Workflow: {result['workflow_name']}")
        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"Steps: {result['success_count']} success, {result['failed_count']} failed")
        print(f"{'='*50}")
        
        for step_result in result["results"]:
            status_icon = "[OK]" if step_result["status"] == "success" else "[FAIL]"
            print(f"  {status_icon} [{step_result['step_id']}] {step_result['step_label'] or step_result['step_type']}: {step_result['message']}")
            if step_result.get("screenshot"):
                print(f"     [SCREENSHOT] {step_result['screenshot']}")
        
        # Exit code
        if result["status"] == "failed":
            sys.exit(1)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except WorkflowValidationError as e:
        logger.error(f"Workflow validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def list_workflows(args, config: dict) -> None:
    """List semua workflow yang tersedia."""
    parser = WorkflowParser()
    workflows_dir = config.get("paths", {}).get("workflows", "workflows")
    
    workflows = parser.list_workflows(workflows_dir)
    
    if not workflows:
        print(f"Tidak ada workflow ditemukan di folder '{workflows_dir}'.")
        return
    
    print(f"\n{'='*60}")
    print(f"Daftar Workflow ({len(workflows)} ditemukan):")
    print(f"{'='*60}")
    
    for wf in workflows:
        print(f"  [WF] {wf['name']} (v{wf['version']})")
        print(f"     ID: {wf['id']}")
        print(f"     File: {wf['file']}")
        print(f"     Steps: {wf['steps_count']}")
        print(f"     Updated: {wf['updated_at']}")
        print()


def validate_workflow(args, config: dict) -> None:
    """Validasi workflow file."""
    parser = WorkflowParser()
    
    try:
        workflow = parser.load(args.workflow)
        print(f"\n[OK] Workflow valid!")
        print(f"   Name: {workflow.name}")
        print(f"   Version: {workflow.version}")
        print(f"   Steps: {len(workflow.steps)}")
        
        for i, step in enumerate(workflow.steps):
            children_info = ""
            if step.children:
                children_info = f" ({len(step.children)} children)"
            print(f"   {i+1}. [{step.type}] {step.label or step.id}{children_info}")
        
    except (FileNotFoundError, WorkflowValidationError) as e:
        print(f"\n[FAIL] Workflow invalid: {e}")
        sys.exit(1)


def preview_excel(args) -> None:
    """Preview data dari Excel."""
    from backend.data_sources.excel_source import ExcelDataSource
    
    source = ExcelDataSource()
    config = {
        "file_path": args.file,
        "sheet": args.sheet or "Sheet1",
    }
    
    errors = source.validate_config(config)
    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        sys.exit(1)
    
    print(f"\nPreview Excel: {args.file} -> Sheet: {args.sheet or 'Sheet1'}")
    print(f"{'='*60}")
    
    rows = source.get_preview(config, max_rows=10)
    if not rows:
        print("  (No data)")
        return
    
    # Print header
    if rows:
        headers = list(rows[0].keys())
        print(f"  Columns: {', '.join(headers)}")
        print(f"  Total preview: {len(rows)} rows")
        print()
        for i, row in enumerate(rows):
            print(f"  Row {i+1}: {json.dumps(row, ensure_ascii=False)}")


def preview_csv(args) -> None:
    """Preview data dari CSV."""
    from backend.data_sources.csv_source import CsvDataSource
    
    source = CsvDataSource()
    config = {
        "file_path": args.file,
        "delimiter": args.delimiter or ",",
        "encoding": args.encoding or "utf-8",
    }
    
    errors = source.validate_config(config)
    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        sys.exit(1)
    
    print(f"\nPreview CSV: {args.file}")
    print(f"{'='*60}")
    
    rows = source.get_preview(config, max_rows=10)
    if not rows:
        print("  (No data)")
        return
    
    if rows:
        headers = list(rows[0].keys())
        print(f"  Columns: {', '.join(headers)}")
        print(f"  Total preview: {len(rows)} rows")
        print()
        for i, row in enumerate(rows):
            print(f"  Row {i+1}: {json.dumps(row, ensure_ascii=False)}")


def list_actions(args) -> None:
    """List semua action yang tersedia."""
    registry = create_action_registry()
    actions = registry.get_action_descriptions()
    
    print(f"\n{'='*60}")
    print(f"Daftar Actions ({len(actions)} tersedia):")
    print(f"{'='*60}")
    
    for action in actions:
        print(f"  [{action['name']}]")
        print(f"     Description: {action['description']}")
        print(f"     Default params: {json.dumps(action['default_params'], ensure_ascii=False)}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automation Studio - Aplikasi Otomasi Modular",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py run workflows/sample_workflow.json
  python main.py list
  python main.py validate workflows/sample_workflow.json
  python main.py actions
  python main.py preview-excel --file data/sample.xlsx
  python main.py preview-csv --file data/sample.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Jalankan workflow")
    run_parser.add_argument("workflow", help="Path ke file workflow JSON")
    run_parser.add_argument("--config", default="config.yaml", help="Path ke file config")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List semua workflow")
    list_parser.add_argument("--config", default="config.yaml", help="Path ke file config")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validasi workflow file")
    validate_parser.add_argument("workflow", help="Path ke file workflow JSON")
    validate_parser.add_argument("--config", default="config.yaml", help="Path ke file config")
    
    # Actions command
    actions_parser = subparsers.add_parser("actions", help="List semua action")
    
    # Preview Excel
    excel_parser = subparsers.add_parser("preview-excel", help="Preview data Excel")
    excel_parser.add_argument("--file", required=True, help="Path ke file Excel")
    excel_parser.add_argument("--sheet", default="Sheet1", help="Nama sheet")
    
    # Preview CSV
    csv_parser = subparsers.add_parser("preview-csv", help="Preview data CSV")
    csv_parser.add_argument("--file", required=True, help="Path ke file CSV")
    csv_parser.add_argument("--delimiter", default=",", help="Delimiter CSV")
    csv_parser.add_argument("--encoding", default="utf-8", help="Encoding file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Commands that don't need config/logging
    if args.command == "actions":
        list_actions(args)
        return
    
    if args.command in ("preview-excel", "preview-csv"):
        if args.command == "preview-excel":
            preview_excel(args)
        else:
            preview_csv(args)
        return
    
    # Load config untuk command yang membutuhkan
    config = load_config(args.config)
    setup_logging(config)
    
    if args.command == "run":
        registry = create_action_registry()
        asyncio.run(run_workflow(args, config, registry))
    
    elif args.command == "list":
        list_workflows(args, config)
    
    elif args.command == "validate":
        validate_workflow(args, config)


if __name__ == "__main__":
    main()