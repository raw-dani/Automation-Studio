"""
Navigate Action - Membuka URL di halaman browser.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class NavigateAction(BaseAction):
    """Membuka URL tertentu di halaman browser."""
    
    @property
    def name(self) -> str:
        return "navigate"
    
    @property
    def default_params(self) -> dict:
        return {
            "url": "",
            "wait_until": "domcontentloaded",  # domcontentloaded, load, networkidle
            "timeout": 30000,  # ms
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("url"):
            errors.append("Parameter 'url' wajib diisi.")
        wait_until = params.get("wait_until", "domcontentloaded")
        if wait_until not in ("domcontentloaded", "load", "networkidle"):
            errors.append("Parameter 'wait_until' harus 'domcontentloaded', 'load', atau 'networkidle'.")
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )
        
        url = params.get("url", "")
        wait_until = params.get("wait_until", "domcontentloaded")
        timeout = params.get("timeout", 30000)
        
        # Variable substitution
        url = self._substitute_variables(url, context)
        
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil buka URL: {url}",
                data={"url": url, "wait_until": wait_until},
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal buka URL '{url}': {str(e)}",
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
