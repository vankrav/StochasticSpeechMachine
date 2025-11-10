"""
Markov Chain правила для генератора
"""

import numpy as np
from typing import Dict, Any, List, Optional
from collections import defaultdict
from .base import Rule


class MarkovChainRule(Rule):
    """
    Правило на основе цепей Маркова.
    Строит матрицу переходов между словами и использует её для выбора.
    """
    
    def __init__(
        self, 
        samples: List[Dict[str, Any]],
        order: int = 1,
        use_pos: bool = False,
        use_sentiment: bool = False,
        smoothing: float = 0.01,
        **kwargs
    ):
        """
        Args:
            samples: список всех семплов для построения модели
            order: порядок цепи Маркова (1, 2 или 3)
            use_pos: учитывать часть речи при построении переходов
            use_sentiment: учитывать эмоцию при построении переходов
            smoothing: сглаживание для нулевых вероятностей (0-1)
        """
        super().__init__(
            name="Markov Chain",
            order=order,
            use_pos=use_pos,
            use_sentiment=use_sentiment,
            smoothing=smoothing,
            **kwargs
        )
        
        self.samples = samples
        self.order = order
        self.use_pos = use_pos
        self.use_sentiment = use_sentiment
        self.smoothing = smoothing
        
        # Матрица переходов: {state: {next_word: count}}
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.transition_probs = {}
        
        # Строим модель
        self._build_model()
    
    def _get_state(self, sample: Dict[str, Any]) -> str:
        """
        Создает состояние на основе семпла.
        Может включать слово, POS тег, эмоцию.
        """
        parts = [sample['word']]
        
        if self.use_pos and sample.get('pos'):
            parts.append(f"[{sample['pos']}]")
        
        if self.use_sentiment and sample.get('sentiment'):
            parts.append(f"<{sample['sentiment']}>")
        
        return "|".join(parts)
    
    def _build_model(self):
        """Строит модель Маркова из последовательности семплов"""
        if len(self.samples) < 2:
            return
        
        # Предполагаем, что семплы упорядочены по индексу
        sorted_samples = sorted(self.samples, key=lambda x: x.get('index', 0))
        
        # Подсчитываем переходы
        for i in range(len(sorted_samples) - 1):
            current_state = self._get_state(sorted_samples[i])
            next_state = self._get_state(sorted_samples[i + 1])
            self.transitions[current_state][next_state] += 1
        
        # Конвертируем в вероятности
        for state, next_states in self.transitions.items():
            total = sum(next_states.values())
            self.transition_probs[state] = {
                next_state: count / total
                for next_state, count in next_states.items()
            }
    
    def score(
        self, 
        current_sample: Optional[Dict[str, Any]], 
        candidate_sample: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """
        Вычисляет вероятность перехода от current к candidate
        согласно цепи Маркова
        """
        if current_sample is None:
            # Для первого семпла используем равномерное распределение
            return 0.5
        
        current_state = self._get_state(current_sample)
        candidate_state = self._get_state(candidate_sample)
        
        # Получаем вероятность перехода
        if current_state in self.transition_probs:
            prob = self.transition_probs[current_state].get(
                candidate_state, 
                self.smoothing
            )
        else:
            # Если состояние не встречалось, используем сглаживание
            prob = self.smoothing
        
        return prob
    
    def get_most_likely_next(
        self, 
        current_sample: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Возвращает наиболее вероятное следующее состояние
        """
        if current_sample is None:
            return None
        
        current_state = self._get_state(current_sample)
        
        if current_state not in self.transition_probs:
            return None
        
        probs = self.transition_probs[current_state]
        if not probs:
            return None
        
        return max(probs.items(), key=lambda x: x[1])[0]


class MarkovChainBigramRule(Rule):
    """
    Упрощенное правило Markov Chain на основе биграмм слов.
    Не учитывает POS/sentiment, только последовательность слов.
    """
    
    def __init__(self, samples: List[Dict[str, Any]], smoothing: float = 0.01, **kwargs):
        super().__init__(name="Markov Bigram", smoothing=smoothing, **kwargs)
        
        self.samples = samples
        self.smoothing = smoothing
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.transition_probs = {}
        
        self._build_model()
    
    def _build_model(self):
        """Строит модель биграмм"""
        sorted_samples = sorted(self.samples, key=lambda x: x.get('index', 0))
        
        for i in range(len(sorted_samples) - 1):
            current_word = sorted_samples[i]['word']
            next_word = sorted_samples[i + 1]['word']
            self.transitions[current_word][next_word] += 1
        
        # Конвертируем в вероятности
        for word, next_words in self.transitions.items():
            total = sum(next_words.values())
            self.transition_probs[word] = {
                next_word: count / total
                for next_word, count in next_words.items()
            }
    
    def score(
        self, 
        current_sample: Optional[Dict[str, Any]], 
        candidate_sample: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Вычисляет вероятность перехода на основе биграмм"""
        if current_sample is None:
            return 0.5
        
        current_word = current_sample['word']
        candidate_word = candidate_sample['word']
        
        if current_word in self.transition_probs:
            return self.transition_probs[current_word].get(
                candidate_word, 
                self.smoothing
            )
        
        return self.smoothing


class MarkovEmotionalRule(Rule):
    """
    Markov Chain только по эмоциям (transitions между sentiment'ами)
    """
    
    def __init__(self, samples: List[Dict[str, Any]], smoothing: float = 0.1, **kwargs):
        super().__init__(name="Markov Emotional", smoothing=smoothing, **kwargs)
        
        self.samples = samples
        self.smoothing = smoothing
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.transition_probs = {}
        
        self._build_model()
    
    def _build_model(self):
        """Строит модель переходов между эмоциями"""
        sorted_samples = sorted(self.samples, key=lambda x: x.get('index', 0))
        
        for i in range(len(sorted_samples) - 1):
            current_sentiment = sorted_samples[i].get('sentiment', 'neutral')
            next_sentiment = sorted_samples[i + 1].get('sentiment', 'neutral')
            self.transitions[current_sentiment][next_sentiment] += 1
        
        # Конвертируем в вероятности
        for sentiment, next_sentiments in self.transitions.items():
            total = sum(next_sentiments.values())
            self.transition_probs[sentiment] = {
                next_sentiment: count / total
                for next_sentiment, count in next_sentiments.items()
            }
    
    def score(
        self, 
        current_sample: Optional[Dict[str, Any]], 
        candidate_sample: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Вычисляет вероятность перехода между эмоциями"""
        if current_sample is None:
            return 0.5
        
        current_sentiment = current_sample.get('sentiment', 'neutral')
        candidate_sentiment = candidate_sample.get('sentiment', 'neutral')
        
        if current_sentiment in self.transition_probs:
            prob = self.transition_probs[current_sentiment].get(
                candidate_sentiment,
                self.smoothing
            )
            return prob
        
        return self.smoothing


class MarkovPOSRule(Rule):
    """
    Markov Chain на основе частей речи (POS tags)
    """
    
    def __init__(self, samples: List[Dict[str, Any]], smoothing: float = 0.1, **kwargs):
        super().__init__(name="Markov POS", smoothing=smoothing, **kwargs)
        
        self.samples = samples
        self.smoothing = smoothing
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.transition_probs = {}
        
        self._build_model()
    
    def _build_model(self):
        """Строит модель переходов между частями речи"""
        sorted_samples = sorted(self.samples, key=lambda x: x.get('index', 0))
        
        for i in range(len(sorted_samples) - 1):
            current_pos = sorted_samples[i].get('pos')
            next_pos = sorted_samples[i + 1].get('pos')
            
            # Пропускаем если нет POS
            if not current_pos or not next_pos:
                continue
            
            self.transitions[current_pos][next_pos] += 1
        
        # Конвертируем в вероятности
        for pos, next_pos_tags in self.transitions.items():
            total = sum(next_pos_tags.values())
            self.transition_probs[pos] = {
                next_pos: count / total
                for next_pos, count in next_pos_tags.items()
            }
    
    def score(
        self, 
        current_sample: Optional[Dict[str, Any]], 
        candidate_sample: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Вычисляет вероятность перехода между частями речи"""
        if current_sample is None:
            return 0.5
        
        current_pos = current_sample.get('pos')
        candidate_pos = candidate_sample.get('pos')
        
        if not current_pos or not candidate_pos:
            return self.smoothing
        
        if current_pos in self.transition_probs:
            prob = self.transition_probs[current_pos].get(
                candidate_pos,
                self.smoothing
            )
            return prob
        
        return self.smoothing
