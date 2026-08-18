"""The stay as one printable page.

Somebody arguing at a billing counter, or handing their claim to a relative who
has just arrived, needs the whole thing on paper: what the policy says, what was
estimated, what has actually been spent, and where each figure came from. A
screen cannot be put in front of a hospital insurance desk and a phone battery
does not last a five-day admission.

Written to be read by somebody else. Every figure carries the clause or the
receipt behind it, because the document's job is to be checkable by a person who
was not there when it was produced, and a summary that cannot be checked is
worth nothing at a counter.
"""

from __future__ import annotations

import io
from datetime import UTC, date, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core import typeface
from app.schemas.money import format_inr

INK = colors.HexColor("#10151C")
MUTED = colors.HexColor("#5B6672")
RULE = colors.HexColor("#D6DBE1")
BAND = colors.HexColor("#EEF3F1")
BRAND = colors.HexColor("#0F5C4A")

FONT, FONT_BOLD, SUPPORTS_RUPEE = typeface.resolve()


def rupee_safe(text: str) -> str:
    return text if SUPPORTS_RUPEE else text.replace("₹", "Rs. ")


_styles = getSampleStyleSheet()

BODY = ParagraphStyle(
    "body", parent=_styles["Normal"], fontName=FONT, fontSize=9,
    leading=12.5, textColor=INK,
)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.8, leading=10.5,
                       textColor=MUTED)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.5, leading=11)
CELL_BOLD = ParagraphStyle("cellb", parent=CELL, fontName=FONT_BOLD)
CELL_RIGHT = ParagraphStyle("cellr", parent=CELL, alignment=2)
CELL_RIGHT_BOLD = ParagraphStyle("cellrb", parent=CELL_RIGHT, fontName=FONT_BOLD)
TITLE = ParagraphStyle("title", parent=BODY, fontName=FONT_BOLD, fontSize=16,
                       leading=19, textColor=BRAND)
H2 = ParagraphStyle("h2", parent=BODY, fontName=FONT_BOLD, fontSize=10,
                    leading=13, spaceBefore=10, spaceAfter=4)

_TABLE = TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])

_HEADED = TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), BAND),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])

PAGE_WIDTH = A4[0] - 36 * mm

DISCLAIMER = (
    "This is an estimate produced from the documents supplied, not a quotation "
    "and not an approval. Only your insurer can decide a claim, and only the "
    "hospital can price your treatment. Nothing here is medical advice."
)


def _heading(text: str):
    return Paragraph(rupee_safe(text), H2)


def _pairs(rows: list[tuple[str, str]], widths=(0.42, 0.58)) -> Table:
    """A two-column block: label on the left, figure on the right."""
    table = Table(
        [
            [Paragraph(rupee_safe(label), CELL),
             Paragraph(rupee_safe(value), CELL_RIGHT)]
            for label, value in rows
        ],
        colWidths=[PAGE_WIDTH * widths[0], PAGE_WIDTH * widths[1]],
    )
    table.setStyle(_TABLE)
    return table


def _table(header: list[str], rows: list[list[str]], widths: list[float]) -> Table:
    data = [[Paragraph(rupee_safe(h), CELL_BOLD) for h in header]]
    for row in rows:
        data.append([
            Paragraph(
                rupee_safe(cell),
                CELL_RIGHT if index and index == len(row) - 1 else CELL,
            )
            for index, cell in enumerate(row)
        ])
    table = Table(data, colWidths=[PAGE_WIDTH * w for w in widths], repeatRows=1)
    table.setStyle(_HEADED)
    return table


def build(session, *, generated_at: datetime | None = None) -> bytes:
    """Render one session into a PDF."""
    policy = session.policy
    if policy is None:
        raise ValueError("There is no policy on this stay yet.")

    when = generated_at or datetime.now(UTC)
    story: list = []

    story.append(Paragraph("Your hospital stay", TITLE))
    story.append(Paragraph(
        f"Prepared {when:%d %B %Y}"
        + (f" · {session.document_name}" if session.document_name else ""),
        SMALL,
    ))
    story.append(Spacer(1, 8))

    _cover(story, session, policy)
    _who(story, policy)
    _not_yet_covered(story, policy)
    _chosen(story, session)
    _estimate(story, session)
    _bill(story, session)
    _spent(story, session)
    _outstanding(story, session)

    story.append(Spacer(1, 10))
    story.append(Paragraph(DISCLAIMER, SMALL))

    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Your hospital stay", author="PoliMap",
    ).build(story)
    return buffer.getvalue()


# --- sections ---------------------------------------------------------------


def _cover(story: list, session, policy) -> None:
    story.append(_heading("Your cover"))

    rows = [
        ("Insurer", policy.meta.insurer_name or "Not stated"),
        ("Policy number", policy.meta.policy_number or "Not stated"),
        ("Total cover this year", format_inr(policy.sum_insured)),
    ]
    if policy.sum_insured_remaining is not None:
        rows.append(("Cover left", format_inr(policy.available_cover)))
    rows.append(
        ("Room you are covered for", policy.room_limit.describe(policy.sum_insured))
    )
    if policy.copay_pct > 0:
        share = f"{policy.copay_pct:g}% of every claim"
        if policy.copay_above_age:
            share += f", for members aged {policy.copay_above_age} and above"
        rows.append(("Your share", share))
    if policy.deductible > 0:
        rows.append(("You pay first", format_inr(policy.deductible)))
    if policy.meta.start_date:
        period = f"{policy.meta.start_date:%d %b %Y}"
        if policy.meta.end_date:
            period += f" to {policy.meta.end_date:%d %b %Y}"
        rows.append(("Policy period", period))
    rows.append((
        "Consumables",
        "Covered" if policy.covers_consumables else "Not covered, yours to pay",
    ))
    if session.second_policy is not None:
        from app.pipeline.s6_simulate import stack

        rows.append((
            "Second policy",
            f"{stack.label_for(session.second_policy)}, "
            f"{format_inr(session.second_policy.sum_insured)}",
        ))

    story.append(_pairs(rows))


def _who(story: list, policy) -> None:
    if not policy.insured:
        return
    story.append(_heading("Who is covered"))
    story.append(_table(
        ["Name", "Relationship", "Age"],
        [
            [p.name, p.relationship or "-", str(p.age) if p.age is not None else "-"]
            for p in policy.insured
        ],
        [0.5, 0.32, 0.18],
    ))


def _not_yet_covered(story: list, policy) -> None:
    if not policy.waiting_periods:
        return
    story.append(_heading("Waiting periods"))

    today = date.today()
    rows = []
    for wait in policy.waiting_periods:
        if policy.meta.start_date:
            clears = wait.clears_on(policy.meta.start_date)
            when = (
                f"served {clears:%d %b %Y}" if clears <= today
                else f"covered from {clears:%d %b %Y}"
            )
        else:
            when = "start date not read"
        rows.append([wait.applies_to, wait.describe(), when])

    story.append(_table(
        ["Applies to", "Length", "Status"], rows, [0.46, 0.18, 0.36]
    ))


def _chosen(story: list, session) -> None:
    journey = session.journey
    if journey is None or not journey.hospital_name:
        return
    story.append(_heading("Where you are being treated"))
    rows = [
        ("Hospital", journey.hospital_name),
        ("Stage", journey.stage.label),
    ]
    if journey.room_category:
        rows.append(("Room", journey.room_category.label))
    if journey.room_rate_per_day:
        rows.append(("Room rate", f"{format_inr(journey.room_rate_per_day)} a day"))
    if journey.admitted_at:
        rows.append(("Admitted", f"{journey.admitted_at:%d %B %Y}"))
    story.append(_pairs(rows))


def _estimate(story: list, session) -> None:
    """The waterfall, which is the part worth arguing from.

    Every line names the reason money came off, so somebody at a counter can
    point at one of them and ask about it, which is the only reason to print an
    estimate rather than a total.
    """
    match = session.match
    if match is None or not match.options:
        return

    best = match.options[0]
    result = best.simulation
    story.append(_heading("What this was estimated to cost"))
    story.append(Paragraph(
        rupee_safe(
            f"At {result.hospital_name}, in a {result.room_category.label.lower()}."
        ),
        SMALL,
    ))
    story.append(Spacer(1, 4))

    rows = [["Hospital's estimate", "", format_inr(result.gross_total)]]
    for step in result.steps:
        rows.append([
            step.kind.label,
            step.explanation,
            format_inr(abs(step.deducted))
            if step.deducted >= 0 else f"+{format_inr(-step.deducted)}",
        ])
    rows.append(["Your insurer pays", "", format_inr(result.payable_by_insurer)])
    rows.append(["You pay", "", format_inr(result.out_of_pocket)])

    story.append(_table(["", "Why", "Amount"], rows, [0.28, 0.52, 0.20]))

    if result.notes:
        story.append(Spacer(1, 4))
        for note in result.notes[:3]:
            story.append(Paragraph(rupee_safe(f"• {note}"), SMALL))


def _bill(story: list, session) -> None:
    """What to raise about the final bill, in the words to raise it in.

    On paper rather than only on a screen because this is read out at a counter,
    standing up, with the bill in the other hand. A phone that has to be woken
    and scrolled while somebody waits is a phone that gets put away.
    """
    review = session.bill_review
    if review is None or not review.findings:
        return

    raisable = [f for f in review.findings if f.ask]
    if not raisable:
        return

    story.append(_heading("What to ask at the billing counter"))
    if review.questionable > 0:
        story.append(Paragraph(
            rupee_safe(
                f"{format_inr(review.questionable)} of this bill sits on lines "
                f"worth asking about."
            ),
            SMALL,
        ))
        story.append(Spacer(1, 4))

    for finding in raisable:
        block = [
            Paragraph(rupee_safe(f"<b>{finding.headline}</b>"), CELL),
            Paragraph(rupee_safe(finding.ask), SMALL),
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 4))


def _spent(story: list, session) -> None:
    journey = session.journey
    if journey is None or not journey.costs:
        return

    story.append(_heading("What has actually been billed"))
    rows = [
        [
            f"{entry.recorded_at:%d %b}",
            entry.head.label,
            entry.description or "-",
            format_inr(entry.amount),
        ]
        for entry in journey.costs
    ]
    rows.append(["", "Total", "", format_inr(journey.accrued_total)])
    story.append(_table(
        ["Date", "Head", "Description", "Amount"], rows, [0.13, 0.24, 0.43, 0.20]
    ))


def _outstanding(story: list, session) -> None:
    """Only what is still to be done. A printed list of ticked boxes is a poster."""
    journey = session.journey
    policy = session.policy
    if journey is None or policy is None:
        return

    from app.api.session import datasets
    from app.journey import checklist

    items = [
        i for i in checklist.items_for(
            journey, policy,
            procedure=datasets.procedures.get(journey.procedure_code or ""),
        )
        if not i.done
    ]
    if not items:
        return

    block = [_heading(f"Still to do: {journey.stage.label.lower()}")]
    for item in items:
        block.append(Paragraph(rupee_safe(f"[ ]  {item.text}"), CELL))
        if item.why:
            block.append(Paragraph(rupee_safe(f"      {item.why}"), SMALL))
        block.append(Spacer(1, 3))
    story.append(KeepTogether(block))
