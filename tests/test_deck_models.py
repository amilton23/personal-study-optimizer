import pytest
from pydantic import ValidationError

from src.graph.deck_models import Deck, validate_deck


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
        "expected 10 academic, got 12",
        "expected 10 practical, got 8",
    ]


def test_deck_model_requires_20_cards() -> None:
    cards = [_card(i + 1, "academic") for i in range(19)]

    with pytest.raises(ValidationError):
        Deck(topic="AI", cards=cards)
