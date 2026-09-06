# SONAR-INTEL — ML Training & Retraining Guide

## Training Pipeline Overview

SONAR-INTEL supports both deep-learning object detector training (YOLOv8s) and downstream second-stage acoustic models.

### Dataset Structure (YOLO Standard)
```
data/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```
Each label file contains normalized YOLO bounding box coordinates:
`<class_id> <x_center> <y_center> <width> <height>`

### 1. Training the Primary Detector (`ml/training/train_yolov8n.py`)
```bash
python ml/training/train_yolov8n.py \
  --data ml/training/dataset.yaml \
  --epochs 100 \
  --imgsz 640 \
  --batch 16 \
  --device cpu
```

Hyperparameters optimized for side-scan sonar waterfall imagery:
- Mosaic augmentation: 0.2 (low, to prevent disruptive swath stitching artifacts)
- Flips: Horizontal only (vertical flip breaks acoustic shadow directionality)
- Contrast & brightness jitter: moderate (models acoustic gain shifts)

### 2. Exporting Retraining Data via Active Learning
When hydrographers verify contacts or flag false positives, review samples accumulate in `training_samples`.
Export candidate training sets using:
```bash
python ml/training/active_learning_export.py
```
Outputs normalized YOLO datasets ready for offline fine-tuning in `data/active_learning_export/`.
