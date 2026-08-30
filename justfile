format:
    ruff format . && ruff check --fix

test:
    uv run pytest

install-front:
    uv pip install -e . && cd frontend && npm install

run:
    cd frontend && npm run build && npm run dev

activate-server:
    uvicorn backend.api.server:app --reload --port 8000