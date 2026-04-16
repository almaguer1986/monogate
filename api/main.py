"""
api/main.py  —  monogate BEST optimizer API
============================================
Thin FastAPI wrapper around monogate.best_optimize().

Runs at http://localhost:8787 by default.  The explorer's OptimizeTab
tries this endpoint first; falls back to its built-in JS analysis when
the server is not reachable.

Start:
    cd api/
    uvicorn main:app --port 8787 --reload

Or from the repo root:
    python api/main.py
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from monogate import best_optimize
from monogate.optimize import OptimizeResult, _CROSSOVER_PCT

app = FastAPI(title="monogate BEST optimizer", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:3000",
        "https://monogate.dev", "https://www.monogate.dev",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    source: str   # Python / NumPy / PyTorch code or bare math expression


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
    return {"status": "ok", "version": "0.3.1"}


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    """
    Analyze source code or a math expression string.

    Returns per-operation node savings, rewritten source, and a
    speedup indicator based on the measured 20% crossover threshold.
    """
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


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8787))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
