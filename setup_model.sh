#!/bin/bash
# Скрипт для скачивания и установки моделей Vosk и RuBERT

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
echo -e "${BLUE}Установка моделей для Speech Machine${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Будут установлены:"
echo "  1. Vosk - модель распознавания речи (~45MB)"
echo "  2. RuBERT - модель анализа эмоций (~500MB)"
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
    echo -e "${GREEN}✓ Модель Vosk успешно установлена!${NC}"
    echo ""
    echo "Путь к модели: $MODEL_PATH"
    echo "Размер: $(du -sh "$MODEL_PATH" | cut -f1)"
    echo ""
else
    echo -e "${RED}✗ Ошибка: модель Vosk не найдена после установки${NC}"
    exit 1
fi

# ========================================
# УСТАНОВКА МОДЕЛИ ЭМОЦИЙ (RuBERT)
# ========================================
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Установка модели анализа эмоций${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Проверяем активацию виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Виртуальное окружение не активировано${NC}"
    if [ -f ".venv/bin/activate" ]; then
        echo "Активация .venv..."
        source .venv/bin/activate
    else
        echo -e "${RED}✗ Ошибка: виртуальное окружение не найдено${NC}"
        echo "Создайте его командой: python3.11 -m venv .venv"
        exit 1
    fi
fi

# Проверяем установку transformers
if ! python -c "import transformers" 2>/dev/null; then
    echo -e "${YELLOW}⚠ transformers не установлен, устанавливаем зависимости...${NC}"
    pip install -q transformers torch safetensors
fi

# Скачиваем модель RuBERT
echo -e "${BLUE}Загрузка модели RuBERT (~500MB)...${NC}"
echo "Модель: sismetanin/rubert-ru-sentiment-rusentiment"
echo ""
echo "Это может занять несколько минут..."
echo ""

# Используем Python для загрузки модели с прогресс-баром
python3 << 'PYTHON_SCRIPT'
import sys
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Включаем отображение прогресса загрузки
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '0'

try:
    print("📦 Загрузка токенизатора...")
    print("-" * 50)
    tokenizer = AutoTokenizer.from_pretrained(
        "sismetanin/rubert-ru-sentiment-rusentiment"
    )
    print("✓ Токенизатор загружен")
    print()
    
    print("📦 Загрузка модели (используется safetensors)...")
    print("-" * 50)
    model = AutoModelForSequenceClassification.from_pretrained(
        "sismetanin/rubert-ru-sentiment-rusentiment",
        use_safetensors=True
    )
    
    # Проверяем размер закэшированной модели
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    print()
    print("=" * 50)
    print("✓ Модель RuBERT успешно загружена!")
    print("=" * 50)
    print(f"  Кэш: {cache_dir}")
    
    # Подсчитываем размер кэша (опционально)
    try:
        import subprocess
        result = subprocess.run(['du', '-sh', cache_dir], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            size = result.stdout.split()[0]
            print(f"  Размер кэша: {size}")
    except:
        pass
    
    sys.exit(0)
    
except Exception as e:
    print()
    print("=" * 50)
    print(f"✗ Ошибка при загрузке модели: {e}")
    print("=" * 50)
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✓ ВСЕ МОДЕЛИ УСТАНОВЛЕНЫ!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "Установленные модели:"
    echo "  • Vosk: $MODEL_PATH"
    echo "  • RuBERT: ~/.cache/huggingface/"
    echo ""
    echo -e "${GREEN}Теперь вы можете запустить:${NC}"
    echo "  ./run.sh your_audio.mp3"
    echo ""
else
    echo -e "${RED}✗ Ошибка при установке модели эмоций${NC}"
    exit 1
fi
