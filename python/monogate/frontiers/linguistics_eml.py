"""
Session 106 — Linguistics & Semantics: EML as Language Substrate

Zipf's law, phonology, syntax trees, semantic embeddings, and language model
probability structures classified by EML depth.

Key theorem: Zipf's law is EML-2 (power law frequency: f(k)~1/k^s). Phonological
rules are EML-0 (finite state = discrete). Syntactic parse trees are EML-0 in
topology (tree structure) but EML-2 in probability (PCFG). Semantic embeddings
are EML-1 (softmax over inner products). Language model perplexity is EML-2
(cross-entropy). Metaphor and creativity are EML-∞ (conceptual blending).
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field


EML_INF = float("inf")


@dataclass
class ZipfLawEML:
    """
    Zipf's law: the k-th most frequent word has frequency f(k) ~ 1/k^s.

    EML structure:
    - f(k) = C/k^s with s≈1: EML-2 (power law = exp(-s·ln k))
    - Zipf-Mandelbrot: f(k) = C/(k+b)^s: EML-2 (shifted power law)
    - Heaps' law: vocabulary V(n) ~ K·n^β with β≈0.5-0.8: EML-2 (power law)
    - Information content: I(w) = -log P(w) = log k + s·log k ≈ s·log(rank): EML-2
    - Surprise of rank-k word: s·ln(k): EML-2 (log of rank)
    - Benford's law (digit frequencies): d(n) ~ log(1+1/n): EML-2 (log of rational)
    """

    def zipf_frequency(self, k: int, s: float = 1.0, N: int = 10000) -> dict:
        """Normalized Zipf frequency for rank k in vocabulary of N words."""
        Z = sum(1.0 / j ** s for j in range(1, N + 1))
        f = 1.0 / (k ** s * Z)
        info = -math.log2(f) if f > 0 else float("inf")
        return {
            "rank": k,
            "s": s,
            "frequency": round(f, 8),
            "information_bits": round(info, 4),
            "eml": 2,
            "reason": "f(k) = 1/(k^s·Z): EML-2 (power law in rank)",
        }

    def heaps_law(self, n_tokens: int, K: float = 44.0, beta: float = 0.7) -> dict:
        """Heaps' law: V ≈ K·n^β."""
        V = K * n_tokens ** beta
        return {
            "n_tokens": n_tokens,
            "K": K,
            "beta": beta,
            "vocabulary_size": int(V),
            "eml": 2,
            "reason": "V ~ K·n^β = exp(ln K + β·ln n): EML-2 (power law in corpus size)",
        }

    def benford_law(self, d: int) -> dict:
        """Benford's law: P(leading digit = d) = log10(1 + 1/d)."""
        if d < 1 or d > 9:
            return {"d": d, "P": 0.0, "eml": 2}
        P = math.log10(1 + 1 / d)
        return {
            "d": d,
            "P_benford": round(P, 6),
            "eml": 2,
            "reason": "P(d) = log(1+1/d): EML-2 (log of rational function of d)",
        }

    def to_dict(self) -> dict:
        ranks = [1, 2, 5, 10, 50, 100, 1000]
        return {
            "zipf_s1": [self.zipf_frequency(k, 1.0) for k in ranks],
            "zipf_s15": [self.zipf_frequency(k, 1.5) for k in [1, 5, 100]],
            "heaps": [self.heaps_law(n) for n in [1000, 10000, 100000, 1000000]],
            "benford": [self.benford_law(d) for d in range(1, 10)],
            "eml_zipf": 2,
            "eml_heaps": 2,
            "eml_benford": 2,
        }


@dataclass
class SyntaxAndParsing:
    """
    Syntax: generative grammars, parse trees, probabilistic context-free grammars (PCFG).

    EML structure:
    - CFG production rule A → α: EML-0 (discrete rewriting rule)
    - Parse tree topology: EML-0 (tree = combinatorial structure)
    - PCFG rule probability P(A → α): EML-0 per rule (trained parameter)
    - PCFG sentence probability: P(T) = ∏_{rule applications} P(rule): EML-2 (product of probs = exp(Σ log P))
    - CYK parsing: O(n³·|G|) dynamic programming: EML-0 (integer algorithm)
    - Ambiguity: multiple parse trees → P(sentence) = Σ_T P(T): EML-2 (sum of EML-2 terms)
    - Dependency grammar: arc-factored model = exp(Σ score(head,dep)): EML-1
    """

    def pcfg_sentence_probability(self, rule_probs: list[float]) -> dict:
        """P(T) = ∏ P(rule_i): product of rule probabilities."""
        log_P = sum(math.log(p) for p in rule_probs if p > 0)
        P = math.exp(log_P)
        return {
            "rule_probs": rule_probs,
            "n_rules": len(rule_probs),
            "log_probability": round(log_P, 6),
            "probability": round(P, 8),
            "eml": 2,
            "reason": "P(T) = ∏ P_i = exp(Σ log P_i): EML-2 (log of product = sum of logs)",
        }

    def chomsky_hierarchy_eml(self) -> list[dict]:
        return [
            {"type": "Type-3 Regular", "automaton": "FSA", "expressiveness": "a^n", "eml": 0,
             "reason": "Regular languages: finite state = EML-0 (discrete transitions)"},
            {"type": "Type-2 Context-Free", "automaton": "PDA", "expressiveness": "a^n b^n", "eml": 0,
             "reason": "CFG topology: tree structure = EML-0; PCFG probabilities = EML-2"},
            {"type": "Type-1 Context-Sensitive", "automaton": "LBA", "expressiveness": "a^n b^n c^n", "eml": EML_INF,
             "reason": "CSG: polynomial space = EML-∞ (PSPACE-complete recognition)"},
            {"type": "Type-0 Unrestricted", "automaton": "Turing machine", "expressiveness": "all RE", "eml": EML_INF,
             "reason": "RE languages: undecidable = EML-∞ (halting problem = EML-∞)"},
        ]

    def to_dict(self) -> dict:
        return {
            "pcfg_example": self.pcfg_sentence_probability([0.8, 0.6, 0.9, 0.7, 0.5]),
            "chomsky_hierarchy": self.chomsky_hierarchy_eml(),
            "eml_parse_tree_topology": 0,
            "eml_pcfg_probability": 2,
            "eml_dependency_grammar": 1,
            "eml_ambiguous_sentence": 2,
            "inside_algorithm": "Inside probability β(A,i,j) = Σ_{rules} P(rule)·β(B,i,k)·β(C,k,j): EML-2 DP",
        }


@dataclass
class SemanticEmbeddings:
    """
    Word2Vec, GloVe, and transformer embeddings: EML structure of meaning.

    EML structure:
    - Word2Vec skip-gram: P(w_O|w_I) = softmax(v_O·v_I): EML-1 (softmax = Boltzmann)
    - Negative sampling loss: Σ log σ(v·u): EML-1 (sigmoid = logistic = EML-1)
    - GloVe: (u_i·v_j + b_i + b_j - log X_{ij})²: EML-2 (squared error on EML-2 co-occurrence)
    - Cosine similarity: cos(u,v) = u·v/(|u||v|): EML-0 (rational in norms, EML-0 up to norm)
    - Analogy: king - man + woman ≈ queen: EML-2 (vector arithmetic in EML-1 embedding space)
    - Semantic change over time: word vector drift ~ EML-2 (gradient of EML-1 loss)
    - T-SNE visualization: EML-2 (KL divergence between Gaussian neighborhoods)
    """

    def skipgram_probability(self, dot_product: float, all_dot_products: list[float]) -> dict:
        """P(w_O|w_I) = exp(v_O·v_I) / Σ_w exp(v_w·v_I)."""
        max_dp = max(all_dot_products)
        exps = [math.exp(d - max_dp) for d in all_dot_products]
        Z = sum(exps)
        target_idx = all_dot_products.index(dot_product) if dot_product in all_dot_products else 0
        P = exps[target_idx] / Z
        return {
            "dot_product": dot_product,
            "softmax_prob": round(P, 6),
            "eml": 1,
            "reason": "P(w|c) = softmax(v·u): EML-1 (Boltzmann over dot products)",
        }

    def glove_loss_term(self, u: list[float], v: list[float],
                        b_u: float, b_v: float, log_Xij: float) -> dict:
        dot = sum(a * b for a, b in zip(u, v))
        residual = dot + b_u + b_v - log_Xij
        loss = residual ** 2
        return {
            "dot_product": round(dot, 4),
            "log_Xij": round(log_Xij, 4),
            "residual": round(residual, 4),
            "squared_loss": round(loss, 4),
            "eml": 2,
            "reason": "(u·v + b_u + b_v - log X_{ij})²: EML-2 (squared deviation from EML-2 log co-occurrence)",
        }

    def analogy_arithmetic(self, king: list[float], man: list[float],
                           woman: list[float]) -> dict:
        queen_approx = [k - m + w for k, m, w in zip(king, man, woman)]
        norm = math.sqrt(sum(x**2 for x in queen_approx))
        queen_normalized = [x / norm for x in queen_approx]
        return {
            "operation": "king - man + woman = queen (approx)",
            "result_norm": round(norm, 4),
            "eml_arithmetic": 2,
            "reason": "Vector arithmetic in EML-1 embedding space = EML-2 (linear combination = EML-2)",
        }

    def to_dict(self) -> dict:
        dps = [3.2, 1.1, 0.5, -0.3, -1.2]
        return {
            "skipgram": self.skipgram_probability(3.2, dps),
            "glove_loss": self.glove_loss_term([0.5, 0.3], [0.4, 0.6], 0.1, 0.2, 2.3),
            "analogy": self.analogy_arithmetic([0.9, 0.3, 0.1], [0.5, 0.2, 0.7], [0.4, 0.8, 0.2]),
            "eml_softmax": 1,
            "eml_glove": 2,
            "eml_tsne": 2,
            "eml_cosine_sim": 0,
        }


@dataclass
class LanguageModelPerplexity:
    """
    Perplexity, cross-entropy, and scaling laws for language models.

    EML structure:
    - Cross-entropy: H(p,q) = -Σ p(w)·log q(w): EML-2 (−Σ p·log q)
    - Perplexity: PP = exp(H): EML-1 (exp of EML-2 = EML-1 in depth? No: exp is applied once to H → EML-1 of EML-2 = EML-3)
      Actually PP = 2^H(bits) or e^H(nats): the exponential of cross-entropy.
      H is EML-2, exp(H) = PP: EML-1 applied to EML-2 → EML-3 by composition
    - Scaling law: L(N,D) ≈ L_0 + (N_c/N)^{α_N} + (D_c/D)^{α_D}: EML-2 (power laws in N, D)
    - Temperature sampling: P(w) ∝ exp(logit(w)/T): EML-1 per token
    - Beam search: max Σ log P(w_i|context): EML-2 (sum of EML-1 log probs)
    """

    def cross_entropy(self, p_true: list[float], p_model: list[float]) -> dict:
        H = -sum(p * math.log(q) for p, q in zip(p_true, p_model) if p > 0 and q > 0)
        PP = math.exp(H)
        return {
            "cross_entropy_nats": round(H, 4),
            "cross_entropy_bits": round(H / math.log(2), 4),
            "perplexity": round(PP, 4),
            "eml_H": 2,
            "eml_PP": 3,
            "reason": "H = -Σ p·log q: EML-2; PP = exp(H): EML-3 (exp of EML-2 = EML-3 by composition)",
        }

    def scaling_law(self, N: float, D: float,
                    L0: float = 1.69, Nc: float = 8.8e13, Dc: float = 5.4e13,
                    aN: float = 0.076, aD: float = 0.095) -> dict:
        L = L0 + (Nc / N) ** aN + (Dc / D) ** aD
        return {
            "N_params": N,
            "D_tokens": D,
            "loss": round(L, 4),
            "eml": 2,
            "reason": "Scaling law: L = L₀ + (N_c/N)^α_N + (D_c/D)^α_D: EML-2 (power laws in N, D)",
        }

    def temperature_sampling(self, logits: list[float], T: float) -> dict:
        scaled = [l / T for l in logits]
        max_l = max(scaled)
        exps = [math.exp(l - max_l) for l in scaled]
        Z = sum(exps)
        probs = [e / Z for e in exps]
        H = -sum(p * math.log(p) for p in probs if p > 0)
        return {
            "logits": logits,
            "temperature": T,
            "probs": [round(p, 4) for p in probs],
            "entropy_nats": round(H, 4),
            "eml": 1,
            "reason": "P(w) ∝ exp(l/T): EML-1 (Boltzmann with temperature T)",
        }

    def to_dict(self) -> dict:
        p_true = [0.5, 0.3, 0.15, 0.05]
        p_model = [0.4, 0.35, 0.2, 0.05]
        return {
            "cross_entropy_example": self.cross_entropy(p_true, p_model),
            "scaling_laws": [
                self.scaling_law(1e9, 1e12),
                self.scaling_law(1e10, 1e13),
                self.scaling_law(1e11, 1e13),
            ],
            "temperature": [
                self.temperature_sampling([3.0, 1.5, 0.5, -1.0], T)
                for T in [0.5, 1.0, 2.0]
            ],
            "eml_cross_entropy": 2,
            "eml_perplexity": 3,
            "eml_scaling_law": 2,
            "eml_temperature_sampling": 1,
        }


def analyze_linguistics_eml() -> dict:
    zipf = ZipfLawEML()
    syntax = SyntaxAndParsing()
    sem = SemanticEmbeddings()
    lm = LanguageModelPerplexity()
    return {
        "session": 106,
        "title": "Linguistics & Semantics: EML as Language Substrate",
        "key_theorem": {
            "theorem": "EML Linguistic Depth Theorem",
            "statement": (
                "Zipf's law f(k)~1/k^s is EML-2 (power law in rank). "
                "Heaps' law V~n^β is EML-2 (power law in corpus size). "
                "CFG/PCFG tree topology is EML-0 (discrete); sentence probability is EML-2 (product → log sum). "
                "Skip-gram softmax P(w|c) is EML-1 (Boltzmann over dot products). "
                "GloVe loss is EML-2 (squared deviation from log co-occurrence). "
                "Cross-entropy H is EML-2; perplexity exp(H) is EML-3 (exp of EML-2). "
                "Language model scaling law is EML-2 (power laws in N and D). "
                "Metaphor and creativity: EML-∞ (no finite EML tree generates conceptual blending)."
            ),
        },
        "zipf_law": zipf.to_dict(),
        "syntax_parsing": syntax.to_dict(),
        "semantic_embeddings": sem.to_dict(),
        "language_model": lm.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Regular grammar (FSA); parse tree topology; cosine similarity (rational); phoneme inventory (discrete)",
            "EML-1": "Skip-gram softmax; temperature sampling (Boltzmann); dependency arc score; word probability",
            "EML-2": "Zipf/Heaps/Benford power laws; PCFG sentence probability; GloVe loss; cross-entropy H; scaling law",
            "EML-3": "Perplexity exp(H) = exp of EML-2; acoustic phonetics (harmonic spectral envelope)",
            "EML-∞": "Metaphor (conceptual blending); creativity; halting problem for unrestricted grammar; pragmatic implicature",
        },
        "rabbit_hole_log": [
            "Zipf's law is EML-2 everywhere in language: word frequencies, phoneme frequencies, morpheme frequencies, sentence length distributions — all follow power laws (EML-2). Language has selected the EML-2 regime as its operating point, perhaps because EML-2 minimizes code length (MDL principle = EML-2 by Session 74).",
            "Perplexity is EML-3: cross-entropy H = -Σ p log q is EML-2, but the perplexity PP = exp(H) applies exp to an EML-2 quantity → EML-3 by composition. Language models are evaluated in EML-3 units (perplexity), but trained in EML-2 units (cross-entropy/loss). The performance metric is one level deeper than the training objective.",
            "The Chomsky hierarchy maps exactly to EML depth: Regular (EML-0) ⊂ Context-Free (EML-0 topology, EML-2 prob) ⊂ Context-Sensitive (EML-∞) ⊂ Unrestricted (EML-∞ = Turing = undecidable). Natural language sits at the EML-2 boundary between CFG and CSG — just complex enough for structure, not so complex as to be undecidable.",
            "Scaling laws are EML-2 with two contributions: L = L₀ + (N_c/N)^α_N + (D_c/D)^α_D. Each power law term is EML-2. The residual irreducible loss L₀ is EML-0 (the entropy of human language itself). Intelligence emerges from EML-2 power-law scaling of EML-1 transformer computations.",
        ],
        "connections": {
            "to_session_60": "Shannon entropy = EML-2. Cross-entropy H = EML-2. Language perplexity = EML-3 = exp(EML-2).",
            "to_session_96": "LM scaling laws = EML-2 (Session 96: neural scaling laws). Language = ML theory in EML-2 regime.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_linguistics_eml(), indent=2, default=str))
