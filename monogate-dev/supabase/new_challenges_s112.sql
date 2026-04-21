-- New challenges from Sessions S105-S112
-- Run in Supabase SQL editor
-- Date: April 2026

-- Challenge: Phantom Attractor Identity
INSERT INTO challenges (id, name, description, status, grammar, best_known_nodes, best_known_depth, best_submission_id)
VALUES (
  'phantom-attractor-identity',
  'Phantom Attractor Identity',
  'The EML training attractor alpha ~ 6.21444185... appears in 60%+ of depth-3 EML training runs targeting pi. Find a closed-form expression for alpha using only standard mathematical constants (e, pi, ln2, gamma, sqrt2, etc.) with integer coefficients. PSLQ has been run at 320-digit precision against 25 constants with no relation found (maxcoeff=100). Either find a relation (degree<=12, |coeff|<=1000) or prove none exists. Prize: first to resolve this open problem.',
  'OPEN',
  'closed-form',
  NULL,
  NULL,
  NULL
),
(
  'pi-half-eml-constructibility',
  'pi/2 Real EML Constructibility',
  'Is pi/2 in the real EML closure from {1}? The depth-6 real EML search finds a value within 9.75e-6 of pi/2. At depth 7+ this gap may close to zero (density conjecture) or remain positive forever. Construct a real EML tree from {1} evaluating to pi/2 within 1e-10, OR prove that no finite-depth real EML tree from {1} evaluates to pi/2 exactly. Resolving this is equivalent to proving/disproving that i is constructible from {1} via EML.',
  'OPEN',
  'eml-real',
  NULL,
  NULL,
  NULL
),
(
  'eml4-exact-separation',
  'EML-4 Exact Separation',
  'Find a function f in C[0.2, 3.0] that is provably EML-3 (floor F(3) < 1e-8) but NOT EML-2 (floor F(2) >= 1e-8). The census confirms x^2 is EML-3 with F(2)=1.7e-8, F(3)=9.3e-21. Extend this to a FORMAL proof (not just numerical evidence) that x^2 is not in the EML-2 closure. Equivalently: prove that no depth-2 EML atom combination can approximate x^2 to arbitrary precision on [0.2, 3.0].',
  'OPEN',
  'formal-proof',
  NULL,
  NULL,
  NULL
),
(
  'sawtooth-g2',
  'Sawtooth Wave G2 Density',
  'The sawtooth wave f(x) = (x mod pi)/pi on [0.1, 6.28] has G2 (EML+DEML) improvement of only 1.8x over G1, and remains OPEN (floor > 1e-8 at depth 4). Is the sawtooth wave in the G2 closure? If so construct a depth-5+ G2 approximation with MSE < 1e-6. If not, characterize the obstruction (the sawtooth has a jump discontinuity -- show this prevents G2 density analogously to the EML Infinite Zeros Barrier for sin).',
  'OPEN',
  'grammar-g2',
  NULL,
  NULL,
  NULL
),
(
  'tight-pumping-lemma',
  'Tight EML Pumping Lemma',
  'The formal Pumping Lemma gives a 2^k upper bound on zeros of depth-k EML trees. Empirically the maximum observed is 0-1 zeros regardless of depth. Prove or disprove: the tight bound is O(k) (linear in depth), not O(2^k). Specifically, either (a) construct a depth-k EML tree with Omega(k) zeros on [-8,8], or (b) prove all depth-k EML trees on any compact interval have at most k+1 zeros.',
  'OPEN',
  'formal-proof',
  NULL,
  NULL,
  NULL
)
ON CONFLICT (id) DO NOTHING;

-- Verify
SELECT id, name, status FROM challenges ORDER BY id;
