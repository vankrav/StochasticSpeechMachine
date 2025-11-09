"""
Акустические правила - работа с звуковыми характеристиками
"""

import numpy as np
from typing import Dict, Any, Optional
from .base import Rule


class PitchProximityRule(Rule):
    """Выбирает слова с близкой высотой тона (pitch)"""
    
    def __init__(self, max_diff: float = 50.0, **kwargs):
        """
        Args:
            max_diff: максимальная разница в Hz (по умолчанию 50 Hz)
        """
        super().__init__(name="Близость pitch", max_diff=max_diff, **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_pitch = current.get('pitch_mean', 0)
        candidate_pitch = candidate.get('pitch_mean', 0)
        
        if current_pitch == 0 or candidate_pitch == 0:
            return 0.5  # Нейтральная оценка если pitch не определен
        
        max_diff = self.params['max_diff']
        diff = abs(current_pitch - candidate_pitch)
        
        if diff > max_diff:
            return 0.0
        
        return 1.0 - (diff / max_diff)


class PitchDirectionRule(Rule):
    """Движение pitch в определенном направлении"""
    
    def __init__(self, direction: str = 'ascending', step: float = 5.0, **kwargs):
        """
        Args:
            direction: 'ascending' (вверх), 'descending' (вниз), 'wave' (волна)
            step: минимальный шаг изменения в Hz
        """
        super().__init__(name="Направление pitch", direction=direction, step=step, **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_pitch = current.get('pitch_mean', 0)
        candidate_pitch = candidate.get('pitch_mean', 0)
        
        if current_pitch == 0 or candidate_pitch == 0:
            return 0.5
        
        diff = candidate_pitch - current_pitch
        step = self.params['step']
        direction = self.params['direction']
        
        if direction == 'ascending':
            return 1.0 if diff > step else 0.0
        elif direction == 'descending':
            return 1.0 if diff < -step else 0.0
        elif direction == 'wave':
            # Волна: чередование вверх-вниз
            history = context.get('history', [])
            if len(history) < 2:
                return 1.0
            prev_diff = history[-1].get('pitch_mean', 0) - history[-2].get('pitch_mean', 0)
            # Меняем направление
            return 1.0 if (prev_diff * diff) < 0 else 0.0
        
        return 0.5


class DurationPatternRule(Rule):
    """Ритмический паттерн длительностей"""
    
    def __init__(self, pattern: list = None, **kwargs):
        """
        Args:
            pattern: список относительных длительностей, например [1.0, 0.5, 0.5, 1.0]
                     (длинный-короткий-короткий-длинный)
        """
        if pattern is None:
            pattern = [1.0, 0.5, 1.0, 0.5]  # По умолчанию
        
        super().__init__(name="Ритм длительности", pattern=pattern, **kwargs)
        self.position = 0
    
    def score(self, current, candidate, context):
        pattern = self.params['pattern']
        target_ratio = pattern[self.position % len(pattern)]
        
        # Средняя длительность всех семплов (берем из контекста)
        avg_duration = context.get('avg_duration', 0.5)
        candidate_duration = candidate.get('duration', 0.5)
        
        candidate_ratio = candidate_duration / avg_duration
        
        # Чем ближе к целевому ratio, тем выше оценка
        diff = abs(candidate_ratio - target_ratio)
        score = max(0.0, 1.0 - diff)
        
        if score > 0.5:  # Если достаточно близко, переходим к следующему шагу паттерна
            self.position += 1
        
        return score


class AmplitudeWaveRule(Rule):
    """Волна громкости (RMS)"""
    
    def __init__(self, wave_type: str = 'crescendo', **kwargs):
        """
        Args:
            wave_type: 'crescendo' (нарастание), 'diminuendo' (затухание), 
                      'wave' (синусоида)
        """
        super().__init__(name="Волна громкости", wave_type=wave_type, **kwargs)
        self.phase = 0
    
    def score(self, current, candidate, context):
        wave_type = self.params['wave_type']
        candidate_rms = candidate.get('rms_relative', 1.0)
        
        if wave_type == 'crescendo':
            # Ищем более громкие семплы
            if current is None:
                target = 0.5
            else:
                target = current.get('rms_relative', 1.0) + 0.1
            
            diff = abs(candidate_rms - target)
            return max(0.0, 1.0 - diff * 2)
        
        elif wave_type == 'diminuendo':
            # Ищем более тихие семплы
            if current is None:
                target = 1.5
            else:
                target = current.get('rms_relative', 1.0) - 0.1
            
            diff = abs(candidate_rms - target)
            return max(0.0, 1.0 - diff * 2)
        
        elif wave_type == 'wave':
            # Синусоидальная волна
            self.phase += 0.1
            target = 1.0 + 0.5 * np.sin(self.phase)
            diff = abs(candidate_rms - target)
            return max(0.0, 1.0 - diff * 2)
        
        return 0.5


class MFCCProximityRule(Rule):
    """Близость тембра (по MFCC коэффициентам)"""
    
    def __init__(self, threshold: float = 0.8, **kwargs):
        """
        Args:
            threshold: порог косинусного сходства (0-1)
        """
        super().__init__(name="Близость тембра", threshold=threshold, **kwargs)
    
    def score(self, current, candidate, context):
        if current is None:
            return 1.0
        
        current_mfcc = np.array(current.get('mfcc_mean', []))
        candidate_mfcc = np.array(candidate.get('mfcc_mean', []))
        
        if len(current_mfcc) == 0 or len(candidate_mfcc) == 0:
            return 0.5
        
        # Косинусное сходство
        similarity = np.dot(current_mfcc, candidate_mfcc) / (
            np.linalg.norm(current_mfcc) * np.linalg.norm(candidate_mfcc) + 1e-10
        )
        
        threshold = self.params['threshold']
        
        if similarity >= threshold:
            return 1.0
        else:
            return max(0.0, similarity / threshold)
