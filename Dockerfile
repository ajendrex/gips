FROM python:3.12

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .

RUN poetry run ./manage.py collectstatic --noinput

CMD ["sh", "./run_gunicorn.sh"]
