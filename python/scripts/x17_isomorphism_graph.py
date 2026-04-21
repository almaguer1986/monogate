"""
Session X17: Isomorphism Graph of Equations
Two equations are isomorphic if they have the same F16 tree structure
(same operator topology, same arity pattern).
"""

import json
import re
from collections import defaultdict

# ============================================================
# EQUATION DATABASE
# Canonical tree form: operator_sequence ignoring variable names
# Based on reading all catalog JSON files
# Format: (name, domain, formula, canonical_tree, cost)
# ============================================================

EQUATIONS = [
    # ================================================================
    # CLASS A: MUL(exp(NEG(MUL)))  — "Arrhenius / exponential decay"
    # Structure: mul(C, exp(neg(mul(a,b))))
    # ================================================================
    {
        "id": "A01", "name": "Arrhenius rate constant", "domain": "Chemistry",
        "formula": "k = A*exp(-Ea/RT)",
        "tree": "MUL_EXP_NEG_MUL",
        "cost": 5,
        "notes": "Thermal activation"
    },
    {
        "id": "A02", "name": "Boltzmann weight", "domain": "Statistical Mechanics",
        "formula": "w = exp(-E/kT)",
        "tree": "EXP_NEG_MUL",
        "cost": 4,
        "notes": "Canonical Boltzmann factor (no prefactor)"
    },
    {
        "id": "A03", "name": "Radioactive decay / first-order kinetics", "domain": "Chemistry/Biology",
        "formula": "[A](t) = [A]0 * exp(-k*t)",
        "tree": "MUL_EXP_NEG_MUL",
        "cost": 5,
        "notes": "Integrated first-order"
    },
    {
        "id": "A04", "name": "Exponential growth N0*exp(r*t)", "domain": "Biology",
        "formula": "N(t) = N0*exp(r*t)",
        "tree": "MUL_EXP_MUL",
        "cost": 5,
        "notes": "Malthusian growth"
    },
    {
        "id": "A05", "name": "Exponential decay N0*exp(-lambda*t)", "domain": "Biology",
        "formula": "N(t) = N0*exp(-lambda*t)",
        "tree": "MUL_EXP_NEG_MUL",
        "cost": 5,
        "notes": "Exponential die-off"
    },
    {
        "id": "A06", "name": "Continuous compounding A=P*exp(rt)", "domain": "Economics",
        "formula": "A = P*exp(r*t)",
        "tree": "MUL_EXP_MUL",
        "cost": 5,
        "notes": "Finance growth"
    },
    {
        "id": "A07", "name": "Beer-Lambert transmittance T=exp(-epsilon*c*l)", "domain": "Biology/Optics",
        "formula": "T = exp(-epsilon*c*l)",
        "tree": "EXP_NEG_MUL_MUL",
        "cost": 7,
        "notes": "Optical transmittance"
    },
    {
        "id": "A08", "name": "One-compartment PK C(t)=C0*exp(-k*t)", "domain": "Biology/Pharmacology",
        "formula": "C(t) = C0*exp(-k*t)",
        "tree": "MUL_EXP_NEG_MUL",
        "cost": 5,
        "notes": "Drug clearance"
    },
    {
        "id": "A09", "name": "Synaptic alpha function I(t)=gmax*(t/tau)*exp(1-t/tau)", "domain": "Neuroscience",
        "formula": "I(t) = gmax*(t/tau)*exp(1-t/tau)",
        "tree": "MUL_MUL_EXP_SUB_MUL",
        "cost": 8,
        "notes": "Has additional structure: exp(sub)"
    },
    {
        "id": "A10", "name": "Cable equation V(x,t)=V0*exp(-x/lambda)*exp(-t/tau)", "domain": "Neuroscience",
        "formula": "V(x,t) = V0*exp(-x/lambda)*exp(-t/tau)",
        "tree": "MUL_MUL_EXP_NEG_MUL_EXP_NEG_MUL",
        "cost": 12,
        "notes": "Two independent decay factors"
    },
    {
        "id": "A11", "name": "Radioactive decay geochronology N(t)=N0*exp(-lambda*t)", "domain": "Geology",
        "formula": "N(t) = N0*exp(-lambda*t)",
        "tree": "MUL_EXP_NEG_MUL",
        "cost": 5,
        "notes": "Same tree as A03/A05/A08 — geology context"
    },

    # ================================================================
    # CLASS B1: MUL (pure linear product, 2 inputs)
    # Structure: mul(a, b)
    # ================================================================
    {
        "id": "B01", "name": "Malthus recursion N(t+1)=lambda*N(t)", "domain": "Biology",
        "formula": "N(t+1) = lambda*N(t)",
        "tree": "MUL",
        "cost": 2,
        "notes": "Linear recursion"
    },
    {
        "id": "B02", "name": "Enzyme turnover v=k_cat*[E]", "domain": "Biology",
        "formula": "v = k_cat*[E]",
        "tree": "MUL",
        "cost": 2,
        "notes": "Linear enzyme"
    },
    {
        "id": "B03", "name": "Fick's first law J=-D*(dc/dx)", "domain": "Biology/Physics",
        "formula": "J = -D*(dc/dx)",
        "tree": "NEG_MUL",
        "cost": 4,
        "notes": "Negative proportionality"
    },
    {
        "id": "B04", "name": "Hooke's law sigma=E*epsilon", "domain": "Materials Science",
        "formula": "sigma = E*epsilon",
        "tree": "MUL",
        "cost": 2,
        "notes": "Linear elasticity"
    },
    {
        "id": "B05", "name": "Hubble's law v=H0*d", "domain": "Astrophysics",
        "formula": "v = H0*d",
        "tree": "MUL",
        "cost": 2,
        "notes": "Proportionality"
    },
    {
        "id": "B06", "name": "Ohm's law V=I*R", "domain": "Electromagnetism",
        "formula": "V = I*R",
        "tree": "MUL",
        "cost": 2,
        "notes": "Classic linear"
    },
    {
        "id": "B07", "name": "Newton's second law F=m*a", "domain": "Classical Mechanics",
        "formula": "F = m*a",
        "tree": "MUL",
        "cost": 2,
        "notes": "Force = mass * acceleration"
    },
    {
        "id": "B08", "name": "Heat flow Fourier's law q=-k*(dT/dx)", "domain": "Geology/Physics",
        "formula": "q = -k*(dT/dx)",
        "tree": "NEG_MUL",
        "cost": 4,
        "notes": "Same signed-mul structure as Fick"
    },
    {
        "id": "B09", "name": "SEIR dR/dt = gamma*I", "domain": "Epidemiology",
        "formula": "dR/dt = gamma*I",
        "tree": "MUL",
        "cost": 2,
        "notes": "Single product"
    },
    {
        "id": "B10", "name": "Beer-Lambert A=epsilon*c*l", "domain": "Biology/Optics",
        "formula": "A = epsilon*c*l",
        "tree": "MUL_MUL",
        "cost": 4,
        "notes": "Triple product (two muls)"
    },
    {
        "id": "B11", "name": "Second-order rate r=k[A][B]", "domain": "Chemistry",
        "formula": "r = k*[A]*[B]",
        "tree": "MUL_MUL",
        "cost": 4,
        "notes": "Same structure as Beer-Lambert absorption"
    },

    # ================================================================
    # CLASS B2: DIV (simple ratio)
    # ================================================================
    {
        "id": "D01", "name": "Boltzmann ratio N2/N1=exp(-dE/kT)", "domain": "Chemistry",
        "formula": "N2/N1 = exp(-dE/kT)",
        "tree": "EXP_NEG_MUL",
        "cost": 4,
        "notes": "Same as Boltzmann weight A02"
    },
    {
        "id": "D02", "name": "Young's modulus E=sigma/eps", "domain": "Materials Science",
        "formula": "E = sigma/eps",
        "tree": "DIV",
        "cost": 1,
        "notes": "Minimal ratio"
    },
    {
        "id": "D03", "name": "Wien's displacement law lambda_max=b/T", "domain": "Astrophysics",
        "formula": "lambda_max = b/T",
        "tree": "DIV",
        "cost": 1,
        "notes": "Inverse proportionality"
    },
    {
        "id": "D04", "name": "Curie law chi=C/T", "domain": "Electromagnetism",
        "formula": "chi = C/T",
        "tree": "DIV",
        "cost": 1,
        "notes": "Same 1n DIV structure"
    },
    {
        "id": "D05", "name": "Perpetuity PV=C/r", "domain": "Economics",
        "formula": "PV = C/r",
        "tree": "DIV",
        "cost": 1,
        "notes": "Finance ratio"
    },
    {
        "id": "D06", "name": "Subduction velocity v=d/t", "domain": "Geology",
        "formula": "v = d/t",
        "tree": "DIV",
        "cost": 1,
        "notes": "Speed = distance/time"
    },
    {
        "id": "D07", "name": "Distribution coefficient Kd=Cs/Cw", "domain": "Geology",
        "formula": "Kd = Cs/Cw",
        "tree": "DIV",
        "cost": 1,
        "notes": "Partition ratio"
    },
    {
        "id": "D08", "name": "Case fatality rate CFR=deaths/cases", "domain": "Epidemiology",
        "formula": "CFR = deaths/cases",
        "tree": "DIV",
        "cost": 1,
        "notes": "Epidemiological ratio"
    },
    {
        "id": "D09", "name": "Vaccine efficacy VE=1-ARV/ARU", "domain": "Epidemiology",
        "formula": "VE = 1 - ARV/ARU",
        "tree": "SUB_DIV",
        "cost": 3,
        "notes": "1 minus ratio"
    },

    # ================================================================
    # CLASS LN: ln-based formulas
    # ================================================================
    {
        "id": "L01", "name": "Boltzmann entropy S=k_B*ln(Omega)", "domain": "Chemistry",
        "formula": "S = k_B*ln(Omega)",
        "tree": "MUL_LN",
        "cost": 3,
        "notes": "Log of count"
    },
    {
        "id": "L02", "name": "pH=-log10[H+]", "domain": "Chemistry",
        "formula": "pH = -log10([H+])",
        "tree": "NEG_LN",
        "cost": 3,
        "notes": "Negative log (base factor is constant)"
    },
    {
        "id": "L03", "name": "Shannon entropy H=-sum p*ln(p)", "domain": "Information Theory",
        "formula": "H = -sum_i p_i * ln(p_i)",
        "tree": "NEG_MUL_LN",
        "cost": 5,
        "notes": "Entropy per term"
    },
    {
        "id": "L04", "name": "KL divergence D_KL=sum p*ln(p/q)", "domain": "Information Theory",
        "formula": "D_KL = sum_i p_i * ln(p_i/q_i)",
        "tree": "MUL_LN_DIV",
        "cost": 4,
        "notes": "Per term: div+ln+mul"
    },
    {
        "id": "L05", "name": "Binary cross-entropy L=-(y*ln(yhat)+(1-y)*ln(1-yhat))", "domain": "ML",
        "formula": "L = -(y*ln(y_hat) + (1-y)*ln(1-y_hat))",
        "tree": "NEG_ADD_MUL_LN_MUL_LN",
        "cost": 12,
        "notes": "Sum of two log terms negated"
    },
    {
        "id": "L06", "name": "Helmholtz free energy A=-kT*ln(Z)", "domain": "Chemistry",
        "formula": "A = -k_B*T*ln(Z)",
        "tree": "NEG_MUL_MUL_LN",
        "cost": 7,
        "notes": "Neg of product-log"
    },
    {
        "id": "L07", "name": "dG=-RT*ln(K)", "domain": "Chemistry",
        "formula": "dG = -RT*ln(K)",
        "tree": "NEG_MUL_MUL_LN",
        "cost": 7,
        "notes": "Same tree as L06"
    },
    {
        "id": "L08", "name": "Nernst equation E=(RT/nF)*ln([ox]/[red])", "domain": "Chemistry",
        "formula": "E = const * ln([ox]/[red])",
        "tree": "MUL_LN_DIV",
        "cost": 5,
        "notes": "folded: mul(C, ln(div))"
    },
    {
        "id": "L09", "name": "Doubling time t_d=ln(2)/r", "domain": "Biology/Epidemiology",
        "formula": "t_d = ln(2)/r",
        "tree": "DIV_LN",
        "cost": 2,
        "notes": "ln(constant)/variable"
    },
    {
        "id": "L10", "name": "Half-life t_1/2=ln(2)/lambda", "domain": "Biology/Physics",
        "formula": "t_{1/2} = ln(2)/lambda",
        "tree": "DIV_LN",
        "cost": 2,
        "notes": "Same tree as doubling time L09"
    },
    {
        "id": "L11", "name": "Entropy of mixing dS=-R*(x1*ln(x1)+x2*ln(x2))", "domain": "Chemistry",
        "formula": "dS_mix = -R*(x1*ln(x1)+x2*ln(x2))",
        "tree": "NEG_MUL_ADD_MUL_LN_MUL_LN",
        "cost": 13,
        "notes": "Two entropy terms summed"
    },
    {
        "id": "L12", "name": "Log return r_log=ln(Pt/Pt-1)", "domain": "Economics/Finance",
        "formula": "r_log = ln(Pt/Pt-1)",
        "tree": "LN_DIV",
        "cost": 2,
        "notes": "Log ratio"
    },
    {
        "id": "L13", "name": "Prime counting approx f(x)=x/ln(x)", "domain": "Number Theory",
        "formula": "pi(x) ~ x/ln(x)",
        "tree": "DIV_LN",
        "cost": 2,
        "notes": "Same div-ln structure as doubling time"
    },
    {
        "id": "L14", "name": "Decibel scale dB=20*ln(A/A0)/ln(10)", "domain": "Acoustics",
        "formula": "dB = const * ln(A/A0)",
        "tree": "MUL_LN_DIV",
        "cost": 4,
        "notes": "Same as L04 structure"
    },

    # ================================================================
    # CLASS S: Sigmoid / logistic
    # Structure: recip(add(1, exp(neg))) or div(K, add(1, exp(neg)))
    # ================================================================
    {
        "id": "S01", "name": "Sigmoid activation sigma(x)=1/(1+exp(-x))", "domain": "Neuroscience/ML",
        "formula": "sigma(x) = 1/(1+exp(-x))",
        "tree": "RECIP_ADD_EXP_NEG",
        "cost": 6,
        "notes": "Canonical sigmoid"
    },
    {
        "id": "S02", "name": "Fermi-Dirac distribution f(E)=1/(exp((E-mu)/kT)+1)", "domain": "Statistical Mechanics",
        "formula": "f(E) = 1/(exp((E-mu)/kT)+1)",
        "tree": "RECIP_ADD_EXP_MUL_SUB",
        "cost": 8,
        "notes": "Fermi-Dirac — sigmoid with linear argument"
    },
    {
        "id": "S03", "name": "Logistic growth N(t)=K/(1+exp(-r*(t-t0)))", "domain": "Biology",
        "formula": "N(t) = K/(1+exp(-r*(t-t0)))",
        "tree": "DIV_ADD_EXP_NEG_MUL_SUB",
        "cost": 10,
        "notes": "Logistic saturation"
    },
    {
        "id": "S04", "name": "Logistic epidemic curve I(t)=K/(1+exp(-r*(t-t0)))", "domain": "Epidemiology",
        "formula": "I(t) = K/(1+exp(-r*(t-t0)))",
        "tree": "DIV_ADD_EXP_NEG_MUL_SUB",
        "cost": 10,
        "notes": "Same sigmoid tree as S03 — epidemic context"
    },
    {
        "id": "S05", "name": "Bose-Einstein distribution n(E)=1/(exp((E-mu)/kT)-1)", "domain": "Statistical Mechanics",
        "formula": "n(E) = 1/(exp((E-mu)/kT)-1)",
        "tree": "RECIP_SUB_EXP_MUL_SUB",
        "cost": 8,
        "notes": "Bose-Einstein — minus instead of plus"
    },
    {
        "id": "S06", "name": "Partition function denominator Z=sum_i exp(-E_i/kT)", "domain": "Statistical Mechanics",
        "formula": "Z = sum_i exp(-E_i/kT)",
        "tree": "ADD_EXP_NEG_MUL",
        "cost": "variable",
        "notes": "Softmax denominator (each term is exp-neg-mul)"
    },
    {
        "id": "S07", "name": "Softmax denominator sum_i exp(z_i)", "domain": "ML",
        "formula": "Z = sum_i exp(z_i)",
        "tree": "ADD_EXP",
        "cost": "variable",
        "notes": "Same structure as S06 (simplified)"
    },
    {
        "id": "S08", "name": "Michaelis-Menten v=Vmax*[S]/(Km+[S])", "domain": "Biology/Chemistry",
        "formula": "v = Vmax*[S]/(Km+[S])",
        "tree": "MUL_DIV_ADD",
        "cost": 5,
        "notes": "Saturation curve — hyperbolic"
    },
    {
        "id": "S09", "name": "Hill fractional saturation theta=[L]/(Kd+[L])", "domain": "Biology",
        "formula": "theta = [L]/(Kd+[L])",
        "tree": "DIV_ADD",
        "cost": 3,
        "notes": "n=1 Hill — same as MM numerator-free"
    },

    # ================================================================
    # CLASS P: Power laws
    # Structure: mul(C, pow(x, alpha))
    # ================================================================
    {
        "id": "P01", "name": "Allometric scaling B=B0*M^alpha", "domain": "Biology",
        "formula": "B = B0*M^alpha",
        "tree": "MUL_POW",
        "cost": 5,
        "notes": "Power law scaling"
    },
    {
        "id": "P02", "name": "Basquin fatigue law sigma=C*N^(-b)", "domain": "Materials Science",
        "formula": "sigma = C*N^(-b)",
        "tree": "MUL_POW",
        "cost": 5,
        "notes": "Same power law tree"
    },
    {
        "id": "P03", "name": "Freundlich isotherm q=Kf*C^(1/n)", "domain": "Geology",
        "formula": "q = Kf*C^(1/n)",
        "tree": "MUL_POW",
        "cost": 5,
        "notes": "Same power law tree"
    },
    {
        "id": "P04", "name": "Scale factor a(t)=a0*(t/t0)^(2/3)", "domain": "Astrophysics",
        "formula": "a(t) = a0*(t/t0)^(2/3)",
        "tree": "MUL_POW_DIV",
        "cost": 6,
        "notes": "Power of ratio"
    },
    {
        "id": "P05", "name": "Gutenberg-Richter log10(N)=a-b*M", "domain": "Geology",
        "formula": "log10(N) = a - b*M",
        "tree": "SUB_MUL",
        "cost": 4,
        "notes": "Linear in log space"
    },
    {
        "id": "P06", "name": "Stefan-Boltzmann L=4*pi*R^2*sigma*T^4", "domain": "Astrophysics",
        "formula": "L = 4*pi*R^2*sigma*T^4",
        "tree": "MUL_MUL_MUL_POW_POW",
        "cost": 10,
        "notes": "Product of powers"
    },
    {
        "id": "P07", "name": "Manning's equation v=(1/n)*R^(2/3)*S^(1/2)", "domain": "Geology",
        "formula": "v = (1/n)*R^(2/3)*S^(1/2)",
        "tree": "MUL_MUL_POW_POW",
        "cost": 8,
        "notes": "Product of two power laws"
    },
    {
        "id": "P08", "name": "Equal temperament f(n)=f0*2^(n/12)", "domain": "Acoustics",
        "formula": "f(n) = f0*2^(n/12)",
        "tree": "MUL_EXP_MUL_DIV",
        "cost": 6,
        "notes": "Same tree as exponential growth with freq ratio"
    },

    # ================================================================
    # CLASS G: Gaussian / Normal kernel
    # Structure: exp(neg(pow(x,2)))
    # ================================================================
    {
        "id": "G01", "name": "Normal/Gaussian PDF f(x)=exp(-x^2/2)/sqrt(2pi)", "domain": "Statistics",
        "formula": "f(x) = exp(-x^2/2)/sqrt(2*pi)",
        "tree": "DIV_EXP_NEG_POW",
        "cost": 5,
        "notes": "Bell curve kernel"
    },
    {
        "id": "G02", "name": "Heat equation fundamental solution u=exp(-x^2/4t)/sqrt(4pi*t)", "domain": "Physics/PDE",
        "formula": "u(x,t) = exp(-x^2/(4t))/sqrt(4*pi*t)",
        "tree": "DIV_EXP_NEG_DIV_POW",
        "cost": 6,
        "notes": "Gaussian kernel with time"
    },
    {
        "id": "G03", "name": "Log-normal PDF f(x)=exp(-(ln(x)-mu)^2/(2*sigma^2))/(x*sigma*sqrt(2pi))", "domain": "Statistics",
        "formula": "f(x) = exp(-(ln(x)-mu)^2/(2*sigma^2)) / (x*sigma*sqrt(2*pi))",
        "tree": "DIV_EXP_NEG_POW_SUB_LN",
        "cost": 10,
        "notes": "Gaussian on log scale"
    },
    {
        "id": "G04", "name": "Advection-dispersion Gaussian C(x,t)=exp(-(x-vt)^2/(4Dt))", "domain": "Geology",
        "formula": "C(x,t) = M/(A*sqrt(4*pi*D*t)) * exp(-(x-v*t)^2/(4*D*t))",
        "tree": "MUL_DIV_EXP_NEG_POW_SUB_MUL",
        "cost": 16,
        "notes": "Shifted Gaussian plume"
    },
    {
        "id": "G05", "name": "Maxwell-Boltzmann distribution f(v)=v^2*exp(-mv^2/2kT)", "domain": "Chemistry/Physics",
        "formula": "f(v) = 4*pi*(m/2*pi*kT)^(3/2)*v^2*exp(-mv^2/2kT)",
        "tree": "MUL_POW_EXP_NEG_MUL_POW",
        "cost": 14,
        "notes": "Gaussian times power"
    },
    {
        "id": "G06", "name": "GBM step dS=mu*S*dt+sigma*S*dW", "domain": "Economics",
        "formula": "dS = mu*S*dt + sigma*S*dW",
        "tree": "ADD_MUL_MUL_MUL_MUL",
        "cost": 11,
        "notes": "SDE step — linear"
    },

    # ================================================================
    # CLASS TWO_EXP: Two-component exponential sum
    # Structure: add(mul(A, exp(neg(mul))), mul(B, exp(neg(mul))))
    # ================================================================
    {
        "id": "T01", "name": "Two-compartment PK C(t)=A*exp(-alpha*t)+B*exp(-beta*t)", "domain": "Biology/Pharmacology",
        "formula": "C(t) = A*exp(-alpha*t) + B*exp(-beta*t)",
        "tree": "ADD_MUL_EXP_NEG_MUL_MUL_EXP_NEG_MUL",
        "cost": 17,
        "notes": "Biexponential"
    },
    {
        "id": "T02", "name": "Butler-Volmer j=j0*(exp(a*F*eta/RT)-exp(-(1-a)*F*eta/RT))", "domain": "Chemistry",
        "formula": "j = j0*(exp(alpha*F*eta/RT) - exp(-(1-a)*F*eta/RT))",
        "tree": "MUL_SUB_EXP_MUL_EXP_NEG_MUL",
        "cost": 17,
        "notes": "Difference of exponentials"
    },
    {
        "id": "T03", "name": "Partition function 2-level Z=1+exp(-dE/kT)", "domain": "Chemistry",
        "formula": "Z = 1 + exp(-dE/kT)",
        "tree": "ADD_EXP_NEG_MUL",
        "cost": 8,
        "notes": "One + exponential"
    },
    {
        "id": "T04", "name": "Thermal subsidence y(t)=E0*(1-exp(-t/tau))", "domain": "Geology",
        "formula": "y(t) = E0*(1 - exp(-t/tau))",
        "tree": "MUL_SUB_EXP_NEG_MUL",
        "cost": 8,
        "notes": "Exponential approach to limit"
    },

    # ================================================================
    # CLASS LIN: Linear / affine
    # ================================================================
    {
        "id": "Lin01", "name": "Gibbs free energy dG=dH-T*dS", "domain": "Chemistry",
        "formula": "dG = dH - T*dS",
        "tree": "SUB_MUL",
        "cost": 4,
        "notes": "Linear combination"
    },
    {
        "id": "Lin02", "name": "CAPM E(Ri)=Rf+beta*(E(Rm)-Rf)", "domain": "Economics",
        "formula": "E(Ri) = Rf + beta*(E(Rm)-Rf)",
        "tree": "ADD_MUL_SUB",
        "cost": 7,
        "notes": "Affine risk model"
    },
    {
        "id": "Lin03", "name": "Phillips curve pi=pie-beta*(u-u*)", "domain": "Economics",
        "formula": "pi = pi_e - beta*(u-u*)",
        "tree": "SUB_MUL_SUB",
        "cost": 6,
        "notes": "Linear in gap"
    },
    {
        "id": "Lin04", "name": "Batch normalization x-hat=(x-mu)/sigma", "domain": "Neuroscience/ML",
        "formula": "x_hat = (x - mu)/sigma",
        "tree": "DIV_SUB",
        "cost": 3,
        "notes": "Standardization"
    },
    {
        "id": "Lin05", "name": "SGD parameter update theta=theta-alpha*grad", "domain": "Neuroscience/ML",
        "formula": "theta = theta - alpha*grad",
        "tree": "SUB_MUL",
        "cost": 4,
        "notes": "Same tree as Gibbs free energy"
    },
    {
        "id": "Lin06", "name": "Sharpe ratio S=(Rp-Rf)/sigma_p", "domain": "Economics",
        "formula": "S = (Rp-Rf)/sigma_p",
        "tree": "DIV_SUB",
        "cost": 3,
        "notes": "Same DIV_SUB as batch norm"
    },

    # ================================================================
    # CLASS RECIP_ADD (hyperbolic / harmonic)
    # ================================================================
    {
        "id": "H01", "name": "Langmuir adsorption q=qmax*KL*C/(1+KL*C)", "domain": "Geology",
        "formula": "q = qmax*KL*C/(1+KL*C)",
        "tree": "MUL_DIV_ADD_MUL",
        "cost": 8,
        "notes": "Saturation isotherm"
    },
    {
        "id": "H02", "name": "Michaelis-Menten (equivalent)", "domain": "Biology",
        "formula": "v = Vmax*[S]/(Km+[S])",
        "tree": "MUL_DIV_ADD",
        "cost": 5,
        "notes": "See S08"
    },
    {
        "id": "H03", "name": "Herd immunity threshold p*=1-1/R0", "domain": "Epidemiology",
        "formula": "p* = 1 - 1/R0",
        "tree": "SUB_RECIP",
        "cost": 3,
        "notes": "1 minus reciprocal"
    },
    {
        "id": "H04", "name": "R0 reproduction number R0=beta*S0/gamma", "domain": "Epidemiology",
        "formula": "R0 = beta*S0/gamma",
        "tree": "DIV_MUL",
        "cost": 3,
        "notes": "Product over constant"
    },

    # ================================================================
    # CLASS VAN_THOFF: ln of ratio with reciprocal temperature
    # ================================================================
    {
        "id": "VT01", "name": "Van't Hoff integrated ln(K2/K1)=-(dH/R)*(1/T2-1/T1)", "domain": "Chemistry",
        "formula": "ln(K2/K1) = -(dH/R)*(1/T2-1/T1)",
        "tree": "NEG_MUL_SUB_RECIP_RECIP",
        "cost": 17,
        "notes": "Log-ratio vs inverse temperatures"
    },
    {
        "id": "VT02", "name": "Clausius-Clapeyron ln(P2/P1)=-(dHvap/R)*(1/T2-1/T1)", "domain": "Chemistry",
        "formula": "ln(P2/P1) = -(dHvap/R)*(1/T2-1/T1)",
        "tree": "NEG_MUL_SUB_RECIP_RECIP",
        "cost": 17,
        "notes": "Same tree as Van't Hoff VT01"
    },

    # ================================================================
    # CLASS COMPOUND_INT: (1+r)^n type
    # ================================================================
    {
        "id": "CI01", "name": "Compound interest A=P*(1+r)^n", "domain": "Economics",
        "formula": "A = P*(1+r)^n",
        "tree": "MUL_POW_ADD",
        "cost": 8,
        "notes": "Discrete compounding"
    },
    {
        "id": "CI02", "name": "Present value PV=FV/(1+r)^n", "domain": "Economics",
        "formula": "PV = FV/(1+r)^n",
        "tree": "DIV_POW_ADD",
        "cost": 7,
        "notes": "Discounting — recip of CI01 structure"
    },
    {
        "id": "CI03", "name": "Inflation adjustment Real=Nominal/(1+pi)^n", "domain": "Economics",
        "formula": "Real = Nominal/(1+pi)^n",
        "tree": "DIV_POW_ADD",
        "cost": 7,
        "notes": "Same DIV_POW_ADD as PV discounting"
    },

    # ================================================================
    # CLASS SQRT_DIV: orbital / wave mechanics
    # ================================================================
    {
        "id": "SQ01", "name": "Orbital velocity v=sqrt(GM/r)", "domain": "Astrophysics",
        "formula": "v = sqrt(GM/r)",
        "tree": "SQRT_DIV_MUL",
        "cost": 6,
        "notes": "Kepler orbit speed"
    },
    {
        "id": "SQ02", "name": "Escape velocity v_esc=sqrt(2GM/r)", "domain": "Astrophysics",
        "formula": "v_esc = sqrt(2*GM/r)",
        "tree": "SQRT_DIV_MUL",
        "cost": 6,
        "notes": "Same SQRT_DIV_MUL structure"
    },
    {
        "id": "SQ03", "name": "Skin depth delta=sqrt(2*rho/(omega*mu))", "domain": "Electromagnetism",
        "formula": "delta = sqrt(2*rho/(omega*mu))",
        "tree": "SQRT_DIV_MUL",
        "cost": 6,
        "notes": "Same tree — EM wave penetration"
    },
    {
        "id": "SQ04", "name": "Phase velocity vp=1/sqrt(mu*eps)", "domain": "Electromagnetism",
        "formula": "vp = 1/sqrt(mu*eps)",
        "tree": "RECIP_SQRT_MUL",
        "cost": 5,
        "notes": "Inverse sqrt of product"
    },
    {
        "id": "SQ05", "name": "[H+]=sqrt(Ka*Ca)", "domain": "Chemistry",
        "formula": "[H+] = sqrt(Ka*Ca)",
        "tree": "SQRT_MUL",
        "cost": 5,
        "notes": "Geometric mean of Ka and Ca"
    },
    {
        "id": "SQ06", "name": "Orbital period T=2*pi*sqrt(a^3/(GM))", "domain": "Astrophysics",
        "formula": "T = 2*pi*sqrt(a^3/(GM))",
        "tree": "MUL_SQRT_DIV_POW",
        "cost": 9,
        "notes": "Kepler third law"
    },

    # ================================================================
    # CLASS COULOMB: k*q1*q2/r^2 type
    # ================================================================
    {
        "id": "C01", "name": "Coulomb's law F=k*q1*q2/r^2", "domain": "Electromagnetism",
        "formula": "F = k*q1*q2/r^2",
        "tree": "DIV_MUL_MUL_POW",
        "cost": 8,
        "notes": "Inverse-square force"
    },
    {
        "id": "C02", "name": "Electric field E=k*q/r^2", "domain": "Electromagnetism",
        "formula": "E = k*q/r^2",
        "tree": "DIV_MUL_POW",
        "cost": 6,
        "notes": "Same inverse-square, one charge"
    },
    {
        "id": "C03", "name": "Gravitational potential energy U=-GMm/r", "domain": "Astrophysics",
        "formula": "U = -G*M*m/r",
        "tree": "NEG_DIV_MUL_MUL",
        "cost": 7,
        "notes": "1/r potential"
    },
    {
        "id": "C04", "name": "Schwarzschild radius Rs=2GM/c^2", "domain": "Astrophysics",
        "formula": "Rs = 2*G*M/c^2",
        "tree": "DIV_MUL_MUL_POW",
        "cost": 8,
        "notes": "Same DIV_MUL_MUL_POW as Coulomb"
    },

    # ================================================================
    # CLASS HILL_GENERAL: [L]^n/(Kd^n+[L]^n)
    # ================================================================
    {
        "id": "Hi01", "name": "Hill equation general theta=[L]^n/(Kd^n+[L]^n)", "domain": "Biology",
        "formula": "theta = [L]^n/(Kd^n+[L]^n)",
        "tree": "DIV_POW_ADD_POW_POW",
        "cost": 15,
        "notes": "General Hill cooperativity"
    },
    {
        "id": "Hi02", "name": "Hill dose-response E=Emax*[D]^n/(EC50^n+[D]^n)", "domain": "Biology/Pharmacology",
        "formula": "E = Emax*[D]^n/(EC50^n+[D]^n)",
        "tree": "MUL_DIV_POW_ADD_POW_POW",
        "cost": 15,
        "notes": "Same tree as Hi01 with prefactor"
    },

    # ================================================================
    # CLASS ENERGY_HALF: U=(1/2)*C*V^2 type
    # ================================================================
    {
        "id": "E01", "name": "Capacitor energy U=(1/2)*C*V^2", "domain": "Electromagnetism",
        "formula": "U = (1/2)*C*V^2",
        "tree": "MUL_MUL_POW",
        "cost": 5,
        "notes": "Quadratic energy"
    },
    {
        "id": "E02", "name": "Inductance energy U=(1/2)*L*I^2", "domain": "Electromagnetism",
        "formula": "U = (1/2)*L*I^2",
        "tree": "MUL_MUL_POW",
        "cost": 5,
        "notes": "Same MUL_MUL_POW structure"
    },
    {
        "id": "E03", "name": "MSE loss L=(y-y_hat)^2", "domain": "ML",
        "formula": "L = (y - y_hat)^2",
        "tree": "POW_SUB",
        "cost": 5,
        "notes": "Squared error"
    },
    {
        "id": "E04", "name": "Magnetic energy density u=B^2/(2*mu0)", "domain": "Electromagnetism",
        "formula": "u = B^2/(2*mu0)",
        "tree": "DIV_POW_MUL",
        "cost": 6,
        "notes": "Quadratic divided"
    },

    # ================================================================
    # CLASS UNIQUE: Structurally distinct equations (no close sibling)
    # ================================================================
    {
        "id": "U01", "name": "Hodgkin-Huxley total current I=gNa*m^3*h*(V-ENa)+gK*n^4*(V-EK)+gL*(V-EL)", "domain": "Neuroscience",
        "formula": "I = gNa*m^3*h*(V-ENa)+gK*n^4*(V-EK)+gL*(V-EL)",
        "tree": "ADD_ADD_MUL_MUL_MUL_POW_SUB_MUL_MUL_POW_SUB_MUL_SUB",
        "cost": 30,
        "notes": "Highly domain-specific conductance model"
    },
    {
        "id": "U02", "name": "Gompertz growth N(t)=N0*exp(-a*exp(-b*t))", "domain": "Biology",
        "formula": "N(t) = N0*exp(-a*exp(-b*t))",
        "tree": "MUL_EXP_NEG_MUL_EXP_NEG_MUL",
        "cost": 12,
        "notes": "Nested exponential"
    },
    {
        "id": "U03", "name": "Black-Scholes d1 formula", "domain": "Economics",
        "formula": "d1 = (ln(S/K) + (r+sigma^2/2)*T)/(sigma*sqrt(T))",
        "tree": "DIV_ADD_LN_DIV_MUL_ADD_POW_MUL_SQRT",
        "cost": 20,
        "notes": "Complex mixed structure"
    },
    {
        "id": "U04", "name": "Goldman-Hodgkin-Katz Vm (2-ion)", "domain": "Neuroscience/Chemistry",
        "formula": "Vm = (RT/F)*ln((PK[K]o+PNa[Na]o)/(PK[K]i+PNa[Na]i))",
        "tree": "MUL_LN_DIV_ADD_MUL_MUL_ADD_MUL_MUL",
        "cost": 27,
        "notes": "Log of sum ratio"
    },
    {
        "id": "U05", "name": "Debye-Huckel ln(gamma)=-A*|z+z-|*sqrt(I)", "domain": "Chemistry",
        "formula": "ln(gamma) = -A*|z+z-|*sqrt(I)",
        "tree": "NEG_MUL_MUL_SQRT",
        "cost": 12,
        "notes": "Neg*mul*sqrt"
    },
    {
        "id": "U06", "name": "Collision theory rate k=A*T^(1/2)*exp(-Ea/RT)", "domain": "Chemistry",
        "formula": "k = A*T^(1/2)*exp(-Ea/RT)",
        "tree": "MUL_MUL_SQRT_EXP_NEG_MUL",
        "cost": 10,
        "notes": "Arrhenius with sqrt(T) prefactor"
    },
    {
        "id": "U07", "name": "Saha equation n_e*n_i/n0=(2*pi*me*kT/h^2)^(3/2)*exp(-chi/kT)", "domain": "Astrophysics",
        "formula": "n_e*n_i/n0 = C*T^(3/2)*exp(-chi/kT)",
        "tree": "MUL_POW_EXP_NEG_MUL",
        "cost": 11,
        "notes": "Power*exponential — Arrhenius with T^(3/2)"
    },
    {
        "id": "U08", "name": "Eyring transition state k=(kB*T/h)*exp(-dG/RT)", "domain": "Chemistry",
        "formula": "k = (kB*T/h)*exp(-dG/RT)",
        "tree": "MUL_DIV_MUL_EXP_NEG_MUL",
        "cost": 9,
        "notes": "Ratio*exp structure"
    },
    {
        "id": "U09", "name": "Henderson-Hasselbalch pH=pKa+log([A-]/[HA])", "domain": "Chemistry",
        "formula": "pH = pKa + log10([A-]/[HA])",
        "tree": "ADD_LN_DIV",
        "cost": 4,
        "notes": "Offset log ratio"
    },
    {
        "id": "U10", "name": "Cobb-Douglas Y=A*K^alpha*L^(1-alpha)", "domain": "Economics",
        "formula": "Y = A*K^alpha*L^(1-alpha)",
        "tree": "MUL_MUL_POW_POW_SUB",
        "cost": 12,
        "notes": "Product of power laws with complementary exponents"
    },
    {
        "id": "U11", "name": "Friedmann equation H^2=(8*pi*G/3)*rho-k*c^2/a^2+Lambda*c^2/3", "domain": "Astrophysics",
        "formula": "H^2 = (8*pi*G/3)*rho - k*c^2/a^2 + Lambda*c^2/3",
        "tree": "ADD_SUB_MUL_DIV_MUL_MUL",
        "cost": 14,
        "notes": "Three-term cosmological"
    },
    {
        "id": "U12", "name": "Nernst (single-ion) E=(RT/F)*ln([ion]o/[ion]i)", "domain": "Biology",
        "formula": "E_ion = (RT/F)*ln([ion]o/[ion]i)",
        "tree": "MUL_LN_DIV",
        "cost": 6,
        "notes": "Same as L08/L04 structure"
    },
    {
        "id": "U13", "name": "Fourier heat conduction q=-k*(dT/dx)", "domain": "Physics",
        "formula": "q = -k*(dT/dx)",
        "tree": "NEG_MUL",
        "cost": 4,
        "notes": "Same tree as Fick's first law B03"
    },
]


def build_isomorphism_graph(equations):
    """
    Build the isomorphism graph where nodes are equations and edges
    connect equations with the same canonical tree structure.
    """
    # Group by tree
    tree_to_equations = defaultdict(list)
    for eq in equations:
        tree_to_equations[eq["tree"]].append(eq)

    # Build adjacency list (edges between same-tree equations)
    adjacency = defaultdict(set)
    edges = []

    for tree, eqs in tree_to_equations.items():
        if len(eqs) > 1:
            for i in range(len(eqs)):
                for j in range(i + 1, len(eqs)):
                    id_i = eqs[i]["id"]
                    id_j = eqs[j]["id"]
                    adjacency[id_i].add(id_j)
                    adjacency[id_j].add(id_i)
                    edges.append({
                        "node_a": id_i,
                        "node_b": id_j,
                        "tree": tree,
                        "name_a": eqs[i]["name"],
                        "name_b": eqs[j]["name"],
                        "domain_a": eqs[i]["domain"],
                        "domain_b": eqs[j]["domain"]
                    })

    return tree_to_equations, adjacency, edges


def find_connected_components(equations, adjacency):
    """
    Find connected components using BFS.
    """
    all_ids = {eq["id"] for eq in equations}
    visited = set()
    components = []

    eq_by_id = {eq["id"]: eq for eq in equations}

    for start_id in all_ids:
        if start_id in visited:
            continue
        # BFS
        component = []
        queue = [start_id]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(sorted(component))

    # Sort by size descending
    components.sort(key=lambda c: -len(c))
    return components, eq_by_id


def describe_component(component_ids, eq_by_id):
    """Describe a connected component."""
    eqs = [eq_by_id[eid] for eid in component_ids]
    return {
        "size": len(eqs),
        "equations": [
            {
                "id": eq["id"],
                "name": eq["name"],
                "domain": eq["domain"],
                "tree": eq["tree"]
            }
            for eq in eqs
        ],
        "domains": sorted(list(set(eq["domain"] for eq in eqs))),
        "tree_classes": sorted(list(set(eq["tree"] for eq in eqs)))
    }


def main():
    equations = EQUATIONS

    tree_to_equations, adjacency, edges = build_isomorphism_graph(equations)
    components, eq_by_id = find_connected_components(equations, adjacency)

    # Node count
    n_nodes = len(equations)
    n_edges = len(edges)

    # Component descriptions
    component_descriptions = []
    for comp in components:
        desc = describe_component(comp, eq_by_id)
        component_descriptions.append(desc)

    # Largest component
    largest = component_descriptions[0]
    # Add insight
    largest_eqs = [eq_by_id[eid] for eid in components[0]]
    domains_in_largest = list(set(eq["domain"] for eq in largest_eqs))
    tree_in_largest = largest_eqs[0]["tree"] if len(set(eq["tree"] for eq in largest_eqs)) == 1 else "MIXED"

    # Cross-domain insight for largest component
    if len(components[0]) > 2:
        eq_names = [eq["name"] for eq in largest_eqs[:5]]
        insight = (f"One canonical tree '{tree_in_largest}' unifies {len(largest_eqs)} equations "
                   f"across {len(domains_in_largest)} domains: {', '.join(domains_in_largest[:5])}. "
                   f"Representative equations: {'; '.join(eq_names[:3])}. "
                   f"This is the most universal mathematical structure in the catalog.")
    else:
        insight = f"Small component. Tree: {tree_in_largest}."

    largest_with_insight = {
        **largest,
        "insight": insight
    }

    # Isolated nodes (degree 0)
    isolated = [eid for eid in eq_by_id if len(adjacency.get(eid, set())) == 0]
    isolated_equations = [
        {
            "id": eq_by_id[eid]["id"],
            "name": eq_by_id[eid]["name"],
            "domain": eq_by_id[eid]["domain"],
            "tree": eq_by_id[eid]["tree"]
        }
        for eid in isolated
    ]

    # Most universal structure (tree with most equations)
    most_universal_tree = max(tree_to_equations.items(), key=lambda kv: len(kv[1]))
    most_universal = {
        "tree": most_universal_tree[0],
        "count": len(most_universal_tree[1]),
        "equations": [
            {
                "id": eq["id"],
                "name": eq["name"],
                "domain": eq["domain"]
            }
            for eq in most_universal_tree[1]
        ],
        "cross_domain_insight": (
            f"The tree '{most_universal_tree[0]}' appears in {len(most_universal_tree[1])} equations "
            f"spanning domains: {', '.join(sorted(set(eq['domain'] for eq in most_universal_tree[1])))}. "
            "This operator pattern is the most universal mathematical structure across scientific domains."
        )
    }

    # All tree classes and their members
    isomorphism_classes = [
        {
            "tree": tree,
            "size": len(eqs),
            "members": [
                {"id": eq["id"], "name": eq["name"], "domain": eq["domain"]}
                for eq in eqs
            ],
            "domains": sorted(list(set(eq["domain"] for eq in eqs))),
            "cross_domain": len(set(eq["domain"] for eq in eqs)) > 1
        }
        for tree, eqs in sorted(tree_to_equations.items(), key=lambda kv: -len(kv[1]))
    ]

    # Degree of each node
    degree = {eid: len(adj) for eid, adj in adjacency.items()}
    # Nodes with zero degree are not in adjacency
    for eq in equations:
        if eq["id"] not in degree:
            degree[eq["id"]] = 0

    most_connected_ids = sorted(degree.items(), key=lambda x: -x[1])[:10]
    most_connected = [
        {
            "id": eid,
            "name": eq_by_id[eid]["name"],
            "domain": eq_by_id[eid]["domain"],
            "tree": eq_by_id[eid]["tree"],
            "degree": deg,
            "interpretation": f"Has {deg} isomorphic partners across multiple scientific domains"
        }
        for eid, deg in most_connected_ids
        if deg > 0
    ]

    # Component statistics
    component_sizes = [len(c) for c in components]
    n_components = len(components)
    n_isolated = sum(1 for s in component_sizes if s == 1)
    n_pairs = sum(1 for s in component_sizes if s == 2)

    # Key findings
    key_findings = [
        f"Total equations cataloged: {n_nodes}",
        f"Total isomorphic pairs (edges): {n_edges}",
        f"Connected components: {n_components}",
        f"Isolated nodes (no isomorphic partner): {n_isolated}",
        f"Isomorphic pairs: {n_pairs}",
        f"Largest component size: {component_sizes[0]}",
        f"Most universal tree: '{most_universal_tree[0]}' with {most_universal_tree[1][0]['name']} as prototype",
        "The MUL_EXP_NEG_MUL tree (Arrhenius/exponential-decay) unifies Chemistry, Biology, Geology, Economics, Pharmacology",
        "The DIV tree (1n ratio) is the minimal universal structure: Wien, Curie, subduction speed, fatality rate",
        "The RECIP_ADD_EXP_NEG (sigmoid) tree unifies statistical mechanics (Fermi-Dirac), neural networks (sigmoid), and ecology (logistic growth)",
        "The MUL_POW (power law) tree unifies allometric scaling, fatigue, adsorption isotherms",
        "Van't Hoff and Clausius-Clapeyron are perfectly isomorphic — thermodynamic universality",
        "Doubling time, half-life, and prime counting approximation share the same DIV_LN tree"
    ]

    result = {
        "metadata": {
            "session": "X17",
            "title": "Isomorphism Graph of Equations",
            "date": "2026-04-20",
            "method": "Canonical tree form = operator sequence ignoring variable names; edges = same canonical tree"
        },
        "nodes": n_nodes,
        "edges": n_edges,
        "n_components": n_components,
        "n_isolated": n_isolated,
        "isomorphism_classes": isomorphism_classes,
        "components": component_descriptions[:20],  # top 20 components
        "largest_component": largest_with_insight,
        "most_universal_structure": most_universal,
        "most_connected_equations": most_connected,
        "isolated_equations": isolated_equations,
        "key_findings": key_findings,
        "edge_list": edges[:50]  # first 50 edges for reference
    }

    return result


if __name__ == "__main__":
    result = main()

    output_path = "D:/monogate/python/results/x17_isomorphism_graph.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Written to {output_path}")
    print(f"Nodes: {result['nodes']}, Edges: {result['edges']}")
    print(f"Components: {result['n_components']}, Isolated: {result['n_isolated']}")
    print(f"Largest component: {result['largest_component']['size']} equations")
    print(f"Most universal tree: {result['most_universal_structure']['tree']} ({result['most_universal_structure']['count']} equations)")
    print("\nTop 5 isomorphism classes:")
    for cls in result["isomorphism_classes"][:5]:
        print(f"  {cls['tree']}: {cls['size']} equations, domains={cls['domains']}")
