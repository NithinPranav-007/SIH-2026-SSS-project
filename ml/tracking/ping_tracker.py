"""
Multi-Ping Contact Tracking Module.

Associates detection candidates across consecutive acoustic pings (Y-axis rows)
in side-scan sonar waterfall data.

SCIENTIFIC PRINCIPLE:
Real physical objects (shipwrecks, shipping containers, ghost nets, pipelines)
persist across multiple consecutive acoustic transmit/receive cycles (pings).
Transient acoustic reverberation and sensor noise spikes rarely persist across pings.
Tracking stability is therefore a direct discriminator of real objects vs. noise.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class TrackObservation:
    track_id: str
    observation_count: int
    track_confidence: float
    track_stability: float
    start_ping_y: int
    end_ping_y: int
    centroid_x: float
    centroid_y: float


class SonarPingTracker:
    """
    IoU and cross-track spatial association tracker for sonar waterfall imagery.
    Associates bounding boxes whose cross-track (X) overlaps and along-track (Y)
    distance is within ping continuity limits.
    """

    def __init__(
        self,
        max_ping_gap: int = 40,        # Maximum Y pixel gap between consecutive observations
        min_x_overlap_ratio: float = 0.25, # Minimum horizontal overlap to associate
        iou_assoc_threshold: float = 0.20
    ):
        self.max_ping_gap = max_ping_gap
        self.min_x_overlap_ratio = min_x_overlap_ratio
        self.iou_assoc_threshold = iou_assoc_threshold

    def associate_detections(
        self,
        detections: List[Dict[str, Any]],
        survey_id: str = "SURVEY"
    ) -> Dict[int, TrackObservation]:
        """
        Associates detections into tracks.
        
        Args:
            detections: List of detection dicts with 'bbox' and 'confidence'.
            survey_id: Parent survey ID prefix for track naming.
            
        Returns:
            Dict mapping detection index to TrackObservation.
        """
        if not detections:
            return {}

        # Sort detections by Y1 (along-track waterfall line)
        indexed_dets = list(enumerate(detections))
        indexed_dets.sort(key=lambda item: item[1]["bbox"]["y1"] if isinstance(item[1]["bbox"], dict) else item[1]["bbox"][1])

        # Active tracks: list of dicts holding observations
        tracks: List[Dict[str, Any]] = []

        for det_idx, det in indexed_dets:
            bbox = det["bbox"]
            x1 = bbox["x1"] if isinstance(bbox, dict) else bbox[0]
            y1 = bbox["y1"] if isinstance(bbox, dict) else bbox[1]
            x2 = bbox["x2"] if isinstance(bbox, dict) else bbox[2]
            y2 = bbox["y2"] if isinstance(bbox, dict) else bbox[3]
            conf = float(det.get("confidence", 0.50))

            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            # Try to associate with an existing active track
            matched_track = None
            best_dist = float("inf")

            for trk in tracks:
                last_obs = trk["observations"][-1]
                gap_y = y1 - last_obs["y2"]
                # Must be forward in time (down the waterfall) and within ping gap
                if -15 <= gap_y <= self.max_ping_gap:
                    # Check horizontal overlap
                    overlap_x = max(0, min(x2, last_obs["x2"]) - max(x1, last_obs["x1"]))
                    width_min = min(x2 - x1, last_obs["x2"] - last_obs["x1"])
                    x_ratio = overlap_x / (width_min + 1e-5)

                    if x_ratio >= self.min_x_overlap_ratio:
                        dist = abs(cx - last_obs["cx"])
                        if dist < best_dist:
                            best_dist = dist
                            matched_track = trk

            obs_data = {
                "det_idx": det_idx,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "cx": cx, "cy": cy,
                "conf": conf
            }

            if matched_track is not None:
                matched_track["observations"].append(obs_data)
            else:
                # Start new track
                track_counter = len(tracks) + 1
                track_id = f"{survey_id[:8]}_TRK_{track_counter:03d}"
                tracks.append({
                    "track_id": track_id,
                    "observations": [obs_data]
                })

        # Build final mapping from detection index to TrackObservation
        result_map: Dict[int, TrackObservation] = {}

        for trk in tracks:
            obs_list = trk["observations"]
            count = len(obs_list)
            conf_mean = float(np.mean([o["conf"] for o in obs_list]))
            start_y = min(o["y1"] for o in obs_list)
            end_y = max(o["y2"] for o in obs_list)
            mean_cx = float(np.mean([o["cx"] for o in obs_list]))
            mean_cy = float(np.mean([o["cy"] for o in obs_list]))

            # Track stability: higher count + lower horizontal drift = higher stability
            x_variance = float(np.var([o["cx"] for o in obs_list])) if count > 1 else 0.0
            stability = min(1.0, (count * 0.25) / (1.0 + x_variance * 0.05))

            observation_info = TrackObservation(
                track_id=trk["track_id"],
                observation_count=count,
                track_confidence=round(conf_mean, 3),
                track_stability=round(stability, 3),
                start_ping_y=start_y,
                end_ping_y=end_y,
                centroid_x=round(mean_cx, 1),
                centroid_y=round(mean_cy, 1)
            )

            for o in obs_list:
                result_map[o["det_idx"]] = observation_info

        return result_map
