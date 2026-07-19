"""
Action Registry - Mendaftarkan dan mengelola semua action yang tersedia.
Menggunakan pattern Registry agar penambahan action baru mudah dilakukan.
"""

from typing import Dict, Type, Optional
from backend.actions.base_action import BaseAction


class ActionRegistry:
    """
    Registry untuk mendaftarkan dan mencari action berdasarkan nama.
    
    Contoh penggunaan:
        registry = ActionRegistry()
        registry.register(ClickAction())
        action = registry.get("click")
        result = await action.execute(context, params)
    """
    
    def __init__(self):
        self._actions: Dict[str, BaseAction] = {}
    
    def register(self, action: BaseAction) -> None:
        """
        Mendaftarkan action baru.
        
        Args:
            action: Instance dari BaseAction.
            
        Raises:
            ValueError: Jika action dengan nama yang sama sudah terdaftar.
        """
        if action.name in self._actions:
            raise ValueError(f"Action '{action.name}' sudah terdaftar.")
        self._actions[action.name] = action
    
    def unregister(self, name: str) -> None:
        """Menghapus action dari registry."""
        self._actions.pop(name, None)
    
    def get(self, name: str) -> Optional[BaseAction]:
        """
        Mendapatkan action berdasarkan nama.
        
        Args:
            name: Nama action (sama dengan field 'type' di workflow JSON).
            
        Returns:
            Instance BaseAction atau None jika tidak ditemukan.
        """
        return self._actions.get(name)
    
    def get_all(self) -> Dict[str, BaseAction]:
        """Mendapatkan semua action yang terdaftar."""
        return dict(self._actions)
    
    def get_action_names(self) -> list[str]:
        """Mendapatkan daftar nama semua action."""
        return list(self._actions.keys())
    
    def get_action_descriptions(self) -> list[dict]:
        """
        Mendapatkan daftar deskripsi semua action (untuk UI).
        
        Returns:
            List of dict: [{"name": "click", "description": "...", "default_params": {...}}, ...]
        """
        return [
            {
                "name": action.name,
                "description": action.description,
                "default_params": action.default_params,
            }
            for action in self._actions.values()
        ]