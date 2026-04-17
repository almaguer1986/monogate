"""
SRBench benchmark functions.

Implements Nguyen-12, Keijzer-15, and Vladislavleva-8 suites.
Each function is a BenchmarkFn dataclass with a callable, domain, and metadata.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class BenchmarkFn:
    name: str
    func: Callable[[np.ndarray], np.ndarray]
    domain: tuple[float, float]
    suite: str
    difficulty: str = "medium"
    tags: list[str] = field(default_factory=list)

    def sample(self, n: int = 20, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
        """Return (X, y) training pairs."""
        rng = np.random.default_rng(seed)
        X = rng.uniform(self.domain[0], self.domain[1], size=n)
        y = self.func(X)
        mask = np.isfinite(y)
        return X[mask], y[mask]

    def test_sample(self, n: int = 100, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
        """Return (X, y) test pairs."""
        rng = np.random.default_rng(seed)
        X = np.sort(rng.uniform(self.domain[0], self.domain[1], size=n))
        y = self.func(X)
        mask = np.isfinite(y)
        return X[mask], y[mask]


# ── Nguyen benchmark suite ────────────────────────────────────────────────────

NGUYEN: list[BenchmarkFn] = [
    BenchmarkFn(
        name="Nguyen-1",
        func=lambda x: x**3 + x**2 + x,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="easy",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Nguyen-2",
        func=lambda x: x**4 + x**3 + x**2 + x,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="easy",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Nguyen-3",
        func=lambda x: x**5 + x**4 + x**3 + x**2 + x,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="medium",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Nguyen-4",
        func=lambda x: x**6 + x**5 + x**4 + x**3 + x**2 + x,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="medium",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Nguyen-5",
        func=lambda x: np.sin(x**2) * np.cos(x) - 1,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Nguyen-6",
        func=lambda x: np.sin(x) + np.sin(x + x**2),
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Nguyen-7",
        func=lambda x: np.log(x + 1) + np.log(x**2 + 1),
        domain=(0, 2),
        suite="Nguyen",
        difficulty="medium",
        tags=["logarithm", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Nguyen-8",
        func=lambda x: np.sqrt(x),
        domain=(0, 4),
        suite="Nguyen",
        difficulty="easy",
        tags=["root"],
    ),
    BenchmarkFn(
        name="Nguyen-9",
        func=lambda x: np.sin(x) + np.sin(x**2),
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Nguyen-10",
        func=lambda x: 2 * np.sin(x) * np.cos(x),
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Nguyen-11",
        func=lambda x: x**x,
        domain=(0, 2),
        suite="Nguyen",
        difficulty="hard",
        tags=["power", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Nguyen-12",
        func=lambda x: x**4 - x**3 + 0.5 * x**2 - 0.5 * x,
        domain=(-1, 1),
        suite="Nguyen",
        difficulty="medium",
        tags=["polynomial"],
    ),
]

# ── Keijzer benchmark suite ───────────────────────────────────────────────────

KEIJZER: list[BenchmarkFn] = [
    BenchmarkFn(
        name="Keijzer-1",
        func=lambda x: 0.3 * x * np.sin(2 * math.pi * x),
        domain=(-1, 1),
        suite="Keijzer",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Keijzer-2",
        func=lambda x: 0.3 * x * np.sin(2 * math.pi * x),
        domain=(-2, 2),
        suite="Keijzer",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Keijzer-3",
        func=lambda x: 0.3 * x * np.sin(2 * math.pi * x),
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Keijzer-4",
        func=lambda x: x**3 * np.exp(-x) * np.cos(x) * np.sin(x) * (np.sin(x)**2 * np.cos(x) - 1),
        domain=(0, 10),
        suite="Keijzer",
        difficulty="hard",
        tags=["exponential", "trigonometric", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Keijzer-5",
        func=lambda x: 30 * x * (x - 1) / (x**2 - 4 * x + 5)**2,
        domain=(-1, 1),
        suite="Keijzer",
        difficulty="medium",
        tags=["rational"],
    ),
    BenchmarkFn(
        name="Keijzer-6",
        func=lambda x: np.sum(1.0 / np.arange(1, int(x) + 1)) if x >= 1 else 0,
        domain=(1, 50),
        suite="Keijzer",
        difficulty="hard",
        tags=["harmonic"],
    ),
    BenchmarkFn(
        name="Keijzer-7",
        func=lambda x: np.log(x),
        domain=(1, 100),
        suite="Keijzer",
        difficulty="easy",
        tags=["logarithm", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Keijzer-8",
        func=lambda x: np.sqrt(x),
        domain=(0, 100),
        suite="Keijzer",
        difficulty="easy",
        tags=["root"],
    ),
    BenchmarkFn(
        name="Keijzer-9",
        func=lambda x: np.arcsinh(x),
        domain=(0, 100),
        suite="Keijzer",
        difficulty="medium",
        tags=["inverse-hyperbolic"],
    ),
    BenchmarkFn(
        name="Keijzer-10",
        func=lambda x: x**x,
        domain=(0, 1),
        suite="Keijzer",
        difficulty="medium",
        tags=["power", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Keijzer-11",
        func=lambda x: x**3 + x**2 + x + 1,
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="easy",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Keijzer-12",
        func=lambda x: 4 * x**3 + 3 * x**2 + 2 * x + 1,
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="easy",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Keijzer-13",
        func=lambda x: 6 * np.sin(x) * np.cos(x),
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="hard",
        tags=["trigonometric"],
    ),
    BenchmarkFn(
        name="Keijzer-14",
        func=lambda x: 8.0 / (2 + x**2),
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="medium",
        tags=["rational"],
    ),
    BenchmarkFn(
        name="Keijzer-15",
        func=lambda x: 0.2 * x**3 + 0.5 * x**2 - 1.2 * x - 0.5,
        domain=(-3, 3),
        suite="Keijzer",
        difficulty="medium",
        tags=["polynomial"],
    ),
]

# ── Vladislavleva benchmark suite ─────────────────────────────────────────────

VLADISLAVLEVA: list[BenchmarkFn] = [
    BenchmarkFn(
        name="Vlad-1",
        func=lambda x: np.exp(-(x - 1) ** 2) / (1.2 + (x - 2.5) ** 2),
        domain=(0.3, 4),
        suite="Vladislavleva",
        difficulty="hard",
        tags=["exponential", "rational", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Vlad-2",
        func=lambda x: np.exp(-x) * x**3 * np.cos(x) * np.sin(x) * (np.cos(x) * np.sin(x)**2 - 1),
        domain=(0.05, 10),
        suite="Vladislavleva",
        difficulty="hard",
        tags=["exponential", "trigonometric", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Vlad-3",
        func=lambda x: np.exp(-x) * x**3 * np.cos(x) * np.sin(x) * (np.cos(x) * np.sin(x)**2 - 1) * (x - 3),
        domain=(0.05, 10),
        suite="Vladislavleva",
        difficulty="hard",
        tags=["exponential", "trigonometric", "eml-friendly"],
    ),
    BenchmarkFn(
        name="Vlad-4",
        func=lambda x: 10.0 / (5 + (x - 3) ** 2),
        domain=(0.05, 6.05),
        suite="Vladislavleva",
        difficulty="medium",
        tags=["rational"],
    ),
    BenchmarkFn(
        name="Vlad-5",
        func=lambda x: x**3 / 5 + x**2 / 2 - x - 0.5,
        domain=(-3, 3),
        suite="Vladislavleva",
        difficulty="easy",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Vlad-6",
        func=lambda x: 4 * x**4 - 3 * x**3 + 2 * x**2 - x,
        domain=(-2, 2),
        suite="Vladislavleva",
        difficulty="medium",
        tags=["polynomial"],
    ),
    BenchmarkFn(
        name="Vlad-7",
        func=lambda x: (x - 3) * (x - 1) ** 3 / ((x - 2) ** 2 + 1),
        domain=(-3, 3),
        suite="Vladislavleva",
        difficulty="medium",
        tags=["rational"],
    ),
    BenchmarkFn(
        name="Vlad-8",
        func=lambda x: (x**6 - 1.5 * x**4 + 0.5 * x**3 + 0.5 * x**2 - 0.5 * x),
        domain=(-3, 3),
        suite="Vladislavleva",
        difficulty="hard",
        tags=["polynomial"],
    ),
]

# ── Combined catalog ──────────────────────────────────────────────────────────

ALL_BENCHMARKS: list[BenchmarkFn] = NGUYEN + KEIJZER + VLADISLAVLEVA

EML_FRIENDLY: list[BenchmarkFn] = [b for b in ALL_BENCHMARKS if "eml-friendly" in b.tags]

SUITES: dict[str, list[BenchmarkFn]] = {
    "Nguyen": NGUYEN,
    "Keijzer": KEIJZER,
    "Vladislavleva": VLADISLAVLEVA,
}
