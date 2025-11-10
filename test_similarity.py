#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации функции поиска похожих слов
"""

import json
from linguistic_features import find_similar_word_from_metadata, find_most_similar_word

def test_similarity():
    """
    Тестирует функцию поиска похожих слов
    """
    metadata_path = 'output_audio/metadata.json'
    
    # Загружаем метаданные
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    all_words = metadata.get('samples', [])
    
    # Фильтруем только слова (не паузы)
    words_only = [w for w in all_words if w.get('type') == 'word']
    
    print(f"Всего слов в датасете: {len(words_only)}")
    print()
    
    # Тестируем на нескольких примерах
    test_indices = [0, 10, 20, 50, 100]
    
    for idx in test_indices:
        if idx >= len(words_only):
            continue
        
        target = words_only[idx]
        target_word = target.get('word', '')
        target_pos = target.get('pos', '')
        
        print(f"{'='*60}")
        print(f"Ищем похожее слово для: '{target_word}'")
        print(f"  POS: {target_pos}")
        print(f"  Род: {target.get('gender')}, Число: {target.get('number')}, Падеж: {target.get('case')}")
        print()
        
        # Ищем похожее слово (исключаем само целевое слово)
        similar = find_most_similar_word(
            target, 
            all_words, 
            exclude_indices=[target.get('index')]
        )
        
        if similar:
            print(f"Наиболее похожее: '{similar.get('word')}'")
            print(f"  POS: {similar.get('pos')}")
            print(f"  Род: {similar.get('gender')}, Число: {similar.get('number')}, Падеж: {similar.get('case')}")
            print(f"  Индекс: {similar.get('index')}")
        else:
            print("Похожее слово не найдено")
        
        print()

def find_similar_for_custom_word(word: str, metadata_path: str):
    """
    Находит похожее слово для произвольного слова
    
    Args:
        word: слово для поиска
        metadata_path: путь к metadata.json
    """
    from linguistic_features import analyze_word
    
    # Анализируем целевое слово
    target_features = analyze_word(word)
    
    print(f"Анализ слова '{word}':")
    print(f"  POS: {target_features.get('pos')}")
    print(f"  Род: {target_features.get('gender')}, Число: {target_features.get('number')}, Падеж: {target_features.get('case')}")
    print()
    
    # Загружаем метаданные
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    all_words = metadata.get('samples', [])
    
    # Ищем похожее слово
    similar = find_most_similar_word(target_features, all_words)
    
    if similar:
        print(f"Наиболее похожее слово из датасета: '{similar.get('word')}'")
        print(f"  POS: {similar.get('pos')}")
        print(f"  Род: {similar.get('gender')}, Число: {similar.get('number')}, Падеж: {similar.get('case')}")
        print(f"  Индекс: {similar.get('index')}")
        print(f"  Файл: {similar.get('filename')}")
    else:
        print("Похожее слово не найдено")

def test_usage_weights():
    """
    Тестирует работу штрафа за частое использование слов
    """
    metadata_path = 'output_audio/metadata.json'
    
    # Загружаем метаданные
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    all_words = metadata.get('samples', [])
    words_only = [w for w in all_words if w.get('type') == 'word']
    
    if len(words_only) < 10:
        print("Недостаточно слов для теста")
        return
    
    # Берем первое слово как целевое
    target = words_only[0]
    
    print(f"Целевое слово: '{target.get('word')}' (POS: {target.get('pos')})")
    print()
    
    # Первый поиск - без весов
    print("--- ПОИСК 1 (без весов) ---")
    similar1 = find_most_similar_word(
        target,
        all_words,
        exclude_indices=[target.get('index')]
    )
    if similar1:
        print(f"Найдено: '{similar1.get('word')}' (индекс {similar1.get('index')})")
    print()
    
    # Создаем веса использования (помечаем найденное слово как использованное)
    usage_weights = {similar1.get('index'): 1}
    
    # Второй поиск - с весами (первое слово должно получить штраф)
    print("--- ПОИСК 2 (с весами: первое слово использовано 1 раз) ---")
    similar2 = find_most_similar_word(
        target,
        all_words,
        exclude_indices=[target.get('index')],
        usage_weights=usage_weights
    )
    if similar2:
        print(f"Найдено: '{similar2.get('word')}' (индекс {similar2.get('index')})")
        if similar2.get('index') == similar1.get('index'):
            print("⚠️  То же слово (штраф недостаточен)")
        else:
            print("✓  Другое слово (штраф сработал!)")
    print()
    
    # Третий поиск - оба слова использованы
    usage_weights[similar2.get('index')] = 1
    
    print("--- ПОИСК 3 (с весами: оба предыдущих слова использованы) ---")
    similar3 = find_most_similar_word(
        target,
        all_words,
        exclude_indices=[target.get('index')],
        usage_weights=usage_weights
    )
    if similar3:
        print(f"Найдено: '{similar3.get('word')}' (индекс {similar3.get('index')})")
        if similar3.get('index') in [similar1.get('index'), similar2.get('index')]:
            print("⚠️  Повторное использование")
        else:
            print("✓  Новое слово!")

if __name__ == '__main__':
    print("=" * 60)
    print("ТЕСТ 1: Поиск похожих слов из датасета")
    print("=" * 60)
    print()
    
    test_similarity()
    
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Поиск похожего слова для произвольного слова")
    print("=" * 60)
    print()
    
    # Пример с произвольным словом
    find_similar_for_custom_word('книга', 'output_audio/metadata.json')
    
    print("\n" + "=" * 60)
    find_similar_for_custom_word('говорить', 'output_audio/metadata.json')
    
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Проверка штрафа за частое использование")
    print("=" * 60)
    print()
    
    test_usage_weights()
