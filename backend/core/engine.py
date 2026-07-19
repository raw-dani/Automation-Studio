"""
Execution Engine - Menjalankan workflow step-by-step menggunakan Playwright.
Handle retry, error, screenshot, dan resume.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Callable

from loguru import logger

from backend.actions.base_action import (
    BaseAction, ExecutionContext, ActionResult, ActionStatus
)
from backend.core.action_registry import ActionRegistry
from backend.core.workflow_parser import Workflow, WorkflowStep, WorkflowParser


class ExecutionEngine:
    """
    Engine utama untuk menjalankan workflow.
    
    Contoh penggunaan:
        engine = ExecutionEngine(action_registry)
        result = await engine.run("workflows/sample.json")
    """
    
    def __init__(self, action_registry: ActionRegistry, config: dict = None):
        self.action_registry = action_registry
        self.config = config or {}
        self._is_running = False
        self._is_paused = False
        self._current_step: Optional[WorkflowStep] = None
        self._browser = None
        self._page = None
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused
    
    @property
    def current_step(self) -> Optional[WorkflowStep]:
        return self._current_step
    
    def set_progress_callback(self, callback: Callable) -> None:
        """Set callback untuk progress update."""
        self._on_progress = callback
    
    def set_log_callback(self, callback: Callable) -> None:
        """Set callback untuk log update."""
        self._on_log = callback
    
    def _log(self, level: str, message: str, data: dict = None) -> None:
        """Internal logging."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {},
        }
        
        # Log ke file via loguru
        getattr(logger, level.lower(), logger.info)(message)
        
        # Callback ke UI
        if self._on_log:
            self._on_log(log_data)
    
    def _update_progress(self, current: int, total: int, step_id: str, status: str) -> None:
        """Update progress ke callback."""
        if self._on_progress:
            self._on_progress({
                "current": current,
                "total": total,
                "step_id": step_id,
                "status": status,
                "percentage": (current / total * 100) if total > 0 else 0,
            })
    
    async def _init_browser(self) -> None:
        """Inisialisasi browser Playwright."""
        from playwright.async_api import async_playwright
        
        playwright_config = self.config.get("playwright", {})
        browser_type = playwright_config.get("browser", "chromium")
        headless = playwright_config.get("headless", False)
        slow_mo = playwright_config.get("slow_mo", 100)
        
        self._playwright = await async_playwright().start()
        
        browser_launcher = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }.get(browser_type, self._playwright.chromium)
        
        self._browser = await browser_launcher.launch(
            headless=headless,
            slow_mo=slow_mo,
        )
        
        viewport = playwright_config.get("viewport", {"width": 1280, "height": 720})
        self._page = await self._browser.new_page(
            viewport=viewport,
        )
        
        self._log("INFO", f"Browser {browser_type} initialized (headless={headless})")
    
    async def _close_browser(self) -> None:
        """Tutup browser."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self._page = None
        self._browser = None
        self._playwright = None
    
    async def _take_screenshot(self, step_id: str, is_error: bool = False) -> Optional[str]:
        """Ambil screenshot dan simpan ke file."""
        if not self._page:
            return None
        
        screenshots_dir = self.config.get("paths", {}).get("screenshots", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        prefix = "error" if is_error else "step"
        filename = f"{prefix}_{step_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        try:
            await self._page.screenshot(path=filepath, full_page=False)
            self._log("INFO", f"Screenshot saved: {filename}")
            return filepath
        except Exception as e:
            self._log("WARNING", f"Failed to take screenshot: {e}")
            return None
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        step_index: int,
        total_steps: int,
    ) -> ActionResult:
        """
        Eksekusi satu step dengan retry logic.
        
        Args:
            step: Step yang akan dieksekusi.
            context: Execution context.
            step_index: Index step (untuk progress).
            total_steps: Total step (untuk progress).
            
        Returns:
            ActionResult.
        """
        self._current_step = step
        self._log("INFO", f"Executing step [{step_index}/{total_steps}]: {step.label or step.type} ({step.id})")
        self._update_progress(step_index, total_steps, step.id, "running")
        
        # Cek apakah di-pause
        while self._is_paused and self._is_running:
            await asyncio.sleep(0.5)
        
        if not self._is_running:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message="Workflow stopped",
            )
        
        # Dapatkan action dari registry
        action = self.action_registry.get(step.type)
        if not action:
            error_msg = f"Action type '{step.type}' tidak ditemukan di registry."
            self._log("ERROR", error_msg)
            return ActionResult(
                status=ActionStatus.FAILED,
                message=error_msg,
                error=error_msg,
            )
        
        # Eksekusi dengan retry
        max_retries = step.retry.get("max_retries", 3)
        retry_delay = step.retry.get("delay", 2000)
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self._log("INFO", f"Retry attempt {attempt}/{max_retries} for step {step.id}")
                    self._update_progress(step_index, total_steps, step.id, "retrying")
                    await asyncio.sleep(retry_delay / 1000)
                
                result = await action.execute(context, step.params)
                
                # Screenshot jika sukses dan di-set
                if (result.status == ActionStatus.SUCCESS and 
                    context.config.get("monitoring", {}).get("screenshot_on_step", False)):
                    screenshot_path = await self._take_screenshot(step.id)
                    result.screenshot_path = screenshot_path
                
                # Screenshot jika error
                if result.status == ActionStatus.FAILED:
                    screenshot_path = await self._take_screenshot(step.id, is_error=True)
                    result.screenshot_path = screenshot_path
                
                self._log(
                    "INFO" if result.status == ActionStatus.SUCCESS else "ERROR",
                    f"Step {step.id}: {result.status.value} - {result.message}",
                )
                
                if result.status == ActionStatus.SUCCESS:
                    self._update_progress(step_index, total_steps, step.id, "success")
                else:
                    self._update_progress(step_index, total_steps, step.id, "failed")
                
                return result
                
            except Exception as e:
                last_error = str(e)
                self._log("WARNING", f"Step {step.id} error (attempt {attempt+1}): {e}")
                
                if attempt < max_retries:
                    continue
                
                # Screenshot error
                screenshot_path = await self._take_screenshot(step.id, is_error=True)
                
                self._update_progress(step_index, total_steps, step.id, "failed")
                
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Failed after {max_retries + 1} attempts: {last_error}",
                    error=last_error,
                    screenshot_path=screenshot_path,
                )
        
        # Should not reach here
        return ActionResult(
            status=ActionStatus.FAILED,
            message="Unknown error",
        )
    
    async def _execute_data_source_loop(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        loop_start_index: int,
        context: ExecutionContext,
        results: list,
    ) -> dict:
        """
        Eksekusi loop dengan data source.
        Untuk workflow flat, loop body = semua step setelah loop step ini.
        Untuk workflow nested, loop body = step.children.
        """
        data_source_config = workflow.data_source
        if not data_source_config:
            self._log("WARNING", f"No data source configured for loop {step.id}")
            return {"next_index": loop_start_index + 1}
        
        # Baca data source
        data_rows = []
        try:
            source_type = data_source_config.get("type", "")
            source = None
            if source_type == "excel":
                from backend.data_sources.excel_source import ExcelDataSource
                source = ExcelDataSource()
            elif source_type == "api":
                from backend.data_sources.api_source import ApiDataSource
                source = ApiDataSource()
            elif source_type == "database":
                from backend.data_sources.database_source import DatabaseDataSource
                source = DatabaseDataSource()
            
            if source:
                config = data_source_config.get("config", {})
                errors = source.validate_config(config)
                if errors:
                    self._log("ERROR", f"Data source validation errors: {errors}")
                    return {"next_index": loop_start_index + 1}
                for row in source.read(config):
                    data_rows.append(row)
        except Exception as e:
            self._log("ERROR", f"Failed to read data source: {e}")
            return {"next_index": loop_start_index + 1}
        
        if not data_rows:
            self._log("WARNING", f"No data found in data source, skipping loop {step.id}")
            return {"next_index": loop_start_index + 1}
        
        # Tentukan loop body
        if step.children:
            loop_body = list(step.children)
        else:
            loop_body = workflow.steps[loop_start_index + 1:]
        
        total_iterations = len(data_rows)
        self._log("INFO", f"Loop {step.id}: {total_iterations} rows from data source")
        
        for iteration, row in enumerate(data_rows):
            if not self._is_running:
                break
            
            # Check pause/stop
            while self._is_paused and self._is_running:
                await asyncio.sleep(0.5)
            
            if not self._is_running:
                break
            
            context.current_data = row.data
            self._log("INFO", f"Loop iteration {iteration + 1}/{total_iterations}: {row.data}")
            
            for body_step in loop_body:
                if not self._is_running:
                    break
                
                while self._is_paused and self._is_running:
                    await asyncio.sleep(0.5)
                
                if not self._is_running:
                    break
                
                result = await self._execute_step(body_step, context, loop_start_index + 1, total_iterations * len(loop_body))
                results.append({
                    "step_id": body_step.id,
                    "step_type": body_step.type,
                    "step_label": body_step.label,
                    "status": result.status.value,
                    "message": result.message,
                    "screenshot": result.screenshot_path,
                    "error": result.error,
                })
                
                if result.status == ActionStatus.FAILED:
                    if body_step.on_error == "stop":
                        self._log("ERROR", f"Workflow stopped due to error at step {body_step.id}")
                        return {"should_stop": True}
                    elif body_step.on_error == "skip":
                        self._log("WARNING", f"Skipping error at step {body_step.id}")
                        continue
        
        # Jika tidak ada children, semua step setelah loop sudah dieksekusi
        if not step.children:
            return {"next_index": len(workflow.steps)}
        else:
            return {"next_index": loop_start_index + 1}
    
    async def run(
        self,
        workflow: Workflow,
        execution_id: Optional[str] = None,
        resume_from: Optional[str] = None,
        start_url: Optional[str] = None,
    ) -> dict:
        """
        Jalankan workflow.
        
        Args:
            workflow: Workflow object.
            execution_id: Optional execution ID.
            resume_from: Optional step ID untuk resume.
            
        Returns:
            Dict dengan hasil eksekusi.
        """
        execution_id = execution_id or str(uuid.uuid4())[:8]
        self._is_running = True
        self._is_paused = False
        
        self._log("INFO", f"Starting workflow: {workflow.name} (ID: {execution_id})")
        self._log("INFO", f"Total steps: {len(workflow.steps)}")
        
        start_time = datetime.now()
        results = []
        should_stop = False
        resume_index = 0
        
        # Cari index untuk resume
        if resume_from:
            for i, step in enumerate(workflow.steps):
                if step.id == resume_from:
                    resume_index = i
                    self._log("INFO", f"Resuming from step: {step.id} (index: {i})")
                    break
        
        try:
            # Init browser
            await self._init_browser()
            
            # Navigate to workflow URL if set
            target_url = start_url or workflow.url
            if target_url:
                try:
                    await self._page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    self._log("INFO", f"Navigated to URL: {target_url}")
                except Exception as e:
                    self._log("WARNING", f"Failed to navigate to URL '{target_url}': {e}")
            
            # Buat execution context
            self._context = ExecutionContext(
                page=self._page,
                browser=self._browser,
                workflow_id=workflow.id,
                execution_id=execution_id,
                screenshots_dir=self.config.get("paths", {}).get("screenshots", "screenshots"),
                logs_dir=self.config.get("paths", {}).get("logs", "logs"),
                config=self.config,
                is_running=self._is_running,
                is_paused=self._is_paused,
            )
            
            context = self._context
            
            # Eksekusi setiap step
            total_steps = len(workflow.steps)
            i = 0
            while i < len(workflow.steps):
                if not self._is_running:
                    break
                
                if i < resume_index:
                    i += 1
                    continue
                
                step = workflow.steps[i]
                
                # Update context state
                if self._context:
                    self._context.is_running = self._is_running
                    self._context.is_paused = self._is_paused
                
                # Special handling for data_source loop
                if step.type == "loop" and step.params.get("loop_type") == "data_source":
                    loop_result = await self._execute_data_source_loop(step, workflow, i, context, results)
                    if loop_result.get("should_stop"):
                        should_stop = True
                        break
                    i = loop_result.get("next_index", i + 1)
                    continue
                
                result = await self._execute_step(step, context, i + 1, total_steps)
                results.append({
                    "step_id": step.id,
                    "step_type": step.type,
                    "step_label": step.label,
                    "status": result.status.value,
                    "message": result.message,
                    "screenshot": result.screenshot_path,
                    "error": result.error,
                })
                
                # Handle on_error
                if result.status == ActionStatus.FAILED:
                    if step.on_error == "stop":
                        self._log("ERROR", f"Workflow stopped due to error at step {step.id}")
                        should_stop = True
                        break
                    elif step.on_error == "skip":
                        self._log("WARNING", f"Skipping error at step {step.id}")
                        i += 1
                        continue
                
                i += 1
            
        except Exception as e:
            self._log("ERROR", f"Workflow execution error: {e}")
            results.append({
                "step_id": "system",
                "step_type": "system",
                "step_label": "System Error",
                "status": "failed",
                "message": str(e),
                "error": str(e),
            })
        
        finally:
            await self._close_browser()
            self._is_running = False
            self._is_paused = False
            self._current_step = None
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Hitung status akhir
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        final_status = "success" if failed_count == 0 and not should_stop else "completed_with_errors" if failed_count > 0 else "failed"
        
        execution_result = {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "status": final_status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_steps": total_steps,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }
        
        self._log("INFO", f"Workflow completed: {final_status} ({duration:.2f}s)")
        
        return execution_result
    
    def pause(self) -> None:
        """Pause eksekusi workflow."""
        if self._is_running:
            self._is_paused = True
            self._log("INFO", "Workflow paused")
            if hasattr(self, '_context') and self._context:
                self._context.is_paused = True
    
    def resume(self) -> None:
        """Resume eksekusi workflow."""
        if self._is_paused:
            self._is_paused = False
            self._log("INFO", "Workflow resumed")
            if hasattr(self, '_context') and self._context:
                self._context.is_paused = False
    
    def stop(self) -> None:
        """Stop eksekusi workflow."""
        self._is_running = False
        self._is_paused = False
        self._log("INFO", "Workflow stopped")
        if hasattr(self, '_context') and self._context:
            self._context.is_running = False
            self._context.is_paused = False