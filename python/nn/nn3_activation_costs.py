#!/usr/bin/env python3
# encoding: utf-8
"""
NN-3: SuperBEST v4 costs for neural network computations.

SuperBEST v4 cost table:
  exp=1n, ln=1n, recip=1n
  neg=2n, mul=2n, sub=2n, div=2n, sqrt=2n
  pow=3n, add_pos=3n
  add_gen=11n  (addition where sign of args unknown)

We compute costs for:
  - Standard activation functions (sigmoid, tanh, GELU, softplus, swish, EML)
  - Dense layers with each activation
  - Single-head attention (seq_len × dim)
  - Layer normalisation (width N)
  - Cross-entropy loss (N classes)
  - Transformer block (embed dim D, seq len L, ff_mul = 4)
"""

import sys

# Ensure UTF-8 output on Windows (avoids cp1252 encode errors for special chars)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ── Cost constants ─────────────────────────────────────────────────────
COST = {
    'exp': 1, 'ln': 1, 'recip': 1,
    'neg': 2, 'mul': 2, 'sub': 2, 'div': 2, 'sqrt': 2,
    'pow': 3, 'add_pos': 3, 'add_gen': 11,
}


# ── Activation costs ───────────────────────────────────────────────────
def cost_sigmoid() -> int:
    """
    sigmoid(x) = 1 / (1 + exp(-x))
    Steps: neg(x)=2n, exp(neg)=1n, add_pos(1, exp)=3n, recip=1n
    Total: 2+1+3+1 = 7n
    """
    return COST['neg'] + COST['exp'] + COST['add_pos'] + COST['recip']


def cost_tanh() -> int:
    """
    tanh(x) = (exp(2x) - 1) / (exp(2x) + 1)
    Steps: mul(2,x)=2n, exp(2x)=1n, sub(exp,1)=2n, add_pos(exp,1)=3n, div=2n
    Total: 2+1+2+3+2 = 10n
    Note: sub uses 'sub' cost even though 1 is positive, because the
    result exp(2x)-1 can be negative near x=0.
    """
    return COST['mul'] + COST['exp'] + COST['sub'] + COST['add_pos'] + COST['div']


def cost_gelu() -> int:
    """
    GELU(x) ≈ x * sigmoid(1.702 * x)   [Hendrycks fast approx]
    Steps: mul(1.702, x)=2n, sigmoid=7n, mul(x, sig)=2n
    Total: 2+7+2 = 11n
    """
    return COST['mul'] + cost_sigmoid() + COST['mul']


def cost_softplus() -> int:
    """
    softplus(x) = ln(1 + exp(x)) = LEAd(x, 1)
    LEAd is a single base operator in the EML family: 1n.
    This is the ONLY standard smooth activation that is a SINGLE node.
    """
    return COST['ln']  # LEAd counts as 1n (it IS ln(exp(x)+y))


def cost_swish() -> int:
    """
    Swish(x) = x * sigmoid(x)
    Steps: sigmoid=7n, mul(x, sigmoid)=2n
    Total: 7+2 = 9n
    """
    return cost_sigmoid() + COST['mul']


def cost_relu() -> str:
    """ReLU is not in the EML algebra (discontinuous derivative at 0)."""
    return "N/A (not EML)"


def cost_eml_neuron() -> int:
    """
    EML neuron: exp(w·x + b)
    Steps (single input for clarity): mul(w,x)=2n, add_gen(mul,b)=11n, exp=1n
    But for dot products, we compute the linear combination first then exp:
    The exp alone on top of a precomputed linear = 1n per neuron.
    We report the marginal cost of the EML nonlinearity: 1n.
    """
    return COST['exp']


# ── Layer costs ────────────────────────────────────────────────────────
def cost_dot_product(d_in: int) -> int:
    """
    Dot product of two d_in-dimensional vectors.
    = (d_in) multiplications + (d_in - 1) additions (positive partial sums)
    Cost: d_in * mul + (d_in-1) * add_pos
    """
    return d_in * COST['mul'] + (d_in - 1) * COST['add_pos']


def cost_linear_neuron(d_in: int) -> int:
    """
    Single neuron linear transform: dot(w, x) + b
    = dot_product(d_in) + add_gen (bias can make result any sign)
    """
    return cost_dot_product(d_in) + COST['add_gen']


def cost_dense_layer(d_in: int, d_out: int, act_cost: int) -> int:
    """Full dense layer: d_out neurons each computing linear + activation."""
    per_neuron = cost_linear_neuron(d_in) + act_cost
    return d_out * per_neuron


# ── Attention cost ─────────────────────────────────────────────────────
def cost_softmax(n: int) -> int:
    """
    Softmax over a vector of length n.
    = n exp + (n-1) add_pos (sum of positives) + n div
    """
    return n * COST['exp'] + (n - 1) * COST['add_pos'] + n * COST['div']


def cost_attention(seq_len: int, d_model: int) -> int:
    """
    Single-head attention, no projection matrices (bare QKV already computed).
    QK^T:       seq_len × seq_len dot products of dim d_model
    Scale 1/sqrt(d): sqrt once + seq_len^2 multiplications
    Softmax:    seq_len rows each of length seq_len
    A·V:        seq_len × d_model dot products of dim seq_len
    """
    n, d = seq_len, d_model

    qkt = n * n * cost_dot_product(d)
    scale = COST['sqrt'] + n * n * COST['mul']
    softmax = n * cost_softmax(n)
    av = n * d * cost_dot_product(n)

    return qkt + scale + softmax + av


# ── Layer norm ─────────────────────────────────────────────────────────
def cost_layer_norm(width: int) -> int:
    """
    LayerNorm(x, γ, β) = γ * (x - μ) / sqrt(σ² + ε) + β

    mean μ:         (width-1) add_gen + 1 div
    variance σ²:    width * (sub + pow) + (width-1) add_pos + div
    sqrt(σ²+ε):     add_pos + sqrt
    normalize:      width * (sub + div)
    affine:         width * (mul + add_gen)
    """
    N = width

    mean_cost = (N - 1) * COST['add_gen'] + COST['div']
    # x_i - mu can be negative, pow(x,2) is fine; sum of squares is positive
    var_cost = N * (COST['sub'] + COST['pow']) + (N - 1) * COST['add_pos'] + COST['div']
    sqrt_var = COST['add_pos'] + COST['sqrt']
    normalize = N * (COST['sub'] + COST['div'])
    affine = N * (COST['mul'] + COST['add_gen'])

    return mean_cost + var_cost + sqrt_var + normalize + affine


# ── Cross-entropy ──────────────────────────────────────────────────────
def cost_cross_entropy(n_classes: int) -> int:
    """
    CE = -ln(softmax(logits)[target])
    = -(logit_t - ln(sum_k exp(logit_k)))
    = ln(sum_k exp(logit_k)) - logit_t

    Steps:
      N exp (one per class):          N * 1n  =  N
      (N-1) add_pos to sum positives: (N-1)*3n = 3N-3
      1 ln (on the sum):              1n       =  1
      1 sub (minus logit_t):          2n       =  2
    Total = N + 3N - 3 + 1 + 2 = 4N
    """
    N = n_classes
    return N * COST['exp'] + (N - 1) * COST['add_pos'] + COST['ln'] + COST['sub']


# ── Transformer block ─────────────────────────────────────────────────
def cost_transformer_block(
    d_model: int, seq_len: int, ff_mul: int = 4, act_name: str = 'softplus'
) -> dict:
    """
    One transformer block (self-attention + FFN), no projection weight ops.
    We count only the arithmetic of the operations, not the weight matrices
    (those are standard matmuls accounted separately).
    """
    act_costs = {
        'softplus': cost_softplus(),
        'gelu': cost_gelu(),
        'swish': cost_swish(),
        'sigmoid': cost_sigmoid(),
    }
    act_cost = act_costs.get(act_name, cost_softplus())

    attn = cost_attention(seq_len, d_model)
    ln1 = seq_len * cost_layer_norm(d_model)
    ff1 = seq_len * cost_dense_layer(d_model, d_model * ff_mul, act_cost)
    ff2 = seq_len * cost_dense_layer(d_model * ff_mul, d_model, 0)  # linear only
    ln2 = seq_len * cost_layer_norm(d_model)

    return {
        'attention': attn,
        'layer_norm_1': ln1,
        'ffn_layer_1': ff1,
        'ffn_layer_2': ff2,
        'layer_norm_2': ln2,
        'total': attn + ln1 + ff1 + ff2 + ln2,
        'activation': act_name,
        'act_cost_n': act_cost,
    }


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 65)
    print("NN-3: SuperBEST v4 Cost Analysis for Neural Network Operations")
    print("=" * 65)

    # 1. Activation function costs
    print("\n--- Activation Function Costs ---")
    print(f"{'Activation':15}  {'Cost':>6}  Formula / Decomposition")
    print("-" * 65)
    print(f"{'ReLU':15}  {'N/A':>6}  Not EML — discontinuous derivative at 0")
    print(f"{'Sigmoid':15}  {cost_sigmoid():>5}n  neg(2) + exp(1) + add_pos(3) + recip(1)")
    print(f"{'Tanh':15}  {cost_tanh():>5}n  mul(2) + exp(1) + sub(2) + add_pos(3) + div(2)")
    print(f"{'GELU':15}  {cost_gelu():>5}n  mul(2) + sigmoid(7) + mul(2)")
    print(f"{'Swish':15}  {cost_swish():>5}n  sigmoid(7) + mul(2)")
    print(f"{'Softplus':15}  {cost_softplus():>5}n  LEAd(x, 1) — single EML operator!")
    print(f"{'EML neuron':15}  {cost_eml_neuron():>5}n  exp(linear) — marginal cost of the nonlinearity")

    # 2. Dense layer costs
    print("\n--- Dense Layer Costs (forward pass only) ---")
    configs = [(784, 256), (256, 128), (128, 10)]
    act_list = [
        ('Softplus', cost_softplus()),
        ('Sigmoid',  cost_sigmoid()),
        ('GELU',     cost_gelu()),
        ('Swish',    cost_swish()),
    ]

    print(f"{'Layer':15}  " + "  ".join(f"{name:>12}" for name, _ in act_list))
    print("-" * 70)
    for d_in, d_out in configs:
        row = [f"({d_in}→{d_out})"]
        for _, ac in act_list:
            row.append(f"{cost_dense_layer(d_in, d_out, ac):>12,}")
        print(f"{row[0]:15}  " + "  ".join(row[1:]))

    # 3. Attention costs
    print("\n--- Single-Head Attention Costs ---")
    print(f"{'(seq, dim)':15}  {'Cost':>14}n")
    print("-" * 35)
    for seq, dim in [(32, 64), (64, 64), (128, 64), (512, 64), (128, 512)]:
        c = cost_attention(seq, dim)
        print(f"({seq:>4}, {dim:>4})       {c:>14,}n")

    # 4. Layer norm costs
    print("\n--- Layer Normalisation Costs ---")
    print(f"{'Width N':>10}  {'Cost':>10}n")
    print("-" * 25)
    for N in [64, 128, 256, 512, 768, 1024]:
        print(f"{N:>10}  {cost_layer_norm(N):>10,}n")

    # 5. Cross-entropy
    print("\n--- Cross-Entropy Loss Costs ---")
    print(f"{'N classes':>12}  {'Cost (6N-1)':>14}n")
    print("-" * 32)
    for N in [2, 10, 100, 1000, 32000]:
        c = cost_cross_entropy(N)
        expected = 4 * N
        assert c == expected, f"Formula mismatch for N={N}: {c} vs {expected}"
        print(f"{N:>12}  {c:>14,}n  (= 4×{N} = N*exp + (N-1)*add_pos + ln + sub)")

    # 6. Transformer block
    print("\n--- Transformer Block Costs (seq=128, d=512, ff_mul=4) ---")
    for act in ['softplus', 'gelu', 'swish']:
        tb = cost_transformer_block(d_model=512, seq_len=128, ff_mul=4, act_name=act)
        print(f"\n  Activation: {act} ({tb['act_cost_n']}n per unit)")
        for k, v in tb.items():
            if k not in ('activation', 'act_cost_n'):
                print(f"    {k:20}: {v:>14,}n")

    # 7. Key headline
    print("\n" + "=" * 65)
    print("HEADLINE: Softplus = 1n = LEAd is the cheapest smooth activation")
    print("=" * 65)
    print()
    ratio_gelu = cost_gelu() / cost_softplus()
    ratio_sigmoid = cost_sigmoid() / cost_softplus()
    ratio_swish = cost_swish() / cost_softplus()
    print(f"  Softplus : {cost_softplus()}n  (LEAd — single EML-family operator)")
    print(f"  Sigmoid  : {cost_sigmoid()}n  ({ratio_sigmoid:.0f}× more expensive than softplus)")
    print(f"  Swish    : {cost_swish()}n  ({ratio_swish:.0f}× more expensive than softplus)")
    print(f"  GELU     : {cost_gelu()}n  ({ratio_gelu:.0f}× more expensive than softplus)")
    print()
    print("  For EML-hardware-aware model design, replacing GELU/Swish")
    print("  with Softplus reduces activation cost by 9-10× per neuron.")
    print("  Quality impact is minimal for most tasks (Softplus ≈ GELU")
    print("  and is exactly the primitive the hardware executes natively).")
