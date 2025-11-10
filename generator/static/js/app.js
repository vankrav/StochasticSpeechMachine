/**
 * Stochastic Speech Machine - Frontend
 */

const API_BASE = 'http://127.0.0.1:5001/api';

let availableRules = {};
let history = [];
let generatedCount = 0;
let samplesDir = '';
let isStreaming = false;
let streamAbortController = null;

/**
 * Инициализация генератора (автоматически при загрузке)
 */
async function initGenerator() {
    try {
        // Проверяем, инициализирован ли генератор на сервере
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('initSection').innerHTML = `
                <h2>❌ Ошибка</h2>
                <p>Генератор не инициализирован на сервере</p>
                <p class="hint">Запустите сервер с параметром --metadata</p>
            `;
            return;
        }
        
        // Показываем основной интерфейс
        document.getElementById('initSection').style.display = 'none';
        document.getElementById('mainInterface').style.display = 'block';
        
        // Обновляем статистику
        document.getElementById('totalSamples').textContent = data.total_samples;
        
        // Загружаем доступные правила
        await loadAvailableRules();
        
        console.log('✓ Генератор инициализирован:', data.total_samples, 'семплов');
    } catch (error) {
        document.getElementById('initSection').innerHTML = `
            <h2>❌ Ошибка подключения</h2>
            <p>${error.message}</p>
            <p class="hint">Убедитесь, что сервер запущен на порту 5001</p>
        `;
    }
}

/**
 * Загрузка списка доступных правил
 */
async function loadAvailableRules() {
    try {
        const response = await fetch(`${API_BASE}/rules/available`);
        availableRules = await response.json();
        
        // Заполняем диалог добавления правил
        populateRuleDialog();
    } catch (error) {
        console.error('Ошибка загрузки правил:', error);
    }
}

/**
 * Заполняет диалог выбора правил
 */
function populateRuleDialog() {
    const categories = {
        'acoustic': 'acousticRules',
        'emotional': 'emotionalRules',
        'phonetic': 'phoneticRules',
        'grammatical': 'grammaticalRules',
        'markov': 'markovRules'
    };
    
    for (const [category, elementId] of Object.entries(categories)) {
        const container = document.getElementById(elementId);
        if (!container) continue; // Пропускаем если контейнер не найден
        
        container.innerHTML = '';
        
        const rules = availableRules[category] || [];
        rules.forEach(rule => {
            const ruleDiv = document.createElement('div');
            ruleDiv.className = 'rule-option';
            ruleDiv.textContent = rule.name;
            ruleDiv.onclick = () => addRule(rule.id, rule.name, rule.params);
            container.appendChild(ruleDiv);
        });
    }
}

/**
 * Добавление правила
 */
async function addRule(ruleId, ruleName, params) {
    // Показываем диалог для параметров, если они есть
    const ruleParams = await promptRuleParams(ruleId, params);
    
    try {
        const response = await fetch(`${API_BASE}/rules/add`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                rule_id: ruleId,
                weight: 1.0,
                params: ruleParams
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
            return;
        }
        
        // Обновляем список активных правил
        await updateActiveRules();
        
        // Закрываем диалог
        closeAddRuleDialog();
        
        console.log('✓ Правило добавлено:', ruleName);
    } catch (error) {
        alert('Ошибка добавления правила: ' + error.message);
    }
}

/**
 * Запрос параметров для правила
 */
async function promptRuleParams(ruleId, paramNames) {
    const params = {};
    
    // Дефолтные значения для разных правил
    const defaults = {
        'pitch_proximity': {max_diff: 50},
        'pitch_direction': {direction: 'ascending', step: 5},
        'duration_pattern': {pattern: [1.0, 0.5, 1.0, 0.5]},
        'amplitude_wave': {wave_type: 'crescendo'},
        'mfcc_proximity': {threshold: 0.8},
        'emotion_wave': {wave: ['positive', 'neutral', 'negative']},
        'sentiment_gradient': {direction: 'ascending'},
        'vowel_consonant_ratio': {mode: 'alternating'},
        'pos_pattern': {pattern: ['NOUN', 'VERB', 'NOUN']},
        'markov_bigram': {smoothing: 0.01},
        'markov_emotional': {smoothing: 0.1},
        'markov_pos': {smoothing: 0.1},
        'markov_chain': {order: 1, use_pos: false, use_sentiment: false, smoothing: 0.01}
    };
    
    return defaults[ruleId] || {};
}

/**
 * Обновление списка активных правил
 */
async function updateActiveRules() {
    try {
        const response = await fetch(`${API_BASE}/rules/list`);
        const data = await response.json();
        
        const container = document.getElementById('activeRules');
        container.innerHTML = '';
        
        if (data.error || !data.rules || data.rules.length === 0) {
            container.innerHTML = '<p class="no-sample">Нет активных правил</p>';
            document.getElementById('activeRulesCount').textContent = '0';
            return;
        }
        
        data.rules.forEach(rule => {
            const ruleDiv = createRuleElement(rule);
            container.appendChild(ruleDiv);
        });
        
        document.getElementById('activeRulesCount').textContent = data.rules.length;
    } catch (error) {
        console.error('Ошибка обновления правил:', error);
    }
}

/**
 * Создание элемента правила
 */
function createRuleElement(rule) {
    const div = document.createElement('div');
    div.className = 'rule-item';
    
    div.innerHTML = `
        <div class="rule-header">
            <span class="rule-name">${rule.name}</span>
            <button class="rule-remove" onclick="removeRule('${rule.name}')">Удалить</button>
        </div>
        <div class="rule-controls">
            <div class="rule-weight">
                <label>Вес: <span id="weight-${rule.name}">${rule.weight.toFixed(2)}</span></label>
                <input type="range" min="0" max="2" step="0.1" value="${rule.weight}" 
                       oninput="updateRuleWeight('${rule.name}', this.value)">
            </div>
        </div>
    `;
    
    return div;
}

/**
 * Обновление веса правила
 */
async function updateRuleWeight(ruleName, weight) {
    document.getElementById(`weight-${ruleName}`).textContent = parseFloat(weight).toFixed(2);
    
    try {
        await fetch(`${API_BASE}/rules/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                rule_name: ruleName,
                weight: parseFloat(weight)
            })
        });
    } catch (error) {
        console.error('Ошибка обновления веса:', error);
    }
}

/**
 * Удаление правила
 */
async function removeRule(ruleName) {
    try {
        await fetch(`${API_BASE}/rules/remove`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({rule_name: ruleName})
        });
        
        await updateActiveRules();
    } catch (error) {
        console.error('Ошибка удаления правила:', error);
    }
}

/**
 * Генерация следующего семпла
 */
async function generateNext() {
    try {
        const response = await fetch(`${API_BASE}/generate/next`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
            return;
        }
        
        displaySample(data.sample);
        addToHistory(data.sample);
        generatedCount++;
        document.getElementById('generatedCount').textContent = generatedCount;
        
    } catch (error) {
        alert('Ошибка генерации: ' + error.message);
    }
}

/**
 * Генерация последовательности
 */
async function generateSequence() {
    const length = parseInt(document.getElementById('seqLength').value);
    
    try {
        const response = await fetch(`${API_BASE}/generate/sequence`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({length: length})
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
            return;
        }
        
        // Воспроизводим последовательность
        playSequence(data.sequence);
        
    } catch (error) {
        alert('Ошибка генерации: ' + error.message);
    }
}

/**
 * Воспроизведение последовательности семплов
 */
async function playSequence(sequence) {
    // Получаем степень нахлеста в процентах
    const overlapPercent = parseInt(document.getElementById('overlap').value);
    
    for (let i = 0; i < sequence.length; i++) {
        const sample = sequence[i];
        
        displaySample(sample);
        addToHistory(sample);
        
        // Воспроизводим семпл (не ждем окончания)
        playSampleOverlap(sample);
        
        generatedCount++;
        document.getElementById('generatedCount').textContent = generatedCount;
        
        // Если это не последний семпл, ждем с учетом нахлеста
        if (i < sequence.length - 1) {
            // Вычисляем задержку: duration * (1 - overlap/100)
            const duration = sample.duration || 1.0;
            const delay = duration * 1000 * (1 - overlapPercent / 100);
            await sleep(delay);
        }
    }
    
    // Ждем окончания последнего семпла
    if (sequence.length > 0) {
        const lastDuration = sequence[sequence.length - 1].duration || 1.0;
        await sleep(lastDuration * 1000);
    }
}

/**
 * Воспроизведение семпла (для последовательного воспроизведения)
 */
function playSample(sample) {
    return new Promise((resolve) => {
        const audio = document.getElementById('audioPlayer');
        const filename = sample.filename;
        
        // Формируем URL для аудио файла
        audio.src = `${API_BASE}/samples/${filename}`;
        
        audio.onended = resolve;
        audio.onerror = () => {
            console.error('Ошибка загрузки аудио:', filename);
            resolve();
        };
        
        audio.play().catch(err => {
            console.error('Ошибка воспроизведения:', err);
            resolve();
        });
    });
}

/**
 * Воспроизведение семпла с нахлестом (создает отдельный Audio элемент)
 */
function playSampleOverlap(sample) {
    const audio = new Audio(`${API_BASE}/samples/${sample.filename}`);
    
    audio.onerror = () => {
        console.error('Ошибка загрузки аудио:', sample.filename);
    };
    
    audio.play().catch(err => {
        console.error('Ошибка воспроизведения:', err);
    });
    
    return audio;
}

/**
 * Отображение текущего семпла
 */
function displaySample(sample) {
    const container = document.getElementById('currentSample');
    
    container.innerHTML = `
        <div class="sample-info">
            <div class="info-item">
                <div class="info-label">Слово</div>
                <div class="info-value">${sample.word}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Длительность</div>
                <div class="info-value">${sample.duration?.toFixed(2)}s</div>
            </div>
            <div class="info-item">
                <div class="info-label">Pitch</div>
                <div class="info-value">${sample.pitch_mean?.toFixed(0)} Hz</div>
            </div>
            <div class="info-item">
                <div class="info-label">Эмоция</div>
                <div class="info-value">${getSentimentEmoji(sample.sentiment)} ${sample.sentiment}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Часть речи</div>
                <div class="info-value">${sample.pos || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Громкость</div>
                <div class="info-value">${(sample.rms_relative || 1.0).toFixed(2)}x</div>
            </div>
        </div>
    `;
}

/**
 * Получение эмодзи для сентимента
 */
function getSentimentEmoji(sentiment) {
    const emojis = {
        'positive': '😊',
        'negative': '😞',
        'neutral': '😐',
        'speech': '💬',
        'skip': '❓'
    };
    return emojis[sentiment] || '❓';
}

/**
 * Добавление в историю
 */
function addToHistory(sample) {
    history.push(sample);
    
    const historyContainer = document.getElementById('history');
    
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    historyItem.textContent = sample.word;
    historyItem.title = `${sample.sentiment} | ${sample.pos}`;
    historyItem.onclick = () => {
        displaySample(sample);
        playSample(sample);
    };
    
    historyContainer.appendChild(historyItem);
    
    // Прокручиваем вниз
    historyContainer.scrollTop = historyContainer.scrollHeight;
}

/**
 * Очистка истории
 */
function clearHistory() {
    history = [];
    document.getElementById('history').innerHTML = '';
}

/**
 * Обновление температуры
 */
async function updateTemperature(value) {
    document.getElementById('tempValue').textContent = parseFloat(value).toFixed(1);
    
    try {
        await fetch(`${API_BASE}/temperature`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({temperature: parseFloat(value)})
        });
    } catch (error) {
        console.error('Ошибка обновления температуры:', error);
    }
}

/**
 * Сброс генератора
 */
async function resetGenerator() {
    if (!confirm('Сбросить состояние генератора?')) {
        return;
    }
    
    // Останавливаем поток если он активен
    if (isStreaming) {
        stopStream();
    }
    
    try {
        await fetch(`${API_BASE}/reset`, {method: 'POST'});
        
        document.getElementById('currentSample').innerHTML = '<p class="no-sample">Нажмите "Следующий" для начала</p>';
        clearHistory();
        generatedCount = 0;
        document.getElementById('generatedCount').textContent = '0';
        
        console.log('✓ Генератор сброшен');
    } catch (error) {
        console.error('Ошибка сброса:', error);
    }
}

/**
 * Переключение непрерывного потока
 */
function toggleStream() {
    if (isStreaming) {
        stopStream();
    } else {
        startStream();
    }
}

/**
 * Запуск непрерывного потока
 */
async function startStream() {
    isStreaming = true;
    streamAbortController = new AbortController();
    
    const btn = document.getElementById('streamBtn');
    btn.textContent = '⏸ Остановить поток';
    btn.classList.add('btn-active');
    
    console.log('🌊 Непрерывный поток запущен');
    
    try {
        await streamLoop();
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Ошибка потока:', error);
        }
    }
}

/**
 * Остановка непрерывного потока
 */
function stopStream() {
    isStreaming = false;
    
    if (streamAbortController) {
        streamAbortController.abort();
        streamAbortController = null;
    }
    
    const btn = document.getElementById('streamBtn');
    btn.textContent = '🌊 Непрерывный поток';
    btn.classList.remove('btn-active');
    
    console.log('⏸ Непрерывный поток остановлен');
}

/**
 * Цикл непрерывного потока
 */
async function streamLoop() {
    const overlapPercent = parseInt(document.getElementById('overlap').value);
    
    while (isStreaming) {
        try {
            // Генерируем следующий семпл
            const response = await fetch(`${API_BASE}/generate/next`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({}),
                signal: streamAbortController.signal
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Ошибка генерации:', data.error);
                break;
            }
            
            const sample = data.sample;
            
            displaySample(sample);
            addToHistory(sample);
            
            // Воспроизводим семпл
            playSampleOverlap(sample);
            
            generatedCount++;
            document.getElementById('generatedCount').textContent = generatedCount;
            
            // Задержка с учетом нахлеста
            const duration = sample.duration || 1.0;
            const delay = duration * 1000 * (1 - overlapPercent / 100);
            await sleep(delay);
            
        } catch (error) {
            if (error.name === 'AbortError') {
                break;
            }
            console.error('Ошибка в потоке:', error);
            break;
        }
    }
    
    stopStream();
}

/**
 * Показать диалог добавления правила
 */
function showAddRuleDialog() {
    document.getElementById('addRuleDialog').style.display = 'flex';
}

/**
 * Закрыть диалог добавления правила
 */
function closeAddRuleDialog() {
    document.getElementById('addRuleDialog').style.display = 'none';
}

/**
 * Утилита: ожидание
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Инициализация при загрузке страницы
 */
window.addEventListener('DOMContentLoaded', () => {
    console.log('🎛️ Stochastic Speech Machine готова');
    
    // Автоматическая инициализация
    initGenerator();
});

// Закрытие диалога по клику вне его
window.addEventListener('click', (e) => {
    const dialog = document.getElementById('addRuleDialog');
    if (e.target === dialog) {
        closeAddRuleDialog();
    }
});
