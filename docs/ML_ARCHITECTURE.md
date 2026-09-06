# SONAR-INTEL — Machine Learning Architecture Specification

## Overview & Scientific Domain Principles

SONAR-INTEL processes high-resolution side-scan sonar (SSS) acoustic waterfall imagery to detect, verify, measure, and track submerged marine targets (ghost fishing gear, shipwrecks, shipping containers, ordnance, and uncatalogued acoustic anomalies).

### Core Hydrographic Domain Principles
1. **Quality Propagates to Confidence**: A degraded acoustic swath (high nadir saturation, thermal layer refraction, or signal dropout) mathematically bounds detection certainty.
2. **"No Shadow" ≠ "Negative Shadow"**: Low-profile anthropogenic targets (e.g. flat bottom trawls, buried cables) may legitimately exhibit low vertical relief. Candidates are evaluated with graded multi-factor evidence rather than binary rejection.
3. **Multi-Ping Continuity**: True physical seabed targets persist across multiple consecutive acoustic ping cycles; transient reverberation noise spikes do not.
4. **Unknown ≠ Critical Risk**: Open-set novelty indicates statistical divergence from catalogued training prototypes. An unknown contact is flagged for specialist triage without alarmist classification.
5. **Zero Fabrication**: Geographic coordinates, metric measurements, and explainability evidence are only reported when verified telemetry exists. Missing values are explicitly flagged `UNAVAILABLE` or `NOT_ESTIMATED`.

---

## End-to-End Pipeline Architecture

```
[ Raw Sonar Waterfall Swath (PNG/TIFF) ]
                  │
                  ▼
  [ ml/preprocessing/quality.py ]
    └── 10 Acoustic Quality Indicators (0–100 UI / 0.0–1.0 Norm)
                  │
                  ▼
  [ ml/preprocessing/tiling.py ]
    └── Overlapping deterministic 640×640 Swath Tiles
                  │
                  ▼
  [ ml/inference/drishti_detector.py ]
    └── Primary Object Detection (DRISHTI-YOLOv8s)
                  │
                  ▼
  [ ml/inference/postprocess.py ]
    └── Cross-Tile Non-Maximum Suppression & Deduplication
                  │
                  ▼
  [ ml/tracking/ping_tracker.py ]
    └── Multi-Ping IoU & Cross-Track Association (track_id, persistence)
                  │
                  ▼
  [ ml/inference/context.py & classifier.py ]
    └── Second-Stage False-Positive Reducer (SonarCropClassifier)
                  │
                  ▼
  [ ml/inference/acoustic_fusion.py ]
    └── 14-Indicator Learned Acoustic Fusion (acoustic_probability)
                  │
                  ▼
  [ ml/inference/calibration.py ]
    └── Temperature-Scaled Confidence Calibration
                  │
                  ▼
  [ ml/inference/measurement.py ]
    └── Target Physical Dimensions & Shadow Metrics (length_m, width_m, area_m2)
                  │
                  ▼
  [ ml/inference/embedding.py & anomaly.py ]
    └── 37-Dim L2 Normalized Feature Vector & Novelty Discovery
                  │
                  ▼
  [ ml/inference/risk.py & explanation.py ]
    └── Calibrated Operational Risk (CRITICAL/HIGH/MEDIUM/LOW) & XAI Evidence
                  │
                  ▼
[ Authoritative Contact Schema & Persistent SQLite/PostGIS Storage ]
```

---

## Component Specifications

### 1. Swath Signal Quality Assessment (`quality.py`)
Computes 10 comprehensive metrics for each survey waterfall swath:
- `dynamic_range`: Fraction of the 256 gray levels actively utilized.
- `blur_metric`: Variance of Laplacian (high = sharp boundary acutance).
- `snr_db`: Signal-to-noise ratio proxy over mean backscatter.
- `contrast_score`: Weber contrast between highlight percentiles and ambient seabed.
- `shadow_visibility`: Bimodal histogram separation between shadow deficit and backscatter.
- `nadir_interference`: Center-column acoustic saturation spike.
- `dropout_ratio`: Percentage of near-zero dead lines.
- `saturation_ratio`: Percentage of clipped 255-intensity backscatter.
- `speckle_index`: Coefficient of variation in homogeneous seabed patch.
- `usable_area_ratio`: Usable acoustic swath proportion.

### 2. Multi-Ping Persistence Tracker (`ping_tracker.py`)
Side-scan sonar waterfall data records along-track progression along the Y-axis (consecutive pings). The `SonarPingTracker`:
- Projects candidate bounding boxes into along-track sequence.
- Evaluates horizontal (cross-track X) overlap ratio and along-track continuity gap.
- Assigns persistent `track_id`, counts `track_observations`, and computes `track_stability`.

### 3. Second-Stage False-Positive Reducer (`classifier.py`)
Evaluates cropped candidate patches to reject seabed sand ripples, reverberation clutter, and nadir reflections.
- Uses calibrated logistic regression over acoustic shadow deficit, local contrast, and shape regularities.
- Outputs `REAL_TARGET` or `SONAR_CLUTTER` probability.

### 4. Learned Acoustic Fusion (`acoustic_fusion.py`)
Integrates 14 domain-specific acoustic and geometric features:
- `shadow_evidence`, `local_contrast`, `geom_score`, `quality_score`, `shadow_length_est`, `highlight_intensity`, `edge_density`, `texture_std`, `distance_from_nadir`, `object_area_px`, `bbox_width`, `bbox_height`, `aspect_ratio`, `snr_proxy`.
- Produces `acoustic_probability` and operational `evidence_score`.

### 5. Metric Dimensioning (`measurement.py`)
- Derives physical `length_m`, `width_m`, `area_m2`, `aspect_ratio`, and `shadow_length_m`.
- If survey navigation log exists, scales by towfish resolution with high confidence (`is_estimated=True`).
- If navigation is absent, marks measurements as unscaled pixel approximations with low confidence (`is_estimated=False`).

### 6. Contact Embeddings & Anomaly Detection (`embedding.py`, `anomaly.py`)
- Constructs 37-dimensional L2-normalized feature vectors (14 acoustic + 7 geometric + 16-bin backscatter histogram).
- Computes Euclidean distance to catalogued class prototype centroids.
- Scores `novelty_score` (0–100); contacts &ge; 40 with confident detection become `UNKNOWN_ANOMALY`.

### 7. Operational Risk & Explainable AI (`risk.py`, `explanation.py`)
- Tiers risk into `CRITICAL` (&ge;80), `HIGH` (&ge;60), `MEDIUM` (&ge;35), and `LOW` (<35).
- Synthesizes positive and negative evidence items for surveyor transparency.
