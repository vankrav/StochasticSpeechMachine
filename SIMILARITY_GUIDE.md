# Руководство по поиску похожих слов

## Описание

Функция `find_most_similar_word()` находит наиболее похожее слово из набора данных на основе лингвистических характеристик.

## Приоритет сравнения

1. **Часть речи (POS)** - критический критерий (вес 100)
   - Если части речи не совпадают, слово не рассматривается
   
2. **Морфологические характеристики** (вес 10 за совпадение, -5 за несовпадение):
   - Род (gender)
   - Число (number)
   - Падеж (case)
   - Время (tense)
   - Лицо (person)
   - Одушевленность (animacy)

3. **Фонетические характеристики** (меньший вес):
   - Длина слова (вес 5)
   - Соотношение гласных к согласным (вес 3)
   - Процент гласных (вес 2)

## Использование

### Вариант 1: Поиск похожего слова из метаданных

```python
from linguistic_features import find_similar_word_from_metadata

# Данные целевого слова (из metadata.json)
target_word = {
    'word': 'книга',
    'pos': 'NOUN',
    'gender': 'femn',
    'number': 'sing',
    'case': 'nomn',
    'word_length': 5,
    'vowels_percent': 40.0,
    # ... остальные характеристики
}

# Находим похожее слово
similar = find_similar_word_from_metadata(
    target_word_data=target_word,
    metadata_path='output_audio/metadata.json',
    exclude_indices=[0, 1, 2]  # исключаем определенные индексы
)

print(f"Похожее слово: {similar['word']}")
```

### Вариант 1a: С учетом частоты использования (NEW!)

```python
from linguistic_features import find_most_similar_word
import json

# Загружаем метаданные
with open('output_audio/metadata.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# Трекинг использования слов (индекс: количество раз)
usage_weights = {
    5: 2,   # слово с индексом 5 использовалось 2 раза
    12: 1,  # слово с индексом 12 использовалось 1 раз
    18: 3   # слово с индексом 18 использовалось 3 раза
}

# Находим похожее слово с учетом весов
similar = find_most_similar_word(
    target_word_data=target_word,
    all_words=metadata['samples'],
    exclude_indices=[0, 1, 2],
    usage_weights=usage_weights  # штраф за частое использование
)

print(f"Похожее слово: {similar['word']}")
```

### Вариант 2: Поиск из списка слов

```python
from linguistic_features import find_most_similar_word
import json

# Загружаем все слова
with open('output_audio/metadata.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)

all_words = metadata['samples']

# Находим похожее
similar = find_most_similar_word(
    target_word_data=target_word,
    all_words=all_words,
    exclude_indices=[5, 10, 15]
)
```

### Вариант 3: Анализ произвольного слова и поиск похожего

```python
from linguistic_features import analyze_word, find_most_similar_word
import json

# Анализируем новое слово
word_to_analyze = 'красивый'
features = analyze_word(word_to_analyze)

# Загружаем датасет
with open('output_audio/metadata.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# Ищем похожее слово из датасета
similar = find_most_similar_word(features, metadata['samples'])

print(f"Для слова '{word_to_analyze}' найдено похожее: '{similar['word']}'")
```

## Примеры

### Запуск тестового скрипта

```bash
python test_similarity.py
```

Скрипт протестирует функцию на нескольких словах из датасета и покажет результаты.

## Параметры функций

### `find_most_similar_word()`

- **target_word_data** (dict): данные целевого слова с характеристиками
- **all_words** (list): список всех слов для поиска
- **exclude_indices** (list, optional): индексы слов, которые нужно исключить
- **usage_weights** (dict, optional): словарь {index: count} для отслеживания частоты использования

**Возвращает**: словарь с данными наиболее похожего слова или `None`

### `find_similar_word_from_metadata()`

- **target_word_data** (dict): данные целевого слова
- **metadata_path** (str): путь к файлу metadata.json
- **exclude_indices** (list, optional): индексы для исключения

**Возвращает**: словарь с данными наиболее похожего слова или `None`

### `calculate_similarity_score()`

- **word1** (dict): первое слово
- **word2** (dict): второе слово

**Возвращает**: float - оценка сходства (чем выше, тем более похожи)

## Логика оценки

### Базовая оценка сходства

```
Оценка сходства = 100 (если POS совпадает, иначе -1000)
                + 10 × (количество совпадающих морфологических признаков)
                - 5 × (количество несовпадающих морфологических признаков)
                + до 5 (за схожую длину слова)
                + до 3 (за схожее соотношение гласных/согласных)
                + до 2 (за схожий процент гласных)
```

### Финальная оценка с учетом использования (NEW!)

```
Штраф за использование = usage_count × 15

Финальная оценка = Оценка сходства - Штраф за использование
```

**Пример:**
- Слово A: оценка сходства = 130, использовалось 0 раз → финальная оценка = 130
- Слово B: оценка сходства = 125, использовалось 1 раз → финальная оценка = 110
- Слово C: оценка сходства = 120, использовалось 2 раза → финальная оценка = 90

**Результат:** Выбирается слово A (130), несмотря на то что изначально было самым похожим.

## Интеграция в проект

Функции можно использовать для:

1. **Замены слов** - найти замену слову с сохранением грамматической структуры
2. **Генерации вариантов** - создать альтернативные версии текста
3. **Фильтрации** - отбирать слова с нужными характеристиками
4. **Анализа** - изучать лингвистическое разнообразие датасета
