---
layout: ../../layouts/Base.astro
title: "How Claude and I Built a Research Program in Two Weeks"
description: "578 expressions, 50 Lean theorems, 5 PyPI packages, an npm port, a HuggingFace dataset, three websites, four interactive demos. Two weeks. One human. Here's what actually worked, what failed, and what the audit system caught before it reached the public."
date: "2026-04-27"
author: "Monogate Research"
tag: deep-dive
featured: true
---

# How Claude and I Built a Research Program in Two Weeks

**Tier: DEEP DIVE** (process essay, not a research result)

In April 2026 I went from "I have an interesting idea about a binary operator" to "the research program has 578 catalogued expressions across 12 domains, 50 Lean-formalized theorems, five published Python packages, an npm port, a HuggingFace dataset, three deployed websites, and four interactive demos." It took roughly two weeks.

I did not work alone. The other half of the keyboard was Claude Code, running across a small fleet of VS Code windows. People keep asking me how. This essay is the answer.

## What Claude actually did

I'll be specific because the honest answer matters more than the cool answer.

**Claude did:** corpus expansion (running symbolic-math probes across thousands of expressions), statistical analysis (Spearman correlations, BH-FDR corrections, false-discovery accounting), Lean audits (running `lake build`, parsing errors, walking dependency chains), package shipping (writing `pyproject.toml`, building wheels, running test suites, twine validation), numerical verification (mpmath at 320-digit precision for cross-checks), and infrastructure (the audit system, the structured memory layer, the knowledge graph, the integration tests).

**I did:** research direction (which mathematical neighborhoods are worth probing, in what order), domain knowledge (when a result connects to existing literature, when it contradicts something I already knew was true), decisions (when to ship, when to wait, when to retract), taste (which framings make a result legible to outsiders), and the "is this real?" judgment calls. I also designed the audit protocol — not because Claude is untrustworthy in particular, but because *any* fast-moving research program needs verification, and a human-in-the-loop has to specify what counts.

Neither of us did our half alone.

## The audit system, which is the part you need

The mechanism that makes this trustworthy isn't speed and it isn't cleverness. It's a 250-line Python script that runs ten verifications and fourteen cross-references on every claim, every push, every commit that touches a public number.

The verifications are concrete. Lean theorem count: 50, computed by parsing every `.lean` file in the repository. Sorries remaining: 4, located by line number, listed by file. Corpus size: 578, counted from the canonical CSV. PyPI test count: 463, fetched by a fresh pytest collection. Headline class membership: 38, computed by filtering the corpus on the four-axis fingerprint.

If any of those numbers diverges from the version recorded in `data/save_points.json` (a SHA256-locked snapshot), the audit fails closed. Nothing pushes. The next session starts by reading the divergence and either updating the canonical state or rolling the change back.

The fourteen cross-references are subtler. Every public-surface mention of a number — on `monogate.org`, in the paper draft, in the README, in capability cards, in roadmap files — gets greppped, normalized, and compared against the canonical state. If the website says "49 Lean theorems" and the audit script counts 50, that's a failure. The system catches stale numbers before they ship.

This sounds bureaucratic. It is. It is also why the program ships at the speed it does. **You can't move fast if every push requires a human spot-check on every number.** You need automated verification that's stricter than human attention, so the humans only have to inspect the diff.

## Six retractions, documented

The program publicly retracted six claims during its arc. I want to walk through them because the retractions are the part that's actually load-bearing, more than any individual finding.

- **`p3-d5-w2-c1` enrichment** — initial small-N sample showed 40× enrichment with apparent significance. Re-ran at N=5,000. Failed BH-FDR. Retracted. The earlier number was a small-sample artifact.
- **Width-vs-training cost coupling** — looked like a clean signal in cross-domain v1. Cross-domain v2 ran controls and found the effect was confounded by collinearity with depth. Disproven dependent claim.
- **PNE-vs-fp16 sensitivity** — first reading suggested Pfaffian-extended functions tolerate fp16 better than elementary ones. Controlled corpus showed the apparent signal was driven by activation-identity lookup, not the structural distinction. Retracted.
- **Standing-wave convention mismatch** — a chain-order miscount on a physics-textbook expression turned out to be us using a different normalization convention than the textbook. Corrected.
- **Reverb impulse-response convention mismatch** — same shape of error, different domain. Corrected.
- **CR2 circadian neighbour class** — a cross-domain class assignment that didn't survive re-clustering at the master 578-row corpus. Demoted.

Six wrong things, all caught by computation, all documented in the public `audit_log.md`. Honest tracking of what didn't survive is the foundation that makes the *survivors* mean something.

## The structured memory system

Most "AI memory" patterns I see online are flat markdown files dumped in a folder. We tried that. It didn't scale past about fifty entries before the memory got contradictory and stale.

What replaced it: typed entries, append-only, with a queryable graph layer on top.

Each memory has a `type` (one of: `user`, `feedback`, `project`, `reference`), a description, and a body. They live in `~/.claude/projects/<repo>/memory/` as individual `.md` files indexed by a `MEMORY.md` table-of-contents. The graph builder ingests them along with the corpus, the Lean files, the audit log, and the roadmap into a single networkx-backed knowledge graph that currently sits at over 1,700 nodes.

Why this matters: when Claude starts a new session, it can query "what do we know about chain-additivity?" and get back the relevant memories, the relevant Lean theorems, the relevant blog posts, and the staleness warnings — not by sifting through a chronological journal, but by walking the graph. The retraction edges are first-class. The "this claim was corrected by that claim" relationship is computable.

This is what agentic memory should be. Not a transcript, not a chat log — a *typed*, *queryable*, *staleness-aware* knowledge layer.

## The phantom attractor incident

Here's an honest example of the system catching a confabulation.

In the middle of a session, I asked Claude to fix a display bug in our chaos-explorer demo involving an attractor we labeled `T05` at value `≈ 6.27`. Claude wrote a confident analysis and started preparing a code change.

The audit halted it. There is no `T05` attractor at value 6.27 in the actual landscape. Claude had hallucinated a plausible-sounding value from context. The real fix involved a different attractor at a different value. The audit didn't know the truth — it just knew that the value Claude was asserting didn't appear in the canonical numbers it had locked. That mismatch surfaced before the change shipped.

This is what "correct by construction" looks like in practice. I trust Claude. I do not trust any individual claim Claude (or I) makes without verification.

## If you're building with an AI coding agent

Five things actually mattered:

1. **Run an audit before every push.** Even if you're alone. The audit catches your mistakes too.
2. **Type your memory.** Flat markdown rots. Typed memory with append-only history doesn't.
3. **Document retractions publicly.** Every wrong thing you caught is evidence that the right things mean something. Hide retractions and your survivors lose their warrant.
4. **Keep canonical numbers in one place.** A `data/` directory with versioned snapshots. Everything else greps against it. No exceptions.
5. **Verify every number before it leaves the building.** Twice. The cost of asking is small; the cost of a wrong number on a paper is large.

There's nothing magical here. It's just disciplined plumbing applied consistently. The discipline is what lets the speed compound.

---

The numbers I quoted at the top of this post — 578 expressions, 50 Lean theorems, 5 PyPI packages — were verified against the canonical state at the time I drafted this. If any of them have aged, the audit will catch it on the next push. That's the system working as intended.

The full toolchain is open. The package is `eml-cost` on PyPI. The Lean repository is at [agent-maestro/monogate-lean](https://github.com/agent-maestro/monogate-lean). The PETAL learning curriculum is on HuggingFace at [Monogate/petal-eml](https://huggingface.co/datasets/Monogate/petal-eml). The site footer links to all of it.

---

*Monogate Research (2026). "How Claude and I Built a Research Program in Two Weeks." monogate research blog. https://monogate.org/blog/built-with-claude*
