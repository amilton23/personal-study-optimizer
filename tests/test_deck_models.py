import pytest
from pydantic import ValidationError

from backend.graph.deck_models import Deck, validate_deck


def _card(i: int, category: str) -> dict:
    return {
        "id": i,
        "category": category,
        "subject": "test",
        "question": f"q{i}",
        "answer": f"a{i}",
        "source": "title - https://example.com",
    }


def test_validate_deck_success() -> None:
    cards = [_card(i + 1, "academic" if i < 10 else "practical") for i in range(20)]
    deck = Deck(topic="AI", cards=cards)

    assert validate_deck(deck) == []


def test_validate_deck_detects_split_errors() -> None:
    cards = [_card(i + 1, "academic" if i < 12 else "practical") for i in range(20)]
    deck = Deck(topic="AI", cards=cards)

    assert validate_deck(deck) == [
        "expected at most 10 academic, got 12",
    ]


def test_deck_model_rejects_more_than_20_cards() -> None:
    cards = [
        _card((i % 20) + 1, "academic" if i < 10 else "practical") for i in range(21)
    ]

    with pytest.raises(ValidationError):
        Deck(topic="AI", cards=cards)
