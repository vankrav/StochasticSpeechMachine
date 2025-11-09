#!/bin/bash
# Скрипт быстрого запуска Stochastic Speech Machine

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка активации виртуального окружения
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Виртуальное окружение не активировано${NC}"
    echo "Активирую .venv..."
    source .venv/bin/activate
    if [ $? -ne 0 ]; then
        echo -e "${RED}Ошибка активации виртуального окружения${NC}"
        echo "Запустите вручную: source .venv/bin/activate"
        exit 1
    fi
    echo -e "${GREEN}✓ Виртуальное окружение активировано${NC}"
fi

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Использование: ./run.sh <audio_file> [--model <model_path>] [другие опции]"
    echo ""
    echo "Примеры:"
    echo "  ./run.sh audio.mp3"
    echo "  ./run.sh recording.wav --model ./models/vosk-model-small-ru-0.22"
    echo "  ./run.sh recording.wav -v"
    echo ""
    python speech_processor.py --help
    exit 0
fi

# Функция поиска модели Vosk
find_vosk_model() {
    # Ищем модель в локальной директории проекта
    local MODEL_PATHS=(
        "./models/vosk-model-small-ru-0.22"
        "./models/vosk-model-ru"
        "./models/ru"
    )
    
    for path in "${MODEL_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # Ищем любую директорию с моделью в ./models/
    if [ -d "./models" ]; then
        local first_model=$(find ./models -maxdepth 1 -type d -name "vosk-model-*" | head -n 1)
        if [ -n "$first_model" ]; then
            echo "$first_model"
            return 0
        fi
    fi
    
    return 1
}

# Проверяем, указана ли модель в аргументах
MODEL_SPECIFIED=0
for arg in "$@"; do
    if [[ "$arg" == "-m" ]] || [[ "$arg" == "--model" ]]; then
        MODEL_SPECIFIED=1
        break
    fi
done

# Если модель не указана, пытаемся найти автоматически
if [ $MODEL_SPECIFIED -eq 0 ]; then
    echo -e "${BLUE}Поиск модели Vosk...${NC}"
    AUTO_MODEL=$(find_vosk_model)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Найдена модель: $AUTO_MODEL${NC}"
        echo ""
        # Запуск с автоматически найденной моделью
        python speech_processor.py "$@" --model "$AUTO_MODEL"
    else
        echo -e "${RED}✗ Модель Vosk не найдена в ./models/${NC}"
        echo ""
        echo -e "${YELLOW}Установите модель с помощью:${NC}"
        echo "  ./setup_model.sh"
        echo ""
        echo "Или укажите путь к модели вручную:"
        echo "  ./run.sh $1 --model <путь_к_модели>"
        exit 1
    fi
else
    # Модель указана явно, запускаем как есть
    python speech_processor.py "$@"
fi
