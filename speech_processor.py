#!/usr/bin/env python3
"""
Stochastic Speech Machine - процессор речи
Разбивает аудиозапись на отдельные слова и создает метаданные для каждого
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

import numpy as np
import librosa
import soundfile as sf
from vosk import Model, KaldiRecognizer

# Локальные модули для анализа
from audio_features import calculate_all_audio_features, add_relative_features
from linguistic_features import analyze_word


# Настройка логирования
def setup_logging(verbose: bool = False) -> logging.Logger:
    """Настраивает систему логирования"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Формат с временем и уровнем
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%H:%M:%S'
    
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def load_audio(file_path: Path, target_sr: int = 16000, logger: logging.Logger = None) -> tuple[np.ndarray, int]:
    """
    Загружает аудиофайл и конвертирует в нужный sample rate
    
    Args:
        file_path: путь к аудиофайлу
        target_sr: целевая частота дискретизации
        logger: логгер для вывода информации
        
    Returns:
        (audio, sample_rate) - аудио массив и частота дискретизации
    """
    if logger:
        logger.info(f"Загрузка аудиофайла: {file_path}")
        logger.info(f"Целевая частота дискретизации: {target_sr} Hz")
    
    start_time = time.time()
    audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
    load_time = time.time() - start_time
    
    duration = len(audio) / sr
    
    if logger:
        logger.info(f"✓ Аудио загружено за {load_time:.2f}s")
        logger.info(f"  Длительность: {duration:.2f}s ({len(audio)} семплов)")
        logger.info(f"  Sample rate: {sr} Hz")
    
    return audio, sr


def recognize_words_with_timestamps(
    audio: np.ndarray, 
    sr: int, 
    model_path: Path,
    logger: logging.Logger = None
) -> List[Dict[str, Any]]:
    """
    Распознает речь и возвращает слова с временными метками
    
    Args:
        audio: аудио массив
        sr: частота дискретизации
        model_path: путь к модели Vosk
        logger: логгер для вывода информации
        
    Returns:
        Список словарей с ключами: word, start, end, conf
    """
    if logger:
        logger.info("=" * 60)
        logger.info("ЭТАП 1: Распознавание речи")
        logger.info("=" * 60)
        logger.info(f"Загрузка модели Vosk из: {model_path}")
    
    start_time = time.time()
    model = Model(str(model_path))
    model_load_time = time.time() - start_time
    
    if logger:
        logger.info(f"✓ Модель загружена за {model_load_time:.2f}s")
    
    rec = KaldiRecognizer(model, sr)
    rec.SetWords(True)  # Включаем получение слов с временными метками
    
    if logger:
        logger.info("Конвертация аудио в формат для распознавания...")
    
    # Конвертируем float32 audio в int16 bytes
    audio_int16 = (audio * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    
    if logger:
        logger.info("Обработка аудио...")
        logger.info(f"Размер данных: {len(audio_bytes) / 1024 / 1024:.2f} MB")
    
    # Обрабатываем аудио чанками
    chunk_size = 4000
    total_chunks = len(audio_bytes) // chunk_size + 1
    
    start_recognition = time.time()
    
    for i in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[i:i + chunk_size]
        rec.AcceptWaveform(chunk)
        
        # Прогресс каждые 20%
        current_chunk = i // chunk_size + 1
        if logger and current_chunk % max(1, total_chunks // 5) == 0:
            progress = (i / len(audio_bytes)) * 100
            logger.info(f"  Прогресс распознавания: {progress:.1f}%")
    
    # Получаем финальный результат
    if logger:
        logger.info("Финализация распознавания...")
    
    result = json.loads(rec.FinalResult())
    recognition_time = time.time() - start_recognition
    
    all_words = []
    
    if "result" in result:
        for word_info in result["result"]:
            all_words.append({
                "word": word_info["word"],
                "start": word_info["start"],
                "end": word_info["end"],
                "conf": word_info.get("conf", 1.0)
            })
    
    if logger:
        logger.info(f"✓ Распознавание завершено за {recognition_time:.2f}s")
        logger.info(f"✓ Распознано слов: {len(all_words)}")
        
        if len(all_words) > 0:
            logger.info(f"  Первое слово: '{all_words[0]['word']}'")
            logger.info(f"  Последнее слово: '{all_words[-1]['word']}'")
    
    return all_words


def extract_and_save_samples(
    audio: np.ndarray,
    sr: int,
    words: List[Dict[str, Any]],
    output_dir: Path,
    original_file: Path,
    logger: logging.Logger = None
) -> List[Dict[str, Any]]:
    """
    Извлекает аудио сегменты для каждого слова и сохраняет их
    
    Args:
        audio: аудио массив
        sr: частота дискретизации
        words: список распознанных слов с временными метками
        output_dir: директория для сохранения
        original_file: путь к исходному файлу
        logger: логгер для вывода информации
        
    Returns:
        Список метаданных для каждого семпла
    """
    if logger:
        logger.info("=" * 60)
        logger.info("ЭТАП 2: Извлечение и сохранение семплов")
        logger.info("=" * 60)
    
    samples_dir = output_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    if logger:
        logger.info(f"Директория для семплов: {samples_dir}")
        logger.info(f"Всего слов для обработки: {len(words)}")
        logger.info("Расчет акустических и лингвистических характеристик...")
    
    samples_metadata = []
    start_time = time.time()
    
    # Общая длительность для относительных метрик
    audio_duration = len(audio) / sr
    
    for idx, word_info in enumerate(words):
        word = word_info["word"]
        start_time_word = word_info["start"]
        end_time_word = word_info["end"]
        confidence = word_info["conf"]
        
        # Конвертируем время в индексы семплов
        start_sample = int(start_time_word * sr)
        end_sample = int(end_time_word * sr)
        
        # Извлекаем аудио сегмент
        audio_segment = audio[start_sample:end_sample]
        
        if len(audio_segment) == 0:
            if logger:
                logger.warning(f"  [{idx+1}/{len(words)}] Пропуск пустого сегмента для слова '{word}'")
            continue
        
        # Формируем имя файла (номер + слово)
        sample_filename = f"{idx:04d}_{word}.wav"
        sample_path = samples_dir / sample_filename
        
        # Сохраняем аудио сегмент
        sf.write(sample_path, audio_segment, sr)
        
        # === АКУСТИЧЕСКИЙ АНАЛИЗ ===
        audio_features = calculate_all_audio_features(audio_segment, sr)
        
        # === ЛИНГВИСТИЧЕСКИЙ АНАЛИЗ ===
        linguistic_features = analyze_word(word)
        
        # Собираем все метаданные
        metadata = {
            "index": idx,
            "word": word,
            "filename": sample_filename,
            "start_time": round(start_time_word, 3),
            "end_time": round(end_time_word, 3),
            "confidence": round(confidence, 3)
        }
        
        # Добавляем акустические характеристики
        metadata.update(audio_features)
        
        # Добавляем лингвистические характеристики
        metadata.update(linguistic_features)
        
        samples_metadata.append(metadata)
        
        # Логирование прогресса
        if logger:
            # Каждые 10 слов или для первых/последних
            if idx < 3 or idx >= len(words) - 3 or (idx + 1) % 10 == 0:
                duration = metadata['duration']
                pitch = metadata.get('pitch_mean', 0)
                pos = metadata.get('pos', 'N/A')
                logger.info(
                    f"  [{idx+1}/{len(words)}] '{word}' - "
                    f"{duration:.3f}s, {pitch:.0f}Hz, {pos}"
                )
            elif (idx + 1) % 10 == 1:  # Показываем что мы работаем
                logger.info(f"  Обработка слов {idx+1}-{min(idx+10, len(words))}...")
    
    processing_time = time.time() - start_time
    
    if logger:
        logger.info(f"✓ Обработка завершена за {processing_time:.2f}s")
        logger.info(f"✓ Сохранено семплов: {len(samples_metadata)}")
        logger.info("Расчет относительных характеристик...")
    
    # Добавляем относительные характеристики (нормализованные по всем словам)
    samples_metadata = add_relative_features(samples_metadata, audio_duration)
    
    if logger:
        logger.info("✓ Относительные характеристики добавлены")
    
    return samples_metadata


def save_metadata(
    metadata: List[Dict[str, Any]],
    output_dir: Path,
    original_file: Path,
    sr: int,
    logger: logging.Logger = None
):
    """
    Сохраняет метаданные в JSON файл
    
    Args:
        metadata: список метаданных
        output_dir: директория для сохранения
        original_file: путь к исходному файлу
        sr: частота дискретизации
        logger: логгер для вывода информации
    """
    if logger:
        logger.info("=" * 60)
        logger.info("ЭТАП 3: Сохранение метаданных")
        logger.info("=" * 60)
    
    json_path = output_dir / "metadata.json"
    
    output_data = {
        "source_file": str(original_file.absolute()),
        "sample_rate": sr,
        "total_words": len(metadata),
        "metadata_version": "2.0",
        "description": "Полные метаданные с акустическими и лингвистическими характеристиками",
        "features": {
            "acoustic": [
                "duration (абсолютная и относительная)",
                "amplitude (RMS, peak, относительная громкость)",
                "pitch (mean, min, max, std, относительная)",
                "spectral (centroid, bandwidth, flatness, rolloff)",
                "mfcc (13 коэффициентов тембра)",
                "energy_envelope (attack_time, variance)",
                "voicing (zero_crossing_rate)"
            ],
            "linguistic": [
                "морфология (часть речи, род, число, падеж, время)",
                "нормальная форма слова",
                "фонетика (длина, гласные/согласные, звонкие/глухие)",
                "процентные соотношения букв"
            ]
        },
        "samples": metadata
    }
    
    if logger:
        logger.info(f"Запись в файл: {json_path}")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    if logger:
        logger.info(f"✓ Метаданные сохранены")
        logger.info(f"  Размер файла: {json_path.stat().st_size / 1024:.2f} KB")


def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description="Stochastic Speech Machine - разбивает аудио на слова и создает метаданные",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python speech_processor.py audio.mp3 -m ~/.cache/speech2text/models/vosk/ru/vosk-model-small-ru-0.22
  python speech_processor.py recording.wav -m ./models/vosk-model-small-ru-0.22 -o output
  python speech_processor.py podcast.mp3 -m ./models/vosk-model-small-en-us-0.15 -v
        """
    )
    
    parser.add_argument(
        "audio_file",
        type=Path,
        help="Путь к входному аудиофайлу (WAV, MP3, FLAC и др.)"
    )
    
    parser.add_argument(
        "-m", "--model",
        type=Path,
        required=True,
        help="Путь к модели Vosk для распознавания речи"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Директория для вывода (по умолчанию: output_<filename>)"
    )
    
    parser.add_argument(
        "-r", "--sample-rate",
        type=int,
        default=16000,
        help="Частота дискретизации для обработки (по умолчанию: 16000)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод (DEBUG уровень логирования)"
    )
    
    return parser.parse_args()


def main() -> int:
    """Основная функция программы"""
    args = parse_args()
    
    # Настраиваем логирование
    logger = setup_logging(args.verbose)
    
    # Проверяем входной файл
    if not args.audio_file.exists():
        logger.error(f"Файл не найден: {args.audio_file}")
        return 1
    
    # Проверяем модель
    if not args.model.exists():
        logger.error(f"Модель не найдена: {args.model}")
        logger.error("Используйте --model для указания пути к модели Vosk")
        logger.info("Скачать модель можно с https://alphacephei.com/vosk/models")
        return 1
    
    # Определяем выходную директорию
    if args.output:
        output_dir = args.output
    else:
        output_dir = Path(f"output_{args.audio_file.stem}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Начало обработки
    logger.info("")
    logger.info("=" * 60)
    logger.info("STOCHASTIC SPEECH MACHINE")
    logger.info("=" * 60)
    logger.info(f"Входной файл: {args.audio_file}")
    logger.info(f"Размер файла: {args.audio_file.stat().st_size / 1024 / 1024:.2f} MB")
    logger.info(f"Выходная директория: {output_dir}")
    logger.info(f"Модель Vosk: {args.model}")
    logger.info(f"Sample rate: {args.sample_rate} Hz")
    logger.info("=" * 60)
    logger.info("")
    
    total_start_time = time.time()
    
    try:
        # Загружаем аудио
        audio, sr = load_audio(args.audio_file, args.sample_rate, logger)
        logger.info("")
        
        # Распознаем слова
        words = recognize_words_with_timestamps(audio, sr, args.model, logger)
        logger.info("")
        
        if not words:
            logger.error("Слова не распознаны в аудиофайле")
            logger.info("Возможные причины:")
            logger.info("  - Плохое качество записи")
            logger.info("  - Неправильная модель (проверьте язык)")
            logger.info("  - Отсутствие речи в файле")
            return 1
        
        # Извлекаем и сохраняем семплы
        samples_metadata = extract_and_save_samples(
            audio, sr, words, output_dir, args.audio_file, logger
        )
        logger.info("")
        
        # Сохраняем метаданные
        save_metadata(samples_metadata, output_dir, args.audio_file, sr, logger)
        logger.info("")
        
        # Финальная статистика
        total_time = time.time() - total_start_time
        
        logger.info("=" * 60)
        logger.info("✓ ОБРАБОТКА ЗАВЕРШЕНА!")
        logger.info("=" * 60)
        logger.info(f"Общее время: {total_time:.2f}s")
        logger.info(f"Обработано слов: {len(samples_metadata)}")
        logger.info(f"Директория семплов: {output_dir / 'samples'}")
        logger.info(f"Файл метаданных: {output_dir / 'metadata.json'}")
        logger.info("=" * 60)
        logger.info("")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\nОбработка прервана пользователем")
        return 130
        
    except Exception as e:
        logger.error(f"\n\nОшибка при обработке: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
