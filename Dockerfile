# --- СТАДИЯ 1: Сборка ---
FROM python:3.11-slim as builder

WORKDIR /app

# Запрещаем кеширование pip и создание .pyc файлов
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости для сборки (если понадобятся)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- СТАДИЯ 2: Финальный образ ---
FROM python:3.11-slim

WORKDIR /app

# Копируем из первой стадии только готовое окружение с библиотеками
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем только наши файлы кода
COPY main.py .
COPY database.py .

# Запуск
CMD ["python", "main.py"]