"""Reading a hospital's final bill into lines.

The document arrives as a photograph taken in a corridor or a PDF mailed by the
billing desk, and both come out of intake as words with positions on a page.
Rows are rebuilt from those positions rather than from the extracted text,
because a PDF's text layer emits a table cell at a time and OCR emits a line at
a time, and only the geometry says which of them belong to the same row.

Columns are read from the table's own header. That is what makes the quantity
and the rate usable: a row whose quantity times its rate does not come to the
amount charged is one of the faults worth raising, and a reader that only kept
figures it could reconcile would quietly discard exactly the lines it is there
to find.

What the reader will not do is guess. A row whose amount is ambiguous, a line
whose head cannot be placed, a total it could not find: each is recorded as
itself. The whole point of the check that follows is to be trusted at a billing
counter, and a reader that invented a figure to fill a gap would put a wrong
number into somebody's argument at the worst possible moment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from statistics import median

from app.bill import heads as head_rules
from app.core.logging import get_logger
from app.schemas.bill import BilledItem, ReadBill
from app.schemas.document import IngestedDocument, Page, SourceMode, Word
from app.schemas.money import ZERO, round_inr
from app.schemas.policy import ExpenseHead

log = get_logger(__name__)

# A token that is money and nothing else. Anchored, so "40mg" and "12/08/2026"
# stay in the description rather than becoming figures.
_MONEY_TOKEN = re.compile(
    r"^(?:rs\.?|inr|₹)?\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(?:/-|/=)?$", re.IGNORECASE
)
_SERIAL = re.compile(r"^\d{1,3}[.)]?$")

_HEADER_LEFT = re.compile(
    r"particular|description|item|service|charge head", re.IGNORECASE
)
_HEADER_RIGHT = re.compile(r"amount|total|value", re.IGNORECASE)
_QTY_HEADER = re.compile(r"qty|quantity|nos|units|days", re.IGNORECASE)
_RATE_HEADER = re.compile(r"rate|price|unit|tariff", re.IGNORECASE)
_AMOUNT_HEADER = re.compile(r"amount|total|value", re.IGNORECASE)

# Without this, "Bill No 3412" becomes a charge of three thousand four hundred
# and twelve rupees.
_METADATA = re.compile(
    r"^(bill\s*(no|number|date)|invoice|receipt\s*no|uhid|mrn|"
    r"(ip|op|mr|reg)\s*(no|number|id)|patient\s*(name|id)|name|"
    r"admitted\s*on|admission\s*date|date\s*of\s*admission|"
    r"discharge\s*date|date\s*of\s*discharge|date|time|age|sex|gender|"
    r"consultant\s*name|address|phone|mobile|gstin|gst\s*no|pan\s*no|"
    r"policy\s*(no|number)|tpa|insurer|claim\s*(no|number)|"
    r"bed\s*no|room\s*no|page)\b",
    re.IGNORECASE,
)
"""The label half of a metadata pair, tightly enough written that an item is not
caught by it. "Admission Kit" is a charge; "Admission Date" is not."""
_MONTH = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b", re.IGNORECASE
)
_PAGE_NUMBER = re.compile(r"\bpage\s*(no\.?|number)?\s*$", re.IGNORECASE)

_TOTAL_WORDS = re.compile(
    r"\b(total|gross|sub\s*total|bill amount|net amount|amount payable|"
    r"grand total|payable|balance|due|discount|concession|waiver|advance|"
    r"deposit|paid|received|rounded)\b",
    re.IGNORECASE,
)
_NET = re.compile(
    r"\b(net payable|amount payable|grand total|net amount|total payable|"
    r"balance due|payable by patient)\b",
    re.IGNORECASE,
)
_DISCOUNT = re.compile(r"\b(discount|concession|waiver|write off)\b", re.IGNORECASE)
_ADVANCE = re.compile(
    r"\b(advance|deposit|paid|received|part payment)\b", re.IGNORECASE
)
_GROSS = re.compile(
    r"\b(gross|sub\s*total|bill amount|total charges|total)\b", re.IGNORECASE
)

FOOTER_BAND = 0.94
"""Rows below this fraction of the page are the printer's footer, not the bill."""


@dataclass
class Token:
    """One word on a row, with where it sits when the page knows."""

    text: str
    x0: float | None = None
    x1: float | None = None
    confidence: float = 1.0

    @property
    def centre(self) -> float | None:
        return None if self.x0 is None or self.x1 is None else (self.x0 + self.x1) / 2


@dataclass
class Columns:
    """Where the quantity, rate and amount columns start."""

    qty: float | None = None
    rate: float | None = None
    amount: float | None = None

    @property
    def known(self) -> bool:
        return self.amount is not None

    def role_of(self, token: Token) -> str | None:
        """Which column a figure sits in, by its left edge."""
        if token.x0 is None:
            return None
        starts = [
            (start, role)
            for start, role in (
                (self.qty, "qty"), (self.rate, "rate"), (self.amount, "amount")
            )
            if start is not None
        ]
        # A value may be right-aligned under a left-aligned header, so a token
        # belongs to the last column that begins at or before it.
        landed = [role for start, role in sorted(starts) if start <= token.x0 + 2.0]
        return landed[-1] if landed else None


def parse_money(token: str) -> Decimal | None:
    match = _MONEY_TOKEN.match(token.strip())
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def rows_of(page: Page) -> list[list[Word]]:
    """Group a page's words into visual rows.

    A row is a run of words whose vertical centres sit within a fraction of a
    line height of each other. The tolerance is derived from the page rather
    than fixed, because a phone photograph and a mailed PDF differ by an order
    of magnitude in scale.
    """
    if not page.words:
        return []

    heights = [w.bbox.y1 - w.bbox.y0 for w in page.words if w.bbox.y1 > w.bbox.y0]
    tolerance = (median(heights) if heights else 10.0) * 0.6

    ordered = sorted(page.words, key=lambda w: ((w.bbox.y0 + w.bbox.y1) / 2, w.bbox.x0))
    rows: list[list[Word]] = []
    centre: float | None = None
    for word in ordered:
        middle = (word.bbox.y0 + word.bbox.y1) / 2
        if centre is None or abs(middle - centre) > tolerance:
            rows.append([word])
            centre = middle
        else:
            rows[-1].append(word)
            # Track the running centre so a gently sloping scan does not drift
            # out of its own row halfway across the page.
            centre = sum((w.bbox.y0 + w.bbox.y1) / 2 for w in rows[-1]) / len(rows[-1])

    return [sorted(row, key=lambda w: w.bbox.x0) for row in rows]


def _trailing_numbers(tokens: list[Token]) -> list[Token]:
    """The run of figures at the right-hand end of a row."""
    run: list[Token] = []
    for token in reversed(tokens):
        if parse_money(token.text) is None:
            break
        run.append(token)
    run.reverse()
    return run


def _looks_like_an_item(description: str) -> bool:
    if len(description) < 3:
        return False
    if _METADATA.match(description) or _PAGE_NUMBER.search(description):
        return False
    if _MONTH.search(description):
        return False
    return any(len(word) >= 3 and word.isalpha() for word in description.split())


class _Reader:
    def __init__(self, document: IngestedDocument) -> None:
        self.document = document
        self.bill = ReadBill(document_name=document.filename)
        self.section: ExpenseHead | None = None
        self.columns = Columns()
        self.in_table = False
        self.line_no = 0

    def run(self) -> ReadBill:
        self.bill.from_text_layer = all(
            page.source_mode is SourceMode.NATIVE for page in self.document.pages
        )
        self.bill.notes.extend(self.document.warnings)
        for page in self.document.pages:
            rows = rows_of(page)
            if rows:
                floor = page.height * FOOTER_BAND
                for row in rows:
                    if row[0].bbox.y0 >= floor:
                        continue
                    self._row(
                        [
                            Token(w.text, w.bbox.x0, w.bbox.x1, w.confidence)
                            for w in row
                        ],
                        page.page_index,
                    )
            else:
                for line in page.text.splitlines():
                    self._row(
                        [Token(word) for word in line.split()], page.page_index
                    )

        if not self.bill.items:
            self.bill.notes.append(
                "We could not find a table of charges on this document. If it is "
                "a photograph, one taken square-on in good light usually reads."
            )
        elif self.bill.gross_total is None and self.bill.net_payable is None:
            self.bill.notes.append(
                "We could not find the bill's own total, so the lines have been "
                "added up instead."
            )
        return self.bill

    def _row(self, tokens: list[Token], page_index: int) -> None:
        if not tokens:
            return
        joined = " ".join(t.text for t in tokens).strip()

        if not self.in_table and _HEADER_LEFT.search(joined) and _HEADER_RIGHT.search(joined):
            self._read_header(tokens)
            return

        run = _trailing_numbers(tokens)
        words = tokens[: len(tokens) - len(run)]
        description = " ".join(t.text for t in words).strip(" .:-|")

        if not run:
            if (head := head_rules.section_head(joined)) is not None:
                self.section = head
            return

        if _TOTAL_WORDS.search(description):
            self._total(description, parse_money(run[-1].text) or ZERO)
            return

        if not _looks_like_an_item(_strip_serial(description)):
            return
        if not self.in_table:
            # A table whose header was lost to OCR still has rows under it.
            self.in_table = True

        self._item(_strip_serial(description), run, page_index)

    def _read_header(self, tokens: list[Token]) -> None:
        """Learn where the quantity, rate and amount columns begin."""
        self.in_table = True
        for token in tokens:
            if token.x0 is None:
                continue
            if self.columns.qty is None and _QTY_HEADER.search(token.text):
                self.columns.qty = token.x0
            elif self.columns.rate is None and _RATE_HEADER.search(token.text):
                self.columns.rate = token.x0
            elif self.columns.amount is None and _AMOUNT_HEADER.search(token.text):
                self.columns.amount = token.x0

    def _total(self, description: str, amount: Decimal) -> None:
        if _DISCOUNT.search(description):
            self.bill.discount = round_inr(amount)
        elif _ADVANCE.search(description):
            self.bill.advance_paid = round_inr(amount)
        elif _NET.search(description):
            self.bill.net_payable = round_inr(amount)
        elif _GROSS.search(description):
            self.bill.gross_total = round_inr(amount)

    def _item(self, description: str, run: list[Token], page_index: int) -> None:
        figures = self._figures(run)
        amount = figures.get("amount")
        if amount is None or amount <= ZERO:
            return

        spare = figures.get("spare") or []
        if spare:
            # Figures the columns did not explain are still part of what the
            # line says, so they go back into the description rather than away.
            description = f"{description} {' '.join(_plain(v) for v in spare)}".strip()

        head = head_rules.head_of(description)
        from_section = False
        if head is None and self.section is not None:
            head, from_section = self.section, True

        self.line_no += 1
        self.bill.items.append(BilledItem(
            line_no=self.line_no,
            description=description,
            amount=round_inr(amount),
            qty=figures.get("qty"),
            rate=round_inr(figures["rate"]) if figures.get("rate") is not None else None,
            head=head,
            from_section=from_section,
            page_index=page_index,
            confidence=min((t.confidence for t in run), default=1.0),
        ))

    def _figures(self, run: list[Token]) -> dict:
        """Split a row's trailing figures into quantity, rate and amount."""
        values = [(token, parse_money(token.text) or ZERO) for token in run]

        if self.columns.known:
            placed: dict = {}
            spare: list[Decimal] = []
            for token, value in values:
                role = self.columns.role_of(token)
                if role and role not in placed:
                    placed[role] = value
                else:
                    spare.append(value)
            if "amount" in placed:
                placed["spare"] = spare
                return placed

        # No header, or nothing landed in the amount column: fall back to
        # position. Three figures at the end of a row in a bill are quantity,
        # rate and amount, whether or not they multiply out, and the ones that
        # do not are the reason this is worth reading at all.
        if len(values) >= 3:
            return {
                "qty": values[-3][1],
                "rate": values[-2][1],
                "amount": values[-1][1],
                "spare": [v for _, v in values[:-3]],
            }
        return {
            "amount": values[-1][1],
            "spare": [v for _, v in values[:-1]],
        }


def _strip_serial(description: str) -> str:
    """Bills number their rows. The number is not part of the item."""
    parts = description.split()
    if len(parts) > 1 and _SERIAL.match(parts[0]):
        return " ".join(parts[1:])
    return description


def _plain(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"


def read(document: IngestedDocument) -> ReadBill:
    """Read an ingested document as a hospital bill."""
    bill = _Reader(document).run()
    log.info(
        "read a bill",
        document=document.filename,
        lines=len(bill.items),
        placed=len(bill.placed),
        total=str(bill.line_total),
    )
    return bill
