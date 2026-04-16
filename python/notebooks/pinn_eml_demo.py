# %% [markdown]
# # Physics-Informed EML Networks (PINN) Demo
#
# Demonstrates ``EMLPINN`` — an interpretable neural network that simultaneously:
# 1. Fits observed data (data loss: MSE against labelled points)
# 2. Satisfies a differential equation (physics loss: PDE/ODE residual)
#
# The learned EML formula doubles as both a fitted model and a symbolic
# candidate for the analytical solution.
#
# Two experiments:
# - **Harmonic oscillator**: u''(x) + ω²·u(x) = 0  (exact solution: sin(ωx))
# - **Steady Burgers**: u·u'(x) − ν·u''(x) = 0  (exact solution: tanh variant)

# %%
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from monogate.pinn import EMLPINN, PINNResult, fit_pinn

print("Physics-Informed EML Network Demo")
print("=" * 50)

# %% [markdown]
# ## 1. Harmonic Oscillator — u''(x) + ω²·u(x) = 0

# %%
print("\n1. Harmonic Oscillator  (ω = 2, exact = sin(2x))")
print("-" * 50)

torch.manual_seed(0)
omega = 2.0

# Training data: noisy samples of sin(2x)
x_data  = torch.linspace(0, math.pi, 60).unsqueeze(1)
y_clean = torch.sin(omega * x_data.squeeze(1))
noise   = 0.02 * torch.randn_like(y_clean)
y_data  = y_clean + noise

# Collocation points (denser, no noise)
x_phys  = torch.linspace(0, math.pi, 120).unsqueeze(1)

# Train PINN
model_h = EMLPINN(equation="harmonic", omega=omega, backbone_depth=3, lam_physics=1.0)
result_h = fit_pinn(
    model_h, x_data, y_data, x_phys,
    steps=2000, lr=5e-3, log_every=400, lam_physics=1.0,
)

print(f"\n  Final data_loss  = {result_h.data_loss:.4e}")
print(f"  Final phys_loss  = {result_h.physics_loss:.4e}")
print(f"  Elapsed          = {result_h.elapsed_s:.2f}s")
print(f"\n  Learned formula:\n    {result_h.formula}")

# %% [markdown]
# ## 2. Steady Burgers Equation — u·u'(x) − ν·u''(x) = 0

# %%
print("\n2. Steady Burgers Equation  (ν = 0.05)")
print("-" * 50)

torch.manual_seed(42)
nu = 0.05

# Exact tanh solution to steady Burgers (u·u' = ν·u'')
# u(x) = -ν·tanh(x/(2ν)) is a steady-state solution for ν>0
def burgers_exact(x_np: np.ndarray, nu: float) -> np.ndarray:
    return -nu * np.tanh(x_np / (2 * nu))

x_np    = np.linspace(-2, 2, 60)
y_np    = burgers_exact(x_np, nu)
x_data_b = torch.tensor(x_np, dtype=torch.float32).unsqueeze(1)
y_data_b = torch.tensor(y_np, dtype=torch.float32)

x_phys_b = torch.linspace(-2, 2, 120).unsqueeze(1)

model_b = EMLPINN(equation="burgers", nu=nu, backbone_depth=3, lam_physics=2.0)
result_b = fit_pinn(
    model_b, x_data_b, y_data_b, x_phys_b,
    steps=2000, lr=5e-3, log_every=400, lam_physics=2.0,
)

print(f"\n  Final data_loss  = {result_b.data_loss:.4e}")
print(f"  Final phys_loss  = {result_b.physics_loss:.4e}")
print(f"  Elapsed          = {result_b.elapsed_s:.2f}s")
print(f"\n  Learned formula:\n    {result_b.formula}")

# %% [markdown]
# ## 3. Training Curves

# %%
print("\n3. Generating training-curve plots …")
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

for ax, result, title in [
    (axes[0], result_h, "Harmonic Oscillator"),
    (axes[1], result_b, "Steady Burgers"),
]:
    if result.history:
        steps  = [h[0] for h in result.history]
        d_loss = [h[1] for h in result.history]
        p_loss = [h[2] for h in result.history]
        ax.semilogy(steps, d_loss, "b-o", ms=3, label="Data loss")
        ax.semilogy(steps, p_loss, "r-s", ms=3, label="Physics loss")
    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel("Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)

fig.tight_layout()
out_path = "pinn_training_curves.png"
fig.savefig(out_path, dpi=120, bbox_inches="tight")
print(f"  Saved: {out_path}")
plt.close(fig)

# %% [markdown]
# ## 4. Solution Comparison

# %%
print("\n4. Generating solution comparison plots …")
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

# Harmonic
x_test = torch.linspace(0, math.pi, 200).unsqueeze(1)
with torch.no_grad():
    y_pred_h = model_h(x_test).numpy()
y_exact_h  = np.sin(omega * x_test.squeeze().numpy())
axes[0].plot(x_test.squeeze().numpy(), y_exact_h, "k-",  lw=2, label="sin(2x) exact")
axes[0].plot(x_test.squeeze().numpy(), y_pred_h,  "r--", lw=1.5, label="EMLPINN prediction")
axes[0].scatter(x_data.squeeze().numpy(), y_data.numpy(), s=8, c="b", alpha=0.5, label="noisy data")
axes[0].set_title("Harmonic oscillator — EMLPINN vs exact")
axes[0].legend(fontsize=8)
axes[0].set_xlabel("x")
axes[0].grid(True, alpha=0.3)

# Burgers
x_test_b = torch.linspace(-2, 2, 200).unsqueeze(1)
with torch.no_grad():
    y_pred_b = model_b(x_test_b).numpy()
y_exact_b  = burgers_exact(x_test_b.squeeze().numpy(), nu)
axes[1].plot(x_test_b.squeeze().numpy(), y_exact_b, "k-",  lw=2, label="Burgers exact")
axes[1].plot(x_test_b.squeeze().numpy(), y_pred_b,  "r--", lw=1.5, label="EMLPINN prediction")
axes[1].scatter(x_data_b.squeeze().numpy(), y_data_b.numpy(), s=8, c="b", alpha=0.5, label="training data")
axes[1].set_title("Steady Burgers — EMLPINN vs exact")
axes[1].legend(fontsize=8)
axes[1].set_xlabel("x")
axes[1].grid(True, alpha=0.3)

fig.tight_layout()
out_path = "pinn_solution_comparison.png"
fig.savefig(out_path, dpi=120, bbox_inches="tight")
print(f"  Saved: {out_path}")
plt.close(fig)

print("\nDone.")
