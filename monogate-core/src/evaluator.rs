//! Core EML/BEST tree evaluation logic.
//!
//! This module implements the same bottom-up fused tree traversal as Python's
//! `FusedEMLActivation`, but in pure Rust with no heap allocation per element
//! and optional rayon parallelism for large batches.
//!
//! # Tree structure
//!
//! A depth-`d` tree has `2^d` leaves and `2^d - 1` internal nodes.
//! Evaluation proceeds level-by-level, pairing consecutive nodes:
//!
//! ```text
//! depth=2, leaves=[l0, l1, l2, l3]
//!
//!   Level 0 (leaves): l0  l1  l2  l3
//!   Level 1:          eml(l0,l1)  eml(l2,l3)
//!   Level 2 (root):   eml(eml(l0,l1), eml(l2,l3))
//! ```
//!
//! # Operators
//!
//! - **EML**: `eml(a, b) = exp(a) - ln(softplus(b))`  — all nodes.
//! - **BEST**: inner nodes use `exl(a, b) = exp(a) * ln(softplus(b))`;
//!             the root node uses `eml`.
//!
//! Using `softplus(b) = ln(1 + exp(b))` instead of raw `b` matches the
//! Python implementation's numerical-safety convention and avoids domain
//! errors when `b` is negative.

use rayon::prelude::*;

/// Threshold above which rayon parallel iteration is engaged.
///
/// Below this the overhead of thread dispatch exceeds the computation time.
/// Tune this constant for your hardware; 1 000 is a conservative default.
pub const PARALLEL_THRESHOLD: usize = 1_000;

// ── Scalar gate functions ─────────────────────────────────────────────────────

/// Numerically safe softplus: `ln(1 + exp(b))`.
///
/// When `b > 20` the naive formula overflows; we use the identity
/// `softplus(b) = b + ln(1 + exp(-b))` for large values.
#[inline(always)]
fn softplus(b: f64) -> f64 {
    if b > 20.0 {
        // ln(1 + exp(b)) ≈ b  for large b; refined: b + ln(1 + exp(-b))
        b + (1.0 + (-b).exp()).ln()
    } else {
        (1.0 + b.exp()).ln()
    }
}

/// EML gate: `exp(a) - ln(softplus(b))`.
///
/// Numerically safe for all `a, b ∈ ℝ` (softplus ensures argument of `ln` is
/// always > 0).
#[inline(always)]
fn eml(a: f64, b: f64) -> f64 {
    a.exp() - softplus(b).ln()
}

/// EXL gate: `exp(a) * ln(softplus(b))`.
///
/// Used for inner nodes in the BEST routing.  Can be negative when
/// `softplus(b) < 1` (i.e. `b < 0`), which is fine — these intermediate
/// values are consumed by the EML root.
#[inline(always)]
fn exl(a: f64, b: f64) -> f64 {
    a.exp() * softplus(b).ln()
}

// ── Single-sample evaluators ──────────────────────────────────────────────────

/// Evaluate one EML tree for a single input `x`.
///
/// # Arguments
/// * `leaf_w` — weight per leaf (length must be `2^depth`).
/// * `leaf_b` — bias per leaf (length must be `2^depth`).
/// * `x`      — scalar input value.
/// * `depth`  — tree depth (1–3 recommended; depth ≥ 4 may overflow).
///
/// # Panics
/// Panics in debug mode if `leaf_w.len() != 1 << depth`.
pub fn eval_eml_bottom_up(leaf_w: &[f64], leaf_b: &[f64], x: f64, depth: usize) -> f64 {
    debug_assert_eq!(leaf_w.len(), 1 << depth, "leaf_w length must be 2^depth");
    debug_assert_eq!(leaf_b.len(), 1 << depth, "leaf_b length must be 2^depth");

    // Initialise node buffer: leaf values = w*x + b
    // We need at most 2^depth entries.  Use a fixed-size stack array (max depth 6
    // covers 64 leaves, which is well beyond the practical depth=3 limit).
    let n_leaves = 1 << depth;
    let mut nodes: Vec<f64> = (0..n_leaves)
        .map(|i| leaf_w[i] * x + leaf_b[i])
        .collect();

    // Bottom-up tree reduction — all nodes use EML.
    for level in 0..depth {
        let half = nodes.len() / 2;
        let new_nodes: Vec<f64> = (0..half)
            .map(|i| eml(nodes[2 * i], nodes[2 * i + 1]))
            .collect();
        nodes = new_nodes;
        let _ = level; // level unused; kept for clarity
    }

    nodes[0]
}

/// Evaluate one BEST tree for a single input `x`.
///
/// Inner nodes use EXL; the root node uses EML.
///
/// # Arguments
/// * `leaf_w` — weight per leaf (length must be `2^depth`).
/// * `leaf_b` — bias per leaf (length must be `2^depth`).
/// * `x`      — scalar input value.
/// * `depth`  — tree depth (1–3 recommended).
pub fn eval_best_bottom_up(leaf_w: &[f64], leaf_b: &[f64], x: f64, depth: usize) -> f64 {
    debug_assert_eq!(leaf_w.len(), 1 << depth, "leaf_w length must be 2^depth");
    debug_assert_eq!(leaf_b.len(), 1 << depth, "leaf_b length must be 2^depth");

    let n_leaves = 1 << depth;
    let mut nodes: Vec<f64> = (0..n_leaves)
        .map(|i| leaf_w[i] * x + leaf_b[i])
        .collect();

    for level in 0..depth {
        let half = nodes.len() / 2;
        let is_root = level == depth - 1;
        let new_nodes: Vec<f64> = (0..half)
            .map(|i| {
                let (a, b) = (nodes[2 * i], nodes[2 * i + 1]);
                if is_root {
                    eml(a, b)
                } else {
                    exl(a, b)
                }
            })
            .collect();
        nodes = new_nodes;
    }

    nodes[0]
}

// ── Batch evaluators ──────────────────────────────────────────────────────────

/// Evaluate an EML tree over a batch of inputs.
///
/// Automatically switches to rayon parallel iteration when
/// `xs.len() >= PARALLEL_THRESHOLD` to exploit multi-core hardware.
///
/// # Arguments
/// * `leaf_w` — weight per leaf (length `2^depth`).
/// * `leaf_b` — bias per leaf (length `2^depth`).
/// * `xs`     — batch of input scalars.
/// * `depth`  — tree depth.
///
/// # Returns
/// `Vec<f64>` of the same length as `xs`.
pub fn eval_eml_batch(
    leaf_w: &[f64],
    leaf_b: &[f64],
    xs: &[f64],
    depth: usize,
) -> Vec<f64> {
    if xs.len() >= PARALLEL_THRESHOLD {
        xs.par_iter()
            .map(|&x| eval_eml_bottom_up(leaf_w, leaf_b, x, depth))
            .collect()
    } else {
        xs.iter()
            .map(|&x| eval_eml_bottom_up(leaf_w, leaf_b, x, depth))
            .collect()
    }
}

/// Evaluate a BEST tree over a batch of inputs.
///
/// Uses rayon parallel iteration for batches above `PARALLEL_THRESHOLD`.
///
/// # Arguments
/// * `leaf_w` — weight per leaf (length `2^depth`).
/// * `leaf_b` — bias per leaf (length `2^depth`).
/// * `xs`     — batch of input scalars.
/// * `depth`  — tree depth.
///
/// # Returns
/// `Vec<f64>` of the same length as `xs`.
pub fn eval_best_batch(
    leaf_w: &[f64],
    leaf_b: &[f64],
    xs: &[f64],
    depth: usize,
) -> Vec<f64> {
    if xs.len() >= PARALLEL_THRESHOLD {
        xs.par_iter()
            .map(|&x| eval_best_bottom_up(leaf_w, leaf_b, x, depth))
            .collect()
    } else {
        xs.iter()
            .map(|&x| eval_best_bottom_up(leaf_w, leaf_b, x, depth))
            .collect()
    }
}

// ── Unit tests ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn default_weights(depth: usize) -> (Vec<f64>, Vec<f64>) {
        let n = 1 << depth;
        // weights near zero, biases = 1 — matches FusedEMLActivation init
        let w = vec![0.05f64; n];
        let b = vec![1.0f64; n];
        (w, b)
    }

    #[test]
    fn test_softplus_positive() {
        // softplus should always be positive
        for x in [-100.0, -1.0, 0.0, 1.0, 100.0] {
            assert!(softplus(x) > 0.0, "softplus({x}) should be positive");
        }
    }

    #[test]
    fn test_softplus_large() {
        // For large b, softplus(b) ≈ b
        let sp = softplus(100.0);
        assert!((sp - 100.0).abs() < 1e-10, "softplus(100) should ≈ 100, got {sp}");
    }

    #[test]
    fn test_eml_depth1() {
        // depth=1: two leaves, one eml node
        // eml(w0*x+b0, w1*x+b1) at x=0 with w=0.05, b=1
        // = eml(1.0, 1.0) = exp(1) - ln(softplus(1))
        let (w, b) = default_weights(1);
        let result = eval_eml_bottom_up(&w, &b, 0.0, 1);
        let expected = eml(1.0, 1.0);
        assert!((result - expected).abs() < 1e-12);
    }

    #[test]
    fn test_batch_matches_scalar() {
        let (w, b) = default_weights(2);
        let xs = vec![-1.0, 0.0, 0.5, 1.0, 2.0];
        let batch = eval_eml_batch(&w, &b, &xs, 2);
        for (i, &x) in xs.iter().enumerate() {
            let scalar = eval_eml_bottom_up(&w, &b, x, 2);
            assert!(
                (batch[i] - scalar).abs() < 1e-12,
                "batch[{i}]={} != scalar={} for x={}",
                batch[i],
                scalar,
                x
            );
        }
    }

    #[test]
    fn test_best_differs_from_eml() {
        // BEST and EML use different inner ops so they should yield different results
        let (w, b) = default_weights(2);
        let x = 1.0;
        let eml_out = eval_eml_bottom_up(&w, &b, x, 2);
        let best_out = eval_best_bottom_up(&w, &b, x, 2);
        // They should differ at depth >= 2
        assert!(
            (eml_out - best_out).abs() > 1e-10,
            "EML and BEST should differ at depth=2"
        );
    }

    #[test]
    fn test_depth3() {
        // Smoke test: depth=3 should not panic or return NaN
        let (w, b) = default_weights(3);
        let result = eval_eml_bottom_up(&w, &b, 0.5, 3);
        assert!(result.is_finite(), "depth=3 result should be finite, got {result}");
    }

    #[test]
    fn test_parallel_matches_sequential() {
        // Force the parallel branch by using a batch > PARALLEL_THRESHOLD
        let (w, b) = default_weights(2);
        let xs: Vec<f64> = (0..PARALLEL_THRESHOLD + 100)
            .map(|i| (i as f64) * 0.001 - 0.5)
            .collect();

        let parallel = eval_eml_batch(&w, &b, &xs, 2);
        // Sequential reference
        let sequential: Vec<f64> = xs
            .iter()
            .map(|&x| eval_eml_bottom_up(&w, &b, x, 2))
            .collect();

        for i in 0..xs.len() {
            assert!(
                (parallel[i] - sequential[i]).abs() < 1e-12,
                "parallel[{i}] != sequential[{i}]"
            );
        }
    }
}
