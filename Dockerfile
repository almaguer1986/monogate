# monogate — Reproducibility Docker Image
#
# Builds a clean, self-contained environment for running all monogate
# experiments, tests, and paper figure generation.
#
# Usage:
#   docker build -t monogate .
#   docker run --rm -v $(pwd):/workspace monogate make reproduce-all
#   docker run --rm monogate make reproduce-n11
#
# To generate the paper figures and compile the preprint:
#   docker run --rm -v $(pwd)/python/paper:/out monogate make paper
#
# GPU support (requires nvidia-docker):
#   docker run --rm --gpus all monogate make reproduce-all
#
# Build arguments:
#   --build-arg PYTHON_VERSION=3.12   (default)
#   --build-arg TORCH_VERSION=2.3.0   (default)

ARG PYTHON_VERSION=3.12
ARG TORCH_VERSION=2.3.0

FROM python:${PYTHON_VERSION}-slim

# Metadata
LABEL org.opencontainers.image.title="monogate"
LABEL org.opencontainers.image.description="EML operator reproducibility environment"
LABEL org.opencontainers.image.source="https://github.com/almaguer1986/monogate"
LABEL org.opencontainers.image.version="0.10.0"

# ── System dependencies ────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      git \
      pkg-config \
      libssl-dev \
      ca-certificates \
      texlive-latex-base \
      texlive-latex-extra \
      texlive-fonts-recommended \
      texlive-science \
      make \
    && rm -rf /var/lib/apt/lists/*

# ── Rust toolchain (for monogate-core PyO3 extension) ─────────────────────────
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# ── Python dependencies ────────────────────────────────────────────────────────
WORKDIR /workspace

# Copy only dependency files first (better layer caching)
COPY python/requirements-reproduce.txt /tmp/requirements-reproduce.txt

ARG TORCH_VERSION
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      torch==${TORCH_VERSION} \
      --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /tmp/requirements-reproduce.txt

# ── Install monogate ───────────────────────────────────────────────────────────
COPY python/ /workspace/python/
RUN cd /workspace/python && pip install --no-cache-dir -e ".[torch,dev]"

# ── Copy full repo ─────────────────────────────────────────────────────────────
COPY . /workspace/

# ── Default working directory ──────────────────────────────────────────────────
WORKDIR /workspace/python

# ── Smoke test that the install works ─────────────────────────────────────────
RUN python -c "from monogate import BEST, CBEST, EMLPINN; print('monogate install OK')"

CMD ["make", "reproduce-all"]
