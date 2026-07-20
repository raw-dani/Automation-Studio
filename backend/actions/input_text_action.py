"""
Input Text Action - Mengetik teks ke input field di halaman web.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class InputTextAction(BaseAction):
    """Mengetik teks ke dalam input field berdasarkan selector."""
    
    @property
    def name(self) -> str:
        return "input_text"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",  # css, xpath
            "value": "",
            "clear_first": True,     # Clear input sebelum mengetik
            "type_delay": 50,        # ms delay between keystrokes
            "wait_before": 500,
            "wait_after": 500,
            "timeout": 30000,
            "skip_if_empty": False,  # Skip step jika value kosong
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("selector"):
            errors.append("Parameter 'selector' wajib diisi.")
        if not params.get("value"):
            errors.append("Parameter 'value' wajib diisi.")
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
        value = params.get("value", "")
        clear_first = params.get("clear_first", True)
        type_delay = params.get("type_delay", 50)
        wait_before = params.get("wait_before", 500)
        wait_after = params.get("wait_after", 500)
        timeout = params.get("timeout", 30000)
        skip_if_empty = params.get("skip_if_empty", False)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        value = self._substitute_variables(value, context)
        
        # Skip jika value kosong
        if skip_if_empty and not value:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message=f"Value kosong, melewati input '{selector}'",
            )
        
        # Konversi selector
        play_selector = self._convert_selector(selector, selector_type)
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Tunggu elemen muncul
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Clear input jika diperlukan
            if clear_first:
                await page.fill(play_selector, "")
            
            # Type text dengan delay (simulasi ketikan manusia)
            if type_delay > 0:
                await page.type(play_selector, value, delay=type_delay)
            else:
                await page.fill(play_selector, value)
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil input teks ke: {selector}",
                data={"selector": selector, "value": value},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal input teks ke '{selector}': {str(e)}",
                error=str(e),
            )
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector
    
    def _substitute_variables(self, text: str, context: ExecutionContext) -> str:
        """Substitusi variable {{data.field}} dengan nilai dari context."""
        if "{{" not in text:
            return text
        
        result = text
        for key, value in context.current_data.items():
            result = result.replace(f"{{{{data.{key}}}}}", str(value))
        
        for key, value in context.variables.items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
        
        return result