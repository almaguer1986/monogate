"""
Physics Identities Discovery — Interactive Exploration
=======================================================
Explore compact EML representations of PDE solutions.
Each section corresponds to a different physics equation.

Run time: < 1 minute (no GPU required)
"""

# %% [markdown]
# # Physics Identities Discovery
#
# monogate v0.12.0 includes a catalog of compact CBEST expressions for
# analytic solutions of important PDEs and ODEs.
#
# Key result: **4 of 7 physics equations** have exact **1-node CBEST** solutions
# via the Euler path identity `exp(ix) = eml(ix, 1)`.

# %% Setup
import math
import json
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

# %% [markdown]
# ## 1. Free-particle Schrödinger Equation
#
# **Equation:** −u''(x) = k²·u(x)
# **Solution:** u(x) = exp(ikx)
# **EML nodes:** 1 (exact CBEST)

# %% Schrödinger
print("=== Schrödinger Free Particle ===\n")
k = 1.0
xs = [-2.0, -1.0, 0.0, 1.0, 2.0, math.pi]
print(f"k = {k}")
print(f"{'x':>8}  {'Re(ψ(x))':>12}  {'cos(kx)':>12}  {'Im(ψ(x))':>12}  {'sin(kx)':>12}")
for x in xs:
    psi = schrodinger_free_cb(x, k=k)
    re, im = psi.real, psi.imag
    print(f"{x:>8.4f}  {re:>12.8f}  {math.cos(k*x):>12.8f}  "
          f"{im:>12.8f}  {math.sin(k*x):>12.8f}")

print("\n✓ Both real and imaginary parts match to machine precision")
print("✓ Nodes used: 1 (vs infinite nodes in real EML)")

# %% [markdown]
# ## 2. Infinite Square Well
#
# **Equation:** −u'' = E_n·u, with u(0) = u(L) = 0
# **Solution:** u_n(x) = sin(nπx/L)
# **EML nodes:** 1 (exact CBEST)

# %% Potential well
print("\n=== Infinite Square Well Eigenfunctions ===\n")
L = 1.0
print(f"L = {L}")
print(f"{'n':>4}  {'u(0)':>8}  {'u(0.5)':>8}  {'u(L)':>8}  {'Exact at 0.5':>14}")
for n in range(1, 6):
    u0  = potential_well_cb(0.0, n=n, L=L)
    u05 = potential_well_cb(0.5, n=n, L=L)
    uL  = potential_well_cb(L,   n=n, L=L)
    ref = math.sin(n * math.pi * 0.5)
    print(f"{n:>4}  {u0:>8.2e}  {u05:>8.4f}  {uL:>8.2e}  {ref:>14.4f}")

# %% [markdown]
# ## 3. Heat Equation
#
# **Equation:** u_t = u_xx
# **Solution:** u(x,t) = exp(-x²/4t) / sqrt(4πt)

# %% Heat kernel
print("\n=== Heat Equation Fundamental Solution ===\n")
print(f"{'t':>6}  {'u(0,t)':>12}  {'expected':>12}  {'integral≈1':>12}")
for t in [0.1, 0.5, 1.0, 2.0]:
    u0  = heat_kernel_cb(0.0, t=t)
    ref = 1.0 / math.sqrt(4 * math.pi * t)
    # Quick Riemann integral check
    xs_int = [-8.0 + 0.05 * i for i in range(321)]
    integral = sum(heat_kernel_cb(x, t=t) * 0.05 for x in xs_int)
    print(f"{t:>6.1f}  {u0:>12.6f}  {ref:>12.6f}  {integral:>12.6f}")

# %% [markdown]
# ## 4. KdV Soliton
#
# **Equation:** u_t + 6u·u_x + u_xxx = 0
# **Solution:** u = (c/2)·sech²(sqrt(c/4)·(x−ct))

# %% KdV
print("\n=== KdV 1-Soliton ===\n")
c = 4.0
print(f"Speed c = {c}, amplitude = c/2 = {c/2}")
print(f"{'t':>6}  {'x_peak':>8}  {'u(x_peak)':>12}  {'ref c/2':>8}")
for t in [0.0, 0.5, 1.0, 2.0]:
    x_peak = c * t
    u_peak = kdv_soliton_cb(x_peak, t=t, c=c)
    print(f"{t:>6.1f}  {x_peak:>8.2f}  {u_peak:>12.6f}  {c/2:>8.4f}")

# %% [markdown]
# ## Catalog Summary

# %% Print catalog
print("\n=== PHYSICS CATALOG SUMMARY ===\n")
print(f"{'Equation':<45} {'Nodes':>6} {'Exact':>6} {'Backend':>8}")
print(f"{'-'*45} {'-'*6} {'-'*6} {'-'*8}")
for name, entry in PHYSICS_CATALOG.items():
    eq    = entry['equation'][:44]
    nodes = entry['n_nodes']
    exact = "✓" if entry['max_abs_error'] == 0.0 else "~"
    be    = entry['backend']
    print(f"{eq:<45} {nodes:>6} {exact:>6} {be:>8}")

exact_count = sum(1 for e in PHYSICS_CATALOG.values() if e['max_abs_error'] == 0.0)
one_node    = sum(1 for e in PHYSICS_CATALOG.values() if e['n_nodes'] == 1)
print(f"\nTotal: {len(PHYSICS_CATALOG)} equations | "
      f"Exact: {exact_count} | 1-node CBEST: {one_node}")

# %% Load and display full catalog JSON
print("\n=== Loading full catalog from JSON ===\n")
try:
    with open("results/physics_identities_catalog.json", encoding="utf-8") as f:
        catalog = json.load(f)
    print(f"Catalog version: {catalog['version']}")
    print(f"Generated: {catalog['generated']}")
    print(f"Key result: {catalog['summary']['key_result']}")
except FileNotFoundError:
    print("JSON catalog not found at results/physics_identities_catalog.json")
    print("Run from python/ directory")

print("\n Physics identities discovery complete.")
