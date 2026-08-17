"""Finding a treatment by the words people actually use.

The catalogue holds 126 clinical names. The person searching was handed a chit
an hour ago and was told their father needs "a stent". If the picker cannot get
from what they type to the right row, nothing downstream matters, because
everything downstream is costed against that row.

The ranking here mirrors the one in the interface. Keeping it under test on this
side means the words themselves, which live in the generator, cannot drift away
from what they are supposed to reach.
"""

from __future__ import annotations

import json

import pytest

from app.core.config import GENERATED_DIR
from datagen.synonyms import SPECIALTY_TERMS, SYNONYMS, specialty_terms_for, synonyms_for


@pytest.fixture(scope="module")
def procedures():
    path = GENERATED_DIR / "procedures.json"
    if not path.exists():
        pytest.skip("procedure catalogue not built")
    return json.loads(path.read_text())


def score(procedure: dict, needle: str) -> int:
    """The interface's ranking, kept in step deliberately.

    Every route to a row is scored and the best wins. Returning on the first
    match was the original defect: "Angioplasty with single stent" contains the
    word "stent", so it scored on the weak name-contains rule and never reached
    the exact synonym that makes it the answer.
    """
    name = procedure["name"].lower()
    best = 0
    if name == needle:
        best = 100
    elif name.startswith(needle):
        best = 90
    elif needle in name:
        best = 70

    synonyms = procedure.get("synonyms", [])
    if any(s == needle for s in synonyms):
        best = max(best, 95)
    elif any(s.startswith(needle) for s in synonyms):
        best = max(best, 80)
    elif any(needle in s for s in synonyms):
        best = max(best, 55)

    terms = procedure.get("specialty_terms", [])
    if any(t == needle for t in terms):
        best = max(best, 40)
    elif any(needle in t for t in terms):
        best = max(best, 25)
    return best


def top_match(procedures: list[dict], query: str) -> str | None:
    ranked = sorted(
        ((score(p, query), p["name"]) for p in procedures),
        key=lambda pair: (-pair[0], pair[1]),
    )
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None


# What a caregiver types, and what they mean by it.
EXACT_EXPECTATIONS = [
    ("heart blockage", "Angioplasty with single stent"),
    ("stent", "Angioplasty with single stent"),
    ("gall bladder", "Laparoscopic cholecystectomy"),
    ("delivery", "Normal delivery"),
    ("c section", "Caesarean section"),
    ("piles", "Haemorrhoidectomy"),
    ("bypass", "Coronary artery bypass graft"),
    ("slip disc", "Lumbar discectomy"),
    ("sugar", "Diabetic ketoacidosis"),
    ("fits", "Epilepsy evaluation admission"),
    ("broken hip", "Hip fracture hemiarthroplasty"),
    ("typhoid", "Enteric fever"),
    ("prostate", "Transurethral resection of prostate"),
    ("pacemaker", "Permanent pacemaker implantation"),
    ("fibroid", "Myomectomy"),
]


@pytest.mark.parametrize("query, expected", EXACT_EXPECTATIONS)
def test_layman_words_reach_the_right_treatment(procedures, query, expected):
    assert top_match(procedures, query) == expected


# Words that should find something sensible without one single right answer.
@pytest.mark.parametrize("query", [
    "kidney stone", "cataract", "appendix", "chemo", "dengue",
    "knee replacement", "hernia", "stroke", "covid", "snake bite",
])
def test_common_words_find_something(procedures, query):
    assert top_match(procedures, query) is not None


def test_a_name_match_beats_a_specialty_term(procedures):
    """"bone" narrows the field; it does not name a treatment in it, so it must
    never outrank a row whose own name the user typed."""
    knee = next(p for p in procedures if p["name"] == "Total knee replacement, single")
    assert score(knee, "knee") > score(knee, "bone")


def test_an_exact_layman_word_beats_a_loose_name_match(procedures):
    """The defect: a search for "stent" returned a ureteric stent, because a
    weak name-contains match was returned before the exact synonym was seen."""
    angioplasty = next(
        p for p in procedures if p["name"] == "Angioplasty with single stent"
    )
    ureteric = next(p for p in procedures if p["name"] == "Ureteric stent placement")
    assert score(angioplasty, "stent") > score(ureteric, "stent")


def test_specialty_words_do_not_claim_a_specific_treatment(procedures):
    """A single combined list put "delivery" on every obstetrics row, so the
    search answered with an ovarian cystectomy."""
    cystectomy = next(p for p in procedures if p["name"] == "Ovarian cystectomy")
    assert "delivery" not in cystectomy.get("synonyms", [])
    assert "delivery" not in cystectomy.get("specialty_terms", [])


# --- the tables themselves --------------------------------------------------


def test_every_synonym_key_matches_a_real_procedure(procedures):
    """A typo in a code prefix means those words reach nothing, silently. The
    first version of this file listed CP-GMED, CP-NSUR and CP-ENDO, none of
    which exist, so "sugar" and "brain surgery" found nothing at all."""
    codes = [p["code"] for p in procedures]
    for key in [*SYNONYMS, *SPECIALTY_TERMS]:
        matched = any(
            code == key or (key.endswith("-") and code.startswith(key))
            for code in codes
        )
        assert matched, f"{key} matches no procedure in the catalogue"


def test_every_procedure_is_reachable_by_some_word(procedures):
    """A row nobody can find is a row that does not exist."""
    for procedure in procedures:
        code = procedure["code"]
        words = synonyms_for(code) + specialty_terms_for(code)
        assert words, f"{code} {procedure['name']} has no search words at all"


def test_synonyms_are_lowercase_and_stripped():
    """Matching is done on a lowercased query, so anything else never matches."""
    for words in [*SYNONYMS.values(), *SPECIALTY_TERMS.values()]:
        for word in words:
            assert word == word.lower().strip()
