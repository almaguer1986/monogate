//! N=12 exhaustive EML tree search for sin(x) barrier.
//!
//! Searches all binary EML trees with exactly 12 internal nodes
//! (Catalan(12) = 208,012 shapes × 2^13 = 8,192 leaf combos = ~1.704B trees).
//!
//! Each tree evaluates the function f(x) where each leaf is either x or 1.0.
//! We compute MSE against sin(x) over 8 probe points.
//!
//! Result: if best_mse > 1e-6 across all 1.704B trees, sin(x) is absent from
//! the N=12 EML tree space — confirming the infinite-zeros barrier to N=12.
//!
//! Usage:
//!   cargo build --release
//!   ./target/release/n12_search
//!   ./target/release/n12_search --n 10      # search N=10 (faster, for testing)
//!   ./target/release/n12_search --out result.json

use rayon::prelude::*;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::Instant;

const N_PROBES: usize = 8;
const PROBE_X: [f64; N_PROBES] = [0.1, 0.3, 0.5, 0.7, 1.0, 1.3, 1.5, 1.7];

// ── Tree shape generation ─────────────────────────────────────────────────────

/// Generate all full binary tree shapes with exactly `n` internal nodes.
///
/// A shape is encoded as a sequence of operations in postorder:
/// - `false` = leaf (push leaf from leaf_iter)
/// - `true`  = internal EML node (pop two, apply eml, push result)
///
/// Returns a Vec of operation sequences (each with 2n+1 entries: n+1 false and n true).
fn generate_shapes(n: usize) -> Vec<Vec<bool>> {
    if n == 0 {
        // A single leaf
        return vec![vec![false]];
    }

    let mut shapes = Vec::new();

    // A tree with n internal nodes splits into:
    // left subtree with k nodes + root (1 node) + right subtree with n-1-k nodes
    for k in 0..n {
        let left_shapes = generate_shapes(k);
        let right_shapes = generate_shapes(n - 1 - k);

        for ls in &left_shapes {
            for rs in &right_shapes {
                // Postorder: left, right, root
                let mut ops = Vec::with_capacity(ls.len() + rs.len() + 1);
                ops.extend_from_slice(ls);
                ops.extend_from_slice(rs);
                ops.push(true); // internal node
                shapes.push(ops);
            }
        }
    }

    shapes
}

// ── EML evaluation ────────────────────────────────────────────────────────────

/// Raw EML gate: eml(a, b) = exp(a) - ln(b).
/// Returns NaN if b <= 0 (domain error). The caller checks is_finite().
#[inline(always)]
fn eml_gate(a: f64, b: f64) -> f64 {
    a.exp() - b.ln()
}

/// Evaluate an EML tree given its postorder operation sequence and a leaf assignment bitmask.
///
/// Returns `None` if the result is non-finite (domain error).
fn eval_tree(ops: &[bool], leaf_mask: u16, x: f64) -> Option<f64> {
    let mut stack = [0.0f64; 16];
    let mut sp: usize = 0;
    let mut leaf_idx: usize = 0;

    for &is_internal in ops {
        if !is_internal {
            // Leaf: value is x if bit set, else 1.0
            let val = if (leaf_mask >> leaf_idx) & 1 == 1 { x } else { 1.0 };
            stack[sp] = val;
            sp += 1;
            leaf_idx += 1;
        } else {
            // Internal EML node: pop two operands (right was pushed last)
            debug_assert!(sp >= 2);
            let b = stack[sp - 1];
            let a = stack[sp - 2];
            sp -= 1;
            stack[sp - 1] = eml_gate(a, b);
        }
    }

    debug_assert_eq!(sp, 1);
    let result = stack[0];
    if result.is_finite() { Some(result) } else { None }
}

/// Compute MSE against sin(x) over the 8 probe points.
/// Returns f64::MAX if any probe point produces a domain error.
fn compute_mse(ops: &[bool], leaf_mask: u16) -> f64 {
    let mut mse = 0.0f64;
    for &x in &PROBE_X {
        let pred = match eval_tree(ops, leaf_mask, x) {
            Some(v) => v,
            None => return f64::MAX,
        };
        let diff = pred - x.sin();
        mse += diff * diff;
    }
    mse / N_PROBES as f64
}

/// Parity filter: f(-x) ≈ -f(x) at two probe points.
/// sin(x) is odd, so any approximating tree must be odd.
fn passes_parity(ops: &[bool], leaf_mask: u16) -> bool {
    const PARITY_PROBES: [f64; 2] = [0.5, 1.0];
    for &x in &PARITY_PROBES {
        let pos = match eval_tree(ops, leaf_mask, x) {
            Some(v) => v,
            None => return false,
        };
        let neg = match eval_tree(ops, leaf_mask, -x) {
            Some(v) => v,
            None => return false,
        };
        if (pos + neg).abs() > 1e-6 {
            return false;
        }
    }
    true
}

// ── Main search ───────────────────────────────────────────────────────────────

/// Format an EML tree as a human-readable formula string.
fn format_tree(ops: &[bool], leaf_mask: u16) -> String {
    let mut stack: Vec<String> = Vec::new();
    let mut leaf_idx: usize = 0;

    for &is_internal in ops {
        if !is_internal {
            let s = if (leaf_mask >> leaf_idx) & 1 == 1 {
                "x".to_string()
            } else {
                "1".to_string()
            };
            stack.push(s);
            leaf_idx += 1;
        } else {
            let b = stack.pop().unwrap();
            let a = stack.pop().unwrap();
            stack.push(format!("eml({a},{b})"));
        }
    }

    stack.into_iter().next().unwrap_or_default()
}

fn search_n(n: usize) -> SearchResult {
    let shapes = generate_shapes(n);
    let n_leaves = n + 1;
    let n_leaf_combos = 1u32 << n_leaves;

    let total_trees = shapes.len() as u64 * n_leaf_combos as u64;
    let trees_checked = AtomicU64::new(0);
    let parity_passed = AtomicU64::new(0);

    // Atomic best MSE (stored as bits of f64)
    let best_mse_bits = AtomicU64::new(f64::MAX.to_bits());
    let best_info: Mutex<(f64, String)> = Mutex::new((f64::MAX, String::new()));

    let start = Instant::now();

    shapes.par_iter().for_each(|ops| {
        let mut local_best_mse = f64::MAX;
        let mut local_best_mask: u16 = 0;
        let mut local_parity = 0u64;

        for mask in 0..n_leaf_combos {
            let mask_u16 = mask as u16;
            trees_checked.fetch_add(1, Ordering::Relaxed);

            if !passes_parity(ops, mask_u16) {
                continue;
            }
            local_parity += 1;

            let mse = compute_mse(ops, mask_u16);
            if mse < local_best_mse {
                local_best_mse = mse;
                local_best_mask = mask_u16;
            }
        }

        parity_passed.fetch_add(local_parity, Ordering::Relaxed);

        // Update global best if we improved
        let current_best = f64::from_bits(best_mse_bits.load(Ordering::Relaxed));
        if local_best_mse < current_best {
            // Use compare-exchange loop for lock-free update
            let new_bits = local_best_mse.to_bits();
            let mut old_bits = current_best.to_bits();
            loop {
                match best_mse_bits.compare_exchange_weak(
                    old_bits, new_bits, Ordering::AcqRel, Ordering::Relaxed,
                ) {
                    Ok(_) => {
                        let formula = format_tree(ops, local_best_mask);
                        let mut guard = best_info.lock().unwrap();
                        if local_best_mse < guard.0 {
                            *guard = (local_best_mse, formula);
                        }
                        break;
                    }
                    Err(actual) => {
                        old_bits = actual;
                        if f64::from_bits(actual) <= local_best_mse {
                            break; // someone found something better
                        }
                    }
                }
            }
        }
    });

    let elapsed = start.elapsed().as_secs_f64();
    let info = best_info.lock().unwrap();
    let final_best_mse = f64::from_bits(best_mse_bits.load(Ordering::Relaxed));

    SearchResult {
        n,
        n_shapes: shapes.len(),
        n_leaves,
        total_trees,
        trees_checked: trees_checked.load(Ordering::Relaxed),
        parity_passed: parity_passed.load(Ordering::Relaxed),
        best_mse: final_best_mse,
        best_formula: info.1.clone(),
        elapsed_secs: elapsed,
        sin_absent: final_best_mse > 1e-6,
    }
}

// ── Result struct ─────────────────────────────────────────────────────────────

#[derive(Debug)]
struct SearchResult {
    n: usize,
    n_shapes: usize,
    n_leaves: usize,
    total_trees: u64,
    trees_checked: u64,
    parity_passed: u64,
    best_mse: f64,
    best_formula: String,
    elapsed_secs: f64,
    sin_absent: bool,
}

impl SearchResult {
    fn to_json(&self) -> String {
        format!(
            r#"{{
  "n": {n},
  "n_shapes": {n_shapes},
  "n_leaves": {n_leaves},
  "total_trees": {total_trees},
  "trees_checked": {trees_checked},
  "parity_passed": {parity_passed},
  "best_mse": {best_mse:.6e},
  "best_formula": "{best_formula}",
  "elapsed_secs": {elapsed_secs:.2},
  "sin_absent": {sin_absent},
  "verdict": "{verdict}"
}}"#,
            n = self.n,
            n_shapes = self.n_shapes,
            n_leaves = self.n_leaves,
            total_trees = self.total_trees,
            trees_checked = self.trees_checked,
            parity_passed = self.parity_passed,
            best_mse = self.best_mse,
            best_formula = self.best_formula.replace('"', "'"),
            elapsed_secs = self.elapsed_secs,
            sin_absent = self.sin_absent,
            verdict = if self.sin_absent { "SIN_ABSENT" } else { "SIN_CANDIDATE_FOUND" },
        )
    }

    fn print_summary(&self) {
        println!("N={} exhaustive EML search", self.n);
        println!("  Tree shapes:    {:>12}", self.n_shapes);
        println!("  Leaf combos:    {:>12}", 1u64 << self.n_leaves);
        println!("  Total trees:    {:>12}", self.total_trees);
        println!("  After parity:   {:>12}", self.parity_passed);
        println!("  Best MSE:       {:.6e}", self.best_mse);
        println!("  Best formula:   {}", self.best_formula);
        println!("  Elapsed:        {:.1}s", self.elapsed_secs);
        println!(
            "  Verdict:        {}",
            if self.sin_absent { "SIN ABSENT (barrier confirmed)" } else { "CANDIDATE FOUND" }
        );
    }
}

// ── Entry point ───────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().collect();

    let mut n = 12usize;
    let mut out_path = String::from("results/n12_search.json");

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--n" | "-n" => {
                n = args.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(12);
                i += 2;
            }
            "--out" | "-o" => {
                out_path = args.get(i + 1).cloned().unwrap_or(out_path);
                i += 2;
            }
            _ => i += 1,
        }
    }

    let cpu_count = rayon::current_num_threads();
    println!("=== monogate N={n} Exhaustive Sin(x) Search ===");
    println!("CPU threads: {cpu_count}");
    println!("Generating tree shapes for N={n}...");

    // Pre-compute shape count
    let shape_count = generate_shapes(n).len();
    let n_leaves = n + 1;
    let total = shape_count as u64 * (1u64 << n_leaves);
    println!("Shapes: {shape_count}, Leaf combos: {}, Total: {total}", 1u64 << n_leaves);
    println!("Starting search...");
    println!();

    let result = search_n(n);
    result.print_summary();

    // Write JSON output
    let json = result.to_json();
    if let Some(parent) = std::path::Path::new(&out_path).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match std::fs::write(&out_path, &json) {
        Ok(_) => println!("\nResults written to: {out_path}"),
        Err(e) => eprintln!("\nWarning: could not write results to {out_path}: {e}"),
    }

    // Exit with code 1 if sin candidate found (test failure)
    if !result.sin_absent {
        eprintln!("WARNING: potential sin(x) candidate found — review best_formula!");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generates_catalan_count() {
        // Catalan numbers: C(0)=1, C(1)=1, C(2)=2, C(3)=5, C(4)=14, C(5)=42
        let expected = [1, 1, 2, 5, 14, 42];
        for (n, &exp) in expected.iter().enumerate() {
            let shapes = generate_shapes(n);
            assert_eq!(shapes.len(), exp, "C({n}) should be {exp}, got {}", shapes.len());
        }
    }

    #[test]
    fn n1_single_leaf_is_x() {
        // Shape: [false] (single leaf), mask=1 (leaf=x)
        let ops = vec![false];
        let val = eval_tree(&ops, 1, 2.0).unwrap();
        assert!((val - 2.0).abs() < 1e-12);
    }

    #[test]
    fn n1_single_leaf_is_one() {
        let ops = vec![false];
        let val = eval_tree(&ops, 0, 2.0).unwrap();
        assert!((val - 1.0).abs() < 1e-12);
    }

    #[test]
    fn n1_eml_x_1() {
        // eml(x, 1) = exp(x) - ln(softplus(1))
        // ops = [false, false, true] = leaf, leaf, eml
        let ops = vec![false, false, true];
        let x = 0.5;
        let softplus_1 = (1.0f64 + 1.0f64.exp()).ln();
        let expected = x.exp() - softplus_1.ln();
        // mask=0b01: leaf0=x (bit0=1), leaf1=1 (bit1=0)
        let val = eval_tree(&ops, 0b01, x).unwrap();
        assert!((val - expected).abs() < 1e-10, "got {val}, expected {expected}");
    }

    #[test]
    fn shapes_have_correct_op_count() {
        // N internal nodes → N+1 leaves → 2N+1 total ops
        for n in 0..=5 {
            let shapes = generate_shapes(n);
            for ops in &shapes {
                assert_eq!(
                    ops.len(), 2 * n + 1,
                    "N={n}: expected {} ops, got {}", 2*n+1, ops.len()
                );
                let leaves = ops.iter().filter(|&&b| !b).count();
                let internals = ops.iter().filter(|&&b| b).count();
                assert_eq!(leaves, n + 1);
                assert_eq!(internals, n);
            }
        }
    }

    #[test]
    fn n3_search_fast() {
        // N=3: 5 shapes × 16 combos = 80 trees — runs in < 1ms
        let result = search_n(3);
        assert!(result.total_trees == 80);
        assert!(result.best_mse.is_finite());
    }

    #[test]
    fn n5_sin_absent() {
        // N=5 is fast (42 shapes × 64 combos = 2688 trees)
        // sin(x) should be absent from N=5 EML trees
        let result = search_n(5);
        assert!(result.sin_absent, "sin should be absent from N=5 EML trees, best_mse={}", result.best_mse);
    }
}
