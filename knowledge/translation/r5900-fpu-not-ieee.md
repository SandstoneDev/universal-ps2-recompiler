# The R5900 FPU is not IEEE

- **Category:** translation
- **Summary:** Clamp operands, round toward zero, flush, no fused multiply-add; the PSP FPU uses denormal inputs, so clamps stay.
- **Applies to:** translating EE floating-point and VU0 macro code
- **Evidence:** PC host, PCSX2, real PSP-3000
- **Status:** confirmed

## Situation

Floating-point results of the port differ from the PS2 in the last bits, which later shows as drifting physics,
objects at the origin or animations that slowly go wrong.

## Cause

The R5900 FPU treats operands with exponent 0 as zero and exponent 255 as the largest finite value, rounds toward zero
and flushes, gives the largest value on division by zero, and rounds the product before the add in multiply-add. The
Allegrex FPU can run round-toward-zero with flush, but it uses denormal inputs. Divide and square-root rounding on the
real PS2 is Unknown (PCSX2's interpreter chops).

## Rule

- Set the FPU control register to round toward zero with flush once at the top of the game thread (it is per PSP
  thread).
- Clamp operands where a value can be denormal or infinite (a branchless clamp is cheap and exact).
- Compile with `-frounding-math -ffp-contract=off`, or the compiler folds constants with the wrong rounding.
- Never use the VFPU for values the game reads back: it rounds to nearest and its dot products differ.

## Evidence

PC host and PCSX2: 43,008 VU0 macro vectors with 0 differences against the interpreter; collision code around VU0
calls matched the interpreter, not the recompiler, in 43 of 400 calls. Real PSP-3000: 0 of 43,008 vectors differ.

## Related

`docs/PORTING_GUIDE.md` section 6, `ps2rc/backend_c.py`, skills/ps2rc-translate
