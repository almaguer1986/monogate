"""
Session 136 — Linguistics Deep II: Compositionality, Ambiguity & Semantic Shift

EML operator: eml(x,y) = exp(x) - ln(y)
EML depth hierarchy: 0 (topology) | 1 (equilibria) | 2 (geometry) | 3 (waves) | ∞ (singularities)

Key theorem: Semantic composition is EML-0 (structural); word meaning is EML-2 (distributional);
semantic ambiguity and meaning shift transitions are EML-∞.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# 1. Compositional Semantics
# ---------------------------------------------------------------------------

@dataclass
class CompositionalSemanticsV2:
    """Montague (1970): meaning = function application in typed lambda calculus."""

    vocab_size: int = 10000
    context_window: int = 5

    def lambda_composition_depth(self, n_constituents: int) -> int:
        """
        Binary tree of function applications: depth = ceil(log2(n)).
        EML-0 (integer = topological count of tree depth).
        """
        if n_constituents <= 1:
            return 0
        return math.ceil(math.log2(n_constituents))

    def type_complexity(self, arg_count: int) -> str:
        """
        Type-theoretic complexity: simple types e, t, et, ett, ...
        Depth = number of function arrows = EML-0.
        """
        type_string = "e"
        for _ in range(arg_count):
            type_string = f"({type_string} → t)"
        return type_string

    def montague_grammar_eml(self) -> dict[str, str]:
        """EML depth of core Montague semantics operations."""
        return {
            "entity_type_e": "EML-0 (atomic)",
            "truth_value_type_t": "EML-0 (Boolean)",
            "function_application": "EML-0 (structural composition)",
            "lambda_abstraction": "EML-0 (binding)",
            "quantifier_raising": "EML-0 (movement in syntax tree)",
            "intensional_operator": "EML-2 (world-relative computation)"
        }

    def productivity_of_language(self) -> float:
        """
        Number of sentences expressible: N^k for vocab N, length k.
        EML-1 (exponential in sentence length).
        """
        k = 10  # average sentence length
        return math.log(self.vocab_size) * k  # log of N^k = k*log(N)

    def analyze(self) -> dict[str, Any]:
        depths = {n: self.lambda_composition_depth(n) for n in [2, 4, 8, 16, 32]}
        types = {k: self.type_complexity(k) for k in range(4)}
        return {
            "model": "CompositionalSemanticsV2",
            "vocab_size": self.vocab_size,
            "lambda_tree_depths": depths,
            "montague_types": types,
            "montague_eml_depths": self.montague_grammar_eml(),
            "log_productivity": round(self.productivity_of_language(), 2),
            "eml_depth": {
                "function_application": 0,
                "lambda_abstraction": 0,
                "quantifiers": 0,
                "intensional_operators": 2,
                "sentence_productivity": 1
            },
            "key_insight": "Compositional grammar is EML-0 (structural tree operations)"
        }


# ---------------------------------------------------------------------------
# 2. Distributional Semantics
# ---------------------------------------------------------------------------

@dataclass
class DistributionalSemanticsV2:
    """Word2Vec, GloVe: meaning = position in high-dimensional vector space."""

    embedding_dim: int = 300
    vocab_size: int = 100000

    def pmi_formula(self, p_wc: float, p_w: float, p_c: float) -> float:
        """
        Pointwise Mutual Information: PMI(w,c) = log(P(w,c)/(P(w)P(c))).
        EML-2 (log of ratio).
        """
        if p_w <= 0 or p_c <= 0 or p_wc <= 0:
            return 0.0
        return math.log(p_wc / (p_w * p_c))

    def word2vec_objective(self, dot_product: float) -> float:
        """log σ(v_w · v_c) = -log(1 + exp(-dot)). EML-2 (log of EML-1)."""
        return -math.log(1 + math.exp(-dot_product))

    def cosine_similarity(self, v1_norm: float, v2_norm: float,
                          dot: float) -> float:
        """cos(v1,v2) = v1·v2/(||v1||||v2||). EML-0 (ratio)."""
        if v1_norm * v2_norm < 1e-15:
            return 0.0
        return dot / (v1_norm * v2_norm)

    def zipf_law(self, rank: int, s: float = 1.0) -> float:
        """
        Zipf's law: f(k) ∝ k^{-s}. EML-2 (power law = log-linear).
        Harmonic normalization constant: H(N, s) = sum k^{-s}.
        """
        H_approx = math.log(self.vocab_size) + 0.5772  # Euler-Mascheroni approx
        return rank ** (-s) / H_approx

    def analogy_geometry(self) -> dict[str, str]:
        """
        King - Man + Woman = Queen: vector arithmetic = EML-0 (affine).
        But the analogy captures EML-2 geometric structure.
        """
        return {
            "vector_arithmetic": "EML-0 (linear operations)",
            "analogy_completion": "EML-2 (nearest neighbor in Euclidean space)",
            "semantic_subspace": "EML-2 (PCA/SVD decomposition)",
            "isotropy": "EML-2 (uniform distribution over sphere)"
        }

    def analyze(self) -> dict[str, Any]:
        pmi_vals = [(0.01, 0.05, 0.05), (0.01, 0.1, 0.1), (0.005, 0.05, 0.05)]
        pmis = [round(self.pmi_formula(p, pw, pc), 4) for p, pw, pc in pmi_vals]

        ranks = [1, 10, 100, 1000, 10000]
        zipf_vals = {r: round(self.zipf_law(r), 6) for r in ranks}

        w2v_dots = [-2.0, -1.0, 0.0, 1.0, 2.0]
        w2v_obj = {d: round(self.word2vec_objective(d), 4) for d in w2v_dots}

        return {
            "model": "DistributionalSemanticsV2",
            "embedding_dim": self.embedding_dim,
            "pmi_examples": pmis,
            "zipf_distribution": zipf_vals,
            "word2vec_objective": w2v_obj,
            "analogy_geometry": self.analogy_geometry(),
            "eml_depth": {
                "pmi": 2,
                "word2vec_objective": 2,
                "cosine_similarity": 0,
                "zipf_law": 2,
                "vector_analogy": 0
            },
            "key_insight": "Distributional semantics = EML-2 (log-linear PMI, power-law Zipf)"
        }


# ---------------------------------------------------------------------------
# 3. Semantic Change & Ambiguity
# ---------------------------------------------------------------------------

@dataclass
class SemanticChangeAndAmbiguity:
    """Temporal semantic change and ambiguity resolution as EML processes."""

    time_span: float = 100.0   # years
    drift_rate: float = 0.01   # semantic drift per year

    def semantic_drift(self, t: float) -> float:
        """
        Gradual semantic drift: D(t) = 1 - exp(-lambda*t). EML-1 (exponential decay).
        D measures cosine distance from original meaning.
        """
        return 1 - math.exp(-self.drift_rate * t)

    def meaning_shift_probability(self, t: float, t_event: float = 50.0) -> float:
        """
        Probability of discrete meaning shift at t_event.
        Sharp sigmoid: EML-∞ in limit k→∞.
        """
        k = 0.5
        exponent = -k * (t - t_event)
        exponent = max(-500.0, min(500.0, exponent))
        return 1.0 / (1 + math.exp(exponent))

    def ambiguity_entropy(self, n_senses: int, dominance: float = 0.7) -> float:
        """
        Shannon entropy of sense distribution.
        Dominant sense has probability 'dominance'; rest split uniformly.
        EML-2.
        """
        if n_senses <= 1:
            return 0.0
        rest = (1 - dominance) / (n_senses - 1)
        probs = [dominance] + [rest] * (n_senses - 1)
        return -sum(p * math.log(p + 1e-15) for p in probs)

    def garden_path_effect(self) -> dict[str, Any]:
        """
        Garden path sentences: initial parse EML-1 (greedy), reanalysis EML-∞.
        "The horse raced past the barn fell."
        Initial parse: EML-1 (most probable interpretation)
        Revision: EML-∞ (non-local structural reanalysis)
        """
        return {
            "example": "The horse raced past the barn fell.",
            "initial_parse_eml": 1,
            "reanalysis_eml": "∞",
            "mechanism": "Reanalysis = phase transition in parse tree space",
            "surprise_cost": "EML-∞ (non-incremental structural jump)"
        }

    def semantic_bleaching(self, t_vals: list[float]) -> list[float]:
        """
        Semantic bleaching: words lose specific meaning over time.
        Rate ~ exp(-decay*t): EML-1.
        E.g., 'very', 'literally' losing intensifier force.
        """
        decay = self.drift_rate * 2
        return [math.exp(-decay * t) for t in t_vals]

    def analyze(self) -> dict[str, Any]:
        t_vals = [0, 10, 25, 50, 75, 100]
        drift = {t: round(self.semantic_drift(t), 4) for t in t_vals}
        shift_prob = {t: round(self.meaning_shift_probability(t), 4) for t in t_vals}
        bleaching = {t: round(v, 4) for t, v in zip(t_vals, self.semantic_bleaching(t_vals))}

        senses = [1, 2, 3, 5, 10]
        entropy = {n: round(self.ambiguity_entropy(n), 4) for n in senses}

        return {
            "model": "SemanticChangeAndAmbiguity",
            "time_span": self.time_span,
            "drift_rate": self.drift_rate,
            "semantic_drift_over_time": drift,
            "meaning_shift_probability": shift_prob,
            "semantic_bleaching": bleaching,
            "ambiguity_entropy_vs_n_senses": entropy,
            "garden_path_effect": self.garden_path_effect(),
            "eml_depth": {
                "semantic_drift": 1,
                "meaning_shift_event": "∞",
                "ambiguity_entropy": 2,
                "bleaching": 1,
                "garden_path_reanalysis": "∞"
            },
            "key_insight": (
                "Gradual semantic change is EML-1 (exponential drift). "
                "Discrete meaning shifts and garden-path reanalysis are EML-∞ (phase transitions)."
            )
        }


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_linguistics_v2_eml() -> dict[str, Any]:
    comp = CompositionalSemanticsV2(vocab_size=50000, context_window=5)
    dist = DistributionalSemanticsV2(embedding_dim=300, vocab_size=100000)
    change = SemanticChangeAndAmbiguity(time_span=100.0, drift_rate=0.015)

    return {
        "session": 136,
        "title": "Linguistics Deep II: Compositionality, Ambiguity & Semantic Shift",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "compositional_semantics": comp.analyze(),
        "distributional_semantics": dist.analyze(),
        "semantic_change_and_ambiguity": change.analyze(),
        "eml_depth_summary": {
            "EML-0": "Lambda calculus composition, syntax tree structure, function application",
            "EML-1": "Sentence productivity (N^k), semantic drift, semantic bleaching",
            "EML-2": "PMI, Word2Vec objective, Zipf's law, ambiguity entropy",
            "EML-3": "Prosodic oscillations, tonal patterns (EML-3 in tone languages)",
            "EML-∞": "Ambiguity resolution, garden-path reanalysis, discrete meaning shift"
        },
        "key_theorem": (
            "The EML Linguistic Depth Theorem: "
            "Compositional meaning (Montague grammar) is EML-0 — it is purely structural, "
            "like topology. Distributional meaning (Word2Vec, PMI) is EML-2 — log-linear geometry. "
            "Semantic ambiguity resolution and garden-path reanalysis are EML-∞: "
            "they are phase transitions in the parse/meaning space, "
            "not computable by any EML-finite algorithm from the local context."
        ),
        "rabbit_hole_log": [
            "Montague grammar = EML-0: type-theoretic composition is counting/structural",
            "Word2Vec objective = log σ(v·c): log of EML-1 = EML-2",
            "Zipf's law P(k)~k^{-1}: power law = EML-2 (same class as all scale-free laws)",
            "Semantic drift = 1-exp(-λt): EML-1 (same as OU mean reversion in evolution)",
            "Garden path reanalysis: non-local structural revision = EML-∞ jump",
            "Ambiguity entropy: Shannon = EML-2 (same as thermodynamic entropy)"
        ],
        "connections": {
            "S60_info_theory": "PMI = pointwise mutual information = EML-2 (same class as Shannon)",
            "S119_transformer": "Word2Vec → Transformer: both EML-2 (distributional geometry)",
            "S124_graph_deep": "Semantic networks = graph structure; syntax trees = EML-0 trees",
            "S130_grand_synthesis_7": "Language ambiguity resolution = EML-∞ phase transition"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_linguistics_v2_eml(), indent=2, default=str))
