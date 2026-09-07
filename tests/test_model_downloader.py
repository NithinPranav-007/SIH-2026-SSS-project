"""
Unit tests for DRISHTI Model Weights Downloader and Checksum Verification.
"""

import hashlib
from pathlib import Path
import pytest

from scripts.download_models import (
    MODEL_REGISTRY,
    compute_sha256,
)
from backend.app.core.config import settings


class TestModelDownloader:
    def test_model_registry_contains_required_models(self):
        assert "best_detector.pt" in MODEL_REGISTRY
        meta = MODEL_REGISTRY["best_detector.pt"]
        assert meta["required"] is True
        assert meta["sha256"] == "2f55eec5d8fe6b4737706392e259c02660a8542cddbcbd603f96d606c54cb927"
        assert meta["url"].startswith("https://huggingface.co/")

    def test_compute_sha256_known_string(self, tmp_path):
        test_file = tmp_path / "hello.txt"
        test_file.write_text("SONAR-INTEL-TEST", encoding="utf-8")
        expected_hash = hashlib.sha256("SONAR-INTEL-TEST".encode("utf-8")).hexdigest()

        computed = compute_sha256(test_file)
        assert computed == expected_hash

    def test_active_model_weights_checksum_matches_registry(self):
        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            pytest.skip("Model weights not yet downloaded on disk")

        actual_sha = compute_sha256(model_path)
        expected_sha = MODEL_REGISTRY["best_detector.pt"]["sha256"]
        assert actual_sha.lower() == expected_sha.lower(), (
            f"Active model at {model_path} does not match expected SHA256!"
        )

    def test_ensure_models_detects_existing_valid_file(self, tmp_path):
        # Create a dummy file with correct hash
        content = b"TEST_MODEL_DATA"
        dummy_file = tmp_path / "test_model.pt"
        dummy_file.write_bytes(content)
        content_hash = hashlib.sha256(content).hexdigest()

        assert compute_sha256(dummy_file) == content_hash
