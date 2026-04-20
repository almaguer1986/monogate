#!/usr/bin/env python3
# encoding: utf-8
"""
NN-1: SuperBEST routing inside symbolic regression training loop.
Three training variants:
  A: Pure EML head (baseline)
  B: SuperBEST head (16 operators, soft mixture)
  C: SuperBEST head + cost penalty
Task: fit y = sin(x) on [-pi, pi]

SuperBEST v4 costs: exp=1n, ln=1n, recip=1n, neg=2n, mul=2n,
  sub=2n, div=2n, sqrt=2n, pow=3n, add_pos=3n, add_gen=11n
"""

import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ── F16 operators (differentiable, clamped for stability) ─────────────
def op_eml(x, r):
    return torch.exp(x) - torch.log(r.clamp(min=1e-8))

def op_deml(x, r):
    return torch.exp(-x) - torch.log(r.clamp(min=1e-8))

def op_exl(x, r):
    return torch.exp(x) * torch.log(r.clamp(min=1e-8))

def op_edl(x, r):
    ln_r = torch.log(r.clamp(min=1e-8))
    return torch.exp(x) / (ln_r + 1e-8)

def op_eal(x, r):
    return torch.exp(x) + torch.log(r.clamp(min=1e-8))

def op_emn(x, r):
    return torch.log(r.clamp(min=1e-8)) - torch.exp(x)

def op_lead(x, r):
    # LEAd(x, y) = ln(exp(x) + y) — the softplus family
    return torch.log(torch.exp(x.clamp(max=80.0)) + r.clamp(min=1e-8))

def op_elsb(x, r):
    return torch.exp(x.clamp(max=80.0)) / r.clamp(min=1e-8)

OPERATORS = [op_eml, op_deml, op_exl, op_edl, op_eal, op_emn, op_lead, op_elsb]
OPERATOR_NAMES = ['EML', 'DEML', 'EXL', 'EDL', 'EAL', 'EMN', 'LEAd', 'ELSb']
# SuperBEST v4 costs (each is a single exp-ln family member = 1n base)
OPERATOR_COSTS = [1, 1, 1, 1, 1, 1, 1, 1]


# ── Leaf: linear combination of trunk features ─────────────────────────
class Leaf(nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.w = nn.Parameter(torch.randn(n_features) * 0.1)
        self.b = nn.Parameter(torch.zeros(1))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        # features: (B, n_features)  → (B, 1)
        return (features * self.w).sum(-1, keepdim=True) + self.b


# ── Version A: Pure EML tree ──────────────────────────────────────────
class EMLNode(nn.Module):
    """Recursive EML binary tree; each internal node applies eml(left, right)."""

    def __init__(self, n_features: int, depth: int = 0, max_depth: int = 3):
        super().__init__()
        self.depth = depth
        self.max_depth = max_depth
        if depth < max_depth:
            self.left = EMLNode(n_features, depth + 1, max_depth)
            self.right = EMLNode(n_features, depth + 1, max_depth)
        else:
            self.left = Leaf(n_features)
            self.right = Leaf(n_features)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        l = self.left(features)
        r = self.right(features)
        r_pos = torch.sigmoid(r) + 1e-6
        return torch.exp(l.clamp(max=80.0)) - torch.log(r_pos)


# ── Version B/C: SuperBEST node (learnable operator selection) ─────────
class SuperBESTNode(nn.Module):
    """Each node holds operator logits; forward computes a soft mixture."""

    def __init__(
        self,
        n_features: int,
        n_operators: int,
        depth: int = 0,
        max_depth: int = 3,
    ):
        super().__init__()
        self.n_operators = n_operators
        self.depth = depth
        self.max_depth = max_depth
        self.op_logits = nn.Parameter(torch.zeros(n_operators))

        if depth < max_depth:
            self.left = SuperBESTNode(n_features, n_operators, depth + 1, max_depth)
            self.right = SuperBESTNode(n_features, n_operators, depth + 1, max_depth)
        else:
            self.left = Leaf(n_features)
            self.right = Leaf(n_features)

    def snap(self) -> int:
        """Return index of the highest-probability operator (hard selection)."""
        return int(torch.argmax(self.op_logits).item())

    def forward(self, features: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
        l = self.left(features)
        r = self.right(features)
        r_pos = torch.sigmoid(r) + 1e-6

        op_weights = F.softmax(self.op_logits / temperature, dim=0)  # (n_ops,)

        outputs = []
        for op in OPERATORS[: self.n_operators]:
            out = op(l, r_pos)
            out = torch.nan_to_num(out, nan=0.0, posinf=100.0, neginf=-100.0)
            outputs.append(out)

        stacked = torch.stack(outputs, dim=-1)  # (B, 1, n_ops)
        return (stacked * op_weights).sum(-1)   # (B, 1)


# ── Hybrid model: MLP trunk + symbolic head ───────────────────────────
class HybridModel(nn.Module):
    def __init__(
        self,
        trunk_hidden: int = 64,
        tree_depth: int = 3,
        n_ops: int = 8,
        version: str = 'A',
    ):
        super().__init__()
        self.version = version
        self.trunk = nn.Sequential(
            nn.Linear(1, trunk_hidden),
            nn.ReLU(),
            nn.Linear(trunk_hidden, trunk_hidden),
            nn.ReLU(),
        )
        n_features = trunk_hidden
        if version == 'A':
            self.head = EMLNode(n_features, max_depth=tree_depth)
        else:
            self.head = SuperBESTNode(n_features, n_ops, max_depth=tree_depth)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.trunk(x)          # (B, trunk_hidden)
        return self.head(features)        # (B, 1)


# ── Cost regularisation for version C ─────────────────────────────────
def soft_cost(model: HybridModel) -> torch.Tensor:
    """
    Differentiable expected cost: for each SuperBEST node, compute
    E[cost] = sum_i p_i * c_i where p_i = softmax(logits)[i].
    """
    total = torch.tensor(0.0)
    costs_t = torch.tensor(OPERATOR_COSTS[:model.head.n_operators], dtype=torch.float32)

    def _collect(node):
        nonlocal total
        if isinstance(node, SuperBESTNode):
            probs = F.softmax(node.op_logits, dim=0)
            total = total + (probs * costs_t).sum()
            _collect(node.left)
            _collect(node.right)

    _collect(model.head)
    return total


# ── Training loop ──────────────────────────────────────────────────────
def train_version(
    version: str,
    n_epochs: int = 600,
    lam: float = 0.0,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    np.random.seed(seed)

    x = torch.linspace(-math.pi, math.pi, 1000).unsqueeze(-1)
    y = torch.sin(x)

    model = HybridModel(trunk_hidden=64, tree_depth=3, n_ops=8, version=version)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=n_epochs, eta_min=1e-4)

    history = []
    for epoch in range(n_epochs):
        pred = model(x)
        loss_fit = F.mse_loss(pred, y)
        loss = loss_fit

        if version == 'C' and lam > 0.0:
            loss = loss_fit + lam * soft_cost(model)

        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        scheduler.step()

        if epoch % 100 == 0:
            history.append({'epoch': epoch, 'mse': loss_fit.item()})

    with torch.no_grad():
        pred = model(x)
        final_mse = F.mse_loss(pred, y).item()

    # Operator distribution for versions B and C
    op_dist = None
    if version in ('B', 'C') and isinstance(model.head, SuperBESTNode):
        with torch.no_grad():
            probs = F.softmax(model.head.op_logits, dim=0).tolist()
            op_dist = {OPERATOR_NAMES[i]: round(probs[i], 4) for i in range(len(probs))}

    return {
        'version': version,
        'final_mse': final_mse,
        'history': history,
        'op_distribution': op_dist,
    }


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("NN-1: SuperBEST Routing in the Training Loop")
    print("Task: fit y = sin(x) on [-π, π], 1 000 samples, 600 epochs")
    print("=" * 60)

    results = {}
    for ver, lam, label in [
        ('A', 0.0, 'Pure EML head'),
        ('B', 0.0, 'SuperBEST head (soft mixture)'),
        ('C', 0.005, 'SuperBEST head + cost penalty (λ=0.005)'),
    ]:
        print(f"\nTraining Version {ver}: {label} ...")
        r = train_version(ver, lam=lam)
        results[ver] = r
        print(f"  Final MSE: {r['final_mse']:.6f}")
        if r['op_distribution']:
            top = sorted(r['op_distribution'].items(), key=lambda kv: -kv[1])[:3]
            print(f"  Top operators at root: {top}")

    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"{'Version':<8} {'MSE':>12}  Description")
    print("-" * 60)
    for ver, label in [
        ('A', 'Pure EML head (baseline)'),
        ('B', 'SuperBEST soft mixture'),
        ('C', 'SuperBEST + cost penalty'),
    ]:
        print(f"{ver:<8} {results[ver]['final_mse']:>12.6f}  {label}")

    print()
    print("Notes:")
    print("  - sin(x) has no finite closed-form in the EML algebra,")
    print("    so all variants fit an approximation via the trunk MLP.")
    print("  - SuperBEST (B) typically matches or beats pure EML (A)")
    print("    because additional operators span a richer function class.")
    print("  - Cost penalty (C) may slightly increase MSE for a cheaper tree.")
    print("  - Real symbolic extraction would anneal temperature → 0 and")
    print("    snap each node to its argmax operator.")
