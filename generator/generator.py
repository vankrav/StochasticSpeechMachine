"""
Основной движок генератора стохастической речи
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from rules.base import Rule


def softmax(scores: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Применяет softmax с температурой к массиву оценок"""
    scores = np.array(scores)
    
    # Защита от overflow
    scores = scores - np.max(scores)
    
    # Применяем температуру
    scores = scores / (temperature + 1e-10)
    
    exp_scores = np.exp(scores)
    return exp_scores / np.sum(exp_scores)


class StochasticGenerator:
    """
    Основной класс генератора стохастической речи
    """
    
    def __init__(self, metadata_path: str):
        """
        Args:
            metadata_path: путь к файлу metadata.json
        """
        self.metadata_path = Path(metadata_path)
        self.metadata = self._load_metadata()
        self.samples = self.metadata.get('samples', [])
        self.rules: List[Rule] = []
        self.context = {
            'history': [],
            'state': {},
            'avg_duration': self._calculate_avg_duration(),
            'avg_pitch': self._calculate_avg_pitch(),
            'avg_rms': self._calculate_avg_rms()
        }
        self.temperature = 1.0
        self.current_sample = None
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Загружает метаданные из JSON файла"""
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _calculate_avg_duration(self) -> float:
        """Вычисляет среднюю длительность семплов"""
        if not self.samples:
            return 0.5
        durations = [s.get('duration', 0.5) for s in self.samples]
        return np.mean(durations)
    
    def _calculate_avg_pitch(self) -> float:
        """Вычисляет среднюю высоту тона"""
        if not self.samples:
            return 150.0
        pitches = [s.get('pitch_mean', 150.0) for s in self.samples if s.get('pitch_mean', 0) > 0]
        return np.mean(pitches) if pitches else 150.0
    
    def _calculate_avg_rms(self) -> float:
        """Вычисляет среднюю громкость"""
        if not self.samples:
            return 0.05
        rms_values = [s.get('rms', 0.05) for s in self.samples]
        return np.mean(rms_values)
    
    def add_rule(self, rule: Rule):
        """Добавляет правило в генератор"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """Удаляет правило по имени"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Получает правило по имени"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def update_rule_weight(self, rule_name: str, weight: float):
        """Обновляет вес правила"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.weight = weight
    
    def update_rule_params(self, rule_name: str, **params):
        """Обновляет параметры правила"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.update_params(**params)
    
    def set_temperature(self, temperature: float):
        """Устанавливает температуру генерации (0-2)"""
        self.temperature = max(0.1, min(2.0, temperature))
    
    def select_next(self, current_sample: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Выбирает следующий семпл согласно правилам
        
        Args:
            current_sample: текущий семпл (если None, используется self.current_sample)
        
        Returns:
            dict: выбранный семпл
        """
        if current_sample is None:
            current_sample = self.current_sample
        
        if not self.samples:
            raise ValueError("Нет семплов для генерации")
        
        if not self.rules or all(not r.enabled for r in self.rules):
            # Если нет правил, выбираем случайно
            next_sample = np.random.choice(self.samples)
        else:
            # Вычисляем взвешенные оценки для всех кандидатов
            scores = []
            for candidate in self.samples:
                total_score = 0.0
                total_weight = 0.0
                
                for rule in self.rules:
                    if rule.enabled:
                        score = rule.score(current_sample, candidate, self.context)
                        total_score += score * rule.weight
                        total_weight += rule.weight
                
                # Нормализуем по сумме весов
                final_score = total_score / (total_weight + 1e-10)
                scores.append(final_score)
            
            # Применяем softmax с температурой для получения вероятностей
            probabilities = softmax(np.array(scores), self.temperature)
            
            # Выбираем случайно согласно вероятностям
            next_sample = np.random.choice(self.samples, p=probabilities)
        
        # Обновляем контекст
        self.context['history'].append(next_sample)
        if len(self.context['history']) > 20:  # Храним последние 20
            self.context['history'].pop(0)
        
        self.current_sample = next_sample
        return next_sample
    
    def generate_sequence(self, length: int = 10, start_word: Optional[str] = None) -> List[Dict]:
        """
        Генерирует последовательность семплов
        
        Args:
            length: длина последовательности
            start_word: начальное слово (опционально)
        
        Returns:
            list: список семплов
        """
        sequence = []
        
        # Находим стартовый семпл
        if start_word:
            current = self.get_sample_by_word(start_word)
        else:
            current = None
        
        for _ in range(length):
            next_sample = self.select_next(current)
            sequence.append(next_sample)
            current = next_sample
        
        return sequence
    
    def get_sample_by_word(self, word: str) -> Optional[Dict]:
        """Находит семпл по слову"""
        for sample in self.samples:
            if sample.get('word', '').lower() == word.lower():
                return sample
        return None
    
    def get_sample_by_index(self, index: int) -> Optional[Dict]:
        """Находит семпл по индексу"""
        for sample in self.samples:
            if sample.get('index') == index:
                return sample
        return None
    
    def reset(self):
        """Сбрасывает контекст и текущее состояние"""
        self.context['history'] = []
        self.context['state'] = {}
        self.current_sample = None
        
        # Сбрасываем состояние правил (позиции в паттернах и т.д.)
        for rule in self.rules:
            if hasattr(rule, 'position'):
                rule.position = 0
            if hasattr(rule, 'phase'):
                rule.phase = 0
    
    def get_config(self) -> Dict[str, Any]:
        """Возвращает текущую конфигурацию генератора"""
        return {
            'metadata_path': str(self.metadata_path),
            'total_samples': len(self.samples),
            'temperature': self.temperature,
            'rules': [rule.get_config() for rule in self.rules],
            'context': {
                'history_length': len(self.context['history']),
                'avg_duration': self.context['avg_duration'],
                'avg_pitch': self.context['avg_pitch'],
                'avg_rms': self.context['avg_rms']
            }
        }
