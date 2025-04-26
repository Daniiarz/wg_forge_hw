FROM python:3.12 as builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock ./

RUN $POETRY_HOME/bin/poetry install --no-interaction --no-root --no-cache

FROM python:3.12-slim as runtime

RUN apt -y update
RUN apt -y install curl

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}


COPY tests.py .
COPY server.py .
COPY entrypoint.sh .
COPY checker.sh .

RUN chmod 700 /entrypoint.sh
RUN chmod 755 /checker.sh

ENTRYPOINT ["./entrypoint.sh"]
