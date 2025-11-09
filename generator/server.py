#!/usr/bin/env python3
"""
Flask сервер для веб-интерфейса генератора стохастической речи
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from pathlib import Path
import json
import sys

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from generator import StochasticGenerator
from rules import (
    PitchProximityRule, PitchDirectionRule, DurationPatternRule, 
    AmplitudeWaveRule, MFCCProximityRule,
    EmotionWaveRule, EmotionContrastRule, SentimentGradientRule,
    AlliterationRule, VowelConsonantRatioRule, VoicingAlternationRule,
    POSPatternRule, POSAlternationRule
)

app = Flask(__name__, static_folder='static')
CORS(app)

# Глобальный генератор
generator = None
samples_dir = None


@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory('static', 'index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """Отдает CSS файлы"""
    return send_from_directory('static/css', filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Отдает JS файлы"""
    return send_from_directory('static/js', filename)


@app.route('/api/init', methods=['POST'])
def init_generator():
    """Инициализация генератора с metadata.json"""
    global generator, samples_dir
    
    data = request.json
    metadata_path = data.get('metadata_path')
    
    if not metadata_path:
        return jsonify({'error': 'metadata_path is required'}), 400
    
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        return jsonify({'error': f'File not found: {metadata_path}'}), 404
    
    # Определяем директорию с семплами
    samples_dir = metadata_path.parent / 'samples'
    
    try:
        generator = StochasticGenerator(str(metadata_path))
        return jsonify({
            'success': True,
            'total_samples': len(generator.samples),
            'samples_dir': str(samples_dir)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rules/available')
def get_available_rules():
    """Возвращает список доступных правил"""
    rules_info = {
        'acoustic': [
            {'id': 'pitch_proximity', 'name': 'Близость pitch', 'params': ['max_diff']},
            {'id': 'pitch_direction', 'name': 'Направление pitch', 'params': ['direction', 'step']},
            {'id': 'duration_pattern', 'name': 'Ритм длительности', 'params': ['pattern']},
            {'id': 'amplitude_wave', 'name': 'Волна громкости', 'params': ['wave_type']},
            {'id': 'mfcc_proximity', 'name': 'Близость тембра', 'params': ['threshold']}
        ],
        'emotional': [
            {'id': 'emotion_wave', 'name': 'Эмоциональная волна', 'params': ['wave']},
            {'id': 'emotion_contrast', 'name': 'Контраст эмоций', 'params': []},
            {'id': 'sentiment_gradient', 'name': 'Градиент эмоций', 'params': ['direction']}
        ],
        'phonetic': [
            {'id': 'alliteration', 'name': 'Аллитерация', 'params': []},
            {'id': 'vowel_consonant_ratio', 'name': 'Гласные/Согласные', 'params': ['mode']},
            {'id': 'voicing_alternation', 'name': 'Звонкость/Глухость', 'params': []}
        ],
        'grammatical': [
            {'id': 'pos_pattern', 'name': 'Паттерн частей речи', 'params': ['pattern']},
            {'id': 'pos_alternation', 'name': 'Существительное/Глагол', 'params': []}
        ]
    }
    return jsonify(rules_info)


@app.route('/api/rules/add', methods=['POST'])
def add_rule():
    """Добавляет правило в генератор"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json
    rule_id = data.get('rule_id')
    weight = data.get('weight', 1.0)
    params = data.get('params', {})
    
    # Создаем правило по ID
    rule_classes = {
        'pitch_proximity': PitchProximityRule,
        'pitch_direction': PitchDirectionRule,
        'duration_pattern': DurationPatternRule,
        'amplitude_wave': AmplitudeWaveRule,
        'mfcc_proximity': MFCCProximityRule,
        'emotion_wave': EmotionWaveRule,
        'emotion_contrast': EmotionContrastRule,
        'sentiment_gradient': SentimentGradientRule,
        'alliteration': AlliterationRule,
        'vowel_consonant_ratio': VowelConsonantRatioRule,
        'voicing_alternation': VoicingAlternationRule,
        'pos_pattern': POSPatternRule,
        'pos_alternation': POSAlternationRule
    }
    
    rule_class = rule_classes.get(rule_id)
    if not rule_class:
        return jsonify({'error': f'Unknown rule: {rule_id}'}), 400
    
    try:
        rule = rule_class(weight=weight, **params)
        generator.add_rule(rule)
        return jsonify({'success': True, 'rule_name': rule.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rules/update', methods=['POST'])
def update_rule():
    """Обновляет параметры правила"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json
    rule_name = data.get('rule_name')
    weight = data.get('weight')
    params = data.get('params')
    
    if weight is not None:
        generator.update_rule_weight(rule_name, weight)
    
    if params is not None:
        generator.update_rule_params(rule_name, **params)
    
    return jsonify({'success': True})


@app.route('/api/rules/remove', methods=['POST'])
def remove_rule():
    """Удаляет правило"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json
    rule_name = data.get('rule_name')
    
    generator.remove_rule(rule_name)
    return jsonify({'success': True})


@app.route('/api/rules/list')
def list_rules():
    """Возвращает текущий список правил"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    rules = [rule.get_config() for rule in generator.rules]
    return jsonify({'rules': rules})


@app.route('/api/generate/next', methods=['POST'])
def generate_next():
    """Генерирует следующий семпл"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json or {}
    current_word = data.get('current_word')
    
    current_sample = None
    if current_word:
        current_sample = generator.get_sample_by_word(current_word)
    
    try:
        next_sample = generator.select_next(current_sample)
        return jsonify({
            'success': True,
            'sample': next_sample
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate/sequence', methods=['POST'])
def generate_sequence():
    """Генерирует последовательность семплов"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json or {}
    length = data.get('length', 10)
    start_word = data.get('start_word')
    
    try:
        sequence = generator.generate_sequence(length, start_word)
        return jsonify({
            'success': True,
            'sequence': sequence
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/temperature', methods=['POST'])
def set_temperature():
    """Устанавливает температуру генерации"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    data = request.json
    temperature = data.get('temperature', 1.0)
    
    generator.set_temperature(temperature)
    return jsonify({'success': True, 'temperature': generator.temperature})


@app.route('/api/reset', methods=['POST'])
def reset_generator():
    """Сбрасывает состояние генератора"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    generator.reset()
    return jsonify({'success': True})


@app.route('/api/config')
def get_config():
    """Возвращает текущую конфигурацию"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    return jsonify(generator.get_config())


@app.route('/api/samples/<path:filename>')
def serve_sample(filename):
    """Отдает аудио файл семпла"""
    if not samples_dir:
        return jsonify({'error': 'Samples directory not set'}), 400
    
    return send_from_directory(samples_dir, filename)


@app.route('/api/samples/list')
def list_samples():
    """Возвращает список всех семплов"""
    if not generator:
        return jsonify({'error': 'Generator not initialized'}), 400
    
    # Возвращаем упрощенную версию для списка
    samples_list = [
        {
            'index': s.get('index'),
            'word': s.get('word'),
            'filename': s.get('filename'),
            'duration': s.get('duration'),
            'sentiment': s.get('sentiment'),
            'pos': s.get('pos')
        }
        for s in generator.samples
    ]
    
    return jsonify({'samples': samples_list})


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Stochastic Speech Generator Server')
    parser.add_argument('--metadata', type=str, help='Path to metadata.json')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host')
    
    args = parser.parse_args()
    
    # Автоинициализация если передан metadata
    if args.metadata:
        metadata_path = Path(args.metadata)
        if metadata_path.exists():
            samples_dir = metadata_path.parent / 'samples'
            generator = StochasticGenerator(str(metadata_path))
            print(f"✓ Генератор инициализирован: {len(generator.samples)} семплов")
    
    print(f"🚀 Сервер запущен: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
