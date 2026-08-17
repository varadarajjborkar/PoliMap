"""Cutting a policy document where its own structure says to cut it.

Extraction used to read one request per page against the first six thousand
characters. On the two-page schedule the test corpus mostly contains, that is
fine. On the document people actually hold, a forty-page wording, everything
past the cut was never read, and the terms that cost money are rarely on page
one.

The invariant that matters most here is that chunking loses nothing. A splitter
that quietly drops a heading or a table row is worse than no splitter, because
the figure it drops is indistinguishable from a figure the policy never stated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.core.config import GENERATED_DIR
from app.pipeline.s2_atomize.chunking import (
    MAX_CHARS,
    Chunk,
    chunk_document,
    chunk_page,
    heading_of,
    looks_like_table,
    section_for,
)
from app.schemas.document import Page, SourceMode
from app.schemas.policy import DocumentSection


def page_of(text: str, section=DocumentSection.UNKNOWN, index: int = 0) -> Page:
    return Page(
        page_index=index, width=595.0, height=842.0, text=text,
        source_mode=SourceMode.NATIVE, section=section,
    )


def normalise(line: str) -> str:
    """Compare on content, not on punctuation a heading match tidies away."""
    return re.sub(r"[^a-z0-9]", "", line.lower())


# --- heading detection ------------------------------------------------------


@pytest.mark.parametrize("line, expected", [
    ("4.2.1  Room Rent and Boarding Expenses", "4.2.1 Room Rent and Boarding Expenses"),
    ("2. ROOM RENT AND ASSOCIATED EXPENSES", "2 ROOM RENT AND ASSOCIATED EXPENSES"),
    ("SECTION C - EXCLUSIONS", "SECTION C - EXCLUSIONS"),
    ("PERMANENT EXCLUSIONS", "PERMANENT EXCLUSIONS"),
    ("(a) Pre-hospitalisation expenses", "a Pre-hospitalisation expenses"),
])
def test_headings_are_recognised(line, expected):
    assert heading_of(line) == expected


@pytest.mark.parametrize("line", [
    "",
    "The Company shall pay the reasonable and customary charges incurred.",
    "Room rent is limited to Rs. 5,000 per day, subject to the terms herein.",
    "   ",
])
def test_prose_is_not_mistaken_for_a_heading(line):
    assert heading_of(line) is None


def test_a_very_long_line_is_never_a_heading():
    assert heading_of("A" * 200) is None


# --- tables -----------------------------------------------------------------


@pytest.mark.parametrize("line", [
    "Cataract surgery          Rs. 40,000 per eye",
    "Room rent | 1% of sum insured | per day",
    "Co-payment                20%",
])
def test_table_rows_are_recognised(line):
    assert looks_like_table(line)


def test_a_table_is_never_split_by_size():
    """A row means nothing without the column heading above it. Splitting
    between the two turns a qualified limit into an unqualified one."""
    header = "Benefit                    Limit                 Condition"
    rows = "\n".join(
        f"Treatment {i:<14} Rs. {i * 1000:<14} per policy year"
        for i in range(400)
    )
    chunks = chunk_page(page_of(f"SCHEDULE OF BENEFITS\n{header}\n{rows}"))

    assert len(chunks) == 1
    assert chunks[0].contains_table


# --- sections ---------------------------------------------------------------


def test_the_heading_decides_the_section_not_a_word_further_down():
    """A general-conditions section that mentions exclusions in passing is not
    an exclusions section, and mislabelling it changes which clause wins a
    conflict during compilation."""
    section = section_for(
        "6 GENERAL CONDITIONS",
        "Nothing in this section limits the exclusions set out above.",
        DocumentSection.WORDING,
    )
    assert section is DocumentSection.WORDING


def test_a_benefits_table_is_not_read_as_the_policy_schedule():
    """They carry different precedence, so confusing them changes the answer."""
    assert section_for("SCHEDULE OF BENEFITS", "", DocumentSection.SCHEDULE) is (
        DocumentSection.BENEFIT_TABLE
    )


@pytest.mark.parametrize("heading", ["PERMANENT EXCLUSIONS", "4. EXCLUSIONS",
                                     "WHAT IS NOT COVERED"])
def test_exclusion_headings_are_recognised_in_their_usual_forms(heading):
    assert section_for(heading, "", DocumentSection.WORDING) is (
        DocumentSection.EXCLUSIONS
    )


def test_an_unheaded_chunk_falls_back_to_its_body():
    assert section_for("", "Policy Schedule\nPolicy No: ABC", DocumentSection.UNKNOWN) is (
        DocumentSection.SCHEDULE
    )


# --- the invariant ----------------------------------------------------------


def test_chunking_a_page_loses_no_text():
    text = (
        "POLICY SCHEDULE\n"
        "Sum Insured: Rs. 5,00,000\n"
        "2. ROOM RENT\n"
        "Limited to 1% of sum insured per day.\n"
        "3. WAITING PERIODS\n"
        "Pre-existing diseases: 36 months.\n"
        "4. PERMANENT EXCLUSIONS\n"
        "Cosmetic surgery is not covered.\n"
    )
    chunks = chunk_page(page_of(text))

    source = {normalise(line) for line in text.splitlines() if line.strip()}
    produced = {
        normalise(line)
        for chunk in chunks for line in chunk.text.splitlines() if line.strip()
    }
    assert not source - produced


def test_a_short_section_keeps_its_own_heading_when_merged():
    """Merging a small block into its neighbour used to drop the heading,
    which is the one line saying what the block is."""
    text = (
        "2. ROOM RENT\n"
        + "The Company shall pay room rent as stated in the schedule. " * 6
        + "\n3. WAITING PERIODS\nPre-existing diseases: 36 months.\n"
    )
    joined = " ".join(c.text for c in chunk_page(page_of(text)))
    assert "WAITING PERIODS" in joined


def test_no_chunk_exceeds_the_hard_ceiling_unless_it_is_a_table():
    prose = "The Company shall indemnify the insured person. " * 900
    for chunk in chunk_page(page_of(f"1. DEFINITIONS\n{prose}")):
        assert chunk.char_count <= MAX_CHARS + 200


def test_a_long_document_is_split_rather_than_truncated():
    """The defect this replaced: a page over six thousand characters had the
    remainder silently discarded before the model ever saw it."""
    body = "\n".join(
        f"{i}. SECTION {i}\nSub-limit of Rs. {i * 1000} applies per policy year."
        for i in range(1, 60)
    )
    page = page_of(body)
    chunks = chunk_page(page)

    covered = sum(chunk.char_count for chunk in chunks)
    assert covered >= page.char_count * 0.9
    assert len(chunks) > 1


def test_every_chunk_traces_back_to_a_page():
    pages = [page_of("1. DEFINITIONS\nA hospital means an institution.", index=i)
             for i in range(3)]
    for chunk in chunk_document(pages):
        assert 0 <= chunk.page_index < 3


def test_an_empty_page_produces_nothing():
    assert chunk_page(page_of("   \n\n  ")) == []


def test_chunk_describe_names_a_place_a_person_could_look():
    chunk = Chunk(page_index=3, text="x" * 80, heading="4. EXCLUSIONS")
    assert "page 4" in chunk.describe()
    assert "EXCLUSIONS" in chunk.describe()


# --- against the real corpus ------------------------------------------------


@pytest.fixture(scope="module")
def policy_pages():
    """Pages of a generated policy, read from the corpus manifest."""
    manifest = GENERATED_DIR / "policies" / "manifest.json"
    if not manifest.exists():
        pytest.skip("policy corpus not built")
    return json.loads(manifest.read_text())


def test_real_policy_documents_chunk_without_losing_lines(policy_pages):
    """The check that actually matters, run over documents the generator
    produced rather than fixtures written to pass."""
    from app.pipeline.s0_intake.intake import ingest
    from app.pipeline.s1_triage.triage import triage

    pdfs = sorted((GENERATED_DIR / "policies" / "clean").glob("*.pdf"))[:3]
    if not pdfs:
        pytest.skip("no clean policy PDFs in the corpus")

    for path in pdfs:
        document = triage(ingest(Path(path), save_page_images=False))
        chunks = chunk_document(document.pages)
        assert chunks

        source = {
            normalise(line)
            for page in document.pages for line in page.text.splitlines()
            if line.strip()
        }
        produced = {
            normalise(line)
            for chunk in chunks for line in chunk.text.splitlines() if line.strip()
        }
        assert not source - produced, f"{path.name} lost lines"


def test_real_policy_documents_find_their_schedule_and_exclusions(policy_pages):
    from app.pipeline.s0_intake.intake import ingest
    from app.pipeline.s1_triage.triage import triage

    pdfs = sorted((GENERATED_DIR / "policies" / "clean").glob("*.pdf"))[:3]
    if not pdfs:
        pytest.skip("no clean policy PDFs in the corpus")

    for path in pdfs:
        document = triage(ingest(Path(path), save_page_images=False))
        sections = {chunk.section for chunk in chunk_document(document.pages)}
        assert DocumentSection.EXCLUSIONS in sections
        assert DocumentSection.BENEFIT_TABLE in sections
