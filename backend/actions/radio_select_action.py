"""
Radio Button Select Action - Memilih opsi radio button berdasarkan value/label/index.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus
import asyncio
import re


class RadioSelectAction(BaseAction):
    """Memilih radio button berdasarkan value, label, atau index."""

    @property
    def name(self) -> str:
        return "radio_select"

    @property
    def description(self) -> str:
        return "Pilih opsi radio button"

    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",
            "value": "",
            "select_by": "label",
            "wait_before": 0,
            "wait_after": 0,
            "timeout": 10000,
        }

    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("value"):
            errors.append("Parameter 'value' wajib diisi.")
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
        value = params.get("value", "")
        select_by = params.get("select_by", "label")
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 10000)

        perf = context.config.get("performance", {})
        perf_mode = perf.get("mode", "normal")
        if perf_mode in ("turbo", "bulk"):
            wait_before = min(wait_before, perf.get(perf_mode, {}).get("wait_before_default", 0))
            wait_after = min(wait_after, perf.get(perf_mode, {}).get("wait_after_default", 0))
            timeout = min(timeout, perf.get(perf_mode, {}).get("parallel_group_timeout", 30000))

        value = self._substitute_variables(value, context)
        play_selector = self._convert_selector(selector, selector_type)

        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)

        try:
            if select_by == "label":
                success = await self._select_by_label(page, play_selector, value, timeout)
            elif select_by == "value":
                success = await self._select_by_value(page, play_selector, value, timeout)
            elif select_by == "index":
                success = await self._select_by_index(page, play_selector, value, timeout)
            else:
                success = await self._select_by_value(page, play_selector, value, timeout)
                if not success:
                    success = await self._select_by_label(page, play_selector, value, timeout)

            if not success:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Gagal pilih radio button '{value}' dengan selector '{selector}'",
                    error=f"Could not find radio button with {select_by}='{value}' using selector '{selector}'",
                )

            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil pilih radio button '{value}'",
                data={"selector": selector, "value": value, "by": select_by},
            )

        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal pilih radio button '{value}': {str(e)}",
                error=str(e),
            )

    async def _select_by_value(self, page, selector: str, value: str, timeout: int) -> bool:
        value_str = value.strip()
        candidates = [value_str, value_str.lower(), value_str.title(), value_str.upper()]

        if selector:
            base = f"{selector} input[type='radio']"
        else:
            base = "input[type='radio']"

        try:
            await page.wait_for_selector(base, state="attached", timeout=timeout)
        except Exception:
            return False

        for candidate in candidates:
            for val in [candidate, candidate.lower(), candidate.strip("'\"")]:
                try:
                    targeted = f"{base}[value='{val}']"
                    el = await page.wait_for_selector(targeted, timeout=2000)
                    if el:
                        is_checked = await el.get_property("checked")
                        if not is_checked:
                            await el.click()
                        return True
                except Exception:
                    continue

        radios = await page.query_selector_all(base)
        target_norm = re.sub(r'\s+', '', value_str.lower())
        for radio in radios:
            try:
                rv = await radio.get_attribute("value") or ""
                rv_norm = re.sub(r'\s+', '', rv.lower())
                if rv_norm == target_norm or rv_norm in target_norm or target_norm in rv_norm:
                    is_checked = await radio.get_property("checked")
                    if not is_checked:
                        await radio.click()
                    return True
            except Exception:
                continue

        return False

    async def _select_by_label(self, page, selector: str, value: str, timeout: int) -> bool:
        value_str = value.strip()
        value_lower = value_str.lower()

        if selector:
            base_radio = f"{selector} input[type='radio']"
            scoped = True
        else:
            base_radio = "input[type='radio']"
            scoped = False

        try:
            await page.wait_for_selector(base_radio, state="attached", timeout=timeout)
        except Exception:
            return False

        alias_groups = {
            value_lower: [value_lower, value_str, value_str.title(), value_str.upper()],
        }
        extra = {
            "individu": ["individu", "individual", "pribadi", "perorangan"],
            "bisnis": ["bisnis", "business", "perusahaan", "usaha", "company"],
            "laki-laki": ["laki-laki", "laki laki", "pria", "male"],
            "perempuan": ["perempuan", "wanita", "female"],
            "ya": ["ya", "yes", "y", "true", "1"],
            "tidak": ["tidak", "no", "n", "false", "0"],
        }
        for key in extra:
            if key not in alias_groups:
                alias_groups[key] = extra[key]

        for key_label, aliases in alias_groups.items():
            if key_label != value_lower and value_lower not in key_label and key_label not in value_lower:
                continue
            for alias in aliases:
                alias_lower = alias.lower()
                for pattern in [alias, alias_lower, alias.title()]:
                    try:
                        if scoped:
                            label_sel = f"{selector} label:has-text('{pattern}')"
                        else:
                            label_sel = f"label:has-text('{pattern}')"
                        elements = await page.query_selector_all(label_sel)
                        for el in elements:
                            txt = await el.text_content() or ""
                            if alias_lower in txt.lower():
                                radio = await el.query_selector("input[type='radio']")
                                if radio:
                                    is_checked = await radio.get_property("checked")
                                    if not is_checked:
                                        await el.click()
                                    return True
                                await el.click()
                                return True
                    except Exception:
                        continue

        try:
            xpath = f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]"
            elements = await page.query_selector_all(f"xpath={xpath}")
            for el in elements:
                radio = await el.query_selector("input[type='radio']")
                if radio:
                    is_checked = await radio.get_property("checked")
                    if not is_checked:
                        await el.click()
                    return True
                await el.click()
                return True
        except Exception:
            pass

        try:
            radios = await page.query_selector_all(base_radio)
            for radio in radios:
                radio_value = await radio.get_attribute("value") or ""
                radio_value_lower = radio_value.lower().strip()
                if self._normalize_match(radio_value, value_str) or self._normalize_match(radio_value_lower, value_lower):
                    is_checked = await radio.get_property("checked")
                    if not is_checked:
                        await radio.click()
                    return True
                id_attr = await radio.get_attribute("id") or ""
                if id_attr:
                    for_js = f"document.querySelector('label[for=\"{id_attr}\"]')"
                    label_el = await page.query_selector(for_js)
                    if label_el:
                        label_text = await label_el.text_content() or ""
                        if self._normalize_match(label_text, value_str):
                            is_checked = await radio.get_property("checked")
                            if not is_checked:
                                await radio.click()
                            return True
                aria = await radio.get_attribute("aria-label") or ""
                if aria and self._normalize_match(aria, value_str):
                    is_checked = await radio.get_property("checked")
                    if not is_checked:
                        await radio.click()
                    return True
        except Exception:
            pass

        try:
            await page.evaluate("""(sel, val) => {
                const radios = document.querySelectorAll(sel);
                const target = val.trim().toLowerCase().replace(/[\\s\\-_.,;:!@#$%^&*()]+/g, '');
                radios.forEach(r => {
                    const rv = (r.getAttribute('value') || '').trim().toLowerCase().replace(/[\\s\\-_.,;:!@#$%^&*()]+/g, '');
                    if (rv === target || target.includes(rv) || rv.includes(target)) {
                        if (!r.checked) r.click();
                        r.setAttribute('data-matched', 'true');
                    }
                });
            }""", base_radio, value_str)
            await asyncio.sleep(0.2)
            checked = await page.evaluate("""(sel) => {
                const r = document.querySelector(sel + '[data-matched="true"]');
                return r ? r.checked : false;
            }""", base_radio)
            if checked:
                try:
                    await page.evaluate("""(sel) => {
                        document.querySelectorAll(sel).forEach(r => r.removeAttribute('data-matched'));
                    }""", base_radio)
                except Exception:
                    pass
                return True
        except Exception:
            pass

        return False

    async def _select_by_index(self, page, selector: str, value: str, timeout: int) -> bool:
        try:
            index = int(value.strip())
            if selector:
                base = f"{selector} input[type='radio']"
            else:
                base = "input[type='radio']"

            radios = await page.query_selector_all(base)
            if 0 <= index < len(radios):
                is_checked = await radios[index].get_property("checked")
                if not is_checked:
                    await radios[index].click()
                return True
        except (ValueError, IndexError):
            pass
        return False

    def _normalize_match(self, text: str, target: str) -> bool:
        t = re.sub(r'[\s\-_.,;:!@#$%^&*()]+', '', text.lower().strip())
        rg = re.sub(r'[\s\-_.,;:!@#$%^&*()]+', '', target.lower().strip())
        return t == rg or rg in t or t in rg

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