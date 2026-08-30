from __future__ import annotations

import random
from typing import Any, Literal

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
    cards: list[Flashcard] = Field(min_length=1, max_length=20)


def validate_deck(deck: Deck) -> list[str]:
    academic = sum(1 for card in deck.cards if card.category == "academic")
    practical = sum(1 for card in deck.cards if card.category == "practical")

    errors: list[str] = []
    if len(deck.cards) > 20:
        errors.append(f"expected at most 20 cards, got {len(deck.cards)}")
    if academic > 10:
        errors.append(f"expected at most 10 academic, got {academic}")
    if practical > 10:
        errors.append(f"expected at most 10 practical, got {practical}")
    return errors


def pick_random_cards_per_category(deck: Deck, limit_per_category: int = 10) -> Deck:
    academic = [card for card in deck.cards if card.category == "academic"]
    practical = [card for card in deck.cards if card.category == "practical"]

    picked = random.sample(academic, k=min(len(academic), limit_per_category))
    picked += random.sample(practical, k=min(len(practical), limit_per_category))
    random.shuffle(picked)

    normalized_cards = [
        card.model_copy(update={"id": index})
        for index, card in enumerate(picked, start=1)
    ]

    return Deck(topic=deck.topic, cards=normalized_cards)


def pick_random_cards_per_category_from_payload(
    payload: dict[str, Any], limit_per_category: int = 10
) -> Deck | None:
    raw_cards = payload.get("cards", [])
    if not isinstance(raw_cards, list):
        return None

    academic_raw: list[dict[str, Any]] = []
    practical_raw: list[dict[str, Any]] = []

    for item in raw_cards:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        if category == "academic":
            academic_raw.append(item)
        elif category == "practical":
            practical_raw.append(item)

    picked = random.sample(academic_raw, k=min(len(academic_raw), limit_per_category))
    picked += random.sample(
        practical_raw, k=min(len(practical_raw), limit_per_category)
    )
    random.shuffle(picked)

    if not picked:
        return None

    cards = [
        Flashcard(
            id=index,
            category=item["category"],
            subject=str(item.get("subject", "")),
            question=str(item.get("question", "")),
            answer=str(item.get("answer", "")),
            source=None if item.get("source") is None else str(item.get("source")),
        )
        for index, item in enumerate(picked, start=1)
    ]

    topic = payload.get("topic", "")
    return Deck(topic="" if topic is None else str(topic), cards=cards)
