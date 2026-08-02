"""
Input Date Action - Mengisi field tanggal dengan format conversion.
Mendukung date picker widget dengan direct JS value assignment.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class InputDateAction(BaseAction):
    """Mengisi field tanggal dengan konversi format dan bypass date picker widget."""
    
    @property
    def name(self) -> str:
        return "input_date"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",
            "value": "",
            "date_format": "dd|MM|yyyy->dd/MM/yyyy",
            "clear_first": True,
            "use_evaluate": True,
            "wait_before": 0,
            "wait_after": 0,
            "timeout": 30000,
            "skip_if_empty": False,
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
        selector_type = params.get("selector_type", "css")
        value = params.get("value", "")
        date_format = params.get("date_format", "dd|MM|yyyy->dd/MM/yyyy")
        clear_first = params.get("clear_first", True)
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 30000)
        skip_if_empty = params.get("skip_if_empty", False)
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        value = self._substitute_variables(value, context)
        
        # Skip jika value kosong
        if skip_if_empty and not value:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message=f"Value kosong, melewati input tanggal '{selector}'",
            )
        
        # Date format conversion
        if value and date_format:
            value = self._convert_date(value, date_format)
        
        # Konversi selector
        play_selector = self._convert_selector(selector, selector_type)
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            # Tunggu elemen muncul
            await page.wait_for_selector(play_selector, timeout=timeout)
            
            # Capture pre-fill state
            pre_value = await page.evaluate(f"() => document.querySelector('{play_selector}')?.value || ''")
            
            # Gunakan evaluate untuk bypass date picker widget
            js_code = """(args) => {
                const [sel, val, clear] = args;
                const el = document.querySelector(sel);
                if (!el) return false;
                
                if (clear) {
                    el.value = '';
                }
                
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                
                return true;
            }"""
            success = await page.evaluate(js_code, [play_selector, value, clear_first])
            
            if not success:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Gagal set tanggal: elemen tidak ditemukan",
                    error="Element not found",
                )
            
            # Verify nilai ter-set
            post_value = await page.evaluate(f"() => document.querySelector('{play_selector}')?.value || ''")
            
            # Wait after
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil input tanggal ke: {selector}",
                data={
                    "selector": selector,
                    "value": value,
                    "pre_value": pre_value,
                    "post_value": post_value,
                    "date_format": date_format,
                },
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal input tanggal ke '{selector}': {str(e)}",
                error=str(e),
            )
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector
    
    def _convert_date(self, value: str, date_format: str) -> str:
        """Convert date format dari Excel ke format web."""
        if not date_format or "->" not in date_format:
            return value
        
        parts = date_format.split("->", 1)
        if len(parts) != 2:
            return value
        
        input_fmt, output_fmt = parts
        
        # Parse input format menjadi tokens
        input_tokens = []
        i = 0
        while i < len(input_fmt):
            if i + 1 < len(input_fmt) and input_fmt[i] == 'M' and input_fmt[i+1] == 'M':
                input_tokens.append('MM')
                i += 2
            elif i + 1 < len(input_fmt) and input_fmt[i] == 'd' and input_fmt[i+1] == 'd':
                input_tokens.append('dd')
                i += 2
            elif i + 3 < len(input_fmt) and input_fmt[i:i+4] == 'yyyy':
                input_tokens.append('yyyy')
                i += 4
            else:
                input_tokens.append(input_fmt[i])
                i += 1
        
        # Parse output format menjadi tokens
        output_tokens = []
        i = 0
        while i < len(output_fmt):
            if i + 1 < len(output_fmt) and output_fmt[i] == 'M' and output_fmt[i+1] == 'M':
                output_tokens.append('MM')
                i += 2
            elif i + 1 < len(output_fmt) and output_fmt[i] == 'd' and output_fmt[i+1] == 'd':
                output_tokens.append('dd')
                i += 2
            elif i + 3 < len(output_fmt) and output_fmt[i:i+4] == 'yyyy':
                output_tokens.append('yyyy')
                i += 4
            else:
                output_tokens.append(output_fmt[i])
                i += 1
        
        # Extract values dari input string
        input_str = value
        values = {}
        pos = 0
        for token in input_tokens:
            if token in ('dd', 'MM', 'yyyy'):
                sep = None
                for s in ['/', '-', '.', '|']:
                    idx = input_str.find(s, pos)
                    if idx != -1:
                        sep = s
                        break
                if sep:
                    val = input_str[pos:idx]
                    pos = idx + 1
                else:
                    val = input_str[pos:]
                    pos = len(input_str)
                values[token] = val
        
        # Build output string
        result = []
        for token in output_tokens:
            if token in values:
                result.append(values[token])
            else:
                result.append(token)
        
        return ''.join(result)
    
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
