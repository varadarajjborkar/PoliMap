"""A photographed table still has rows, even when the text stream does not.

OCR reads a two-column benefit table by block, so it can hand back every label
in order and then every value in order. Read as text, "Room Rent Limit" is
followed by "Intensive Care Unit (ICU) Limit", and every rule that looks for a
label and then its value finds a label and then another label.

The fix is not to search further down: the next figure below "Room Rent Limit"
is the ICU limit, and attaching it would state a room cap the policy does not
have. The rows are rebuilt from where the words were recognised instead.
"""

from __future__ import annotations

from app.pipeline.s2_atomize import grammar
from app.pipeline.s2_atomize.layout import rows_text
from app.schemas.document import Page, SourceMode, Word
from app.schemas.policy import BoundingBox, DocumentSection

# A schedule as a camera sees it: labels down the left, values down the right,
# four visual rows. `text` is what OCR made of it, reading each column through
# in turn, which is the failure this exists for.
ROWS = [
    ("Sum Insured", "Rs. 3,00,000/-"),
    ("Room Rent Limit", "1% of Sum Insured per day, subject to a maximum of Rs. 5,000/- per day"),
    ("Intensive Care Unit (ICU) Limit", "Rs. 10,000/- per day"),
    ("Co-payment", "20% of each and every admissible claim"),
]

LABEL_X, VALUE_X, ROW_HEIGHT, CHAR_WIDTH = 60.0, 300.0, 18.0, 7.0


def _words_for(text: str, x: float, y: float) -> list[Word]:
    words = []
    for token in text.split():
        width = len(token) * CHAR_WIDTH
        words.append(Word(
            text=token,
            bbox=BoundingBox(x0=x, y0=y, x1=x + width, y1=y + ROW_HEIGHT),
            confidence=0.9,
        ))
        x += width + CHAR_WIDTH
    return words


def _photographed_page() -> Page:
    words: list[Word] = []
    for index, (label, value) in enumerate(ROWS):
        y = 100.0 + index * (ROW_HEIGHT * 2)
        words.extend(_words_for(label, LABEL_X, y))
        words.extend(_words_for(value, VALUE_X, y))

    # Column by column, which is the order that loses the pairing.
    stream = "\n".join(label for label, _ in ROWS)
    stream += "\n" + "\n".join(value for _, value in ROWS)

    return Page(
        page_index=0, width=900, height=1200, text=stream, words=words,
        source_mode=SourceMode.OCR, section=DocumentSection.SCHEDULE,
    )


def test_the_text_stream_really_does_lose_the_pairing():
    """The premise. Without this the rest of the file proves nothing."""
    page = _photographed_page()
    lines = page.text.splitlines()
    after_room = lines[lines.index("Room Rent Limit") + 1]
    assert after_room == "Intensive Care Unit (ICU) Limit"


def test_rows_are_rebuilt_from_where_the_words_sit():
    rebuilt = rows_text(_photographed_page()).splitlines()
    assert len(rebuilt) == len(ROWS)
    for line, (label, value) in zip(rebuilt, ROWS, strict=True):
        assert line.startswith(label)
        assert value in line


def test_a_label_finds_the_value_on_its_own_visual_row():
    page = _photographed_page()
    found = grammar.find_in_page(
        page, grammar.ROOM_RENT_RE, value_test=grammar._has_amount_or_pct
    )
    assert len(found) == 1
    assert "1% of Sum Insured" in found[0].value_text
    assert "5,000" in found[0].value_text


def test_the_room_rule_does_not_reach_the_icu_figure():
    """The wrong answer this replaces: the next figure down the page."""
    page = _photographed_page()
    found = grammar.find_in_page(
        page, grammar.ROOM_RENT_RE, value_test=grammar._has_amount_or_pct
    )
    assert "10,000" not in found[0].value_text


def test_a_photographed_schedule_yields_the_capped_room_limit():
    page = _photographed_page()
    room = [
        c for c in grammar.extract_page(page)
        if c.kind.value == "room_rent_cap"
    ]
    assert len(room) == 1
    assert room[0].params == {
        "basis": "pct_with_max", "pct_of_si": "1", "amount_inr": "5000",
        "per_day": True,
    }


def test_a_native_page_is_never_rebuilt():
    """Its own text layer carries the publisher's line structure already."""
    page = _photographed_page()
    page.source_mode = SourceMode.NATIVE
    assert rows_text(page) == ""


def test_a_page_with_no_word_boxes_is_never_rebuilt():
    page = _photographed_page()
    page.words = []
    assert rows_text(page) == ""


def test_rebuilding_is_a_fallback_and_cannot_displace_a_reading():
    """A page whose text already pairs the row is left exactly as it reads."""
    page = _photographed_page()
    page.text = "Room Rent Limit    Rs. 4,000 per day"
    found = grammar.find_in_page(
        page, grammar.ROOM_RENT_RE, value_test=grammar._has_amount_or_pct
    )
    assert "4,000" in found[0].value_text
    assert "5,000" not in found[0].value_text
