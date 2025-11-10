"""
Модуль для лингвистического анализа слов
"""

import pymorphy3
import json
from typing import Dict, Any, List, Optional


# Инициализируем морфологический анализатор (делаем это один раз)
morph = pymorphy3.MorphAnalyzer()


# Классификация букв русского алфавита
VOWELS = set('аеёиоуыэюяАЕЁИОУЫЭЮЯ')
CONSONANTS = set('бвгджзйклмнпрстфхцчшщБВГДЖЗЙКЛМНПРСТФХЦЧШЩ')
VOICED_CONSONANTS = set('бвгджзлмнрБВГДЖЗЛМНР')
VOICELESS_CONSONANTS = set('кпстфхцчшщКПСТФХЦЧШЩ')


def analyze_morphology(word: str) -> Dict[str, Any]:
    """
    Анализирует морфологические характеристики слова
    
    Args:
        word: слово для анализа
        
    Returns:
        dict с морфологическими характеристиками
    """
    parsed = morph.parse(word)[0]  # Берем первый (наиболее вероятный) разбор
    
    # Извлекаем характеристики
    pos = parsed.tag.POS  # Часть речи
    animacy = parsed.tag.animacy  # Одушевленность
    gender = parsed.tag.gender  # Род
    number = parsed.tag.number  # Число
    case = parsed.tag.case  # Падеж
    tense = parsed.tag.tense  # Время (для глаголов)
    person = parsed.tag.person  # Лицо
    
    # Нормальная форма
    normal_form = parsed.normal_form
    
    return {
        "normal_form": normal_form,
        "pos": str(pos) if pos else None,
        "animacy": str(animacy) if animacy else None,
        "gender": str(gender) if gender else None,
        "number": str(number) if number else None,
        "case": str(case) if case else None,
        "tense": str(tense) if tense else None,
        "person": str(person) if person else None
    }


def analyze_phonetics(word: str) -> Dict[str, Any]:
    """
    Анализирует фонетические характеристики слова
    
    Args:
        word: слово для анализа
        
    Returns:
        dict с фонетическими характеристиками
    """
    # Считаем буквы разных типов
    total_letters = len(word)
    
    vowels_count = sum(1 for char in word if char in VOWELS)
    consonants_count = sum(1 for char in word if char in CONSONANTS)
    voiced_count = sum(1 for char in word if char in VOICED_CONSONANTS)
    voiceless_count = sum(1 for char in word if char in VOICELESS_CONSONANTS)
    
    # Процентные соотношения
    vowels_percent = round(vowels_count / total_letters * 100, 2) if total_letters > 0 else 0.0
    consonants_percent = round(consonants_count / total_letters * 100, 2) if total_letters > 0 else 0.0
    voiced_percent = round(voiced_count / total_letters * 100, 2) if total_letters > 0 else 0.0
    voiceless_percent = round(voiceless_count / total_letters * 100, 2) if total_letters > 0 else 0.0
    
    # Соотношение гласных к согласным
    vowel_consonant_ratio = round(vowels_count / consonants_count, 3) if consonants_count > 0 else 0.0
    
    return {
        "word_length": total_letters,
        "vowels_count": vowels_count,
        "consonants_count": consonants_count,
        "voiced_consonants_count": voiced_count,
        "voiceless_consonants_count": voiceless_count,
        "vowels_percent": vowels_percent,
        "consonants_percent": consonants_percent,
        "voiced_percent": voiced_percent,
        "voiceless_percent": voiceless_percent,
        "vowel_consonant_ratio": vowel_consonant_ratio
    }


def analyze_word(word: str) -> Dict[str, Any]:
    """
    Полный лингвистический анализ слова
    
    Args:
        word: слово для анализа
        
    Returns:
        dict со всеми лингвистическими характеристиками
    """
    features = {}
    
    # Морфология
    features.update(analyze_morphology(word))
    
    # Фонетика
    features.update(analyze_phonetics(word))
    
    return features


def calculate_similarity_score(word1: Dict[str, Any], word2: Dict[str, Any]) -> float:
    """
    Вычисляет оценку сходства между двумя словами на основе лингвистических характеристик
    
    Приоритет:
    1. Часть речи (POS) - наивысший приоритет
    2. Морфологические характеристики (род, число, падеж, время, лицо, одушевленность)
    3. Фонетические характеристики
    
    Args:
        word1: первое слово (словарь с характеристиками)
        word2: второе слово (словарь с характеристиками)
        
    Returns:
        float: оценка сходства (чем выше, тем более похожи слова)
    """
    score = 0.0
    
    # 1. Часть речи - критически важно (вес 100)
    if word1.get('pos') == word2.get('pos') and word1.get('pos') is not None:
        score += 100
    else:
        # Если части речи не совпадают, это слово не подходит
        return -1000
    
    # 2. Морфологические характеристики (вес 10 за каждое совпадение)
    morph_features = ['gender', 'number', 'case', 'tense', 'person', 'animacy']
    for feature in morph_features:
        val1 = word1.get(feature)
        val2 = word2.get(feature)
        # Совпадение (включая случаи, когда оба None)
        if val1 == val2:
            score += 10
        # Если оба не None, но не совпадают - штраф
        elif val1 is not None and val2 is not None:
            score -= 5
    
    # 3. Фонетические характеристики (меньший вес)
    # Длина слова (вес 5)
    len1 = word1.get('word_length', 0)
    len2 = word2.get('word_length', 0)
    if len1 > 0 and len2 > 0:
        len_diff = abs(len1 - len2)
        score += max(0, 5 - len_diff)
    
    # Соотношение гласных к согласным (вес 3)
    ratio1 = word1.get('vowel_consonant_ratio', 0)
    ratio2 = word2.get('vowel_consonant_ratio', 0)
    ratio_diff = abs(ratio1 - ratio2)
    score += max(0, 3 - ratio_diff * 2)
    
    # Процент гласных (вес 2)
    vowels1 = word1.get('vowels_percent', 0)
    vowels2 = word2.get('vowels_percent', 0)
    vowels_diff = abs(vowels1 - vowels2)
    score += max(0, 2 - vowels_diff / 10)
    
    return score


def find_most_similar_word(
    target_word_data: Dict[str, Any],
    all_words: List[Dict[str, Any]],
    exclude_indices: Optional[List[int]] = None,
    usage_weights: Optional[Dict[int, int]] = None
) -> Optional[Dict[str, Any]]:
    """
    Находит наиболее похожее слово из набора данных с учетом весов использования
    
    Приоритет поиска:
    1. Сначала совпадение части речи (POS)
    2. Затем максимальное совпадение морфологических характеристик
    3. Затем фонетическое сходство
    4. Штраф за частое использование в качестве замены
    
    Args:
        target_word_data: данные целевого слова (словарь с характеристиками)
        all_words: список всех слов для поиска
        exclude_indices: список индексов слов, которые нужно исключить из поиска
        usage_weights: словарь {index: usage_count} - сколько раз слово использовалось как замена
        
    Returns:
        Dict или None: наиболее похожее слово или None, если не найдено
    """
    if not all_words:
        return None
    
    exclude_set = set(exclude_indices) if exclude_indices else set()
    usage_weights = usage_weights or {}
    
    # Собираем кандидатов с оценками
    candidates = []
    
    for word_data in all_words:
        # Пропускаем паузы
        if word_data.get('type') != 'word':
            continue
        
        # Пропускаем исключенные индексы
        word_index = word_data.get('index')
        if word_index in exclude_set:
            continue
        
        # Вычисляем оценку сходства
        similarity_score = calculate_similarity_score(target_word_data, word_data)
        
        # Если части речи не совпадают, пропускаем
        if similarity_score < 0:
            continue
        
        # Применяем штраф за использование
        # Чем чаще слово использовалось, тем меньше его финальная оценка
        usage_count = usage_weights.get(word_index, 0)
        # Штраф: каждое использование уменьшает оценку на 15 баллов
        usage_penalty = usage_count * 15
        final_score = similarity_score - usage_penalty
        
        candidates.append({
            'word_data': word_data,
            'similarity_score': similarity_score,
            'usage_count': usage_count,
            'final_score': final_score
        })
    
    if not candidates:
        return None
    
    # Сортируем кандидатов по финальной оценке
    candidates.sort(key=lambda x: x['final_score'], reverse=True)
    
    # Возвращаем лучшего кандидата
    best_candidate = candidates[0]
    
    return best_candidate['word_data']


def find_similar_word_from_metadata(
    target_word_data: Dict[str, Any],
    metadata_path: str,
    exclude_indices: Optional[List[int]] = None
) -> Optional[Dict[str, Any]]:
    """
    Находит наиболее похожее слово из файла метаданных
    
    Args:
        target_word_data: данные целевого слова
        metadata_path: путь к файлу metadata.json
        exclude_indices: список индексов слов, которые нужно исключить
        
    Returns:
        Dict или None: наиболее похожее слово
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    all_words = metadata.get('samples', [])
    
    return find_most_similar_word(target_word_data, all_words, exclude_indices)
