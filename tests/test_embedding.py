"""
Tests for 37-Dimensional Contact Embeddings (ContactEmbedder).
"""

import numpy as np
from ml.inference.embedding import ContactEmbedder


def test_embedding_dimension_and_normalization():
    embedder = ContactEmbedder()
    crop = np.random.randint(0, 255, size=(40, 40), dtype=np.uint8)
    context = {"shadow_evidence": 0.6, "local_contrast": 0.5, "aspect_ratio": 1.5}
    bbox = {"x1": 100, "y1": 100, "x2": 140, "y2": 140}

    vec = embedder.extract_embedding(crop, context, bbox, image_shape=(640, 640))

    assert len(vec) == 37
    assert isinstance(vec, np.ndarray)
    # Norm must be 1.0 (L2-normalized)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4


def test_cosine_similarity_identical_and_orthogonal():
    embedder = ContactEmbedder()
    v1 = np.zeros(37, dtype=np.float32)
    v1[0] = 1.0
    v2 = np.zeros(37, dtype=np.float32)
    v2[0] = 1.0
    v3 = np.zeros(37, dtype=np.float32)
    v3[1] = 1.0

    # Identical vectors -> similarity 1.0
    assert abs(embedder.cosine_similarity(v1, v2) - 1.0) < 1e-4
    # Orthogonal vectors -> similarity 0.0
    assert abs(embedder.cosine_similarity(v1, v3)) < 1e-4
