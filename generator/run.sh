#!/bin/bash

# Скрипт запуска генератора стохастической речи

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎛️  Stochastic Speech Generator${NC}"
echo "=================================="

# Проверка виртуального окружения
if [ ! -d "../.venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "Создайте его командой: python3 -m venv ../.venv"
    exit 1
fi

# Активация окружения
source ../.venv/bin/activate

# Проверка зависимостей
echo "Проверка зависимостей..."
pip install -q -r ../requirements.txt

# Стандартный путь к metadata
METADATA_PATH="../output_audio/metadata.json"

# Можно переопределить через аргумент
if [ -n "$1" ]; then
    METADATA_PATH="$1"
fi

# Проверка существования файла
if [ ! -f "$METADATA_PATH" ]; then
    echo "❌ metadata.json не найден: $METADATA_PATH"
    echo ""
    echo "Сначала обработайте аудио файл:"
    echo "  cd .."
    echo "  ./run.sh your_audio.mp3"
    exit 1
fi

echo -e "${GREEN}✓ Найден metadata: $METADATA_PATH${NC}"

# Запуск сервера
echo ""
echo "Запуск сервера..."
echo "Откройте в браузере: http://127.0.0.1:5001"
echo ""

python server.py --metadata "$METADATA_PATH" --port 5001
