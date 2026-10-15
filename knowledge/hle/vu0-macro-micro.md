# VU0: macro ops exact by rule, micro programs with static timing

- **Category:** hle
- **Summary:** Translate VU0 macro instructions inline with the VU's own arithmetic rules; translate VU0 micro programs to C with flag and Q timing resolved at translation time; never use the VFPU for results the game reads.
- **Applies to:** COP2 macro mode, VCALLMS micro programs, the PSP VFPU
- **Evidence:** PCSX2 interpreter vectors on host, PPSSPP and the PSP; hardware timings on a PSP-3000
- **Status:** confirmed

## Situation

Games use VU0 in macro mode (vector math inline in EE code) and call small micro programs (collision, skinning
helpers). The PSP has no VU; its VFPU looks similar but is not.

## Cause

VU arithmetic is not IEEE: operands are clamped, products are rounded before the add (no fused multiply-add),
x - x is +0, VF00 reads as constants. Micro programs depend on pipeline timing: status and MAC flags become visible
4 cycles after the FMAC instruction, Q 7 or 13 cycles after DIV / RSQRT. The VFPU rounds to nearest, aligns dot
product terms to the largest exponent and approximates special functions to about 22 bits.

## Rule

- Macro: clamp operands, round each product, keep LQC2/SQC2 addresses 16-byte aligned (address & ~15), integer
  registers VI01-15 are 16 bits in CFC2. Test against the PCSX2 interpreter (its recompiler differs on exponent-255
  inputs).
- Micro: get the microcode by following the game's VIF0 DMA chain; translate it with the timing resolved statically
  (sequential execution is wrong); running it synchronously at VCALLMS is exact when nothing reads VU0 state before
  the interlocking read. Generate it on the user's PC from their disc.
- Test with an ordinary vector set (no exponent 255), a separate edge set, and a mutation per rule.
- VFPU only for renderer math the game never reads back. It needs the VFPU thread attribute; coroutines share its
  registers; the Media Engine has none.

## Evidence

Macro: 43,008 vectors, 0 differences against the PCSX2 interpreter (host, PPSSPP, PSP). Micro: one 245-instruction
program, 11,264 vectors, 0 differences; each timing mutation turned 2,300-4,100 vectors red. PSP-3000: 3.35 us per
call with the register file in memory, about 1,100-1,300 calls per frame (3.9-4.5 ms); a version holding values in
FPU registers was 7 % slower (spills). VFPU: only raw moves are exact; `sv.q` to cached memory has a 7-cycle
interlock (slower than four `sw`).

## Related

`ps2rc/vu/micro_gen.py`, [The R5900 FPU is not IEEE](../translation/r5900-fpu-not-ieee.md),
[Reference runs](reference-run-first-divergence.md), skills/hle-authoring
