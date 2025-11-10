#!/usr/bin/env python3
"""
Быстрый тест Markov Chain генератора
"""

import sys
from pathlib import Path
from generator.generator import StochasticGenerator
from generator.rules.markov import (
    MarkovChainBigramRule,
    MarkovEmotionalRule,
    MarkovPOSRule
)


def test_markov_rules():
    """Тестирует Markov Chain правила в генераторе"""
    
    metadata_path = Path("output_audio/metadata.json")
    
    if not metadata_path.exists():
        print("❌ Файл output_audio/metadata.json не найден")
        print("   Сначала запустите speech_processor.py для создания метаданных")
        return 1
    
    print("\n" + "="*60)
    print("🧪 ТЕСТ MARKOV CHAIN ПРАВИЛ")
    print("="*60)
    
    # Создаем генератор
    print("\n1️⃣  Инициализация генератора...")
    gen = StochasticGenerator(str(metadata_path))
    print(f"   ✓ Загружено семплов: {len(gen.samples)}")
    
    # Тест 1: Markov Bigram Rule
    print("\n2️⃣  Тест: Markov Bigram (переходы между словами)")
    print("   Добавляем правило...")
    bigram_rule = MarkovChainBigramRule(gen.samples, weight=1.0)
    gen.add_rule(bigram_rule)
    
    print("   Генерация последовательности из 10 слов...")
    gen.reset()
    sequence = gen.generate_sequence(length=10)
    
    words = [s['word'] for s in sequence]
    print(f"   Результат: {' → '.join(words)}")
    
    # Тест 2: Markov Emotional Rule
    print("\n3️⃣  Тест: Markov Emotional (переходы между эмоциями)")
    gen.reset()
    gen.remove_rule("Markov Bigram")
    
    emotional_rule = MarkovEmotionalRule(gen.samples, weight=1.0)
    gen.add_rule(emotional_rule)
    
    print("   Генерация последовательности с эмоциональной логикой...")
    sequence = gen.generate_sequence(length=10)
    
    for i, s in enumerate(sequence, 1):
        emotion = s.get('sentiment', 'N/A')
        print(f"   {i:2d}. {s['word']:15s} [{emotion}]")
    
    # Тест 3: Markov POS Rule
    print("\n4️⃣  Тест: Markov POS (переходы между частями речи)")
    gen.reset()
    gen.remove_rule("Markov Emotional")
    
    pos_rule = MarkovPOSRule(gen.samples, weight=1.0)
    gen.add_rule(pos_rule)
    
    print("   Генерация с учетом частей речи...")
    sequence = gen.generate_sequence(length=10)
    
    for i, s in enumerate(sequence, 1):
        pos = s.get('pos', 'N/A')
        print(f"   {i:2d}. {s['word']:15s} [{pos}]")
    
    # Тест 4: Комбинация правил
    print("\n5️⃣  Тест: Комбинация Bigram + Emotional")
    gen.reset()
    gen.remove_rule("Markov POS")
    
    bigram_rule = MarkovChainBigramRule(gen.samples, weight=0.7)
    emotional_rule = MarkovEmotionalRule(gen.samples, weight=0.3)
    gen.add_rule(bigram_rule)
    gen.add_rule(emotional_rule)
    
    print("   Веса: Bigram=0.7, Emotional=0.3")
    print("   Температура: 0.8")
    gen.set_temperature(0.8)
    
    sequence = gen.generate_sequence(length=12)
    
    for i, s in enumerate(sequence, 1):
        emotion = s.get('sentiment', 'N/A')
        print(f"   {i:2d}. {s['word']:15s} [{emotion}]")
    
    print("\n" + "="*60)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    print("="*60 + "\n")
    
    return 0


def main():
    """Главная функция"""
    try:
        return test_markov_rules()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
