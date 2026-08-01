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

        selector = self._substitute_variables(selector, context)
        search_selector = self._substitute_variables(search_selector, context)
        value = self._substitute_variables(value, context)

        if skip_if_empty and not value:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message=f"Value kosong, melewati Select2 '{selector}'",
            )

        import asyncio

        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)

        try:
            adjacent_trigger = f"{selector} + .select2-container .select2-selection--single, {selector} + .select2-container"
            container_id = selector.replace("#", "select2-") + "-container"
            container_trigger = f"#{container_id} .select2-selection--single, #{container_id}"

            click_target = f"{adjacent_trigger}, {container_trigger}"

            await page.wait_for_selector(click_target, state="visible", timeout=timeout)

            await page.locator(click_target).first.click(timeout=timeout)
            await asyncio.sleep(0.5)

            results_selector = ".select2-dropdown, .select2-container--open .select2-results, .select2-dropdown--below .select2-results, .select2-dropdown--above .select2-results"
            await page.wait_for_selector(results_selector, state="visible", timeout=timeout)
            await asyncio.sleep(0.3)

            search_input_selector = search_selector or ".select2-container--open .select2-search__field, .select2-dropdown .select2-search__field"
            target_input = search_selector or search_input_selector

            search_count = await page.locator(target_input).count()
            if search_count > 0 and await page.locator(target_input).first.is_visible():
                if clear_first:
                    await page.fill(target_input, "")
                    await asyncio.sleep(0.2)

                await page.type(target_input, value, delay=80)
                await asyncio.sleep(0.6)

                option_selector = await self._find_option(page, value, timeout=timeout)

                if option_selector:
                    await page.locator(option_selector).first.click(timeout=timeout)
                elif add_new:
                    add_result = await self._try_add_new(page, selector, value, timeout)
                    if not add_result:
                        return ActionResult(
                            status=ActionStatus.FAILED,
                            message=f"Opsi '{value}' tidak ditemukan setelah search.",
                            error=f"Option not found: {value}",
                        )
                else:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Opsi '{value}' tidak ditemukan dalam dropdown setelah search.",
                        error=f"Option not found: {value}",
                    )
            else:
                option_selector = await self._find_option(page, value, timeout=timeout)

                if option_selector:
                    await page.locator(option_selector).first.click(timeout=timeout)
                elif add_new:
                    add_result = await self._try_add_new(page, selector, value, timeout)
                    if not add_result:
                        return ActionResult(
                            status=ActionStatus.FAILED,
                            message=f"Opsi '{value}' tidak ditemukan dalam dropdown.",
                            error=f"Option not found: {value}",
                        )
                else:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Opsi '{value}' tidak ditemukan dan tidak ada search field.",
                        error=f"Option not found: {value}",
                    )

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

    async def _find_option(self, page, value: str, timeout: int = 5000):
        """Cari opsi Select2: exact match dulu, lalu fallback partial match (contains)."""
        exact_selectors = [
            ".select2-container--open .select2-results__option:has-text('%s')" % value,
            ".select2-dropdown .select2-results__option:has-text('%s')" % value,
        ]
        for sel in exact_selectors:
            if await page.locator(sel).count() > 0:
                return sel

        partial_xpath = "//li[contains(@class,'select2-results__option') and contains(., '%s')]" % value
        if await page.locator(f"xpath={partial_xpath}").count() > 0:
            return f"xpath={partial_xpath}"

        return None
    
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
    
    async def _try_add_new(self, page, selector: str, value: str, timeout: int = 30000) -> bool:
        """
        Coba klik tombol add new (+) jika opsi tidak ditemukan.
        Returns True if add new succeeded and option was selected.
        """
        try:
            # Cek apakah ada tombol add new (+)
            add_btn_selector = f"#{selector.replace('#', '')} + .input-group-btn .btn-modal, #{selector.replace('#', '')} .btn-modal, .select2-container + .input-group-btn .btn-modal"
            add_btn = page.locator(add_btn_selector).first
            
            if await add_btn.count() == 0:
                return False
            
            # Klik tombol add new
            add_href = await add_btn.get_attribute("data-href")
            from loguru import logger
            logger.info(f"Option '{value}' not found, opening add new modal: {add_href}")
            
            await add_btn.click()
            await asyncio.sleep(1)
            
            # Coba isi modal form
            modal_filled = await self._fill_add_modal(page, value, timeout)
            if not modal_filled:
                return False
            
            # Submit modal (biasanya tombol submit atau enter)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            
            option_selectors = [
                ".select2-container--open .select2-results__option:has-text('%s')" % value,
                ".select2-dropdown .select2-results__option:has-text('%s')" % value,
            ]
            for opt_sel in option_selectors:
                option_count = await page.locator(opt_sel).count()
                if option_count > 0:
                    await page.locator(opt_sel).first.click(timeout=timeout)
                    return True
            
            return False
            
        except Exception as e:
            self._log("WARNING", f"Failed to add new option: {e}")
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
