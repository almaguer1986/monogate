declare module "monogate" {
  export const op:    (x: number, y: number) => number;
  export const E:     number;
  export const ZERO:  number;
  export const NEG_ONE: number;
  export const exp:   (x: number) => number;
  export const ln:    (x: number) => number;
  export const sub:   (x: number, y: number) => number;
  export const neg:   (y: number) => number;
  export const add:   (x: number, y: number) => number;
  export const mul:   (x: number, y: number) => number;
  export const div:   (x: number, y: number) => number;
  export const pow:   (x: number, n: number) => number;
  export const recip: (x: number) => number;
}
