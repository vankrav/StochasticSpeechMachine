#!/usr/bin/env python3
"""
Standalone Markov Chain генератор для стохастической речи
Простой и независимый от веб-интерфейса
"""

import json
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


class SimpleMarkovGenerator:
    """
    Простой генератор на основе цепей Маркова
    """
    
    def __init__(self, metadata_path: str):
        """
        Args:
            metadata_path: путь к metadata.json
        """
        self.metadata_path = Path(metadata_path)
        self.metadata = self._load_metadata()
        self.samples = self.metadata.get('samples', [])
        
        # Сортируем по индексу (исходная последовательность)
        self.samples = sorted(self.samples, key=lambda x: x.get('index', 0))
        
        # Матрицы переходов
        self.word_transitions = defaultdict(lambda: defaultdict(int))
        self.word_probs = {}
        
        self.emotion_transitions = defaultdict(lambda: defaultdict(int))
        self.emotion_probs = {}
        
        self.pos_transitions = defaultdict(lambda: defaultdict(int))
        self.pos_probs = {}
        
        # Строим модели
        self._build_models()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Загружает метаданные из JSON"""
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_models(self):
        """Строит все модели переходов"""
        if len(self.samples) < 2:
            print("⚠️  Недостаточно данных для построения модели (нужно минимум 2 семпла)")
            return
        
        # Подсчитываем переходы
        for i in range(len(self.samples) - 1):
            current = self.samples[i]
            next_sample = self.samples[i + 1]
            
            # Переходы между словами
            current_word = current['word']
            next_word = next_sample['word']
            self.word_transitions[current_word][next_word] += 1
            
            # Переходы между эмоциями
            current_emotion = current.get('sentiment', 'neutral')
            next_emotion = next_sample.get('sentiment', 'neutral')
            self.emotion_transitions[current_emotion][next_emotion] += 1
            
            # Переходы между частями речи
            current_pos = current.get('pos')
            next_pos = next_sample.get('pos')
            if current_pos and next_pos:
                self.pos_transitions[current_pos][next_pos] += 1
        
        # Конвертируем в вероятности
        self._compute_probabilities()
        
        print(f"✓ Построено {len(self.word_transitions)} переходов между словами")
        print(f"✓ Построено {len(self.emotion_transitions)} переходов между эмоциями")
        print(f"✓ Построено {len(self.pos_transitions)} переходов между частями речи")
    
    def _compute_probabilities(self):
        """Конвертирует счетчики в вероятности"""
        # Слова
        for word, next_words in self.word_transitions.items():
            total = sum(next_words.values())
            self.word_probs[word] = {
                next_word: count / total
                for next_word, count in next_words.items()
            }
        
        # Эмоции
        for emotion, next_emotions in self.emotion_transitions.items():
            total = sum(next_emotions.values())
            self.emotion_probs[emotion] = {
                next_emotion: count / total
                for next_emotion, count in next_emotions.items()
            }
        
        # Части речи
        for pos, next_pos_tags in self.pos_transitions.items():
            total = sum(next_pos_tags.values())
            self.pos_probs[pos] = {
                next_pos: count / total
                for next_pos, count in next_pos_tags.items()
            }
    
    def get_next_word(
        self, 
        current_word: str, 
        use_emotion: Optional[str] = None,
        use_pos: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Выбирает следующее слово на основе текущего
        
        Args:
            current_word: текущее слово
            use_emotion: если указано, выбирает только слова с этой эмоцией
            use_pos: если указано, выбирает только слова с этой частью речи
        
        Returns:
            Семпл следующего слова или None
        """
        # Получаем вероятности переходов
        if current_word not in self.word_probs:
            # Если слово не встречалось в переходах, выбираем случайно
            return random.choice(self.samples)
        
        probs = self.word_probs[current_word]
        
        # Фильтруем кандидатов
        candidates = []
        weights = []
        
        for next_word, prob in probs.items():
            # Находим семпл для этого слова
            sample = self._find_sample_by_word(next_word)
            if not sample:
                continue
            
            # Фильтр по эмоции
            if use_emotion and sample.get('sentiment') != use_emotion:
                continue
            
            # Фильтр по части речи
            if use_pos and sample.get('pos') != use_pos:
                continue
            
            candidates.append(sample)
            weights.append(prob)
        
        if not candidates:
            # Если после фильтрации ничего не осталось, выбираем случайно
            return random.choice(self.samples)
        
        # Нормализуем веса
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Выбираем согласно вероятностям
        return random.choices(candidates, weights=weights)[0]
    
    def get_next_by_emotion(self, current_emotion: str) -> Optional[str]:
        """Предсказывает следующую эмоцию на основе текущей"""
        if current_emotion not in self.emotion_probs:
            return None
        
        probs = self.emotion_probs[current_emotion]
        emotions = list(probs.keys())
        weights = list(probs.values())
        
        return random.choices(emotions, weights=weights)[0]
    
    def get_next_by_pos(self, current_pos: str) -> Optional[str]:
        """Предсказывает следующую часть речи на основе текущей"""
        if current_pos not in self.pos_probs:
            return None
        
        probs = self.pos_probs[current_pos]
        pos_tags = list(probs.keys())
        weights = list(probs.values())
        
        return random.choices(pos_tags, weights=weights)[0]
    
    def _find_sample_by_word(self, word: str) -> Optional[Dict[str, Any]]:
        """Находит семпл по слову"""
        for sample in self.samples:
            if sample['word'] == word:
                return sample
        return None
    
    def generate_sequence(
        self, 
        length: int = 10, 
        start_word: Optional[str] = None,
        emotion_filter: Optional[str] = None,
        pos_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерирует последовательность слов
        
        Args:
            length: длина последовательности
            start_word: начальное слово (если None, выбирается случайно)
            emotion_filter: фильтр по эмоции ('positive', 'negative', 'neutral')
            pos_filter: фильтр по части речи ('NOUN', 'VERB', и т.д.)
        
        Returns:
            Список семплов
        """
        sequence = []
        
        # Выбираем стартовое слово
        if start_word:
            current = self._find_sample_by_word(start_word)
            if not current:
                print(f"⚠️  Слово '{start_word}' не найдено, выбираю случайное")
                current = random.choice(self.samples)
        else:
            current = random.choice(self.samples)
        
        sequence.append(current)
        
        # Генерируем последовательность
        for i in range(length - 1):
            next_sample = self.get_next_word(
                current['word'],
                use_emotion=emotion_filter,
                use_pos=pos_filter
            )
            
            if not next_sample:
                next_sample = random.choice(self.samples)
            
            sequence.append(next_sample)
            current = next_sample
        
        return sequence
    
    def print_sequence(self, sequence: List[Dict[str, Any]], show_details: bool = False):
        """Выводит последовательность в читаемом виде"""
        print("\n" + "="*60)
        print("📝 СГЕНЕРИРОВАННАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ")
        print("="*60)
        
        words = []
        for i, sample in enumerate(sequence):
            word = sample['word']
            words.append(word)
            
            if show_details:
                emotion = sample.get('sentiment', 'N/A')
                pos = sample.get('pos', 'N/A')
                pitch = sample.get('pitch_mean', 0)
                duration = sample.get('duration', 0)
                print(f"{i+1:2d}. {word:20s} [{emotion:8s}] [{pos:6s}] {pitch:6.0f}Hz {duration:.2f}s")
            else:
                print(f"{i+1:2d}. {word}")
        
        print("="*60)
        print("Текст:", " ".join(words))
        print("="*60 + "\n")
    
    def analyze_transitions(self):
        """Выводит статистику по переходам"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ПЕРЕХОДОВ")
        print("="*60)
        
        # Наиболее вероятные переходы между словами
        print("\n🔤 Топ-10 переходов между словами:")
        word_pairs = []
        for word, next_words in self.word_probs.items():
            for next_word, prob in next_words.items():
                word_pairs.append((word, next_word, prob))
        
        word_pairs.sort(key=lambda x: x[2], reverse=True)
        for i, (w1, w2, prob) in enumerate(word_pairs[:10], 1):
            print(f"  {i:2d}. '{w1}' → '{w2}' ({prob:.1%})")
        
        # Переходы между эмоциями
        print("\n😊 Переходы между эмоциями:")
        for emotion, next_emotions in self.emotion_probs.items():
            top_next = max(next_emotions.items(), key=lambda x: x[1])
            print(f"  {emotion:10s} → {top_next[0]:10s} ({top_next[1]:.1%})")
        
        # Переходы между частями речи
        if self.pos_probs:
            print("\n📝 Переходы между частями речи:")
            for pos, next_pos_tags in list(self.pos_probs.items())[:10]:
                top_next = max(next_pos_tags.items(), key=lambda x: x[1])
                print(f"  {pos:6s} → {top_next[0]:6s} ({top_next[1]:.1%})")
        
        print("="*60 + "\n")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Markov Chain генератор стохастической речи",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Сгенерировать последовательность из 10 слов
  python markov_generator.py output_audio/metadata.json

  # Начать с определенного слова
  python markov_generator.py output_audio/metadata.json --start заложник

  # Сгенерировать 20 слов с фильтром по эмоции
  python markov_generator.py output_audio/metadata.json -n 20 --emotion positive

  # Показать детали и статистику
  python markov_generator.py output_audio/metadata.json --details --analyze

  # Фильтр по части речи
  python markov_generator.py output_audio/metadata.json --pos NOUN -n 15
        """
    )
    
    parser.add_argument(
        'metadata',
        type=Path,
        help='Путь к metadata.json'
    )
    
    parser.add_argument(
        '-n', '--length',
        type=int,
        default=10,
        help='Длина последовательности (по умолчанию: 10)'
    )
    
    parser.add_argument(
        '-s', '--start',
        type=str,
        help='Начальное слово'
    )
    
    parser.add_argument(
        '-e', '--emotion',
        type=str,
        choices=['positive', 'negative', 'neutral', 'skip'],
        help='Фильтр по эмоции'
    )
    
    parser.add_argument(
        '-p', '--pos',
        type=str,
        help='Фильтр по части речи (NOUN, VERB, ADJF, и т.д.)'
    )
    
    parser.add_argument(
        '-d', '--details',
        action='store_true',
        help='Показать детали (эмоции, POS, pitch, duration)'
    )
    
    parser.add_argument(
        '-a', '--analyze',
        action='store_true',
        help='Показать статистику переходов'
    )
    
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=1,
        help='Количество последовательностей для генерации (по умолчанию: 1)'
    )
    
    args = parser.parse_args()
    
    # Проверяем файл
    if not args.metadata.exists():
        print(f"❌ Файл не найден: {args.metadata}")
        return 1
    
    print(f"\n🎲 Markov Chain Generator")
    print(f"📁 Метаданные: {args.metadata}")
    
    # Создаем генератор
    generator = SimpleMarkovGenerator(str(args.metadata))
    
    if not generator.samples:
        print("❌ Нет семплов в метаданных")
        return 1
    
    print(f"✓ Загружено семплов: {len(generator.samples)}")
    
    # Показываем анализ если запрошено
    if args.analyze:
        generator.analyze_transitions()
    
    # Генерируем последовательности
    for i in range(args.count):
        if args.count > 1:
            print(f"\n--- Последовательность {i+1}/{args.count} ---")
        
        sequence = generator.generate_sequence(
            length=args.length,
            start_word=args.start,
            emotion_filter=args.emotion,
            pos_filter=args.pos
        )
        
        generator.print_sequence(sequence, show_details=args.details)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
