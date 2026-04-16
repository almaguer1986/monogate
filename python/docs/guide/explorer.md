# Explorer Guide

The **[monogate.dev](https://monogate.dev)** interactive explorer lets you optimize any expression directly in the browser — no install required.

## Tabs

### Optimize

Paste any Python/JS expression into the input box and click **Optimize**. The explorer calls the FastAPI backend (or falls back to the offline JS engine) and shows:

- **EML nodes**: node count in the standard EML representation
- **BEST nodes**: node count after BEST routing (dispatches each primitive to the cheapest operator family)
- **Savings %**: relative node reduction
- **Rewritten code**: drop-in replacement using `BEST.*` primitives

Example — optimize `sin(x)**2 + exp(-x)`:

```
EML nodes   : 509
BEST nodes  : 145
Savings     : 71.5%
```

### Attractor Lab

Visualizes the **phantom attractor** phenomenon:

- 40 seeds of depth=3 EMLTree training toward π
- At λ=0: all seeds converge to **3.1696** (the attractor), never reaching π
- At λ=0.005: seeds escape the basin and converge to π

Controls:

- **λ toggle**: switch between λ=0 (attractor regime) and λ=0.005 (escape regime)
- **Play / Pause**: animate the loss curves
- **Speed slider**: 1×–10× playback speed

### SIREN

Shows node-count comparison between sin activation and EMLLayer for SIREN-style networks. A depth=2 EMLLayer uses **3 nodes** vs **245** for sin (8-term Taylor) — a **98.8% reduction**.

### Calculator

Interactive EML arithmetic — enter any EML expression and evaluate it step by step.

### BEST

Explore the operator family routing table: for each elementary function, see which family (EML/EDL/EXL) is chosen and how many nodes it saves.

---

## Offline mode

The explorer works fully offline for common patterns. The JS optimizer (`opt-engine.js`) handles:

- `sin`, `cos`, `exp`, `log`, `pow`, `mul`, `div`
- PyTorch style: `torch.sin(x)`, `F.gelu(x)`, `torch.sigmoid(x)`
- NumPy style: `np.sin(x)`, `np.exp(x)`

When the FastAPI backend is unreachable, the optimizer tab automatically falls back to the client-side engine.

---

## Self-hosting

```bash
cd explorer/
npm install
npm run dev     # localhost:5173
```

For the backend optimizer:

```bash
cd python/
uvicorn monogate.api:app --reload
```
