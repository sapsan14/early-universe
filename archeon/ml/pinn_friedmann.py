"""Physics-Informed Neural Network for the Friedmann equations.

A PINN embeds the governing differential equations directly into the loss:
    L = L_data + lambda * L_physics

where L_physics penalises deviations from the Friedmann equations.

The first Friedmann equation (flat LCDM):
    H^2(a) = H0^2 * [Omega_r / a^4 + Omega_m / a^3 + Omega_Lambda]

The second (acceleration) equation:
    a'' / a = -H0^2/2 * [Omega_r / a^4 + Omega_m / a^3 - 2 * Omega_Lambda]

The PINN learns H(a) or a(t) as a differentiable neural network, and
the physics residual is computed via automatic differentiation.

Key advantage: once trained, the PINN provides an analytic, differentiable
approximation of the expansion history — useful for fast Fisher forecasts,
gradient-based optimisation, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# PINN model
# ---------------------------------------------------------------------------

class FriedmannPINN(nn.Module):
    """Neural network approximation of the Hubble parameter H(a).

    Given scale factor a ∈ (0, 1], predicts H(a).

    Architecture: MLP with tanh activations. Tanh is preferred for PINNs
    because it is smooth and infinitely differentiable, which is important
    for computing physics residuals via autograd.

    Parameters
    ----------
    hidden_dim : int
        Width of hidden layers.
    n_layers : int
        Number of hidden layers.
    """

    def __init__(self, hidden_dim: int = 64, n_layers: int = 4):
        super().__init__()
        layers: list[nn.Module] = [nn.Linear(1, hidden_dim), nn.Tanh()]
        for _ in range(n_layers - 1):
            layers.extend([nn.Linear(hidden_dim, hidden_dim), nn.Tanh()])
        layers.append(nn.Linear(hidden_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, a: torch.Tensor) -> torch.Tensor:
        """Predict H(a).

        Parameters
        ----------
        a : tensor of shape (batch, 1) — scale factor values.

        Returns
        -------
        H : tensor of shape (batch, 1) — Hubble parameter (km/s/Mpc).
        """
        return F.softplus(self.net(a))

    def predict(self, a: np.ndarray) -> np.ndarray:
        """Convenience numpy interface."""
        self.eval()
        with torch.no_grad():
            at = torch.from_numpy(a.reshape(-1, 1).astype(np.float32))
            return self(at).numpy().ravel()


# ---------------------------------------------------------------------------
# Physics residuals
# ---------------------------------------------------------------------------

@dataclass
class CosmologyParams:
    """Flat LCDM cosmological parameters for Friedmann equations."""
    H0: float = 67.36        # km/s/Mpc
    Omega_m: float = 0.3153
    Omega_r: float = 9.1e-5  # radiation density today
    Omega_Lambda: float = 0.6847

    @property
    def H0_natural(self) -> float:
        """H0 in natural units (1/s) for internal use."""
        return self.H0


def friedmann_H_squared(a: torch.Tensor, params: CosmologyParams) -> torch.Tensor:
    """Analytic H^2(a) from the first Friedmann equation (flat LCDM).

    H^2(a) = H0^2 * [Omega_r/a^4 + Omega_m/a^3 + Omega_Lambda]
    """
    a_safe = torch.clamp(a, min=1e-6)
    return params.H0**2 * (
        params.Omega_r / a_safe**4
        + params.Omega_m / a_safe**3
        + params.Omega_Lambda
    )


def compute_physics_residual(
    model: FriedmannPINN,
    a: torch.Tensor,
    params: CosmologyParams,
) -> torch.Tensor:
    """Compute the physics-informed residual.

    The PINN should satisfy: H_nn(a)^2 = H_analytic(a)^2

    Residual = |H_nn^2 - H_friedmann^2| / H0^2
    """
    a = a.requires_grad_(True)
    h_pred = model(a)
    h2_pred = h_pred ** 2
    h2_true = friedmann_H_squared(a, params)
    residual = (h2_pred - h2_true) / (params.H0**2 + 1e-10)
    return residual


def compute_derivative_residual(
    model: FriedmannPINN,
    a: torch.Tensor,
    params: CosmologyParams,
) -> torch.Tensor:
    """Residual from dH/da consistency.

    From H^2 = H0^2 [Omega_r/a^4 + Omega_m/a^3 + Omega_Lambda], taking d/da:
    2H dH/da = H0^2 [-4 Omega_r/a^5 - 3 Omega_m/a^4]

    So: dH/da = H0^2 / (2H) * [-4 Omega_r/a^5 - 3 Omega_m/a^4]
    """
    a = a.clone().requires_grad_(True)
    H = model(a)

    dH_da = torch.autograd.grad(
        H, a, grad_outputs=torch.ones_like(H),
        create_graph=True, retain_graph=True)[0]

    a_safe = torch.clamp(a, min=1e-6)
    rhs = params.H0**2 / (2.0 * H + 1e-10) * (
        -4.0 * params.Omega_r / a_safe**5
        - 3.0 * params.Omega_m / a_safe**4
    )

    return (dH_da - rhs) / (params.H0 + 1e-10)


# ---------------------------------------------------------------------------
# PINN loss
# ---------------------------------------------------------------------------

def pinn_loss(
    model: FriedmannPINN,
    a_data: torch.Tensor,
    h_data: torch.Tensor,
    a_physics: torch.Tensor,
    params: CosmologyParams,
    lambda_phys: float = 1.0,
    lambda_deriv: float = 0.5,
) -> tuple[torch.Tensor, dict]:
    """Combined PINN loss = data + physics + derivative.

    Parameters
    ----------
    a_data : (N, 1) — data points (scale factors).
    h_data : (N, 1) — observed H values.
    a_physics : (M, 1) — collocation points for physics loss.
    params : cosmological parameters.
    lambda_phys : weight for H^2 residual.
    lambda_deriv : weight for dH/da residual.

    Returns
    -------
    total_loss, components_dict
    """
    h_pred = model(a_data)
    loss_data = F.mse_loss(h_pred, h_data)

    residual = compute_physics_residual(model, a_physics, params)
    loss_physics = residual.pow(2).mean()

    residual_d = compute_derivative_residual(model, a_physics, params)
    loss_deriv = residual_d.pow(2).mean()

    total = loss_data + lambda_phys * loss_physics + lambda_deriv * loss_deriv

    return total, {
        "data": loss_data.item(),
        "physics": loss_physics.item(),
        "derivative": loss_deriv.item(),
        "total": total.item(),
    }


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def generate_friedmann_data(
    params: CosmologyParams | None = None,
    n_data: int = 200,
    n_collocation: int = 500,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate analytic training/collocation data.

    Returns (a_data, H_data, a_collocation).
    """
    if params is None:
        params = CosmologyParams()
    rng = np.random.default_rng(seed)

    a_data = np.sort(rng.uniform(0.01, 1.0, n_data)).astype(np.float32).reshape(-1, 1)
    H_data = np.sqrt(
        params.H0**2 * (
            params.Omega_r / a_data**4
            + params.Omega_m / a_data**3
            + params.Omega_Lambda
        )
    ).astype(np.float32)

    # Add small noise to simulate observational uncertainty
    H_data += rng.normal(0, 0.5, H_data.shape).astype(np.float32)

    a_coll = np.sort(rng.uniform(0.001, 1.0, n_collocation)).astype(np.float32).reshape(-1, 1)

    return a_data, H_data, a_coll


def train_pinn(
    model: FriedmannPINN,
    params: CosmologyParams | None = None,
    n_epochs: int = 2000,
    lr: float = 1e-3,
    lambda_phys: float = 1.0,
    lambda_deriv: float = 0.5,
    n_data: int = 200,
    n_collocation: int = 500,
    seed: int = 42,
    device: str = "cpu",
) -> dict:
    """Train the PINN for Friedmann equations.

    Returns dict with loss history and final metrics.
    """
    if params is None:
        params = CosmologyParams()

    model = model.to(device)

    a_data_np, h_data_np, a_coll_np = generate_friedmann_data(
        params, n_data, n_collocation, seed)

    a_data = torch.from_numpy(a_data_np).to(device)
    h_data = torch.from_numpy(h_data_np).to(device)
    a_coll = torch.from_numpy(a_coll_np).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, n_epochs)

    history = []

    for epoch in range(n_epochs):
        model.train()
        total, components = pinn_loss(
            model, a_data, h_data, a_coll, params,
            lambda_phys, lambda_deriv)

        optimizer.zero_grad()
        total.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        history.append(components)

    # Final evaluation
    model.eval()
    with torch.no_grad():
        H_pred = model(a_data).cpu().numpy().ravel()
    H_true = h_data_np.ravel()
    rel_error = np.abs(H_pred - H_true) / (np.abs(H_true) + 1e-10)

    return {
        "history": history,
        "final_mean_rel_error": float(rel_error.mean()),
        "final_max_rel_error": float(rel_error.max()),
    }


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_pinn(
    model: FriedmannPINN,
    params: CosmologyParams | None = None,
    n_test: int = 1000,
) -> dict:
    """Evaluate PINN accuracy against analytic solution."""
    if params is None:
        params = CosmologyParams()

    a_test = np.linspace(0.01, 1.0, n_test).astype(np.float32).reshape(-1, 1)
    H_true = np.sqrt(
        params.H0**2 * (
            params.Omega_r / a_test**4
            + params.Omega_m / a_test**3
            + params.Omega_Lambda
        )
    ).ravel()

    H_pred = model.predict(a_test)

    rel_error = np.abs(H_pred - H_true) / (H_true + 1e-10)

    return {
        "a": a_test.ravel(),
        "H_true": H_true,
        "H_pred": H_pred,
        "rel_error": rel_error,
        "mean_rel_error": float(rel_error.mean()),
        "max_rel_error": float(rel_error.max()),
    }
