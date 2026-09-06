"""
Contact Embedding Module — 37-Dimensional Acoustic Feature Representation.

Constructs a compact, interpretable, CPU-only 37-dimensional representation
for every detected sonar contact:
- 14 Acoustic Physics Features (shadow, contrast, SNR, nadir distance, texture)
- 7 Geometric Features (aspect ratio, normalized area, normalized width/height, compactness)
- 16 Grayscale Histogram Bins (normalized backscatter distribution across the crop)

Total: 14 + 7 + 16 = 37 dimensions. L2-normalized.

Enables:
1. Fast Cosine-Similarity Search across contacts ("FIND SIMILAR CONTACTS").
2. Prototype-based Unknown Anomaly Detection.
3. Completely offline, zero GPU required, deterministic.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2


class ContactEmbedder:
    """
    Extracts 37-dimensional normalized feature embeddings and computes similarity.
    """
    EMBEDDING_DIM = 37

    def extract_embedding(
        self,
        crop: Optional[np.ndarray],
        context: Dict[str, Any],
        bbox: Dict[str, int],
        image_shape: Tuple[int, int] = (640, 640),
        data_quality: float = 1.0
    ) -> np.ndarray:
        """
        Extracts an L2-normalized 37-dimensional feature vector.
        
        Args:
            crop: Contact patch image (grayscale or BGR)
            context: Acoustic context dictionary
            bbox: dict with x1, y1, x2, y2
            image_shape: (height, width) of parent image
            data_quality: Swath quality score
            
        Returns:
            np.ndarray of shape (37,), dtype float32, L2 normalized.
        """
        img_h, img_w = image_shape

        # 1. 14 Acoustic Physics Features
        ar = float(context.get("aspect_ratio", 1.0))
        geom = float(context.get("geom_score", 0.8 if 1.2 <= ar <= 5.0 else 0.5))
        texture = float(context.get("texture_std", 15.0))
        highlight = float(context.get("highlight_intensity", 120.0))
        snr_proxy = float(np.clip(texture / (highlight + 1e-4), 0.0, 5.0))

        acoustic_feats = [
            float(context.get("shadow_evidence", 0.35)),
            float(context.get("local_contrast", 0.40)),
            geom,
            float(context.get("quality_score", data_quality)),
            float(context.get("shadow_length_est", 0.0)) / 100.0,
            highlight / 255.0,
            float(context.get("edge_density", 0.20)),
            texture / 50.0,
            float(context.get("distance_from_nadir", 200.0)) / max(1.0, float(img_w / 2)),
            float(context.get("object_area_px", 400.0)) / 10000.0,
            float(context.get("bbox_width", 20.0)) / max(1.0, float(img_w)),
            float(context.get("bbox_height", 20.0)) / max(1.0, float(img_h)),
            min(5.0, ar) / 5.0,
            snr_proxy / 5.0
        ]  # length 14

        # 2. 7 Geometric Features
        x1 = bbox.get("x1", 0)
        y1 = bbox.get("y1", 0)
        x2 = bbox.get("x2", 0)
        y2 = bbox.get("y2", 0)
        bw = max(1, x2 - x1)
        bh = max(1, y2 - y1)
        area_norm = (bw * bh) / max(1.0, float(img_w * img_h))
        perim_norm = (2 * (bw + bh)) / max(1.0, float(img_w + img_h))
        compactness = (4.0 * np.pi * (bw * bh)) / max(1.0, (2 * (bw + bh)) ** 2)

        geo_feats = [
            x1 / max(1.0, float(img_w)),
            y1 / max(1.0, float(img_h)),
            bw / max(1.0, float(img_w)),
            bh / max(1.0, float(img_h)),
            area_norm,
            perim_norm,
            compactness
        ]  # length 7

        # 3. 16-bin Histogram of Crop Backscatter
        if crop is not None and crop.size > 0:
            if len(crop.shape) == 3:
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            else:
                gray = crop
            hist, _ = np.histogram(gray, bins=16, range=(0, 256), density=True)
            hist_feats = (hist / (hist.sum() + 1e-6)).tolist()
        else:
            hist_feats = [1.0 / 16.0] * 16  # length 16

        # Assemble 37-dim vector
        raw_vec = np.array(acoustic_feats + geo_feats + hist_feats, dtype=np.float32)

        # L2 normalize
        norm = np.linalg.norm(raw_vec)
        if norm > 1e-6:
            raw_vec = raw_vec / norm

        return raw_vec

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Computes cosine similarity between two normalized vectors [0.0 - 1.0]."""
        dot = float(np.dot(vec1, vec2))
        return round(float(np.clip(dot, -1.0, 1.0)), 4)

    def find_most_similar(
        self,
        query_vec: np.ndarray,
        corpus_embeddings: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Finds the top-K most similar contacts in the corpus by cosine similarity.
        
        Args:
            query_vec: (37,) query vector
            corpus_embeddings: list of dicts with 'contact_id', 'class_name', 'embedding'
            top_k: max items to return
            
        Returns:
            List of dicts with contact_id, similarity, class_name
        """
        results = []
        for item in corpus_embeddings:
            emb = item["embedding"]
            if isinstance(emb, bytes):
                emb = np.frombuffer(emb, dtype=np.float32)
            sim = self.cosine_similarity(query_vec, emb)
            results.append({
                "contact_id": item["contact_id"],
                "class_name": item.get("class_name", "unknown"),
                "similarity": round(float((sim + 1.0) / 2.0), 3),  # map to [0, 1]
                "priority": item.get("priority", "MEDIUM")
            })

        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:top_k]
