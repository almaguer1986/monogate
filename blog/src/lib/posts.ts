// Unified post discovery for monogate.org/blog.
//
// Two sources merge into one Post[] sorted by date desc:
//   1. Markdown posts under src/pages/blog/*.md (auto-discovered via
//      Vite's import.meta.glob — adding a new .md file with frontmatter
//      automatically registers it; no manifest edit needed).
//   2. The 14 hand-built .astro posts (one-off feature pages with
//      custom JSX content). These are listed in ASTRO_POSTS below.
//      Add a new row when (rarely) authoring another .astro post.
//
// The shape is stable so downstream consumers (index, tag pages, search
// index, RSS, sitemap) don't care which source a post came from.

export type Post = {
  href: string;          // url path, e.g. /blog/one-operator
  slug: string;          // url-segment, e.g. one-operator
  title: string;
  desc: string;          // short description (frontmatter.description)
  tag: string;           // category — see tagMeta below
  date: string;          // YYYY-MM-DD
  featured?: boolean;    // hero-row eligibility (frontmatter or manifest)
};

// ─── Markdown auto-discovery ─────────────────────────────────────────────
// Vite's eager glob loads frontmatter at build time. We only read what we
// need; the markdown body is rendered separately by Astro when the post's
// route is requested.

type MdModule = {
  frontmatter?: {
    title?: string;
    description?: string;
    tag?: string;
    date?: string;
    pubDate?: string;
    featured?: boolean;
  };
};

const mdGlob = import.meta.glob<MdModule>('../pages/blog/*.md', { eager: true });

const mdPosts: Post[] = Object.entries(mdGlob).flatMap(([path, mod]) => {
  const slugMatch = path.match(/\/([^/]+)\.md$/);
  if (!slugMatch) return [];
  const slug = slugMatch[1];
  const fm = mod.frontmatter ?? {};
  if (!fm.title || !fm.tag) return [];   // skip drafts / partials
  return [{
    href: `/blog/${slug}`,
    slug,
    title: fm.title,
    desc: fm.description ?? '',
    tag: fm.tag,
    date: fm.date ?? fm.pubDate ?? '',
    featured: fm.featured === true,
  }];
});

// ─── Hand-maintained .astro post manifest ────────────────────────────────

const ASTRO_POSTS: Post[] = [
  { href: '/blog/auditing-1200-sessions', slug: 'auditing-1200-sessions', title: 'Auditing 1200 Sessions', tag: 'meta', date: '2026-04-19', desc: 'From 957 claimed theorems to 18 honest ones. What the audit process revealed and why it matters.' },
  { href: '/blog/complexity-census', slug: 'complexity-census', title: 'The EML Complexity Census', tag: 'observation', date: '2026-04-19', desc: '23 elementary functions classified by minimum EML approximation depth. What is proved, what is computational, what is open.' },
  { href: '/blog/deml-is-incomplete', slug: 'deml-is-incomplete', title: 'DEML Is Incomplete', tag: 'theorem', date: '2026-04-19', desc: 'deml(x,y) = exp(−x) − ln(y) cannot construct exp(+x) or neg(x). Structural proof + exhaustive search over 861,952 trees.' },
  { href: '/blog/depth-6-phase-transition', slug: 'depth-6-phase-transition', title: 'The Depth-6 Phase Transition', tag: 'observation', date: '2026-04-19', desc: 'At depth 5, all complex EML values have Im = −π exactly. At depth 6, imaginary parts explode. A structural phase transition.' },
  { href: '/blog/eml-chaos', slug: 'eml-chaos', title: 'EML Chaos: Attractors, Bifurcation, and Lyapunov Exponents', tag: 'research', date: '2026-04-19', desc: 'DEML and EMN generate bounded 2D strange attractors. No classical period-doubling — the exponential family is a different universality class. Lyapunov landscape 92.9% correlated with Mandelbrot interior.' },
  { href: '/blog/euler-formula-is-eml', slug: 'euler-formula-is-eml', title: "Euler's Formula Is the EML Operator", tag: 'exposition', date: '2026-04-19', desc: 'eml(ix, 1) = exp(ix). One node. The deepest identity in mathematics, as a single binary tree leaf.' },
  { href: '/blog/infinite-zeros-barrier', slug: 'infinite-zeros-barrier', title: 'The Infinite Zeros Barrier', tag: 'theorem', date: '2026-04-19', desc: 'Why sin(x) cannot be expressed as a finite real EML tree. Every real EML tree is real-analytic with finitely many zeros.' },
  { href: '/blog/i-unconstructibility', slug: 'i-unconstructibility', title: "Why You Can't Build i from 1", tag: 'theorem', date: '2026-04-19', desc: 'Under strict principal-branch semantics, i is unreachable from {eml, 1}. Lean-verified. Depth-6 closest approach: 0.99999524.' },
  { href: '/blog/near-miss', slug: 'near-miss', title: '0.99999524: The Near-Miss', tag: 'research', date: '2026-04-19', desc: 'How close can an EML tree get to i? A gap of 4.76×10⁻⁶ and the transcendental obstruction via Lindemann–Weierstrass.' },
  { href: '/blog/negative-exponent', slug: 'negative-exponent', title: 'exp(−x) and the Five-Operator Barrier', tag: 'observation', date: '2026-04-19', desc: 'exp(−x) is blocked for 1-node EML across five operator families. DEML breaks through: deml(x,1) = exp(−x) exactly.' },
  { href: '/blog/phantom-attractor', slug: 'phantom-attractor', title: 'The Phantom Attractor Is Not Real', tag: 'observation', date: '2026-04-19', desc: 'EML gradient descent converges to ~3.17 on 40/40 seeds when targeting π. PSLQ found no relation. Vanishes at higher precision.' },
  { href: '/blog/pumping-lemma', slug: 'pumping-lemma', title: 'The Pumping Lemma for EML Trees', tag: 'conjecture', date: '2026-04-19', desc: 'Depth-k trees have at most 2^k zeros (proved). Observed maximum is O(k). The gap suggests a tighter bound — still open.' },
  { href: '/blog/weierstrass-theorem', slug: 'weierstrass-theorem', title: 'The EML Weierstrass Theorem', tag: 'theorem', date: '2026-04-19', desc: 'EML trees are dense in C([a,b]). Any continuous function approximable to arbitrary precision — but not always exactly representable.' },
  { href: '/blog/what-best-routing-saves', slug: 'what-best-routing-saves', title: 'What BEST Routing Saves', tag: 'engineering', date: '2026-04-19', desc: 'Node-count and wall-clock benchmarks across 8 elementary functions. BEST dispatch vs naive EML.' },
];

// ─── Tag taxonomy ────────────────────────────────────────────────────────

export const tagMeta: Record<string, { color: string; label: string }> = {
  announcement:{ color: 'var(--pink)', label: 'announcement' },
  theorem:     { color: 'var(--green)', label: 'theorem' },
  conjecture:  { color: '#f87171', label: 'conjecture' },
  observation: { color: 'var(--orange)', label: 'observation' },
  research:    { color: 'var(--violet)', label: 'research' },
  'deep-dive': { color: 'var(--cyan)', label: 'deep dive' },
  exposition:  { color: 'var(--cyan)', label: 'exposition' },
  engineering: { color: 'var(--orange)', label: 'engineering' },
  meta:        { color: '#9ca3af', label: 'meta' },
};

export const tagOrder = [
  'announcement', 'theorem', 'conjecture', 'observation', 'research',
  'deep-dive', 'exposition', 'engineering', 'meta',
];

// ─── Public API ──────────────────────────────────────────────────────────

/** Every post, sorted newest first. */
export function getAllPosts(): Post[] {
  return [...mdPosts, ...ASTRO_POSTS]
    .filter(p => p.tag in tagMeta)
    .sort((a, b) => b.date.localeCompare(a.date));
}

/** Hero-row eligibility: featured: true in frontmatter / manifest. */
export function getFeaturedPosts(): Post[] {
  return getAllPosts().filter(p => p.featured);
}

/** Newest N posts (excluding featured to avoid duplication in the hero row). */
export function getRecentPosts(limit = 6): Post[] {
  return getAllPosts().filter(p => !p.featured).slice(0, limit);
}

/** Random N posts excluding the newest M and featured (so each row holds different content). */
export function getRandomPosts(limit = 6, excludeRecentN = 6): Post[] {
  const eligible = getAllPosts().filter(p => !p.featured).slice(excludeRecentN);
  // Build-time deterministic shuffle: Fisher-Yates seeded by post count
  // (so random row is stable per build but reshuffles when content changes).
  const rng = mulberry32(eligible.length * 2654435761);
  const arr = [...eligible];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.slice(0, limit);
}

export function getPostsByTag(tag: string): Post[] {
  return getAllPosts().filter(p => p.tag === tag);
}

export function getAllTags(): string[] {
  const seen = new Set<string>();
  for (const p of getAllPosts()) seen.add(p.tag);
  return tagOrder.filter(t => seen.has(t));
}

// Tiny seeded RNG (Mulberry32) so the random row is deterministic per build.
function mulberry32(seed: number) {
  let s = seed | 0;
  return function () {
    s = (s + 0x6D2B79F5) | 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
