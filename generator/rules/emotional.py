"""
Эмоциональные правила - работа с сентиментом и эмоциями
"""

from typing import Dict, Any, Optional, List
from .base import Rule


class EmotionWaveRule(Rule):
    """Движение по заданной эмоциональной траектории"""
    
    def __init__(self, wave: List[str] = None, **kwargs):
        """
        Args:
            wave: список эмоций для циклического повторения
                  например: ['positive', 'neutral', 'negative']
        """
        if wave is None:
            wave = ['neutral', 'positive', 'neutral', 'negative']
        
        super().__init__(name="Эмоциональная волна", wave=wave, **kwargs)
        self.position = 0
    
    def score(self, current, candidate, context):
        wave = self.params['wave']
        target_emotion = wave[self.position % len(wave)]
        
        candidate_emotion = candidate.get('sentiment', 'neutral')
        
        if candidate_emotion == target_emotion:
            self.position += 1
            return 1.0
        
        return 0.0


class EmotionContrastRule(Rule):
    """Чередование противоположных эмоций"""
    
    def __init__(self, **kwargs):
        super().__init__(name="Контраст эмоций", **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_emotion = current.get('sentiment', 'neutral')
        candidate_emotion = candidate.get('sentiment', 'neutral')
        
        # Определяем противоположности
        opposites = {
            'positive': 'negative',
            'negative': 'positive',
            'neutral': ['positive', 'negative']  # Из нейтрального можем идти куда угодно
        }
        
        if current_emotion == 'neutral':
            return 1.0 if candidate_emotion in ['positive', 'negative'] else 0.5
        
        target = opposites.get(current_emotion)
        
        if candidate_emotion == target:
            return 1.0
        elif candidate_emotion == 'neutral':
            return 0.5  # Переход через нейтральное
        else:
            return 0.0


class SentimentGradientRule(Rule):
    """Плавный градиент от негатива к позитиву или наоборот"""
    
    def __init__(self, direction: str = 'ascending', **kwargs):
        """
        Args:
            direction: 'ascending' (негатив→позитив) или 'descending' (позитив→негатив)
        """
        super().__init__(name="Градиент эмоций", direction=direction, **kwargs)
        
        # Порядок эмоций по интенсивности
        self.emotion_order = ['negative', 'neutral', 'positive']
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        direction = self.params['direction']
        
        current_emotion = current.get('sentiment', 'neutral')
        candidate_emotion = candidate.get('sentiment', 'neutral')
        
        try:
            current_idx = self.emotion_order.index(current_emotion)
            candidate_idx = self.emotion_order.index(candidate_emotion)
        except ValueError:
            return 0.5  # Неизвестная эмоция
        
        if direction == 'ascending':
            # Хотим двигаться вверх по списку
            if candidate_idx > current_idx:
                return 1.0
            elif candidate_idx == current_idx:
                return 0.5
            else:
                return 0.0
        
        elif direction == 'descending':
            # Хотим двигаться вниз по списку
            if candidate_idx < current_idx:
                return 1.0
            elif candidate_idx == current_idx:
                return 0.5
            else:
                return 0.0
        
        return 0.5
