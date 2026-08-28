from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Flashcard(BaseModel):
    id: int = Field(ge=1, le=20)
    category: Literal["academic", "practical"]
    subject: str
    question: str
    answer: str
    source: str | None = None


class Deck(BaseModel):
    topic: str
    cards: list[Flashcard] = Field(min_length=20, max_length=20)


def validate_deck(deck: Deck) -> list[str]:
    academic = sum(1 for card in deck.cards if card.category == "academic")
    practical = sum(1 for card in deck.cards if card.category == "practical")

    errors: list[str] = []
    if len(deck.cards) != 20:
        errors.append(f"expected 20 cards, got {len(deck.cards)}")
    if academic != 10:
        errors.append(f"expected 10 academic, got {academic}")
    if practical != 10:
        errors.append(f"expected 10 practical, got {practical}")
    return errors
