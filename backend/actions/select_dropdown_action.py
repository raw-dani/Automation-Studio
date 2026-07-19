"""
Select Dropdown Action - Memilih opsi dari dropdown/select element.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class SelectDropdownAction(BaseAction):
    """Memilih opsi dari dropdown berdasarkan label, value, atau index."""
    
    @property
    def name(self) -> str:
        return "select_dropdown"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",
            "select_by": "label",     # label, value, index
            "select_value": "",
            "wait_before": 500,
            "wait_after": 500,
            "timeout": 30000,
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("selector"):
            errors.append("Parameter 'selector' wajib diisi.")
        if not params.get("select_value"):
            errors.append("Parameter 'select_value' wajib diisi.")
        if params.get("select_by") not in ("label", "value", "index"):
            errors.append("Parameter 'select_by' harus 'label', 'value', atau 'index'.")
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
        select_by = params.get("select_by", "label")
        select_value = params.get("select_value", "")
        wait_before = params.get("wait_before", 500)
        wait_after = params.get("wait_after", 500)
        timeout = params.get("timeout", 30000)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        select_value = self._substitute_variables(select_value, context)
        
        play_selector = self._convert_selector(selector, selector_type)
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Select berdasarkan metode
            if select_by == "label":
                await page.select_option(play_selector, label=select_value)
            elif select_by == "value":
                await page.select_option(play_selector, value=select_value)
            elif select_by == "index":
                await page.select_option(play_selector, index=int(select_value))
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih '{select_value}' dari dropdown '{selector}'",
                data={"selector": selector, "value": select_value, "by": select_by},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal pilih dropdown '{selector}': {str(e)}",
                error=str(e),
            )
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector
    
    def _substitute_variables(self, text: str, context: ExecutionContext) -> str:
        if "{{" not in text:
            return text
        result = text
        for key, value in context.current_data.items():
            result = result.replace(f"{{{{data.{key}}}}}", str(value))
        for key, value in context.variables.items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
        return result