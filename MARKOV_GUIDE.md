# 🎲 Markov Chain генератор

Документация по использованию Markov Chain для генерации стохастической речи.

## Что такое Markov Chain?

**Цепь Маркова** — это вероятностная модель, которая предсказывает следующее состояние на основе текущего состояния. В контексте речи:

- **Текущее состояние** = текущее слово/эмоция/часть речи
- **Следующее состояние** = следующее слово/эмоция/часть речи
- **Вероятность перехода** = как часто одно состояние следует за другим в исходных данных

### Преимущества:
✅ Не требует обучения нейросети  
✅ Работает на малом количестве данных (даже 100+ слов)  
✅ Быстро работает  
✅ Легко интерпретируется  
✅ Генерирует связные последовательности  

### Как работает:
```
Исходная последовательность: "заложник" → "гау" → "шестая" → "история"

Матрица переходов:
  "заложник" → "гау" (100%)
  "гау" → "шестая" (100%)
  "шестая" → "история" (100%)

При генерации:
  Текущее: "заложник" → выбираем "гау" с вероятностью 100%
  Текущее: "гау" → выбираем "шестая" с вероятностью 100%
```

Если одно слово встречается в разных контекстах, вероятности распределяются:
```
"слово" → "А" (60%), "Б" (30%), "В" (10%)
```

---

## 📦 Что добавлено

### 1. Markov Chain правила для генератора

Новые правила в `generator/rules/markov.py`:

#### **MarkovChainBigramRule** 
Переходы между словами (биграммы).

```python
from generator.rules.markov import MarkovChainBigramRule

rule = MarkovChainBigramRule(samples, weight=1.0, smoothing=0.01)
```

**Параметры:**
- `smoothing` (0-1) - сглаживание для редких переходов

---

#### **MarkovEmotionalRule**
Переходы между эмоциями (sentiment).

```python
from generator.rules.markov import MarkovEmotionalRule

rule = MarkovEmotionalRule(samples, weight=0.5, smoothing=0.1)
```

**Применение:** Генерация эмоционально связной речи.

---

#### **MarkovPOSRule**
Переходы между частями речи (POS tags).

```python
from generator.rules.markov import MarkovPOSRule

rule = MarkovPOSRule(samples, weight=0.8, smoothing=0.1)
```

**Применение:** Генерация грамматически корректных последовательностей.

---

#### **MarkovChainRule** (продвинутая)
Комплексное правило, учитывающее слово + POS + эмоцию.

```python
from generator.rules.markov import MarkovChainRule

rule = MarkovChainRule(
    samples,
    order=1,            # Порядок цепи (1, 2, 3)
    use_pos=True,       # Учитывать часть речи
    use_sentiment=True, # Учитывать эмоцию
    weight=1.0,
    smoothing=0.01
)
```

**Параметры:**
- `order` - порядок цепи Маркова (сколько предыдущих состояний учитывать)
- `use_pos` - включить часть речи в состояние
- `use_sentiment` - включить эмоцию в состояние

---

### 2. Standalone генератор

Независимый скрипт `markov_generator.py` для использования без веб-интерфейса.

---

## 🚀 Использование

### Вариант 1: Через веб-интерфейс генератора

Запустите веб-генератор:
```bash
cd generator
python server.py --metadata ../output_audio/metadata.json
```

В интерфейсе добавьте правила Markov Chain:
1. **Markov Bigram** - для последовательности слов
2. **Markov Emotional** - для эмоциональной динамики
3. **Markov POS** - для грамматической структуры

Комбинируйте с другими правилами (акустическими, фонетическими).

---

### Вариант 2: Standalone скрипт

#### Базовое использование

```bash
# Простая генерация 10 слов
python markov_generator.py output_audio/metadata.json

# Указать длину последовательности
python markov_generator.py output_audio/metadata.json -n 20

# Начать с конкретного слова
python markov_generator.py output_audio/metadata.json --start заложник -n 15
```

#### С фильтрами

```bash
# Только слова с положительной эмоцией
python markov_generator.py output_audio/metadata.json --emotion positive -n 12

# Только существительные
python markov_generator.py output_audio/metadata.json --pos NOUN -n 10

# Комбинация фильтров
python markov_generator.py output_audio/metadata.json --emotion neutral --pos VERB -n 8
```

#### С аналитикой

```bash
# Показать детали (эмоции, POS, pitch, duration)
python markov_generator.py output_audio/metadata.json --details

# Показать статистику переходов
python markov_generator.py output_audio/metadata.json --analyze

# Сгенерировать 3 последовательности
python markov_generator.py output_audio/metadata.json -n 15 -c 3
```

---

### Вариант 3: Программно в Python

```python
from markov_generator import SimpleMarkovGenerator

# Создаем генератор
gen = SimpleMarkovGenerator('output_audio/metadata.json')

# Генерируем последовательность
sequence = gen.generate_sequence(
    length=10,
    start_word='заложник',
    emotion_filter='positive'
)

# Выводим результат
gen.print_sequence(sequence, show_details=True)

# Анализ переходов
gen.analyze_transitions()
```

---

### Вариант 4: Интеграция в существующий генератор

```python
from generator.generator import StochasticGenerator
from generator.rules.markov import MarkovChainBigramRule, MarkovEmotionalRule

# Создаем генератор
gen = StochasticGenerator('output_audio/metadata.json')

# Добавляем Markov правила
bigram = MarkovChainBigramRule(gen.samples, weight=0.7)
emotion = MarkovEmotionalRule(gen.samples, weight=0.3)

gen.add_rule(bigram)
gen.add_rule(emotion)

# Устанавливаем температуру
gen.set_temperature(0.8)

# Генерируем
sequence = gen.generate_sequence(length=15)

# Выводим
for sample in sequence:
    print(sample['word'], sample.get('sentiment'))
```

---

## 🧪 Тестирование

Быстрый тест всех Markov правил:

```bash
python test_markov.py
```

Тест проверит:
1. ✅ Markov Bigram (переходы между словами)
2. ✅ Markov Emotional (переходы между эмоциями)
3. ✅ Markov POS (переходы между частями речи)
4. ✅ Комбинацию правил

---

## 📊 Примеры

### Пример 1: Генерация с эмоциональной динамикой

```bash
python markov_generator.py output_audio/metadata.json -n 15 --details
```

**Результат:**
```
 1. заложник         [neutral] [NOUN ] 201Hz 0.75s
 2. гау              [skip   ] [N/A  ] 332Hz 0.36s
 3. шестая           [neutral] [ADJF ] 190Hz 0.42s
 4. история          [neutral] [NOUN ] 188Hz 0.51s
 5. показывает       [neutral] [VERB ] 195Hz 0.69s
 ...
```

---

### Пример 2: Только позитивные слова

```bash
python markov_generator.py output_audio/metadata.json --emotion positive -n 10
```

**Результат:**
```
 1. радость
 2. счастье
 3. любовь
 4. солнце
 5. улыбка
 ...
```

---

### Пример 3: Грамматическая структура (NOUN → VERB → NOUN)

```bash
python markov_generator.py output_audio/metadata.json --pos NOUN -n 5
```

---

### Пример 4: Анализ переходов

```bash
python markov_generator.py output_audio/metadata.json --analyze
```

**Результат:**
```
📊 СТАТИСТИКА ПЕРЕХОДОВ
==========================================================

🔤 Топ-10 переходов между словами:
   1. 'заложник' → 'гау' (100.0%)
   2. 'гау' → 'шестая' (100.0%)
   3. 'шестая' → 'история' (100.0%)
   ...

😊 Переходы между эмоциями:
  neutral    → neutral    (65.3%)
  positive   → neutral    (55.0%)
  negative   → neutral    (48.2%)
  skip       → neutral    (52.1%)

📝 Переходы между частями речи:
  NOUN   → VERB   (42.5%)
  VERB   → NOUN   (38.1%)
  ADJF   → NOUN   (52.3%)
  ...
```

---

## 🎛️ Параметры и настройки

### Параметры правил

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `weight` | float | 0.0-2.0 | Вес правила в генераторе |
| `smoothing` | float | 0.0-1.0 | Сглаживание для нулевых вероятностей |
| `order` | int | 1-3 | Порядок цепи Маркова (для MarkovChainRule) |
| `use_pos` | bool | True/False | Учитывать часть речи |
| `use_sentiment` | bool | True/False | Учитывать эмоцию |

### Параметры генератора

```python
gen.set_temperature(0.8)  # 0.1 = детерминированно, 2.0 = хаос
```

**Температура:**
- `0.1-0.3` - всегда выбирает наиболее вероятное
- `0.8-1.2` - стандартная случайность
- `1.5-2.0` - максимальная вариативность

---

## 💡 Советы и лучшие практики

### 1. Комбинируйте правила
Не используйте только Markov - комбинируйте с акустическими правилами:

```python
# 50% Markov + 30% Pitch + 20% Emotion Wave
gen.add_rule(MarkovChainBigramRule(samples, weight=0.5))
gen.add_rule(PitchProximityRule(max_diff=30, weight=0.3))
gen.add_rule(EmotionWaveRule(wave=['positive', 'neutral'], weight=0.2))
```

### 2. Начинайте с простого
- Сначала попробуйте **MarkovChainBigramRule** (самое простое)
- Потом добавьте **MarkovEmotionalRule**
- Экспериментируйте с весами

### 3. Используйте фильтры
```bash
# Генерируйте только нужные эмоции или части речи
--emotion positive --pos NOUN
```

### 4. Анализируйте данные
Запустите `--analyze` чтобы понять, какие переходы есть в ваших данных:
```bash
python markov_generator.py output_audio/metadata.json --analyze
```

### 5. Настраивайте smoothing
- **Большой датасет** (1000+ слов) → `smoothing=0.001`
- **Малый датасет** (100-500 слов) → `smoothing=0.01-0.1`
- Если генератор зацикливается → увеличьте `smoothing`

---

## 🔧 Расширение

### Создание своего Markov правила

```python
from generator.rules.base import Rule
from collections import defaultdict

class MyCustomMarkovRule(Rule):
    def __init__(self, samples, **kwargs):
        super().__init__(name="My Markov", **kwargs)
        self.samples = samples
        self.transitions = defaultdict(lambda: defaultdict(int))
        self._build_model()
    
    def _build_model(self):
        # Ваша логика построения модели
        for i in range(len(self.samples) - 1):
            current = self.samples[i]
            next_sample = self.samples[i + 1]
            
            # Считаем переходы
            current_state = self._get_state(current)
            next_state = self._get_state(next_sample)
            self.transitions[current_state][next_state] += 1
    
    def _get_state(self, sample):
        # Определяем состояние (например, по высоте тона)
        pitch = sample.get('pitch_mean', 0)
        if pitch < 150:
            return "low"
        elif pitch < 250:
            return "mid"
        else:
            return "high"
    
    def score(self, current_sample, candidate_sample, context):
        if not current_sample:
            return 0.5
        
        current_state = self._get_state(current_sample)
        candidate_state = self._get_state(candidate_sample)
        
        # Возвращаем вероятность перехода
        if current_state in self.transitions:
            total = sum(self.transitions[current_state].values())
            count = self.transitions[current_state].get(candidate_state, 0)
            return count / total if total > 0 else 0.01
        
        return 0.01
```

---

## 🐛 Решение проблем

### Генератор зацикливается на одних и тех же словах
**Решение:**
- Увеличьте `smoothing` параметр
- Увеличьте `temperature` генератора
- Комбинируйте с другими правилами

### Нет разнообразия
**Решение:**
- Увеличьте temperature до 1.2-1.5
- Используйте фильтры (`--emotion`, `--pos`)
- Комбинируйте несколько Markov правил с разными весами

### Ошибка "состояние не найдено"
**Решение:**
- Увеличьте `smoothing` до 0.1-0.5
- Проверьте, что в данных есть все необходимые атрибуты (POS, sentiment)

### Слишком хаотично
**Решение:**
- Уменьшите temperature до 0.3-0.5
- Увеличьте вес Markov правила
- Используйте **MarkovChainRule** с `use_pos=True`

---

## 📚 Ссылки

- **Основной README**: [README.md](README.md)
- **Генератор**: [generator/README.md](generator/README.md)
- **Метаданные**: [METADATA_GUIDE.md](METADATA_GUIDE.md)

---

## 🎯 Итоги

Markov Chain добавляет в генератор:
- ✅ Вероятностную модель переходов между состояниями
- ✅ Генерацию связных последовательностей без обучения нейросети
- ✅ Работу на малых датасетах (100+ слов)
- ✅ Быструю генерацию
- ✅ Интерпретируемость результатов

**Попробуйте:**
```bash
# Быстрый старт
python markov_generator.py output_audio/metadata.json -n 15 --details

# Тест
python test_markov.py

# С веб-интерфейсом
cd generator && python server.py --metadata ../output_audio/metadata.json
```

Приятной генерации! 🎲✨
