"""
Select Dropdown Action - Memilih opsi dari dropdown/select element.
"""

import asyncio
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
            "wait_before": 0,         # ms (dikurangi dari 500ms untuk performa)
            "wait_after": 0,          # ms (dikurangi dari 500ms untuk performa)
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
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
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
        select_value = self._substitute_variables(select_value, context)
        
        play_selector = self._convert_selector(selector, selector_type)
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            play_selector = self._convert_selector(selector, selector_type)
            
            # Wait for selector with visibility check
            visible_selector = f"{play_selector} >> visible=true"
            await page.wait_for_selector(visible_selector, timeout=timeout)
            
            # Select berdasarkan metode
            if select_by == "label":
                await page.select_option(visible_selector, label=select_value)
            elif select_by == "value":
                await page.select_option(visible_selector, value=select_value)
            elif select_by == "index":
                await page.select_option(visible_selector, index=int(select_value))
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih '{select_value}' dari dropdown '{selector}'",
                data={"selector": selector, "value": select_value, "by": select_by},
            )
            
        except Exception as e:
            # Fallback: jika ini Select2 widget, coba interaksi via Select2 UI
            if "select2-hidden-accessible" in selector or await self._is_select2(page, play_selector):
                fallback = await self._select2_fallback(page, play_selector, select_by, select_value, timeout, wait_after)
                if fallback.status == ActionStatus.SUCCESS:
                    return fallback
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Gagal pilih dropdown '{selector}': {str(e)}",
                    error=str(e),
                )
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal pilih dropdown '{selector}': {str(e)}",
                error=str(e),
            )
    
    async def _is_select2(self, page, selector: str) -> bool:
        """Deteksi apakah element adalah Select2 widget."""
        try:
            el = await page.query_selector(selector)
            if not el:
                return False
            cls = await el.get_attribute("class") or ""
            return "select2-hidden-accessible" in cls or "select2" in cls
        except Exception:
            return False
    
    async def _select2_fallback(self, page, selector, select_by, select_value, timeout, wait_after):
        """Fallback interaksi untuk Select2 widget."""
        try:
            adjacent_trigger = f"{selector} + .select2-container .select2-selection--single, {selector} + .select2-container"
            container_id = selector.replace("#", "select2-") + "-container"
            container_trigger = f"#{container_id} .select2-selection--single, #{container_id}"
            click_target = f"{adjacent_trigger}, {container_trigger}"
            
            await page.locator(click_target).first.wait_for(state="visible", timeout=timeout)
            await page.locator(click_target).first.click(timeout=timeout)
            await asyncio.sleep(0.5)
            
            results_selector = ".select2-dropdown, .select2-container--open .select2-results, .select2-dropdown--below .select2-results, .select2-dropdown--above .select2-results"
            await page.wait_for_selector(results_selector, state="visible", timeout=timeout)
            await asyncio.sleep(0.3)
            
            # Build candidate selectors based on select_by
            candidates = []
            if select_by == "label":
                candidates.append(f".select2-container--open .select2-results__option:has-text('{select_value}'), .select2-dropdown .select2-results__option:has-text('{select_value}')")
                candidates.append(f".select2-container--open .select2-results__option[data-value='{select_value}'], .select2-dropdown .select2-results__option[data-value='{select_value}']")
            elif select_by == "value":
                candidates.append(f".select2-container--open .select2-results__option[data-value='{select_value}'], .select2-dropdown .select2-results__option[data-value='{select_value}']")
                candidates.append(f".select2-container--open .select2-results__option:has-text('{select_value}'), .select2-dropdown .select2-results__option:has-text('{select_value}')")
            else:
                candidates.append(f".select2-container--open .select2-results__option:has-text('{select_value}'), .select2-dropdown .select2-results__option:has-text('{select_value}')")
                candidates.append(f".select2-container--open .select2-results__option[data-value='{select_value}'], .select2-dropdown .select2-results__option[data-value='{select_value}']")
            
            option_selector = ", ".join(candidates)
            count = await page.locator(option_selector).count()
            if count > 0:
                await page.locator(option_selector).first.click(timeout=timeout)
            else:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Opsi '{select_value}' tidak ditemukan di Select2 dropdown.",
                    error="Option not found",
                )
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih '{select_value}' dari Select2 dropdown '{selector}'",
                data={"selector": selector, "value": select_value, "by": select_by, "fallback": "select2"},
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Select2 fallback gagal: {str(e)}",
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