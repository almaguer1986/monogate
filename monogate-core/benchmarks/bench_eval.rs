//! Criterion benchmarks for the monogate-core EML/BEST evaluators.
//!
//! Run with:
//! ```bash
//! cargo bench
//! # or for a specific bench:
//! cargo bench --bench bench_eval eml_depth2
//! ```
//!
//! HTML reports are written to `target/criterion/`.
//!
//! # What we measure
//!
//! | Benchmark | Description |
//! |-----------|-------------|
//! | `eml_scalar_depth{1,2,3}`  | Single-sample EML eval at various depths |
//! | `best_scalar_depth{1,2,3}` | Single-sample BEST eval at various depths |
//! | `eml_batch_{small,medium,large}` | Batch EML eval (100 / 10k / 1M elements) |
//! | `best_batch_{small,medium,large}`| Batch BEST eval |
//!
//! # Expected numbers (rough; i7-class laptop, release build)
//!
//! | Workload               | Expected throughput |
//! |------------------------|---------------------|
//! | scalar depth=2         | ~80–120 ns/eval     |
//! | batch 10k depth=2      | ~15–25 ns/eval (amortised rayon setup) |
//! | batch 1M depth=2       | ~5–10 ns/eval (full rayon benefit)      |
//!
//! Python FusedEMLActivation baseline (torch, batch=1M, depth=2): ~50–200 μs/eval
//! → expect 50–200× improvement from this Rust path.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use monogate_core::evaluator::{eval_best_batch, eval_best_bottom_up, eval_eml_batch, eval_eml_bottom_up};

// ── Helpers ───────────────────────────────────────────────────────────────────

fn make_leaves(depth: usize) -> (Vec<f64>, Vec<f64>) {
    let n = 1 << depth;
    (vec![0.05f64; n], vec![1.0f64; n])
}

fn make_inputs(n: usize) -> Vec<f64> {
    (0..n).map(|i| -1.0 + 2.0 * (i as f64) / (n as f64)).collect()
}

// ── Scalar benchmarks ─────────────────────────────────────────────────────────

fn bench_eml_scalar(c: &mut Criterion) {
    let mut group = c.benchmark_group("eml_scalar");
    for depth in [1usize, 2, 3] {
        let (w, b) = make_leaves(depth);
        group.bench_with_input(BenchmarkId::new("depth", depth), &depth, |bench, &d| {
            bench.iter(|| eval_eml_bottom_up(black_box(&w), black_box(&b), black_box(0.5), d));
        });
    }
    group.finish();
}

fn bench_best_scalar(c: &mut Criterion) {
    let mut group = c.benchmark_group("best_scalar");
    for depth in [1usize, 2, 3] {
        let (w, b) = make_leaves(depth);
        group.bench_with_input(BenchmarkId::new("depth", depth), &depth, |bench, &d| {
            bench.iter(|| eval_best_bottom_up(black_box(&w), black_box(&b), black_box(0.5), d));
        });
    }
    group.finish();
}

// ── Batch benchmarks ──────────────────────────────────────────────────────────

const SMALL: usize = 100;
const MEDIUM: usize = 10_000;
const LARGE: usize = 1_000_000;

fn bench_eml_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("eml_batch_depth2");
    for &n in &[SMALL, MEDIUM, LARGE] {
        let (w, b) = make_leaves(2);
        let xs = make_inputs(n);
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("n", n), &n, |bench, _| {
            bench.iter(|| eval_eml_batch(black_box(&w), black_box(&b), black_box(&xs), 2));
        });
    }
    group.finish();
}

fn bench_best_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("best_batch_depth2");
    for &n in &[SMALL, MEDIUM, LARGE] {
        let (w, b) = make_leaves(2);
        let xs = make_inputs(n);
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("n", n), &n, |bench, _| {
            bench.iter(|| eval_best_batch(black_box(&w), black_box(&b), black_box(&xs), 2));
        });
    }
    group.finish();
}

fn bench_eml_batch_depths(c: &mut Criterion) {
    let mut group = c.benchmark_group("eml_batch_n10k");
    let xs = make_inputs(10_000);
    group.throughput(Throughput::Elements(10_000));
    for depth in [1usize, 2, 3] {
        let (w, b) = make_leaves(depth);
        group.bench_with_input(BenchmarkId::new("depth", depth), &depth, |bench, &d| {
            bench.iter(|| eval_eml_batch(black_box(&w), black_box(&b), black_box(&xs), d));
        });
    }
    group.finish();
}

// ── Criterion wiring ──────────────────────────────────────────────────────────

criterion_group!(
    benches,
    bench_eml_scalar,
    bench_best_scalar,
    bench_eml_batch,
    bench_best_batch,
    bench_eml_batch_depths,
);
criterion_main!(benches);
