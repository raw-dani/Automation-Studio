"""
Wait Action - Menunggu dengan berbagai kondisi.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class WaitAction(BaseAction):
    """Menunggu selama waktu tertentu atau hingga kondisi terpenuhi."""
    
    @property
    def name(self) -> str:
        return "wait"
    
    @property
    def default_params(self) -> dict:
        return {
            "wait_type": "fixed",     # fixed, until_visible, until_hidden, until_selector
            "duration": 1000,         # ms (untuk fixed)
            "selector": "",           # selector untuk until_visible/hidden
            "selector_type": "css",   # css, xpath
            "timeout": 30000,         # max wait time
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        wait_type = params.get("wait_type", "fixed")
        
        if wait_type not in ("fixed", "until_visible", "until_hidden", "until_selector"):
            errors.append("Parameter 'wait_type' tidak valid.")
        
        if wait_type == "fixed" and not params.get("duration", 0):
            errors.append("Parameter 'duration' wajib diisi untuk wait_type 'fixed'.")
        
        if wait_type in ("until_visible", "until_hidden", "until_selector"):
            if not params.get("selector"):
                errors.append(f"Parameter 'selector' wajib diisi untuk wait_type '{wait_type}'.")
        
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        wait_type = params.get("wait_type", "fixed")
        duration = params.get("duration", 1000)
        timeout = params.get("timeout", 30000)
        
        try:
            if wait_type == "fixed":
                await self._sleep_with_check(duration / 1000, context)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Menunggu selama {duration}ms",
                    data={"duration": duration},
                )
            
            elif wait_type == "until_visible":
                selector = params.get("selector", "")
                selector_type = params.get("selector_type", "css")
                play_selector = self._convert_selector(selector, selector_type)
                
                await self._wait_for_selector_with_check(page, play_selector, state="visible", timeout=timeout, context=context)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Elemen '{selector}' muncul",
                    data={"selector": selector},
                )
            
            elif wait_type == "until_hidden":
                selector = params.get("selector", "")
                selector_type = params.get("selector_type", "css")
                play_selector = self._convert_selector(selector, selector_type)
                
                await self._wait_for_selector_with_check(page, play_selector, state="hidden", timeout=timeout, context=context)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Elemen '{selector}' menghilang",
                    data={"selector": selector},
                )
            
            elif wait_type == "until_selector":
                selector = params.get("selector", "")
                selector_type = params.get("selector_type", "css")
                play_selector = self._convert_selector(selector, selector_type)
                
                await self._wait_for_selector_with_check(page, play_selector, timeout=timeout, context=context)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Elemen '{selector}' tersedia",
                    data={"selector": selector},
                )
            
            else:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Wait type '{wait_type}' tidak dikenal.",
                )
                
        except asyncio.CancelledError:
            return ActionResult(
                status=ActionStatus.SKIPPED,
                message="Workflow stopped",
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal menunggu: {str(e)}",
                error=str(e),
            )
    
    async def _sleep_with_check(self, duration: float, context: ExecutionContext) -> None:
        """Sleep dengan periodic check untuk pause/stop."""
        interval = 0.5
        end_time = asyncio.get_event_loop().time() + duration
        while True:
            if not context.is_running:
                raise asyncio.CancelledError("Workflow stopped")
            if context.is_paused:
                await asyncio.sleep(interval)
                continue
            remaining = end_time - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            await asyncio.sleep(min(interval, remaining))
    
    async def _wait_for_selector_with_check(self, page, selector: str, state: str = None, timeout: int = 30000, context: ExecutionContext = None) -> None:
        """Wait for selector dengan periodic check untuk pause/stop."""
        interval = 0.5
        timeout_seconds = timeout / 1000
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if not context.is_running:
                raise asyncio.CancelledError("Workflow stopped")
            if context.is_paused:
                await asyncio.sleep(interval)
                continue
            
            try:
                if state:
                    await page.wait_for_selector(selector, state=state, timeout=int(interval * 1000))
                else:
                    await page.wait_for_selector(selector, timeout=int(interval * 1000))
                return
            except Exception:
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    raise
                await asyncio.sleep(interval)
    
    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector