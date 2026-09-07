"""
Tests for Active Learning Service.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.connection import Base
from backend.app.database.models import ContactModel, SurveyModel
from backend.app.services.active_learning_service import ActiveLearningService


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


def test_active_learning_capture_sample(test_db):
    # Setup parent survey & contact
    survey = SurveyModel(survey_id="SURV_01", filename="test.png", raw_image_path="test.png")
    test_db.add(survey)
    contact = ContactModel(
        contact_id="SURV_01_C001",
        survey_id="SURV_01",
        class_name="ghost_net",
        confidence=0.52,  # high uncertainty (~0.5)
        bbox_x1=10, bbox_y1=10, bbox_x2=50, bbox_y2=50,
        novelty_score=65.0
    )
    test_db.add(contact)
    test_db.commit()

    service = ActiveLearningService(test_db)
    sample = service.capture_review_sample(
        contact_id="SURV_01_C001",
        review_status="FALSE_POSITIVE",
        review_note="Geological boulder ridge, not a ghost net"
    )

    assert sample is not None
    assert sample.contact_id == "SURV_01_C001"
    assert sample.review_decision == "FALSE_POSITIVE"
    assert sample.sample_priority == "HIGH"
    assert sample.uncertainty_score > 0.8

    # Query high-value samples
    samples = service.get_high_value_samples(min_priority="HIGH")
    assert len(samples) == 1
    assert samples[0]["contact_id"] == "SURV_01_C001"
