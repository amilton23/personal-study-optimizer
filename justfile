format:
    ruff format . && ruff check --fix

test:
    uv run pytest

install-front:
    uv pip install -e . && cd flashcards-web && npm install

run:
    cd flashcards-web && npm run build && npm run dev