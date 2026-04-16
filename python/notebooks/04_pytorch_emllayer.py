"""
Tutorial 04: PyTorch Integration — EMLLayer vs Standard Activations
====================================================================
Shows how to use EMLLayer as a drop-in activation function in PyTorch models.

Run time: ~1-2 minutes (requires torch)
"""

# %% [markdown]
# # PyTorch Integration
#
# `EMLLayer` provides a drop-in replacement for standard PyTorch activation
# functions (ReLU, GELU, etc.) using the EML expression tree.

# %%
try:
    import torch
    import torch.nn as nn
    import math
    _HAS_TORCH = True
except ImportError:
    print("torch not installed — skipping GPU tutorial")
    print("Install: pip install torch")
    _HAS_TORCH = False

if _HAS_TORCH:
    from monogate import EMLLayer, EMLActivation

    # %% Simple usage
    print("=== EMLLayer basic usage ===\n")

    layer = EMLLayer(in_features=8, out_features=8)
    x = torch.randn(4, 8)  # batch=4, features=8
    y = layer(x)
    print(f"Input shape:  {x.shape}")
    print(f"Output shape: {y.shape}")
    print(f"Output dtype: {y.dtype}")

    # %% As activation in a network
    print("\n=== EMLLayer in a neural network ===\n")

    class MLPWithEML(nn.Module):
        def __init__(self, hidden: int = 64):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(1, hidden),
                EMLActivation(),
                nn.Linear(hidden, hidden),
                EMLActivation(),
                nn.Linear(hidden, 1),
            )

        def forward(self, x):
            return self.net(x)

    model = MLPWithEML(hidden=32)
    x = torch.linspace(-3, 3, 100).unsqueeze(1)
    y = model(x)
    print(f"MLP with EMLActivation: {sum(p.numel() for p in model.parameters())} params")
    print(f"Output shape: {y.shape}")

    # %% EMLTree — symbolic constant fitting
    print("\n=== EMLTree — symbolic regression of constants ===\n")

    from monogate import EMLTree, fit

    # Train to fit π
    torch.manual_seed(42)
    tree = EMLTree(depth=3)
    losses = fit(tree, target=torch.tensor(math.pi),
                 steps=500, lr=1e-2, lam=0.01)  # lam > 0 escapes attractor

    print(f"Target:  π = {math.pi:.8f}")
    print(f"Result:  {tree().item():.8f}")
    print(f"Error:   {abs(tree().item() - math.pi):.2e}")
    print(f"Formula: {tree.formula()}")

    # %% PINN demo
    print("\n=== EMLPINN — physics-informed neural network ===\n")

    try:
        from monogate import EMLPINN, fit_pinn

        # Simple ODE: u'(x) = u(x), u(0) = 1 → solution: u(x) = exp(x)
        pinn = EMLPINN(depth=3, width=16, input_dim=1)
        result = fit_pinn(
            pinn,
            ode_residual=lambda u, x: torch.autograd.grad(u.sum(), x, create_graph=True)[0] - u,
            domain=(-1.0, 1.0),
            bc_points=[(torch.tensor([[0.0]]), torch.tensor([[1.0]]))],
            n_collocation=50,
            steps=200,
            lr=1e-3,
        )
        print(f"PINN training: {result.final_loss:.4e} final loss")
        print(f"Trained on: u'(x) = u(x), u(0) = 1")

    except ImportError:
        print("EMLPINN requires torch (already imported above)")

    print("\n Tutorial 04 complete.")
