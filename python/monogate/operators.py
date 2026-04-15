"""
monogate.operators -- registry and comparison utilities for all Operator instances.

Usage::

    from monogate.operators import EML, EDL, EXL, EAL, EMN
    from monogate.operators import ALL_OPERATORS, COMPLETE_OPERATORS
    from monogate.operators import get_operator, markdown_table, compare_all

    get_operator('EXL')         # -> EXL Operator instance
    compare_all()               # prints ASCII comparison table
    print(markdown_table())     # prints GitHub-Flavored Markdown table
"""

import math
from .core import EML, EDL, EXL, EAL, EMN, Operator

__all__ = [
    "EML", "EDL", "EXL", "EAL", "EMN",
    "ALL_OPERATORS",
    "COMPLETE_OPERATORS",
    "get_operator",
    "compare_all",
    "markdown_table",
]

ALL_OPERATORS: list[Operator] = [EML, EDL, EXL, EAL, EMN]
COMPLETE_OPERATORS: list[Operator] = [EML, EDL]

_REGISTRY: dict[str, Operator] = {op.name: op for op in ALL_OPERATORS}

# Node counts for known operations (None = not computable)
_NODE_COUNTS: dict[str, tuple] = {
    # name       EML   EDL   EXL   EAL   EMN
    "exp(x)":   (  1,    1,    1,    1, None),
    "ln(x)":    (  3,    3,    1, None, None),
    "mul(x,y)": ( 13,    7, None, None, None),
    "div(x,y)": ( 15,    1, None, None, None),
    "pow(x,n)": ( 15,   11,    3, None, None),
    "recip(x)": (  5,    2, None, None, None),
    "neg(x)":   (  9,    6, None, None, None),
    "add(x,y)": ( 11, None, None, None, None),
    "sub(x,y)": (  5, None, None, None, None),
}

_OP_ORDER = ["EML", "EDL", "EXL", "EAL", "EMN"]


def get_operator(name: str) -> Operator:
    """Look up an Operator by name ('EML', 'EDL', 'EXL', 'EAL', 'EMN').

    Raises:
        KeyError: if name not in registry.
    """
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown operator {name!r}. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]


def compare_all(operators: list[Operator] | None = None) -> None:
    """Print an ASCII comparison table for the given operators.

    Args:
        operators: list of Operator instances to compare.
                   Defaults to ALL_OPERATORS.
    """
    ops = operators or ALL_OPERATORS
    names = [o.name for o in ops]

    col = 7
    sep_row = "  " + "-" * (14 + (col + 2) * len(names))

    header = f"  {'Function':<14}" + "".join(f"  {n:^{col}}" for n in names)
    print(header)
    print(sep_row)

    for fname, counts in _NODE_COUNTS.items():
        row = f"  {fname:<14}"
        row_vals = [counts[_OP_ORDER.index(n)] if n in _OP_ORDER else None for n in names]
        valid = [v for v in row_vals if v is not None]
        best = min(valid) if valid else None
        for v in row_vals:
            if v is None:
                cell = "---"
            else:
                cell = f"{v}n" + ("*" if v == best and valid.count(best) < len(valid) else "")
            row += f"  {cell:^{col}}"
        print(row)

    print(sep_row)

    # Stability row
    bm_row = f"  {'exp err':<14}"
    for op in ops:
        bm = op.benchmark()
        v = bm.get('exp_max_err')
        bm_row += f"  {(str(v.__format__('.0e')) if v is not None else '---'):^{col}}"
    print(bm_row)

    bm_row = f"  {'ln  err':<14}"
    for op in ops:
        bm = op.benchmark()
        v = bm.get('ln_max_err')
        bm_row += f"  {(str(v.__format__('.0e')) if v is not None else '---'):^{col}}"
    print(bm_row)

    print(sep_row)

    comp_row = f"  {'Complete?':<14}"
    for op in ops:
        meta = op.__dict__.get('_meta', {})
        comp_row += f"  {'YES' if meta.get('complete') else 'NO':^{col}}"
    print(comp_row)

    print(f"\n  * = uniquely fewest nodes for this function")


def markdown_table(operators: list[Operator] | None = None) -> str:
    """Return a GitHub-Flavored Markdown comparison table.

    Args:
        operators: list of Operator instances. Defaults to ALL_OPERATORS.

    Returns:
        Markdown string ready to paste into README or docs.
    """
    ops = operators or ALL_OPERATORS
    names = [o.name for o in ops]

    lines: list[str] = []

    # Header
    header_cols = ["Function"] + names + ["Notes"]
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

    # Node count rows
    for fname, counts in _NODE_COUNTS.items():
        row_vals = [counts[_OP_ORDER.index(n)] if n in _OP_ORDER else None for n in names]
        valid = [v for v in row_vals if v is not None]
        best = min(valid) if valid else None
        cells = []
        for v in row_vals:
            if v is None:
                cells.append("---")
            elif v == best and valid.count(best) < len(valid):
                cells.append(f"**{v}n**")
            else:
                cells.append(f"{v}n")
        lines.append("| " + fname + " | " + " | ".join(cells) + " | |")

    # Separator
    lines.append("| | " + " | ".join([""] * len(names)) + " | |")

    # Accuracy rows
    for label, key in [("exp rel err", "exp_max_err"), ("ln rel err", "ln_max_err")]:
        cells = []
        for op in ops:
            bm = op.benchmark()
            v = bm.get(key)
            cells.append(f"`{v:.0e}`" if v is not None else "---")
        lines.append("| " + label + " | " + " | ".join(cells) + " | |")

    # Complete row
    cells = []
    for op in ops:
        meta = op.__dict__.get('_meta', {})
        cells.append("**YES**" if meta.get('complete') else "NO")
    lines.append("| Complete? | " + " | ".join(cells) + " | |")

    # Gate row
    cells = []
    for op in ops:
        meta = op.__dict__.get('_meta', {})
        g = meta.get('gate', '?')
        cells.append(f"`{g}`")
    lines.append("| Gate | " + " | ".join(cells) + " | |")

    return "\n".join(lines)
