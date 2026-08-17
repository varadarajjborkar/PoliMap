# CoverPath

**Insurance-aware hospital decision support for patients and caregivers in India.**

Built for *Precision Care Challenge 2026, "Hospitality: Holistic Optimization
System for Policy-Integrated Admission & Treatment Intelligence."*

---

## The problem, and the gap

Most people in India hold at least one health cover, private, employer, or a
government scheme like PM-JAY, ESI, Arogya Karnataka or Yeshaswini. During an
admission, nobody can answer the questions that actually matter in time: *which
hospitals am I covered at, what room am I entitled to, what will I have to pay
myself?* The policy, the hospital's tariff and the treatment plan live in three
separate places, and the person holding the policy is the patient.

A system that stops at "extract the fields, filter the hospitals, show a list"
answers *where can I go*. It does not answer **what will this cost me**, which is
the question that causes the financial stress. CoverPath answers that one, in
rupees, with the reasoning shown.

## What makes it different

### The proportionate deduction, modelled correctly

Take a room above your eligible category in India and you do not merely pay the
difference in room rent. Your insurer reduces its payout on everything priced by
room tier, surgeon, theatre, nursing. Almost nobody knows this before they are
handed the bill.

The IRDAI master circular of May 2024 narrowed that reduction so it no longer
touches ICU, pharmacy, diagnostics, implants or consumables. Modelling that
boundary is not a detail:

> ₹5 lakh cover, ₹5,000/day room limit, patient takes an ₹8,000/day room on a
> ₹2,00,000 bill. Ratio 62.5%.
>
> | | Insurer pays | Patient pays |
> |---|---:|---:|
> | Naive whole-bill formula | ₹1,25,000 | ₹75,000 |
> | **Correct, post-2024** | **₹1,43,750** | **₹56,250** |

₹18,750 of difference, from one boundary. Both regimes are implemented so the
two can be compared rather than asserted.

### Extraction that cannot invent a number

A clause is admissible only if the text it claims to quote can be found in the
page it claims to come from. This is enforced in code, not requested in a
prompt. Matching tolerates OCR damage, folding `O`/`0`, `S`/`5`, while
requiring that a quote's *digits* genuinely appear in the source, because a
misread letter is harmless and an invented figure is not.

### An adversarial verification loop, because the measurement demanded one

Adding a language model to extraction halved the missed fields and **tripled the
confidently wrong ones**. Wrong values are the dangerous failure: nothing
prompts anyone to check them. So the model's output is attacked before it is
believed, most sharply by re-parsing each clause's own quote and confirming it
still yields the value reported.

Measured across 158 fields, 10 policies, 6 document conditions:

| Configuration | Accuracy | **Wrong values** | Missing |
|---|---:|---:|---:|
| Rules only | 93.4% | 2 | 10 |
| Rules + model | 93.0% | 6 | 5 |
| Rules + verification | 94.3% | 1 | 8 |
| **Rules + model + verification** | **94.9%** | **3** | **5** |

Verification is what makes the model layer safe to use: it keeps the recall gain
and halves the wrong values the model introduced. Whatever it cannot settle
becomes a plain-language question rather than a silent guess.

### It never returns an empty page

Every hospital that fails a filter records *why*. When nothing matches,
constraints are relaxed in a stated order, cheapest sacrifice first, and each
relaxation is labelled with its consequence. Travelling further is an
inconvenience; leaving your cashless network means funding the whole bill
upfront, so those are not surrendered in the same breath.

---

## Running it

**One-time setup**

```bash
brew install tesseract              # OCR engine (apt: tesseract-ocr)

python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

cp backend/.env.example backend/.env    # then paste your OLLAMA_API_KEY into it

.venv/bin/python -m datagen.build_all   # builds the corpus, ~2 minutes
```

**Run it, two terminals**

```bash
# Terminal 1, API
cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload --port 8000

# Terminal 2, web interface
cd frontend && npm install && npm run dev
```

Then open **http://localhost:5173**.

Upload any policy from `data/generated/policies/`, try `clean/POL001.pdf` for
the clean path, or `scanned/POL003_phone_photo.pdf` to watch the OCR ladder and
vision escalation work on a photographed document.

**Verifying it**

```bash
cd backend && ../.venv/bin/python -m pytest -q     # 337 tests

.venv/bin/python -m bench.ocr_bench                # intake quality by condition
.venv/bin/python -m bench.extract_bench            # extraction accuracy
.venv/bin/python -m bench.extract_bench --no-model # ablation: rules only
.venv/bin/python -m bench.extract_bench --no-verify # ablation: no verification
```

`curl localhost:8000/api/health/providers` shows which model is serving each
role on your account.

---

## The pipeline

```
S0 INTAKE     document → pages of text, with word boxes and confidence
S1 TRIAGE     which page is the schedule, which is generic wording
S2 ATOMIZE    text → clause ledger  (grammar ∥ model, both evidence-grounded)
S3 CHALLENGE  attack every clause; settle by rule, then model, then ask
S4 COMPILE    surviving ledger → one executable policy
S5 MATCH      policy × context × 580 hospitals → candidates (+ why each failed)
S6 SIMULATE   itemised bill → deduction waterfall → rupees you pay
S7 RANK       Pareto frontier → preference-ranked, explained, with alternatives
JOURNEY       re-answers all of it at each care stage against real accrued cost
```

Every step emits a `PipelineEvent` written to the server log *and* streamed to
the browser's activity panel, so what the user sees cannot drift from what the
server did.

**Intake ladder**, cheapest rung first: native text layer → Tesseract → vision
model → ask the user. Preprocessing branches on measured page condition,
speckle detection picks a median filter over non-local means, lighting is
flattened only when a shadow is actually present, and capture DPI is inferred
from page dimensions. Field recall across the corpus: **94.3%**, from 81.3%
before those fixes.

## The data

Synthetic, per the problem statement's mandate, but generated from real anchors.

| | | |
|---|---:|---|
| Procedures | 126 | CGHS-anchored package rates, NABH vs non-NABH |
| Hospitals | 580 | Bengaluru 250, Delhi NCR 120, Mumbai 120, Hyderabad 90 |
| Insurers | 18 | 10 invented companies + 8 government schemes |
| Policies | 40 | rendered as 104 documents, each with ground truth |

Hospital attributes are *correlated*, not drawn independently: size drives
accreditation odds and specialty breadth, locality drives tariffs, and both
drive how many insurers sign a cashless tie-up. That is what gives matching real
trade-offs, the cheap hospital genuinely tends to be the one outside your
network without an ICU, which is the decision a family actually faces.

The policy corpus is adversarial by design. The same room limit appears as a
flat amount, a percentage of cover, a percentage capped by a maximum, a room
category with no figure, and as no limit at all. Amounts are written as
`Rs. 5,00,000`, `INR 5,00,000`, `₹5,00,000` and `5.00 Lakhs`. Premium and GST sit
directly below the sum insured, because grabbing the premium is the commonest
extraction error. Three policies contradict themselves between schedule and
wording. 52% of documents carry no text layer at all.

Insurer names are invented. Attaching fabricated networks and tariffs to real
companies would be misleading.

## Scope

This is a decision-support and information tool. It does not diagnose, does not
recommend treatment, and does not give binding insurance advice. Journey stages
are administrative, where the paperwork stands, and nothing in the system
records or reasons about a diagnosis. Every figure is an estimate and is
labelled as one.

## Layout

```
backend/app/
  pipeline/     s0_intake … s7_rank, plus run.py for the whole chain
  agents/       provider-agnostic model layer with role-based fallback chains
  schemas/      the domain contracts
  journey/      care journey tracking
  core/         config, telemetry bus, guardrails
  api/          HTTP surface and the SSE activity stream
datagen/        corpus builders
bench/          OCR and extraction benchmarks
frontend/       React + Vite + Tailwind
```

Models are addressed by *role*, extract, challenge, adjudicate, vision, narrate
never by name. Each role has a fallback chain probed at boot, so a plan
change or a deprecated model degrades gracefully instead of breaking. With no
key at all the application still runs, on the deterministic path only, and says
so.