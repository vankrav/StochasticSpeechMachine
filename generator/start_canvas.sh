#!/bin/bash
# Скрипт для быстрого запуска Canvas модуля

# Определяем пути
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
METADATA_PATH="$PROJECT_ROOT/output_audio/metadata.json"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Canvas - Модуль визуализации текста"
echo "  Stochastic Speech Machine"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Проверяем наличие metadata.json
if [ ! -f "$METADATA_PATH" ]; then
    echo -e "${RED}✗ Ошибка: metadata.json не найден${NC}"
    echo -e "  Путь: $METADATA_PATH"
    echo ""
    echo "Сначала обработайте аудио файл:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./run.sh assets/audio.mp3"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Найден metadata.json${NC}"

# Подсчет количества семплов
SAMPLE_COUNT=$(python3 -c "import json; data=json.load(open('$METADATA_PATH')); print(data['total_words'])" 2>/dev/null || echo "?")
echo -e "${GREEN}✓ Семплов: $SAMPLE_COUNT${NC}"
echo ""

# Определяем порт
PORT=${1:-5000}

echo -e "${YELLOW}Запуск сервера...${NC}"
echo "  Адрес: http://127.0.0.1:$PORT"
echo "  Canvas: http://127.0.0.1:$PORT/canvas"
echo "  Generator: http://127.0.0.1:$PORT/"
echo ""
echo -e "${YELLOW}Нажмите Ctrl+C для остановки${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Запускаем сервер
cd "$SCRIPT_DIR"
python3 server.py --metadata "$METADATA_PATH" --port "$PORT"
