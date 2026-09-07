"""
download_models.py: Automated DRISHTI Model Weights Downloader.

Downloads the fine-tuned DRISHTI YOLOv8s weights and calibration assets
from Hugging Face with cryptographic SHA256 hash verification.

Usage:
    python scripts/download_models.py [--target-dir ml/models/dristri] [--force]
"""

import os
import sys
import argparse
import hashlib
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("model_downloader")

MODEL_REGISTRY = {
    "best_detector.pt": {
        "url": "https://huggingface.co/rehan9599/drishti-detector/resolve/main/best_detector.pt",
        "sha256": "2f55eec5d8fe6b4737706392e259c02660a8542cddbcbd603f96d606c54cb927",
        "description": "DRISHTI YOLOv8s fine-tuned side-scan sonar detector",
        "required": True,
    },
    "calibrator.pkl": {
        "url": "https://huggingface.co/rehan9599/drishti-detector/resolve/main/calibrator.pkl",
        "sha256": None,  # Optional calibration artifact
        "description": "Empirical confidence calibrator artifact",
        "required": False,
    }
}


def compute_sha256(file_path: Path, block_size: int = 65536) -> str:
    """Computes SHA256 hex digest of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()


def download_file(url: str, target_path: Path, expected_sha256: str = None) -> bool:
    """Downloads a file with streaming progress and verifies checksum."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")

    logger.info("Downloading %s ...", url)
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                downloaded_mb = (count * block_size) / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  Progress: {percent:3d}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, temp_path, reporthook=reporthook)
        sys.stdout.write("\n")

        # Verify checksum if specified
        if expected_sha256:
            actual_sha256 = compute_sha256(temp_path)
            if actual_sha256.lower() != expected_sha256.lower():
                logger.error(
                    "SHA256 mismatch for %s!\n  Expected: %s\n  Actual:   %s",
                    target_path.name, expected_sha256, actual_sha256
                )
                if temp_path.exists():
                    temp_path.unlink()
                return False
            logger.info("SHA256 checksum verified: %s", actual_sha256)

        # Atomic rename
        if target_path.exists():
            target_path.unlink()
        temp_path.rename(target_path)
        logger.info("Successfully saved to %s", target_path)
        return True

    except Exception as exc:
        logger.error("Download failed for %s: %s", url, exc)
        if temp_path.exists():
            temp_path.unlink()
        return False


def ensure_models(target_dir: Path, force: bool = False) -> bool:
    """Ensures all required models are present and valid."""
    all_success = True
    for filename, meta in MODEL_REGISTRY.items():
        dest = target_dir / filename
        already_valid = False

        if dest.exists() and not force:
            if meta["sha256"]:
                actual_hash = compute_sha256(dest)
                if actual_hash.lower() == meta["sha256"].lower():
                    logger.info("Model '%s' already exists with verified checksum.", filename)
                    already_valid = True
                else:
                    logger.warning("Existing '%s' hash mismatch. Re-downloading...", filename)
            else:
                logger.info("Model '%s' already exists.", filename)
                already_valid = True

        if not already_valid:
            logger.info("Fetching %s: %s", filename, meta["description"])
            ok = download_file(meta["url"], dest, meta["sha256"])
            if not ok and meta["required"]:
                all_success = False

    return all_success


def main():
    parser = argparse.ArgumentParser(description="DRISHTI Model Weights Downloader")
    default_dir = Path(__file__).resolve().parent.parent / "ml" / "models" / "dristri"
    parser.add_argument("--target-dir", type=Path, default=default_dir, help="Directory to save weights")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    args = parser.parse_args()

    print("=" * 60)
    print("SONAR-INTEL: DRISHTI Model Weights Manager")
    print(f"Target Directory: {args.target_dir}")
    print("=" * 60)

    success = ensure_models(args.target_dir, force=args.force)
    if success:
        print("\n[OK] All model artifacts are present and verified.")
        sys.exit(0)
    else:
        print("\n[FAIL] Failed to download one or more required model artifacts.")
        sys.exit(1)


if __name__ == "__main__":
    main()
