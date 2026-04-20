---
layout: ../../layouts/Base.astro
title: "The SuperBEST Cost of Everything"
description: "From Google's PageRank to your GPS to the NFL passer rating — every equation has a node count. Here are the ones that matter."
date: "2026-04-20"
tag: "observation"
author: "Arturo R. Almaguer"
---

## From Google's PageRank to your GPS to the NFL passer rating

Every equation has a cost. Not in dollars or milliseconds — in operator nodes. Under the SuperBEST v4 routing table (div=2n, recip=1n), any arithmetic expression reduces to a tree of EML-family primitives, and that tree has an exact node count. The count is structural: it does not depend on hardware, language, or numerical library. It depends only on the shape of the formula.

We spent nine sessions measuring equations across technology, sports, and nature. Here is what we found.

---

## The cheapest equation in technology

**ETA = 2 nodes.**

Estimated time of arrival is distance divided by speed: `d / v`. Under v4 routing, division costs 2 nodes. That is the entire computation. Every time a navigation app shows you "14 minutes," it performed a 2-node calculation — the same cost as a batting average (`H / AB`) or a field-goal percentage (`FG / FGA`).

The 2-node ratio is the simplest non-trivial formula that can exist. Anything cheaper is a constant or a variable, which cost zero nodes by definition. ETA, batting average, and field-goal percentage all sit at the absolute floor: one irreducible arithmetic operation, two nodes.

The remarkable thing is where that floor shows up. ETA is arguably the most-used computation in consumer technology. The Maps app runs it millions of times per minute, worldwide. The cheapest formula in technology is also one of the most frequently evaluated ones.

---

## Search engines

**TF-IDF: 7 nodes.**

The formula that made Google's early relevance ranking possible costs 7 nodes. TF-IDF is `(f / total_terms) * ln(N / df)` — one division (2n), one ln (1n), one division (2n), one multiplication (2n). Total: 7n. That is it. The foundation of a trillion-dollar industry.

**PageRank: 5N + 4 nodes** for a graph of N pages.

PageRank is more expensive because it sums contributions from N incoming links. Each link contributes a 5-node term (division plus scaling), and the N terms add linearly. The iterative ranking algorithm that shaped the modern web scales as O(N) in the link graph — no transcendentals required.

**BM25 (modern search): 34 nodes per query term.**

BM25 is the standard ranking function in production search systems today, including Elasticsearch. It costs 34 nodes per term (37 nodes for the query term frequency component, minus 3 shared nodes). The jump from TF-IDF (7n) to BM25 (34n) is the arithmetic cost of saturation — BM25 includes a term-frequency normalization that prevents very common terms from dominating, but that normalization requires extra divisions and additions that multiply the node count by nearly 5x.

Softmax, which converts raw scores to probabilities in neural ranking, costs 4N−3 nodes for N classes. It is cheaper per class than BM25 per term, but it accumulates over every candidate in the retrieval set.

---

## Your GPS

**Haversine: 28 nodes.**

Every time you open Maps and a route appears, the Haversine formula ran. It computes the great-circle distance between two GPS coordinates on a spherical Earth:

```
a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlon/2)
d = 2R·arcsin(√a)
```

The node count is 28: four trigonometric terms (each 1n), four multiplications (each 2n), two divisions for the half-angle reductions (each 2n), three additions (each 3n for positive domain), one square root (3n via pow), and the final arcsin and scaling.

Haversine is almost certainly the most-evaluated "outdoor" equation in human history. Every mapping application — Google Maps, Apple Maps, Waze, ride-share apps, delivery routing — runs this formula for every distance query. The number of daily Haversine evaluations across all devices worldwide is in the billions. It has been running at this scale since smartphones became common. No equation in the physical sciences comes close to this evaluation frequency.

The Vincenty formula (more accurate, accounts for Earth's elliptical shape) costs approximately 80 nodes per iteration. GPS devices and precision surveying use it. Navigation apps use Haversine — 28 nodes is fast enough and accurate enough for routing at human scales.

---

## Video games and 3D graphics

**Quaternion rotation: 99 nodes** (positive-domain addition), **235 nodes** (general-domain addition).

This is why 3D rendering is the GPU bottleneck.

A quaternion rotation requires multiplying two quaternions — four components each — then applying the result to a 3D vector. The algebra expands into many cross-multiplications and additions. Under v4 routing with add_gen=11n (required because quaternion components can be negative), the full general-domain count reaches 235 nodes per rotation.

GPUs exist because of this number. A single rendered frame at 60 fps requires quaternion rotations for every moving object, every bone in an animation rig, every camera transformation. At 235 nodes each, the only way to hit frame-rate targets is massive parallelism — thousands of shader cores doing quaternion arithmetic simultaneously.

For comparison:

| Operation | Nodes |
|-----------|-------|
| Perspective projection | 8n |
| Verlet integration (physics) | 12n |
| Phong lighting (per pixel, per light) | 43n |
| Quaternion rotation (general) | 235n |

Verlet integration — the algorithm used for cloth simulation, soft bodies, and rigid-body physics in games — costs only 12 nodes. Physics engines are arithmetically cheap. It is the rotation and lighting that consume GPU budget.

Phong lighting at 43 nodes is evaluated per pixel, per light source. A scene with four lights and a 1080p framebuffer requires 4 × 1920 × 1080 × 43 = 357 million node evaluations per frame. At 60 fps, that is 21 billion node evaluations per second, for lighting alone. This is why rasterization is a parallel problem.

---

## Sports

**NFL passer rating: 33 nodes. Hodgkin-Huxley neuron: 30 nodes.**

The NFL passer rating formula is more arithmetically complex than the equation that describes how neurons fire.

The passer rating formula, introduced in 1973, involves four components (completion percentage, yards per attempt, touchdown rate, interception rate), each clamped to a range and scaled by specific constants, then averaged and converted to a 0–158.3 scale. The clamping and averaging require multiple additions and divisions that accumulate to 33 nodes.

The Hodgkin-Huxley model — the 1963 Nobel Prize equation describing how action potentials propagate along nerve axons — costs 30 nodes. It contains three conductance terms with voltage-gated variables, but the terms are structurally simpler than the NFL's clamped polynomial.

This is not a joke about sports versus science. It is a factual observation about arithmetic structure: the NFL's particular choice of formula, with its four normalized components and range restrictions, happens to require more irreducible operations than the biophysical model of a neuron. Both equations are what they are. Cost theory just counts them.

Other results:

| Formula | Nodes |
|---------|-------|
| Batting average | 2n |
| ELO rating update | 26n |
| Kelly criterion | 8n |
| Nash equilibrium (2-player) | 19n |
| Pythagorean expectation | 11n |

ELO (26n) costs more than batting average (2n) because it includes a logistic sigmoid transformation on the rating difference — that sigmoid costs 7n on its own — plus the update arithmetic. Nash equilibrium (19n) requires add_gen=11n in the denominator because game payoffs can be negative; the counterexample exists and was verified.

---

## The EML boundary

**CRC-32, Hamming distance, parity check: outside EML.**

This is an important boundary to state honestly.

EML arithmetic handles real and complex numbers via exp, ln, and their combinations. It does not handle GF(2) — the finite field with two elements, where addition is XOR and multiplication is AND. CRC-32, Hamming error-correcting codes, and parity checks all operate in GF(2). They are not more or less expensive than EML formulas; they are in a categorically different domain.

Asking for the SuperBEST node count of a CRC checksum is a type error, the way asking for the temperature of a poem is a type error. The arithmetic is not comparable. Any cost measurement in this series applies only within the real/complex exp-ln domain. Bitwise polynomial arithmetic is elsewhere.

---

## Cross-domain isomorphisms

The deepest result of the nine sessions is not any individual equation cost. It is that the universe reuses the same arithmetic templates across completely unrelated physics.

**The 5-node exponential decay template: `A · exp(−B·x)`**

Five nodes. This structure appears in:

- Beer-Lambert law (optical absorption through a medium)
- CT scan attenuation (X-ray through tissue)
- Radioactive decay (nuclear physics)
- RC circuit discharge (electrical engineering)
- Atmospheric absorption (meteorology)

These equations describe different physical phenomena with different variables and different units. They are structurally identical. The operator tree is `mul(A, exp(mul(neg(B), x)))` — 5 nodes every time. The universe has one algorithm for exponential attenuation and applies it everywhere.

**The 5-node exponential growth template: `A · exp(B·t)`**

Same cost, different sign:

- Population growth (biology)
- Compound interest (finance)
- Bacterial colony growth (microbiology)
- Logarithmic spiral geometry (mathematics)

**The 7-node logarithmic ratio template: `10 · log10(ratio)`**

Seven nodes. This template underlies:

- Sound pressure level in decibels (acoustics)
- Signal-to-noise ratio in communications
- Richter magnitude scale (seismology)
- dBm power measurement (radio engineering)
- Perceptual audio loudness

All five measure ratios on a logarithmic scale. All five cost 7 nodes. The ear, the seismograph, and the radio antenna solve the same 7-node problem.

**The 11-node Hill/Pythagorean template: `x^k / (x^k + y^k)`**

Eleven nodes. Three disciplines:

- Pythagorean expectation (sports analytics): predicts win probability from runs scored and allowed
- Hill equation (pharmacology): models receptor-ligand binding cooperativity
- Michaelis-Menten kinetics (biochemistry): enzyme saturation model

A baseball statistician in 1983, a pharmacologist in 1910, and a biochemist in 1913 each discovered a different interpretation of the same 11-node rational function.

---

## The most expensive equation computed

**Reed-Solomon syndrome computation for RS(255,223): 2037 nodes.**

Every QR code, every DVD, every deep-space transmission from the Voyager probes uses Reed-Solomon error correction. The syndrome computation for the standard RS(255,223) code — 255 total symbols, 223 data symbols, capable of correcting up to 16 symbol errors — requires evaluating a degree-254 polynomial at 32 points over GF(256).

The syndrome computation itself (translating from XOR-based GF arithmetic to real-arithmetic EML, evaluating under 8N−3 with N=255) costs 2037 nodes. This is the most expensive regularly-computed formula in the catalog, by a wide margin.

For reference: the next most expensive is Haversine (28n), used billions of times per day. Reed-Solomon syndrome (2037n) is computed millions of times per second in storage and communication hardware. Error correction is expensive. That cost is why dedicated RS hardware exists — no general-purpose processor core can afford to run 2037-node evaluations on every symbol block in real time without hardware acceleration.

---

## Conclusion

A formula is a formula.

The same node-counting that works for chemistry and neuroscience works for sports analytics, GPS navigation, and error correction. The SuperBEST cost is structural — it does not care whether the equation came from a physics textbook, an NFL rulebook, or an IETF standard.

What the nine sessions established:

- The floor is 2n (ETA, batting average, FG%) — any ratio.
- The ceiling in daily computation is 2037n (Reed-Solomon) — error correction.
- The most frequently evaluated formula in outdoor navigation is 28n (Haversine).
- Sports statistics can exceed neuroscience in arithmetic complexity (NFL 33n > HH 30n).
- The universe uses five or six canonical templates — exponential decay, exponential growth, log ratio, Hill function — across every domain of science and engineering.
- GF(2) bitwise arithmetic is outside EML. The boundary is real and important.

SuperBEST cost theory does not tell you what an equation *means*. It tells you how many irreducible operations it requires. Sometimes that number surprises you. The NFL passer rating surprised us. The Reed-Solomon syndrome count did not — we just had not measured it before.

The cost of everything is countable. We are counting.

---

*Almaguer, A.R. (2026). "The SuperBEST Cost of Everything." monogate research blog. https://monogate.org/blog/cost-of-everything*

*Sessions: TECH-1 through TECH-5, SPORT-1 through SPORT-2, NAT-1 through NAT-2. SuperBEST v4 routing table (div=2n, recip=1n). All results exact and reproducible.*
