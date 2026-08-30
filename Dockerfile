FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv pip install --system -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
