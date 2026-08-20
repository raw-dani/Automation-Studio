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
                await page.select_option(visible_selector, label=select_value, timeout=timeout)
            elif select_by == "value":
                await page.select_option(visible_selector, value=select_value, timeout=timeout)
            elif select_by == "index":
                await page.select_option(visible_selector, index=int(select_value), timeout=timeout)
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih '{select_value}' dari dropdown '{selector}'",
                data={"selector": selector, "value": select_value, "by": select_by},
            )
            
        except Exception as e:
            fallback_attempted = False
            fallback_error = str(e)
            fallback_result = None
            
            try:
                is_select2 = False
                if "select2-hidden-accessible" in selector or "select2" in selector:
                    is_select2 = True
                else:
                    is_select2 = await self._is_select2(page, play_selector)
                
                if is_select2:
                    fallback_attempted = True
                    fallback_result = await self._select2_fallback(page, play_selector, select_by, select_value, timeout, wait_after)
                    if fallback_result.status == ActionStatus.SUCCESS:
                        return fallback_result
                    fallback_error = fallback_result.message
            except Exception:
                pass
            
            msg = f"Gagal pilih dropdown '{selector}': {fallback_error}"
            if fallback_attempted:
                msg = f"Gagal pilih dropdown '{selector}': native select gagal ({str(e)}), Select2 fallback juga gagal ({fallback_error})"
            return ActionResult(
                status=ActionStatus.FAILED,
                message=msg,
                error=str(e) if not fallback_attempted else fallback_error,
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
            base_id = selector.replace("#", "")
            container_id = f"select2-{base_id}-container"
            
            # Strategy A: Klik trigger via Playwright menggunakan ID container yang diprediksi
            trigger_selectors = [
                f"#{container_id} .select2-selection--single",
                f"#{container_id}",
                f"{selector} + .select2-container .select2-selection--single",
                f"{selector} + .select2-container",
            ]
            
            clicked = False
            for sel in trigger_selectors:
                try:
                    loc = page.locator(sel).first
                    await loc.wait_for(state="visible", timeout=3000)
                    await loc.click(timeout=timeout)
                    clicked = True
                    break
                except Exception:
                    continue
            
            if not clicked:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message="Select2 trigger tidak ditemukan.",
                    error="Trigger not found",
                )
            
            await asyncio.sleep(1.0)
            
            # Buka dropdown via JS jika belum terbuka
            await page.evaluate("""() => {
                const containers = document.querySelectorAll('.select2-container');
                for (const c of containers) {
                    if (!c.classList.contains('select2-container--open')) {
                        const evt = new MouseEvent('mousedown', { bubbles: true });
                        c.dispatchEvent(evt);
                    }
                }
            }""")
            await asyncio.sleep(0.5)
            
            # Tunggu dropdown terbuka
            results_selector = ".select2-dropdown, .select2-container--open .select2-results, .select2-dropdown--below .select2-results, .select2-dropdown--above .select2-results"
            try:
                await page.wait_for_selector(results_selector, state="visible", timeout=timeout)
            except Exception:
                pass
            await asyncio.sleep(0.5)
            
            # Cari opsi via Playwright selector
            candidates = []
            if select_by == "label":
                candidates.append(f"#{container_id} .select2-results__option:has-text('{select_value}')")
                candidates.append(f".select2-container--open .select2-results__option:has-text('{select_value}')")
            elif select_by == "value":
                candidates.append(f"#{container_id} .select2-results__option[data-value='{select_value}']")
                candidates.append(f".select2-container--open .select2-results__option[data-value='{select_value}']")
            else:
                candidates.append(f"#{container_id} .select2-results__option:has-text('{select_value}')")
                candidates.append(f".select2-container--open .select2-results__option:has-text('{select_value}')")
            
            option_selector = ", ".join(candidates)
            count = await page.locator(option_selector).count()
            if count > 0:
                await page.locator(option_selector).first.click(timeout=timeout)
                if wait_after > 0:
                    await asyncio.sleep(wait_after / 1000)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Berhasil pilih '{select_value}' dari Select2 dropdown '{selector}'",
                    data={"selector": selector, "value": select_value, "by": select_by, "fallback": "select2"},
                )
            
            # Strategy B: JS fallback - cari dan klik opsi via JavaScript
            js_result = await page.evaluate("""(args) => {
                const searchText = args.value.toLowerCase();
                const container = document.querySelector('#' + args.containerId);
                const scope = container || document;
                const options = scope.querySelectorAll('.select2-results__option, .select2-dropdown .select2-results__option');
                for (const opt of options) {
                    const text = (opt.textContent || '').trim().toLowerCase();
                    const dataValue = (opt.getAttribute('data-value') || '').toLowerCase();
                    if (text.includes(searchText) || text === searchText || dataValue === searchText || dataValue.includes(searchText)) {
                        opt.scrollIntoView({block: 'center'});
                        opt.click();
                        return {found: true, text: opt.textContent.trim()};
                    }
                }
                const available = Array.from(options).map(o => o.textContent.trim()).filter(t => t);
                return {found: false, available: available.slice(0, 20)};
            }""", {"value": select_value, "containerId": container_id})
            
            if js_result.get("found"):
                if wait_after > 0:
                    await asyncio.sleep(wait_after / 1000)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Berhasil pilih '{select_value}' dari Select2 dropdown '{selector}' via JS",
                    data={"selector": selector, "value": select_value, "by": select_by, "fallback": "select2_js"},
                )
            
            # Strategy C: Direct Select2 API via jQuery
            js_direct = await page.evaluate("""(args) => {
                const searchText = args.value;
                const selectEl = document.querySelector(args.selector);
                if (!selectEl || typeof jQuery === 'undefined') return {found: false, reason: 'no_jquery'};
                
                try {
                    const $select = jQuery(selectEl);
                    if (!$select.hasClass('select2-hidden-accessible')) return {found: false, reason: 'not_select2'};
                    
                    $select.val(searchText).trigger('change.select2');
                    return {found: true, method: 'jquery_change'};
                } catch (e) {
                    return {found: false, reason: e.message};
                }
            }""", {"selector": selector, "value": select_value})
            
            if js_direct.get("found"):
                if wait_after > 0:
                    await asyncio.sleep(wait_after / 1000)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Berhasil pilih '{select_value}' dari Select2 dropdown '{selector}' via jQuery trigger",
                    data={"selector": selector, "value": select_value, "by": select_by, "fallback": "select2_jquery"},
                )
            
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Opsi '{select_value}' tidak ditemukan di Select2 dropdown. Reason: {js_direct.get('reason', 'unknown')}. Available: {js_result.get('available', [])}",
                error="Option not found",
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Select2 fallback gagal: {str(e)}",
                error=str(e),
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