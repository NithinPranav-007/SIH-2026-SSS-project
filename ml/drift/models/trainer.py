"""
Training Pipeline, Loss Optimization, and Checkpointing for Drift Residual Models.

Features:
- Training data sufficiency verification (halts with INSUFFICIENT_TRAINING_DATA if below threshold)
- Robust Huber loss (Smooth L1) for geographic meter displacements
- AdamW optimizer with decoupled weight decay
- Learning-rate scheduling with early stopping
- Deterministic seed control and reproducibility manifest generation
"""

import time
import random
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from backend.app.core.config import settings
from ml.drift.models.architectures import DriftGRU, DriftLSTM, get_model_summary

logger = logging.getLogger(__name__)


def set_deterministic_seed(seed: int = 42):
    """Enforces determinism across random, numpy, and PyTorch backends."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class DriftResidualTrainer:
    """
    Supervises training of GRU and LSTM physics residual correction models.
    """

    def __init__(
        self,
        model_type: str = "gru",
        input_dim: int = 19,
        hidden_size: Optional[int] = None,
        num_layers: Optional[int] = None,
        dropout: Optional[float] = None,
        learning_rate: Optional[float] = None,
        batch_size: Optional[int] = None,
        epochs: Optional[int] = None,
        patience: Optional[int] = None,
        device: Optional[str] = None,
        seed: int = 42
    ):
        self.model_type = model_type.lower()
        self.input_dim = input_dim
        self.seed = seed
        set_deterministic_seed(seed)

        cfg = settings.drift
        if self.model_type == "gru":
            self.hidden_size = hidden_size or cfg.GRU_HIDDEN_SIZE
            self.num_layers = num_layers or cfg.GRU_LAYERS
            self.dropout = dropout or cfg.GRU_DROPOUT
            self.model = DriftGRU(
                input_dim=self.input_dim,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout
            )
        elif self.model_type == "lstm":
            self.hidden_size = hidden_size or cfg.LSTM_HIDDEN_SIZE
            self.num_layers = num_layers or cfg.LSTM_LAYERS
            self.dropout = dropout or cfg.LSTM_DROPOUT
            self.model = DriftLSTM(
                input_dim=self.input_dim,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}. Expected 'gru' or 'lstm'.")

        self.lr = learning_rate or cfg.LEARNING_RATE
        self.batch_size = batch_size or cfg.BATCH_SIZE
        self.epochs = epochs or cfg.EPOCHS
        self.patience = patience or cfg.EARLY_STOPPING_PATIENCE

        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Huber loss: robust against ocean current surges and outliers
        self.criterion = nn.HuberLoss(delta=1000.0)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=3
        )

    def train(
        self,
        X_train: np.ndarray,
        Y_train: np.ndarray,
        X_val: np.ndarray,
        Y_val: np.ndarray,
        trajectory_count: int,
        checkpoint_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Trains model if data meets sufficiency threshold.
        Otherwise returns INSUFFICIENT_TRAINING_DATA without fabricating data.
        """
        min_required = settings.drift.MIN_TRAJECTORIES_FOR_TRAINING
        if trajectory_count < min_required:
            logger.warning(
                "Training aborted: Available trajectories (%d) below minimum threshold (%d).",
                trajectory_count, min_required
            )
            return {
                "status": "INSUFFICIENT_TRAINING_DATA",
                "message": (
                    f"Dataset contains {trajectory_count} valid trajectories, which is below the minimum "
                    f"threshold of {min_required} required for scientifically defensible ML training. "
                    "The system will continue operating with the deterministic Physics Baseline."
                ),
                "trajectories_available": trajectory_count,
                "trajectories_required": min_required,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Build PyTorch DataLoaders
        train_ds = TensorDataset(torch.from_numpy(X_train).float(), torch.from_numpy(Y_train).float())
        val_ds = TensorDataset(torch.from_numpy(X_val).float(), torch.from_numpy(Y_val).float())

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        best_val_loss = float("inf")
        patience_counter = 0
        history = {"train_loss": [], "val_loss": [], "lr": []}

        ckpt_dir = checkpoint_dir or settings.drift.MODELS_DIR
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        model_filename = f"drift_{self.model_type}_best.pt"
        best_model_path = ckpt_dir / model_filename

        start_time = time.time()
        for epoch in range(1, self.epochs + 1):
            # Training pass
            self.model.train()
            total_train_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                self.optimizer.zero_grad()
                preds = self.model(batch_x)
                loss = self.criterion(preds, batch_y)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()

                total_train_loss += loss.item() * len(batch_x)

            avg_train_loss = total_train_loss / max(1, len(train_ds))

            # Validation pass
            self.model.eval()
            total_val_loss = 0.0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)
                    preds = self.model(batch_x)
                    val_loss = self.criterion(preds, batch_y)
                    total_val_loss += val_loss.item() * len(batch_x)

            avg_val_loss = total_val_loss / max(1, len(val_ds))
            curr_lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step(avg_val_loss)

            history["train_loss"].append(round(avg_train_loss, 4))
            history["val_loss"].append(round(avg_val_loss, 4))
            history["lr"].append(curr_lr)

            # Early stopping check
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "model_type": self.model_type,
                    "input_dim": self.input_dim,
                    "hidden_size": self.hidden_size,
                    "num_layers": self.num_layers,
                    "dropout": self.dropout,
                    "epoch": epoch,
                    "val_loss": avg_val_loss,
                    "hyperparameters": {
                        "lr": self.lr,
                        "batch_size": self.batch_size,
                        "seed": self.seed
                    }
                }, best_model_path)
            else:
                patience_counter += 1
                if patience_counter >= self.patience:
                    logger.info("Early stopping triggered at epoch %d", epoch)
                    break

        duration_sec = time.time() - start_time
        return {
            "status": "TRAINING_COMPLETED",
            "model_type": self.model_type,
            "epochs_trained": len(history["train_loss"]),
            "best_val_loss": round(best_val_loss, 4),
            "training_duration_seconds": round(duration_sec, 2),
            "checkpoint_path": str(best_model_path),
            "history": history,
            "model_summary": get_model_summary(self.model)
        }
