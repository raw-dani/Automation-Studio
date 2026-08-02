"""
Click Action - Melakukan klik pada elemen di halaman web.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus
import asyncio


class ClickAction(BaseAction):
    """Melakukan klik pada elemen berdasarkan CSS selector, XPath, atau teks."""
    
    @property
    def name(self) -> str:
        return "click"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",  # css, xpath, text
            "wait_before": 0,        # ms (dikurangi dari 500ms untuk performa)
            "wait_after": 0,         # ms (dikurangi dari 500ms untuk performa)
            "force": False,          # force click even if not visible
            "timeout": 30000,        # ms
            "wait_for_load_state": "none",  # none, domcontentloaded, load, networkidle
            "use_evaluate": False,           # Jika True, gunakan page.evaluate() untuk klik bypass selector engine
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("selector"):
            errors.append("Parameter 'selector' wajib diisi.")
        if params.get("selector_type") not in ("css", "xpath", "text"):
            errors.append("Parameter 'selector_type' harus 'css', 'xpath', atau 'text'.")
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )
        
        selector = params.get("selector", "")
        selector_type = params.get("selector_type", "css")
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
        force = params.get("force", False)
        timeout = params.get("timeout", 10000)
        wait_for_load_state = params.get("wait_for_load_state", "none")
        use_evaluate = params.get("use_evaluate", False)
        
        # Performance config
        perf = context.config.get("performance", {})
        perf_mode = perf.get("mode", "normal")
        if perf_mode in ("turbo", "bulk"):
            wait_before = min(wait_before, perf.get(perf_mode, {}).get("wait_before_default", 0))
            wait_after = min(wait_after, perf.get(perf_mode, {}).get("wait_after_default", 0))
            timeout = min(timeout, perf.get(perf_mode, {}).get("parallel_group_timeout", 30000))
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        
        # Konversi selector
        play_selector = self._convert_selector(selector, selector_type)
        
        # Wait before
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Capture pre-click state for diagnostics
            pre_click_url = page.url
            pre_click_title = await page.title()
            element_info = {}
            
            if not use_evaluate:
                try:
                    locator = page.locator(play_selector).first
                    element_info = {
                        "selector": selector,
                        "selector_type": selector_type,
                        "play_selector": play_selector,
                        "count": await locator.count(),
                        "visible": await locator.is_visible() if await locator.count() > 0 else None,
                    }
                    if await locator.count() > 0:
                        try:
                            bbox = await locator.bounding_box()
                            element_info["bounding_box"] = bbox
                        except Exception:
                            element_info["bounding_box"] = None
                except Exception as e:
                    element_info["locator_error"] = str(e)
            
            if use_evaluate:
                result = await self._evaluate_click(page, selector, selector_type, force, timeout, wait_for_load_state)
                if result.status == ActionStatus.SUCCESS:
                    result.data = result.data or {}
                    result.data.update({
                        "pre_click_url": pre_click_url,
                        "pre_click_title": pre_click_title,
                        "element_info": element_info,
                        "method": "evaluate",
                    })
                return result
            
            # Tunggu elemen muncul
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Tutup modal overlay yang mungkin menghalangi klik
            await self._dismiss_modal(page)
            
            await self._safe_click(page, play_selector, force, timeout, wait_for_load_state)
            
            # Capture post-click state
            post_click_url = page.url
            post_click_title = await page.title()
            
            # Wait after
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            # Check for JS errors after click
            js_errors = []
            try:
                js_errors = await page.evaluate("""() => {
                    return window.__playwright_js_errors || [];
                }""")
            except Exception:
                pass
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil klik elemen: {selector}",
                data={
                    "selector": selector,
                    "selector_type": selector_type,
                    "pre_click_url": pre_click_url,
                    "post_click_url": post_click_url,
                    "url_changed": pre_click_url != post_click_url,
                    "pre_click_title": pre_click_title,
                    "post_click_title": post_click_title,
                    "element_info": element_info,
                    "js_errors": js_errors,
                },
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal klik elemen '{selector}': {str(e)}",
                error=str(e),
                data={
                    "selector": selector,
                    "selector_type": selector_type,
                    "pre_click_url": pre_click_url,
                    "element_info": element_info,
                },
            )
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        """Konversi selector ke format Playwright."""
        if selector_type == "xpath":
            return f"xpath={selector}"
        elif selector_type == "text":
            return f"text={selector}"
        else:  # css
            return selector

    async def _dismiss_modal(self, page):
        """Tutup modal overlay yang mungkin menghalangi klik."""
        try:
            dismissors = [
                ".modal.show .btn-close",
                ".modal.show .close",
                ".modal.in .btn-close",
                ".modal.in .close",
                ".contact_modal .close",
                ".contact_modal .btn-close",
                ".modal-backdrop",
            ]
            for sel in dismissors:
                try:
                    elements = await page.query_selector_all(sel)
                    for el in elements:
                        visible = await el.is_visible()
                        if visible:
                            await el.click(force=True, timeout=1000)
                            await asyncio.sleep(0.15)
                            break
                except Exception:
                    continue

            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.1)
            except Exception:
                pass
        except Exception:
            pass

    async def _dismiss_modal_js(self, page):
        """Tutup modal overlay menggunakan JavaScript."""
        try:
            await page.evaluate("""() => {
                document.querySelectorAll('.modal.in, .modal.show').forEach(m => {
                    m.classList.remove('in', 'show');
                    m.style.display = 'none';
                });
                document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
                document.body.classList.remove('modal-open');
            }""")
        except Exception:
            pass

    async def _safe_click(self, page, play_selector, force, timeout, wait_for_load_state):
        """Klik elemen dengan retry jika tertutup modal overlay."""
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            attempts += 1
            try:
                await self._dismiss_modal(page)
                await self._dismiss_modal_js(page)
                await page.click(play_selector, force=force, timeout=timeout)
                if wait_for_load_state != "none":
                    await page.wait_for_load_state(wait_for_load_state, timeout=timeout)
                return
            except Exception as e:
                error_msg = str(e).lower()
                if "intercept" in error_msg or "blocked" in error_msg or "overlay" in error_msg or "modal" in error_msg:
                    await self._dismiss_modal(page)
                    await self._dismiss_modal_js(page)
                    await asyncio.sleep(0.3)
                    continue
                raise
        await page.evaluate("""(sel) => {
            const el = document.querySelector(sel);
            if (el) {
                el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
            }
        }""", play_selector)
        if wait_for_load_state != "none":
            try:
                await page.wait_for_load_state(wait_for_load_state, timeout=timeout)
            except Exception:
                pass
    
    async def _evaluate_click(self, page, selector: str, selector_type: str, force: bool, timeout: int, wait_for_load_state: str, pre_click_url: str = "", pre_click_title: str = "", element_info: dict = None):
        """Klik elemen menggunakan page.evaluate() untuk bypass selector engine Playwright."""
        element_info = element_info or {}
        try:
            if selector_type == "xpath":
                js_code = """(args) => {
                    const [xpath, force] = args;
                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    const el = result.singleNodeValue;
                    if (el) {
                        if (force) {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                        }
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        return true;
                    }
                    return false;
                }"""
                clicked = await page.evaluate(js_code, [selector, force])
                if not clicked:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Elemen tidak ditemukan dengan XPath: {selector}",
                        error="Element not found via evaluate",
                        data={"pre_click_url": pre_click_url, "element_info": element_info},
                    )
            else:
                js_code = """(args) => {
                    const [sel, force] = args;
                    const el = document.querySelector(sel);
                    if (el) {
                        if (force) {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                        }
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        return true;
                    }
                    return false;
                }"""
                clicked = await page.evaluate(js_code, [selector, force])
                if not clicked:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Elemen tidak ditemukan dengan selector: {selector}",
                        error="Element not found via evaluate",
                        data={"pre_click_url": pre_click_url, "element_info": element_info},
                    )
            
            if wait_for_load_state != "none":
                try:
                    await page.wait_for_load_state(wait_for_load_state, timeout=timeout)
                except Exception:
                    pass
            
            post_click_url = page.url
            post_click_title = await page.title()
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil klik elemen via evaluate: {selector}",
                data={
                    "selector": selector,
                    "selector_type": selector_type,
                    "method": "evaluate",
                    "pre_click_url": pre_click_url,
                    "post_click_url": post_click_url,
                    "url_changed": pre_click_url != post_click_url,
                    "pre_click_title": pre_click_title,
                    "post_click_title": post_click_title,
                    "element_info": element_info,
                },
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal klik elemen via evaluate '{selector}': {str(e)}",
                error=str(e),
                data={"pre_click_url": pre_click_url, "element_info": element_info},
            )
    
    def _substitute_variables(self, text: str, context: ExecutionContext) -> str:
        """Substitusi variable {{data.field}} dengan nilai dari context."""
        if "{{" not in text:
            return text
        
        result = text
        for key, value in context.current_data.items():
            result = result.replace(f"{{{{data.{key}}}}}", str(value))
        
        # Juga substitusi dari variables
        for key, value in context.variables.items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
        
        return result