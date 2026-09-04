"""
Unit Tests for SurveyRepository and ContactRepository.
Uses SQLite in-memory via conftest.py session fixture.
"""

import pytest
from backend.app.database.repository import SurveyRepository, ContactRepository
from backend.app.schemas.contact import Contact, BoundingBox


def make_contact(contact_id: str, survey_id: str, priority: str = "MEDIUM") -> Contact:
    """Factory helper for test Contact objects using minimal required fields."""
    return Contact(
        contact_id=contact_id,
        survey_id=survey_id,
        class_name="ghost_net",
        confidence=0.72,
        bbox=BoundingBox(x1=50, y1=60, x2=150, y2=160),
        data_quality=0.65,
        shadow_evidence=0.55,
        context_score=0.60,
        priority=priority,
        latitude=None,
        longitude=None,
        localization_status="UNAVAILABLE",
        review_status="AI_CANDIDATE",
        review_note=None,
        model_version="DRISHTI-YOLOv8s-baseline-v1"
    )


class TestSurveyRepository:
    def test_save_and_retrieve_survey(self, db_session):
        """Saving a survey and retrieving it by ID should return identical data."""
        repo = SurveyRepository(db_session)
        repo.save_survey(
            survey_id="REPO_TEST_001",
            filename="test_swath.png",
            raw_image_path="/data/raw/test_swath.png",
            image_width=1920,
            image_height=1080,
            data_quality=0.80
        )
        db_session.commit()
        survey = repo.get_survey("REPO_TEST_001")
        assert survey is not None
        assert survey.survey_id == "REPO_TEST_001"
        assert survey.filename == "test_swath.png"
        assert survey.image_width == 1920
        assert survey.image_height == 1080
        assert abs(survey.data_quality - 0.80) < 1e-6

    def test_get_nonexistent_survey_returns_none(self, db_session):
        """Fetching a survey that does not exist must return None, not raise."""
        repo = SurveyRepository(db_session)
        result = repo.get_survey("THIS_DOES_NOT_EXIST")
        assert result is None


class TestContactRepository:
    def test_save_and_list_contacts(self, db_session):
        """Contacts saved for a survey should all be retrievable by survey ID."""
        SurveyRepository(db_session).save_survey(
            survey_id="SURV_CONTACT_TEST",
            filename="contact_test.png",
            raw_image_path="/data/contact_test.png",
            image_width=640,
            image_height=640,
            data_quality=0.70
        )
        db_session.commit()

        contacts = [
            make_contact("SURV_CONTACT_TEST_C001", "SURV_CONTACT_TEST", "HIGH"),
            make_contact("SURV_CONTACT_TEST_C002", "SURV_CONTACT_TEST", "LOW"),
        ]
        repo = ContactRepository(db_session)
        repo.save_contacts(contacts)
        db_session.commit()

        retrieved = repo.get_contacts_by_survey("SURV_CONTACT_TEST")
        assert len(retrieved) == 2

    def test_update_review_status(self, db_session):
        """Submitting a CONFIRMED review must update review_status and preserve the note."""
        SurveyRepository(db_session).save_survey(
            survey_id="SURV_REVIEW_TEST",
            filename="review_test.png",
            raw_image_path="/data/review_test.png",
            image_width=640,
            image_height=640,
            data_quality=0.70
        )
        db_session.commit()

        c = make_contact("SURV_REVIEW_TEST_C001", "SURV_REVIEW_TEST")
        ContactRepository(db_session).save_contacts([c])
        db_session.commit()

        repo = ContactRepository(db_session)
        updated = repo.update_review(
            contact_id="SURV_REVIEW_TEST_C001",
            review_status="CONFIRMED",
            review_note="Visually verified by operator."
        )
        assert updated is not None
        assert updated.review_status == "CONFIRMED"
        assert updated.review_note == "Visually verified by operator."

    def test_get_nonexistent_contact_returns_none(self, db_session):
        """Fetching a contact that does not exist must return None, not raise."""
        repo = ContactRepository(db_session)
        result = repo.get_contact_by_id("DOES_NOT_EXIST_C000")
        assert result is None
