"""
Select Action - Memilih nilai dari daftar opsi yang tersedia.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class SelectAction(BaseAction):
    """Memilih satu nilai dari daftar opsi."""
    
    @property
    def name(self) -> str:
        return "select"
    
    @property
    def default_params(self) -> dict:
        return {
            "options": [],      # List of options: ["option1", "option2", ...]
            "selected": "",     # Selected option value
            "variable_name": "", # Optional: store result in context variable
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        options = params.get("options", [])
        if not options:
            errors.append("Parameter 'options' wajib diisi dengan minimal 1 pilihan.")
        if not isinstance(options, list):
            errors.append("Parameter 'options' harus berupa list.")
        return errors
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        options = params.get("options", [])
        selected = params.get("selected", "")
        variable_name = params.get("variable_name", "")
        
        if not options:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada opsi yang tersedia.",
                error="Empty options list",
            )
        
        # If selected is empty, use first option
        if not selected:
            selected = options[0]
        
        # If selected is not in options, fail
        if selected not in options:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Opsi '{selected}' tidak ditemukan dalam daftar: {options}",
                error=f"Invalid option: {selected}",
            )
        
        # Store in variable if specified
        if variable_name:
            context.variables[variable_name] = selected
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Berhasil memilih: {selected}",
            data={
                "options": options,
                "selected": selected,
                "variable_name": variable_name,
            },
        )
