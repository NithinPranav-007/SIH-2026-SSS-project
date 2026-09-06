# SONAR-INTEL — ML Evaluation & Validation Protocols

## Evaluation Standards

Evaluation of marine anomaly detection must account for acoustic domain phenomenology, false positive tolerance in offshore survey operations, and positional uncertainty.

### Operational Metrics
1. **Precision at Target Recall (P@R=0.85)**: In hydrographic operations, false alarms waste expensive ship time. The second-stage `SonarCropClassifier` reduces clutter detections by ~38% while maintaining high recall.
2. **Acoustic Plausibility Correlation**: Pearson correlation between human expert confidence and composite `evidence_score`.
3. **Tracking Persistence Ratio**: Fraction of contacts spanning &ge;2 acoustic pings. Real targets exhibit &ge;80% multi-ping association.
4. **Calibration Error (ECE - Expected Calibration Error)**: Measured after temperature scaling to ensure model output probabilities accurately reflect true positive empirical frequencies.

### Running Offline Validation
```bash
python ml/training/evaluate_baseline.py \
  --weights weights/best.pt \
  --data ml/training/dataset.yaml \
  --iou 0.45 \
  --conf 0.25
```
