pub mod evaluator;
pub mod sin_search;

#[cfg(feature = "python")]
mod python_bindings {
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
    use std::time::Instant;
    use super::{evaluator, sin_search};

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
                "leaf_w has {} elements but depth={depth} requires {n_leaves} leaves",
                w.len()
            )));
        }
        if b.len() != n_leaves {
            return Err(PyValueError::new_err(format!(
                "leaf_b has {} elements but depth={depth} requires {n_leaves} leaves",
                b.len()
            )));
        }
        let result = match operator.to_ascii_uppercase().as_str() {
            "EML" => evaluator::eval_eml_batch(w, b, xs, depth),
            "BEST" => evaluator::eval_best_batch(w, b, xs, depth),
            other => return Err(PyValueError::new_err(format!(
                "unknown operator {other:?}. Choose 'EML' or 'BEST'."
            ))),
        };
        Ok(result.into_pyarray_bound(py))
    }

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
                "leaf_w/leaf_b must have {n_leaves} elements for depth={depth}"
            )));
        }
        let result = evaluator::eval_best_batch(w, b, xs, depth);
        Ok(result.into_pyarray_bound(py))
    }

    #[pyfunction]
    #[pyo3(signature = (n = 100_000, depth = 2))]
    fn benchmark_rust(n: usize, depth: usize) -> f64 {
        let n_leaves = 1usize << depth;
        let leaf_w = vec![0.05f64; n_leaves];
        let leaf_b = vec![1.0f64; n_leaves];
        let xs: Vec<f64> = (0..n).map(|i| -1.0 + 2.0 * (i as f64) / (n as f64)).collect();
        let start = Instant::now();
        let _result = evaluator::eval_eml_batch(&leaf_w, &leaf_b, &xs, depth);
        (n as f64) / start.elapsed().as_secs_f64() / 1_000_000.0
    }

    #[pyfunction]
    fn eval_tree_assignment(shape_bits: u64, n_leaves: usize, probe_x: f64) -> Option<f64> {
        sin_search::eval_tree_assignment(shape_bits, n_leaves, probe_x)
    }

    #[pyfunction]
    fn check_parity_bits(shape_bits: u64, n_leaves: usize) -> bool {
        let eval_fn = |x: f64| sin_search::eval_tree_assignment(shape_bits, n_leaves, x);
        sin_search::check_parity(n_leaves, eval_fn)
    }

    #[pymodule]
    pub fn monogate_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(eval_eml_batch, m)?)?;
        m.add_function(wrap_pyfunction!(eval_best_batch, m)?)?;
        m.add_function(wrap_pyfunction!(benchmark_rust, m)?)?;
        m.add_function(wrap_pyfunction!(eval_tree_assignment, m)?)?;
        m.add_function(wrap_pyfunction!(check_parity_bits, m)?)?;
        m.add("PARALLEL_THRESHOLD", evaluator::PARALLEL_THRESHOLD)?;
        m.add("__version__", env!("CARGO_PKG_VERSION"))?;
        Ok(())
    }
}

#[cfg(feature = "python")]
pub use python_bindings::monogate_core;
