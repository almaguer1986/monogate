-- Fix challenge statuses to match proved results
-- Run in Supabase SQL editor
-- Date: April 2026

-- sin(x): PROVED IMPOSSIBLE — T01 Infinite Zeros Barrier
UPDATE challenges
SET
  status = 'closed',
  result_summary = 'Proved impossible by T01 (Infinite Zeros Barrier). Every depth-k real EML tree has at most 2^k zeros on any compact interval. sin(x) has infinitely many zeros, so no finite-depth EML tree can equal sin(x) exactly.',
  proof_reference = 'T01',
  proof_link = NULL
WHERE id = 'sin';

-- cos(x): PROVED IMPOSSIBLE — T01 Infinite Zeros Barrier (same theorem)
UPDATE challenges
SET
  status = 'closed',
  result_summary = 'Proved impossible by T01 (Infinite Zeros Barrier). cos(x) has infinitely many zeros on the real line; every finite-depth EML tree has at most finitely many zeros. No EML expression can equal cos(x).',
  proof_reference = 'T01',
  proof_link = NULL
WHERE id = 'cos';

-- i (strict, real grammar): PROVED IMPOSSIBLE — T17, Lean-verified
UPDATE challenges
SET
  status = 'closed',
  result_summary = 'Proved impossible under the strict real grammar (principal-branch ln, ln(0) throws). Theorem T17, machine-verified in Lean 4: no finite real EML tree from {1} evaluates to i = sqrt(-1). Under the extended-reals grammar the problem remains open.',
  proof_reference = 'T17',
  proof_link = NULL
WHERE id = 'i-strict';

-- pi: OPEN (no proof either way)
UPDATE challenges
SET
  status = 'open',
  result_summary = NULL,
  proof_reference = NULL,
  proof_link = NULL
WHERE id = 'pi';

-- i (extended, complex grammar): OPEN
UPDATE challenges
SET
  status = 'open',
  result_summary = NULL,
  proof_reference = NULL,
  proof_link = NULL
WHERE id = 'i-extended';

-- Verify
SELECT id, name, status, proof_reference FROM challenges ORDER BY created_at;
