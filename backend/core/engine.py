"""
Execution Engine - Menjalankan workflow step-by-step menggunakan Playwright.
Handle retry, error, screenshot, dan resume.
"""

import os
import sys
import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, Callable

from loguru import logger

from backend.actions.base_action import (
    BaseAction, ExecutionContext, ActionResult, ActionStatus
)
from backend.core.action_registry import ActionRegistry
from backend.core.workflow_parser import Workflow, WorkflowStep, WorkflowParser
from backend.license.license_manager import LicenseManager
from backend.license.usage_tracker import UsageTracker


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
        self.license_manager: Optional[LicenseManager] = None
        self.usage_tracker: Optional[UsageTracker] = None
        self._completed_count = 0
        self._failed_count = 0
        self._skipped_count = 0
    
    def _get_app_dir(self) -> str:
        """Dapatkan direktori aplikasi (berisi EXE/config.yaml)."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.getcwd()
    
    def _filter_rows_by_range(self, rows: list, row_range: dict) -> list:
        """Filter data rows sesuai row_range config dari UI."""
        if not row_range or row_range.get("mode") == "all":
            return rows
        
        mode = row_range.get("mode", "all")
        if mode == "single":
            row_num = max(1, int(row_range.get("row", 1)))
            idx = row_num - 1
            if 0 <= idx < len(rows):
                return [rows[idx]]
            return []
        
        if mode == "range":
            range_str = row_range.get("range_str", "")
            selected_indices = set()
            for part in range_str.split(","):
                part = part.strip()
                if "-" in part:
                    try:
                        start, end = part.split("-", 1)
                        start = int(start.strip())
                        end = int(end.strip())
                        for i in range(start, end + 1):
                            selected_indices.add(i - 1)
                    except Exception:
                        continue
                else:
                    try:
                        selected_indices.add(int(part) - 1)
                    except Exception:
                        continue
            return [rows[i] for i in sorted(selected_indices) if 0 <= i < len(rows)]
        
        return rows
    
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

    def set_license_manager(self, license_manager: LicenseManager, usage_tracker: UsageTracker):
        """Set license manager untuk batasan free mode."""
        self.license_manager = license_manager
        self.usage_tracker = usage_tracker
    
    def _log(self, level: str, message: str, data: dict = None) -> None:
        """Internal logging."""
        message = self._short(message)
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
    
    def _short(self, text: str, limit: int = 200) -> str:
        """Ringkas pesan log agar tidak terlalu panjang di UI."""
        if not text:
            return text
        text = str(text)
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."
    
    def _short_row(self, row_data: dict, keys: list = None) -> str:
        """Ringkas data baris untuk log loop."""
        if not row_data:
            return "{}"
        if keys is None:
            keys = ["Nama", "NIK", "Alamat", "Pemanfaatan", "Penggunaan", "Metode Ukur", "nama", "alamat", "email", "phone"]
        parts = []
        for k in keys:
            if k in row_data:
                v = str(row_data[k])
                if len(v) > 40:
                    v = v[:37] + "..."
                parts.append(f"{k}={v}")
        return "{" + ", ".join(parts) + "}"
    
    def _update_progress(self, current: int, total: int, step_id: str, status: str) -> None:
        """Update progress ke callback."""
        if self._on_progress:
            self._on_progress({
                "current": current,
                "total": total,
                "step_id": step_id,
                "status": status,
                "percentage": (current / total * 100) if total > 0 else 0,
                "completed_steps": self._completed_count,
                "failed_steps": self._failed_count,
                "skipped_steps": self._skipped_count,
            })
    
    async def _ensure_browser_installed(self, browser_type: str) -> None:
        """Pastikan browser Playwright terinstall sebelum dijalankan."""
        # Skip auto-install di bundled mode (EXE PyInstaller)
        if getattr(sys, 'frozen', False):
            self._log("INFO", "Bundled mode detected. Skipping browser auto-install.")
            return
            
        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            launcher = {
                "chromium": pw.chromium,
                "firefox": pw.firefox,
                "webkit": pw.webkit,
            }.get(browser_type, pw.chromium)
            
            executable_path = launcher.executable_path
            if not os.path.exists(executable_path):
                self._log("WARNING", f"Browser {browser_type} belum terinstall. Mencari executable di: {executable_path}")
                self._log("INFO", f"Sedang menginstall browser {browser_type}...")
                await launcher.install()
                self._log("SUCCESS", f"Browser {browser_type} berhasil diinstall.")
            
            await pw.stop()
        except Exception as e:
            self._log("ERROR", f"Gagal install browser {browser_type}: {e}")
            self._log("ERROR", "Silakan jalankan manual: python -m playwright install")
            raise RuntimeError(
                f"Browser Playwright ({browser_type}) tidak terinstall.\n"
                f"Silakan jalankan perintah berikut di terminal:\n"
                f"    python -m playwright install {browser_type}\n"
                f"Atau install semua browser:\n"
                f"    python -m playwright install"
            ) from e
    
    def _find_system_browser_executable(self, browser_type: str) -> Optional[str]:
        """Cari executable Chrome/Edge/Firefox yang terinstall di sistem."""
        import winreg
        
        if browser_type == "chromium":
            chrome_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    return path
            
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
                value, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if os.path.exists(value):
                    return value
            except Exception:
                pass
            
            edge_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
            ]
            for path in edge_paths:
                if os.path.exists(path):
                    return path
        
        elif browser_type == "firefox":
            firefox_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Mozilla Firefox", "firefox.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Mozilla Firefox", "firefox.exe"),
            ]
            for path in firefox_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    async def _init_browser(self) -> None:
        """Inisialisasi browser Playwright.
        
        Mendukung 3 mode session:
        - default: Buka browser baru setiap kali (tanpa session)
        - persistent: Browser menyimpan session (cookies, localStorage) ke folder lokal
        - connect: Connect ke browser Chrome/Edge yang sudah running (manual login)
        """
        from playwright.async_api import async_playwright
        
        # Support both 'playwright' and 'engine' config keys for backward compatibility
        playwright_config = self.config.get("playwright", {})
        engine_config = self.config.get("engine", {})
        # Merge: engine config is base, playwright config overrides (from UI)
        merged_playwright = {**engine_config, **playwright_config}
        
        browser_type = merged_playwright.get("browser", "chromium")
        headless = merged_playwright.get("headless", False)
        session_config = self.config.get("session", {})
        session_mode = session_config.get("mode", "default")
        
        # Terapkan performance mode ke slow_mo
        perf_config = self.config.get("performance", {})
        perf_mode = perf_config.get("mode", "normal")
        if perf_mode in ("turbo", "bulk"):
            slow_mo = perf_config.get(perf_mode, {}).get("slow_mo", 0)
        else:
            slow_mo = merged_playwright.get("slow_mo", 100)
        
        self._perf_mode = perf_mode
        self._perf_config = perf_config.get(perf_mode, {})
        
        # Ensure Playwright browsers are installed before launching (skip for connect mode)
        if session_mode != "connect":
            await self._ensure_browser_installed(browser_type)
        
        # Detect system browser (Chrome/Edge) untuk bundled mode
        executable_path = None
        if session_mode != "connect":
            executable_path = self._find_system_browser_executable(browser_type)
            if executable_path:
                self._log("INFO", f"System browser detected: {executable_path}")
            else:
                self._log("WARNING", "System browser not found. Playwright will try bundled browser.")
        
        self._playwright = await async_playwright().start()
        
        browser_launcher = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }.get(browser_type, self._playwright.chromium)
        
        viewport = merged_playwright.get("viewport", {"width": 1280, "height": 720})
        
        if session_mode == "connect":
            # Mode CONNECT: Sambungkan ke browser yang sudah running (Chrome/Edge)
            # Cara: chrome.exe --remote-debugging-port=9222
            connect_config = session_config.get("connect", {})
            ws_endpoint = connect_config.get("ws_endpoint", "http://localhost:9222")
            connect_browser_type = connect_config.get("browser", browser_type)
            
            self._log("INFO", f"Connecting to existing browser at {ws_endpoint}...")
            
            connect_launcher = {
                "chromium": self._playwright.chromium,
                "firefox": self._playwright.firefox,
                "webkit": self._playwright.webkit,
            }.get(connect_browser_type, self._playwright.chromium)
            
            try:
                self._browser = await connect_launcher.connect_over_cdp(ws_endpoint)
                self._page = await self._browser.new_page(viewport=viewport)
                self._log("INFO", f"Connected to existing browser. Pages tersedia: {len(await self._browser.pages())}")
            except Exception as e:
                self._log("ERROR", f"Gagal connect ke browser di {ws_endpoint}: {e}")
                self._log("INFO", "Fallback ke mode persistent context...")
                # Fallback: buka browser baru dengan persistent context
                session_mode = "persistent"
        
        if session_mode == "persistent" or (session_mode == "default" and not headless):
            # Mode PERSISTENT: Simpan session ke folder lokal
            # Login sekali, session tersimpan untuk eksekusi berikutnya
            persistent_config = session_config.get("persistent", {})
            user_data_dir = persistent_config.get("user_data_dir", "browser_session")
            login_url = persistent_config.get("login_url", "") or merged_playwright.get("start_url", "")
            login_timeout = persistent_config.get("login_timeout", 120)
            
            # Selalu resolve relative to app directory, bukan CWD
            app_dir = self._get_app_dir()
            if os.path.isabs(user_data_dir):
                user_data_dir_abs = user_data_dir
            else:
                user_data_dir_abs = os.path.join(app_dir, user_data_dir)
            user_data_dir_abs = os.path.abspath(user_data_dir_abs)
            os.makedirs(user_data_dir_abs, exist_ok=True)
            
            self._log("INFO", f"Using persistent session directory: {user_data_dir_abs}")
            
            # Cek apakah sudah ada session sebelumnya (ada file cookies/localStorage)
            has_existing_session = os.path.exists(os.path.join(user_data_dir_abs, "Default"))
            
            # Log status session
            if has_existing_session:
                self._log("INFO", "Existing browser session found. Attempting to reuse login state.")
            else:
                self._log("INFO", "No existing session found. Fresh browser session will be created.")
            
            # Gunakan launch_persistent_context untuk menyimpan session
            self._browser = None
            self._context = await browser_launcher.launch_persistent_context(
                user_data_dir=user_data_dir_abs,
                headless=headless,
                slow_mo=slow_mo,
                viewport=viewport,
                no_viewport=False,
                executable_path=executable_path,
            )
            
            # Ambil halaman yang sudah ada atau buat baru
            pages = self._context.pages
            if pages:
                self._page = pages[0]
            else:
                self._page = await self._context.new_page()
            
            if has_existing_session:
                self._log("SUCCESS", "Session tersimpan ditemukan! Anda TIDAK perlu login ulang.")
            else:
                self._log("INFO", "Session baru akan dibuat. Login sekali, session tersimpan otomatis.")
                if login_url:
                    self._log("INFO", f"Membuka halaman login: {login_url}")
                    try:
                        await self._page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                        self._log("WAITING", f"Silakan login manual dalam {login_timeout} detik...")
                        # Tunggu user login manual
                        if login_timeout > 0:
                            await asyncio.sleep(login_timeout)
                            self._log("INFO", "Timeout login selesai, melanjutkan eksekusi...")
                    except Exception as e:
                        self._log("WARNING", f"Gagal membuka login URL: {e}")
        
        if session_mode == "default":
            # Mode DEFAULT: Buka browser baru setiap kali (tanpa session persistence)
            self._browser = await browser_launcher.launch(
                headless=headless,
                slow_mo=slow_mo,
                executable_path=executable_path,
            )
            
            self._page = await self._browser.new_page(
                viewport=viewport,
            )
        
        self._log("INFO", f"Browser {browser_type} initialized (mode: {session_mode}, headless={headless})")
    
    async def _close_browser(self) -> None:
        """Tutup browser.
        
        Untuk mode persistent, context akan disimpan otomatis (cookies, localStorage, dll)
        sehingga session bisa digunakan kembali di eksekusi berikutnya.
        """
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
        
        # Untuk persistent context, kita close context (session akan disave otomatis)
        if hasattr(self, '_context') and self._context:
            try:
                await self._context.close()
                self._log("INFO", "Persistent context closed. Session saved for next execution.")
            except Exception:
                pass
        elif self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        
        # Beri waktu Chrome menulis profile ke disk (penting di Windows 11)
        import asyncio
        await asyncio.sleep(1.0)
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        
        self._page = None
        self._browser = None
        self._playwright = None
        if hasattr(self, '_context'):
            self._context = None
    
    async def _take_screenshot(self, step_id: str, is_error: bool = False) -> Optional[str]:
        """Ambil screenshot dan simpan ke file."""
        if not self._page:
            return None
        
        # Skip semua screenshot di mode turbo/bulk untuk performa maksimal
        perf_mode = getattr(self, '_perf_mode', 'normal')
        if perf_mode in ('turbo', 'bulk'):
            return None
        
        screenshots_dir = self.config.get("paths", {}).get("screenshots", "screenshots")
        if getattr(sys, 'frozen', False):
            screenshots_dir = os.path.join(self._get_app_dir(), screenshots_dir)
        else:
            screenshots_dir = os.path.abspath(screenshots_dir)
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
            self._log("ERROR", self._short(error_msg))
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
                    f"Step {step.id}: {result.status.value} - {self._short(result.message)}",
                )
                
                # Log detailed diagnostics jika ada
                if result.data:
                    if "url_changed" in result.data:
                        self._log("INFO", f"  URL: {result.data.get('pre_click_url', '')} -> {result.data.get('post_click_url', '')} (changed={result.data.get('url_changed')})")
                    if "element_info" in result.data and result.data["element_info"]:
                        info = result.data["element_info"]
                        self._log("INFO", f"  Element: count={info.get('count')}, visible={info.get('visible')}, bbox={info.get('bounding_box')}")
                    if result.data.get("js_errors"):
                        self._log("WARNING", f"  JS Errors after click: {result.data['js_errors']}")
                
                if result.status == ActionStatus.SUCCESS:
                    self._completed_count += 1
                    self._update_progress(step_index, total_steps, step.id, "success")
                elif result.status == ActionStatus.SKIPPED:
                    self._skipped_count += 1
                    self._update_progress(step_index, total_steps, step.id, "skipped")
                else:
                    self._failed_count += 1
                    self._update_progress(step_index, total_steps, step.id, "failed")
                
                return result
                
            except Exception as e:
                last_error = str(e)
                self._log("WARNING", f"Step {step.id} error (attempt {attempt+1}): {self._short(str(e))}")
                
                if attempt < max_retries:
                    continue
                
                # Screenshot error
                screenshot_path = await self._take_screenshot(step.id, is_error=True)
                self._failed_count += 1
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
                    self._log("ERROR", f"Data source validation errors: {self._short(errors)}")
                    return {"next_index": loop_start_index + 1}
                for row in source.read(config):
                    data_rows.append(row)
        except Exception as e:
            self._log("ERROR", f"Failed to read data source: {self._short(str(e))}")
            return {"next_index": loop_start_index + 1}
        
        if not data_rows:
            self._log("WARNING", f"No data found in data source, skipping loop {step.id}")
            return {"next_index": loop_start_index + 1}
        
        # Filter rows sesuai row_range config dari UI
        row_range = self.config.get("execution", {}).get("row_range", {"mode": "all"})
        original_count = len(data_rows)
        data_rows = self._filter_rows_by_range(data_rows, row_range)
        if row_range.get("mode") != "all":
            self._log("INFO", f"Row filter active: {original_count} -> {len(data_rows)} rows (mode={row_range.get('mode')})")
        
        # Tentukan loop body
        if step.children:
            loop_body = list(step.children)
        else:
            loop_body = workflow.steps[loop_start_index + 1:]
        
        total_iterations = len(data_rows)
        
        # ==================== LICENSE ENFORCEMENT ====================
        # Cek kuota untuk free mode
        processed_count = 0
        is_licensed = False
        remaining_quota = -1  # -1 = unlimited
        
        if self.license_manager:
            is_licensed = self.license_manager.is_licensed()
        
        if not is_licensed and self.usage_tracker:
            remaining_quota = self.usage_tracker.get_remaining_quota()
            if remaining_quota == 0:
                self._log("WARNING", "Free mode: Kuota harian 10 data telah tercapai. Eksekusi dibatalkan.")
                return {
                    "next_index": len(workflow.steps),
                    "quota_exceeded": True,
                    "message": "Kuota harian 10 data telah tercapai. Aktifkan lisensi untuk pemrosesan tanpa batas."
                }
            elif remaining_quota > 0:
                # Batasi jumlah data yang akan diproses
                total_iterations = min(total_iterations, remaining_quota)
                self._log("INFO", f"Free mode: Membatasi {total_iterations} dari {len(data_rows)} data (sisa kuota: {remaining_quota})")
        # ==================== END LICENSE ENFORCEMENT ====================
        
        self._log("INFO", f"Loop {step.id}: {total_iterations} rows from data source")
        
        for iteration, row in enumerate(data_rows):
            if not self._is_running:
                break
            
            # Check pause/stop
            while self._is_paused and self._is_running:
                await asyncio.sleep(0.5)
            
            if not self._is_running:
                break
            
            # Stop jika sudah mencapai batas kuota
            if processed_count >= total_iterations:
                break
            
            context.current_data = row.data
            self._log("INFO", f"Loop {iteration + 1}/{total_iterations}: {self._short_row(row.data)}")
            
            for body_step in loop_body:
                if not self._is_running:
                    break
                
                while self._is_paused and self._is_running:
                    await asyncio.sleep(0.5)
                
                if not self._is_running:
                    break
                
                if body_step.type == "parallel_group" and body_step.children:
                    child_results = await self._execute_parallel_group(body_step, context, loop_start_index + 1, total_iterations * len(loop_body))
                    for child_result in child_results:
                        results.append({
                            "step_id": child_result["step_id"],
                            "step_type": child_result["step_type"],
                            "step_label": child_result["step_label"],
                            "status": child_result["status"],
                            "message": child_result["message"],
                            "screenshot": child_result.get("screenshot"),
                            "error": child_result.get("error"),
                        })
                        if child_result["status"] == "failed":
                            if body_step.on_error == "stop":
                                self._log("ERROR", f"Workflow stopped due to error at step {child_result['step_id']}")
                                return {"should_stop": True}
                            elif body_step.on_error == "skip":
                                self._log("WARNING", f"Skipping error at step {child_result['step_id']}")
                                continue
                    self._completed_count = sum(1 for r in results if r["status"] == "success")
                    self._failed_count = sum(1 for r in results if r["status"] == "failed")
                    self._skipped_count = sum(1 for r in results if r["status"] == "skipped")
                    continue
                
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
                
                self._completed_count = sum(1 for r in results if r["status"] == "success")
                self._failed_count = sum(1 for r in results if r["status"] == "failed")
                self._skipped_count = sum(1 for r in results if r["status"] == "skipped")
                
                if result.status == ActionStatus.FAILED:
                    if body_step.on_error == "stop":
                        self._log("ERROR", f"Workflow stopped due to error at step {body_step.id}")
                        return {"should_stop": True}
                    elif body_step.on_error == "skip":
                        self._log("WARNING", f"Skipping error at step {body_step.id}")
                        continue
            
            processed_count += 1
        
        # ==================== UPDATE USAGE TRACKER ====================
        if not is_licensed and self.usage_tracker and processed_count > 0:
            self.usage_tracker.increment_usage(processed_count)
            self._log("INFO", f"Free mode: Usage updated. {processed_count} data processed today.")
        # ==================== END UPDATE USAGE TRACKER ====================
        
        # Jika tidak ada children, semua step setelah loop sudah dieksekusi
        if not step.children:
            return {"next_index": len(workflow.steps)}
        else:
            return {"next_index": loop_start_index + 1}
    
    async def _execute_parallel_group(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        step_index: int,
        total_steps: int,
    ) -> list:
        """
        Eksekusi parallel group - semua child steps dijalankan concurrent menggunakan asyncio.gather().
        
        Args:
            step: Parallel group step yang berisi children.
            context: Execution context.
            step_index: Index step (untuk progress).
            total_steps: Total step (untuk progress).
            
        Returns:
            List of result dicts.
        """
        if not step.children:
            self._log("WARNING", f"Parallel group {step.id} has no children, skipping")
            return []
        
        self._log("INFO", f"Executing parallel group: {step.label or step.id} ({len(step.children)} steps concurrent)")
        self._update_progress(step_index, total_steps, step.id, "running")
        
        # Cek pause/stop
        while self._is_paused and self._is_running:
            await asyncio.sleep(0.5)
        
        if not self._is_running:
            return []
        
        # Eksekusi semua child steps secara concurrent dengan stagger delay untuk hindari race condition DOM
        stagger_delay = step.params.get("stagger_delay", 200)  # ms antara setiap child start
        group_timeout_seconds = step.params.get("timeout", 30000) / 1000
        group_start = asyncio.get_event_loop().time()
        
        async def run_child_with_stagger(child_step: WorkflowStep, delay_ms: int) -> dict:
            elapsed = asyncio.get_event_loop().time() - group_start
            remaining = max(0.1, group_timeout_seconds - elapsed)
            
            if delay_ms > 0:
                await asyncio.sleep(min(delay_ms / 1000, remaining))
                elapsed = asyncio.get_event_loop().time() - group_start
                remaining = max(0.1, group_timeout_seconds - elapsed)
            
            if not self._is_running:
                return {
                    "step_id": child_step.id,
                    "step_type": child_step.type,
                    "step_label": child_step.label,
                    "status": "skipped",
                    "message": "Workflow stopped",
                }
            
            try:
                result = await asyncio.wait_for(
                    self._execute_step(child_step, context, step_index, total_steps),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                return {
                    "step_id": child_step.id,
                    "step_type": child_step.type,
                    "step_label": child_step.label,
                    "status": "failed",
                    "message": f"Timed out after {group_timeout_seconds}s",
                    "error": "Timeout",
                }
            
            return {
                "step_id": child_step.id,
                "step_type": child_step.type,
                "step_label": child_step.label,
                "status": result.status.value,
                "message": result.message,
                "screenshot": result.screenshot_path,
                "error": result.error,
            }
        
        # Jalankan semua child secara concurrent dengan stagger (masing-masing mulai dengan delay bertahap)
        tasks = []
        for i, child in enumerate(step.children):
            delay = i * stagger_delay  # child 0: 0ms, child 1: 200ms, child 2: 400ms, dst
            tasks.append(run_child_with_stagger(child, delay))
        
        child_results = await asyncio.gather(*tasks)
        
        # Cek apakah ada yang failed dan perlu stop
        for child_result in child_results:
            if child_result["status"] == "failed":
                # Cari step yang failed untuk cek on_error
                failed_step = next((s for s in step.children if s.id == child_result["step_id"]), None)
                if failed_step and failed_step.on_error == "skip":
                    child_result["status"] = "skipped"
                    self._failed_count -= 1
                    self._skipped_count += 1
                elif failed_step and failed_step.on_error == "stop":
                    self._log("ERROR", f"Parallel group stopped due to error at step {failed_step.id}")
                    return child_results
        
        self._update_progress(step_index, total_steps, step.id, "success")
        return child_results
    
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
        self._completed_count = 0
        self._failed_count = 0
        self._skipped_count = 0
        
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
            
            screenshots_dir = self.config.get("paths", {}).get("screenshots", "screenshots")
            logs_dir = self.config.get("paths", {}).get("logs", "logs")
            if getattr(sys, 'frozen', False):
                screenshots_dir = os.path.join(self._get_app_dir(), screenshots_dir)
                logs_dir = os.path.join(self._get_app_dir(), logs_dir)
            else:
                screenshots_dir = os.path.abspath(screenshots_dir)
                logs_dir = os.path.abspath(logs_dir)
            
            # Buat execution context
            self._context = ExecutionContext(
                page=self._page,
                browser=self._browser,
                workflow_id=workflow.id,
                execution_id=execution_id,
                screenshots_dir=screenshots_dir,
                logs_dir=logs_dir,
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
                
                # Special handling for parallel group
                if step.type == "parallel_group":
                    child_results = await self._execute_parallel_group(step, context, i + 1, total_steps)
                    for child_result in child_results:
                        results.append(child_result)
                        if child_result["status"] == "failed":
                            # Cek on_error dari parent parallel_group
                            if step.on_error == "stop":
                                self._log("ERROR", f"Parallel group stopped due to error at step {child_result['step_id']}")
                                should_stop = True
                                break
                            elif step.on_error == "skip":
                                self._log("WARNING", f"Skipping error at step {child_result['step_id']}")
                                continue
                    if should_stop:
                        break
                    self._completed_count = sum(1 for r in results if r["status"] == "success")
                    self._failed_count = sum(1 for r in results if r["status"] == "failed")
                    self._skipped_count = sum(1 for r in results if r["status"] == "skipped")
                    i += 1
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
                
                # Update counts from results so far
                self._completed_count = sum(1 for r in results if r["status"] == "success")
                self._failed_count = sum(1 for r in results if r["status"] == "failed")
                self._skipped_count = sum(1 for r in results if r["status"] == "skipped")
                
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