"""Assemble the policy corpus: documents, ground truth, and degraded variants.

The manifest this writes is what the extraction benchmark reads. Each entry
pairs a document with the exact answer for it, so accuracy can be reported per
clause kind and per document condition, which is what makes it possible to say
"OCR escalation improved room-limit recall on phone photos by X" instead of
guessing whether a change helped.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from app.core.config import GENERATED_DIR
from datagen.degrade import PROFILES, degrade_pdf, degrade_to_photo
from datagen.policies import PolicyBlueprint, blueprint_to_truth, make_blueprints
from datagen.render_pdf import render_card_pdf, render_policy_pdf

POLICY_COUNT = 40
POLICY_DIR = GENERATED_DIR / "policies"
CLEAN_DIR = POLICY_DIR / "clean"
SCANNED_DIR = POLICY_DIR / "scanned"
PHOTO_DIR = POLICY_DIR / "photos"
CARD_DIR = POLICY_DIR / "cards"
TRUTH_DIR = POLICY_DIR / "truth"


def _blueprint_summary(bp: PolicyBlueprint) -> dict[str, Any]:
    data = asdict(bp)
    data["start_date"] = bp.start_date.isoformat()
    data["end_date"] = bp.end_date.isoformat()
    data["room_category"] = bp.room_category.value if bp.room_category else None
    data["sublimits"] = [
        {
            "head": head.value if head else None,
            "procedure_code": code,
            "label": label,
            "amount": amount,
        }
        for head, code, label, amount in bp.sublimits
    ]
    return data


def build_policy_corpus(count: int = POLICY_COUNT) -> dict[str, Any]:
    """Generate every policy artefact and return the manifest."""
    blueprints = make_blueprints(count)
    entries: list[dict[str, Any]] = []

    for index, bp in enumerate(blueprints):
        truth = blueprint_to_truth(bp)

        clean_pdf = CLEAN_DIR / f"{bp.policy_id}.pdf"
        render_policy_pdf(bp, clean_pdf)

        truth_path = TRUTH_DIR / f"{bp.policy_id}.json"
        truth_path.parent.mkdir(parents=True, exist_ok=True)
        truth_path.write_text(
            json.dumps(
                {
                    "truth": truth.model_dump(mode="json"),
                    "blueprint": _blueprint_summary(bp),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        documents: list[dict[str, Any]] = [
            {
                "path": str(clean_pdf.relative_to(GENERATED_DIR)),
                "condition": "native_pdf",
                "has_text_layer": True,
                "kind": "policy",
            }
        ]

        # Health cards for a subset, the artefact people photograph most often,
        # and one that carries only a few of the fields.
        if index % 4 == 0:
            card = CARD_DIR / f"{bp.policy_id}_card.pdf"
            render_card_pdf(bp, card)
            documents.append({
                "path": str(card.relative_to(GENERATED_DIR)),
                "condition": "native_pdf",
                "has_text_layer": True,
                "kind": "card",
            })

        # Rotate degradation profiles across the corpus rather than applying all
        # of them to every policy: 40 policies x 5 profiles x 2 formats would be
        # slow to build and slow to benchmark for no extra signal.
        profile = PROFILES[index % len(PROFILES)]

        scanned = SCANNED_DIR / f"{bp.policy_id}_{profile.name}.pdf"
        degrade_pdf(clean_pdf, profile, scanned, seed=index)
        documents.append({
            "path": str(scanned.relative_to(GENERATED_DIR)),
            "condition": profile.name,
            "has_text_layer": False,
            "kind": "policy",
        })

        # Every third policy also gets a single-page photo upload.
        if index % 3 == 0:
            photo_profile = PROFILES[(index + 2) % len(PROFILES)]
            photo = PHOTO_DIR / f"{bp.policy_id}_{photo_profile.name}.jpg"
            degrade_to_photo(clean_pdf, photo_profile, photo, seed=index + 100)
            documents.append({
                "path": str(photo.relative_to(GENERATED_DIR)),
                "condition": photo_profile.name,
                "has_text_layer": False,
                "kind": "photo",
            })

        entries.append({
            "policy_id": bp.policy_id,
            "insurer_id": bp.insurer_id,
            "insurer_name": bp.insurer_name,
            "plan_name": bp.plan_name,
            "policy_type": bp.policy_type,
            "room_basis": bp.room_basis,
            "amount_style": bp.amount_style,
            "contradicts_wording": bp.contradicts_wording,
            "is_top_up": bp.is_top_up,
            "sum_insured": bp.sum_insured,
            "truth_path": str(truth_path.relative_to(GENERATED_DIR)),
            "documents": documents,
        })

    manifest = {
        "policy_count": len(entries),
        "document_count": sum(len(e["documents"]) for e in entries),
        "conditions": sorted({
            d["condition"] for e in entries for d in e["documents"]
        }),
        "policies": entries,
    }

    manifest_path = POLICY_DIR / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_manifest() -> dict[str, Any]:
    path = POLICY_DIR / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            "Policy corpus not built. Run: python -m datagen.build_all"
        )
    return json.loads(path.read_text(encoding="utf-8"))