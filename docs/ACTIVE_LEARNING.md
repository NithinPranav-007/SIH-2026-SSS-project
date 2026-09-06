# SONAR-INTEL — Active Learning & Continuous Curation Protocol

## Human-in-the-Loop Operational Architecture

Active learning closes the feedback loop between marine surveyors in the field and the machine learning model stack.

### 1. Sample Capture Trigger
Every operator triage decision submitted via `POST /api/contacts/{contact_id}/review` automatically invokes `ActiveLearningService.capture_review_sample()`.
The system stores:
- Operator review decision (`CONFIRMED`, `FALSE_POSITIVE`, `UNCERTAIN`)
- Review note and timestamp
- Snapshot of all model scores at triage time (detector confidence, classifier confidence, acoustic probability, novelty score, risk score)
- 14 acoustic features and swath quality indicators

### 2. Sample Prioritization
Samples are assigned prioritization tiers:
- **HIGH Priority**:
  - False positive corrections (AI predicted target, operator rejected as clutter)
  - Uncatalogued contacts (`novelty_score >= 50.0`)
  - Epistemic uncertainty spikes (`|confidence - 0.5| < 0.15`)
- **MEDIUM Priority**:
  - Moderate uncertainty contacts (`0.15 <= |confidence - 0.5| < 0.30`)
- **LOW Priority**:
  - Routine high-confidence confirmations

### 3. Model Governance & Safety Rule
**MANDATORY SAFETY POLICY**:
Captured active learning samples inform future training datasets but **NEVER automatically overwrite or deploy** to the active production model stack.
A candidate stack must be registered with `ModelRegistry.register_candidate_stack()`, evaluated against the benchmark test set, and explicitly approved before promotion to active production.
