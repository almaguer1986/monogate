---
layout: ../../layouts/Base.astro
title: "Hear the Math: When Equations Become Sound"
description: "The best-selling synthesizer in history runs on a Bessel function. The Gibbs phenomenon's 9% overshoot is a theorem you can hear. Three interactive demos at 1op.io let you turn structural complexity into sound."
date: "2026-04-27"
author: "Monogate Research"
tag: deep-dive
featured: true
---

# Hear the Math: When Equations Become Sound

**Tier: DEEP DIVE** (interactive, audio-first)

The best-selling synthesizer in history is the Yamaha DX7. It sold over 200,000 units in the 1980s. You've heard it in nearly every chart-topping pop song from that decade — Phil Collins, Whitney Houston, Brian Eno, the bell tones, the electric pianos, the bass patches that defined a sound.

The DX7 is, mathematically, a single equation:

<div class="math-block">y(t) = sin(ω<sub>c</sub> · t + I · sin(ω<sub>m</sub> · t))</div>

A carrier sine wave. Its phase is modulated by another sine wave. The modulation index `I` controls how hard you push the modulator into the carrier. That's it. Six operators per voice, sixteen voices, one equation. Every patch you ever loved — bell, bass, EP, brass, woodwind — is the same expression with different settings of `I` and the frequency ratio `ω_m / ω_c`.

## What the Bessel function is doing

When you push `I` past zero, the spectrum of that equation is exactly described by Bessel functions of the first kind, `J_n(I)`. The carrier amplitude is `J_0(I)`. The first sideband on each side is `J_1(I)`. The second is `J_2(I)`. And so on, infinitely many sidebands at `ω_c ± n·ω_m`, each weighted by `J_n(I)`.

Here's where it gets eerie. `J_0(I)` has its first zero at `I ≈ 2.4048`. That means at exactly that modulation index, **the carrier vanishes**. The fundamental frequency you started with is gone. All the energy has been pushed into sidebands.

You can hear this. Push the slider to 2.4 and the tone changes character entirely — the root pitch you started on disappears, replaced by a hollow timbre made of sidebands only. That sonic discontinuity at I ≈ 2.4 is a Bessel zero. It's a property of the function `J_0`, not a property of any particular synthesizer. Every FM synth in history has this happen at the same number.

There's a [demo at 1op.io/playground/bessel-fm-synth](https://1op.io/playground/bessel-fm-synth). Slide the modulation index. When the carrier disappears, you've just heard a Bessel zero.

## The Gibbs phenomenon, audible

Try a different demo. Take a square wave and rebuild it from sine waves — the standard Fourier-series construction. Three sines, then five, then nine, then ninety-nine. As you add more terms, the wave gets sharper and sharper at the edges. It looks like it's converging to a perfect square.

It isn't.

There's a fixed overshoot at every discontinuity, **about 9% of the jump height**, that does not go away no matter how many sines you add. It's the Gibbs phenomenon, named for J. Willard Gibbs who explained it in 1898. The overshoot's exact size is a number you can compute from a specific integral — `(1/π) · ∫₀^π sin(x)/x dx ≈ 1.0895`, giving the famous ≈8.95% overshoot.

And you can hear it. With more partials the wave is sharper, but the *peak* of the spike near the edge stays the same height relative to the jump. Forever. There's a [demo at 1op.io/playground/math-as-melody](https://1op.io/playground/math-as-melody) where you can stack partials and listen. Past about 15 partials, the changing thing is the *width* of the overshoot, not its height.

This is a mathematical theorem audible in your speakers. We don't usually expect those.

## Why this is structurally interesting

We catalogued a corpus of 578 mathematical expressions across 12 domains — physics, signal processing, neuroscience, color science, the rest — and gave each one a structural fingerprint based on its Pfaffian complexity. The fingerprints have four axes; we've written about them in [other posts](/blog/one-operator).

When you look across the whole corpus, **FM synthesis sits in a fingerprint class no other expression occupies.** Out of 578 expressions, exactly one has the chain-of-functions structure deep enough to need the maximum recorded chain order: the carrier-modulator equation that powers the DX7.

The most structurally complex elementary function humans have *mass-produced* is the one inside every Yamaha DX7. We didn't put it there. The math did.

## What this means for sound design

The structural complexity of an expression isn't an academic curiosity — it's a budget. Each unit of chain order roughly corresponds to one nonlinear cascade, and nonlinear cascades are where harmonic richness comes from. FM synthesis sounds rich because it has the chain depth to support a rich spectrum.

Subtractive synthesis sits at lower chain depth. It produces simpler harmonic structures. Granular synthesis lives somewhere else entirely, inside chain orders the elementary catalog doesn't reach. If you've ever wondered why some synthesis methods sound categorically richer than others — chain depth is a measurable answer.

## The third demo: structural sound

The third demo at [1op.io/playground/pfaffian-phase-portrait](https://1op.io/playground/pfaffian-phase-portrait) doesn't generate audio — it shows you what the structural fingerprint of an expression looks like as a 2D phase portrait. Type in an equation, watch the geometry. Some shapes you'll recognize from physics class. Some you won't, because they belong to fingerprint classes that span fields you've never been told are connected.

You drive your car using one of these structural classes (closed-loop control). Your phone resamples your photos using another one (Shannon sinc filters). Your eyes detect color using a third (HSL sinusoids). All three classes are the same structural family, with different physical interpretations bolted on.

## Try them

Three demos, no signup, no install:

- [bessel-fm-synth](https://1op.io/playground/bessel-fm-synth) — slide the modulation index, hear the Bessel zeros
- [math-as-melody](https://1op.io/playground/math-as-melody) — additive synthesis, hear the Gibbs phenomenon
- [pfaffian-phase-portrait](https://1op.io/playground/pfaffian-phase-portrait) — see structural fingerprints as geometry

Headphones recommended. The Gibbs overshoot is more obvious through them than through laptop speakers.

---

*Monogate Research (2026). "Hear the Math: When Equations Become Sound." monogate research blog. https://monogate.org/blog/hear-the-math*
