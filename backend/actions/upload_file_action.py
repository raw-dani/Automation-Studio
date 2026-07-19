"""
Upload File Action - Upload file melalui input type file.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class UploadFileAction(BaseAction):
    """Upload file ke input type file. Mendukung absolute path."""
    
    @property
    def name(self) -> str:
        return "upload_file"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",
            "file_path": "",           # Absolute path file
            "wait_before": 500,
            "wait_after": 1000,
            "timeout": 30000,
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("selector"):
            errors.append("Parameter 'selector' wajib diisi.")
        if not params.get("file_path"):
            errors.append("Parameter 'file_path' wajib diisi.")
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
        file_path = params.get("file_path", "")
        wait_before = params.get("wait_before", 500)
        wait_after = params.get("wait_after", 1000)
        timeout = params.get("timeout", 30000)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        file_path = self._substitute_variables(file_path, context)
        
        play_selector = self._convert_selector(selector, selector_type)
        
        import asyncio
        import os
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Cek file exists
            if not os.path.exists(file_path):
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"File tidak ditemukan: {file_path}",
                )
            
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Set input files
            await page.set_input_files(play_selector, file_path)
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil upload file: {file_path}",
                data={"selector": selector, "file": file_path},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal upload file '{file_path}': {str(e)}",
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