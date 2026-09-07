"""
PyTorch Neural Network Architectures for Ocean Drift Physics Residual Correction.

Implements:
1. DriftGRU: Multi-layer Gated Recurrent Unit network
2. DriftLSTM: Multi-layer Long Short-Term Memory network

Both models ingest historical sequence tensors [N, seq_len, feature_dim]
and predict multi-horizon East/North tangent plane physics correction vectors:
[Delta E24, Delta N24, Delta E48, Delta N48, Delta E72, Delta N72] in meters.
"""

import torch
import torch.nn as nn
from typing import Dict, Any


class DriftGRU(nn.Module):
    """
    Physics Residual GRU Model.
    Learns systematic errors in deterministic Lagrangian trajectories.
    """

    def __init__(
        self,
        input_dim: int = 19,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_dim: int = 6
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_dim = output_dim

        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        self.head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape [batch_size, seq_len, input_dim]
        Returns:
            residuals: Tensor of shape [batch_size, 6]
                       [dE_24, dN_24, dE_48, dN_48, dE_72, dN_72] in meters
        """
        out, _ = self.gru(x)
        # Take representation from last time step
        last_step = out[:, -1, :]
        residuals = self.head(last_step)
        return residuals


class DriftLSTM(nn.Module):
    """
    Physics Residual LSTM Model.
    Architectural counterpart to DriftGRU for comparative empirical evaluation.
    """

    def __init__(
        self,
        input_dim: int = 19,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_dim: int = 6
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_dim = output_dim

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        self.head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape [batch_size, seq_len, input_dim]
        Returns:
            residuals: Tensor of shape [batch_size, 6]
                       [dE_24, dN_24, dE_48, dN_48, dE_72, dN_72] in meters
        """
        out, (hn, cn) = self.lstm(x)
        last_step = out[:, -1, :]
        residuals = self.head(last_step)
        return residuals


def get_model_summary(model: nn.Module) -> Dict[str, Any]:
    """Returns parameter count, layer breakdown, and architecture info."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "model_class": model.__class__.__name__,
        "input_dim": getattr(model, "input_dim", None),
        "hidden_size": getattr(model, "hidden_size", None),
        "num_layers": getattr(model, "num_layers", None),
        "output_dim": getattr(model, "output_dim", None),
        "total_parameters": total_params,
        "trainable_parameters": trainable_params
    }
