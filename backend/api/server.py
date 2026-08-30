from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.graph.research_graph import research_graph


class DeckRequest(BaseModel):
    topic: str = Field(min_length=3)


app = FastAPI(title="Personal Study Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/flashcards")
def create_flashcards(payload: DeckRequest) -> dict:
    result = research_graph.invoke(
        {
            "query": payload.topic,
            "sources": [],
            "messages": [],
            "final_report": "",
            "deck": {},
            "validation_errors": [],
            "retry_count": 0,
        }
    )

    if result.get("validation_errors"):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Deck failed validation after retries",
                "errors": result["validation_errors"],
            },
        )

    return result["deck"]
