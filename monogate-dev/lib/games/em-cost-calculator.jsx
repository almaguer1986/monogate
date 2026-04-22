// EM Cost Calculator — 6 canonical electromagnetism formulas with
// F16-node cost breakdowns. Click an expression to see its per-operator
// decomposition, a "route" annotation (why each choice is cheap), and the
// total. A small catalog of other cross-domain formulas is included with
// search/filter; the full 315+ equation catalog lives in the blog posts.

import { useState, useMemo } from "react";

// ── Data: 6 EM formulas from sE_em_costs.json ───────────────────────────────

const EM_FORMULAS = [
  {
    id: "photon-energy",
    name: "photon energy",
    latex: "E = h\\,\\nu = h c / \\lambda",
    total: 3,
    elc: "inside",
    breakdown: [
      ["mul (hc)",   1],
      ["div (/λ)",   2],
    ],
    note: "Trivial arithmetic. Alternate form hν = 1 mul.",
  },
  {
    id: "skin-depth",
    name: "skin depth",
    latex: "\\delta = \\sqrt{2 / (\\omega \\mu \\sigma)}",
    total: 5,
    elc: "inside",
    breakdown: [
      ["mul (ωμ)",       1],
      ["mul (×σ)",       1],
      ["div (2/⋅)",      2],
      ["sqrt = EPL(0.5)", 1],
    ],
    note: "Pure positive-domain arithmetic. sqrt is 1n via EPL(0.5, x).",
  },
  {
    id: "damped-wave",
    name: "damped EM wave",
    latex: "E(x,t) = E_0\\,e^{-\\alpha x}\\cos(kx - \\omega t)",
    total: 9,
    elc: "boundary",
    breakdown: [
      ["mul (αx)",                  1],
      ["DEML (exp(−αx))",           1],
      ["mul (kx)",                  1],
      ["mul (ωt)",                  1],
      ["sub (kx − ωt)",             2],
      ["cos (complex bypass)",      1],
      ["mul (E₀·damp)",             1],
      ["mul (×cos)",                1],
    ],
    note: "Mix of ELC-interior damping (1n via DEML) and boundary (cos = 1 complex node).",
  },
  {
    id: "energy-density",
    name: "EM energy density",
    latex: "u = \\tfrac{1}{2}\\varepsilon_0 E^2 + \\tfrac{1}{2\\mu_0} B^2",
    total: 10,
    elc: "inside",
    breakdown: [
      ["pow (E²)",          1],
      ["mul (ε₀·E²)",      1],
      ["div (/2)",          2],
      ["pow (B²)",          1],
      ["mul (2μ₀)",         1],
      ["div (B²/(2μ₀))",    2],
      ["add",               2],
    ],
    note: "All positive-domain arithmetic; entirely inside ELC.",
  },
  {
    id: "poynting-A",
    name: "Poynting (cos·cos form)",
    latex: "S = E_0 B_0 \\cos^2(kx - \\omega t) / \\mu_0",
    total: 10,
    elc: "boundary",
    breakdown: [
      ["mul (kx)",                 1],
      ["mul (ωt)",                 1],
      ["sub (kx − ωt)",            2],
      ["cos (complex bypass)",     1],
      ["mul (cos²)",               1],
      ["mul (E₀B₀)",               1],
      ["mul (×cos²)",              1],
      ["div (/μ₀)",                2],
    ],
    note: "Squaring the single cos bypass.",
  },
  {
    id: "poynting-B",
    name: "Poynting via cos²=(1+cos 2θ)/2",
    latex: "S = \\tfrac{E_0 B_0}{\\mu_0} \\cdot \\tfrac{1 + \\cos 2\\theta}{2}",
    total: 14,
    elc: "boundary",
    breakdown: [
      ["mul (kx)",                 1],
      ["mul (ωt)",                 1],
      ["sub (kx − ωt)",            2],
      ["mul (×2)",                 1],
      ["cos (2θ, complex bypass)", 1],
      ["add (1 + cos)",            2],
      ["div (/2)",                 2],
      ["mul (E₀B₀/μ₀)",            1],
      ["div (×)",                  2],
      ["mul (×bracket)",           1],
    ],
    note: "Double-angle identity INFLATES cost: 14n vs 10n for the direct form.",
  },
  {
    id: "planck",
    name: "Planck radiation",
    latex: "B(\\nu, T) = \\tfrac{2h\\nu^3}{c^2} \\cdot \\tfrac{1}{e^{h\\nu/kT} - 1}",
    total: 14,
    elc: "inside",
    breakdown: [
      ["pow (ν³)",         1],
      ["mul (2h·ν³)",      1],
      ["pow (c²)",         1],
      ["div (/c²)",        2],
      ["mul (hν)",         1],
      ["mul (kT)",         1],
      ["div (hν/kT)",      2],
      ["exp",              1],
      ["sub (−1)",         2],
      ["recip",            1],
      ["mul (pre·recip)",  1],
    ],
    note: "NO trig. Entirely inside ELC — thermal radiation is F16-native.",
  },
];

// ── Cross-domain catalog (representative sample from the 315+ blog catalog) ─

const CATALOG = [
  // Physics
  { domain: "physics",    name: "E = mc²",                          cost: 1,   elc: "inside",   formula: "mul" },
  { domain: "physics",    name: "Lorentz γ = 1/√(1−v²/c²)",         cost: 7,   elc: "inside",   formula: "sub, div, sqrt" },
  { domain: "physics",    name: "Planck radiation B(ν,T)",          cost: 14,  elc: "inside",   formula: "see above" },
  { domain: "physics",    name: "Schrödinger U(t) = exp(−iHt/ℏ)",   cost: 1,   elc: "inside",   formula: "1 matrix EML node" },
  { domain: "physics",    name: "Einstein G_μν = κT_μν",            cost: 1,   elc: "inside",   formula: "mul" },

  // Math / Analysis
  { domain: "analysis",   name: "Gaussian e^(−x²/2)",                cost: 2,   elc: "inside",   formula: "pow + DEML" },
  { domain: "analysis",   name: "softplus ln(1+eˣ)",                 cost: 1,   elc: "inside",   formula: "LEAd(x,1) = T19" },
  { domain: "analysis",   name: "sigmoid 1/(1+e^{−x})",              cost: 4,   elc: "inside",   formula: "exp + add + recip" },
  { domain: "analysis",   name: "tanh(x)",                          cost: 4,   elc: "inside",   formula: "sinh/cosh" },
  { domain: "analysis",   name: "sin(x) via Euler",                  cost: 1,   elc: "boundary", formula: "1 complex EML node" },
  { domain: "analysis",   name: "Fourier kernel e^(iωt)",            cost: 1,   elc: "inside",   formula: "complex EML" },
  { domain: "analysis",   name: "Laplace kernel e^(−st)",            cost: 1,   elc: "inside",   formula: "DEML" },

  // Stats / ML
  { domain: "ml",         name: "softmax numerator e^(zᵢ)",          cost: 1,   elc: "inside",   formula: "per term: exp" },
  { domain: "ml",         name: "ReLU(x) = max(0, x)",               cost: "∞", elc: "outside",  formula: "NOT in ELC" },
  { domain: "ml",         name: "binary entropy H(p)",               cost: 14,  elc: "inside",   formula: "2 terms × (ln + mul)" },
  { domain: "ml",         name: "KL per-term λ·ln(λ/μ)",              cost: 5,   elc: "inside",   formula: "D_F13 route (avoid free mul)" },
  { domain: "ml",         name: "swish/SiLU x·σ(x)",                 cost: 7,   elc: "inside",   formula: "σ=4n + free-var mul=3n" },
  { domain: "ml",         name: "MSE (y−ŷ)²",                        cost: 3,   elc: "inside",   formula: "sub + pow" },

  // Finance
  { domain: "finance",    name: "continuous comp. A·e^(rt)",         cost: 2,   elc: "inside",   formula: "mul + exp" },
  { domain: "finance",    name: "Black-Scholes d₁",                  cost: 12,  elc: "inside",   formula: "ln + div + mul + sqrt" },
  { domain: "finance",    name: "log return ln(pᵗ/pᵗ⁻¹)",             cost: 3,   elc: "inside",   formula: "div + ln" },

  // Chem / Bio
  { domain: "chembio",    name: "Arrhenius k = A·e^(−Ea/RT)",         cost: 4,   elc: "inside",   formula: "mul + div + DEML" },
  { domain: "chembio",    name: "Michaelis-Menten v = Vmax·S/(Km+S)", cost: 4,   elc: "inside",   formula: "mul + add + div" },
  { domain: "chembio",    name: "Hill equation θ = xⁿ/(Kⁿ+xⁿ)",       cost: 5,   elc: "inside",   formula: "pow + add + div" },
  { domain: "chembio",    name: "Nernst E = E₀ − (RT/zF)·ln(Q)",      cost: 6,   elc: "inside",   formula: "ln + mul + sub" },

  // Geometry
  { domain: "geometry",   name: "Euclidean dist √(dx² + dy²)",        cost: 3,   elc: "inside",   formula: "pow + add + sqrt" },
  { domain: "geometry",   name: "Haversine",                         cost: 28,  elc: "boundary", formula: "sin/cos + ln — most-evaluated outdoor" },
  { domain: "geometry",   name: "hyperbolic dist arccosh(a·b+1)",     cost: 5,   elc: "inside",   formula: "mul + add + ln" },
  { domain: "geometry",   name: "Bures √(λμ)",                       cost: 2,   elc: "inside",   formula: "positive mul=1n + EPL=1n" },

  // Info / Signals
  { domain: "signals",    name: "heat kernel (t fixed, x var)",      cost: 4,   elc: "inside",   formula: "pow + mul + DEML" },
  { domain: "signals",    name: "GPS ETA",                           cost: 2,   elc: "inside",   formula: "cheapest outdoor formula" },
  { domain: "signals",    name: "Reed-Solomon syndrome",             cost: 2037, elc: "inside",  formula: "most expensive (EDB test)" },
  { domain: "signals",    name: "PageRank iterate",                  cost: 5,   elc: "inside",   formula: "per iterate, sparse" },
];

const DOMAIN_COLORS = {
  physics:   "#4facfe",
  analysis:  "#a18cd1",
  ml:        "#0fd38d",
  finance:   "#fccb52",
  chembio:   "#f5576c",
  geometry:  "#7af0c8",
  signals:   "#e8a020",
};

const ELC_COLORS = {
  inside:   "#5ec47a",
  boundary: "#fccb52",
  outside:  "#f87171",
};

export default function EmCostCalculator() {
  const [selectedId, setSelectedId] = useState(EM_FORMULAS[0].id);
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState("all");

  const selected = EM_FORMULAS.find((f) => f.id === selectedId);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return CATALOG.filter((e) => {
      if (domainFilter !== "all" && e.domain !== domainFilter) return false;
      if (!q) return true;
      return e.name.toLowerCase().includes(q)
          || e.formula.toLowerCase().includes(q)
          || e.domain.toLowerCase().includes(q);
    });
  }, [search, domainFilter]);

  const domains = Array.from(new Set(CATALOG.map((e) => e.domain)));

  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>EM cost calculator</span>
        <span style={S.formula}>F16-node decomposition for 6 EM formulas + cross-domain catalog</span>
      </header>

      <h2 style={S.h2}>Electromagnetic formulas</h2>

      <div style={S.formulaList}>
        {EM_FORMULAS.map((f) => (
          <button
            key={f.id}
            onClick={() => setSelectedId(f.id)}
            style={{
              ...S.formulaBtn,
              background: selectedId === f.id ? "rgba(79,172,254,0.12)" : "transparent",
              borderColor: selectedId === f.id ? "#4facfe" : "rgba(255,255,255,0.1)",
              color: selectedId === f.id ? "#e8e8f0" : "rgba(255,255,255,0.65)",
            }}
          >
            <span style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <span style={{
                ...S.elcDot, background: ELC_COLORS[f.elc],
              }} />
              <span>{f.name}</span>
            </span>
            <span style={{ fontWeight: 600, color: "#e8e8f0", fontSize: 13 }}>{f.total}n</span>
          </button>
        ))}
      </div>

      <div style={S.detail}>
        <div style={S.detailHead}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{selected.name}</div>
            <div style={{
              fontFamily: "'Times New Roman', serif", fontSize: 15,
              color: "rgba(255,255,255,0.75)", marginTop: 6,
            }}>
              {/* Render LaTeX-ish inline; we don't ship a math renderer here */}
              {prettyLatex(selected.latex)}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={S.bigCost}>{selected.total}<span style={{ fontSize: 14, fontWeight: 400, color: "rgba(255,255,255,0.5)" }}> nodes</span></div>
            <div style={{
              fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em",
              color: ELC_COLORS[selected.elc], marginTop: 2,
            }}>
              {selected.elc === "inside" ? "inside ELC" : selected.elc === "boundary" ? "ELC boundary (needs complex)" : "outside ELC"}
            </div>
          </div>
        </div>

        <div style={S.breakdownWrap}>
          {selected.breakdown.map(([op, count], i) => (
            <div key={i} style={S.breakdownRow}>
              <span style={{ color: "rgba(255,255,255,0.7)" }}>{op}</span>
              <span style={{
                fontWeight: 600, color: "#e8e8f0",
                minWidth: 40, textAlign: "right",
              }}>{count}n</span>
            </div>
          ))}
          <div style={{ ...S.breakdownRow, ...S.breakdownTotal }}>
            <span>total</span>
            <span>{selected.total}n</span>
          </div>
        </div>

        <div style={S.note}>{selected.note}</div>
      </div>

      <div style={S.inside}>
        <span style={{ color: "rgba(255,255,255,0.55)" }}>
          Inside ELC subtotal (photon + skin + energy density + Planck):
        </span>
        <span style={{ color: "#5ec47a", fontWeight: 600 }}>
          {EM_FORMULAS.filter((f) => f.elc === "inside").reduce((a, f) => a + f.total, 0)}n
        </span>
        <span style={{ color: "rgba(255,255,255,0.55)" }}>
          Boundary subtotal (damped wave + Poynting×2):
        </span>
        <span style={{ color: "#fccb52", fontWeight: 600 }}>
          {EM_FORMULAS.filter((f) => f.elc === "boundary").reduce((a, f) => a + f.total, 0)}n
        </span>
      </div>

      <h2 style={{ ...S.h2, marginTop: 38 }}>Cross-domain catalog</h2>
      <p style={S.para}>
        A representative {CATALOG.length}-equation sample across 7 domains.
        The full 315+ catalog lives in the blog posts&nbsp;
        <a href="/blog/cost-of-everything" style={{ color: "#4facfe" }}>cost-of-everything</a>,&nbsp;
        <a href="/blog/157-equations"     style={{ color: "#4facfe" }}>157-equations</a>,&nbsp;
        <a href="/blog/chembio-costs"     style={{ color: "#4facfe" }}>chembio-costs</a>,&nbsp;
        <a href="/blog/quantum-costs"     style={{ color: "#4facfe" }}>quantum-costs</a>,&nbsp;
        <a href="/blog/geometry-costs"    style={{ color: "#4facfe" }}>geometry-costs</a>,&nbsp;
        <a href="/blog/calculus-costs"    style={{ color: "#4facfe" }}>calculus-costs</a>.
      </p>

      <div style={S.controls}>
        <input
          type="text"
          placeholder="search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={S.searchBox}
        />
        <span style={S.label}>domain</span>
        <button
          onClick={() => setDomainFilter("all")}
          style={{
            ...S.btn,
            background: domainFilter === "all" ? "rgba(255,255,255,0.12)" : "transparent",
          }}
        >all · {CATALOG.length}</button>
        {domains.map((d) => {
          const n = CATALOG.filter((e) => e.domain === d).length;
          return (
            <button
              key={d}
              onClick={() => setDomainFilter(d)}
              style={{
                ...S.btn,
                background: domainFilter === d ? "rgba(255,255,255,0.12)" : "transparent",
                borderColor: domainFilter === d ? DOMAIN_COLORS[d] + "aa" : "rgba(255,255,255,0.1)",
                color: domainFilter === d ? "#e8e8f0" : "rgba(255,255,255,0.5)",
              }}
            >{d} · {n}</button>
          );
        })}
      </div>

      <div style={S.catalogList}>
        {filtered.length === 0 ? (
          <div style={{ padding: 20, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>
            No matches.
          </div>
        ) : filtered.map((e, i) => (
          <div key={i} style={S.catalogRow}>
            <span style={{ ...S.domainDot, background: DOMAIN_COLORS[e.domain] }} />
            <span style={{
              color: "rgba(255,255,255,0.4)", fontSize: 9,
              minWidth: 62, textTransform: "uppercase", letterSpacing: "0.05em",
            }}>{e.domain}</span>
            <span style={{ flex: 1, color: "#e8e8f0" }}>{e.name}</span>
            <span style={{
              fontSize: 9, textTransform: "uppercase", letterSpacing: "0.04em",
              color: ELC_COLORS[e.elc],
              background: ELC_COLORS[e.elc] + "22",
              padding: "1px 6px", borderRadius: 2,
              border: `1px solid ${ELC_COLORS[e.elc]}55`,
            }}>{e.elc}</span>
            <span style={{ fontWeight: 600, minWidth: 56, textAlign: "right" }}>
              {typeof e.cost === "number" ? `${e.cost}n` : e.cost}
            </span>
            <span style={{
              color: "rgba(255,255,255,0.4)", fontSize: 10, minWidth: 180,
              fontFamily: "'IBM Plex Mono', monospace",
            }}>{e.formula}</span>
          </div>
        ))}
      </div>

      <div style={S.help}>
        Every formula here is measured in F16 node counts using the v5.2
        positive-domain costs: mul = 1n, exp = 1n, ln = 1n, div = 2n,
        sqrt = 1n via EPL(0.5, x), sub = 2n. For cross-domain equations,
        see the blog posts linked above — they break down every route
        (where a DEML avoids a sub, where D_F13 avoids a free-variable
        mul, etc.). ReLU is outside ELC because the Infinite Zeros Barrier
        prohibits it; for a formal account, see&nbsp;
        <a href="/blog/relu-softplus-exact-error" style={{ color: "#4facfe" }}>
          relu-softplus-exact-error</a>.
      </div>
    </div>
  );
}

// Prettify a tiny subset of LaTeX for display without a renderer.
function prettyLatex(s) {
  return s
    .replace(/\\,/g, " ")
    .replace(/\\nu/g, "ν")
    .replace(/\\mu/g, "μ")
    .replace(/\\sigma/g, "σ")
    .replace(/\\omega/g, "ω")
    .replace(/\\alpha/g, "α")
    .replace(/\\lambda/g, "λ")
    .replace(/\\varepsilon/g, "ε")
    .replace(/\\delta/g, "δ")
    .replace(/\\cdot/g, "·")
    .replace(/\\sqrt\{([^}]+)\}/g, "√($1)")
    .replace(/\\tfrac\{([^}]+)\}\{([^}]+)\}/g, "$1/$2")
    .replace(/\\cos/g, "cos")
    .replace(/e\^\{-([^}]+)\}/g, "e^(−$1)")
    .replace(/e\^\{([^}]+)\}/g, "e^($1)")
    .replace(/\^2/g, "²")
    .replace(/\^3/g, "³")
    .replace(/_0/g, "₀")
    .replace(/_\\mu/g, "_μ")
    .replace(/\\/g, "");
}

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";
const S = {
  root: {
    background: "#08080c", color: "#e8e8f0", fontFamily: FONT,
    minHeight: "100vh", padding: "20px 24px 80px",
  },
  header: {
    display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap",
    marginBottom: 18, paddingBottom: 10,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: 13, fontWeight: 600, letterSpacing: "0.15em",
    textTransform: "uppercase", color: "#4facfe",
  },
  subBrand: { fontSize: 13, color: "rgba(255,255,255,0.3)" },
  formula: { fontSize: 11, color: "rgba(255,255,255,0.45)", marginLeft: "auto" },

  h2: { fontSize: 14, fontWeight: 600, margin: "8px 0 14px", color: "#e8e8f0" },
  para: { fontSize: 12, lineHeight: 1.65, color: "rgba(255,255,255,0.55)",
    fontFamily: "system-ui, sans-serif", marginBottom: 12 },

  formulaList: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: 6, marginBottom: 20,
  },
  formulaBtn: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: 10, padding: "10px 12px", borderRadius: 5,
    border: "1px solid", cursor: "pointer",
    fontFamily: "inherit", fontSize: 12, textAlign: "left",
    transition: "all 0.15s",
  },
  elcDot: {
    display: "inline-block", width: 8, height: 8, borderRadius: "50%",
  },

  detail: {
    background: "rgba(79,172,254,0.04)",
    border: "1px solid rgba(79,172,254,0.2)",
    borderRadius: 6, padding: 18, marginBottom: 16,
  },
  detailHead: {
    display: "flex", gap: 20, alignItems: "flex-start",
    flexWrap: "wrap", marginBottom: 16,
    paddingBottom: 14, borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  bigCost: { fontSize: 36, fontWeight: 700, color: "#4facfe", lineHeight: 1 },
  breakdownWrap: {
    display: "grid", gridTemplateColumns: "1fr", gap: 2,
    fontSize: 11, marginBottom: 12,
  },
  breakdownRow: {
    display: "flex", justifyContent: "space-between",
    padding: "6px 10px", borderRadius: 3,
    background: "rgba(255,255,255,0.02)",
  },
  breakdownTotal: {
    background: "rgba(79,172,254,0.12)",
    color: "#e8e8f0", fontWeight: 600, fontSize: 12,
    marginTop: 4,
  },
  note: {
    fontSize: 11, color: "rgba(255,255,255,0.55)",
    fontStyle: "italic", lineHeight: 1.6,
  },

  inside: {
    display: "flex", gap: 10, flexWrap: "wrap", alignItems: "baseline",
    fontSize: 12, padding: "10px 16px", borderRadius: 5,
    background: "rgba(255,255,255,0.02)",
    border: "1px solid rgba(255,255,255,0.05)",
    marginBottom: 12,
  },

  controls: {
    display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap",
    marginBottom: 12,
  },
  searchBox: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.12)",
    color: "#e8e8f0", borderRadius: 4, padding: "5px 10px", fontSize: 12,
    fontFamily: "inherit", width: 200,
  },
  label: { fontSize: 10, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em", marginLeft: 8 },
  btn: {
    borderRadius: 4, padding: "4px 10px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", border: "1px solid rgba(255,255,255,0.1)",
    background: "transparent", color: "rgba(255,255,255,0.5)",
  },

  catalogList: {
    display: "flex", flexDirection: "column",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 5, overflow: "hidden",
  },
  catalogRow: {
    display: "flex", gap: 12, alignItems: "center",
    padding: "8px 12px", fontSize: 12,
    borderBottom: "1px solid rgba(255,255,255,0.04)",
    background: "rgba(255,255,255,0.01)",
  },
  domainDot: {
    display: "inline-block", width: 8, height: 8, borderRadius: "50%",
    flexShrink: 0,
  },

  help: {
    maxWidth: 820, marginTop: 20, lineHeight: 1.75, fontSize: 12,
    color: "rgba(255,255,255,0.55)", fontFamily: "system-ui, sans-serif",
  },
};
