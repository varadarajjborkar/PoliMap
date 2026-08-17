"""Treatment package catalogue, anchored on CGHS published rates.

Base rates are non-NABH figures in the CGHS band for each procedure; NABH rates
are derived at a 15% premium, matching the spread CGHS publishes between the two
tiers on comparable line items.

Two structural details from CGHS practice are modelled deliberately:

* Implants, stents, intraocular lenses, meshes, valves, are reimbursed
  *separately* from the package rate, at ceiling prices. They therefore appear
  as their own expense head with real weight, which matters because implants are
  exempt from proportionate deduction under the post-2024 rules. A patient in an
  over-limit room keeps full implant cover, and the system should show that.

* Length of stay carries variability rather than a single figure, so cost
  estimates can be presented as a band instead of a falsely precise number.
"""

from __future__ import annotations

from decimal import Decimal

from app.schemas.money import round_inr
from app.schemas.policy import ExpenseHead as H
from app.schemas.procedure import CostSplit, Procedure
from app.schemas.procedure import Specialty as S
from datagen.synonyms import specialty_terms_for, synonyms_for

NABH_PREMIUM = Decimal("1.15")

# How a package total divides across bill heads, by shape of treatment.
ARCHETYPES: dict[str, dict[H, float]] = {
    "major_surgery_implant": {
        H.ROOM_RENT: 0.08, H.NURSING: 0.04, H.SURGEON_FEE: 0.14,
        H.ANAESTHETIST_FEE: 0.05, H.OT_CHARGES: 0.09, H.ICU_CHARGES: 0.05,
        H.INVESTIGATIONS: 0.07, H.PHARMACY: 0.10, H.CONSUMABLES: 0.06,
        H.IMPLANTS: 0.30, H.NON_MEDICAL: 0.02,
    },
    "major_surgery": {
        H.ROOM_RENT: 0.12, H.NURSING: 0.06, H.SURGEON_FEE: 0.20,
        H.ANAESTHETIST_FEE: 0.07, H.OT_CHARGES: 0.13, H.ICU_CHARGES: 0.07,
        H.INVESTIGATIONS: 0.10, H.PHARMACY: 0.14, H.CONSUMABLES: 0.08,
        H.NON_MEDICAL: 0.03,
    },
    "minor_surgery": {
        H.ROOM_RENT: 0.15, H.NURSING: 0.06, H.SURGEON_FEE: 0.22,
        H.ANAESTHETIST_FEE: 0.07, H.OT_CHARGES: 0.12, H.INVESTIGATIONS: 0.11,
        H.PHARMACY: 0.15, H.CONSUMABLES: 0.09, H.NON_MEDICAL: 0.03,
    },
    "daycare_surgery": {
        H.ROOM_RENT: 0.07, H.NURSING: 0.05, H.SURGEON_FEE: 0.30,
        H.ANAESTHETIST_FEE: 0.07, H.OT_CHARGES: 0.15, H.INVESTIGATIONS: 0.11,
        H.PHARMACY: 0.13, H.CONSUMABLES: 0.09, H.NON_MEDICAL: 0.03,
    },
    "daycare_implant": {
        H.ROOM_RENT: 0.05, H.NURSING: 0.03, H.SURGEON_FEE: 0.24,
        H.ANAESTHETIST_FEE: 0.05, H.OT_CHARGES: 0.12, H.INVESTIGATIONS: 0.08,
        H.PHARMACY: 0.09, H.CONSUMABLES: 0.07, H.IMPLANTS: 0.24,
        H.NON_MEDICAL: 0.03,
    },
    "medical_admission": {
        H.ROOM_RENT: 0.28, H.NURSING: 0.10, H.DOCTOR_VISIT: 0.12,
        H.INVESTIGATIONS: 0.22, H.PHARMACY: 0.20, H.CONSUMABLES: 0.05,
        H.NON_MEDICAL: 0.03,
    },
    "icu_medical": {
        H.ROOM_RENT: 0.06, H.ICU_CHARGES: 0.30, H.NURSING: 0.08,
        H.DOCTOR_VISIT: 0.09, H.INVESTIGATIONS: 0.18, H.PHARMACY: 0.20,
        H.CONSUMABLES: 0.06, H.OXYGEN: 0.02, H.NON_MEDICAL: 0.01,
    },
    "maternity": {
        H.ROOM_RENT: 0.20, H.NURSING: 0.08, H.SURGEON_FEE: 0.18,
        H.ANAESTHETIST_FEE: 0.06, H.OT_CHARGES: 0.12, H.INVESTIGATIONS: 0.12,
        H.PHARMACY: 0.14, H.CONSUMABLES: 0.07, H.NON_MEDICAL: 0.03,
    },
    "diagnostic_procedure": {
        H.ROOM_RENT: 0.08, H.NURSING: 0.04, H.DOCTOR_VISIT: 0.06,
        H.OT_CHARGES: 0.14, H.INVESTIGATIONS: 0.42, H.PHARMACY: 0.10,
        H.CONSUMABLES: 0.13, H.NON_MEDICAL: 0.03,
    },
    "cyclic_therapy": {
        H.ROOM_RENT: 0.10, H.NURSING: 0.10, H.DOCTOR_VISIT: 0.08,
        H.INVESTIGATIONS: 0.14, H.PHARMACY: 0.48, H.CONSUMABLES: 0.08,
        H.NON_MEDICAL: 0.02,
    },
}

# code, name, specialty, archetype, non-NABH base rate, LOS days, ICU days
SPECS: list[tuple[str, str, S, str, int, float, float]] = [
    # --- cardiology -------------------------------------------------------
    ("CP-CARD-001", "Coronary angiography", S.CARDIOLOGY, "diagnostic_procedure", 18000, 1, 0),
    ("CP-CARD-002", "Angioplasty with single stent", S.CARDIOLOGY, "major_surgery_implant", 165000, 3, 1),
    ("CP-CARD-003", "Angioplasty with two stents", S.CARDIOLOGY, "major_surgery_implant", 245000, 3, 1),
    ("CP-CARD-004", "Coronary artery bypass graft", S.CARDIOTHORACIC_SURGERY, "major_surgery", 225000, 8, 3),
    ("CP-CARD-005", "Permanent pacemaker implantation", S.CARDIOLOGY, "major_surgery_implant", 195000, 3, 1),
    ("CP-CARD-006", "Heart valve replacement", S.CARDIOTHORACIC_SURGERY, "major_surgery_implant", 275000, 10, 4),
    ("CP-CARD-007", "Acute myocardial infarction management", S.CARDIOLOGY, "icu_medical", 95000, 5, 2),
    ("CP-CARD-008", "Congestive heart failure management", S.CARDIOLOGY, "icu_medical", 65000, 6, 2),
    ("CP-CARD-009", "Radiofrequency ablation for arrhythmia", S.CARDIOLOGY, "major_surgery", 185000, 3, 1),
    ("CP-CARD-010", "Atrial septal defect closure", S.CARDIOLOGY, "major_surgery_implant", 165000, 5, 2),
    ("CP-CARD-011", "Holter and stress evaluation admission", S.CARDIOLOGY, "diagnostic_procedure", 14000, 1, 0),
    ("CP-CARD-012", "Cardiac catheterisation, paediatric", S.CARDIOLOGY, "diagnostic_procedure", 32000, 2, 0),
    # --- general surgery --------------------------------------------------
    ("CP-GSUR-001", "Laparoscopic appendectomy", S.GENERAL_SURGERY, "minor_surgery", 28000, 3, 0),
    ("CP-GSUR-002", "Open appendectomy", S.GENERAL_SURGERY, "minor_surgery", 24000, 4, 0),
    ("CP-GSUR-003", "Laparoscopic cholecystectomy", S.GENERAL_SURGERY, "minor_surgery", 45000, 3, 0),
    ("CP-GSUR-004", "Inguinal hernia repair with mesh", S.GENERAL_SURGERY, "minor_surgery", 24000, 2, 0),
    ("CP-GSUR-005", "Umbilical hernia repair", S.GENERAL_SURGERY, "minor_surgery", 22000, 2, 0),
    ("CP-GSUR-006", "Haemorrhoidectomy", S.GENERAL_SURGERY, "daycare_surgery", 18000, 1, 0),
    ("CP-GSUR-007", "Fissurectomy", S.GENERAL_SURGERY, "daycare_surgery", 15000, 1, 0),
    ("CP-GSUR-008", "Thyroidectomy", S.GENERAL_SURGERY, "major_surgery", 62000, 4, 0),
    ("CP-GSUR-009", "Mastectomy", S.GENERAL_SURGERY, "major_surgery", 78000, 5, 0),
    ("CP-GSUR-010", "Bowel resection", S.GENERAL_SURGERY, "major_surgery", 135000, 8, 2),
    ("CP-GSUR-011", "Varicose vein surgery", S.GENERAL_SURGERY, "minor_surgery", 42000, 2, 0),
    ("CP-GSUR-012", "Incision and drainage of abscess", S.GENERAL_SURGERY, "daycare_surgery", 9000, 1, 0),
    ("CP-GSUR-013", "Laparotomy for perforation", S.GENERAL_SURGERY, "major_surgery", 118000, 9, 3),
    ("CP-GSUR-014", "Pilonidal sinus excision", S.GENERAL_SURGERY, "daycare_surgery", 21000, 1, 0),
    # --- orthopaedics -----------------------------------------------------
    ("CP-ORTH-001", "Total knee replacement, single", S.ORTHOPAEDICS, "major_surgery_implant", 152000, 6, 0),
    ("CP-ORTH-002", "Total knee replacement, bilateral", S.ORTHOPAEDICS, "major_surgery_implant", 275000, 8, 1),
    ("CP-ORTH-003", "Total hip replacement", S.ORTHOPAEDICS, "major_surgery_implant", 165000, 7, 0),
    ("CP-ORTH-004", "Arthroscopic ACL reconstruction", S.ORTHOPAEDICS, "major_surgery_implant", 92000, 3, 0),
    ("CP-ORTH-005", "Knee arthroscopy, diagnostic", S.ORTHOPAEDICS, "daycare_surgery", 48000, 1, 0),
    ("CP-ORTH-006", "Femur fracture fixation", S.ORTHOPAEDICS, "major_surgery_implant", 88000, 5, 0),
    ("CP-ORTH-007", "Tibia fracture fixation", S.ORTHOPAEDICS, "major_surgery_implant", 72000, 4, 0),
    ("CP-ORTH-008", "Spinal fusion, single level", S.ORTHOPAEDICS, "major_surgery_implant", 195000, 6, 1),
    ("CP-ORTH-009", "Lumbar discectomy", S.ORTHOPAEDICS, "major_surgery", 96000, 4, 0),
    ("CP-ORTH-010", "Shoulder rotator cuff repair", S.ORTHOPAEDICS, "major_surgery_implant", 85000, 3, 0),
    ("CP-ORTH-011", "Carpal tunnel release", S.ORTHOPAEDICS, "daycare_surgery", 24000, 1, 0),
    ("CP-ORTH-012", "Colles fracture reduction", S.ORTHOPAEDICS, "daycare_surgery", 16000, 1, 0),
    ("CP-ORTH-013", "Implant removal", S.ORTHOPAEDICS, "daycare_surgery", 22000, 1, 0),
    ("CP-ORTH-014", "Hip fracture hemiarthroplasty", S.ORTHOPAEDICS, "major_surgery_implant", 128000, 6, 0),
    # --- ophthalmology ----------------------------------------------------
    ("CP-OPHT-001", "Cataract surgery with monofocal lens", S.OPHTHALMOLOGY, "daycare_implant", 16000, 1, 0),
    ("CP-OPHT-002", "Cataract surgery with multifocal lens", S.OPHTHALMOLOGY, "daycare_implant", 42000, 1, 0),
    ("CP-OPHT-003", "Vitrectomy", S.OPHTHALMOLOGY, "daycare_surgery", 58000, 1, 0),
    ("CP-OPHT-004", "Retinal detachment repair", S.OPHTHALMOLOGY, "major_surgery", 72000, 2, 0),
    ("CP-OPHT-005", "Glaucoma trabeculectomy", S.OPHTHALMOLOGY, "daycare_surgery", 32000, 1, 0),
    ("CP-OPHT-006", "Intravitreal injection", S.OPHTHALMOLOGY, "daycare_surgery", 22000, 1, 0),
    ("CP-OPHT-007", "Pterygium excision", S.OPHTHALMOLOGY, "daycare_surgery", 14000, 1, 0),
    # --- obstetrics and gynaecology --------------------------------------
    ("CP-OBGY-001", "Normal delivery", S.OBSTETRICS_GYNAECOLOGY, "maternity", 32000, 3, 0),
    ("CP-OBGY-002", "Caesarean section", S.OBSTETRICS_GYNAECOLOGY, "maternity", 53000, 4, 0),
    ("CP-OBGY-003", "Abdominal hysterectomy", S.OBSTETRICS_GYNAECOLOGY, "major_surgery", 58000, 5, 0),
    ("CP-OBGY-004", "Laparoscopic hysterectomy", S.OBSTETRICS_GYNAECOLOGY, "major_surgery", 78000, 3, 0),
    ("CP-OBGY-005", "Ovarian cystectomy", S.OBSTETRICS_GYNAECOLOGY, "minor_surgery", 42000, 3, 0),
    ("CP-OBGY-006", "Myomectomy", S.OBSTETRICS_GYNAECOLOGY, "major_surgery", 62000, 4, 0),
    ("CP-OBGY-007", "Dilatation and curettage", S.OBSTETRICS_GYNAECOLOGY, "daycare_surgery", 14000, 1, 0),
    ("CP-OBGY-008", "Ectopic pregnancy surgery", S.OBSTETRICS_GYNAECOLOGY, "minor_surgery", 48000, 3, 0),
    ("CP-OBGY-009", "High-risk pregnancy management", S.OBSTETRICS_GYNAECOLOGY, "medical_admission", 45000, 5, 0),
    # --- neurology and neurosurgery --------------------------------------
    ("CP-NEUR-001", "Acute stroke management", S.NEUROLOGY, "icu_medical", 125000, 7, 3),
    ("CP-NEUR-002", "Stroke thrombolysis", S.NEUROLOGY, "icu_medical", 185000, 7, 3),
    ("CP-NEUR-003", "Epilepsy evaluation admission", S.NEUROLOGY, "medical_admission", 42000, 4, 0),
    ("CP-NEUR-004", "Craniotomy for tumour", S.NEUROSURGERY, "major_surgery", 285000, 10, 4),
    ("CP-NEUR-005", "Ventriculoperitoneal shunt", S.NEUROSURGERY, "major_surgery_implant", 145000, 6, 2),
    ("CP-NEUR-006", "Subdural haematoma evacuation", S.NEUROSURGERY, "major_surgery", 165000, 8, 3),
    ("CP-NEUR-007", "Guillain-Barre syndrome management", S.NEUROLOGY, "icu_medical", 195000, 12, 6),
    ("CP-NEUR-008", "Meningitis management", S.NEUROLOGY, "icu_medical", 88000, 8, 3),
    # --- oncology ---------------------------------------------------------
    ("CP-ONCO-001", "Chemotherapy cycle, standard", S.ONCOLOGY, "cyclic_therapy", 32000, 2, 0),
    ("CP-ONCO-002", "Chemotherapy cycle, high cost regimen", S.ONCOLOGY, "cyclic_therapy", 125000, 2, 0),
    ("CP-ONCO-003", "Radiotherapy, full course", S.ONCOLOGY, "cyclic_therapy", 165000, 3, 0),
    ("CP-ONCO-004", "Tumour excision, soft tissue", S.ONCOLOGY, "major_surgery", 95000, 5, 1),
    ("CP-ONCO-005", "Radical nephrectomy", S.ONCOLOGY, "major_surgery", 175000, 7, 2),
    ("CP-ONCO-006", "Bone marrow biopsy", S.ONCOLOGY, "daycare_surgery", 12000, 1, 0),
    ("CP-ONCO-007", "Immunotherapy cycle", S.ONCOLOGY, "cyclic_therapy", 185000, 2, 0),
    ("CP-ONCO-008", "Palliative care admission", S.ONCOLOGY, "medical_admission", 38000, 6, 0),
    # --- nephrology and urology ------------------------------------------
    ("CP-NEPH-001", "Haemodialysis session", S.NEPHROLOGY, "cyclic_therapy", 2500, 1, 0),
    ("CP-NEPH-002", "Acute kidney injury management", S.NEPHROLOGY, "icu_medical", 78000, 7, 3),
    ("CP-NEPH-003", "AV fistula creation", S.NEPHROLOGY, "daycare_surgery", 32000, 1, 0),
    ("CP-NEPH-004", "Renal transplant", S.NEPHROLOGY, "major_surgery", 485000, 14, 4),
    ("CP-UROL-001", "Ureteroscopy with stone removal", S.UROLOGY, "minor_surgery", 42000, 2, 0),
    ("CP-UROL-002", "Percutaneous nephrolithotomy", S.UROLOGY, "minor_surgery", 68000, 3, 0),
    ("CP-UROL-003", "Transurethral resection of prostate", S.UROLOGY, "minor_surgery", 58000, 3, 0),
    ("CP-UROL-004", "Extracorporeal shock wave lithotripsy", S.UROLOGY, "daycare_surgery", 24000, 1, 0),
    ("CP-UROL-005", "Cystoscopy", S.UROLOGY, "daycare_surgery", 12000, 1, 0),
    ("CP-UROL-006", "Ureteric stent placement", S.UROLOGY, "daycare_implant", 28000, 1, 0),
    # --- gastroenterology -------------------------------------------------
    ("CP-GAST-001", "Upper GI endoscopy", S.GASTROENTEROLOGY, "diagnostic_procedure", 8000, 1, 0),
    ("CP-GAST-002", "Colonoscopy", S.GASTROENTEROLOGY, "diagnostic_procedure", 12000, 1, 0),
    ("CP-GAST-003", "ERCP with stenting", S.GASTROENTEROLOGY, "daycare_implant", 58000, 2, 0),
    ("CP-GAST-004", "Acute pancreatitis management", S.GASTROENTEROLOGY, "icu_medical", 95000, 9, 4),
    ("CP-GAST-005", "Upper GI bleed management", S.GASTROENTEROLOGY, "icu_medical", 68000, 5, 2),
    ("CP-GAST-006", "Liver cirrhosis decompensation", S.GASTROENTEROLOGY, "medical_admission", 72000, 8, 1),
    ("CP-GAST-007", "Variceal banding", S.GASTROENTEROLOGY, "daycare_surgery", 26000, 1, 0),
    # --- pulmonology ------------------------------------------------------
    ("CP-PULM-001", "Community acquired pneumonia", S.PULMONOLOGY, "medical_admission", 42000, 5, 0),
    ("CP-PULM-002", "Severe pneumonia with ventilation", S.PULMONOLOGY, "icu_medical", 165000, 10, 6),
    ("CP-PULM-003", "COPD exacerbation", S.PULMONOLOGY, "medical_admission", 38000, 5, 0),
    ("CP-PULM-004", "Acute severe asthma", S.PULMONOLOGY, "medical_admission", 32000, 3, 0),
    ("CP-PULM-005", "Bronchoscopy", S.PULMONOLOGY, "diagnostic_procedure", 14000, 1, 0),
    ("CP-PULM-006", "Pleural effusion drainage", S.PULMONOLOGY, "minor_surgery", 28000, 3, 0),
    ("CP-PULM-007", "Pulmonary tuberculosis admission", S.PULMONOLOGY, "medical_admission", 45000, 7, 0),
    # --- general medicine -------------------------------------------------
    ("CP-MEDI-001", "Dengue fever with thrombocytopenia", S.GENERAL_MEDICINE, "medical_admission", 32000, 4, 0),
    ("CP-MEDI-002", "Severe dengue with ICU care", S.GENERAL_MEDICINE, "icu_medical", 88000, 6, 3),
    ("CP-MEDI-003", "Enteric fever", S.GENERAL_MEDICINE, "medical_admission", 26000, 5, 0),
    ("CP-MEDI-004", "Malaria, complicated", S.GENERAL_MEDICINE, "medical_admission", 34000, 5, 0),
    ("CP-MEDI-005", "Sepsis management", S.GENERAL_MEDICINE, "icu_medical", 145000, 9, 5),
    ("CP-MEDI-006", "Diabetic ketoacidosis", S.ENDOCRINOLOGY, "icu_medical", 62000, 5, 2),
    ("CP-MEDI-007", "Hypertensive emergency", S.GENERAL_MEDICINE, "medical_admission", 38000, 3, 0),
    ("CP-MEDI-008", "Acute gastroenteritis with dehydration", S.GENERAL_MEDICINE, "medical_admission", 18000, 3, 0),
    ("CP-MEDI-009", "Anaemia evaluation and transfusion", S.GENERAL_MEDICINE, "medical_admission", 28000, 3, 0),
    ("CP-MEDI-010", "Snake bite management", S.GENERAL_MEDICINE, "icu_medical", 72000, 5, 2),
    ("CP-MEDI-011", "Thyroid disorder admission", S.ENDOCRINOLOGY, "medical_admission", 24000, 3, 0),
    ("CP-MEDI-012", "COVID-19 moderate admission", S.GENERAL_MEDICINE, "medical_admission", 52000, 7, 0),
    # --- paediatrics ------------------------------------------------------
    ("CP-PAED-001", "Neonatal jaundice phototherapy", S.PAEDIATRICS, "medical_admission", 22000, 3, 0),
    ("CP-PAED-002", "Neonatal intensive care, preterm", S.PAEDIATRICS, "icu_medical", 185000, 14, 12),
    ("CP-PAED-003", "Paediatric pneumonia", S.PAEDIATRICS, "medical_admission", 28000, 4, 0),
    ("CP-PAED-004", "Paediatric seizure evaluation", S.PAEDIATRICS, "medical_admission", 32000, 3, 0),
    ("CP-PAED-005", "Bronchiolitis", S.PAEDIATRICS, "medical_admission", 24000, 4, 0),
    ("CP-PAED-006", "Paediatric hernia repair", S.PAEDIATRICS, "daycare_surgery", 26000, 1, 0),
    # --- ENT and others ---------------------------------------------------
    ("CP-ENT-001", "Tonsillectomy", S.ENT, "daycare_surgery", 28000, 1, 0),
    ("CP-ENT-002", "Functional endoscopic sinus surgery", S.ENT, "minor_surgery", 45000, 2, 0),
    ("CP-ENT-003", "Septoplasty", S.ENT, "daycare_surgery", 32000, 1, 0),
    ("CP-ENT-004", "Tympanoplasty", S.ENT, "minor_surgery", 38000, 2, 0),
    ("CP-ENT-005", "Mastoidectomy", S.ENT, "minor_surgery", 52000, 3, 0),
    ("CP-ENT-006", "Cochlear implant", S.ENT, "major_surgery_implant", 585000, 4, 0),
    ("CP-PLAS-001", "Split skin grafting", S.PLASTIC_SURGERY, "minor_surgery", 42000, 4, 0),
    ("CP-PLAS-002", "Burns management, moderate", S.PLASTIC_SURGERY, "icu_medical", 165000, 12, 5),
    ("CP-PSYC-001", "Psychiatric inpatient stabilisation", S.PSYCHIATRY, "medical_admission", 38000, 7, 0),
    ("CP-DERM-001", "Severe drug reaction admission", S.DERMATOLOGY, "medical_admission", 42000, 5, 0),
    ("CP-EMER-001", "Emergency stabilisation and observation", S.EMERGENCY, "medical_admission", 22000, 2, 0),
    ("CP-EMER-002", "Polytrauma stabilisation", S.EMERGENCY, "icu_medical", 195000, 10, 5),
]


def build_procedures() -> list[Procedure]:
    """Materialise the catalogue."""
    procedures: list[Procedure] = []
    for code, name, specialty, archetype, base, los, icu in SPECS:
        fractions = ARCHETYPES[archetype]
        non_nabh = Decimal(base)
        procedures.append(
            Procedure(
                code=code,
                name=name,
                specialty=specialty,
                description=f"{name}, indicative package, CGHS-anchored.",
                base_rate_non_nabh=non_nabh,
                base_rate_nabh=round_inr(non_nabh * NABH_PREMIUM),
                typical_los_days=float(los),
                typical_icu_days=float(icu),
                cost_split=CostSplit(fractions=dict(fractions)),
                requires_implant=H.IMPLANTS in fractions,
                is_daycare=archetype.startswith("daycare"),
                # ICU-heavy and major surgical stays vary far more than a
                # daycare procedure, whose length is essentially fixed.
                los_variability=(
                    0.10 if archetype.startswith("daycare")
                    else 0.45 if archetype == "icu_medical"
                    else 0.30
                ),
                synonyms=synonyms_for(code),
                specialty_terms=specialty_terms_for(code),
            )
        )
    return procedures


def procedures_by_specialty(procedures: list[Procedure]) -> dict[S, list[Procedure]]:
    grouped: dict[S, list[Procedure]] = {}
    for proc in procedures:
        grouped.setdefault(proc.specialty, []).append(proc)
    return grouped
