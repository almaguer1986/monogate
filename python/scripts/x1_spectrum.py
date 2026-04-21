import json

equations = [
    (2, "Basic Reproduction Number R0", "epidemiology"),
    (3, "Herd Immunity Threshold", "epidemiology"),
    (5, "Malthusian Growth", "population biology"),
    (5, "Allometric Scaling Kleiber", "biological scaling"),
    (6, "Michaelis-Menten Hill n=1", "enzyme kinetics"),
    (7, "Infection Growth Exponential", "epidemiology"),
    (8, "Gompertz Growth", "tumor biology"),
    (9, "Logistic Growth", "ecology"),
    (12, "Hill Equation general n", "pharmacology"),
    (16, "Lotka-Volterra per step", "ecology"),
    (20, "SIR Model per timestep", "epidemiology"),
    (6, "Proton Motive Force", "biophysics"),
    (6, "Motor Torque simplified", "biophysics"),
    (5, "Proton Hop Rate Arrhenius", "biophysics"),
    (10, "Motor Switching Hill", "biophysics"),
    (4, "Motor Efficiency simplified", "biophysics"),
    (11, "Nernst Equation", "electrochemistry"),
    (7, "Henderson-Hasselbalch", "acid-base chemistry"),
    (18, "Chemical Equilibrium Constant", "chemical thermodynamics"),
    (10, "Rate Law 2-species", "chemical kinetics"),
    (6, "Michaelis-Menten chem", "enzyme kinetics"),
    (4, "Beer-Lambert absorbance", "spectroscopy"),
    (5, "Beer-Lambert transmittance", "spectroscopy"),
    (5, "pH Definition", "acid-base chemistry"),
    (2, "Gibbs-Helmholtz ratio", "thermodynamics"),
    (7, "Reaction Free Energy dG", "thermodynamics"),
    (5, "Integrated First-Order Rate Law", "chemical kinetics"),
    (1, "Log Utility U=ln(C)", "microeconomics"),
    (5, "Compound Interest continuous", "finance"),
    (6, "Price Elasticity arc", "microeconomics"),
    (6, "Laffer Curve", "public finance"),
    (6, "Discounting Factor", "finance"),
    (7, "CRRA Utility", "microeconomics"),
    (10, "Cobb-Douglas Production", "macroeconomics"),
    (11, "Compound Interest discrete", "finance"),
    (18, "CES Utility Function", "microeconomics"),
    (19, "Black-Scholes d1", "finance"),
    (2, "Black-Scholes d2 marginal", "finance"),
    (9, "Normal CDF approximation", "finance"),
    (50, "Black-Scholes Call Price standalone", "finance"),
    (54, "Black-Scholes Put Price standalone", "finance"),
    (14, "Black-Scholes Gamma", "finance"),
    (12, "Black-Scholes Vega", "finance"),
    (20, "Black-Scholes Theta shared", "finance"),
    (6, "Black-Scholes Rho shared", "finance"),
    (4, "Sharpe Ratio", "finance"),
    (6, "CAPM Expected Return", "finance"),
    (31, "Portfolio Variance 2-asset", "finance"),
    (4, "Value at Risk Normal", "finance"),
    (5, "Kelly Criterion continuous", "finance"),
    (3, "Log Return", "finance"),
    (8, "CAGR", "finance"),
    (4, "Sortino Ratio", "finance"),
    (12, "Shannon Entropy N=2", "information theory"),
    (12, "KL Divergence N=2", "information theory"),
    (12, "Cross-Entropy Loss N=2", "information theory"),
    (9, "Perplexity N=2", "information theory"),
    (3, "Boltzmann Factor kT const", "statistical mechanics"),
    (5, "Boltzmann Factor standalone", "statistical mechanics"),
    (8, "Fermi-Dirac Distribution", "quantum mechanics"),
    (8, "Bose-Einstein Distribution", "quantum mechanics"),
    (19, "Planck Spectral Radiance", "blackbody radiation"),
    (7, "Hydrogen Energy Levels", "atomic physics"),
    (2, "de Broglie Wavelength p given", "quantum mechanics"),
    (4, "de Broglie Wavelength mv", "quantum mechanics"),
    (2, "Heisenberg Uncertainty check", "quantum mechanics"),
    (9, "Particle-in-Box Wavefunction L const", "quantum mechanics"),
    (13, "Particle-in-Box Wavefunction full", "quantum mechanics"),
    (7, "Particle-in-Box Energy Levels", "quantum mechanics"),
    (8, "Partition Function N=2", "statistical mechanics"),
    (19, "Maxwell-Boltzmann Speed Distribution", "statistical mechanics"),
    (4, "Carnot Efficiency", "thermodynamics"),
    (3, "Boltzmann Entropy", "thermodynamics"),
    (9, "Clausius-Clapeyron Equation", "thermodynamics"),
    (10, "van_t Hoff log-ratio", "thermodynamics"),
    (13, "van_t Hoff full K2", "thermodynamics"),
    (6, "Ideal Gas Law", "thermodynamics"),
    (4, "Gibbs Free Energy", "thermodynamics"),
    (7, "Arrhenius Equation", "thermodynamics"),
    (9, "Stefan-Boltzmann Law", "thermodynamics"),
    (13, "Maxwell-Boltzmann Energy Distribution", "statistical mechanics"),
    (11, "Entropy of Mixing N=2", "thermodynamics"),
    (2, "Batting Average", "sports statistics"),
    (4, "Earned Run Average", "sports statistics"),
    (2, "Basketball Field Goal Pct", "sports statistics"),
    (30, "NFL Passer Rating", "sports statistics"),
    (10, "Pythagorean Expectation", "sports statistics"),
    (16, "ELO Rating System", "sports statistics"),
    (4, "Bayes Theorem", "probability"),
    (8, "Kelly Criterion discrete", "game theory"),
    (10, "Nash Equilibrium 2x2", "game theory"),
    (7, "Expected Value N=2", "probability"),
    (2, "Ohms Law V=IR", "physics"),
    (2, "Newtons Second Law F=ma", "physics"),
    (7, "Kinetic Energy 1/2 mv^2", "physics"),
    (9, "Newton Gravitation", "physics"),
    (2, "Wave Speed v=f lambda", "physics"),
    (4, "Hookes Law F=-kx", "physics"),
    (2, "Electric Power P=VI", "physics"),
    (2, "Pressure P=F/A", "physics"),
    (4, "Work W=Fd theta=0", "physics"),
    (2, "Momentum p=mv", "physics"),
    (5, "Centripetal Acceleration v^2/r", "physics"),
    (8, "Simple Pendulum Period", "physics"),
    (9, "Coulombs Law", "physics"),
    (2, "Wiens Displacement Law", "physics"),
    (8, "Sigmoid Logistic Activation", "machine learning"),
]

histogram = {}
eq_by_cost = {}
for cost, name, domain in equations:
    histogram[str(cost)] = histogram.get(str(cost), 0) + 1
    if cost not in eq_by_cost:
        eq_by_cost[cost] = (name, domain)

sorted_hist = {k: histogram[k] for k in sorted(histogram.keys(), key=lambda x: int(x))}
covered = set(int(k) for k in histogram)
gaps_in_catalog = [k for k in range(1, 51) if k not in covered]

reps = []
for k in range(1, 21):
    if k in eq_by_cost:
        name, domain = eq_by_cost[k]
        reps.append({"cost": k, "equation": name, "domain": domain, "source": "catalog_natural"})
    else:
        reps.append({
            "cost": k,
            "equation": "exp(f_{" + str(k-1) + "}): apply exp (1n) to any F16 expression with cost " + str(k-1),
            "domain": "constructed_inductive",
            "source": "inductive",
            "note": "No natural catalog equation at cost " + str(k) + ". Inductive: exp adds exactly 1n."
        })

proof = (
    "Proof by strong induction that for all k >= 1, there exists an F16 tree with cost exactly k."
    " Base case k=1: the expression ln(C) costs exactly 1n since ln is a single EML primitive node"
    " (verified: log utility U=ln(C) in economics, Boltzmann entropy S=kB*ln(Omega) in thermodynamics)."
    " Inductive step: suppose for some k >= 2 that every integer 1, 2, ..., k-1 is achievable."
    " In particular, there exists an F16 expression f with cost exactly k-1."
    " Then exp(f) is a valid F16 expression with cost exactly k, because the exp node costs 1n"
    " and the subtree f costs k-1n, giving total cost k."
    " Therefore by induction all k >= 1 are achievable. QED."
    " Remark: exp, ln, and recip each cost 1n in SuperBEST v5, providing three independent"
    " ways to increment cost by exactly 1. This is the structural reason the spectrum has no gaps."
    " Contrast: mul, div, sub, add, neg, sqrt cost 2n each; pow costs 3n."
    " The 1n primitives are the gap-fillers that make the spectrum dense over all positive integers."
)

proposition = (
    "The ELC/F16 cost spectrum is exactly the positive integers {1, 2, 3, 4, ...}."
    " For every k >= 1, there exists a natural or constructible F16 tree with cost exactly k."
    " The spectrum is DENSE - every positive integer is achievable."
    " Catalog gaps (k=15, 17, 21-29, ...) are sampling artifacts of the 295-equation catalog,"
    " not theoretical impossibilities."
    " Natural equations cover costs 1-14 continuously and reach 16, 18-20 as well."
    " The proposition is TRUE."
)

result = {
    "session": "X1",
    "title": "ELC/F16 Cost Spectrum - Full Analysis",
    "date": "2026-04-20",
    "cost_model": "SuperBEST v5",
    "catalog_equation_count": len(equations),
    "cost_histogram": sorted_hist,
    "gaps_in_catalog": gaps_in_catalog,
    "gaps_in_catalog_note": (
        "These integers (1-50) have zero natural equations in the ~295-equation catalog."
        " They are NOT impossible - inductive construction fills all gaps via exp composition."
    ),
    "spectrum_dense": True,
    "spectrum_note": (
        "The F16 cost spectrum is exactly the positive integers."
        " Every k >= 1 is achievable by induction. Catalog gaps are sampling artifacts."
    ),
    "proof": proof,
    "representatives_1_to_20": reps,
    "proposition": proposition,
    "key_findings": [
        "k=1: Unique class - only ln(C) achieves cost 1. Single EML primitive, the absolute minimum.",
        "k=2: Richest class with 14 natural equations spanning 6 domains: F=ma, V=IR, p=mv, R0=beta/gamma, batting avg, Wiens law, momentum, pressure, de Broglie, Heisenberg check, etc.",
        "k=3: Four equations - all are one-1n-primitive + one-2n-op: Boltzmann entropy (ln+mul), log return (div+ln), Boltzmann factor kT-const (div+DEML), herd immunity (recip+sub).",
        "k=4: Twelve equations - all two-op 2n patterns across 5 domains: Carnot (div+sub), Gibbs free energy (mul+sub), Hookes law (mul+neg), Beer-Lambert absorbance (mul+mul), Sharpe ratio (sub+div), Bayes (mul+div).",
        "k=5: Ten equations - the universal exponential decay class. mul+DEML+mul pattern for Beer-Lambert transmittance, radioactive decay, RC discharge, Malthusian growth. Also: pH (ln+div+neg), centripetal acceleration (pow+div), allometric scaling (pow+mul).",
        "Costs 1 through 14 are continuously covered by natural equations with no gaps.",
        "k=15 is the first catalog gap. k=17 is the second. Both are easily constructible via induction.",
        "k=16, 18, 19, 20 all have natural representatives: Lotka-Volterra (16n), ELO (16n), CES/equilibrium constant (18n), Black-Scholes d1 (19n), SIR/Theta (20n).",
        "Most expensive standalone natural equation: Black-Scholes Put Price at 54n.",
        "Inductive density proof is airtight: exp costs exactly 1n, so the gap from k-1 to k is always bridgeable."
    ],
    "catalog_cost_ranges": {
        "minimum_natural": 1,
        "maximum_natural": 54,
        "naturally_covered_1_to_20": sorted([k for k in range(1, 21) if k in covered]),
        "catalog_gaps_1_to_20": [k for k in range(1, 21) if k not in covered],
        "total_distinct_costs_in_catalog": len(covered),
        "total_distinct_costs_covered": len(covered)
    }
}

output_path = "D:/monogate/python/results/x1_cost_spectrum.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Written to:", output_path)
print("Gaps 1-20:", [k for k in range(1, 21) if k not in covered])
print("Covered:", sorted(covered))
print("Histogram:", json.dumps(sorted_hist, indent=2))
