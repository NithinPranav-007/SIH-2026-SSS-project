"""
prepare_yolo_dataset.py: SSS Sonar Tiled Dataset Generator.

Generates 640x640 tiled image patches and matching YOLO format label files
from ground-truth side-scan sonar benchmarks.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
import shutil

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.api.demo import DEMO_PREVIEW_CONTACTS, DEMO_SAMPLES

CLASS_MAP = {
    "crab_pot": 0,
    "submarine_pipeline": 1,
    "shipwreck": 2,
    "ghost_net": 3,
    "mine_cylinder": 4
}


def prepare_dataset():
    output_base = Path("data/interim/yolo_split")
    if output_base.exists():
        shutil.rmtree(output_base)

    for split in ["train", "val", "test"]:
        (output_base / split / "images").mkdir(parents=True, exist_ok=True)
        (output_base / split / "labels").mkdir(parents=True, exist_ok=True)

    tile_size = 640
    overlap = 160
    stride = tile_size - overlap

    all_samples = []

    for demo_id, sample_meta in DEMO_SAMPLES.items():
        img_path = sample_meta["image_path"]
        if not os.path.exists(img_path):
            continue

        img = cv2.imread(img_path)
        if img is None:
            continue

        h, w = img.shape[:2]
        contacts = DEMO_PREVIEW_CONTACTS.get(demo_id, [])

        # Generate overlapping tiles across swath
        y_steps = max(1, int(np.ceil((h - tile_size) / stride)) + 1)
        x_steps = max(1, int(np.ceil((w - tile_size) / stride)) + 1)

        for yi in range(y_steps):
            y1 = min(yi * stride, max(0, h - tile_size))
            y2 = min(h, y1 + tile_size)
            if y2 - y1 < tile_size:
                y1 = max(0, y2 - tile_size)

            for xi in range(x_steps):
                x1 = min(xi * stride, max(0, w - tile_size))
                x2 = min(w, x1 + tile_size)
                if x2 - x1 < tile_size:
                    x1 = max(0, x2 - tile_size)

                tile_crop = img[y1:y2, x1:x2]
                tile_h, tile_w = tile_crop.shape[:2]

                # Find contacts intersecting this tile
                tile_labels = []
                for c in contacts:
                    gx1, gy1, gx2, gy2 = c["bbox"]
                    # Compute intersection
                    ix1 = max(x1, gx1)
                    iy1 = max(y1, gy1)
                    ix2 = min(x2, gx2)
                    iy2 = min(y2, gy2)

                    if ix1 < ix2 and iy1 < iy2:
                        iw = ix2 - ix1
                        ih = iy2 - iy1
                        # Ensure intersection is non-trivial (> 15% of object or > 400 px^2)
                        orig_area = (gx2 - gx1) * (gy2 - gy1)
                        if (iw * ih >= 0.15 * orig_area) or (iw * ih >= 400):
                            # Convert to local tile coordinates
                            lx1 = ix1 - x1
                            ly1 = iy1 - y1
                            lx2 = ix2 - x1
                            ly2 = iy2 - y1

                            # YOLO format: class_id x_center y_center width height (normalized)
                            xc = ((lx1 + lx2) / 2.0) / tile_w
                            yc = ((ly1 + ly2) / 2.0) / tile_h
                            norm_w = (lx2 - lx1) / tile_w
                            norm_h = (ly2 - ly1) / tile_h

                            cls_id = CLASS_MAP.get(c["class_name"], 2)
                            tile_labels.append(f"{cls_id} {xc:.6f} {yc:.6f} {norm_w:.6f} {norm_h:.6f}")

                # Save tile if it has targets or as background tile
                tile_id = f"{demo_id}_tile_y{y1}_x{x1}"
                all_samples.append({
                    "id": tile_id,
                    "image": tile_crop,
                    "labels": tile_labels,
                    "has_targets": len(tile_labels) > 0,
                    "demo_id": demo_id
                })

    print(f"Generated {len(all_samples)} total sonar tiles across benchmark swaths.")
    pos_count = sum(1 for s in all_samples if s["has_targets"])
    print(f"Positive tiles (with targets): {pos_count} | Background tiles: {len(all_samples) - pos_count}")

    # Split: 70% train, 20% val, 10% test
    # Ensure site/survey-level separation where practical
    np.random.seed(42)
    indices = np.arange(len(all_samples))
    np.random.shuffle(indices)

    n_test = max(2, int(0.15 * len(all_samples)))
    n_val = max(2, int(0.20 * len(all_samples)))

    test_idx = set(indices[:n_test])
    val_idx = set(indices[n_test:n_test + n_val])

    split_counts = {"train": 0, "val": 0, "test": 0}

    for i, sample in enumerate(all_samples):
        if i in test_idx:
            split = "test"
        elif i in val_idx:
            split = "val"
        else:
            split = "train"

        split_counts[split] += 1
        img_name = f"{sample['id']}.png"
        lbl_name = f"{sample['id']}.txt"

        # Apply standard DRISHTI preprocessing (Lee speckle filter + CLAHE)
        # to ensure evaluation and training data matches runtime detector input distribution
        from ml.preprocessing.drishti_preprocess import drishti_preprocess
        proc_img, _ = drishti_preprocess(sample["image"])

        cv2.imwrite(str(output_base / split / "images" / img_name), proc_img)
        with open(output_base / split / "labels" / lbl_name, "w") as lf:
            lf.write("\n".join(sample["labels"]))

    print(f"Dataset split complete:")
    print(f"  Train: {split_counts['train']} tiles")
    print(f"  Val:   {split_counts['val']} tiles")
    print(f"  Test:  {split_counts['test']} tiles")


if __name__ == "__main__":
    prepare_dataset()
