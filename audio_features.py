"""
Модуль для расчета акустических характеристик аудио
"""

import numpy as np
import librosa
from typing import Dict, Any


def calculate_amplitude_features(audio_segment: np.ndarray) -> Dict[str, float]:
    """
    Рассчитывает характеристики амплитуды/громкости
    
    Returns:
        dict с ключами: rms, peak_amplitude
    """
    # RMS - средняя громкость
    rms = float(np.sqrt(np.mean(audio_segment ** 2)))
    
    # Пиковая амплитуда
    peak_amplitude = float(np.max(np.abs(audio_segment)))
    
    return {
        "rms": round(rms, 6),
        "peak_amplitude": round(peak_amplitude, 6)
    }


def calculate_pitch_features(audio_segment: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Рассчитывает характеристики основной частоты (pitch)
    
    Returns:
        dict с ключами: pitch_mean, pitch_min, pitch_max, pitch_std
    """
    try:
        # Используем pyin для более точного определения pitch
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_segment,
            fmin=librosa.note_to_hz('C2'),  # ~65 Hz
            fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
            sr=sr
        )
        
        # Фильтруем только звонкие части
        valid_f0 = f0[~np.isnan(f0)]
        
        if len(valid_f0) > 0:
            pitch_mean = float(np.mean(valid_f0))
            pitch_min = float(np.min(valid_f0))
            pitch_max = float(np.max(valid_f0))
            pitch_std = float(np.std(valid_f0))
        else:
            pitch_mean = pitch_min = pitch_max = pitch_std = 0.0
            
    except Exception:
        pitch_mean = pitch_min = pitch_max = pitch_std = 0.0
    
    return {
        "pitch_mean": round(pitch_mean, 2),
        "pitch_min": round(pitch_min, 2),
        "pitch_max": round(pitch_max, 2),
        "pitch_std": round(pitch_std, 2)
    }


def calculate_spectral_features(audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Рассчитывает спектральные характеристики
    
    Returns:
        dict с ключами: spectral_centroid, spectral_bandwidth, 
        spectral_flatness, spectral_rolloff, mfcc_mean
    """
    # Адаптивный n_fft в зависимости от длины сегмента
    n_fft = min(2048, len(audio_segment))
    # n_fft должен быть степенью двойки
    n_fft = 2 ** int(np.log2(n_fft))
    
    # Spectral Centroid - "яркость" звука
    spectral_centroid = librosa.feature.spectral_centroid(y=audio_segment, sr=sr, n_fft=n_fft)[0]
    centroid_mean = float(np.mean(spectral_centroid))
    
    # Spectral Bandwidth - ширина спектра
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_segment, sr=sr, n_fft=n_fft)[0]
    bandwidth_mean = float(np.mean(spectral_bandwidth))
    
    # Spectral Flatness - шумность/тональность (0=тональный, 1=шумный)
    spectral_flatness = librosa.feature.spectral_flatness(y=audio_segment, n_fft=n_fft)[0]
    flatness_mean = float(np.mean(spectral_flatness))
    
    # Spectral Rolloff - частота, ниже которой 85% энергии
    spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_segment, sr=sr, roll_percent=0.85, n_fft=n_fft)[0]
    rolloff_mean = float(np.mean(spectral_rolloff))
    
    # MFCC - тембральные характеристики (13 коэффициентов)
    mfcc = librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=13, n_fft=n_fft)
    mfcc_mean = [round(float(np.mean(mfcc[i])), 4) for i in range(13)]
    
    return {
        "spectral_centroid": round(centroid_mean, 2),
        "spectral_bandwidth": round(bandwidth_mean, 2),
        "spectral_flatness": round(flatness_mean, 4),
        "spectral_rolloff": round(rolloff_mean, 2),
        "mfcc_mean": mfcc_mean
    }


def calculate_energy_envelope(audio_segment: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Рассчитывает характеристики энергетической огибающей
    
    Returns:
        dict с ключами: attack_time, envelope_variance
    """
    # Огибающая амплитуды
    envelope = np.abs(librosa.util.normalize(audio_segment))
    
    # Attack time - время до достижения максимума (в секундах)
    max_idx = np.argmax(envelope)
    attack_time = float(max_idx / sr)
    
    # Variance огибающей - изменчивость
    envelope_variance = float(np.var(envelope))
    
    return {
        "attack_time": round(attack_time, 4),
        "envelope_variance": round(envelope_variance, 6)
    }


def calculate_voicing_features(audio_segment: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Рассчитывает характеристики звонкости/шумности
    
    Returns:
        dict с ключами: zero_crossing_rate
    """
    # Zero Crossing Rate - мера шумности (больше = более шумный)
    zcr = librosa.feature.zero_crossing_rate(audio_segment)[0]
    zcr_mean = float(np.mean(zcr))
    
    return {
        "zero_crossing_rate": round(zcr_mean, 6)
    }


def calculate_all_audio_features(audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Рассчитывает все акустические характеристики
    
    Args:
        audio_segment: аудио сегмент
        sr: частота дискретизации
        
    Returns:
        dict со всеми характеристиками
    """
    features = {}
    
    # Базовая длительность
    features["duration"] = round(len(audio_segment) / sr, 3)
    
    # Амплитуда/громкость
    features.update(calculate_amplitude_features(audio_segment))
    
    # Pitch
    features.update(calculate_pitch_features(audio_segment, sr))
    
    # Спектральные характеристики
    features.update(calculate_spectral_features(audio_segment, sr))
    
    # Энергетическая огибающая
    features.update(calculate_energy_envelope(audio_segment, sr))
    
    # Звонкость/шумность
    features.update(calculate_voicing_features(audio_segment, sr))
    
    return features


def add_relative_features(
    samples_metadata: list,
    audio_duration: float
) -> list:
    """
    Добавляет относительные характеристики (нормализованные по всем словам)
    
    Args:
        samples_metadata: список метаданных всех семплов
        audio_duration: общая длительность аудио
        
    Returns:
        обновленный список метаданных
    """
    if not samples_metadata:
        return samples_metadata
    
    # Собираем значения для нормализации
    durations = [s["duration"] for s in samples_metadata]
    rms_values = [s["rms"] for s in samples_metadata]
    pitch_means = [s["pitch_mean"] for s in samples_metadata if s["pitch_mean"] > 0]
    
    # Считаем статистику
    total_duration = sum(durations)
    max_rms = max(rms_values) if rms_values else 1.0
    mean_pitch = np.mean(pitch_means) if pitch_means else 1.0
    
    # Добавляем относительные метрики
    for sample in samples_metadata:
        # Относительная длительность (процент от общей)
        sample["duration_relative"] = round(sample["duration"] / total_duration * 100, 2)
        
        # Относительная громкость (нормализованная 0-1)
        sample["rms_relative"] = round(sample["rms"] / max_rms, 4) if max_rms > 0 else 0.0
        
        # Относительная частота (отношение к средней)
        if sample["pitch_mean"] > 0 and mean_pitch > 0:
            sample["pitch_relative"] = round(sample["pitch_mean"] / mean_pitch, 4)
        else:
            sample["pitch_relative"] = 0.0
    
    return samples_metadata
