"""What people actually call these treatments.

A dropdown of 126 clinical names assumes the person searching already knows the
clinical name. They do not: they were handed a chit an hour ago and told their
father needs "a stent". They will type "heart blockage", "stone operation",
"delivery", "gall bladder".

Two lists, deliberately, because they are worth different amounts.

`SYNONYMS` maps one catalogue code to the words that mean *that treatment*.
Someone typing "piles" means haemorrhoidectomy and nothing else, so these rank
above a loose match on a clinical name.

`SPECIALTY_TERMS` maps a code prefix to words that only narrow the field:
"heart", "bone", "kidney". These rank *below* a name match, because a single
list mixing the two put "delivery" on every obstetrics row and answered a
search for it with an ovarian cystectomy.

Search only. Nothing here renames a procedure, reclassifies it, or picks one on
the user's behalf; it decides which rows are offered, and the user still
chooses. Kept in the generator rather than the interface so anything that has
to interpret free text later, including reading a doctor's note, has the same
list.
"""

from __future__ import annotations

# Precise: these words mean this specific treatment.
SYNONYMS: dict[str, list[str]] = {
    # Cardiology
    "CP-CARD-001": ["angiogram", "angio", "dye test", "heart test"],
    "CP-CARD-002": ["stent", "ptca", "heart blockage", "angioplasty", "balloon",
                    "single stent", "one stent", "block in heart"],
    "CP-CARD-003": ["two stents", "double stent", "multiple stents"],
    "CP-CARD-004": ["bypass", "cabg", "open heart surgery", "heart bypass"],
    "CP-CARD-005": ["pacemaker", "heart battery"],
    "CP-CARD-006": ["valve replacement", "valve surgery", "heart valve"],
    "CP-CARD-007": ["heart attack", "mi", "cardiac arrest"],
    "CP-CARD-008": ["heart failure", "weak heart", "water in lungs"],
    "CP-CARD-009": ["ablation", "irregular heartbeat", "palpitations"],
    "CP-CARD-010": ["hole in heart", "asd closure"],

    # General surgery
    "CP-GSUR-001": ["appendix", "appendix operation", "keyhole appendix"],
    "CP-GSUR-002": ["appendix", "appendix operation"],
    "CP-GSUR-003": ["gall bladder", "gallbladder", "gall stone", "gallstone"],
    "CP-GSUR-004": ["hernia", "groin hernia"],
    "CP-GSUR-005": ["hernia", "navel hernia"],
    "CP-GSUR-006": ["piles", "haemorrhoids", "hemorrhoids"],
    "CP-GSUR-007": ["fissure"],
    "CP-GSUR-008": ["thyroid operation", "thyroid removal", "goitre"],

    # Orthopaedics
    "CP-ORTH-001": ["knee replacement", "new knee", "knee operation"],
    "CP-ORTH-002": ["both knees", "knee replacement"],
    "CP-ORTH-003": ["hip replacement", "new hip"],
    "CP-ORTH-004": ["acl", "ligament tear", "knee ligament"],
    "CP-ORTH-006": ["thigh fracture", "broken leg", "femur break"],
    "CP-ORTH-007": ["leg fracture", "broken leg", "shin break"],
    "CP-ORTH-008": ["spine surgery", "back surgery", "spinal fusion"],
    "CP-ORTH-009": ["slip disc", "slipped disc", "disc operation", "back pain surgery"],
    "CP-ORTH-010": ["shoulder tear", "rotator cuff"],
    "CP-ORTH-012": ["wrist fracture", "broken wrist", "broken hand"],
    "CP-ORTH-014": ["hip fracture", "broken hip"],

    # Obstetrics and gynaecology
    "CP-OBGY-001": ["delivery", "normal delivery", "childbirth", "baby born"],
    "CP-OBGY-002": ["caesarean", "c section", "csection", "cesarean", "operation delivery"],
    "CP-OBGY-003": ["hysterectomy", "uterus removal"],
    "CP-OBGY-004": ["hysterectomy", "uterus removal", "keyhole hysterectomy"],
    "CP-OBGY-005": ["ovarian cyst", "cyst removal"],
    "CP-OBGY-006": ["fibroid", "fibroid removal"],
    "CP-OBGY-008": ["ectopic", "tubal pregnancy"],
    "CP-OBGY-009": ["high risk pregnancy", "pregnancy complication"],

    # Ophthalmology
    "CP-OPHT-001": ["cataract", "cataract operation", "eye lens", "white in eye"],
    "CP-OPHT-002": ["cataract", "cataract operation", "premium lens"],
    "CP-OPHT-004": ["retina detachment", "retina surgery"],
    "CP-OPHT-005": ["glaucoma", "eye pressure"],

    # Kidney and urology
    "CP-NEPH-": ["kidney", "dialysis", "renal"],
    "CP-UROL-001": ["kidney stone", "stone operation", "stone removal", "ureteroscopy"],
    "CP-UROL-002": ["kidney stone", "big stone", "pcnl"],
    "CP-UROL-003": ["prostate", "prostate operation", "turp", "urine problem"],
    "CP-UROL-004": ["stone breaking", "lithotripsy", "laser for stone"],

    # Neurology
    "CP-NEUR-001": ["stroke", "paralysis", "brain stroke"],
    "CP-NEUR-002": ["stroke", "clot buster", "thrombolysis"],
    "CP-NEUR-003": ["fits", "seizure", "epilepsy"],
    "CP-NEUR-004": ["brain tumour", "brain tumor", "brain surgery"],
    "CP-NEUR-006": ["head injury", "brain bleed", "clot in brain"],
    "CP-NEUR-008": ["meningitis", "brain fever"],

    # General medicine
    "CP-MEDI-001": ["dengue", "platelet drop"],
    "CP-MEDI-002": ["dengue", "severe dengue"],
    "CP-MEDI-003": ["typhoid"],
    "CP-MEDI-004": ["malaria"],
    "CP-MEDI-005": ["sepsis", "blood infection"],
    "CP-MEDI-006": ["sugar", "diabetes", "high sugar", "dka"],
    "CP-MEDI-007": ["bp", "blood pressure", "high bp"],
    "CP-MEDI-008": ["loose motion", "vomiting", "dehydration", "food poisoning"],
    "CP-MEDI-009": ["anaemia", "anemia", "low blood", "blood transfusion"],
    "CP-MEDI-010": ["snake bite"],
    "CP-MEDI-011": ["thyroid"],
    "CP-MEDI-012": ["covid", "corona"],

    # Oncology
    "CP-ONCO-": ["cancer", "chemotherapy", "chemo", "tumour", "tumor"],

    # Gastroenterology
    "CP-GAST-": ["stomach", "liver", "intestine", "endoscopy"],

    # Pulmonology
    "CP-PULM-": ["lungs", "breathing", "asthma", "tb", "pneumonia"],

    # ENT
    "CP-ENT-": ["ear", "nose", "throat", "tonsils", "sinus"],

    # Emergency
    "CP-EMER-": ["emergency", "accident", "casualty"],
}


# Broad: these words narrow the field but do not name a treatment. Scored below
# a name match, so "bone" offers the orthopaedic rows without claiming any one
# of them is what the user meant.
SPECIALTY_TERMS: dict[str, list[str]] = {
    "CP-CARD-": ["heart", "cardiac", "chest pain"],
    "CP-GSUR-": ["operation", "surgery"],
    "CP-ORTH-": ["bone", "fracture", "joint", "ortho", "orthopaedic", "broken"],
    "CP-OBGY-": ["pregnancy", "maternity", "baby", "womb", "gynaec"],
    "CP-OPHT-": ["eye", "vision", "sight"],
    "CP-NEPH-": ["kidney", "renal"],
    "CP-UROL-": ["urine", "bladder", "stone"],
    "CP-NEUR-": ["brain", "nerve", "neuro"],
    "CP-MEDI-": ["fever", "infection", "medical admission"],
    "CP-ONCO-": ["cancer"],
    "CP-GAST-": ["stomach", "digestion"],
    "CP-PULM-": ["lung", "breathing", "chest"],
    "CP-PAED-": ["child", "baby", "kids", "paediatric"],
    "CP-ENT-": ["ear", "nose", "throat"],
    "CP-DERM-": ["skin"],
    "CP-PSYC-": ["mental health", "depression"],
    "CP-PLAS-": ["reconstruction", "burns", "skin graft"],
    "CP-EMER-": ["emergency", "accident"],
}


def _matching(table: dict[str, list[str]], code: str) -> list[str]:
    found: list[str] = []
    for key, words in table.items():
        if key == code or (key.endswith("-") and code.startswith(key)):
            found.extend(words)

    seen: set[str] = set()
    unique = []
    for word in found:
        if word not in seen:
            seen.add(word)
            unique.append(word)
    return unique


def synonyms_for(code: str) -> list[str]:
    """Words that mean this specific treatment."""
    return _matching(SYNONYMS, code)


def specialty_terms_for(code: str) -> list[str]:
    """Words that only narrow the field this treatment belongs to."""
    return _matching(SPECIALTY_TERMS, code)