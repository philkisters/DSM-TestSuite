# Build context is the repository root (see docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV CHALLENGES_DIR=/app/TestSuite/Challenges PYTHONUNBUFFERED=1 UV_LINK_MODE=copy PATH="/app/TestSuite/.venv/bin:$PATH"
WORKDIR /app/TestSuite
COPY dsm-db /app/dsm-db
COPY TestSuite/pyproject.toml TestSuite/uv.lock TestSuite/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY TestSuite/src ./src
COPY TestSuite/Challenges ./Challenges
RUN uv sync --frozen --no-dev && useradd -r appuser
USER appuser
EXPOSE 8000
CMD ["testsuite"]
