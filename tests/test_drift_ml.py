"""
Tests for PyTorch GRU & LSTM Residual Correction Models, Leakage Prevention, and Model Registry.
"""

import torch
import numpy as np
from ml.drift.models.architectures import DriftGRU, DriftLSTM, get_model_summary
from ml.drift.models.features import check_data_leakage
from ml.drift.models.trainer import DriftResidualTrainer
from ml.drift.models.registry import ModelRegistry


def test_gru_architecture_forward_shape():
    batch_size = 4
    seq_len = 24
    input_dim = 19
    output_dim = 6

    model = DriftGRU(input_dim=input_dim, hidden_size=32, num_layers=2, output_dim=output_dim)
    dummy_input = torch.randn(batch_size, seq_len, input_dim)
    out = model(dummy_input)

    assert out.shape == (batch_size, output_dim)
    summary = get_model_summary(model)
    assert summary["total_parameters"] > 0


def test_lstm_architecture_forward_shape():
    batch_size = 4
    seq_len = 24
    input_dim = 19
    output_dim = 6

    model = DriftLSTM(input_dim=input_dim, hidden_size=32, num_layers=2, output_dim=output_dim)
    dummy_input = torch.randn(batch_size, seq_len, input_dim)
    out = model(dummy_input)

    assert out.shape == (batch_size, output_dim)


def test_data_leakage_detection():
    train_ids = ["TRK_01", "TRK_02", "TRK_03"]
    val_ids = ["TRK_04", "TRK_05"]
    test_ids = ["TRK_06", "TRK_07"]

    # Clean split
    is_leak_free, report = check_data_leakage(train_ids, val_ids, test_ids)
    assert is_leak_free is True
    assert report["status"] == "PASSED"

    # Leaked split
    leaked_val = ["TRK_02", "TRK_05"]
    is_leak_free, report = check_data_leakage(train_ids, leaked_val, test_ids)
    assert is_leak_free is False
    assert report["status"] == "FAILED_LEAKAGE_DETECTED"
    assert "TRK_02" in report["id_overlap"]["train_val_overlap"]


def test_training_sufficiency_guard():
    trainer = DriftResidualTrainer(model_type="gru")
    # Call train with 0 trajectories (below minimum threshold)
    res = trainer.train(
        X_train=np.empty((0, 24, 19), dtype=np.float32),
        Y_train=np.empty((0, 6), dtype=np.float32),
        X_val=np.empty((0, 24, 19), dtype=np.float32),
        Y_val=np.empty((0, 6), dtype=np.float32),
        trajectory_count=0
    )

    assert res["status"] == "INSUFFICIENT_TRAINING_DATA"
    assert "deterministic Physics Baseline" in res["message"]


def test_model_registry_champion_selection(tmp_path):
    registry = ModelRegistry(registry_dir=tmp_path)
    champ = registry.get_champion()
    assert champ["model_name"] == "PHYSICS"

    # Export comparison reports
    json_p, csv_p = registry.export_comparison_reports(output_dir=tmp_path)
    assert json_p.exists()
    assert csv_p.exists()
