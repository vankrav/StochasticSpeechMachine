"""
Базовый класс для правил выбора семплов
"""

from typing import Dict, Any, List, Optional


class Rule:
    """Базовый класс для правил выбора следующего семпла"""
    
    def __init__(self, name: str, weight: float = 1.0, **params):
        """
        Args:
            name: название правила
            weight: вес правила (0.0-1.0)
            **params: дополнительные параметры правила
        """
        self.name = name
        self.weight = weight
        self.params = params
        self.enabled = True
    
    def score(
        self, 
        current_sample: Optional[Dict[str, Any]], 
        candidate_sample: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """
        Вычисляет оценку (0-1) насколько candidate подходит для выбора
        
        Args:
            current_sample: текущий семпл (None если это первый)
            candidate_sample: кандидат на следующий семпл
            context: контекст (история, глобальное состояние)
        
        Returns:
            float: оценка от 0.0 (не подходит) до 1.0 (идеально подходит)
        """
        raise NotImplementedError("Subclasses must implement score()")
    
    def get_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию правила"""
        return {
            'name': self.name,
            'weight': self.weight,
            'enabled': self.enabled,
            'params': self.params
        }
    
    def update_params(self, **new_params):
        """Обновляет параметры правила"""
        self.params.update(new_params)
