"""Render policy blueprints into realistic policy documents.

Layout follows the convention Indian insurers use: a schedule page carrying this
policyholder's actual figures, then wording pages carrying generic terms. That
separation is not cosmetic; it is the distinction the triage stage has to make,
because the schedule overrides the wording when they disagree, and a pipeline
that reads them as one document will confidently report the wrong number.

Decoy figures (premium, GST, agent code, UIN) are placed deliberately close to
the sum insured. Grabbing the premium instead of the cover amount is the single
most common extraction failure, and the corpus should punish it.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core import typeface
from app.schemas.money import format_inr
from datagen.policies import (
    PolicyBlueprint,
    _icu_limit_sentence,
    _room_limit_sentence,
    write_amount,
)

INK = colors.HexColor("#111111")
RULE = colors.HexColor("#666666")
BAND = colors.HexColor("#E8E8E8")

FONT, FONT_BOLD, SUPPORTS_RUPEE = typeface.resolve()


def _rupee_safe(text: str) -> str:
    """Strip the rupee sign when the active font cannot draw it."""
    return text if SUPPORTS_RUPEE else text.replace("₹", "Rs. ")


_styles = getSampleStyleSheet()

BODY = ParagraphStyle(
    "body", parent=_styles["Normal"], fontName=FONT, fontSize=8.5,
    leading=11.5, textColor=INK,
)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=10.5)
CELL_BOLD = ParagraphStyle("cellb", parent=CELL, fontName=FONT_BOLD)
JUSTIFIED = ParagraphStyle("just", parent=BODY, alignment=TA_JUSTIFY)
H1 = ParagraphStyle(
    "h1", parent=BODY, fontName=FONT_BOLD, fontSize=13, leading=16,
    spaceAfter=2,
)
H2 = ParagraphStyle(
    "h2", parent=BODY, fontName=FONT_BOLD, fontSize=9.5, leading=13,
    spaceBefore=8, spaceAfter=3,
)
CENTRE = ParagraphStyle("centre", parent=BODY, alignment=1)

TABLE_STYLE = TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), BAND),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])

PLAIN_TABLE_STYLE = TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (0, -1), BAND),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])


def _footer(bp: PolicyBlueprint):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 6.5)
        canvas.setFillColor(RULE)
        canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
        canvas.drawString(18 * mm, 11 * mm, f"{bp.insurer_name}  |  UIN: {bp.uin}")
        canvas.drawRightString(
            A4[0] - 18 * mm, 11 * mm, f"Policy No. {bp.policy_number}  |  Page {doc.page}"
        )
        canvas.restoreState()

    return draw


def _kv_table(rows: list[tuple[str, str]], widths=(58 * mm, 116 * mm)) -> Table:
    data = [[Paragraph(_rupee_safe(k), CELL_BOLD), Paragraph(_rupee_safe(v), CELL)]
            for k, v in rows]
    table = Table(data, colWidths=widths, hAlign="LEFT")
    table.setStyle(PLAIN_TABLE_STYLE)
    return table


def _grid_table(header: list[str], rows: list[list[str]], widths) -> Table:
    data = [[Paragraph(_rupee_safe(h), CELL_BOLD) for h in header]]
    data += [[Paragraph(_rupee_safe(c), CELL) for c in row] for row in rows]
    table = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    table.setStyle(TABLE_STYLE)
    return table


def _schedule_story(bp: PolicyBlueprint) -> list:
    story: list = []
    story.append(Paragraph(bp.insurer_name.upper(), H1))
    story.append(Paragraph(f"{bp.plan_name}, {bp.policy_type} Policy", BODY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("<b>POLICY SCHEDULE</b>", CENTRE))
    story.append(Spacer(1, 3 * mm))

    story.append(_kv_table([
        ("Policy Number", bp.policy_number),
        ("UIN", bp.uin),
        ("Policyholder Name", bp.policyholder),
        ("Address", bp.address),
        ("Policy Period",
         f"From 00:00 hrs on {bp.start_date.strftime('%d/%m/%Y')} "
         f"to 23:59 hrs on {bp.end_date.strftime('%d/%m/%Y')}"),
        ("Date of Issue", bp.start_date.strftime("%d/%m/%Y")),
        ("Intermediary Code", bp.agent_code),
    ]))

    story.append(Paragraph("INSURED PERSONS", H2))
    # A floater states the one sum insured against the proposer's row and leaves
    # the rest blank, because the cover is shared rather than held per person.
    story.append(_grid_table(
        ["Sl.", "Name of Insured Person", "Age", "Relationship", "Sum Insured"],
        [
            [str(index), name, str(age), relationship,
             write_amount(bp.sum_insured, bp.amount_style) if index == 1
             else "Floater"]
            for index, (name, age, relationship) in enumerate(bp.members, start=1)
        ],
        (12 * mm, 62 * mm, 14 * mm, 30 * mm, 56 * mm),
    ))

    story.append(Paragraph("SCHEDULE OF BENEFITS", H2))
    benefit_rows = [
        ["Sum Insured (per policy year)", write_amount(bp.sum_insured, bp.amount_style)],
        ["Room Rent Limit", _room_limit_sentence(bp)],
        ["Intensive Care Unit (ICU) Limit", _icu_limit_sentence(bp)],
    ]
    if bp.deductible:
        benefit_rows.append(
            ["Deductible (aggregate, per policy year)",
             write_amount(bp.deductible, bp.amount_style)]
        )
    benefit_rows.append([
        "Co-payment",
        (
            f"{bp.copay_pct}% of each and every admissible claim"
            + (
                f" for Insured Persons aged {bp.copay_above_age} years and above"
                if bp.copay_above_age else ""
            )
        )
        if bp.copay_pct else "Nil",
    ])
    benefit_rows += [
        ["Day Care Treatments",
         "Covered as per the list of day care procedures in the Policy Wording"
         if bp.covers_daycare
         else "Not covered. Minimum 24 hours of hospitalisation required."],
        ["Pre-hospitalisation Expenses", f"{bp.pre_hosp_days} days prior to admission"],
        ["Post-hospitalisation Expenses", f"{bp.post_hosp_days} days from discharge"],
        ["Restoration of Sum Insured",
         "Available once per policy year" if bp.restore_benefit else "Not applicable"],
        ["Non-Medical Consumables",
         "Covered under Consumables Benefit" if bp.covers_consumables
         else "Not covered. Refer Annexure of non-payable items."],
        ["Cashless Facility", "Available at network hospitals"],
    ]
    story.append(_grid_table(
        ["Benefit", "Limit / Applicability"], benefit_rows, (58 * mm, 116 * mm)
    ))

    if bp.sublimits:
        story.append(Paragraph("SUB-LIMITS", H2))
        story.append(_grid_table(
            ["Benefit / Procedure", "Maximum Payable"],
            [[label, write_amount(amount, bp.amount_style)]
             for _, _, label, amount in bp.sublimits],
            (100 * mm, 74 * mm),
        ))

    # Premium block. Placed immediately after the cover figures on purpose:
    # these numbers are the most attractive wrong answers in the document.
    story.append(Paragraph("PREMIUM DETAILS", H2))
    story.append(_grid_table(
        ["Description", "Amount"],
        [
            ["Net Premium", format_inr(bp.premium)],
            ["GST @ 18%", format_inr(bp.gst)],
            ["Total Premium Paid", format_inr(bp.premium + bp.gst)],
        ],
        (100 * mm, 74 * mm),
    ))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "This Schedule is to be read together with the Policy Wording. In the "
        "event of any inconsistency between this Schedule and the Policy "
        "Wording, the particulars stated in this Schedule shall prevail.",
        JUSTIFIED,
    ))
    return story


def _wording_story(bp: PolicyBlueprint) -> list:
    story: list = [Paragraph(f"{bp.insurer_name.upper()}, POLICY WORDING", H1),
                   Paragraph(f"{bp.plan_name}", BODY), Spacer(1, 4 * mm)]

    story.append(Paragraph("1. DEFINITIONS", H2))
    definitions = [
        ("Sum Insured", "the maximum amount of cover available to the Insured "
                        "Person during a policy year, as stated in the Schedule."),
        ("Room Rent", "the amount charged by a Hospital towards accommodation "
                      "per day of admission, excluding Intensive Care Unit charges."),
        ("Network Hospital", "a Hospital which has entered into an agreement with "
                             "the Company for providing cashless treatment."),
        ("Co-payment", "a cost-sharing requirement under which the Insured Person "
                       "bears a specified percentage of the admissible claim amount."),
        ("Proportionate Deduction", "a pro-rata reduction applied to associated "
                                    "medical expenses where the Insured Person occupies "
                                    "a room category exceeding the eligible limit. "
                                    "Proportionate deduction shall not be applied to "
                                    "Intensive Care Unit charges, pharmacy, diagnostics, "
                                    "implants and consumables."),
    ]
    for term, meaning in definitions:
        story.append(Paragraph(f"<b>{term}</b> means {meaning}", JUSTIFIED))
        story.append(Spacer(1, 1.5 * mm))

    story.append(Paragraph("2. ROOM RENT AND ASSOCIATED EXPENSES", H2))
    if bp.contradicts_wording and bp.wording_room_flat:
        # A stale standard clause that the schedule overrides. Precedence must
        # settle this without the user being asked.
        story.append(Paragraph(
            f"Where the Insured Person is admitted to a room category for which "
            f"the rent exceeds {write_amount(bp.wording_room_flat, 'rs_grouped')} per "
            f"day, the Company shall reduce the associated medical expenses in the "
            f"proportion which the eligible room rent bears to the actual room rent "
            f"charged. Room rent entitlement under the standard plan is "
            f"{write_amount(bp.wording_room_flat, 'rs_grouped')} per day unless "
            f"otherwise specified in the Schedule.",
            JUSTIFIED,
        ))
    else:
        story.append(Paragraph(
            "Where the Insured Person is admitted to a room category for which the "
            "rent exceeds the eligible limit specified in the Schedule, the Company "
            "shall reduce the associated medical expenses in the proportion which "
            "the eligible room rent bears to the actual room rent charged.",
            JUSTIFIED,
        ))

    story.append(Paragraph("3. WAITING PERIODS", H2))
    story.append(_grid_table(
        ["Waiting Period", "Applicable To"],
        [
            [f"{days} days" if days else f"{months} months", applies]
            for months, days, applies in bp.waiting_periods
        ],
        (40 * mm, 134 * mm),
    ))

    story.append(Paragraph("4. PERMANENT EXCLUSIONS", H2))
    story.append(Paragraph(
        "The Company shall not be liable to make any payment in respect of:", BODY))
    story.append(Spacer(1, 1.5 * mm))
    for i, exclusion in enumerate(bp.exclusions, start=1):
        story.append(Paragraph(f"{chr(96 + i)}) {exclusion}", JUSTIFIED))
        story.append(Spacer(1, 1 * mm))

    story.append(Paragraph("5. CLAIM PROCEDURE", H2))
    story.append(Paragraph(
        f"For cashless treatment, the Insured Person shall obtain pre-authorisation "
        f"from the Company at least 48 hours prior to a planned admission, or within "
        f"24 hours of an emergency admission. For reimbursement claims, all original "
        f"documents shall be submitted within 30 days of discharge. Pre-hospitalisation "
        f"expenses incurred up to {bp.pre_hosp_days} days before admission and "
        f"post-hospitalisation expenses incurred up to {bp.post_hosp_days} days after "
        f"discharge are payable, subject to the claim being admitted.",
        JUSTIFIED,
    ))

    story.append(Paragraph("6. GENERAL CONDITIONS", H2))
    story.append(Paragraph(
        "This Policy is subject to the terms, conditions and exclusions contained "
        "herein and in the Schedule. The Policy shall be governed by and construed "
        "in accordance with the laws of India. Any dispute shall be subject to the "
        "exclusive jurisdiction of the courts in India.",
        JUSTIFIED,
    ))
    return story


def render_policy_pdf(bp: PolicyBlueprint, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=20 * mm,
        title=f"{bp.plan_name}, Policy {bp.policy_number}",
        author=bp.insurer_name,
        subject="Health Insurance Policy",
    )
    story = _schedule_story(bp)
    story.append(PageBreak())
    story.extend(_wording_story(bp))
    doc.build(story, onFirstPage=_footer(bp), onLaterPages=_footer(bp))
    return path


def render_card_pdf(bp: PolicyBlueprint, path: Path) -> Path:
    """A one-page health card, the thing people photograph most often."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=25 * mm, bottomMargin=25 * mm,
    )
    story = [
        Paragraph(bp.insurer_name.upper(), H1),
        Paragraph("HEALTH INSURANCE IDENTITY CARD", BODY),
        Spacer(1, 6 * mm),
        _kv_table([
            ("Member Name", bp.policyholder),
            ("Policy Number", bp.policy_number),
            ("Sum Insured", write_amount(bp.sum_insured, bp.amount_style)),
            ("Room Entitlement", _room_limit_sentence(bp)),
            ("Valid Upto", bp.end_date.strftime("%d/%m/%Y")),
            ("Plan", bp.plan_name),
        ]),
        Spacer(1, 4 * mm),
        Paragraph(
            "Present this card at the hospital insurance desk for cashless "
            "treatment. This card is not a proof of coverage on its own.",
            BODY,
        ),
    ]
    doc.build(story, onFirstPage=_footer(bp), onLaterPages=_footer(bp))
    return path


# --- hospital bills ---------------------------------------------------------


BILL_TITLE = ParagraphStyle(
    "billtitle", parent=BODY, fontName=FONT_BOLD, fontSize=14, leading=17,
    alignment=1, spaceAfter=1,
)
BILL_HEADING = ParagraphStyle(
    "billheading", parent=BODY, fontName=FONT_BOLD, fontSize=11, leading=14,
    alignment=1, spaceBefore=6, spaceAfter=2,
)


def _bill_footer(bp):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 7)
        canvas.setFillColor(RULE)
        canvas.drawString(
            18 * mm, 11 * mm,
            "Computer generated bill. Subject to verification by the billing department.",
        )
        canvas.drawRightString(
            A4[0] - 18 * mm, 11 * mm, f"Bill No. {bp.bill_number}  |  Page {doc.page}"
        )
        canvas.restoreState()

    return draw


def _bill_story(bp) -> list:
    """A final bill as an Indian hospital prints one: header, then a priced table."""
    from app.schemas.money import format_inr

    story: list = [
        Paragraph(bp.hospital_name.upper(), BILL_TITLE),
        Paragraph(f"{bp.city} · Inpatient Billing Department", CENTRE),
        Spacer(1, 4),
        Paragraph("FINAL BILL", BILL_HEADING),
        Spacer(1, 4),
    ]

    story.append(_kv_table([
        ("Patient Name", bp.patient_name),
        ("UHID", bp.uhid),
        ("Bill No.", bp.bill_number),
        ("Bill Date", f"{bp.discharged:%d/%m/%Y}"),
        ("Date of Admission", f"{bp.admitted:%d/%m/%Y}"),
        ("Date of Discharge", f"{bp.discharged:%d/%m/%Y}"),
        ("Treatment", bp.procedure_name),
        ("Room Category", f"{bp.room_label} at {format_inr(bp.room_rate)} per day"),
    ]))
    story.append(Spacer(1, 8))

    widths = (12 * mm, 82 * mm, 16 * mm, 26 * mm, 28 * mm)
    rows: list[list[str]] = []
    serial = 0
    for section in bp.sections:
        rows.append(["", section.title, "", "", ""])
        for line in section.lines:
            serial += 1
            rows.append([
                str(serial),
                line.description,
                f"{line.qty:g}" if line.qty is not None else "",
                format_inr(line.rate) if line.rate is not None else "",
                format_inr(line.amount),
            ])

    story.append(_grid_table(
        ["Sr", "Particulars", "Qty", "Rate", "Amount"], rows, widths
    ))
    story.append(Spacer(1, 6))

    totals = [("Gross Total", format_inr(bp.stated_gross))]
    if bp.discount > 0:
        totals.append(("Less: Discount", format_inr(bp.discount)))
    if bp.advance_paid > 0:
        totals.append(("Less: Advance Paid", format_inr(bp.advance_paid)))
    totals.append(("Net Payable", format_inr(bp.net_payable)))
    story.append(_kv_table(totals, widths=(58 * mm, 40 * mm)))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Items marked as non-payable under the IRDAI schedule are recoverable "
        "from the patient. Original bills once issued will not be reprinted.",
        BODY,
    ))
    return story


def render_bill_pdf(bp, path: Path) -> Path:
    """Render one bill blueprint into a printable document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"Final bill {bp.bill_number}", author=bp.hospital_name,
    )
    doc.build(
        _bill_story(bp), onFirstPage=_bill_footer(bp), onLaterPages=_bill_footer(bp)
    )
    return path
