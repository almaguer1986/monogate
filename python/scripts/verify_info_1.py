"""
verify_info_1.py
Verify information theory equations from info_1_information_theory.json

Tests:
  1. Shannon entropy — binary: H(0.5,0.5)=ln(2); H(0.9,0.1) known value
  2. KL divergence — P=[0.4,0.6], Q=[0.5,0.5]
  3. Mutual information — independent: I = 0
  4. Perplexity — uniform over 100 classes => PP = 100
  5. JSD — P=[1,0], Q=[0,1] => JSD = ln(2)
"""
import math
import sys

PASS = 0
FAIL = 0

def check(label, computed, expected, tol=1e-10):
    global PASS, FAIL
    err = abs(computed - expected)
    if err <= tol:
        print(f"  PASS  {label}: {computed:.8f}  (expected {expected:.8f})")
        PASS += 1
    else:
        print(f"  FAIL  {label}: got {computed:.8f}, expected {expected:.8f}, err={err:.2e}")
        FAIL += 1

# ----------------------------------------------------------------
print("=" * 60)
print("Verify: Information Theory Equations")
print("=" * 60)

# --- 1. Shannon entropy -sum p_i * ln(p_i) ---
print("\n[1] Shannon Entropy H(X)")

def shannon(probs):
    return -sum(p * math.log(p) for p in probs if p > 0)

# H(0.5, 0.5) = ln(2) in nats
check("H(0.5,0.5) = ln(2)", shannon([0.5, 0.5]), math.log(2))
# H(0.9, 0.1): -0.9*ln(0.9) - 0.1*ln(0.1)
expected_h91 = -(0.9 * math.log(0.9) + 0.1 * math.log(0.1))
check("H(0.9,0.1)", shannon([0.9, 0.1]), expected_h91)
# Uniform N=4: H = ln(4)
check("H(0.25,0.25,0.25,0.25) = ln(4)", shannon([0.25]*4), math.log(4))

# --- 2. KL divergence sum p_i * ln(p_i/q_i) ---
print("\n[2] KL Divergence D_KL(P||Q)")

def kl(P, Q):
    return sum(p * math.log(p / q) for p, q in zip(P, Q) if p > 0)

P = [0.4, 0.6]
Q = [0.5, 0.5]
expected_kl = 0.4 * math.log(0.4/0.5) + 0.6 * math.log(0.6/0.5)
check("D_KL([0.4,0.6]||[0.5,0.5])", kl(P, Q), expected_kl)
# D_KL >= 0
check("D_KL >= 0", kl(P, Q), abs(kl(P, Q)))
# D_KL(P||P) = 0
check("D_KL(P||P) = 0", kl(P, P), 0.0)

# --- 3. Mutual Information I(X;Y) ---
print("\n[3] Mutual Information I(X;Y)")

def mutual_info(joint):
    """joint is 2D array joint[i][j] = p(x_i, y_j)"""
    rows = len(joint)
    cols = len(joint[0])
    p_x = [sum(joint[i][j] for j in range(cols)) for i in range(rows)]
    p_y = [sum(joint[i][j] for i in range(rows)) for j in range(cols)]
    total = 0.0
    for i in range(rows):
        for j in range(cols):
            pxy = joint[i][j]
            if pxy > 0:
                total += pxy * math.log(pxy / (p_x[i] * p_y[j]))
    return total

# Independent case: p(x,y) = p(x)*p(y) => I = 0
joint_independent = [[0.2*0.3, 0.2*0.7], [0.8*0.3, 0.8*0.7]]
check("I(X;Y) independent = 0", mutual_info(joint_independent), 0.0)

# Perfectly correlated: p(x=0,y=0)=0.5, p(x=1,y=1)=0.5 => I = H(X) = ln(2)
joint_corr = [[0.5, 0.0], [0.0, 0.5]]
check("I(X;Y) perfectly correlated = ln(2)", mutual_info(joint_corr), math.log(2))

# --- 4. Perplexity PP = exp(-1/N * sum ln(p_i)) ---
print("\n[4] Perplexity")

def perplexity(probs):
    N = len(probs)
    avg_log = sum(math.log(p) for p in probs) / N
    return math.exp(-avg_log)

# Uniform over 100: PP = 100
uniform_100 = [1/100] * 100
check("PP(uniform 100) = 100", perplexity(uniform_100), 100.0)

# Uniform over N: PP = N
for N in [2, 10, 1000]:
    check(f"PP(uniform {N}) = {N}", perplexity([1/N]*N), float(N))

# --- 5. JSD(P||Q) = H(M) - (H(P)+H(Q))/2 ---
print("\n[5] Jensen-Shannon Divergence")

def jsd(P, Q):
    M = [(p + q) / 2 for p, q in zip(P, Q)]
    return shannon(M) - (shannon(P) + shannon(Q)) / 2

# JSD(P||P) = 0
P2 = [0.3, 0.7]
check("JSD(P||P) = 0", jsd(P2, P2), 0.0)

# JSD([1,0]||[0,1]): M=[0.5,0.5], H(M)=ln(2), H(P)=H(Q)=0
# JSD = ln(2) - 0 = ln(2)
P_delta0 = [1.0, 1e-300]  # approximate: pure point mass
Q_delta1 = [1e-300, 1.0]
# Use analytic limit: H([1,0])=0, H([0,1])=0, H([0.5,0.5])=ln2
jsd_analytic = math.log(2)  # ln(2)
# Compute numerically with proper endpoint handling
def shannon_safe(probs):
    return -sum(p * math.log(p) for p in probs if p > 1e-300)

def jsd_safe(P, Q):
    M = [(p + q) / 2 for p, q in zip(P, Q)]
    return shannon_safe(M) - (shannon_safe(P) + shannon_safe(Q)) / 2

check("JSD([1,0]||[0,1]) = ln(2)", jsd_safe([1.0, 0.0], [0.0, 1.0]), math.log(2), tol=1e-10)

# JSD([0.4,0.6]||[0.5,0.5])
jsd_val = jsd([0.4, 0.6], [0.5, 0.5])
check("JSD >= 0", jsd_val, abs(jsd_val))
check("JSD <= ln(2)", jsd_val <= math.log(2), True)

# ----------------------------------------------------------------
print("\n" + "=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
print("=" * 60)

# Summary table
print("\n--- Summary: Equation Costs (SuperBEST v4) ---")
print(f"{'Equation':<40} {'Cost formula':<25} {'Key EML insight'}")
print("-" * 100)
rows = [
    ("Shannon entropy H(X)         [N terms]", "8N - 3",
     "neg-first makes each term positive => add_pos"),
    ("KL divergence D_KL(P||Q)     [N terms]", "16N - 11",
     "terms individually signed => add_gen; 2x Shannon"),
    ("Cross-entropy loss H(P,Q)    [N terms]", "8N - 3",
     "identical structure to Shannon; ML loss == IT formula"),
    ("Mutual info I(X;Y)           [|X||Y| cells]", "18|X||Y| - 11",
     "extra mul for marginal product; add_gen (signed terms)"),
    ("Perplexity PP                [N tokens]", "12N - 6",
     "costly: add_gen dominates (all ln<=0, no sign flip)"),
    ("Entropy rate H(Markov)       [|S| states]", "8|S|^2 + 2|S| - 3",
     "quadratic in |S|: inner Shannon loop per state"),
    ("Conditional entropy H(Y|X)   [|X||Y| pairs]", "10|X||Y| - 3",
     "div for p(y|x); terms positive => add_pos saves cost"),
    ("Jensen-Shannon div JSD(P||Q) [N terms]", "29N - 2",
     "3x Shannon plus mixture compute; most expensive per-N"),
]
for name, formula, insight in rows:
    print(f"  {name:<44} {formula:<22} {insight}")

if FAIL > 0:
    sys.exit(1)
