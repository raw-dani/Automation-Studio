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
            "wait_before": 500,      # ms
            "wait_after": 500,       # ms
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
        wait_before = params.get("wait_before", 500)
        wait_after = params.get("wait_after", 500)
        force = params.get("force", False)
        timeout = params.get("timeout", 30000)
        
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