"""
Модуль для анализа эмоциональных характеристик слов
Использует модель RuBERT для определения сентимента
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, Any
import logging


# Глобальные переменные для модели (инициализируются один раз)
_tokenizer = None
_model = None
_device = None

# Маппинг меток модели на эмоции (RuSentiment датасет: 5 классов)
SENTIMENT_LABELS = {
    0: "negative",     # негативный
    1: "neutral",      # нейтральный  
    2: "positive",     # позитивный
    3: "skip",         # пропустить (неопределенный)
    4: "speech"        # речевой акт
}


def initialize_model(logger: logging.Logger = None):
    """
    Инициализирует модель RuBERT для анализа сентимента
    Вызывается один раз при первом использовании
    Поддерживает локальную модель в ./models/emotion/
    """
    global _tokenizer, _model, _device
    
    if _model is not None:
        return  # Уже инициализировано
    
    # Определяем устройство
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Проверяем локальную модель
    import os
    local_model_paths = [
        "./models/emotion/rubert-ru-sentiment-rusentiment",
        "./models/emotion/rubert-ru-sentiment",  # Альтернативное название
        "./models/rubert-ru-sentiment-rusentiment",
        "./models/rubert-ru-sentiment",
        "./emotion_model"
    ]
    
    model_path = None
    for path in local_model_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Проверяем, что есть config.json
            if os.path.exists(os.path.join(path, "config.json")):
                model_path = path
                break
    
    if model_path:
        model_name_or_path = model_path
        model_source = f"локальная модель: {model_path}"
    else:
        model_name_or_path = "sismetanin/rubert-ru-sentiment-rusentiment"
        model_source = "HuggingFace Hub"
    
    if logger:
        logger.info("Загрузка модели RuBERT для анализа эмоций...")
        logger.info(f"Источник: {model_source}")
    
    try:
        # Загружаем токенизатор
        _tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        
        # Пытаемся загрузить с safetensors, если не получается - используем pytorch_model.bin
        try:
            _model = AutoModelForSequenceClassification.from_pretrained(
                model_name_or_path,
                use_safetensors=True
            )
        except (OSError, ValueError):
            # Fallback на pytorch_model.bin
            if logger:
                logger.info("Используется pytorch_model.bin (safetensors не найден)")
            _model = AutoModelForSequenceClassification.from_pretrained(
                model_name_or_path
            )
        
        # Переносим модель на устройство
        _model.to(_device)
        _model.eval()  # Режим оценки (не обучения)
        
        if logger:
            logger.info(f"✓ Модель загружена (устройство: {_device})")
            
    except Exception as e:
        if logger:
            logger.error(f"Ошибка при загрузке модели: {e}")
        raise


def analyze_emotion(word: str, logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Анализирует эмоциональную окраску слова с помощью RuBERT
    
    Args:
        word: слово для анализа
        logger: логгер (опционально)
        
    Returns:
        dict с ключами:
        - sentiment: "positive", "negative", "neutral"
        - sentiment_score: уверенность модели (0-1)
        - sentiment_probabilities: вероятности для всех классов
    """
    global _tokenizer, _model, _device
    
    # Инициализируем модель при первом вызове
    if _model is None:
        initialize_model(logger)
    
    try:
        # Токенизация
        inputs = _tokenizer(
            word,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(_device)
        
        # Предсказание
        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)[0]
        
        # Получаем предсказанный класс
        predicted_class = torch.argmax(probabilities).item()
        sentiment = SENTIMENT_LABELS.get(predicted_class, "neutral")
        sentiment_score = probabilities[predicted_class].item()
        
        # Вероятности для всех классов
        prob_dict = {
            "negative_prob": round(probabilities[0].item(), 4),
            "neutral_prob": round(probabilities[1].item(), 4),
            "positive_prob": round(probabilities[2].item(), 4),
            "skip_prob": round(probabilities[3].item(), 4),
            "speech_prob": round(probabilities[4].item(), 4)
        }
        
        return {
            "sentiment": sentiment,
            "sentiment_score": round(sentiment_score, 4),
            **prob_dict
        }
        
    except Exception as e:
        if logger:
            logger.warning(f"Ошибка при анализе эмоций для '{word}': {e}")
        
        # Возвращаем нейтральные значения при ошибке
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "negative_prob": 0.0,
            "neutral_prob": 1.0,
            "positive_prob": 0.0,
            "skip_prob": 0.0,
            "speech_prob": 0.0
        }


def cleanup_model():
    """
    Освобождает память, удаляя модель
    Вызывается при завершении работы
    """
    global _tokenizer, _model, _device
    
    if _model is not None:
        del _model
        del _tokenizer
        _model = None
        _tokenizer = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
