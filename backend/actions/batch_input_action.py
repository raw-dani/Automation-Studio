"""
Batch Input Action - Mengisi banyak form field sekaligus via JavaScript.
Lebih cepat daripada input_text individual karena menghindari round-trip Playwright.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class BatchInputAction(BaseAction):
    """Mengisi banyak form field sekaligus menggunakan JavaScript."""
    
    @property
    def name(self) -> str:
        return "batch_input"
    
    @property
    def description(self) -> str:
        return "Mengisi banyak form field sekaligus via JavaScript untuk kecepatan maksimal."
    
    @property
    def default_params(self) -> dict:
        return {
            "fields": {},             # Dict {selector: value}
            "clear_first": True,      # Clear semua field sebelum diisi
            "wait_after": 100,        # Jeda setelah semua field diisi (ms)
            "timeout": 10000,         # Timeout untuk JS evaluate
            "trigger_events": True,   # Trigger input/change event setelah isi
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        fields = params.get("fields", {})
        if not fields or not isinstance(fields, dict):
            errors.append("Parameter 'fields' wajib diisi sebagai dict {selector: value}.")
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )
        
        fields = params.get("fields", {})
        clear_first = params.get("clear_first", True)
        wait_after = params.get("wait_after", 100)
        timeout = params.get("timeout", 10000)
        trigger_events = params.get("trigger_events", True)
        
        if not fields:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Parameter 'fields' kosong.",
            )
        
        # Substitute variables in values
        processed_fields = {}
        for selector, value in fields.items():
            if isinstance(value, str):
                processed_fields[selector] = self._substitute_variables(value, context)
            else:
                processed_fields[selector] = value
        
        try:
            result = await page.evaluate("""(args) => {
                const { fields, clearFirst, triggerEvents } = args;
                const results = [];
                
                for (const [selector, value] of Object.entries(fields)) {
                    try {
                        const el = document.querySelector(selector);
                        if (!el) {
                            results.push({ selector, status: 'not_found', error: 'Element not found' });
                            continue;
                        }
                        
                        const tagName = el.tagName.toLowerCase();
                        const type = (el.type || '').toLowerCase();
                        
                        if (clearFirst) {
                            if (tagName === 'input' && (type === 'text' || type === 'email' || type === 'password' || type === 'number' || type === 'tel' || type === 'url' || type === 'search')) {
                                el.value = '';
                            } else if (tagName === 'textarea') {
                                el.value = '';
                            }
                        }
                        
                        if (tagName === 'input' && (type === 'checkbox' || type === 'radio')) {
                            const boolVal = String(value).toLowerCase() === 'true' || String(value) === '1' || String(value) === 'yes';
                            el.checked = boolVal;
                        } else if (tagName === 'select') {
                            el.value = String(value);
                        } else if (tagName === 'textarea') {
                            el.value = String(value);
                        } else if (tagName === 'input' && (type === 'text' || type === 'email' || type === 'password' || type === 'number' || type === 'tel' || type === 'url' || type === 'search' || type === 'hidden')) {
                            el.value = String(value);
                        } else {
                            el.value = String(value);
                        }
                        
                        if (triggerEvents) {
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        
                        results.push({ selector, status: 'success', tagName, type });
                    } catch (e) {
                        results.push({ selector, status: 'error', error: e.message });
                    }
                }
                
                return results;
            }""", {
                "fields": processed_fields,
                "clearFirst": clear_first,
                "triggerEvents": trigger_events,
            }, timeout=timeout)
            
            failed = [r for r in result if r.get("status") != "success"]
            if failed:
                error_details = "; ".join([f"{r['selector']}: {r.get('error', r['status'])}" for r in failed[:5]])
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Batch input gagal pada {len(failed)} field: {error_details}",
                    error="Field fill failed",
                    data={"results": result},
                )
            
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            filled_count = len([r for r in result if r.get("status") == "success"])
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Batch input berhasil mengisi {filled_count} field.",
                data={"results": result},
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Batch input gagal: {str(e)}",
                error=str(e),
            )
    
    def _substitute_variables(self, text: str, context: ExecutionContext) -> str:
        if "{{" not in text:
            return text
        result = text
        for key, value in context.current_data.items():
            result = result.replace(f"{{{{data.{key}}}}}", str(value))
        for key, value in context.variables.items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
        return result
