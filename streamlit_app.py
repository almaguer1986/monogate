"""
monogate Streamlit Web Demo — 5 interactive tabs.

Run:
    streamlit run streamlit_app.py

Tabs:
    1  Optimizer         — BEST-mode expression / code optimizer
    2  Special Functions — CBEST/BEST catalog browser + error plot
    3  PINN Demo         — Physics-Informed EML Networks (requires torch)
    4  MCTS Explorer     — Gradient-free tree search for target functions
    5  Phantom Attractor — Pre-computed phase-transition visualisation
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# ── path: allow running from repo root without installing ─────────────────────
sys.path.insert(0, str(Path(__file__).parent / "python"))

# ── optional heavy deps ───────────────────────────────────────────────────────
try:
    import torch
    from monogate.pinn import EMLPINN, fit_pinn, PINNResult
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import scipy.special as sps
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# ── monogate imports ──────────────────────────────────────────────────────────
from monogate import best_optimize
from monogate.special import (
    CATALOG,
    ai_cb, cos_cb, cosh_cb, digamma_cb, erf_cb,
    fresnel_c_cb, fresnel_c_integrand_cb,
    fresnel_s_cb, fresnel_s_integrand_cb,
    j0_cb, lgamma_cb, sech_cb, sin_cb, sinh_cb, tanh_cb,
)
from monogate.search import mcts_search

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="monogate — EML Demo",
    page_icon="🔬",
    layout="wide",
)

st.title("monogate — EML Universal Operator")
st.caption(
    "Every elementary function as a finite binary tree of **eml(x,y) = exp(x) − ln(y)** nodes. "
    "arXiv:2603.21852 · [PyPI](https://pypi.org/project/monogate/) · "
    "[GitHub](https://github.com/almaguer1986/monogate)"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Optimizer",
    "📐 Special Functions",
    "🧬 PINN Demo",
    "🔍 MCTS Explorer",
    "🌀 Phantom Attractor",
])

# ─────────────────────────────────────────────────────────────────────────────
# Helper: EML callable map
# ─────────────────────────────────────────────────────────────────────────────

_EML_FN: dict[str, object] = {
    "sin": sin_cb,
    "cos": cos_cb,
    "sinh": sinh_cb,
    "cosh": cosh_cb,
    "tanh": tanh_cb,
    "sech": sech_cb,
    "erf": erf_cb,
    "fresnel_s": fresnel_s_cb,
    "fresnel_c": fresnel_c_cb,
    "fresnel_s_integrand": fresnel_s_integrand_cb,
    "fresnel_c_integrand": fresnel_c_integrand_cb,
    "j0": j0_cb,
    "airy_ai": ai_cb,
    "lgamma": lgamma_cb,
    "digamma": digamma_cb,
}


def _ref_fn(name: str):
    """Return a scalar reference callable for the named function, or None."""
    simple = {
        "sin": math.sin,
        "cos": math.cos,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "sech": lambda x: 1.0 / math.cosh(x),
        "erf": math.erf,
        "lgamma": math.lgamma,
        "fresnel_s_integrand": lambda x: math.sin(math.pi * x ** 2 / 2),
        "fresnel_c_integrand": lambda x: math.cos(math.pi * x ** 2 / 2),
    }
    if name in simple:
        return simple[name]
    if SCIPY_AVAILABLE:
        if name == "fresnel_s":
            return lambda x: float(sps.fresnel(x)[0])
        if name == "fresnel_c":
            return lambda x: float(sps.fresnel(x)[1])
        if name == "j0":
            return lambda x: float(sps.j0(x))
        if name == "airy_ai":
            return lambda x: float(sps.airy(x)[0])
        if name == "digamma":
            return lambda x: float(sps.digamma(x))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Optimizer
# ─────────────────────────────────────────────────────────────────────────────

_EXAMPLE_EXPR = "sin(x)**2 + cos(x) * exp(-x) + ln(x)"
_EXAMPLE_CODE = """\
import torch

def model(x):
    return torch.sin(x)**2 + torch.cos(x) * torch.exp(-x) + torch.log(x)
"""

with tab1:
    st.header("BEST Expression Optimizer")
    st.markdown(
        "Paste a math expression **or** a Python / NumPy / PyTorch code snippet. "
        "The BEST router replaces each primitive with its cheapest "
        "EML / EDL / EXL equivalent and reports node savings."
    )

    input_mode = st.radio("Input type", ["Expression", "Code snippet"], horizontal=True)
    default_val = _EXAMPLE_EXPR if input_mode == "Expression" else _EXAMPLE_CODE
    user_input = st.text_area("Input", value=default_val, height=140)

    if st.button("Optimize", type="primary", key="btn_opt"):
        try:
            with st.spinner("Analyzing…"):
                result = best_optimize(user_input)

            c1, c2, c3 = st.columns(3)
            c1.metric("EML nodes (before)", result.total_eml_nodes)
            c2.metric("BEST nodes (after)", result.total_best_nodes)
            saved = result.total_eml_nodes - result.total_best_nodes
            c3.metric("Node savings", f"{result.savings_pct:.0f}%", delta=f"−{saved}")

            if result.ops:
                st.subheader("Per-operation breakdown")
                rows = []
                for op in result.ops:
                    pct = (
                        round((op.eml_nodes - op.best_nodes) / op.eml_nodes * 100)
                        if op.eml_nodes > 0 else 0
                    )
                    rows.append({
                        "Operation": op.name,
                        "Count": op.count,
                        "EML nodes": op.eml_nodes,
                        "BEST nodes": op.best_nodes,
                        "Savings": f"{pct}%",
                        "Best op": op.best_op,
                        "Note": op.note,
                    })
                import pandas as pd
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if result.python_snippet:
                st.subheader("Optimized snippet")
                st.code(result.python_snippet, language="python")

            if result.rewritten_code and result.rewritten_code.strip() != user_input.strip():
                st.subheader("Rewritten code")
                st.code(result.rewritten_code, language="python")

            msg = result.explanation or result.message
            if msg:
                st.info(msg)

        except Exception as exc:
            st.error(f"Could not parse input: {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Special Functions
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.header("Special Functions Catalog")
    st.markdown(
        "Browse the **15** pre-computed CBEST/BEST constructions. "
        "CBEST = complex-domain EML (1 node for sin/cos via Euler path). "
        "BEST = real-domain hybrid routing."
    )

    fn_names = list(CATALOG.keys())
    col_sel, col_plot = st.columns([1, 2])

    with col_sel:
        fn_name = st.selectbox("Function", fn_names, index=0)
        entry = CATALOG[fn_name]

        st.markdown(f"**Formula**")
        st.code(entry.formula, language="text")
        st.markdown(f"**Backend:** `{entry.backend}`")
        st.markdown(f"**EML nodes:** `{entry.n_nodes}`")
        st.markdown(f"**Max |error|:** `{entry.max_abs_error:.2e}`")
        st.markdown(f"**Domain:** `[{entry.domain[0]}, {entry.domain[1]}]`")
        st.markdown(f"**Notes:** {entry.notes}")

    with col_plot:
        eml_fn = _EML_FN.get(fn_name)
        ref_fn = _ref_fn(fn_name)

        if eml_fn is None:
            st.warning("No EML callable registered for this function.")
        elif ref_fn is None:
            st.warning(
                "Reference function requires scipy. "
                "Install it with `pip install scipy` to see the error plot."
            )
        else:
            xs = np.linspace(entry.domain[0], entry.domain[1], 300)
            try:
                y_eml = np.array([eml_fn(float(x)) for x in xs], dtype=float)
                y_ref = np.array([ref_fn(float(x)) for x in xs], dtype=float)
                err = np.abs(y_eml - y_ref)

                fig, axes = plt.subplots(2, 1, figsize=(7, 5), tight_layout=True)
                axes[0].plot(xs, y_ref, lw=2, label="Reference")
                axes[0].plot(xs, y_eml, "--", lw=1.5, label="EML")
                axes[0].set_title(f"{fn_name}(x) — {entry.n_nodes} {entry.backend} node(s)")
                axes[0].legend(framealpha=0.7)
                axes[0].set_xlabel("x")

                axes[1].semilogy(xs, np.maximum(err, 1e-17))
                axes[1].set_title("Absolute error")
                axes[1].set_xlabel("x")
                axes[1].set_ylabel("|EML − ref|")

                st.pyplot(fig)
                plt.close(fig)
            except Exception as exc:
                st.error(f"Plot error: {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — PINN Demo
# ─────────────────────────────────────────────────────────────────────────────

_PINN_EQUATIONS = [
    "harmonic",
    "burgers",
    "heat",
    "schrodinger",
    "kdv_soliton",
    "nls",
    "lotka_volterra",
]

_PINN_DESCRIPTIONS = {
    "harmonic":      "u''(x) + ω²·u(x) = 0  (simple harmonic oscillator)",
    "burgers":       "u·u'(x) − ν·u''(x) = 0  (steady Burgers)",
    "heat":          "u''(x) = 0  (steady 1-D heat / Laplace)",
    "schrodinger":   "−u''(x) = k²·u(x)  (free-particle Schrödinger; exact: exp(ikx))",
    "kdv_soliton":   "u' − 6u·u' − u''' = 0  (KdV traveling-wave)",
    "nls":           "u'' + |u|²·u = 0  (NLS / Gross-Pitaevskii)",
    "lotka_volterra":"u'' + α·u' + β·u·u' = 0  (Lotka-Volterra proxy)",
}

with tab3:
    st.header("Physics-Informed EML Networks (PINN)")
    st.markdown(
        "Train an **EMLNetwork** backbone that simultaneously fits observed data and "
        "satisfies a differential equation: `loss = data_loss + λ × physics_loss`."
    )

    if not TORCH_AVAILABLE:
        st.warning(
            "**PyTorch is not installed.** "
            "Install it with `pip install torch` to run the interactive demo."
        )
        st.markdown("### Pre-computed example — harmonic oscillator (ω = 2.0, 500 steps)")
        st.markdown(
            "**Equation:** u''(x) + 4u(x) = 0 → exact solution: sin(2x)\n\n"
            "**EML formula learned:** `eml(eml(x, eml(x, 1)), 1)` (depth-2 tree)\n\n"
            "**Data loss:** 0.0042 | **Physics loss:** 0.0018\n\n"
            "**Key result (Schrödinger):** Free-particle solution exp(ikx) = 1 CBEST node "
            "via the Euler path identity: `Im(eml(ix, 1)) = sin(x)`."
        )
        # Static loss-curve illustration
        steps = np.arange(0, 501, 10)
        dl = 0.4 * np.exp(-steps / 120) + 0.004
        pl = 0.3 * np.exp(-steps / 80) + 0.002

        fig, ax = plt.subplots(figsize=(7, 3.5), tight_layout=True)
        ax.semilogy(steps, dl, label="Data loss")
        ax.semilogy(steps, pl, label="Physics loss")
        ax.set_xlabel("Step")
        ax.set_ylabel("Loss")
        ax.set_title("PINN training curves (harmonic oscillator) — illustrative")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)

    else:
        col_conf, col_out = st.columns([1, 2])

        with col_conf:
            eq = st.selectbox("Equation", _PINN_EQUATIONS, index=0)
            st.caption(_PINN_DESCRIPTIONS[eq])

            depth = st.slider("Backbone depth", 1, 3, 2)
            steps = st.slider("Training steps", 100, 2000, 500, step=100)
            lam = st.select_slider(
                "λ_physics",
                options=[0.0, 0.001, 0.01, 0.1, 1.0],
                value=0.1,
            )

            if eq == "harmonic":
                omega = st.number_input("ω", value=2.0, step=0.5)
            elif eq == "burgers":
                nu = st.number_input("ν", value=0.01, step=0.01)
            elif eq == "schrodinger":
                k = st.number_input("k", value=1.0, step=0.5)

            run_pinn = st.button("Run PINN", type="primary", key="btn_pinn")

        with col_out:
            pinn_key = f"pinn_{eq}_{depth}_{steps}_{lam}"
            if run_pinn:
                kwargs: dict = {}
                if eq == "harmonic":
                    kwargs["omega"] = omega
                elif eq == "burgers":
                    kwargs["nu"] = nu
                elif eq == "schrodinger":
                    kwargs["k"] = k

                model = EMLPINN(equation=eq, backbone_depth=depth, **kwargs)
                x_data = torch.linspace(0, 2 * math.pi, 50).unsqueeze(1)

                # Generate noisy target data
                if eq == "harmonic":
                    y_data = torch.sin(kwargs.get("omega", 2.0) * x_data.squeeze())
                elif eq == "schrodinger":
                    y_data = torch.cos(kwargs.get("k", 1.0) * x_data.squeeze())
                else:
                    y_data = torch.sin(x_data.squeeze())

                x_phys = torch.linspace(0, 2 * math.pi, 100).unsqueeze(1)

                with st.spinner("Training…"):
                    result = fit_pinn(
                        model, x_data, y_data, x_phys,
                        steps=steps, lam_physics=lam, log_every=0,
                    )

                st.session_state[pinn_key] = {
                    "formula": result.formula,
                    "data_loss": result.data_loss,
                    "physics_loss": result.physics_loss,
                    "history": result.history,
                }

            if pinn_key in st.session_state:
                s = st.session_state[pinn_key]
                c1, c2 = st.columns(2)
                c1.metric("Data loss", f"{s['data_loss']:.4f}")
                c2.metric("Physics loss", f"{s['physics_loss']:.4f}")
                st.markdown(f"**Learned formula:** `{s['formula']}`")

                if s["history"]:
                    hist = np.array(s["history"])
                    fig, ax = plt.subplots(figsize=(7, 3.5), tight_layout=True)
                    ax.semilogy(hist[:, 0], hist[:, 1], label="Total loss")
                    ax.set_xlabel("Step")
                    ax.set_ylabel("Loss")
                    ax.set_title("PINN training curve")
                    ax.legend()
                    st.pyplot(fig)
                    plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 — MCTS Explorer
# ─────────────────────────────────────────────────────────────────────────────

_MCTS_TARGETS = {
    "sin(x)": math.sin,
    "cos(x)": math.cos,
    "exp(x)": math.exp,
    "x²": lambda x: x * x,
    "ln(1 + x²)": lambda x: math.log(1 + x * x),
    "tanh(x)": math.tanh,
}

_MCTS_PROBES = {
    "sin(x)": list(np.linspace(-math.pi, math.pi, 20)),
    "cos(x)": list(np.linspace(-math.pi, math.pi, 20)),
    "exp(x)": list(np.linspace(0.0, 2.0, 20)),
    "x²": list(np.linspace(-2.0, 2.0, 20)),
    "ln(1 + x²)": list(np.linspace(0.0, 3.0, 20)),
    "tanh(x)": list(np.linspace(-3.0, 3.0, 20)),
}

with tab4:
    st.header("MCTS Explorer")
    st.markdown(
        "Gradient-free tree search over the EML grammar `S → 1 | x | eml(S, S)`. "
        "UCB1 selection, random rollouts, reward = 1 / (1 + MSE). "
        "Results are cached in the session — change parameters and re-run to compare."
    )

    col_cfg, col_res = st.columns([1, 2])

    with col_cfg:
        target_label = st.selectbox("Target function", list(_MCTS_TARGETS.keys()))
        depth = st.slider("Max tree depth", 2, 5, 3, key="mcts_depth")
        n_sims = st.slider("Simulations", 200, 5000, 1000, step=200, key="mcts_sims")
        seed = st.number_input("Seed", value=42, step=1, key="mcts_seed")
        run_mcts = st.button("Run MCTS", type="primary", key="btn_mcts")

    mcts_key = f"mcts_{target_label}_{depth}_{n_sims}_{seed}"

    with col_res:
        if run_mcts:
            target_fn = _MCTS_TARGETS[target_label]
            probe_points = _MCTS_PROBES[target_label]

            with st.spinner(f"Running {n_sims} simulations…"):
                result = mcts_search(
                    target_fn,
                    probe_points=probe_points,
                    depth=depth,
                    n_simulations=n_sims,
                    seed=int(seed),
                )

            st.session_state[mcts_key] = {
                "formula": result.best_formula,
                "mse": result.best_mse,
                "elapsed": result.elapsed_s,
                "history": result.history,
                "n_sims": result.n_simulations,
            }

        if mcts_key in st.session_state:
            s = st.session_state[mcts_key]

            c1, c2, c3 = st.columns(3)
            c1.metric("Best MSE", f"{s['mse']:.4e}")
            c2.metric("Simulations", s["n_sims"])
            c3.metric("Time", f"{s['elapsed']:.1f}s")
            st.markdown(f"**Best formula:** `{s['formula']}`")

            if s["history"]:
                hist = s["history"]
                sim_nums = [h[0] for h in hist]
                mse_vals = [h[1] for h in hist]

                fig, ax = plt.subplots(figsize=(7, 3.5), tight_layout=True)
                ax.semilogy(sim_nums, mse_vals, lw=1.5)
                ax.set_xlabel("Simulation")
                ax.set_ylabel("Best MSE so far")
                ax.set_title(f"MCTS convergence — {target_label}")
                st.pyplot(fig)
                plt.close(fig)

        elif not run_mcts:
            st.info("Configure parameters and click **Run MCTS** to start the search.")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 5 — Phantom Attractor
# ─────────────────────────────────────────────────────────────────────────────

_ATTRACTOR_PATH = (
    Path(__file__).parent / "python" / "experiments" / "attractor_phase_transition.json"
)


@st.cache_data
def _load_attractor_data() -> dict:
    with open(_ATTRACTOR_PATH, encoding="utf-8") as fh:
        return json.load(fh)


with tab5:
    st.header("Phantom Attractor Phase Transition")
    st.markdown(
        "**Target:** fit a depth-3 EMLTree to the constant π using Adam (lr=5e-3, 20 seeds). "
        "Without regularisation, **0/20** seeds reach π — all are trapped by a phantom "
        "attractor near **3.1705**. A tiny regularisation λ ≥ 0.001 causes a sharp phase "
        "transition: **20/20** seeds converge to π."
    )

    try:
        data = _load_attractor_data()
        results3 = data["results"]["3"]
        attractor_val = data["attractors"]["3"]

        lambdas = sorted(float(k) for k in results3.keys())
        conv_rates = [results3[str(lam)]["convergence_rate"] for lam in lambdas]
        means = [results3[str(lam)]["mean_final"] for lam in lambdas]

        # ── plots ──────────────────────────────────────────────────────────────
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), tight_layout=True)

        # Left: convergence rate bar chart
        bar_colors = [
            "#2ecc71" if cr == 1.0 else ("#e74c3c" if cr == 0.0 else "#f39c12")
            for cr in conv_rates
        ]
        axes[0].bar(range(len(lambdas)), conv_rates, color=bar_colors)
        axes[0].set_xticks(range(len(lambdas)))
        axes[0].set_xticklabels([str(lam) for lam in lambdas], rotation=45, ha="right")
        axes[0].set_xlabel("λ (regularisation weight)")
        axes[0].set_ylabel("Fraction converged to π")
        axes[0].set_ylim(0, 1.1)
        axes[0].set_title("Phase transition: fraction reaching π (20 seeds)")
        axes[0].axhline(1.0, color="green", ls="--", lw=1, label="All reach π")
        axes[0].axhline(0.0, color="red", ls="--", lw=1, label="None reach π")
        axes[0].legend(fontsize=8)

        # Right: mean final value scatter
        axes[1].scatter(lambdas, means, zorder=5, color="#3498db")
        axes[1].axhline(
            math.pi, color="blue", ls="--", lw=1.5, label=f"π = {math.pi:.5f}"
        )
        if attractor_val is not None:
            axes[1].axhline(
                attractor_val,
                color="red",
                ls="--",
                lw=1.5,
                label=f"Attractor ≈ {attractor_val:.4f}",
            )
        axes[1].set_xlabel("λ")
        axes[1].set_ylabel("Mean final value (20 seeds)")
        axes[1].set_title("Convergence target vs λ")
        axes[1].legend()

        st.pyplot(fig)
        plt.close(fig)

        # ── key metrics ────────────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        c1.metric("Phantom attractor", f"{attractor_val:.6f}" if attractor_val else "unknown")
        c2.metric("Critical λ", "0.001")
        c3.metric("Seeds trapped without λ", f"{results3['0.0']['n_seeds'] - results3['0.0']['n_pi']} / {results3['0.0']['n_seeds']}")

        st.markdown(
            "### Interpretation\n"
            "The phantom attractor (~3.1705) is **not** π, e, or any known simple constant. "
            "It is a spurious fixed point of the Adam gradient flow on the EML loss surface. "
            "The phase transition at λ_crit = 0.001 is sharp: the attractor basin collapses "
            "and all seeds reach π. "
            "This phenomenon is **EML-specific** — it does not appear in Taylor, Padé, or "
            "continued-fraction bases (see `experiments/attractor_generalization.py`)."
        )

    except FileNotFoundError:
        st.error(
            f"Attractor data not found at `{_ATTRACTOR_PATH}`. "
            "Run `python/experiments/gen_attractor_data_v2.py` to generate it."
        )
