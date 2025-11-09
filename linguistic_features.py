"""
Модуль для лингвистического анализа слов
"""

import pymorphy3
from typing import Dict, Any


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
