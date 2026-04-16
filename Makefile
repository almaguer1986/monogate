# monogate — Root Makefile
#
# All targets run from the repository root.
# Most Python work delegates to python/ subdirectory.
#
# Quickstart:
#   make test           — run full test suite
#   make reproduce-n11  — verify N=11 exhaustive search results
#   make reproduce-all  — run all reproducibility checks
#   make paper          — compile preprint.tex to PDF
#   make theory         — render THEORY.md to PDF (requires pandoc)
#
# Docker:
#   make docker-build   — build the reproducibility image
#   make docker-run     — run reproduce-all inside the container

PYTHON  := python
PY      := cd python && $(PYTHON)
PYTEST  := cd python && $(PYTHON) -m pytest
PAPER   := cd python/paper && pdflatex

.PHONY: help test test-new reproduce-n11 reproduce-all \
        paper theory docker-build docker-run \
        clean lint version-check

# ── Help ───────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "monogate Makefile"
	@echo "─────────────────────────────────────────────────────"
	@echo "  make test            Run full test suite (662 tests)"
	@echo "  make test-new        Run only v0.10.0 new tests"
	@echo "  make reproduce-n11   Verify N=11 exhaustive search"
	@echo "  make reproduce-all   All reproducibility checks"
	@echo "  make paper           Compile preprint.tex → PDF"
	@echo "  make theory          Render THEORY.md → PDF (needs pandoc)"
	@echo "  make docker-build    Build reproducibility container"
	@echo "  make docker-run      Run reproduce-all in container"
	@echo "  make clean           Remove build artifacts"
	@echo "  make lint            Run ruff linter"
	@echo "  make version-check   Print installed package versions"
	@echo ""

# ── Tests ──────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/ -q --tb=short

test-new:
	$(PYTEST) tests/test_complex_best.py tests/test_pinn.py -v --tb=short

test-search:
	$(PYTEST) tests/test_mcts.py tests/test_beam.py -v --tb=short 2>/dev/null || \
	$(PYTEST) tests/ -k "mcts or beam or search" -v --tb=short

# ── Reproducibility ────────────────────────────────────────────────────────────

reproduce-n11:
	@echo "── Reproducing N=11 exhaustive search ──"
	$(PY) scripts/reproduce_n11.py
	@echo "── Done ──"

reproduce-all:
	@echo "── monogate v0.10.0 full reproducibility check ──"
	$(PY) scripts/prepare_v0.10.py
	@echo ""
	@echo "── N=11 search verification ──"
	$(PY) scripts/reproduce_n11.py
	@echo ""
	@echo "── Full test suite ──"
	$(PYTEST) tests/ -q --tb=short
	@echo ""
	@echo "── All checks complete ──"

# ── Paper ──────────────────────────────────────────────────────────────────────

paper:
	@echo "── Generating attractor landscape figure ──"
	$(PY) experiments/plot_attractor_landscape.py || \
	    echo "  (figure generation skipped — matplotlib/numpy may not be installed)"
	@echo "── Compiling preprint.tex (pass 1) ──"
	$(PAPER) preprint.tex </dev/null >/dev/null 2>&1 || \
	    (echo "  pdflatex not found — install TeX Live or run via Docker"; exit 0)
	@echo "── Compiling preprint.tex (pass 2 — cross-refs) ──"
	$(PAPER) preprint.tex </dev/null >/dev/null 2>&1 || true
	@echo "── Output: python/paper/preprint.pdf ──"

# ── Theory document ────────────────────────────────────────────────────────────

theory:
	@which pandoc >/dev/null 2>&1 || (echo "pandoc not installed — brew/apt install pandoc"; exit 1)
	pandoc THEORY.md \
	    --pdf-engine=pdflatex \
	    -V geometry:margin=1in \
	    -V fontsize=11pt \
	    -V mainfont="Latin Modern Roman" \
	    --toc \
	    -o THEORY.pdf
	@echo "── Output: THEORY.pdf ──"

# ── Docker ─────────────────────────────────────────────────────────────────────

docker-build:
	docker build -t monogate:0.10.0 -t monogate:latest .

docker-run:
	docker run --rm -v "$(shell pwd)":/workspace monogate:latest make reproduce-all

docker-shell:
	docker run --rm -it -v "$(shell pwd)":/workspace monogate:latest bash

# ── Utilities ──────────────────────────────────────────────────────────────────

clean:
	find python -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find python -name "*.pyc" -delete 2>/dev/null || true
	find python -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -f python/paper/preprint.{aux,log,out,toc}
	rm -f THEORY.pdf
	@echo "── Cleaned ──"

lint:
	cd python && $(PYTHON) -m ruff check monogate/ --select E,W,F || true

version-check:
	@echo "── Installed versions ──"
	$(PY) -c "import monogate; print('monogate:', monogate.__version__)"
	$(PY) -c "import torch; print('torch:', torch.__version__)" 2>/dev/null || echo "torch: not installed"
	$(PY) -c "import numpy; print('numpy:', numpy.__version__)"
	$(PY) -c "import scipy; print('scipy:', scipy.__version__)" 2>/dev/null || echo "scipy: not installed"
	$(PYTHON) --version
