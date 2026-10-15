# Translator levers measured on hardware: code size beats instruction count

- **Category:** translation
- **Summary:** On the I-cache-bound PSP, back-end levers that remove code win; instruction-count savings that grow code lose; every lever needs a hardware A/B.
- **Applies to:** the C back-end (`ps2rc/backend_c.py`), psp-gcc flags, any large translated program
- **Evidence:** real PSP-3000 at 333 MHz (A/B sets with controls), host instruction counts, static sizes
- **Status:** confirmed

## Situation

The first full translation was 3.9x the guest code and ran the reference game at about 7-8 fps. Only about 30 % of
the generated instructions did the guest's work.

## Cause

Where the code went (first generation): guest context loads and stores 21 %, FPU operand clamps 13.5 %, guest
address masking 11.8 %, host stack traffic 11.4 %; callee-saved save/restore lines were 18.9 % of the code. A frame
enters about 4.8 MB of code against a 16 KB instruction cache, so bytes cost more than instructions.

## Rule

Adopt, in this order (each was measured):

| Lever | Effect |
|---|---|
| Width analysis: narrow 64/128-bit integer ops that are really 32-bit (96.8 % of them were) | the base of everything below |
| Register caching of guest registers in C locals (v0 -> v4 -> v5) | benchmark 34.9 -> 24.0 ms (-31 %) |
| Branchless 6-instruction FPU clamp, clamp once at load | size 3.89x -> 3.38x |
| 128-bit, HI/LO, ACC in locals | -> 3.00x |
| Drop dead callee-saved save/restore pairs (94-97 % qualify), one-word write-backs | -> 2.57x |
| Mask only the base register, 64 KB guard areas around the guest RAM window | -> 2.31x; -6.0 % frame time (-3.0 ms) |
| Constant window mask, lean back-edge safe points, fused unaligned load pairs (about 70 instructions -> 1), `-fsched-pressure` | -5.8 % frame time (86.2 -> 81.2 ms) |
| Return values written back only where a caller reads them, one-word arguments through pass-through callees (whole-program) | -8.25 % code, EBOOT -971 KB, about -2 ms (-3 %) |
| Cold attribute on never-run functions + call-chain ordering (section ordering file) | -1.9 % (-0.95 ms) |
| Bit-exact natives of the 5 hottest leaves, with a check mode | +1.9 % fps (-1.6 ms) for -4.3 % instructions |

Do not adopt (measured worse or zero): `-Os` (34 % less code, **41 % slower**); `-O1` (larger); `-falign-*` (no
effect); "smaller" flag sets (`-freorder-blocks-algorithm=simple`, no loop-invariant motion, no PRE/GCSE: 1.7-3.4 %
less hot code, slower); profile-guided branch hints (+0.47 to +0.9 %: fewer I-misses, more D-misses); VU0 vector
lanes in locals everywhere (spills, larger); global host registers (0 %); FPU-register rewrite of a VU0 program
(+7 %); a cold-path out-of-line clamp (+8 % size).

Whole-program levers (return demand, argument width) bake liveness into the C: translate again whenever the hook
list or HLE references change.

## Evidence

Real PSP-3000, 333 MHz, A/B sets with control and control-again; size ladder static; instruction counts from the host
build. Placement alone moves a binary by 1-3 %: levers under 2 % need repeated runs. Not done yet, estimated -3 to
-10 ms: register arguments between translated functions (the call protocol is about 17 % of instructions),
hot/cold block splitting.

## Related

[Memory-bound CPU](../hardware/memory-bound-cpu-icache.md), [Width and liveness bugs](width-liveness-bugs-at-boot.md),
[The R5900 FPU is not IEEE](r5900-fpu-not-ieee.md), skills/psp-performance
