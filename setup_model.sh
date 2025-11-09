#!/bin/bash
# Скрипт для скачивания и установки модели Vosk

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODEL_DIR="./models"
MODEL_NAME="vosk-model-small-ru-0.22"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_NAME}.zip"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Установка модели Vosk для русского языка${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Проверяем, установлена ли уже модель
if [ -d "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓ Модель уже установлена: $MODEL_PATH${NC}"
    echo ""
    read -p "Переустановить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Установка отменена"
        exit 0
    fi
    echo -e "${YELLOW}Удаление старой модели...${NC}"
    rm -rf "$MODEL_PATH"
fi

# Создаем директорию для моделей
mkdir -p "$MODEL_DIR"

# Проверяем наличие wget или curl
if command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -O"
elif command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -L -o"
else
    echo -e "${RED}✗ Ошибка: не найдены wget или curl${NC}"
    echo "Установите один из них:"
    echo "  brew install wget"
    exit 1
fi

# Проверяем наличие unzip
if ! command -v unzip &> /dev/null; then
    echo -e "${RED}✗ Ошибка: не найден unzip${NC}"
    echo "Установите его:"
    echo "  brew install unzip"
    exit 1
fi

# Скачиваем модель
echo -e "${BLUE}Скачивание модели (размер ~45MB)...${NC}"
echo "URL: $MODEL_URL"
echo ""

ZIP_FILE="${MODEL_DIR}/${MODEL_NAME}.zip"

$DOWNLOAD_CMD "$ZIP_FILE" "$MODEL_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Ошибка при скачивании модели${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Модель скачана${NC}"

# Распаковываем
echo -e "${BLUE}Распаковка модели...${NC}"
unzip -q "$ZIP_FILE" -d "$MODEL_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Ошибка при распаковке${NC}"
    rm -f "$ZIP_FILE"
    exit 1
fi

# Удаляем архив
rm -f "$ZIP_FILE"

# Проверяем результат
if [ -d "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓ Модель успешно установлена!${NC}"
    echo ""
    echo "Путь к модели: $MODEL_PATH"
    echo "Размер: $(du -sh "$MODEL_PATH" | cut -f1)"
    echo ""
    echo -e "${GREEN}Теперь вы можете запустить:${NC}"
    echo "  ./run.sh your_audio.mp3"
    echo ""
else
    echo -e "${RED}✗ Ошибка: модель не найдена после установки${NC}"
    exit 1
fi
