# %% [markdown]
# # monogate Special Functions Gallery
#
# Pre-computed short CBEST/BEST expressions for 14 special functions.
#
# Key results:
# - sin(x) and cos(x): **1 CBEST node each** (Euler path)
# - Fresnel integrand sin(πx²/2): **2 CBEST nodes**
# - erf(x): **5 CBEST nodes** (tanh approximation)
# - Bessel J₀(x): **7 CBEST nodes** (complex MCTS)
# - Airy Ai(x): **9 CBEST nodes** (complex MCTS)
#
# Run as a script or open in Jupyter / VS Code with Python extension.

# %%
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from monogate.special import (
    CATALOG,
    sin_cb, cos_cb,
    sinh_cb, cosh_cb, tanh_cb, sech_cb,
    erf_cb, j0_cb, ai_cb,
    fresnel_s_integrand_cb, fresnel_c_integrand_cb,
    fresnel_s_cb, fresnel_c_cb,
    lgamma_cb, digamma_cb,
    catalog_summary, save_catalog,
)

print("monogate.special — Special Functions Gallery")
print("=" * 55)
print()
print(catalog_summary())

# %% [markdown]
# ## 1. Exact trig: 1 CBEST node each

# %%
print()
print("1. sin(x) and cos(x) — 1 CBEST node each")
print("-" * 45)

xs = np.linspace(0, 2 * math.pi, 9)
print(f"  {'x':>8}  {'sin_cb(x)':>12}  {'math.sin(x)':>12}  {'error':>10}")
print("  " + "-" * 48)
for x in xs:
    got = sin_cb(x)
    ref = math.sin(x)
    print(f"  {x:>8.4f}  {got:>12.8f}  {ref:>12.8f}  {abs(got-ref):>10.2e}")

max_sin_err = max(abs(sin_cb(x) - math.sin(x)) for x in np.linspace(-10, 10, 1000))
max_cos_err = max(abs(cos_cb(x) - math.cos(x)) for x in np.linspace(-10, 10, 1000))
print(f"\n  Max |sin_cb - sin| over [-10,10]: {max_sin_err:.2e}")
print(f"  Max |cos_cb - cos| over [-10,10]: {max_cos_err:.2e}")
print(f"  Node count: {CATALOG['sin'].n_nodes} CBEST (vs 63 for 8-term Taylor)")

# %% [markdown]
# ## 2. Hyperbolic functions

# %%
print()
print("2. Hyperbolic functions — algebraic BEST constructions")
print("-" * 55)

hyp_fns = [
    ("sinh", sinh_cb, math.sinh, CATALOG["sinh"].n_nodes),
    ("cosh", cosh_cb, math.cosh, CATALOG["cosh"].n_nodes),
    ("tanh", tanh_cb, math.tanh, CATALOG["tanh"].n_nodes),
    ("sech", sech_cb, lambda x: 1.0/math.cosh(x), CATALOG["sech"].n_nodes),
]

xs_hyp = np.linspace(0.1, 3.0, 200)
print(f"  {'Function':>8}  {'Nodes':>6}  {'Max Error':>12}")
print("  " + "-" * 32)
for name, fn_cb, fn_ref, n in hyp_fns:
    errs = [abs(fn_cb(x) - fn_ref(x)) for x in xs_hyp]
    print(f"  {name:>8}  {n:>6}  {max(errs):>12.2e}")

# Pythagorean identity check
print(f"\n  cosh²(2) - sinh²(2) = {cosh_cb(2.0)**2 - sinh_cb(2.0)**2:.15f}  (should be 1.0)")

# %% [markdown]
# ## 3. Fresnel functions

# %%
print()
print("3. Fresnel functions")
print("-" * 45)

xs_f = np.linspace(0.0, 4.0, 200)
si = [fresnel_s_integrand_cb(x) for x in xs_f]
ci = [fresnel_c_integrand_cb(x) for x in xs_f]
s  = [fresnel_s_cb(x) for x in xs_f]
c  = [fresnel_c_cb(x) for x in xs_f]

# Verify integrand formula
print(f"  sin_integrand at x=1:  {fresnel_s_integrand_cb(1.0):.8f}")
print(f"  sin(pi/2):             {math.sin(math.pi/2.0):.8f}  (should match)")
print(f"  S(1.0) = {fresnel_s_cb(1.0):.6f}  (expected ≈ 0.4383)")
print(f"  C(1.0) = {fresnel_c_cb(1.0):.6f}  (expected ≈ 0.9045)")
print(f"\n  Fresnel integrand: 2 CBEST nodes (Im/Re of eml(i*pi*x^2/2, 1))")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(xs_f, si, label="sin(πx²/2) = Im(eml(i·πx²/2, 1))", color="steelblue")
axes[0].plot(xs_f, ci, label="cos(πx²/2) = Re(eml(i·πx²/2, 1))", color="darkorange")
axes[0].set_title("Fresnel integrands — 2 CBEST nodes each")
axes[0].set_xlabel("x")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(xs_f, s, label="S(x) = ∫₀ˣ sin(πt²/2) dt", color="steelblue")
axes[1].plot(xs_f, c, label="C(x) = ∫₀ˣ cos(πt²/2) dt", color="darkorange")
axes[1].set_title("Fresnel integrals")
axes[1].set_xlabel("x")
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("fresnel_gallery.png", dpi=120)
plt.close()
print("  Saved: fresnel_gallery.png")

# %% [markdown]
# ## 4. erf(x) — 5-node CBEST approximation

# %%
print()
print("4. erf(x) — tanh(1.2025x) approximation")
print("-" * 45)

xs_e = np.linspace(-3.0, 3.0, 300)
erf_approx = [erf_cb(x) for x in xs_e]
erf_exact  = [math.erf(x) for x in xs_e]
erf_error  = [abs(erf_approx[i] - erf_exact[i]) for i in range(len(xs_e))]

print(f"  Nodes: {CATALOG['erf'].n_nodes} CBEST  |  Max abs error: {max(erf_error):.4f}")
print(f"  Formula: {CATALOG['erf'].formula}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(xs_e, erf_exact,  label="math.erf(x)", color="black", linewidth=1.5)
axes[0].plot(xs_e, erf_approx, label="erf_cb(x) = tanh(1.2025x)", color="crimson",
             linestyle="--", linewidth=1.5)
axes[0].set_title(f"erf(x) — {CATALOG['erf'].n_nodes} CBEST nodes")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].semilogy(xs_e, [max(e, 1e-16) for e in erf_error], color="crimson")
axes[1].set_title("Absolute error: |erf_cb - math.erf|")
axes[1].set_xlabel("x")
axes[1].set_ylabel("|error|")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("erf_gallery.png", dpi=120)
plt.close()
print("  Saved: erf_gallery.png")

# %% [markdown]
# ## 5. Bessel J₀(x) — 7 CBEST nodes

# %%
print()
print("5. Bessel J₀(x) — 7 CBEST nodes (complex MCTS construction)")
print("-" * 60)

xs_j = np.linspace(0.0, 10.0, 300)
j0_vals = [j0_cb(x) for x in xs_j]
print(f"  J₀(0) = {j0_cb(0.0):.8f}  (should be 1.0)")
print(f"  First zero near x = 2.4048")
print(f"  j0_cb(2.4048) = {j0_cb(2.4048):.6f}  (should be ≈ 0)")

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(xs_j, j0_vals, color="darkgreen", linewidth=1.5)
ax.axhline(0, color="black", linewidth=0.8, linestyle=":")
ax.set_title(f"Bessel J₀(x) — {CATALOG['j0'].n_nodes} CBEST nodes")
ax.set_xlabel("x")
ax.set_ylabel("J₀(x)")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("j0_gallery.png", dpi=120)
plt.close()
print("  Saved: j0_gallery.png")

# %% [markdown]
# ## 6. Airy Ai(x) — 9 CBEST nodes

# %%
print()
print("6. Airy Ai(x) — 9 CBEST nodes (complex MCTS construction)")
print("-" * 60)

xs_a = np.linspace(-8.0, 4.0, 400)
ai_vals = [ai_cb(x) for x in xs_a]
print(f"  Ai(0) = {ai_cb(0.0):.8f}  (should be ≈ 0.35503)")
print(f"  Ai(2) = {ai_cb(2.0):.8f}")

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(xs_a, ai_vals, color="purple", linewidth=1.5)
ax.axhline(0, color="black", linewidth=0.8, linestyle=":")
ax.set_ylim(-0.6, 0.6)
ax.set_title(f"Airy Ai(x) — {CATALOG['airy_ai'].n_nodes} CBEST nodes")
ax.set_xlabel("x")
ax.set_ylabel("Ai(x)")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("airy_gallery.png", dpi=120)
plt.close()
print("  Saved: airy_gallery.png")

# %% [markdown]
# ## 7. Log-Gamma and Digamma

# %%
print()
print("7. lgamma_cb and digamma_cb — Stirling series")
print("-" * 50)

xs_g = np.linspace(0.5, 15.0, 300)
lgamma_vals = [lgamma_cb(x) for x in xs_g]
lgamma_ref  = [math.lgamma(x) for x in xs_g]
lgamma_err  = [abs(a - b) for a, b in zip(lgamma_vals, lgamma_ref)]

print(f"  lgamma_cb: max error over [0.5, 15] = {max(lgamma_err):.2e}")
print(f"  digamma_cb(1) = {digamma_cb(1.0):.8f}  (should be ≈ -0.57722)")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].semilogy(xs_g, [max(e, 1e-16) for e in lgamma_err], color="teal")
axes[0].set_title(f"lgamma_cb error (Stirling, {CATALOG['lgamma'].n_nodes} BEST nodes)")
axes[0].set_xlabel("x")
axes[0].set_ylabel("|error|")
axes[0].grid(alpha=0.3)

dig_vals = [digamma_cb(x) for x in xs_g]
axes[1].plot(xs_g, dig_vals, color="teal")
axes[1].axhline(0, color="black", linewidth=0.8, linestyle=":")
axes[1].set_title(f"digamma_cb(x) ({CATALOG['digamma'].n_nodes} BEST nodes)")
axes[1].set_xlabel("x")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("lgamma_gallery.png", dpi=120)
plt.close()
print("  Saved: lgamma_gallery.png")

# %% [markdown]
# ## 8. Complete catalog summary

# %%
print()
print("8. CATALOG summary")
print("-" * 50)
print()
print(f"  {'Function':<24} {'Nodes':>6}  {'Backend':>7}  {'Max Error':>10}  Formula")
print("  " + "-" * 75)
for entry in sorted(CATALOG.values(), key=lambda e: e.n_nodes):
    print(
        f"  {entry.name:<24} {entry.n_nodes:>6}  {entry.backend:>7}  "
        f"{entry.max_abs_error:>10.2e}  {entry.formula[:35]}"
    )

# Save the catalog
import os
results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(results_dir, exist_ok=True)
catalog_path = os.path.join(results_dir, "special_catalog.json")
save_catalog(catalog_path)
print(f"\n  Catalog saved: {catalog_path}")

# %% [markdown]
# ## Summary
#
# | Construction | Nodes | Accuracy |
# |---|---|---|
# | sin, cos (Euler path) | **1 CBEST** | Machine precision |
# | Fresnel integrand | **2 CBEST** | Machine precision |
# | erf (tanh approx) | **5 CBEST** | Max error ~1.5e-2 |
# | Bessel J₀ (MCTS) | **7 CBEST** | MSE < 1e-4 |
# | Airy Ai (MCTS) | **9 CBEST** | MSE ~2e-3 |
# | sinh, cosh | **9–15 BEST** | Machine precision |
# | lgamma (Stirling) | **~12 BEST** | Max error < 1e-9 |
#
# **Open:** Find a shorter CBEST construction for J₀ (currently 7 nodes).
# See THEORY.md Conjecture C6.

print()
print("Gallery complete.")
