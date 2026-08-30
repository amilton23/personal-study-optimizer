# Personal Study Optimizer

Agentic study app that researches a topic, builds a validated 20-card deck, and serves a quiz UI.

- Backend: Python + LangGraph + LangChain (OpenRouter models)
- Frontend: React + Vite + Tailwind (`flashcards-web/`)
- Output contract: **exactly 20 flashcards** (`10 academic + 10 practical`)

---

## Features

- Parallel research branches:
  - `academic_researcher` (paper-style insights)
  - `practical_researcher` (real-world/application insights)
- Professor/summarizer creates one unified deck with structured output
- Deterministic validation node enforces business rules:
  - 20 cards total
  - 10 academic
  - 10 practical
- Retry loop on validation failure (without rerunning whole pipeline)
- Quiz UX: questions first, answers only at end

---

## Architecture

```text
start_query
  ├─ academic_researcher
  └─ corporate_researcher (practical)
        \ 
         -> summarize (structured Deck)
              -> validate_deck
                   ├─ valid   -> END
                   └─ invalid -> summarize (retry, max 3)
```

Core files:

- `src/graph/research_graph.py` - graph nodes, edges, retry routing
- `src/graph/deck_models.py` - deck schema + deterministic validator
- `src/agents/academic_researcher.py` - academic branch prompt + search
- `src/agents/corporate_researcher.py` - practical branch prompt + search
- `src/tools/web_search.py` - Tavily + RSS + DuckDuckGo with freshness/reachability
- `src/api_server.py` - FastAPI endpoint for web app
- `flashcards-web/src/App.jsx` - quiz interface

---

## Requirements

- Python `>=3.11`
- Node.js `>=18`
- OpenRouter API key

Install backend deps:

```bash
pip install -e .
```

Install frontend deps:

```bash
cd flashcards-web
npm install
```

---

## Environment variables

Create `.env/.env`:

```env
OPENROUTER_API_KEY=your_key_here

# Optional model config
# OPENROUTER_OPENAI_MODEL=openai/gpt-4o-mini
# GEMINI_FOUNDATION_MODEL=google/gemini-3.1-flash-lite
# OPENROUTER_HTTP_REFERER=https://your-app-url
# OPENROUTER_APP_TITLE=Personal Study Optimizer

# Optional tracing
# LANGSMITH_TRACING=true
# LANGCHAIN_TRACING_V2=true
# LANGSMITH_API_KEY=lsv2_pt_xxx
# LANGSMITH_PROJECT=personal-study-optimizer
# LANGSMITH_ENDPOINT=https://api.smith.langchain.com
# LANGSMITH_WORKSPACE_ID=<workspace-uuid>

# Optional logs
# LOG_LEVEL=DEBUG

# Optional search quality
# TAVILY_API_KEY=tvly_xxx
```

---

## Run

### 1) CLI

```bash
python main.py "spaced repetition for medical students"
```

Prints final validated deck JSON.

### 2) API (backend)

```bash
uvicorn src.api_server:app --reload --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 3) Web app (frontend)

```bash
cd flashcards-web
npm run dev
```

Open: `http://localhost:5173`

---

## API contract

### `POST /api/flashcards`

Request:

```json
{ "topic": "transformers in healthcare" }
```

Success response:

```json
{
  "topic": "transformers in healthcare",
  "cards": [
    {
      "id": 1,
      "category": "academic",
      "subject": "...",
      "question": "...",
      "answer": "...",
      "source": "title - url"
    }
  ]
}
```

Failure response (`422`) when deck still invalid after retries:

```json
{
  "detail": {
    "message": "Deck failed validation after retries",
    "errors": ["expected 10 practical, got 9"]
  }
}
```

---

## Validation rules

Enforced in `src/graph/deck_models.py` and graph validator node:

- schema-level:
  - card id in `1..20`
  - category in `{academic, practical}`
  - deck length exactly `20`
- business-level:
  - exactly `10` academic + `10` practical

If invalid:
- append concrete errors to feedback
- regenerate in summarizer node
- retry up to 3 times

---

## Testing

Run tests:

```bash
pytest -q
```

or

```bash
just test
```

Current tests cover deck validation behavior.

---

## Notes (SOLID + YAGNI applied)

- Single responsibility by module:
  - research, summarization, validation, API, UI separated
- Minimal orchestration:
  - one retry loop only where needed (deck conformance)
- No speculative features:
  - strict scope: generate/validate/serve 20-card quiz

---

## Troubleshooting

- `Missing OPENROUTER_API_KEY`
  - set key in `.env/.env`
- frontend cannot reach backend
  - ensure backend at `http://127.0.0.1:8000`
- slow/weak source quality
  - add `TAVILY_API_KEY` for better web retrieval
- frequent validation retries
  - expected occasionally; deterministic validator will force exact format/split


## Next steps
1. Create a feature of uploading study files and then generate those flashcards.
2. Create a feature of settings for the user to customize their experience by:
    - Setting the number of flashcards to generate
    - Setting the type of flashcards to generate (academic, practical, etc.)
    - Setting the difficulty level of the flashcards
    - Setting the language of the flashcards
3. Develop a AI Tutor that can help the user learn the material through conversations and quizzes using the best learning techniques combined:
    - Simple understanding, avoiding memorizing.
    - Active recovery.
    - Spaced repetition.
    - Transform knowledge in questions.
    - Apply the knowledge in real scenarios.
    - Teach without looking.
    - Similar connections between concepts and analogies.

### Efficient protocol to unite everything:

**60-minute session**

#### Recovery (0-5 min)

What do I remember from the last session?
Write without consulting.

#### Learning (5-25 min)

- Study a small amount.
- Understand mechanisms and relationships.
- Don't try to absorb an entire chapter.

#### Recovery (25-40 min)

- Close everything.
- Explain the memory content.
- Ask yourself questions.
- Solve a few problems.

#### Correction (40-50 min)

- Consult the material.
- Identify exactly what you got wrong or forgot.
- Correct.

#### Application (50-60 min)

- Solve a new problem.
- Explain the concept.
- Create an example.
- Relate it to something you already know.

Then do **short reviews at 1, 3, 7, 14, 30 and 60+ days.**