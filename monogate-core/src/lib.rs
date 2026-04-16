//! # monogate-core
//!
//! Native Rust extension for [monogate](https://pypi.org/project/monogate/) —
//! a Python library for EML (Exp-Minus-Log) arithmetic.
//!
//! ## What this crate provides
//!
//! * **`eval_eml_batch`** — evaluate a depth-`d` EML tree over a NumPy array of
//!   inputs.  Internally iterative (no Python recursion) and rayon-parallel for
//!   large batches.  Expected speedup: 50–200× vs `FusedEMLActivation` (Python).
//!
//! * **`eval_best_batch`** — same for BEST routing (EXL inner nodes, EML root).
//!
//! * **`benchmark_rust`** — measure Rust throughput in millions of evaluations
//!   per second; useful for quick hardware profiling without Python overhead.
//!
//! * **`sin_search`** module — fast bitmask-encoded tree search helpers for the
//!   sin(x) barrier research.
//!
//! ## Building
//!
//! ```bash
//! cd monogate-core
//! pip install maturin
//! maturin develop          # development build (debug)
//! maturin develop --release # release build (full optimisations)
//! ```
//!
//! ## Usage from Python
//!
//! ```python
//! import monogate_core
//! import numpy as np
//!
//! leaf_w = np.array([0.05, 0.05, 0.05, 0.05])  # depth=2 → 4 leaves
//! leaf_b = np.array([1.0,  1.0,  1.0,  1.0])
//! x      = np.linspace(-2, 2, 10_000)
//!
//! out = monogate_core.eval_eml_batch(leaf_w, leaf_b, x, depth=2, operator="EML")
//! throughput = monogate_core.benchmark_rust(n=100_000, depth=2)
//! print(f"{throughput:.1f} M evals/sec")
//! ```

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use std::time::Instant;

pub mod evaluator;
pub mod sin_search;

// ── Python-facing functions ───────────────────────────────────────────────────

/// Evaluate a complete binary EML or BEST tree over a batch of inputs.
///
/// This is the primary entry point for Python.  It mirrors the forward pass of
/// `FusedEMLActivation` but runs in compiled Rust with optional rayon
/// parallelism for batches ≥ 1 000 elements.
///
/// # Arguments (Python)
/// * `leaf_w`    — 1-D NumPy float64 array of leaf weights (length `2^depth`).
/// * `leaf_b`    — 1-D NumPy float64 array of leaf biases  (length `2^depth`).
/// * `x`         — 1-D NumPy float64 array of input values.
/// * `depth`     — integer tree depth (1–3; depth=4 risks numerical overflow).
/// * `operator`  — `"EML"` (all EML nodes) or `"BEST"` (EXL inner, EML root).
///
/// # Returns
/// 1-D NumPy float64 array, same shape as `x`.
///
/// # Raises
/// `ValueError` if `leaf_w.len() != 2^depth` or `operator` is unknown.
#[pyfunction]
#[pyo3(signature = (leaf_w, leaf_b, x, depth, operator = "EML"))]
fn eval_eml_batch<'py>(
    py: Python<'py>,
    leaf_w: PyReadonlyArray1<f64>,
    leaf_b: PyReadonlyArray1<f64>,
    x: PyReadonlyArray1<f64>,
    depth: usize,
    operator: &str,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let n_leaves = 1usize << depth;
    let w = leaf_w.as_slice()?;
    let b = leaf_b.as_slice()?;
    let xs = x.as_slice()?;

    if w.len() != n_leaves {
        return Err(PyValueError::new_err(format!(
            "eval_eml_batch: leaf_w has {} elements but depth={} requires {} leaves (2^depth)",
            w.len(),
            depth,
            n_leaves,
        )));
    }
    if b.len() != n_leaves {
        return Err(PyValueError::new_err(format!(
            "eval_eml_batch: leaf_b has {} elements but depth={} requires {} leaves (2^depth)",
            b.len(),
            depth,
            n_leaves,
        )));
    }

    let result = match operator.to_ascii_uppercase().as_str() {
        "EML" => evaluator::eval_eml_batch(w, b, xs, depth),
        "BEST" => evaluator::eval_best_batch(w, b, xs, depth),
        other => {
            return Err(PyValueError::new_err(format!(
                "eval_eml_batch: unknown operator {other:?}. Choose 'EML' or 'BEST'."
            )))
        }
    };

    Ok(result.into_pyarray_bound(py))
}

/// Evaluate a BEST-routed binary tree over a batch of inputs.
///
/// Convenience alias for `eval_eml_batch(..., operator="BEST")`.
///
/// # Arguments (Python)
/// * `leaf_w` — 1-D NumPy float64 array of leaf weights (length `2^depth`).
/// * `leaf_b` — 1-D NumPy float64 array of leaf biases  (length `2^depth`).
/// * `x`      — 1-D NumPy float64 array of input values.
/// * `depth`  — integer tree depth (1–3).
///
/// # Returns
/// 1-D NumPy float64 array, same shape as `x`.
#[pyfunction]
fn eval_best_batch<'py>(
    py: Python<'py>,
    leaf_w: PyReadonlyArray1<f64>,
    leaf_b: PyReadonlyArray1<f64>,
    x: PyReadonlyArray1<f64>,
    depth: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let n_leaves = 1usize << depth;
    let w = leaf_w.as_slice()?;
    let b = leaf_b.as_slice()?;
    let xs = x.as_slice()?;

    if w.len() != n_leaves || b.len() != n_leaves {
        return Err(PyValueError::new_err(format!(
            "eval_best_batch: leaf_w/leaf_b must have {} elements for depth={depth}",
            n_leaves,
        )));
    }

    let result = evaluator::eval_best_batch(w, b, xs, depth);
    Ok(result.into_pyarray_bound(py))
}

/// Measure Rust evaluation throughput.
///
/// Runs `n` evaluations of a depth-`d` EML tree with default parameters
/// (weights=0.05, biases=1.0, inputs in `[-1, 1]`) and returns throughput
/// in millions of evaluations per second.
///
/// Use this to confirm the Rust extension is installed correctly and to
/// compare against Python baseline numbers.
///
/// # Arguments (Python)
/// * `n`     — number of evaluations to run (default 100 000).
/// * `depth` — tree depth (default 2).
///
/// # Returns
/// `float` — throughput in millions of evaluations/sec.
///
/// # Example
/// ```python
/// import monogate_core
/// mps = monogate_core.benchmark_rust(n=1_000_000, depth=2)
/// print(f"Rust: {mps:.0f} M eval/sec")
/// ```
#[pyfunction]
#[pyo3(signature = (n = 100_000, depth = 2))]
fn benchmark_rust(n: usize, depth: usize) -> f64 {
    let n_leaves = 1usize << depth;
    let leaf_w: Vec<f64> = vec![0.05; n_leaves];
    let leaf_b: Vec<f64> = vec![1.0; n_leaves];

    // Generate input values: evenly spaced in [-1, 1]
    let xs: Vec<f64> = (0..n).map(|i| -1.0 + 2.0 * (i as f64) / (n as f64)).collect();

    let start = Instant::now();
    let _result = evaluator::eval_eml_batch(&leaf_w, &leaf_b, &xs, depth);
    let elapsed = start.elapsed().as_secs_f64();

    // Throughput in millions per second
    (n as f64) / elapsed / 1_000_000.0
}

/// Evaluate a sin-search tree assignment from Python.
///
/// Thin wrapper around `sin_search::eval_tree_assignment`.
///
/// # Arguments (Python)
/// * `shape_bits` — `int` bitmask encoding leaf assignments.
/// * `n_leaves`   — number of leaves (must be a power of 2, ≤ 64).
/// * `probe_x`    — scalar input value.
///
/// # Returns
/// `float | None` — the tree output, or `None` on domain error.
#[pyfunction]
fn eval_tree_assignment(
    shape_bits: u64,
    n_leaves: usize,
    probe_x: f64,
) -> Option<f64> {
    sin_search::eval_tree_assignment(shape_bits, n_leaves, probe_x)
}

/// Check if a bitmask shape passes the odd-parity filter for sin(x) search.
///
/// Tests `f(-x) ≈ -f(x)` at four probe points `{0.1, 0.5, 1.0, 1.5}`.
/// Returns `True` if all pass (shape is a candidate), `False` otherwise.
///
/// # Arguments (Python)
/// * `shape_bits` — `int` bitmask encoding leaf assignments.
/// * `n_leaves`   — number of leaves.
#[pyfunction]
fn check_parity_bits(shape_bits: u64, n_leaves: usize) -> bool {
    let eval_fn = |x: f64| sin_search::eval_tree_assignment(shape_bits, n_leaves, x);
    sin_search::check_parity(n_leaves, eval_fn)
}

// ── PyO3 module definition ────────────────────────────────────────────────────

/// monogate_core — native EML/BEST evaluation kernels.
///
/// Install with: `maturin develop --release`
/// Then import normally: `import monogate_core`
#[pymodule]
fn monogate_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(eval_eml_batch, m)?)?;
    m.add_function(wrap_pyfunction!(eval_best_batch, m)?)?;
    m.add_function(wrap_pyfunction!(benchmark_rust, m)?)?;
    m.add_function(wrap_pyfunction!(eval_tree_assignment, m)?)?;
    m.add_function(wrap_pyfunction!(check_parity_bits, m)?)?;

    // Expose the parallel threshold so Python can query it
    m.add("PARALLEL_THRESHOLD", evaluator::PARALLEL_THRESHOLD)?;

    // Version string
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
