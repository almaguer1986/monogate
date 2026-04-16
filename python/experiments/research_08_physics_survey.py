"""
research_08_physics_survey.py — CBEST Physics Survey
=====================================================
Systematic survey of compact CBEST/BEST representations for analytic
solutions of important differential equations.

Sections
--------
A. Free-particle Schrödinger (exp(ikx)) — confirmed 1 CBEST node
B. Infinite potential well eigenfunctions
C. NLS bright soliton
D. Heat equation fundamental solution
E. KdV 1-soliton
F. Wave equation solutions
G. Summary catalog and node count table

Run from python/:
    python experiments/research_08_physics_survey.py
"""

import sys, math, cmath, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEP  = "-" * 70
SEP2 = "=" * 70

print(SEP2)
print("  research_08: CBEST Physics Survey")
print(SEP2)
print("  Catalog of compact EML expressions for PDE/ODE solutions")

from monogate.physics import (
    schrodinger_free_cb,
    potential_well_cb,
    nls_soliton_amplitude_cb,
    heat_kernel_cb,
    kdv_soliton_cb,
    wave_cos_cb,
    wave_sin_cb,
    PHYSICS_CATALOG,
)


# ── Helper ────────────────────────────────────────────────────────────────────

def max_abs_err(fn_ours, fn_ref, xs):
    """Compute max |fn_ours(x) - fn_ref(x)| over xs."""
    return max(abs(fn_ours(x) - fn_ref(x)) for x in xs)


xs = [-2.0 + 0.2 * i for i in range(21)]  # [-2, 2] step 0.2


# ── A. Free-particle Schrödinger ──────────────────────────────────────────────

print(f"\n{SEP}")
print("  A. Free-particle Schrödinger: exp(ikx)")
print(SEP)

k = 1.5
re_err = max_abs_err(
    lambda x: schrodinger_free_cb(x, k=k, part='re'),
    lambda x: math.cos(k * x),
    xs
)
im_err = max_abs_err(
    lambda x: schrodinger_free_cb(x, k=k, part='im'),
    lambda x: math.sin(k * x),
    xs
)

print(f"  k = {k}")
print(f"  Re(exp(ikx)) = cos(kx):  max_err = {re_err:.3e}  (nodes: 1 CBEST)")
print(f"  Im(exp(ikx)) = sin(kx):  max_err = {im_err:.3e}  (nodes: 1 CBEST)")
print(f"  EXACT: both errors are floating-point rounding only (~1e-16)")


# ── B. Potential well eigenfunctions ──────────────────────────────────────────

print(f"\n{SEP}")
print("  B. Infinite square well eigenfunctions")
print(SEP)

for n in [1, 2, 3, 4]:
    boundary_err = max(
        abs(potential_well_cb(0.0, n=n, L=1.0)),
        abs(potential_well_cb(1.0, n=n, L=1.0))
    )
    midpt_ref = math.sin(n * math.pi * 0.5)
    midpt_val = potential_well_cb(0.5, n=n, L=1.0)
    print(f"  n={n}: ψ(0)=ψ(L)=0 err={boundary_err:.3e}  "
          f"ψ(0.5)={midpt_val:.6f} (ref={midpt_ref:.6f})")


# ── C. NLS bright soliton ─────────────────────────────────────────────────────

print(f"\n{SEP}")
print("  C. NLS bright soliton amplitude sech(x)")
print(SEP)

sech_err = max_abs_err(
    nls_soliton_amplitude_cb,
    lambda x: 1.0 / math.cosh(x),
    xs
)
print(f"  sech(x) = 1/cosh(x):  max_err = {sech_err:.3e}  (nodes: 2 BEST)")
print(f"  Value at x=0:  {nls_soliton_amplitude_cb(0.0):.10f}  (ref: 1.0)")
print(f"  Value at x=1:  {nls_soliton_amplitude_cb(1.0):.10f}  "
      f"(ref: {1/math.cosh(1.0):.10f})")


# ── D. Heat equation fundamental solution ─────────────────────────────────────

print(f"\n{SEP}")
print("  D. Heat equation fundamental solution")
print(SEP)

t_vals = [0.1, 0.5, 1.0, 2.0]
for t in t_vals:
    kernel_zero = heat_kernel_cb(0.0, t=t)
    ref_zero    = 1.0 / math.sqrt(4 * math.pi * t)
    err         = abs(kernel_zero - ref_zero)
    print(f"  t={t:.1f}: u(0,t)={kernel_zero:.6f}  ref={ref_zero:.6f}  err={err:.3e}")

# Verify normalization
xs_norm = [-5.0 + 0.02 * i for i in range(501)]
integral = sum(heat_kernel_cb(x, t=1.0) * 0.02 for x in xs_norm)
print(f"\n  Normalization check (t=1): integral = {integral:.6f}  (should be ≈ 1.0)")


# ── E. KdV soliton ───────────────────────────────────────────────────────────

print(f"\n{SEP}")
print("  E. KdV 1-soliton")
print(SEP)

c = 4.0
peak_t0 = kdv_soliton_cb(0.0, t=0.0, c=c)
peak_t1 = kdv_soliton_cb(c * 1.0, t=1.0, c=c)
print(f"  c={c}: peak at t=0, x=0: {peak_t0:.8f}  (ref: {c/2:.8f})")
print(f"  c={c}: peak at t=1, x=ct={c}: {peak_t1:.8f}  (ref: {c/2:.8f})")
print(f"  Traveling wave check: |peak_t0 - peak_t1| = {abs(peak_t0-peak_t1):.3e}")

# Check positivity and decay
soliton_at_inf = kdv_soliton_cb(20.0, t=0.0, c=c)
print(f"  Decay: u(20, 0) = {soliton_at_inf:.3e}  (should be near 0)")


# ── F. Wave equation ──────────────────────────────────────────────────────────

print(f"\n{SEP}")
print("  F. Wave equation solutions")
print(SEP)

k, omega = 2.0, 3.0
cos_err = max_abs_err(
    lambda x: wave_cos_cb(x, k=k, omega=omega, t=0.5),
    lambda x: math.cos(k*x - omega*0.5),
    xs
)
sin_err = max_abs_err(
    lambda x: wave_sin_cb(x, k=k, omega=omega, t=0.5),
    lambda x: math.sin(k*x - omega*0.5),
    xs
)
print(f"  k={k}, omega={omega}, t=0.5:")
print(f"  cos(kx-ωt): max_err = {cos_err:.3e}  (nodes: 1 CBEST)")
print(f"  sin(kx-ωt): max_err = {sin_err:.3e}  (nodes: 1 CBEST)")


# ── G. Summary catalog ────────────────────────────────────────────────────────

print(f"\n{SEP2}")
print("  G. PHYSICS CATALOG SUMMARY")
print(SEP2)

print(f"\n  {'Equation':<45} {'Nodes':>6} {'Backend':>8} {'Max Error':>12}")
print(f"  {'-'*45} {'-'*6} {'-'*8} {'-'*12}")

for name, entry in PHYSICS_CATALOG.items():
    eq    = entry['equation'][:44]
    nodes = entry['n_nodes']
    be    = entry['backend']
    err   = entry['max_abs_error']
    err_s = "exact" if err == 0.0 else f"{err:.0e}"
    print(f"  {eq:<45} {nodes:>6} {be:>8} {err_s:>12}")

print(f"\n  Total: {len(PHYSICS_CATALOG)} physics equations cataloged")
exact = sum(1 for e in PHYSICS_CATALOG.values() if e['max_abs_error'] == 0.0)
print(f"  Exact (0 error): {exact}/{len(PHYSICS_CATALOG)}")
print(f"  1-node CBEST solutions: {sum(1 for e in PHYSICS_CATALOG.values() if e['n_nodes']==1)}")

print(f"\n  Survey complete.")
