"""Assemble the bill corpus: documents, ground truth, and photographed copies.

The manifest pairs every rendered bill with the exact answer for it: each line,
its head, and which faults were planted. That is what lets the checker be
reported as a number rather than demonstrated on a screenshot. Recall matters
here, but so does precision: a fifth of the corpus carries no fault at all,
because a checker that finds something wrong with every bill is one nobody will
believe the second time.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import GENERATED_DIR
from app.schemas.hospital import Hospital
from app.schemas.procedure import Procedure
from datagen.bills import blueprint_to_truth, make_blueprints
from datagen.degrade import PROFILES, degrade_to_photo
from datagen.render_pdf import render_bill_pdf

BILL_COUNT = 20
BILL_DIR = GENERATED_DIR / "bills"
CLEAN_DIR = BILL_DIR / "clean"
PHOTO_DIR = BILL_DIR / "photos"
TRUTH_DIR = BILL_DIR / "truth"


def _load(name: str, model) -> list:
    path = GENERATED_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{name} not built. Run: python -m datagen.build_all --core"
        )
    return [model(**row) for row in json.loads(path.read_text(encoding="utf-8"))]


def build_bill_corpus(count: int = BILL_COUNT) -> dict[str, Any]:
    """Generate every bill artefact and return the manifest."""
    hospitals = _load("hospitals.json", Hospital)
    procedures = _load("procedures.json", Procedure)
    blueprints = make_blueprints(hospitals, procedures, count=count)

    entries: list[dict[str, Any]] = []
    for index, bp in enumerate(blueprints):
        clean = CLEAN_DIR / f"{bp.bill_id}.pdf"
        render_bill_pdf(bp, clean)

        truth_path = TRUTH_DIR / f"{bp.bill_id}.json"
        truth_path.parent.mkdir(parents=True, exist_ok=True)
        truth_path.write_text(
            json.dumps(blueprint_to_truth(bp), indent=2), encoding="utf-8"
        )

        documents = [{
            "path": str(clean.relative_to(GENERATED_DIR)),
            "condition": "clean",
            "has_text_layer": True,
        }]

        # A final bill is photographed far more often than it is emailed, so
        # every third one exists as a phone photo too.
        if index % 3 == 0:
            profile = PROFILES[index % len(PROFILES)]
            photo = PHOTO_DIR / f"{bp.bill_id}_{profile.name}.jpg"
            degrade_to_photo(clean, profile, photo, seed=index + 500)
            documents.append({
                "path": str(photo.relative_to(GENERATED_DIR)),
                "condition": profile.name,
                "has_text_layer": False,
            })

        entries.append({
            "bill_id": bp.bill_id,
            "hospital_id": bp.hospital_id,
            "hospital_name": bp.hospital_name,
            "procedure_code": bp.procedure_code,
            "room_category": bp.room_category.value,
            "line_count": len(bp.lines),
            "line_total": str(bp.line_total),
            "planted": bp.planted,
            "truth_path": str(truth_path.relative_to(GENERATED_DIR)),
            "documents": documents,
        })

    manifest = {
        "bill_count": len(entries),
        "document_count": sum(len(e["documents"]) for e in entries),
        "clean_bills": sum(1 for e in entries if not e["planted"]),
        "faults": sorted({fault for e in entries for fault in e["planted"]}),
        "bills": entries,
    }
    manifest_path = BILL_DIR / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_manifest() -> dict[str, Any]:
    path = BILL_DIR / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            "Bill corpus not built. Run: python -m datagen.build_all"
        )
    return json.loads(path.read_text(encoding="utf-8"))
