# Обновление: Штраф за частое использование слов

## Обзор

Добавлен механизм, который уменьшает вероятность повторного выбора слов, уже использованных в качестве замены. Это обеспечивает большее разнообразие при множественных заменах.

## Как это работает

### Формула
```
Финальная оценка = Оценка сходства - (Количество использований × 15)
```

### Пример
Есть 3 похожих слова:
- **газета** - сходство: 130
- **книга** - сходство: 125  
- **журнал** - сходство: 120

**Первая замена:**
- газета: 130 → выбирается

**Вторая замена (газета использована 1 раз):**
- газета: 130 - 15 = 115
- книга: 125 - 0 = 125 → выбирается
- журнал: 120 - 0 = 120

**Третья замена (газета и книга использованы):**
- газета: 130 - 15 = 115
- книга: 125 - 15 = 110
- журнал: 120 - 0 = 120 → выбирается

## Изменения в коде

### 1. JavaScript (`canvas.js`)
```javascript
state.usageAsReplacement = {}  // Трекинг использования слов

// При замене:
state.usageAsReplacement[originalIndex] = 
  (state.usageAsReplacement[originalIndex] || 0) + 1;

// Передача в API:
body: JSON.stringify({
  target_word: targetWord,
  exclude_indices: [targetWord.index],
  usage_as_replacement: state.usageAsReplacement  // NEW!
})
```

### 2. Python (`linguistic_features.py`)
```python
def find_most_similar_word(
    target_word_data: Dict[str, Any],
    all_words: List[Dict[str, Any]],
    exclude_indices: Optional[List[int]] = None,
    usage_weights: Optional[Dict[int, int]] = None  # NEW!
) -> Optional[Dict[str, Any]]:
    # Применяем штраф за использование
    usage_count = usage_weights.get(word_index, 0)
    usage_penalty = usage_count * 15
    final_score = similarity_score - usage_penalty
```

### 3. Flask API (`server.py`)
```python
@app.route('/api/find-similar-word', methods=['POST'])
def find_similar_word():
    usage_as_replacement = data.get('usage_as_replacement', {})
    usage_weights = {int(k): v for k, v in usage_as_replacement.items()}
    
    similar_word = find_most_similar_word(
        target_word_data=target_word,
        all_words=generator.samples,
        exclude_indices=exclude_indices,
        usage_weights=usage_weights  # NEW!
    )
```

## Настройка штрафа

Штраф по умолчанию: **15 баллов за каждое использование**

Чтобы изменить:
```python
# В linguistic_features.py, строка 233:
usage_penalty = usage_count * 15  # Измените 15 на нужное значение
```

**Рекомендации:**
- **5-10**: мягкий штраф, больше повторений
- **15-20**: сбалансированный (текущее значение)
- **25-30**: жесткий штраф, минимум повторений

## Тестирование

Запустите тест:
```bash
python test_similarity.py
```

Тест 3 покажет, как работает штраф:
```
ТЕСТ 3: Проверка штрафа за частое использование
---
ПОИСК 1 (без весов)
Найдено: 'газета' (индекс 5)

ПОИСК 2 (с весами: первое слово использовано 1 раз)
Найдено: 'книга' (индекс 12)
✓ Другое слово (штраф сработал!)

ПОИСК 3 (с весами: оба предыдущих слова использованы)
Найдено: 'журнал' (индекс 18)
✓ Новое слово!
```

## Преимущества

1. **Разнообразие** - каждое нажатие кнопки дает новое слово
2. **Автоматически** - не требуется ручное управление
3. **Гибко** - можно настроить силу штрафа
4. **Прозрачно** - логика видна в консоли браузера

## Визуализация

В Canvas:
- Замененные слова подкрашиваются оранжевым
- Интенсивность зависит от количества замен (до 5 уровней)
- Консоль показывает счетчики использования

## Сброс счетчиков

Счетчики сбрасываются при:
- Перезагрузке страницы
- Сбросе лупа (кнопка "⊗ СБРОС ЦИКЛА")

Для ручного сброса в консоли:
```javascript
state.usageAsReplacement = {}
state.replacementCount = {}
renderText()
```
