"""
Session 126 — Linguistics & Semantics: Compositional Meaning, Ambiguity & Semantic Shift

Montague semantics, distributional semantics, semantic change over time, word sense
disambiguation, compositionality, and the semantics of analogy classified by EML depth.

Key theorem: Montague compositional semantics is EML-0 (type-theoretic lambda calculus =
combinatorial). Distributional vector space semantics is EML-2 (inner product = EML-2).
Semantic change (word drift) follows an EML-1 exponential decay of old meaning.
Semantic ambiguity resolution via Bayesian inference is EML-2. Metaphor (novel meaning
creation) is EML-∞ (non-compositional, irreducible to EML-finite rules).
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class CompositionalSemantics:
    """
    Montague semantics and type-theoretic compositionality.

    EML structure:
    - Lambda calculus: λx.φ(x): EML-0 (syntactic combinator = EML-0)
    - Type composition: e→t (entity to truth value): EML-0 (type-theoretic)
    - Truth conditions of atomic sentence: EML-0 (set-theoretic extension)
    - Quantifier: ∀x.P(x)→Q(x): EML-0 (first-order logic)
    - Probabilistic semantics: P(meaning | form): EML-2 (Bayesian inference)
    - Semantic ambiguity: H(P(s|w)) = -Σ P(s|w) log P(s|w): EML-2 (entropy of interpretation)
    - Garden-path sentences: EML-∞ (non-analytic reparse = insight transition)
    """

    def type_composition_eml(self) -> list[dict]:
        """Map semantic types to EML depths."""
        return [
            {"type": "e (entity)", "eml": 0, "example": "John"},
            {"type": "t (truth value)", "eml": 0, "example": "True/False"},
            {"type": "e→t (predicate)", "eml": 0, "example": "λx.run(x)"},
            {"type": "⟨e,t⟩→t (quantifier)", "eml": 0, "example": "∀, ∃"},
            {"type": "functional application f(a)", "eml": 0, "example": "run(John)"},
            {"type": "P(s|w) (Bayesian)", "eml": 2, "example": "P(bank=river|context)"},
            {"type": "H(meanings) (ambiguity)", "eml": 2, "example": "-Σp log p"},
        ]

    def ambiguity_entropy(self, sense_probs: list[float]) -> dict:
        """Ambiguity entropy H = -Σ P(s) log P(s)."""
        H = -sum(p * math.log(p) for p in sense_probs if p > 0)
        n_senses = len(sense_probs)
        return {
            "sense_probabilities": sense_probs,
            "n_senses": n_senses,
            "ambiguity_entropy_nats": round(H, 4),
            "max_entropy_nats": round(math.log(n_senses), 4),
            "eml": 2,
            "reason": "H=-Σp log p: Shannon entropy of sense distribution = EML-2.",
        }

    def garden_path_eml(self) -> dict:
        """Garden-path sentence reparse = EML-∞ transition."""
        return {
            "example": "The horse raced past the barn fell.",
            "initial_parse_eml": 2,
            "reparse_event_eml": "∞",
            "post_reparse_eml": 0,
            "reason": (
                "Garden-path: initial parse proceeds EML-2 (incremental left-to-right). "
                "At 'fell': EML-∞ structural reanalysis (non-analytic backtrack = insight). "
                "Correct parse: 'the horse [that was] raced past the barn fell' = EML-0 structure."
            ),
        }

    def to_dict(self) -> dict:
        return {
            "type_composition": self.type_composition_eml(),
            "ambiguity": [
                self.ambiguity_entropy([0.9, 0.1]),
                self.ambiguity_entropy([0.5, 0.5]),
                self.ambiguity_entropy([0.33, 0.33, 0.34]),
                self.ambiguity_entropy([0.25, 0.25, 0.25, 0.25]),
            ],
            "garden_path": self.garden_path_eml(),
            "eml_montague": 0,
            "eml_bayesian_semantics": 2,
            "eml_ambiguity_entropy": 2,
            "eml_garden_path_reparse": "∞",
        }


@dataclass
class DistributionalSemantics:
    """
    Vector space models: word2vec, GloVe, contextual embeddings.

    EML structure:
    - Cosine similarity: cos(u,v) = u·v/(|u||v|): EML-2 (inner product / norms)
    - Word analogy: king - man + woman ≈ queen: EML-2 (vector arithmetic)
    - GloVe objective: Σ f(X_ij)(w_i·w̃_j + b_i + b̃_j - log X_ij)²: EML-2 (quadratic + log)
    - Skip-gram: P(w_o|w_c) = exp(u_o·v_c)/Σ exp(u_w·v_c): EML-1 (softmax = Boltzmann)
    - PMI: log P(w,c)/P(w)P(c): EML-2 (log ratio = EML-2)
    - BERT contextual: attention softmax = EML-1; FFN GELU = EML-3
    - Semantic similarity (cosine) distribution: EML-2
    """

    def cosine_similarity(self, u: list[float], v: list[float]) -> dict:
        """cos(u,v) = u·v / (|u|·|v|)."""
        dot = sum(a * b for a, b in zip(u, v))
        norm_u = math.sqrt(sum(a**2 for a in u))
        norm_v = math.sqrt(sum(b**2 for b in v))
        cos = dot / (norm_u * norm_v) if norm_u * norm_v > 0 else 0.0
        return {
            "u": u, "v": v,
            "dot_product": round(dot, 4),
            "cos_similarity": round(cos, 4),
            "eml": 2,
            "reason": "cos=u·v/(|u||v|): inner product / product of norms = EML-2.",
        }

    def pmi(self, p_wc: float, p_w: float, p_c: float) -> dict:
        """PMI = log P(w,c) / (P(w)·P(c))."""
        if p_w * p_c == 0 or p_wc == 0:
            return {"pmi": float("-inf"), "eml": 2}
        pmi_val = math.log(p_wc / (p_w * p_c))
        return {
            "p_wc": p_wc, "p_w": p_w, "p_c": p_c,
            "PMI": round(pmi_val, 4),
            "eml": 2,
            "reason": "PMI=log(P(w,c)/P(w)P(c)): log of probability ratio = EML-2.",
        }

    def analogy_vector(self, king: list[float], man: list[float],
                       woman: list[float]) -> dict:
        """king - man + woman ≈ queen (vector arithmetic)."""
        queen_approx = [k - m + w for k, m, w in zip(king, man, woman)]
        return {
            "king": king, "man": man, "woman": woman,
            "queen_approx": [round(v, 4) for v in queen_approx],
            "eml": 2,
            "reason": "Vector analogy = linear arithmetic on EML-2 embeddings = EML-2.",
        }

    def glove_loss(self, w_i: list[float], w_tilde_j: list[float],
                    b_i: float, b_j: float, log_X_ij: float, f: float = 1.0) -> dict:
        """GloVe: f(X_ij)·(wᵢ·w̃_j + bᵢ + b̃_j - log X_ij)²."""
        dot = sum(a * b for a, b in zip(w_i, w_tilde_j))
        residual = dot + b_i + b_j - log_X_ij
        loss = f * residual**2
        return {
            "dot": round(dot, 4),
            "log_X_ij": log_X_ij,
            "residual": round(residual, 4),
            "loss": round(loss, 4),
            "eml": 2,
            "reason": "GloVe: (dot + bias - log X_ij)²: quadratic of (inner product + log) = EML-2.",
        }

    def to_dict(self) -> dict:
        u = [1.0, 0.5, -0.3]
        v = [0.8, 0.6, -0.2]
        king = [0.9, 0.5, 0.1]
        man = [0.8, 0.3, 0.2]
        woman = [0.1, 0.9, 0.3]
        return {
            "cosine_similarity": [self.cosine_similarity(u, v)],
            "pmi": [self.pmi(0.01, 0.1, 0.05), self.pmi(0.001, 0.1, 0.05)],
            "analogy": self.analogy_vector(king, man, woman),
            "glove_loss": self.glove_loss(u, v, 0.1, 0.1, 2.3),
            "eml_cosine": 2,
            "eml_pmi": 2,
            "eml_analogy": 2,
            "eml_glove": 2,
            "eml_skip_gram_softmax": 1,
            "eml_bert_attention": 1,
            "eml_bert_gelu": 3,
        }


@dataclass
class SemanticChange:
    """
    Diachronic semantics: word meaning drift over time.

    EML structure:
    - Meaning decay: P(old_sense | t) = exp(-t/τ): EML-1 (exponential forgetting)
    - Meaning gain: P(new_sense | t) = 1 - exp(-t/τ): EML-1 (complementary)
    - Frequency-meaning correlation: log(freq) ↔ semantic stability: EML-2
    - Semantic bleaching (gradual): P(strong_sense) = P₀·exp(-λt): EML-1
    - Semantic shift acceleration (sudden): EML-∞ (social phase transition)
    - Neologism creation: EML-∞ (irreducible creative act)
    - Metaphor → dead metaphor: EML-∞ → EML-1 (freeze = no longer creative)
    """

    def meaning_decay(self, t: float, tau: float = 50.0) -> dict:
        """P(old_sense|t) = exp(-t/τ): exponential meaning decay."""
        p_old = math.exp(-t / tau)
        p_new = 1 - p_old
        return {
            "t_years": t,
            "tau_years": tau,
            "P_old_sense": round(p_old, 4),
            "P_new_sense": round(p_new, 4),
            "eml": 1,
            "reason": "P(old|t)=exp(-t/τ): EML-1 (exponential forgetting = meaning half-life).",
        }

    def semantic_shift_eml(self, shift_type: str) -> dict:
        """Classify types of semantic change by EML depth."""
        types = {
            "broadening": {"eml": 2, "example": "bird (now includes penguins)", "mechanism": "prototype extension = EML-2 (prototype similarity = cosine = EML-2)"},
            "narrowing": {"eml": 2, "example": "meat (all food → animal flesh)", "mechanism": "frequency selection = EML-2"},
            "bleaching": {"eml": 1, "example": "very (extremely → intensifier)", "mechanism": "exponential decay of semantic force = EML-1"},
            "metaphor_freeze": {"eml": 1, "example": "deadline (literal → schedule term)", "mechanism": "EML-∞ creative act → EML-1 routine use"},
            "neologism": {"eml": EML_INF, "example": "googling, unfriend", "mechanism": "novel meaning creation = EML-∞ (not derivable from prior semantics)"},
            "pejoration": {"eml": 2, "example": "villain (farm worker → criminal)", "mechanism": "social connotation drift = EML-2"},
        }
        result = types.get(shift_type, {"eml": 0, "example": "unknown"})
        result["shift_type"] = shift_type
        if result["eml"] == EML_INF:
            result["eml"] = "∞"
        return result

    def to_dict(self) -> dict:
        return {
            "meaning_decay": [self.meaning_decay(t) for t in [0, 10, 25, 50, 100, 200]],
            "semantic_shifts": [self.semantic_shift_eml(t) for t in
                                ["broadening", "narrowing", "bleaching",
                                 "metaphor_freeze", "neologism", "pejoration"]],
            "eml_decay": 1,
            "eml_broadening": 2,
            "eml_bleaching": 1,
            "eml_neologism": "∞",
            "eml_metaphor_live": "∞",
            "eml_metaphor_dead": 1,
        }


def analyze_linguistics_deep_eml() -> dict:
    cs = CompositionalSemantics()
    ds = DistributionalSemantics()
    sc = SemanticChange()
    return {
        "session": 126,
        "title": "Linguistics & Semantics: Compositional Meaning, Ambiguity & Semantic Shift",
        "key_theorem": {
            "theorem": "EML Semantic Compositionality Theorem",
            "statement": (
                "Montague compositional semantics (lambda calculus, type theory) is EML-0. "
                "Distributional semantics (cosine similarity, PMI, GloVe loss) is EML-2. "
                "Skip-gram softmax P(w_o|w_c)=exp(u·v)/Z is EML-1 (Boltzmann). "
                "Semantic ambiguity entropy H=-Σp log p is EML-2. "
                "Meaning decay P(old|t)=exp(-t/τ) is EML-1 (semantic half-life). "
                "Neologism creation and live metaphor are EML-∞ (irreducible creative act). "
                "Garden-path reparse is EML-∞ (non-analytic structural reanalysis = insight). "
                "BERT attention is EML-1; GELU is EML-3."
            ),
        },
        "compositional_semantics": cs.to_dict(),
        "distributional_semantics": ds.to_dict(),
        "semantic_change": sc.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Montague lambda calculus; type composition; truth conditions; quantifiers",
            "EML-1": "Softmax word distribution; meaning decay exp(-t/τ); bleaching; BERT attention",
            "EML-2": "Cosine similarity; PMI log ratio; GloVe quadratic loss; analogy arithmetic; ambiguity entropy; broadening/narrowing",
            "EML-3": "BERT GELU activation; contextual embedding compositionality",
            "EML-∞": "Garden-path reparse; live metaphor; neologism; creative semantic invention; polysemy explosion",
        },
        "rabbit_hole_log": [
            "Distributional semantics is EML-2: PMI = log P(w,c)/P(w)P(c) = log ratio of probabilities = EML-2 (log of ratio = EML-2 by the same argument as Shannon entropy, KL divergence, and CO₂ forcing 5.35·ln(C/C₀)). The entire word2vec/GloVe/PMI tradition implicitly operates at EML-2. The vector arithmetic of analogy (king-man+woman≈queen) is EML-2 linear algebra. Meaning IN distributional space is EML-2.",
            "Semantic change is EML-1 in the smooth case (bleaching, decay) and EML-∞ in the discontinuous case (neologism, live metaphor). The metaphor life cycle is: creative insight (EML-∞) → propagation in community (EML-1, epidemic spreading) → conventionalization (EML-2, frequency-meaning correlation) → dead metaphor (EML-1, exponential routine use). A word's semantic history traverses {∞, 1, 2, 1} — the EML ladder in non-monotone order.",
            "The garden-path effect is the linguistic analog of the insight aha moment (S121): incremental left-to-right parsing proceeds EML-2 (Bayesian inference updating probability of parse), hits an EML-∞ barrier at the disambiguating word ('fell'), and undergoes a non-analytic reparse. The resulting correct parse structure is EML-0 (syntactic tree). Parsing is an EML-∞ problem in general (chart parsing = O(n³) = EML-2 complexity for CFG, but NLP ambiguity resolution = EML-∞).",
        ],
        "connections": {
            "to_session_106": "S106 covered Zipf (EML-2), skip-gram (EML-1), perplexity (EML-3) at overview. S126 adds compositional semantics (EML-0), semantic change (EML-1/EML-∞), garden-path (EML-∞).",
            "to_session_121": "Garden-path reparse (EML-∞) = insight aha moment (EML-∞): same non-analytic restructuring.",
            "to_session_60": "PMI = log ratio = EML-2, same as KL divergence and all log-ratio information measures.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_linguistics_deep_eml(), indent=2, default=str))
