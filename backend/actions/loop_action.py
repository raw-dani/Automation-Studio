"""
Loop Action - Melakukan iterasi berdasarkan data source atau jumlah iterasi.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class LoopAction(BaseAction):
    """Melakukan perulangan untuk mengeksekusi child steps."""
    
    @property
    def name(self) -> str:
        return "loop"
    
    @property
    def default_params(self) -> dict:
        return {
            "loop_type": "count",     # count, data_source, while
            "count": 1,               # Jumlah iterasi (untuk count)
            "data_key": "",           # Key data dari current_data (untuk data_source)
            "condition": "",          # Condition (untuk while)
            "max_iterations": 100,    # Safety limit
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        loop_type = params.get("loop_type", "count")
        if loop_type not in ("count", "data_source", "while"):
            errors.append("Parameter 'loop_type' harus 'count', 'data_source', atau 'while'.")
        if loop_type == "count" and not params.get("count", 0):
            errors.append("Parameter 'count' wajib diisi untuk loop_type 'count'.")
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        """
        Loop action - mengeksekusi child steps berulang kali.
        Note: Logic looping dihandle oleh engine, action ini hanya return config.
        """
        loop_type = params.get("loop_type", "count")
        count = params.get("count", 1)
        max_iterations = params.get("max_iterations", 100)
        
        if count > max_iterations:
            count = max_iterations
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Loop: {count}x ({loop_type})",
            data={
                "loop_type": loop_type,
                "count": count,
                "max_iterations": max_iterations,
            },
        )