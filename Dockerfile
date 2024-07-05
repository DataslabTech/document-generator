FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /code/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /code/

RUN bash -c "poetry install --no-root"

# Verify the files copied (for debugging purposes)
RUN ls -la /code

ENV PYTHONPATH=.

COPY ./app /code/app

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]