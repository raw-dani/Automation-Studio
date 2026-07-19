"""
Select2 Action - Menangani dropdown Select2 custom widget.
Langsung mengetik nilai yang diinginkan ke field search Select2,
tanpa perlu membuka dropdown atau mengklik opsi.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class Select2Action(BaseAction):
    """Mengisi dropdown Select2 dengan langsung mengetik nilai."""
    
    @property
    def name(self) -> str:
        return "select2"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",          # Selector elemen Select2 trigger/container
            "search_selector": "",   # Selector search input di dalam Select2
            "value": "",             # Nilai yang akan dipilih
            "wait_before": 500,
            "wait_after": 500,
            "timeout": 30000,
            "clear_first": True,
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
        search_selector = params.get("search_selector", "")
        value = params.get("value", "")
        wait_before = params.get("wait_before", 500)
        wait_after = params.get("wait_after", 500)
        timeout = params.get("timeout", 30000)
        clear_first = params.get("clear_first", True)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        search_selector = self._substitute_variables(search_selector, context)
        value = self._substitute_variables(value, context)
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Pastikan container Select2 terlihat
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            
            # Klik container untuk membuka dropdown
            await page.click(selector, timeout=timeout)
            await asyncio.sleep(0.3)
            
            # Tentukan search input selector
            target_input = search_selector or f"{selector} .select2-search__field"
            
            # Tunggu search input muncul
            await page.wait_for_selector(target_input, state="visible", timeout=timeout)
            
            # Clear jika diperlukan
            if clear_first:
                await page.fill(target_input, "")
                await asyncio.sleep(0.2)
            
            # Ketik nilai yang diinginkan
            await page.type(target_input, value, delay=50)
            await asyncio.sleep(0.5)
            
            # Tekan Enter untuk memilih opsi yang cocok
            await page.keyboard.press("Enter")
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih Select2 '{selector}' dengan nilai: {value}",
                data={"selector": selector, "search_selector": target_input, "value": value},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal pilih Select2 '{selector}' dengan nilai '{value}': {str(e)}",
                error=str(e),
            )
    
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
