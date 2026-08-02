"""
Input Text Action - Mengetik teks ke input field di halaman web.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class InputTextAction(BaseAction):
    """Mengetik teks ke dalam input field berdasarkan selector."""
    
    @property
    def name(self) -> str:
        return "input_text"
    
    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",  # css, xpath
            "value": "",
            "clear_first": True,     # Clear input sebelum mengetik
            "type_delay": 50,        # ms delay between keystrokes
            "use_fill": False,       # Jika True, gunakan fill() langsung tanpa type() delay
            "wait_before": 0,        # Dikurangi dari 500ms untuk performa
            "wait_after": 0,         # Dikurangi dari 500ms untuk performa
            "timeout": 30000,
            "skip_if_empty": False,  # Skip step jika value kosong
            "use_evaluate": False,   # Jika True, gunakan page.evaluate() untuk bypass pattern validation
            "date_format": None,     # Jika diisi, convert value dari format Excel ke format web. Contoh: "dd|MM|yyyy|dd/MM/yyyy"
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
        clear_first = params.get("clear_first", True)
        type_delay = params.get("type_delay", 0)
        use_fill = params.get("use_fill", False)
        use_evaluate = params.get("use_evaluate", False)
        date_format = params.get("date_format", None)
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 10000)
        skip_if_empty = params.get("skip_if_empty", False)
        
        # Performance config
        perf = context.config.get("performance", {})
        perf_mode = perf.get("mode", "normal")
        if perf_mode in ("turbo", "bulk"):
            wait_before = min(wait_before, perf.get(perf_mode, {}).get("wait_before_default", 0))
            wait_after = min(wait_after, perf.get(perf_mode, {}).get("wait_after_default", 0))
            timeout = min(timeout, perf.get(perf_mode, {}).get("parallel_group_timeout", 30000))
            if perf.get(perf_mode, {}).get("use_fill", False):
                use_fill = True
        
        # Variable substitution
        selector = self._substitute_variables(selector, context)
        value = self._substitute_variables(value, context)
        
        # Date format conversion
        if date_format and value:
            value = self._convert_date(value, date_format)
        
        # Skip jika value kosong
        if skip_if_empty and not value:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message=f"Value kosong, melewati input '{selector}'",
            )
        
        # Konversi selector
        play_selector = self._convert_selector(selector, selector_type)
        
        import asyncio
        
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
        
        try:
            visible_selector = f"{play_selector} >> visible=true"
            await page.wait_for_selector(visible_selector, timeout=timeout)
            
            locator = page.locator(play_selector).filter(visible=True).first
            
            # Type text - use_fill untuk performa maksimal (langsung isi tanpa simulasi)
            # fill() sudah otomatis replace seluruh nilai, tidak perlu clear_first terpisah
            if use_fill:
                await locator.fill(value)
            elif use_evaluate:
                await page.evaluate("""(args) => {
                    const [sel, val] = args;
                    const el = document.querySelector(sel);
                    if (el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }""", [play_selector, value])
            else:
                # Clear input jika diperlukan (hanya untuk mode type simulation)
                if clear_first:
                    await locator.fill("")
                
                if type_delay > 0:
                    await locator.type(value, delay=type_delay)
                else:
                    await locator.fill(value)
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Berhasil input teks ke: {selector}",
                data={"selector": selector, "value": value},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal input teks ke '{selector}': {str(e)}",
                error=str(e),
            )
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector
    
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
    
    def _convert_date(self, value: str, date_format: str) -> str:
        """Convert date format dari Excel ke format web.
        
        Args:
            value: Nilai tanggal dari Excel, contoh "05|02|1976"
            date_format: Format string "input_format->output_format"
                         Contoh: "dd|MM|yyyy->dd/MM/yyyy"
        
        Returns:
            Tanggal dalam format web, contoh "05/02/1976"
        """
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
                # Find next separator or end
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