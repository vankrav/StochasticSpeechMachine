// Canvas - модуль для визуализации и манипуляции текста семплов
// ================================================================

// Состояние приложения
const state = {
    samples: [],           // Все семплы из metadata.json
    words: [],            // Текущий порядок слов для отображения
    isPlaying: false,     // Играет ли сейчас
    currentIndex: 0,      // Индекс текущего читаемого элемента
    readingSpeed: 1.0,    // Скорость чтения (множитель)
    columnWidth: 600,     // Ширина колонки текста
    overlap: 30,           // Нахлест между семплами в мс (+ = наложение, - = пауза)
    audioContext: null,   // Web Audio API context
    currentAudio: null,   // Текущий проигрываемый аудио элемент
    nextTimeout: null,    // Таймер для запуска следующего семпла
    loopStart: null,      // Индекс начала зацикленного фрагмента
    loopEnd: null,        // Индекс конца зацикленного фрагмента
    replacementCount: {}, // Счетчик замен для каждого индекса {index: count}
    usageAsReplacement: {}, // Счетчик использования слов в качестве замены {originalIndex: count}
    autoReplaceEnabled: false, // Включена ли автозамена
    autoReplaceInterval: 0.5,  // Интервал автозамены в секундах
    autoReplaceTimer: null     // Таймер для автозамены
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Canvas модуль загружен');
    
    // Инициализация Audio Context
    state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Загрузка семплов
    await loadSamples();
    
    // Привязка обработчиков событий
    setupEventListeners();
    
    // Отображение текста
    renderText();
});

// Загрузка семплов с сервера
async function loadSamples() {
    try {
        const response = await fetch('/api/samples/list');
        if (!response.ok) {
            throw new Error('Ошибка загрузки семплов');
        }
        
        const data = await response.json();
        state.samples = data.samples || [];
        
        // Сортируем по естественному порядку (index)
        state.samples.sort((a, b) => a.index - b.index);
        
        // Инициализируем words как копию samples
        state.words = state.samples.map((s, idx) => ({
            ...s,
            displayIndex: idx
        }));
        
        console.log(`Загружено семплов: ${state.words.length}`);
        updateWordCount();
        
    } catch (error) {
        console.error('Ошибка при загрузке семплов:', error);
        const textColumn = document.getElementById('textColumn');
        textColumn.innerHTML = '<p class="loading" style="color: #ff0000;">ОШИБКА ЗАГРУЗКИ. ПРОВЕРЬТЕ СЕРВЕР.</p>';
    }
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопки управления
    document.getElementById('playBtn').addEventListener('click', startReading);
    document.getElementById('pauseBtn').addEventListener('click', pauseReading);
    document.getElementById('resetBtn').addEventListener('click', resetReading);
    document.getElementById('clearLoopBtn').addEventListener('click', clearLoop);
    document.getElementById('replaceRandomBtn').addEventListener('click', replaceRandomWordInLoop);
    document.getElementById('autoReplaceToggleBtn').addEventListener('click', toggleAutoReplace);
    document.getElementById('panelToggle').addEventListener('click', toggleControlsPanel);
    
    // Слайдеры
    document.getElementById('readingSpeed').addEventListener('input', (e) => {
        state.readingSpeed = parseFloat(e.target.value);
        document.getElementById('speedValue').textContent = state.readingSpeed.toFixed(1);
    });
    
    document.getElementById('columnWidth').addEventListener('input', (e) => {
        state.columnWidth = parseInt(e.target.value);
        document.getElementById('widthValue').textContent = state.columnWidth;
        document.querySelector('.text-column').style.width = `${state.columnWidth}px`;
    });
    
    document.getElementById('overlap').addEventListener('input', (e) => {
        state.overlap = parseInt(e.target.value);
        document.getElementById('overlapValue').textContent = state.overlap;
    });
    
    document.getElementById('autoReplaceInterval').addEventListener('input', (e) => {
        state.autoReplaceInterval = parseFloat(e.target.value);
        document.getElementById('autoReplaceIntervalValue').textContent = state.autoReplaceInterval.toFixed(1);
        
        // Если автозамена активна, обновляем статус и перезапускаем таймер
        if (state.autoReplaceEnabled) {
            // Обновляем статус с новым интервалом
            const statusElement = document.getElementById('autoReplaceStatus');
            statusElement.textContent = `ВКЛ (${state.autoReplaceInterval}s)`;
            
            // Перезапускаем таймер
            if (state.autoReplaceTimer) {
                clearTimeout(state.autoReplaceTimer);
            }
            scheduleNextAutoReplace();
        }
    });
}

// Отображение текста на экране
function renderText() {
    const textColumn = document.getElementById('textColumn');
    textColumn.innerHTML = '';
    
    if (state.words.length === 0) {
        textColumn.innerHTML = '<p class="loading">НЕТ СЛОВ ДЛЯ ОТОБРАЖЕНИЯ</p>';
        return;
    }
    
    // Создаем элементы для каждого слова или паузы
    state.words.forEach((item, index) => {
        const element = document.createElement('span');
        const isPause = item.type === 'pause';
        
        // Определяем класс и содержимое
        element.className = isPause ? 'pause' : 'word';
        
        if (!isPause) {
            element.textContent = item.word;
        }
        
        element.dataset.index = index;
        element.dataset.type = item.type;
        element.draggable = true;
        
        // Применяем классы для рамок зацикливания
        if (state.loopStart === index) {
            element.classList.add('loop-start');
        }
        if (state.loopEnd === index) {
            element.classList.add('loop-end');
        }
        
        // Применяем подкрашивание для замененных слов
        const replacementCount = state.replacementCount[index] || 0;
        if (replacementCount > 0) {
            element.classList.add('replaced');
            element.dataset.replacementCount = replacementCount;
            // Интенсивность цвета зависит от количества замен (макс 5)
            const intensity = Math.min(replacementCount, 5);
            element.style.backgroundColor = `rgba(255, 200, 100, ${0.1 + intensity * 0.15})`;
        }
        
        // Делаем серым текст вне зацикленного фрагмента
        if (state.loopStart !== null && state.loopEnd !== null) {
            if (index < state.loopStart || index > state.loopEnd) {
                element.classList.add('outside-loop');
            }
        }
        
        // Кнопка начала зацикливания
        const loopStartBtn = document.createElement('button');
        loopStartBtn.className = 'loop-start-btn';
        loopStartBtn.textContent = '[';
        loopStartBtn.onclick = (e) => {
            e.stopPropagation();
            setLoopStart(index);
        };
        element.appendChild(loopStartBtn);
        
        // Кнопка конца зацикливания
        const loopEndBtn = document.createElement('button');
        loopEndBtn.className = 'loop-end-btn';
        loopEndBtn.textContent = ']';
        loopEndBtn.onclick = (e) => {
            e.stopPropagation();
            setLoopEnd(index);
        };
        element.appendChild(loopEndBtn);
        
        // Кнопка дублирования
        const duplicateBtn = document.createElement('button');
        duplicateBtn.className = 'duplicate-btn';
        duplicateBtn.textContent = '+';
        duplicateBtn.onclick = (e) => {
            e.stopPropagation();
            duplicateWord(index);
        };
        element.appendChild(duplicateBtn);
        
        // Кнопка удаления
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = '×';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteWord(index);
        };
        element.appendChild(deleteBtn);
        
        // Drag and Drop обработчики
        element.addEventListener('dragstart', handleDragStart);
        element.addEventListener('dragover', handleDragOver);
        element.addEventListener('drop', handleDrop);
        element.addEventListener('dragend', handleDragEnd);
        
        textColumn.appendChild(element);
    });
}

// === DRAG AND DROP ===

let draggedElement = null;
let draggedIndex = null;

function handleDragStart(e) {
    draggedElement = e.target;
    draggedIndex = parseInt(e.target.dataset.index);
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    const targetElement = e.target.closest('.word, .pause');
    if (targetElement && targetElement !== draggedElement) {
        targetElement.classList.add('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    
    const targetElement = e.target.closest('.word, .pause');
    if (!targetElement || targetElement === draggedElement) return;
    
    const targetIndex = parseInt(targetElement.dataset.index);
    
    // Меняем местами элементы в массиве
    [state.words[draggedIndex], state.words[targetIndex]] = 
    [state.words[targetIndex], state.words[draggedIndex]];
    
    // Перерисовываем текст
    renderText();
    
    // Если читаем, обновляем currentIndex
    if (state.isPlaying) {
        if (state.currentIndex === draggedIndex) {
            state.currentIndex = targetIndex;
        } else if (state.currentIndex === targetIndex) {
            state.currentIndex = draggedIndex;
        }
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    
    // Убираем все drag-over классы
    document.querySelectorAll('.word, .pause').forEach(element => {
        element.classList.remove('drag-over');
    });
    
    draggedElement = null;
    draggedIndex = null;
}

// === УДАЛЕНИЕ И ДУБЛИРОВАНИЕ ===

function deleteWord(index) {
    if (state.isPlaying) {
        alert('ОСТАНОВИТЕ ЧТЕНИЕ ПЕРЕД УДАЛЕНИЕМ');
        return;
    }
    
    // Удаляем элемент из массива
    state.words.splice(index, 1);
    
    // Перерисовываем
    renderText();
    updateWordCount();
}

function duplicateWord(index) {
    if (state.isPlaying) {
        alert('ОСТАНОВИТЕ ЧТЕНИЕ ПЕРЕД ДУБЛИРОВАНИЕМ');
        return;
    }
    
    // Создаем копию элемента
    const original = state.words[index];
    const duplicate = { ...original };
    
    // Вставляем копию сразу после оригинала
    state.words.splice(index + 1, 0, duplicate);
    
    // Перерисовываем
    renderText();
    updateWordCount();
}

// === ЗАЦИКЛИВАНИЕ ===

function setLoopStart(index) {
    state.loopStart = index;
    
    // Если конец цикла уже установлен и он меньше начала, сбрасываем его
    if (state.loopEnd !== null && state.loopEnd < index) {
        state.loopEnd = null;
    }
    
    renderText();
    console.log(`Начало цикла установлено на индекс ${index}`);
}

function setLoopEnd(index) {
    // Конец цикла должен быть после начала
    if (state.loopStart !== null && index < state.loopStart) {
        alert('КОНЕЦ ЦИКЛА ДОЛЖЕН БЫТЬ ПОСЛЕ НАЧАЛА');
        return;
    }
    
    state.loopEnd = index;
    renderText();
    console.log(`Конец цикла установлен на индекс ${index}`);
}

function clearLoop() {
    state.loopStart = null;
    state.loopEnd = null;
    
    // Останавливаем автозамену при сбросе лупа
    if (state.autoReplaceEnabled) {
        stopAutoReplace();
    }
    
    renderText();
}

// === ЗАМЕНА СЛУЧАЙНОГО СЛОВА ===

async function replaceRandomWordInLoop() {
    // Проверяем, что цикл установлен
    if (state.loopStart === null || state.loopEnd === null) {
        alert('СНАЧАЛА УСТАНОВИТЕ ЦИКЛ [ ]');
        return;
    }
    
    // Получаем все слова в цикле (не паузы)
    const wordsInLoop = [];
    for (let i = state.loopStart; i <= state.loopEnd; i++) {
        if (state.words[i].type === 'word') {
            wordsInLoop.push({
                index: i,
                word: state.words[i]
            });
        }
    }
    
    if (wordsInLoop.length === 0) {
        alert('В ЦИКЛЕ НЕТ СЛОВ ДЛЯ ЗАМЕНЫ');
        return;
    }
    
    // Выбираем случайное слово
    const randomIndex = Math.floor(Math.random() * wordsInLoop.length);
    const targetWordData = wordsInLoop[randomIndex];
    const targetIndex = targetWordData.index;
    const targetWord = targetWordData.word;
    
    console.log(`Выбрано слово для замены: "${targetWord.word}" (индекс ${targetIndex})`);
    
    try {
        // Запрашиваем похожее слово с сервера
        const response = await fetch('/api/find-similar-word', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_word: targetWord,
                exclude_indices: [targetWord.index],
                usage_as_replacement: state.usageAsReplacement
            })
        }).catch(networkError => {
            console.error('Ошибка сети:', networkError);
            throw new Error('Ошибка подключения к серверу');
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ответ сервера:', response.status, errorText);
            throw new Error(`Ошибка сервера: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.similar_word) {
            console.warn('Не найдено похожее слово для:', targetWord.word);
            // Пропускаем эту замену и продолжаем работу
            return;
        }
        
        const similarWord = data.similar_word;
        
        // Валидация данных
        if (!similarWord || !similarWord.word || similarWord.index === undefined) {
            console.error('Некорректные данные похожего слова:', similarWord);
            return;
        }
        
        console.log(`Найдено похожее слово: "${similarWord.word}" (оценка: ${data.similarity_score})`);
        
        // Заменяем слово в массиве
        state.words[targetIndex] = similarWord;
        
        // Увеличиваем счетчик замен для этого индекса
        state.replacementCount[targetIndex] = (state.replacementCount[targetIndex] || 0) + 1;
        
        // Увеличиваем счетчик использования этого слова как замены
        const originalIndex = similarWord.index;
        state.usageAsReplacement[originalIndex] = (state.usageAsReplacement[originalIndex] || 0) + 1;
        
        // Перерисовываем текст
        renderText();
        
        console.log(`Замена выполнена. Счетчик замен для индекса ${targetIndex}: ${state.replacementCount[targetIndex]}`);
        console.log(`Слово "${similarWord.word}" (индекс ${originalIndex}) использовано как замена ${state.usageAsReplacement[originalIndex]} раз`);
        
    } catch (error) {
        console.error('Ошибка при замене слова:', error);
        console.error('Детали ошибки:', {
            message: error.message,
            stack: error.stack,
            targetWord: targetWord,
            targetIndex: targetIndex
        });
        
        // Не показываем алерт - просто логируем и продолжаем
        // Это позволит автозамене работать без прерываний
    }
}

// === АВТОЗАМЕНА ===

function toggleAutoReplace() {
    if (state.autoReplaceEnabled) {
        stopAutoReplace();
    } else {
        startAutoReplace();
    }
}

function startAutoReplace() {
    // Проверяем, что цикл установлен
    if (state.loopStart === null || state.loopEnd === null) {
        alert('СНАЧАЛА УСТАНОВИТЕ ЦИКЛ [ ]');
        return;
    }
    
    state.autoReplaceEnabled = true;
    
    // Обновляем UI кнопки
    const button = document.getElementById('autoReplaceToggleBtn');
    button.textContent = '⟳ АВТОЗАМЕНА: ВКЛ';
    button.classList.remove('btn-secondary');
    button.classList.add('btn-primary');
    
    // Обновляем статус
    const statusElement = document.getElementById('autoReplaceStatus');
    statusElement.textContent = `ВКЛ (${state.autoReplaceInterval}s)`;
    statusElement.style.color = '#00ff00';
    
    console.log(`Автозамена запущена с интервалом ${state.autoReplaceInterval}s`);
    
    // Запускаем цикл автозамены
    scheduleNextAutoReplace();
}

function stopAutoReplace() {
    state.autoReplaceEnabled = false;
    
    // Останавливаем таймер
    if (state.autoReplaceTimer) {
        clearTimeout(state.autoReplaceTimer);
        state.autoReplaceTimer = null;
    }
    
    // Обновляем UI кнопки
    const button = document.getElementById('autoReplaceToggleBtn');
    button.textContent = '⟳ АВТОЗАМЕНА: ВЫКЛ';
    button.classList.remove('btn-primary');
    button.classList.add('btn-secondary');
    
    // Обновляем статус
    const statusElement = document.getElementById('autoReplaceStatus');
    statusElement.textContent = 'ВЫКЛ';
    statusElement.style.color = '';
    
    console.log('Автозамена остановлена');
}

function scheduleNextAutoReplace() {
    if (!state.autoReplaceEnabled) return;
    
    // Устанавливаем таймер на следующую замену
    state.autoReplaceTimer = setTimeout(() => {
        replaceRandomWordInLoop();
        // Планируем следующую замену
        scheduleNextAutoReplace();
    }, state.autoReplaceInterval * 1000);
}

// === ЧТЕНИЕ ТЕКСТА ===

function startReading() {
    if (state.isPlaying) return;
    if (state.words.length === 0) return;
    
    state.isPlaying = true;
    document.getElementById('playBtn').disabled = true;
    document.getElementById('pauseBtn').disabled = false;
    document.getElementById('readerIndicator').classList.add('active');
    
    // Если установлен цикл и текущий индекс вне цикла, начинаем с начала цикла
    if (state.loopStart !== null && state.loopEnd !== null) {
        if (state.currentIndex < state.loopStart || state.currentIndex > state.loopEnd) {
            state.currentIndex = state.loopStart;
        }
    }
    
    // Возобновляем Audio Context если приостановлен
    if (state.audioContext.state === 'suspended') {
        state.audioContext.resume();
    }
    
    readNextWord();
}

function pauseReading() {
    state.isPlaying = false;
    document.getElementById('playBtn').disabled = false;
    document.getElementById('pauseBtn').disabled = true;
    
    // Останавливаем текущее аудио
    if (state.currentAudio) {
        state.currentAudio.pause();
        state.currentAudio = null;
    }
    
    // Очищаем таймер следующего семпла
    if (state.nextTimeout) {
        clearTimeout(state.nextTimeout);
        state.nextTimeout = null;
    }
    
    // Убираем индикатор
    document.getElementById('readerIndicator').classList.remove('active');
    
    // Убираем подсветку с текущих элементов
    document.querySelectorAll('.word, .pause').forEach(element => element.classList.remove('reading'));
}

function resetReading() {
    pauseReading();
    state.currentIndex = 0;
    document.getElementById('currentWordIndex').textContent = '-';
}

async function readNextWord() {
    if (!state.isPlaying) return;
    
    // Проверяем зацикливание
    const hasLoop = state.loopStart !== null && state.loopEnd !== null;
    
    if (hasLoop) {
        // Если достигли конца цикла, возвращаемся к началу
        if (state.currentIndex > state.loopEnd) {
            state.currentIndex = state.loopStart;
        }
    } else {
        // Без цикла - обычное поведение
        if (state.currentIndex >= state.words.length) {
            resetReading();
            return;
        }
    }
    
    const item = state.words[state.currentIndex];
    const allElements = document.querySelectorAll('.word, .pause');
    const currentElement = allElements[state.currentIndex];
    
    if (!currentElement) {
        console.error('Элемент не найден');
        return;
    }
    
    // Обновляем UI
    const loopIndicator = hasLoop ? ' [LOOP]' : '';
    document.getElementById('currentWordIndex').textContent = `${state.currentIndex + 1} / ${state.words.length}${loopIndicator}`;
    
    // Убираем подсветку с предыдущих элементов
    allElements.forEach(element => element.classList.remove('reading'));
    currentElement.classList.add('reading');
    
    // Позиционируем индикатор над элементом
    positionReaderIndicator(currentElement);
    
    // Переходим к следующему элементу
    state.currentIndex++;
    
    // Запускаем проигрывание и планируем следующий семпл
    playWordAudioWithOverlap(item);
}

// Проигрывание с учетом нахлеста
function playWordAudioWithOverlap(item) {
    const audioUrl = `/api/samples/${item.filename}`;
    const audio = new Audio(audioUrl);
    state.currentAudio = audio;
    
    // Учитываем скорость чтения
    audio.playbackRate = state.readingSpeed;
    
    // Обработчик загрузки метаданных (чтобы узнать длительность)
    audio.addEventListener('loadedmetadata', () => {
        if (!state.isPlaying) return;
        
        // Вычисляем реальную длительность с учетом скорости
        const duration = (audio.duration * 1000) / state.readingSpeed;
        
        // Вычисляем когда запустить следующий семпл
        // overlap > 0 = наложение (запускаем раньше)
        // overlap < 0 = пауза (запускаем позже)
        const nextDelay = duration - state.overlap;
        
        // Планируем следующий семпл
        if (state.currentIndex < state.words.length) {
            state.nextTimeout = setTimeout(() => {
                if (state.isPlaying) {
                    readNextWord();
                }
            }, Math.max(0, nextDelay));
        }
    });
    
    audio.onerror = () => {
        console.error(`Ошибка загрузки аудио: ${item.filename}`);
        state.currentAudio = null;
        // Переходим к следующему даже при ошибке
        if (state.isPlaying && state.currentIndex < state.words.length) {
            readNextWord();
        }
    };
    
    audio.play().catch(error => {
        console.error('Ошибка при проигрывании аудио:', error);
    });
}

// Позиционирование индикатора над словом
function positionReaderIndicator(element) {
    const indicator = document.getElementById('readerIndicator');
    const rect = element.getBoundingClientRect();
    const canvasRect = document.querySelector('.text-canvas').getBoundingClientRect();
    
    // Позиция относительно canvas
    const left = rect.left - canvasRect.left + (rect.width / 2) - 6;
    const top = rect.top - canvasRect.top - 20;
    
    indicator.style.left = `${left}px`;
    indicator.style.top = `${top}px`;
}

// Обновление счетчика слов
function updateWordCount() {
    const totalWords = state.words.filter(item => item.type === 'word').length;
    const totalPauses = state.words.filter(item => item.type === 'pause').length;
    document.getElementById('wordCount').textContent = `${totalWords} слов, ${totalPauses} пауз`;
}

// === УПРАВЛЕНИЕ ПАНЕЛЬЮ ===

function toggleControlsPanel() {
    const panel = document.getElementById('controlsPanel');
    const button = document.getElementById('panelToggle');
    const textCanvas = document.querySelector('.text-canvas');
    
    panel.classList.toggle('collapsed');
    
    if (panel.classList.contains('collapsed')) {
        button.textContent = '►';
        button.title = 'Показать панель';
        button.style.left = '0px';
        textCanvas.style.marginLeft = '0';
        textCanvas.style.width = '100%';
    } else {
        button.textContent = '◄';
        button.title = 'Скрыть панель';
        button.style.left = '280px';
        textCanvas.style.marginLeft = '280px';
        textCanvas.style.width = 'calc(100% - 280px)';
    }
}
