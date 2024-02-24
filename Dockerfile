FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

COPY poetry.lock pyproject.toml src /app/

WORKDIR /app

ENV POETRY_VIRTUALENVS_IN_PROJECT true

RUN pip install --upgrade pip \
    pip install poetry && poetry install

# Create a non-root user and switch to it
RUN groupadd -r apiuser && useradd -r -m -g apiuser apiuser

# Switch to the non-root user
USER apiuser

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=20s --start-period=5s --retries=3 CMD ["curl --fail -so /dev/null http://localhost:80/health"]

ENTRYPOINT [ ".venv/bin/uvicorn", "whisper_batch_api.main:app", "--host",  "0.0.0.0", "--port", "80" ]
