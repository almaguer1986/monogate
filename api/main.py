"""
api/main.py  —  monogate public API
=====================================
Endpoints:
  GET  /health         — liveness probe
  POST /optimize       — EML code optimizer (best_optimize)
  POST /sr             — Symbolic regression: find best EML formula for X/y data

Rate limits (per IP):
  /optimize — 30/hour
  /sr       — 10/hour  (more compute-intensive)
"""

from __future__ import annotations

import os
from typing import Annotated

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from monogate import best_optimize
from monogate.optimize import OptimizeResult, _CROSSOVER_PCT
from monogate.search.mcts import mcts_search

# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="monogate API", version="0.4.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:3000",
        "https://monogate.dev", "https://www.monogate.dev",
        "https://capcard.ai",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── /optimize ─────────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    source: str


class OpMatchOut(BaseModel):
    name: str
    count: int
    best_nodes: int
    eml_nodes: int
    best_op: str
    note: str
    savings_pct: int


class OptimizeResponse(BaseModel):
    message: str
    savings_pct: int
    total_best_nodes: int
    total_eml_nodes: int
    rewritten_code: str
    python_snippet: str
    ops: list[OpMatchOut]
    speedup_expected: bool
    crossover_pct: int
    error: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.post("/optimize", response_model=OptimizeResponse)
@limiter.limit("30/hour")
def optimize(request: Request, req: OptimizeRequest):
    if not req.source.strip():
        return OptimizeResponse(
            message="Empty input",
            savings_pct=0,
            total_best_nodes=0,
            total_eml_nodes=0,
            rewritten_code="",
            python_snippet="",
            ops=[],
            speedup_expected=False,
            crossover_pct=_CROSSOVER_PCT,
            error="Empty source",
        )

    try:
        r: OptimizeResult = best_optimize(req.source)
    except Exception as exc:
        return OptimizeResponse(
            message=f"Analysis error: {exc}",
            savings_pct=0,
            total_best_nodes=0,
            total_eml_nodes=0,
            rewritten_code=req.source,
            python_snippet="",
            ops=[],
            speedup_expected=False,
            crossover_pct=_CROSSOVER_PCT,
            error=str(exc),
        )

    ops_out = [
        OpMatchOut(
            name=op.name,
            count=op.count,
            best_nodes=op.best_nodes,
            eml_nodes=op.eml_nodes,
            best_op=op.best_op,
            note=op.note,
            savings_pct=op.savings,
        )
        for op in r.ops
    ]

    return OptimizeResponse(
        message=r.message,
        savings_pct=r.savings_pct,
        total_best_nodes=r.total_best_nodes,
        total_eml_nodes=r.total_eml_nodes,
        rewritten_code=r.rewritten_code,
        python_snippet=r.python_snippet,
        ops=ops_out,
        speedup_expected=r.savings_pct >= _CROSSOVER_PCT,
        crossover_pct=_CROSSOVER_PCT,
    )


# ── /sr — Symbolic Regression ─────────────────────────────────────────────────

_SR_MAX_POINTS = 200
_SR_MAX_SIMS = 500


class SRRequest(BaseModel):
    x: Annotated[list[float], Field(min_length=3, max_length=_SR_MAX_POINTS)]
    y: Annotated[list[float], Field(min_length=3, max_length=_SR_MAX_POINTS)]
    n_simulations: Annotated[int, Field(ge=100, le=_SR_MAX_SIMS)] = 300
    depth: Annotated[int, Field(ge=2, le=6)] = 4
    objective: Annotated[str, Field(pattern="^(mse|minimax)$")] = "mse"


class SRResponse(BaseModel):
    formula: str
    mse: float
    objective: str
    n_simulations_used: int
    depth: int
    n_points: int
    note: str
    error: str | None = None


@app.post("/sr", response_model=SRResponse)
@limiter.limit("10/hour")
def symbolic_regression(request: Request, req: SRRequest):
    """Find the best EML expression tree for the given (x, y) dataset."""
    if len(req.x) != len(req.y):
        return SRResponse(
            formula="",
            mse=float("inf"),
            objective=req.objective,
            n_simulations_used=0,
            depth=req.depth,
            n_points=0,
            note="",
            error="x and y must have the same length",
        )

    x_arr = np.array(req.x, dtype=float)
    y_arr = np.array(req.y, dtype=float)

    # Interpolation target function — allows MCTS to evaluate at any probe point
    def target_fn(x: float) -> float:
        return float(np.interp(x, x_arr, y_arr))

    try:
        result = mcts_search(
            target_fn=target_fn,
            probe_points=list(x_arr),
            depth=req.depth,
            n_simulations=req.n_simulations,
            objective=req.objective,
            seed=42,
        )
    except Exception as exc:
        return SRResponse(
            formula="",
            mse=float("inf"),
            objective=req.objective,
            n_simulations_used=req.n_simulations,
            depth=req.depth,
            n_points=len(req.x),
            note="",
            error=str(exc),
        )

    note = (
        f"Best EML formula found after {req.n_simulations} simulations. "
        "This is the free tier — upgrade at capcard.ai/pricing.html for longer searches."
    )

    return SRResponse(
        formula=result.best_formula,
        mse=float(result.best_mse),
        objective=req.objective,
        n_simulations_used=req.n_simulations,
        depth=req.depth,
        n_points=len(req.x),
        note=note,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8787))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
