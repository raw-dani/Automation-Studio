"""
Parallel Group Action - Mengeksekusi child steps secara paralel (concurrent).
Semua child steps dijalankan bersamaan, dan group selesai ketika semua child selesai atau timeout.
"""

import asyncio
from backend.actions.base_action import (
    BaseAction, ExecutionContext, ActionResult, ActionStatus
)


class ParallelGroupAction(BaseAction):
    """Menjalankan beberapa child steps secara paralel dalam satu group."""

    @property
    def name(self) -> str:
        return "parallel_group"

    @property
    def description(self) -> str:
        return "Jalankan beberapa action secara paralel dalam satu group"

    @property
    def default_params(self) -> dict:
        return {
            "timeout": 30000,       # Maximum time in ms untuk semua child selesai
            "stagger_delay": 200,   # Delay antar start tiap child (ms)
            "on_error": "stop",     # skip, stop, continue_all
        }

    def validate_params(self, params: dict) -> list[str]:
        errors = []
        timeout = params.get("timeout", 30000)
        if not isinstance(timeout, (int, float)) or timeout < 0:
            errors.append("Parameter 'timeout' harus berupa angka positif (ms).")
        return errors

    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        """
        Execute all child steps concurrently.

        Note: Actual parallel execution logic is handled by the engine.
        This action only validates and returns configuration for the engine.
        """
        timeout = params.get("timeout", 30000)
        stagger_delay = params.get("stagger_delay", 200)
        on_error = params.get("on_error", "stop")

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Parallel Group: {len(getattr(context, '_children', []))} steps, timeout={timeout}ms",
            data={
                "timeout": timeout,
                "stagger_delay": stagger_delay,
                "on_error": on_error,
                "parallel": True,
            },
        )

