FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip \
    && pip install --no-cache pipenv \
    && pip install --no-cache poetry

COPY poetry.lock pyproject.toml /app/

WORKDIR /app

RUN poetry config virtualenvs.create false \
    && poetry install --with dev

ENTRYPOINT ["/bin/bash"]

# Default command starts the FastAPI app via single-worker uvicorn.
# Single worker is a deliberate research-methodology choice: it isolates the
# effect of async I/O on latency/throughput/energy without multi-process
# concurrency confounding the comparison. Do not add --workers N or wrap
# with gunicorn without revisiting the measurement design.
CMD ["poetry", "run", "uvicorn", "realworld.asgi:app", "--host", "0.0.0.0", "--port", "8080"]