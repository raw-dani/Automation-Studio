"""
Click Action - Melakukan klik pada elemen di halaman web.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


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
        
        import asyncio
        
        # Wait before
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Tunggu elemen muncul
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Tutup modal overlay yang mungkin menghalangi klik
            await self._dismiss_modal(page)
            
            # Klik elemen
            await page.click(play_selector, force=force, timeout=timeout)
            
            # Wait after
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil klik elemen: {selector}",
                data={"selector": selector, "selector_type": selector_type},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal klik elemen '{selector}': {str(e)}",
                error=str(e),
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
            ]
            for sel in dismissors:
                elements = await page.query_selector_all(sel)
                for el in elements:
                    visible = await el.is_visible()
                    if visible:
                        await el.click(force=True, timeout=1000)
                        await asyncio.sleep(0.1)
                        break
        except Exception:
            pass

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