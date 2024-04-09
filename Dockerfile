FROM python:3.12

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .

RUN poetry run ./manage.py collectstatic --noinput

CMD ["sh", "./run_gunicorn.sh"]
