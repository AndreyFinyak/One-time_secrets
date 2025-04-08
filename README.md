# One-Time Secrets

One-Time Secrets — это приложение для безопасного обмена секретами, которое использует PostgreSQL для хранения данных и Alembic для управления миграциями базы данных.

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd One-time_secrets
   ```

2. Убедитесь, что у вас установлен Docker и Docker Compose.

3. Создайте файл `.env` на основе `.env.sample`:
   ```bash
   cp .env.sample .env
   ```
   Заполните переменные окружения в `.env`.

4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск

1. Запустите приложение с помощью Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Примените миграции базы данных:
   ```bash
   docker-compose run alembic upgrade head
   ```

3. Приложение будет доступно по адресу: [http://localhost:8000](http://localhost:8000).

## Использование

- Для работы с API используйте документацию Swagger: [http://localhost:8000/docs](http://localhost:8000/docs).

## Логирование

Для логирования используется библиотека Loguru. Логи сохраняются в папке `logs`.

## Миграции базы данных

Для управления схемой базы данных используется Alembic. Команды для работы с миграциями:
- Создание новой миграции:
  ```bash
  alembic revision --autogenerate -m "Описание изменений"
  ```
- Применение миграций:
  ```bash
  alembic upgrade head
  ```

## Переменные окружения

- `DATABASE_URL` — строка подключения к базе данных PostgreSQL.
- `FERNET_KEY` — ключ для шифрования данных.

## Лицензия

Этот проект распространяется под лицензией MIT.
