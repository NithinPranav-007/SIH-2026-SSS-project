"""
Active Learning Dataset Exporter.

Exports operator-reviewed contacts and confirmed targets into standard
YOLO annotation format (images/ + labels/ with normalized cx, cy, w, h).

SAFETY RULE:
This script compiles candidate training sets for offline evaluation.
It NEVER directly modifies production weights or auto-deploys models.
"""

from typing import Dict, Any, List, Optional
import os
import shutil
import logging
from sqlalchemy.orm import Session
from backend.app.database.models import ContactModel, SurveyModel, TrainingSampleModel

logger = logging.getLogger(__name__)


def export_active_learning_dataset(
    db: Session,
    output_dir: str = "data/active_learning_export",
    include_uncertain: bool = False
) -> Dict[str, Any]:
    """
    Exports confirmed contacts to YOLO dataset directory.
    
    Returns:
        Summary dict with export counts.
    """
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)

    status_filter = ["CONFIRMED"]
    if include_uncertain:
        status_filter.append("UNCERTAIN")

    contacts = (
        db.query(ContactModel)
        .filter(ContactModel.review_status.in_(status_filter))
        .all()
    )

    exported_count = 0
    survey_ids = set()

    for c in contacts:
        survey = db.query(SurveyModel).filter(SurveyModel.survey_id == c.survey_id).first()
        if not survey or not os.path.exists(survey.raw_image_path):
            continue

        survey_ids.add(survey.survey_id)
        w = survey.image_width or 640
        h = survey.image_height or 640

        # Normalized YOLO format: class_id, cx, cy, bw, bh
        bw = (c.bbox_x2 - c.bbox_x1) / float(w)
        bh = (c.bbox_y2 - c.bbox_y1) / float(h)
        cx = (c.bbox_x1 + c.bbox_x2) / (2.0 * float(w))
        cy = (c.bbox_y1 + c.bbox_y2) / (2.0 * float(h))

        label_path = os.path.join(output_dir, "labels", f"{c.contact_id}.txt")
        with open(label_path, "w") as f:
            f.write(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")

        exported_count += 1

    return {
        "status": "success",
        "exported_contacts": exported_count,
        "surveys_represented": len(survey_ids),
        "output_directory": output_dir,
        "format": "YOLO_TXT"
    }


if __name__ == "__main__":
    from backend.app.database.connection import SessionLocal
    db = SessionLocal()
    try:
        res = export_active_learning_dataset(db)
        print(f"Exported: {res}")
    finally:
        db.close()
