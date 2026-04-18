"""
Session 119 — Transformer Architecture: EML Dissection

Softmax attention, positional encodings, layer normalization, residual streams,
scaling laws, and emergent capabilities classified by EML depth.

Key theorem: Softmax attention is EML-1 per token (exp normalization = EML-1
ground state of attention). Positional encoding sin/cos is EML-3. Layer norm
is EML-2 (variance normalization). Residual stream addition preserves depth.
Emergent capabilities at scale are EML-∞ phase transitions in loss landscape.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field

EML_INF = float("inf")


@dataclass
class SoftmaxAttention:
    """
    Scaled dot-product attention: Attn(Q,K,V) = softmax(QKᵀ/√d)·V

    EML structure:
    - Score: s_ij = qᵢ·kⱼ/√d_k: EML-2 (inner product = bilinear = EML-2)
    - Softmax: p_ij = exp(s_ij)/Σ_j exp(s_ij): EML-1 (Boltzmann normalization)
    - Output: oᵢ = Σ_j p_ij·vⱼ: EML-1 (convex combination = EML-1 weighted avg)
    - Attention entropy: H = -Σ_j p_ij log p_ij: EML-2 (Shannon entropy of attention)
    - Causal mask: -∞ for future tokens → EML-0 (binary mask = EML-0)
    - Multi-head: concat + project → EML-2 (linear combination of EML-1 heads)
    """

    d_model: int = 64
    n_heads: int = 8

    @property
    def d_k(self) -> int:
        return self.d_model // self.n_heads

    def attention_scores(self, seq_len: int = 4) -> dict:
        """Simulate uniform attention scores and compute softmax."""
        import math
        scores = [1.0 / math.sqrt(self.d_k)] * seq_len
        exp_s = [math.exp(s) for s in scores]
        Z = sum(exp_s)
        probs = [e / Z for e in exp_s]
        entropy = -sum(p * math.log(p) for p in probs)
        return {
            "seq_len": seq_len,
            "d_k": self.d_k,
            "scores": [round(s, 4) for s in scores],
            "softmax_probs": [round(p, 4) for p in probs],
            "attention_entropy_nats": round(entropy, 4),
            "max_entropy_nats": round(math.log(seq_len), 4),
            "eml_score": 2,
            "eml_softmax": 1,
            "eml_entropy": 2,
            "reason": (
                "Score qᵢ·kⱼ/√d = EML-2 (inner product). "
                "Softmax exp(s)/Σexp = EML-1 (Boltzmann). "
                "Entropy -Σp·log p = EML-2."
            ),
        }

    def multihead_eml(self, n_heads: int = 8) -> dict:
        """Multi-head attention EML depth analysis."""
        return {
            "n_heads": n_heads,
            "per_head_eml": 1,
            "concat_projection_eml": 2,
            "combined_eml": 2,
            "reason": (
                "Each head = EML-1 (Boltzmann softmax). "
                "Concatenation + linear projection = EML-2 (linear combination of EML-1)."
            ),
        }

    def flash_attention_eml(self) -> dict:
        """FlashAttention (numerically stable): same EML depth as standard."""
        return {
            "algorithm": "FlashAttention (tiled)",
            "eml": 1,
            "reason": (
                "FlashAttention computes identical output to standard softmax attention "
                "via tiled reduction — EML depth unchanged: EML-1 (numerically stable log-sum-exp)."
            ),
        }

    def to_dict(self) -> dict:
        return {
            "attention_scores": [self.attention_scores(n) for n in [2, 4, 8, 16]],
            "multihead": self.multihead_eml(),
            "flash_attention": self.flash_attention_eml(),
            "eml_attention_score": 2,
            "eml_softmax_normalized": 1,
            "eml_multihead_output": 2,
        }


@dataclass
class PositionalEncoding:
    """
    Sinusoidal PE: PE(pos, 2i) = sin(pos/10000^{2i/d})
                   PE(pos, 2i+1) = cos(pos/10000^{2i/d})

    EML structure:
    - Base: 10000^{2i/d} = exp(2i/d · ln 10000): EML-2 (exp of rational × log)
    - sin/cos of this: EML-3 (trig of EML-2 argument = EML-3)
    - RoPE (Rotary PE): complex rotation exp(imθ_i): EML-3 (same depth)
    - ALiBi (linear bias): position bias = -m·|i-j|: EML-0 (linear ramp = EML-0)
    - Learned PE: lookup table → EML-0 (tabulated constants)
    """

    d_model: int = 64

    def sinusoidal(self, pos: int, d_model: int = 64) -> dict:
        """Compute sinusoidal PE for position pos."""
        dims = list(range(0, min(d_model, 8), 2))
        pe = {}
        for i in dims:
            freq = math.exp(-i / d_model * math.log(10000.0))
            pe[f"sin_dim_{i}"] = round(math.sin(pos * freq), 6)
            pe[f"cos_dim_{i+1}"] = round(math.cos(pos * freq), 6)
        return {
            "pos": pos,
            "d_model": d_model,
            "pe_sample": pe,
            "eml": 3,
            "reason": (
                "sin(pos / 10000^{2i/d}): argument = pos·exp(-2i/d·ln10000) = EML-2, "
                "sin of EML-2 = EML-3."
            ),
        }

    def rope_encoding(self, pos: int, dim: int = 0, theta: float = 10000.0) -> dict:
        """Rotary Position Embedding: exp(i·pos·θ_dim)."""
        freq = theta ** (-2 * dim / self.d_model)
        angle = pos * freq
        return {
            "pos": pos,
            "dim": dim,
            "angle_rad": round(angle, 6),
            "cos_component": round(math.cos(angle), 6),
            "sin_component": round(math.sin(angle), 6),
            "eml": 3,
            "reason": "RoPE: exp(i·pos·θ^{-2i/d}): EML-3 (complex exponential of EML-2 frequency).",
        }

    def alibi_bias(self, i: int, j: int, slope_m: float = 1.0) -> dict:
        """ALiBi: attention bias = -m·|i-j|."""
        bias = -slope_m * abs(i - j)
        return {
            "i": i, "j": j,
            "bias": bias,
            "eml": 0,
            "reason": "ALiBi bias = -m|i-j|: linear ramp = EML-0 (affine function, no exp/log).",
        }

    def to_dict(self) -> dict:
        return {
            "sinusoidal": [self.sinusoidal(pos) for pos in [0, 1, 5, 10, 100]],
            "rope": [self.rope_encoding(pos) for pos in [0, 1, 5, 10]],
            "alibi": [self.alibi_bias(i, j) for i, j in [(0, 1), (0, 5), (3, 7)]],
            "eml_sinusoidal": 3,
            "eml_rope": 3,
            "eml_alibi": 0,
            "eml_learned_pe": 0,
        }


@dataclass
class LayerNormResidual:
    """
    Layer normalization and residual stream.

    EML structure:
    - LayerNorm: x̂ = (x - μ)/σ · γ + β where μ,σ = E[x],Std[x]: EML-2
      (variance = EML-2 quadratic; sqrt of EML-2 = EML-2; division by EML-2 = EML-2)
    - Residual connection: x + sublayer(x): EML-depth(sublayer) (addition preserves max depth)
    - FFN: W₂·ReLU(W₁·x + b₁) + b₂: EML-∞ (ReLU not EML-finite in general; but
      two-layer FFN with smooth activations = EML-2)
    - GELU: x·Φ(x) = x·½(1+erf(x/√2)): EML-3 (erf = EML-3)
    - SwiGLU: x·σ(Wₓ)·(Wx): EML-2 (sigmoid = EML-1, product = EML-2)
    """

    eps: float = 1e-6

    def layer_norm(self, x: list[float]) -> dict:
        """LayerNorm: normalize to zero mean, unit variance."""
        n = len(x)
        mu = sum(x) / n
        var = sum((xi - mu) ** 2 for xi in x) / n
        std = math.sqrt(var + self.eps)
        x_hat = [(xi - mu) / std for xi in x]
        return {
            "x": x,
            "mu": round(mu, 4),
            "sigma": round(std, 4),
            "x_hat": [round(v, 4) for v in x_hat],
            "eml": 2,
            "reason": "LayerNorm: variance=EML-2 (quadratic), sqrt(var)=EML-2, (x-mu)/sigma=EML-2.",
        }

    def gelu_activation(self, x: float) -> dict:
        """GELU: x·Φ(x) ≈ x·σ(1.702·x)."""
        approx = x * (1 / (1 + math.exp(-1.702 * x)))
        exact_erf_approx = x * 0.5 * (1 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))
        return {
            "x": x,
            "gelu_approx": round(approx, 6),
            "gelu_tanh": round(exact_erf_approx, 6),
            "eml": 3,
            "reason": "GELU = x·Φ(x): erf(x/√2) = EML-3 (error function = EML-3 power series).",
        }

    def swiglu_activation(self, x: float, gate: float) -> dict:
        """SwiGLU: x·σ(gate)."""
        sigma = 1 / (1 + math.exp(-gate))
        out = x * sigma
        return {
            "x": x, "gate": gate,
            "sigma_gate": round(sigma, 6),
            "swiglu_out": round(out, 6),
            "eml": 2,
            "reason": "SwiGLU: σ(gate)=EML-1, x·σ(gate)=EML-2 (product of EML-1 with linear).",
        }

    def residual_depth(self, sublayer_eml: int) -> dict:
        """x + sublayer(x): depth = max(1, sublayer_eml)."""
        return {
            "sublayer_eml": sublayer_eml,
            "residual_eml": max(1, sublayer_eml),
            "reason": "Residual x + f(x): depth = max(depth(x)=1, depth(f)) = depth(f) for f nontrivial.",
        }

    def to_dict(self) -> dict:
        test_vecs = [[1.0, 2.0, 3.0, 4.0], [-1.0, 0.0, 1.0, 2.0]]
        return {
            "layer_norm": [self.layer_norm(v) for v in test_vecs],
            "gelu": [self.gelu_activation(x) for x in [-2.0, -1.0, 0.0, 1.0, 2.0]],
            "swiglu": [self.swiglu_activation(x, g) for x, g in [(1.0, 2.0), (0.5, -1.0), (2.0, 0.0)]],
            "residual": [self.residual_depth(k) for k in [1, 2, 3]],
            "eml_layernorm": 2,
            "eml_gelu": 3,
            "eml_swiglu": 2,
            "eml_relu": "∞ (EML-∞: not EML-finite as analytic function)",
            "eml_residual": "depth(sublayer)",
        }


@dataclass
class ScalingLaws:
    """
    Neural scaling laws and emergent capabilities.

    EML structure:
    - Chinchilla loss: L(N,D) = E + A/N^α + B/D^β: EML-2 (power law in N,D)
      where E=irreducible entropy floor, α≈0.34, β≈0.28
    - Training compute: C ≈ 6·N·D: EML-0 (linear)
    - Optimal N given C: N* = (αA/βB)^{1/(α+β)} · C^{1/(α+β)}: EML-2 (power of C)
    - Emergent capabilities: tasks with step-function accuracy vs scale → EML-∞
    - Grokking: delayed generalization after memorization → EML-∞ phase transition
    - In-context learning: few-shot accuracy vs n_shots → EML-2 (improves ~log n_shots)
    """

    E: float = 1.69
    A: float = 406.4
    B: float = 410.7
    alpha: float = 0.34
    beta: float = 0.28

    def chinchilla_loss(self, N: float, D: float) -> dict:
        """L(N,D) = E + A/N^α + B/D^β."""
        L = self.E + self.A / (N ** self.alpha) + self.B / (D ** self.beta)
        return {
            "N_params": N,
            "D_tokens": D,
            "L": round(L, 4),
            "irreducible_E": self.E,
            "param_term": round(self.A / (N ** self.alpha), 4),
            "data_term": round(self.B / (D ** self.beta), 4),
            "eml": 2,
            "reason": "L(N,D) = E + A/N^α + B/D^β: power laws in N,D = EML-2.",
        }

    def optimal_allocation(self, C: float) -> dict:
        """Chinchilla: N* ≈ (C/6)^{0.5}, D* ≈ (C/6)^{0.5} (simplified equal split)."""
        tokens_per_param = self.alpha / self.beta * (self.B / self.A) ** ((self.alpha + self.beta) / self.alpha)
        N_opt = (C / 6) ** 0.5
        D_opt = (C / 6) ** 0.5 * tokens_per_param
        return {
            "compute_flops": C,
            "N_optimal_approx": round(N_opt, 0),
            "D_optimal_approx": round(D_opt, 0),
            "tokens_per_param": round(tokens_per_param, 2),
            "eml": 2,
            "reason": "N* ~ C^{1/2}: power law in C = EML-2.",
        }

    def emergent_capability(self, model_size: float, threshold: float = 7e9) -> dict:
        """Step-function emergence: accuracy jumps near threshold scale."""
        accuracy_proxy = 0.0 if model_size < threshold * 0.5 else (
            0.5 if model_size < threshold else 0.9
        )
        return {
            "model_size": model_size,
            "threshold": threshold,
            "accuracy_proxy": accuracy_proxy,
            "eml": EML_INF,
            "regime": "pre-emergence" if model_size < threshold else "emergent",
            "reason": (
                "Emergent capabilities: step-function accuracy vs scale = EML-∞ phase transition "
                "(discontinuous jump in capability = non-analytic EML-∞ event)."
            ),
        }

    def grokking_eml(self) -> dict:
        """Grokking: delayed generalization after overfit memorization."""
        return {
            "phase_1": "memorization (overfit): EML-2 loss curve",
            "phase_2": "delayed generalization: EML-∞ transition",
            "eml_transition": "∞",
            "reason": (
                "Grokking exhibits a sharp phase transition from memorization to generalization "
                "at a critical training duration — EML-∞ (non-analytic in training step)."
            ),
        }

    def to_dict(self) -> dict:
        sizes = [(1e8, 2e9), (1e9, 2e10), (7e9, 1.4e11), (7e10, 1.4e12)]
        return {
            "chinchilla_loss": [self.chinchilla_loss(N, D) for N, D in sizes],
            "optimal_allocation": [self.optimal_allocation(C) for C in [1e18, 1e21, 1e24]],
            "emergent_capabilities": [self.emergent_capability(s) for s in [1e8, 1e9, 7e9, 7e10]],
            "grokking": self.grokking_eml(),
            "eml_scaling_law": 2,
            "eml_optimal_compute": 2,
            "eml_emergence": "∞",
            "eml_grokking": "∞",
        }


def analyze_transformer_eml() -> dict:
    attn = SoftmaxAttention()
    pe = PositionalEncoding()
    ln = LayerNormResidual()
    sl = ScalingLaws()
    return {
        "session": 119,
        "title": "Transformer Architecture: EML Dissection",
        "key_theorem": {
            "theorem": "EML Transformer Depth Theorem",
            "statement": (
                "Softmax attention is EML-1 per token (Boltzmann normalization = EML-1 ground state). "
                "Attention score QKᵀ/√d is EML-2 (inner product). "
                "Sinusoidal/RoPE positional encoding is EML-3 (trig of EML-2 frequency). "
                "ALiBi positional bias is EML-0 (linear ramp). "
                "LayerNorm is EML-2 (variance normalization). "
                "GELU activation is EML-3 (erf = EML-3). "
                "SwiGLU is EML-2. "
                "Chinchilla scaling laws L(N,D) ~ N^{-α} are EML-2 (power laws). "
                "Emergent capabilities at scale are EML-∞ phase transitions. "
                "The transformer is an architecture whose ground-state operation is EML-1 "
                "(softmax attention) with EML-3 positional structure and EML-∞ phase transitions at scale."
            ),
        },
        "softmax_attention": attn.to_dict(),
        "positional_encoding": pe.to_dict(),
        "layer_norm_residual": ln.to_dict(),
        "scaling_laws": sl.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Causal mask (binary); ALiBi bias (linear); learned PE (lookup); compute C=6ND (linear)",
            "EML-1": "Softmax attention normalization exp(s)/Σexp (Boltzmann); coherent state output (weighted avg)",
            "EML-2": "Attention score QKᵀ/√d (inner product); LayerNorm (variance); SwiGLU; scaling law L~N^{-α}",
            "EML-3": "Sinusoidal PE sin(pos/10000^{2i/d}); RoPE exp(i·pos·θ); GELU activation (erf = EML-3)",
            "EML-∞": "Emergent capabilities (step-function vs scale); grokking (delayed generalization); loss landscape phase transitions",
        },
        "rabbit_hole_log": [
            "Softmax attention is EML-1: it is the Boltzmann distribution over keys given a query temperature. This is the thermodynamic equilibrium state of an associative memory. The transformer rediscovered Hopfield networks' EML-1 ground state — the retrieval operation of dense associative memory is exp(Q·Kᵀ/β)/Z, identical to softmax with β=1/√d_k. The EML-1 depth of attention is the same depth as the Gibbs distribution in statistical physics.",
            "Sinusoidal PE is EML-3: the frequencies 1/10000^{2i/d} = exp(-2i/d · ln10000) are EML-2 (exp of rational × log), and sin/cos of EML-2 arguments = EML-3. This connects to the Fourier basis (Session 37): sinusoidal PE is a learned Fourier basis for sequence position. RoPE is EML-3 for the same reason — it encodes position as complex phase rotation.",
            "The scaling law L(N,D) = E + A/N^α + B/D^β is EML-2: power laws in N and D. The Chinchilla result N*~D*/20 means optimal compute splits equally between parameters and data. The EML-2 structure of the scaling law predicts that model loss is a power-law function of scale — the same EML-2 universality as neural avalanches (S118), LFP 1/f noise (S118), and Zipf's law (S106). Scale-free structure is EML-2.",
            "Emergent capabilities are EML-∞ phase transitions: accuracy on benchmark tasks (e.g., few-shot arithmetic) jumps from near-chance to near-perfect over a narrow range of model scale. This is the same EML-∞ structure as the Ising critical point (S57), epidemic threshold R₀=1 (S113), laser threshold (S116), and neural criticality σ=1 (S118). The deep unity: all phase transitions are EML-∞, whether in physics, biology, epidemiology, or AI.",
        ],
        "connections": {
            "to_session_118": "Neural criticality (EML-∞ at σ=1) = emergent capability in transformers (EML-∞ at scale threshold). Both are phase transitions.",
            "to_session_57": "Softmax = Boltzmann distribution = same EML-1 ground state as Gibbs ensemble in statistical mechanics.",
            "to_session_37": "Sinusoidal PE = Fourier basis for sequence position: EML-3 = same depth as trig Fourier atoms.",
            "to_session_106": "Scaling law L~N^{-α} = EML-2 power law, same depth as Zipf's law f(k)~k^{-s} in language.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_transformer_eml(), indent=2, default=str))
