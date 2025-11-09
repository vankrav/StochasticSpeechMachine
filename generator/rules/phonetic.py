"""
Фонетические правила - работа со звуковым составом слов
"""

from typing import Dict, Any, Optional
from .base import Rule


class AlliterationRule(Rule):
    """Аллитерация - повторение первой буквы"""
    
    def __init__(self, **kwargs):
        super().__init__(name="Аллитерация", **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_word = current.get('word', '')
        candidate_word = candidate.get('word', '')
        
        if not current_word or not candidate_word:
            return 0.5
        
        current_letter = current_word[0].lower()
        candidate_letter = candidate_word[0].lower()
        
        return 1.0 if current_letter == candidate_letter else 0.0


class VowelConsonantRatioRule(Rule):
    """Чередование по соотношению гласных/согласных"""
    
    def __init__(self, mode: str = 'alternating', **kwargs):
        """
        Args:
            mode: 'alternating' (чередование) или 'increasing' (возрастание) 
                  или 'decreasing' (убывание)
        """
        super().__init__(name="Гласные/Согласные", mode=mode, **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        mode = self.params['mode']
        current_ratio = current.get('vowel_consonant_ratio', 0.5)
        candidate_ratio = candidate.get('vowel_consonant_ratio', 0.5)
        
        if mode == 'alternating':
            # Хотим противоположное соотношение
            # Если было много гласных, ищем много согласных и наоборот
            target = 1.0 / (current_ratio + 0.1)  # Инверсия с защитой от деления на 0
            diff = abs(candidate_ratio - target)
            return max(0.0, 1.0 - diff)
        
        elif mode == 'increasing':
            # Постепенно увеличиваем долю гласных
            if candidate_ratio > current_ratio:
                return 1.0
            return 0.5
        
        elif mode == 'decreasing':
            # Постепенно уменьшаем долю гласных
            if candidate_ratio < current_ratio:
                return 1.0
            return 0.5
        
        return 0.5


class VoicingAlternationRule(Rule):
    """Чередование звонких и глухих звуков"""
    
    def __init__(self, **kwargs):
        super().__init__(name="Звонкость/Глухость", **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_voiced = current.get('voiced_percent', 50)
        candidate_voiced = candidate.get('voiced_percent', 50)
        
        # Хотим чередовать: если было звонко, ищем глухое
        if current_voiced > 50:
            # Было звонкое, ищем глухое
            return 1.0 if candidate_voiced < 50 else 0.0
        else:
            # Было глухое, ищем звонкое
            return 1.0 if candidate_voiced > 50 else 0.0
