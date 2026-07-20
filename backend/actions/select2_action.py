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
            "skip_if_empty": False,  # Skip step jika value kosong
            "add_new": False,        # Jika true, klik tombol add new jika opsi tidak ditemukan
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
        skip_if_empty = params.get("skip_if_empty", False)
        add_new = params.get("add_new", False)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        search_selector = self._substitute_variables(search_selector, context)
        value = self._substitute_variables(value, context)
        
        # Skip jika value kosong
        if skip_if_empty and not value:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message=f"Value kosong, melewati Select2 '{selector}'",
            )
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Build visible Select2 click target.
            # The native <select> is hidden by Select2; the visible trigger is
            # usually the adjacent `.select2-container .select2-selection--single`.
            adjacent_trigger = f"{selector} + .select2-container .select2-selection--single, {selector} + .select2-container"
            container_id = selector.replace("#", "select2-") + "-container"
            container_trigger = f"#{container_id} .select2-selection--single, #{container_id}"
            
            # Prefer adjacent container, fallback to generated container id
            click_target = f"{adjacent_trigger}, {container_trigger}, {selector}"
            
            # Pastikan target terlihat
            await page.wait_for_selector(click_target, state="visible", timeout=timeout)
            
            # Klik trigger visible. Use locator().last to avoid the hidden <select> when multiple elements match.
            await page.locator(click_target).last.click(timeout=timeout)
            await asyncio.sleep(0.3)
            
            # Wait for dropdown to open and search field to appear
            search_input_selector = ".select2-container--open .select2-search__field"
            target_input = search_selector or search_input_selector
            
            await page.wait_for_selector(target_input, state="visible", timeout=timeout)
            
            # Clear jika diperlukan
            if clear_first:
                await page.fill(target_input, "")
                await asyncio.sleep(0.2)
            
            # Ketik nilai yang diinginkan
            await page.type(target_input, value, delay=50)
            await asyncio.sleep(0.5)
            
            # Cek apakah opsi muncul di dropdown
            option_selector = f".select2-results__option:has-text('{value}')"
            option_exists = await page.locator(option_selector).count() > 0
            
            if not option_exists and add_new:
                # Cek apakah ada tombol add new (+)
                add_btn_selector = f"#{selector.replace('#', '')} + .input-group-btn .btn-modal, #{selector.replace('#', '')} .btn-modal, .select2-container + .input-group-btn .btn-modal"
                add_btn = page.locator(add_btn_selector).first
                
                if await add_btn.count() > 0:
                    # Klik tombol add new
                    add_href = await add_btn.get_attribute("data-href")
                    from loguru import logger
                    logger.info(f"Option '{value}' not found, opening add new modal: {add_href}")
                    
                    await add_btn.click()
                    await asyncio.sleep(1)
                    
                    # Coba isi modal form
                    modal_filled = await self._fill_add_modal(page, value, timeout)
                    if not modal_filled:
                        return ActionResult(
                            status=ActionStatus.FAILED,
                            message=f"Gagal mengisi modal tambah '{value}'",
                            error="Modal fill failed",
                        )
                    
                    # Submit modal (biasanya tombol submit atau enter)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)
                    
                    # Tunggu opsi baru muncul dan pilih
                    await page.wait_for_selector(option_selector, state="visible", timeout=timeout)
                    await page.click(option_selector, timeout=timeout)
                else:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Opsi '{value}' tidak ditemukan dan tidak ada tombol add new.",
                        error=f"Option not found: {value}",
                    )
            elif not option_exists:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Opsi '{value}' tidak ditemukan dalam dropdown.",
                    error=f"Option not found: {value}",
                )
            else:
                # Opsi ditemukan, klik untuk memilih
                await page.click(option_selector, timeout=timeout)
            
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
    
    async def _fill_add_modal(self, page, value: str, timeout: int = 30000) -> bool:
        """
        Coba isi modal tambah data baru.
        Modal biasanya memiliki field nama/name dan tombol submit.
        """
        try:
            # Tunggu modal muncul
            await page.wait_for_selector(".modal, .view_modal", state="visible", timeout=timeout)
            await asyncio.sleep(0.5)
            
            # Cari input field di modal
            modal_input_selectors = [
                ".modal input[name='name']",
                ".modal input[name='title']",
                ".modal input[type='text']",
                ".view_modal input[name='name']",
                ".view_modal input[type='text']",
            ]
            
            for input_selector in modal_input_selectors:
                input_field = page.locator(input_selector).first
                if await input_field.count() > 0:
                    await input_field.fill(value)
                    await asyncio.sleep(0.3)
                    return True
            
            return False
            
        except Exception as e:
            self._log("WARNING", f"Failed to fill add modal: {e}")
            return False
    
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
