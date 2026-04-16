# Installation

## Python package

### Core (no dependencies)

```bash
pip install monogate
```

The core package is pure Python 3.10+ with zero runtime dependencies. It includes:

- `monogate.core` — EML operator, constants, elementary function identities
- `monogate.optimize` — BEST optimizer, sin/cos/GELU node-count analysis
- `monogate.operators` — operator family comparison table
- `monogate.search` — MCTS and Beam Search over the EML grammar
- `monogate.complex_eval` — complex-domain EML, Euler path constructions

### With PyTorch

```bash
pip install "monogate[torch]"
```

Adds:

- `monogate.network` — `EMLNetwork`, `HybridNetwork`, `EMLTree`, `fit()`
- `monogate.torch` — `EMLLayer`, `EMLActivation` (differentiable nn.Module layers)

Requires: `torch >= 2.0`

### Development

```bash
pip install "monogate[dev]"
```

Includes pytest and torch. Then run tests:

```bash
cd python/
pytest
```

---

## JavaScript / Node.js

```bash
npm install monogate
```

```js
import { op, sinBEST, cosBEST } from "monogate";

console.log(op(1, 1));          // e
console.log(sinBEST(Math.PI));  // ≈ 0
```

---

## From source

```bash
git clone https://github.com/almaguer1986/monogate
cd monogate/python
pip install -e ".[dev]"
pytest
```

---

## Verify installation

```python
import monogate
print(monogate.__version__)   # 0.5.0

# Smoke test: eml(1, 1) = e
from monogate import op
import math
assert abs(op(1, 1) - math.e) < 1e-14
print("OK")
```
