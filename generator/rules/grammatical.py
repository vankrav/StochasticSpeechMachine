"""
Грамматические правила - работа с частями речи и морфологией
"""

from typing import Dict, Any, Optional, List
from .base import Rule


class POSPatternRule(Rule):
    """Следование паттерну частей речи"""
    
    def __init__(self, pattern: List[str] = None, **kwargs):
        """
        Args:
            pattern: последовательность частей речи, например ['NOUN', 'VERB', 'ADJF']
        """
        if pattern is None:
            pattern = ['NOUN', 'VERB', 'NOUN']
        
        super().__init__(name="Паттерн частей речи", pattern=pattern, **kwargs)
        self.position = 0
    
    def score(self, current, candidate, context):
        pattern = self.params['pattern']
        target_pos = pattern[self.position % len(pattern)]
        
        candidate_pos = candidate.get('pos', '')
        
        if candidate_pos == target_pos:
            self.position += 1
            return 1.0
        
        return 0.0


class POSAlternationRule(Rule):
    """Чередование существительных и глаголов"""
    
    def __init__(self, **kwargs):
        super().__init__(name="Существительное/Глагол", **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_pos = current.get('pos', '')
        candidate_pos = candidate.get('pos', '')
        
        # Если было существительное, ищем глагол
        if current_pos == 'NOUN':
            return 1.0 if candidate_pos in ['VERB', 'INFN'] else 0.0
        
        # Если был глагол, ищем существительное
        elif current_pos in ['VERB', 'INFN']:
            return 1.0 if candidate_pos == 'NOUN' else 0.0
        
        # Для других частей речи
        return 0.5
