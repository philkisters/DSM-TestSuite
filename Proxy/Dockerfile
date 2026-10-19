# Build context is the repository root (see docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/Proxy/.venv/bin:$PATH"
WORKDIR /app/Proxy
COPY dsm-protocol /app/dsm-protocol
COPY Proxy/pyproject.toml Proxy/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY Proxy/src ./src
RUN uv sync --frozen --no-dev && useradd -r appuser
USER appuser
EXPOSE 9000 9001 9002
CMD ["python", "-m", "proxy"]
