"""
If Else Action - Conditional branching dalam workflow.
"""

from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class IfElseAction(BaseAction):
    """Percabangan bersyarat. Evaluasi kondisi dan jalankan branch yang sesuai."""
    
    @property
    def name(self) -> str:
        return "if_else"
    
    @property
    def default_params(self) -> dict:
        return {
            "condition": {
                "variable": "",
                "operator": "equals",     # equals, not_equals, contains, greater_than, less_than, empty, not_empty
                "value": "",
            },
        }
    
    def validate_params(self, params: dict) -> list[str]:
        errors = []
        condition = params.get("condition", {})
        if not condition.get("variable"):
            errors.append("Parameter 'condition.variable' wajib diisi.")
        if condition.get("operator") not in ("equals", "not_equals", "contains", "greater_than", "less_than", "empty", "not_empty"):
            errors.append("Parameter 'condition.operator' tidak valid.")
        return errors
    
    def _evaluate_condition(self, condition: dict, context: ExecutionContext) -> bool:
        """Evaluasi kondisi dengan data dari context."""
        variable = condition.get("variable", "")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value", "")
        
        # Variable substitution
        variable = self._substitute_variables(variable, context)
        expected_value = self._substitute_variables(expected_value, context)
        
        # Dapatkan nilai aktual
        actual_value = self._get_variable_value(variable, context)
        
        # Evaluasi
        if operator == "equals":
            return str(actual_value) == str(expected_value)
        elif operator == "not_equals":
            return str(actual_value) != str(expected_value)
        elif operator == "contains":
            return str(expected_value) in str(actual_value)
        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "empty":
            return not actual_value or str(actual_value).strip() == ""
        elif operator == "not_empty":
            return bool(actual_value) and str(actual_value).strip() != ""
        
        return False
    
    def _get_variable_value(self, variable: str, context: ExecutionContext) -> any:
        """Dapatkan nilai variable dari context."""
        # Cek dari current_data
        if variable.startswith("data."):
            key = variable[5:]  # Remove "data." prefix
            return context.current_data.get(key, "")
        
        # Cek dari variables
        if variable.startswith("variables."):
            key = variable[10:]  # Remove "variables." prefix
            return context.variables.get(key, "")
        
        # Cek langsung
        return context.variables.get(variable, context.current_data.get(variable, ""))
    
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        """Evaluasi kondisi dan return hasilnya."""
        condition = params.get("condition", {})
        
        try:
            result = self._evaluate_condition(condition, context)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Condition: {result}",
                data={
                    "condition_result": result,
                    "variable": condition.get("variable", ""),
                    "operator": condition.get("operator", "equals"),
                },
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal evaluasi kondisi: {str(e)}",
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