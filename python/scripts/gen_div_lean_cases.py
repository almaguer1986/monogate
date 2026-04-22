"""
Generate Lean proof code for all 3072 F1-F12-outer 2-node F16 circuits.
Witness: (x,y) = (6,3), target = x/y = 2.
Each circuit is proved ≠ div by showing its value at (6,3) ≠ 2.
"""
import math
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Lean-compatible semantics: Real.log x = log|x| for x≠0, 0 for x=0
def L(x): return math.log(abs(x)) if x != 0 else 0.0
def E(x):
    try: return math.exp(x)
    except OverflowError: return float('inf')

OPS_PY = {
    'F1':  lambda a, b: E(a) - L(b),
    'F2':  lambda a, b: E(a) - L(-b),
    'F3':  lambda a, b: E(-a) - L(b),
    'F4':  lambda a, b: E(-a) - L(-b),
    'F5':  lambda a, b: E(b) - L(a),
    'F6':  lambda a, b: E(-b) - L(a),
    'F7':  lambda a, b: E(b) - L(-a),
    'F8':  lambda a, b: E(-b) - L(-a),
    'F9':  lambda a, b: a - L(b),
    'F10': lambda a, b: a - L(-b),
    'F11': lambda a, b: L(E(a) + b),
    'F12': lambda a, b: L(E(a) - b),
    'F13': lambda a, b: E(a * L(b)),
    'F14': lambda a, b: E(a + L(b)),
    'F15': lambda a, b: E(a + L(-b)),
    'F16': lambda a, b: E(L(a) + L(b)),
}

# Lean definition strings for each op (one arg = v, other = c based on shape)
# D_Fk_lean(v, c) = the Lean expression for the OUTER op
# Shape A: outer(inner(a,b), c) i.e. outer_lean(inner_expr, c_expr)
# Shape B: outer(c, inner(a,b)) i.e. outer_lean(c_expr, inner_expr)
# We'll just unfold using simp [D_Fx] in Lean.

# Lean inner expression at specific numeric inputs
def inner_lean_expr(inner_name, a_val, b_val):
    """Return the Lean expression for inner(a_val, b_val)."""
    av = str(int(a_val)) if a_val == int(a_val) else str(a_val)
    bv = str(int(b_val)) if b_val == int(b_val) else str(b_val)
    exprs = {
        'F1':  f"Real.exp {av} - Real.log {bv}",
        'F2':  f"Real.exp {av} - Real.log (-{bv})",
        'F3':  f"Real.exp (-{av}) - Real.log {bv}",
        'F4':  f"Real.exp (-{av}) - Real.log (-{bv})",
        'F5':  f"Real.exp {bv} - Real.log {av}",
        'F6':  f"Real.exp (-{bv}) - Real.log {av}",
        'F7':  f"Real.exp {bv} - Real.log (-{av})",
        'F8':  f"Real.exp (-{bv}) - Real.log (-{av})",
        'F9':  f"({av} : ℝ) - Real.log {bv}",
        'F10': f"({av} : ℝ) - Real.log (-{bv})",
        'F11': f"Real.log (Real.exp {av} + {bv})",
        'F12': f"Real.log (Real.exp {av} - {bv})",
        'F13': f"Real.exp ({av} * Real.log {bv})",
        'F14': f"Real.exp ({av} + Real.log {bv})",
        'F15': f"Real.exp ({av} + Real.log (-{bv}))",
        'F16': f"Real.exp (Real.log {av} + Real.log {bv})",
    }
    return exprs[inner_name]

def lean_op_names():
    return ['F1','F2','F3','F4','F5','F6','F7','F8',
            'F9','F10','F11','F12','F13','F14','F15','F16']

F12_OUTERS = ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12']

def gen_proof(outer, inner, a_s, b_s, c_s, shape, inner_val, result, idx):
    """Generate Lean proof for one circuit. Returns proof block string."""
    a_val = 6.0 if a_s == 'x' else 3.0
    b_val = 6.0 if b_s == 'x' else 3.0
    c_val = 6.0 if c_s == 'x' else 3.0

    # Lean argument names in the theorem statement
    # Shape A: D_outer (D_inner (if a_x then x else y) (if b_x then x else y)) (if c_x then x else y)
    # Shape B: D_outer (if c_x then x else y) (D_inner ...)

    a_wire = "x" if a_s == 'x' else "y"
    b_wire = "x" if b_s == 'x' else "y"
    c_wire = "x" if c_s == 'x' else "y"

    # Theorem name
    thm_name = f"circ_{idx:04d}_{outer}_{inner}_{a_s}{b_s}{c_s}_{shape}"

    # Circuit expression in Lean
    inner_call = f"D_{inner} {a_wire} {b_wire}"
    if shape == 'A':
        circ_call = f"D_{outer} ({inner_call}) {c_wire}"
    else:
        circ_call = f"D_{outer} {c_wire} ({inner_call})"

    # Inner and outer Lean expressions at (6,3)
    ie = inner_lean_expr(inner, a_val, b_val)
    cv = str(int(c_val)) if c_val == int(c_val) else str(c_val)

    # Determine proof strategy
    diff = abs(result - 2.0)

    # Generate the proof body
    proof = gen_proof_body(outer, inner, a_val, b_val, c_val, shape,
                           inner_val, result, ie, cv, diff)

    lines = [
        f"private lemma {thm_name} :",
        f"    ¬ (∀ x y : ℝ, {circ_call} = x / y) := by",
        f"  intro h",
        f"  have key := h 6 3",
        f"  norm_num at key",
        f"  simp only [D_{outer}, D_{inner}] at key",
        f"  simp only [Real.log_neg_eq_log] at key",
    ] + proof
    return "\n".join(lines)

def gen_proof_body(outer, inner, a_val, b_val, c_val, shape,
                   inner_val, result, ie, cv, diff):
    """
    Return list of lines (proof tactics) after the simp unfolding.
    key has type: [unfolded circuit expression at (6,3)] = 2
    """
    # Categorize result
    if result > 50:
        # Very large: use exp6_gt_390 or exp3_gt_19
        return large_result_proof(outer, inner_val, c_val, ie, cv, shape)
    elif result > 3.5:
        # Moderately large
        return moderate_large_proof(outer, inner_val, c_val, ie, cv, shape)
    elif result < -1:
        # Clearly negative
        return negative_result_proof(outer, inner_val, c_val, ie, cv, shape)
    elif result < 1:
        # Small positive or zero
        return small_result_proof(outer, inner_val, c_val, ie, cv, shape)
    else:
        # Near 2: specific proof
        return near2_proof(outer, inner, a_val, b_val, c_val, shape,
                           inner_val, result, ie, cv, diff)

def log_lt_2_lemma(c_val):
    return f"log{int(c_val)}_lt_2"

def log_gt_1_lemma(c_val):
    return f"log{int(c_val)}_gt_1"

def large_result_proof(outer, inner_val, c_val, ie, cv, shape):
    """Value >> 2. Use exponential lower bounds."""
    return [
        f"  -- result >> 2; contradiction from positivity and bounds",
        f"  linarith [exp6_gt_390, Real.log_pos (show (1:ℝ) < {int(c_val)} from by norm_num)]",
    ]

def moderate_large_proof(outer, inner_val, c_val, ie, cv, shape):
    """Value ∈ (3.5, 50). Use exp3_gt_19 or similar."""
    llt2 = log_lt_2_lemma(c_val)
    if outer in ('F1', 'F2', 'F5', 'F7'):
        return [
            f"  -- result > 3 since exp(inner) > exp(3) > 19 and log(c) < 2",
            f"  linarith [exp3_gt_19, {llt2}]",
        ]
    elif outer in ('F9', 'F10'):
        return [
            f"  -- inner_val > 3.5 and log(c) < 2; result > 1.5",
            f"  linarith [{llt2}]",
        ]
    elif outer in ('F11', 'F12'):
        return [
            f"  -- log(exp(inner) + c) > log(exp(3)) = 3 > 2",
            f"  linarith [exp3_gt_19, Real.log_pos (show (0:ℝ) < Real.exp 3 from Real.exp_pos _)]",
        ]
    else:
        return [
            f"  linarith [exp3_gt_19, {llt2}]",
        ]

def negative_result_proof(outer, inner_val, c_val, ie, cv, shape):
    """Value < -1 < 0 < 2."""
    lgt1 = log_gt_1_lemma(c_val)
    if outer in ('F3', 'F4', 'F6', 'F8'):
        return [
            f"  -- exp(-inner) < 1 and log(c) > 1, so result < 0 < 2",
            f"  linarith [Real.exp_pos _, {lgt1}]",
        ]
    elif outer in ('F1', 'F2', 'F5', 'F7'):
        return [
            f"  -- inner < 0 so exp(inner) < 1 and log(c) > 1; result < 0",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9, Real.exp_pos ({ie}), {lgt1}]",
        ]
    else:
        return [
            f"  linarith [Real.exp_pos _, {lgt1}]",
        ]

def small_result_proof(outer, inner_val, c_val, ie, cv, shape):
    """Value < 1 < 2."""
    lgt1 = log_gt_1_lemma(c_val)
    if outer in ('F3', 'F4', 'F6', 'F8'):
        return [
            f"  -- result < 1: exp(-v) small and log subtracted",
            f"  linarith [Real.exp_pos _, {lgt1}]",
        ]
    elif outer in ('F1', 'F5'):
        return [
            f"  -- exp(small_inner) small relative to log(c) > 1; result < 2",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9, Real.exp_pos ({ie}), {lgt1}]",
        ]
    elif outer in ('F9',):
        return [
            f"  linarith [{lgt1}]",
        ]
    else:
        return [
            f"  linarith [Real.exp_pos _, {lgt1}]",
        ]

def near2_proof(outer, inner, a_val, b_val, c_val, shape,
                inner_val, result, ie, cv, diff):
    """Near-2 case: custom arithmetic proof."""
    # We'll generate specific proofs based on the outer op and inner value
    key = (outer, inner, int(a_val), int(b_val), int(c_val), shape)

    # Specific known near-2 cases with their proofs
    # These are the cases from the Python analysis output

    if outer == 'F9':
        # F9(v, c) = v - log(c). For = 2: v = 2 + log(c).
        # We need to show v ≠ 2 + log(c).
        if shape == 'A':
            # v = inner_val at (a_val, b_val), c = c_val
            return gen_F9A_proof(inner, a_val, b_val, c_val, inner_val, result)
        else:
            # F9(c, v): c - log(v) = 2 → log(v) = c-2. v = exp(c-2).
            return gen_F9B_proof(inner, a_val, b_val, c_val, inner_val, result, cv)

    elif outer == 'F11':
        # F11(v, c) = log(exp(v) + c). For = 2: exp(v)+c = exp(2). v = log(exp(2)-c).
        return gen_F11_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F3':
        # F3(v, c) = exp(-v) - log(c). For = 2: exp(-v) = 2 + log(c).
        return gen_F3_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F6':
        # F6(v, c) = exp(-c) - log(v). For = 2: log(v) = exp(-c) - 2.
        return gen_F6_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F1':
        # F1(v, c) = exp(v) - log(c). For = 2: exp(v) = 2 + log(c).
        return gen_F1_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F5':
        # F5(v, c) = exp(c) - log(v). Note: F5(a,b) = exp(b) - log(a).
        # Shape A: D_F5(inner, c) = exp(c) - log(inner). For = 2: log(inner) = exp(c) - 2.
        return gen_F5_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F10':
        # F10(v, c) = v - log(-c). For c > 0: log(-c) = 0. So F10(v,c) = v.
        # For = 2: v = 2. But inner_val ≠ 2 at (6,3).
        return gen_F10_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    elif outer == 'F12':
        # F12(v, c) = log(exp(v) - c). For = 2: exp(v) - c = exp(2). v = log(exp(2)+c).
        return gen_F12_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv)

    else:
        # Fallback: use nlinarith with bounds
        return [
            f"  -- Near-2 case for {outer} outer, {inner} inner",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9, Real.exp_add 1 1,",
            f"             Real.exp_add 1 2, Real.exp_add 3 3,",
            f"             Real.log_pos (show (1:ℝ) < 3 from by norm_num),",
            f"             Real.log_pos (show (1:ℝ) < 6 from by norm_num)]",
        ]

def gen_F9A_proof(inner, a_val, b_val, c_val, inner_val, result):
    """F9(inner_val, c_val) ≠ 2. Need: inner_val ≠ 2 + log(c_val)."""
    # F9(v,c) = v - log(c). = 2 iff v = 2 + log(c).
    # result > 2: inner_val > 2 + log(c_val). Prove inner_val > 2 + log(c_val).
    # result < 2: inner_val < 2 + log(c_val). Prove inner_val < 2 + log(c_val).
    c = int(c_val)

    if result > 2:
        # inner_val > 2 + log(c). Need to lower-bound inner_val and upper-bound 2+log(c).
        return gen_F9A_gt_proof(inner, a_val, b_val, c, inner_val, result)
    else:
        # inner_val < 2 + log(c).
        return gen_F9A_lt_proof(inner, a_val, b_val, c, inner_val, result)

def gen_F9A_gt_proof(inner, a_val, b_val, c, inner_val, result):
    """inner_val > 2 + log(c). Result > 2."""
    a, b = int(a_val), int(b_val)
    # Specific cases
    if inner == 'F11':
        # inner = log(exp(a) + b) > 2 + log(c)?
        # log(exp(a)+b) > 2 + log(c) ↔ exp(a)+b > exp(2+log(c)) = exp(2)*c
        # exp(a)+b > exp(2)*c: exp(3)+3 > exp(2)*3? exp(3) > 3*exp(2)-3.
        # exp(3) = exp(1)*exp(2) > 2.718*7.38 > 20.06 > 3*7.39-3 = 22.17-3 = 19.17 ✓
        return [
            f"  -- F9(log(exp({a})+{b}), {c}) > 2: log(exp({a})+{b}) > 2+log({c})",
            f"  -- ↔ exp({a})+{b} > exp(2)*{c} = {c}*exp(2)",
            f"  -- exp(3)+3 > 3*exp(2)-3 since exp(3)=exp(1)*exp(2) > 2.718*7.38 > 20.06 > 19.17",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  have he3 : Real.exp 3 = Real.exp 1 * Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add, ← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.log_lt_log (by linarith [Real.exp_pos 3] : (0:ℝ) < Real.exp {a} + {b})",
            f"               (show Real.exp {a} + {b} < Real.exp 2 * {c} from by nlinarith),",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]
    elif inner == 'F12':
        # inner = log(exp(a)-b) > 2 + log(c)?
        a_v, b_v = int(a_val), int(b_val)
        return [
            f"  -- F9(log(exp({a_v})-{b_v}), {c}) > 2 since log(exp({a_v})-{b_v}) > 2+log({c})",
            f"  -- exp({a_v})-{b_v} > exp(2)*{c}",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]
    elif inner in ('F9', 'F10'):
        # inner = a_v - log(b_v) or a_v - log(-b_v) = a_v (since b_v > 0)
        return [
            f"  -- F9({inner_val:.3f}, {c}) > 2 since {inner_val:.3f} > 2+log({c})",
            f"  linarith [{log_lt_2_lemma(c)}]",
        ]
    else:
        return [
            f"  -- F9 outer, result {result:.4f} > 2, inner={inner}, c={c}",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9, Real.exp_add 1 1,",
            f"             Real.exp_add 1 2, Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]

def gen_F9A_lt_proof(inner, a_val, b_val, c, inner_val, result):
    """inner_val < 2 + log(c). Result < 2."""
    return [
        f"  -- F9({inner_val:.4f}, {c}) < 2 since {inner_val:.4f} < 2+log({c})",
        f"  linarith [{log_gt_1_lemma(c)}]",
    ]

def gen_F9B_proof(inner, a_val, b_val, c_val, inner_val, result, cv):
    """F9(c_val, inner) ≠ 2. c - log(inner) = 2 → log(inner) = c-2. inner = exp(c-2)."""
    c = int(c_val)
    a, b = int(a_val), int(b_val)
    c_minus_2 = c - 2
    if result > 2:
        return [
            f"  -- F9({c}, inner) > 2 since log(inner) < {c_minus_2}",
            f"  linarith [{log_lt_2_lemma(c)}]",
        ]
    else:
        return [
            f"  -- F9({c}, inner) < 2 since log(inner) > {c_minus_2}",
            f"  linarith [{log_gt_1_lemma(c)}]",
        ]

def gen_F11_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F11(v, c) = log(exp(v) + c). For = 2: exp(v)+c = exp(2) ≈ 7.389."""
    c = int(c_val)
    a, b = int(a_val), int(b_val)
    # If result < 2: log(exp(v)+c) < 2 → exp(v)+c < exp(2)
    # Need: exp(v)+c < exp(2).
    # For inner_val (v) very negative (like -1.79): exp(-1.79) ≈ 0.17. exp(v)+c ≈ 0.17+6 = 6.17.
    # exp(2) ≈ 7.39. 6.17 < 7.39. ✓
    # For inner_val near 0 (like 0.049): exp(0.049)+6 ≈ 1.05+6 = 7.05. exp(2) ≈ 7.389. 7.05 < 7.389. ✓
    # For inner_val = 1.21: exp(1.21)+3 ≈ 3.35+3 = 6.35. exp(2) ≈ 7.39. 6.35 < 7.39. ✓
    # For inner_val = 1.21, c=6: exp(1.21)+6 ≈ 9.35 > exp(2). Result > 2. ✓
    if result < 2:
        # exp(v) + c < exp(2). Use exp(2) > 7.38 and bound exp(v)+c.
        return [
            f"  -- F11: log(exp(v)+{c}) < 2 since exp(v)+{c} < exp(2) ≈ 7.39",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  have hlog2 : Real.log (Real.exp 2) = 2 := Real.log_exp 2",
            f"  -- key: log(exp(v)+{c}) = 2 → exp(v)+{c} = exp(2)",
            f"  -- But exp(v)+{c} < exp(2): exp(v) < exp(2)-{c} < 7.39-{c}",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.exp_pos ({ie}),",
            f"             Real.log_lt_log (show (0:ℝ) < Real.exp ({ie}) + {c} from by positivity)",
            f"                           (show Real.exp ({ie}) + {c} < Real.exp 2 from by",
            f"                             nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9])]",
        ]
    else:
        # exp(v) + c > exp(2). Result > 2.
        return [
            f"  -- F11: log(exp(v)+{c}) > 2 since exp(v)+{c} > exp(2)",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.exp_pos ({ie})]",
        ]

def gen_F3_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F3(v, c) = exp(-v) - log(c). For = 2: exp(-v) = 2 + log(c) ≈ 3.1."""
    c = int(c_val)
    if result < 2:
        # exp(-v) - log(c) < 2 → exp(-v) < 2 + log(c).
        # v > 0 (inner is negative? no inner_val is the inner value which is negative)
        # Actually inner_val is negative (around -1), so v = inner_val < 0.
        # exp(-v) = exp(-inner_val) where inner_val < 0, so -inner_val > 0, exp(-inner_val) > 1.
        # But exp(-inner_val) < 2 + log(c): inner_val ≈ -1.09, exp(1.09) ≈ 2.97. 2+log(3) ≈ 3.10. 2.97 < 3.10. ✓
        return [
            f"  -- F3(v,{c}) = exp(-v) - log({c}) < 2 since exp(-v) < 2+log({c})",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9, Real.exp_add 1 1,",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num),",
            f"             Real.exp_pos ({ie})]",
        ]
    else:
        return [
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]

def gen_F6_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F6(v, c) = exp(-c) - log(v). After log_neg_eq_log, handle log(inner_val)."""
    c = int(c_val)
    # D_F6(a,b) = exp(-b) - log(a). Shape A: D_F6(inner, c) = exp(-c) - log(inner).
    # exp(-c) is very small (exp(-3) ≈ 0.05, exp(-6) ≈ 0.0025).
    # Result < 2 in all F6 near-2 cases since exp(-c) < 1 and log(|inner|) could be >0.
    if result < 2:
        if inner_val > 1:
            return [
                f"  -- F6: exp(-{c}) - log(inner). exp(-{c}) < 1, log(inner) > 0. result < 1 < 2.",
                f"  nlinarith [Real.exp_pos ((-{c}:ℝ)), Real.exp_one_gt_d9,",
                f"             Real.log_pos (show (1:ℝ) < {inner_val:.2f} from by norm_num)]",
            ]
        else:
            return [
                f"  -- F6: exp(-{c}) - log(inner) << 2. exp(-{c}) < 1 < 2.",
                f"  nlinarith [Real.exp_pos ((-{c}:ℝ)), Real.exp_one_gt_d9, exp3_gt_19,",
                f"             Real.exp_add 1 1, Real.exp_add 1 2]",
            ]
    else:
        return [
            f"  -- F6: exp(-{c}) - log(inner) > 2. Needs exp(-inner) large.",
            f"  nlinarith [Real.exp_pos ((-{c}:ℝ)), Real.exp_one_gt_d9, exp3_gt_19]",
        ]

def gen_F1_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F1(v,c) = exp(v) - log(c). Near-2 case."""
    c = int(c_val)
    a, b = int(a_val), int(b_val)
    # inner_val ≈ 1.21 (F9(y,x) = 3-log(6))
    if result < 2:
        # exp(inner_val) - log(c) < 2 → exp(inner_val) < 2 + log(c).
        # For inner=F9(y,x): inner_val = 3-log(6). exp(3-log(6)) = exp(3)/6. 2+log(6) ≈ 3.79.
        # exp(3)/6 < 3.79 ↔ exp(3) < 6*3.79 = 22.74 ↔ exp(3) < 22.74.
        # exp(3) < (exp(1))^3 < 2.71829^3. 2.71829^3 ≈ 20.088 < 22.74. ✓
        return [
            f"  -- F1: exp(v) - log({c}) < 2. v = {inner_val:.4f}, exp(v) < 2+log({c}).",
            f"  have he3 : Real.exp 3 = Real.exp 1 * Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add, ← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]
    else:
        return [
            f"  -- F1: exp(v) - log({c}) > 2. v = {inner_val:.4f}, exp(v) > 2+log({c}).",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
        ]

def gen_F5_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F5(v,c) = exp(c) - log(v). Near-2 case."""
    # D_F5(a,b) = exp(b) - log(a). Shape A: D_F5(inner, c) = exp(c) - log(inner).
    c = int(c_val)
    return [
        f"  -- F5: exp(c) - log(inner). Result {result:.4f}.",
        f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
        f"    rw [← Real.exp_add]; ring_nf",
        f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
        f"             Real.log_pos (show (1:ℝ) < {c} from by norm_num)]",
    ]

def gen_F10_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F10(v,c) = v - log(-c). Lean: log(-c) = log(c). F10 = F9 after rewrite."""
    c = int(c_val)
    # After simp [Real.log_neg_eq_log], log(-c) → log(c).
    # So key becomes: inner_val - log(c) = 2. Prove inner_val ≠ 2 + log(c).
    if result < 2:
        return [
            f"  -- F10: after log_neg_eq_log, inner - log({c}) < 2. inner = {inner_val:.4f}.",
            f"  linarith [{log_gt_1_lemma(c)}]",
        ]
    else:
        return [
            f"  -- F10: after log_neg_eq_log, inner - log({c}) > 2. inner = {inner_val:.4f}.",
            f"  linarith [{log_lt_2_lemma(c)}]",
        ]

def gen_F12_proof(inner, a_val, b_val, c_val, inner_val, result, shape, ie, cv):
    """F12(v, c) = log(exp(v) - c). Near-2 case."""
    c = int(c_val)
    if result < 2:
        return [
            f"  -- F12: log(exp(v)-{c}) < 2. exp(v)-{c} < exp(2).",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.exp_pos ({ie})]",
        ]
    else:
        return [
            f"  -- F12: log(exp(v)-{c}) > 2. exp(v)-{c} > exp(2).",
            f"  have he2 : Real.exp 2 = Real.exp 1 * Real.exp 1 := by",
            f"    rw [← Real.exp_add]; ring_nf",
            f"  nlinarith [Real.exp_one_gt_d9, Real.exp_one_lt_d9,",
            f"             Real.exp_pos ({ie})]",
        ]

# ========================================================
# Main generation
# ========================================================

X, Y = 6.0, 3.0

inner_vals = {}
for name, fn in OPS_PY.items():
    for a_s in ['x', 'y']:
        for b_s in ['x', 'y']:
            a = X if a_s == 'x' else Y
            b = X if b_s == 'x' else Y
            try:
                v = fn(a, b)
                if not math.isfinite(v): v = 1e18
            except: v = 1e18
            inner_vals[(name, a_s, b_s)] = v

# Generate the Lean file
lines = []
lines.append("import MonogateEML.DivLowerBound3")
lines.append("")
lines.append("open Real")
lines.append("")
lines.append("namespace DivLowerBound3Full")
lines.append("")

# Helper lemmas
lines.append("""private lemma exp2_gt_7 : (7 : ℝ) < Real.exp 2 := by
  have h := Real.exp_add 1 1
  nlinarith [Real.exp_one_gt_d9, Real.exp_pos 1]

private lemma exp3_gt_19 : (19 : ℝ) < Real.exp 3 := by
  have h12 := Real.exp_add 1 2
  have h2 := exp2_gt_7
  nlinarith [Real.exp_one_gt_d9]

private lemma exp6_gt_390 : (390 : ℝ) < Real.exp 6 := by
  have h33 := Real.exp_add 3 3
  nlinarith [exp3_gt_19]

private lemma log3_gt_1 : (1 : ℝ) < Real.log 3 := by
  have : Real.log (Real.exp 1) < Real.log 3 :=
    Real.log_lt_log (Real.exp_pos 1) (by linarith [Real.exp_one_lt_d9])
  rwa [Real.log_exp] at this

private lemma log6_gt_1 : (1 : ℝ) < Real.log 6 := by
  have : Real.log (Real.exp 1) < Real.log 6 :=
    Real.log_lt_log (Real.exp_pos 1) (by linarith [Real.exp_one_lt_d9])
  rwa [Real.log_exp] at this

private lemma log3_lt_2 : Real.log 3 < (2 : ℝ) := by
  have : Real.log 3 < Real.log (Real.exp 2) :=
    Real.log_lt_log (by norm_num) (by linarith [exp2_gt_7])
  rwa [Real.log_exp] at this

private lemma log6_lt_2 : Real.log 6 < (2 : ℝ) := by
  have : Real.log 6 < Real.log (Real.exp 2) :=
    Real.log_lt_log (by norm_num) (by linarith [exp2_gt_7])
  rwa [Real.log_exp] at this
""")

# Generate circuit lemmas
idx = 0
all_lemma_names = []
for outer in F12_OUTERS:
    outer_fn = OPS_PY[outer]
    for (inner, a_s, b_s), iv in inner_vals.items():
        for c_s in ['x', 'y']:
            c = X if c_s == 'x' else Y
            for shape in ['A', 'B']:
                try:
                    result = outer_fn(iv, c) if shape == 'A' else outer_fn(c, iv)
                    if not math.isfinite(result): result = 1e18
                except: result = 1e18

                idx += 1
                thm_name = f"circ_{idx:04d}_{outer}_{inner}_{a_s}{b_s}{c_s}_{shape}"
                all_lemma_names.append(thm_name)

                proof_block = gen_proof(outer, inner, a_s, b_s, c_s, shape, iv, result, idx)
                lines.append(proof_block)
                lines.append("")

# Write the bundled main theorem
lines.append("")
lines.append("end DivLowerBound3Full")

output_path = "lean/MonogateEML/MonogateEML/DivLowerBound3Full.lean"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Generated {idx} lemmas -> {output_path}")
print(f"File size: {len(chr(10).join(lines))} chars")
