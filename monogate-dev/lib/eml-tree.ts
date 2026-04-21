/**
 * Minimal tree-building layer for node/depth counting.
 * Mirrors monogate/src/index.js but returns AST nodes instead of numbers.
 */

export type TreeNode =
  | { tag: "eml"; left: TreeNode; right: TreeNode }
  | { tag: "lit"; label: string };

export const mkLit = (v: number | string): TreeNode => ({
  tag: "lit",
  label: String(v),
});

export const mkVar = (name = "x"): TreeNode => ({ tag: "lit", label: name });

// Auto-wrap: numbers/strings become lit nodes; TreeNodes pass through
const wrap = (v: unknown): TreeNode => {
  if (v !== null && typeof v === "object" && "tag" in (v as object)) {
    return v as TreeNode;
  }
  return mkLit(v as number | string);
};

const eml = (x: unknown, y: unknown): TreeNode => ({
  tag: "eml",
  left: wrap(x),
  right: wrap(y),
});

const ONE: TreeNode = { tag: "lit", label: "1" };
const TWO: TreeNode = { tag: "lit", label: "2" };

export const E_t: TreeNode = eml(ONE, ONE);
export const ZERO_t: TreeNode = eml(ONE, eml(eml(ONE, ONE), ONE));
export const NEG_ONE_t: TreeNode = eml(ZERO_t, eml(TWO, ONE));

export const exp_t = (x: unknown): TreeNode => eml(wrap(x), ONE);
export const ln_t  = (x: unknown): TreeNode => eml(ONE, eml(eml(ONE, wrap(x)), ONE));
export const sub_t = (x: unknown, y: unknown): TreeNode => eml(ln_t(x), exp_t(y));
export const neg_t = (y: unknown): TreeNode => eml(ZERO_t, eml(sub_t(wrap(y), NEG_ONE_t), ONE));
export const add_t = (x: unknown, y: unknown): TreeNode => eml(ln_t(x), eml(neg_t(y), ONE));
export const mul_t = (x: unknown, y: unknown): TreeNode => eml(add_t(ln_t(x), ln_t(y)), ONE);
export const div_t = (x: unknown, y: unknown): TreeNode => eml(add_t(ln_t(x), neg_t(ln_t(y))), ONE);
export const pow_t = (x: unknown, n: unknown): TreeNode => eml(mul_t(n, ln_t(x)), ONE);
export const recip_t = (x: unknown): TreeNode => eml(neg_t(ln_t(x)), ONE);
export const sqrt_t = (x: unknown): TreeNode => pow_t(x, mkLit(0.5));

export function countNodes(node: TreeNode): number {
  if (node.tag === "lit") return 1;
  return 1 + countNodes(node.left) + countNodes(node.right);
}

export function countDepth(node: TreeNode): number {
  if (node.tag === "lit") return 1;
  return 1 + Math.max(countDepth(node.left), countDepth(node.right));
}
