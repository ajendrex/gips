FROM python:3.12

RUN apt-get update && apt-get install npm postgresql-client lighttpd -y
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

WORKDIR /app/frontend/tests
COPY frontend/tests/package.json frontend/tests/package-lock.json ./
RUN npm install

COPY frontend/tests ./
RUN npm run build

WORKDIR /app
COPY . .

RUN poetry run ./manage.py collectstatic --noinput

CMD ["sh", "./run_gunicorn.sh"]
