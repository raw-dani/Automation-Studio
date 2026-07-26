"""
Radio Button Select Action - Memilih opsi radio button berdasarkan value/label/index.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


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

        # Performance config
        perf = context.config.get("performance", {})
        perf_mode = perf.get("mode", "normal")
        if perf_mode in ("turbo", "bulk"):
            wait_before = min(wait_before, perf.get(perf_mode, {}).get("wait_before_default", 0))
            wait_after = min(wait_after, perf.get(perf_mode, {}).get("wait_after_default", 0))
            timeout = min(timeout, perf.get(perf_mode, {}).get("parallel_group_timeout", 30000))

        value = self._substitute_variables(value, context)
        play_selector = self._convert_selector(selector, selector_type)

        import asyncio
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
        value_lower = value.lower().strip()
        if selector:
            radio_selectors = [
                f"{selector} input[type='radio'][value='{value_lower}']",
                f"{selector} input[type='radio'][value='{value}']",
            ]
        else:
            radio_selectors = [
                f"input[type='radio'][value='{value_lower}']",
                f"input[type='radio'][value='{value}']",
            ]

        for radio_selector in radio_selectors:
            try:
                element = await page.wait_for_selector(radio_selector, timeout=timeout)
                if element:
                    is_checked = await element.get_property("checked")
                    if not is_checked:
                        await element.click()
                    return True
            except Exception:
                continue
        return False

    async def _select_by_label(self, page, selector: str, value: str, timeout: int) -> bool:
        value_lower = value.lower().strip()
        label_mappings = {
            "individu": ["individu", "individual", "pribadi", "perorangan"],
            "bisnis": ["bisnis", "business", "perusahaan", "usaha", "company"],
            "laki-laki": ["laki-laki", "laki laki", "pria", "male", "laki"],
            "perempuan": ["perempuan", "wanita", "female", "wantita"],
            "ya": ["ya", "yes", "y", "true"],
            "tidak": ["tidak", "no", "n", "false"],
        }

        label_selectors = []
        if selector:
            label_selectors.extend([
                f"{selector} label:text-is('{value}')",
                f"{selector} label:text('{value}')",
                f"{selector} label:has-text('{value}')",
                f"{selector} label:has(input[type='radio'])",
            ])
        else:
            label_selectors.extend([
                f"label:text-is('{value}')",
                f"label:text('{value}')",
                f"label:has-text('{value}')",
                f"label:has(input[type='radio'])",
            ])

        for label_selector in label_selectors:
            try:
                elements = await page.query_selector_all(label_selector)
                for element in elements:
                    text = await element.text_content()
                    if text and value_lower in text.lower().strip():
                        radio = await element.query_selector("input[type='radio']")
                        if radio:
                            is_checked = await radio.get_property("checked")
                            if not is_checked:
                                await element.click()
                            return True
                        else:
                            await element.click()
                            return True
            except Exception:
                continue

        try:
            xpath = f"//label[contains(text(), '{value}')]"
            elements = await page.query_selector_all(f"xpath={xpath}")
            for element in elements:
                radio = await element.query_selector("input[type='radio']")
                if radio:
                    is_checked = await radio.get_property("checked")
                    if not is_checked:
                        await element.click()
                    return True
                else:
                    await element.click()
                    return True
        except Exception:
            pass

        if value_lower in label_mappings:
            aliases = label_mappings[value_lower]
            for alias in aliases:
                if alias == value_lower:
                    continue
                try:
                    if selector:
                        label_sel = f"{selector} label:has-text('{alias}')"
                    else:
                        label_sel = f"label:has-text('{alias}')"

                    element = await page.query_selector(label_sel)
                    if element:
                        radio = await element.query_selector("input[type='radio']")
                        if radio:
                            is_checked = await radio.get_property("checked")
                            if not is_checked:
                                await element.click()
                            return True
                        else:
                            await element.click()
                            return True
                except Exception:
                    continue

        return False

    async def _select_by_index(self, page, selector: str, value: str, timeout: int) -> bool:
        try:
            index = int(value)
            if selector:
                radio_selector = f"{selector} input[type='radio']"
            else:
                radio_selector = "input[type='radio']"

            radios = await page.query_selector_all(radio_selector)
            if 0 <= index < len(radios):
                is_checked = await radios[index].get_property("checked")
                if not is_checked:
                    await radios[index].click()
                return True
        except (ValueError, IndexError):
            pass
        return False

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
