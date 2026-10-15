# Memory-bound CPU: the instruction cache dominates

- **Category:** hardware
- **Summary:** A large translated program on the PSP stalls on instruction-cache misses; code size and layout are speed.
- **Applies to:** PSP-2000/3000 at 333 MHz, any large translated program
- **Evidence:** real PSP-3000 (hardware counters)
- **Status:** confirmed

## Situation

A recompiled 3D game ran at a fraction of the expected speed, and the profile was flat: no translated function took
more than about 1 % of the frame. Hand-optimised C versions of the hottest functions gained little.

## Cause

The translated program touches megabytes of code per frame; the Allegrex has a 16 KB instruction cache. The miss is a
capacity problem, not a conflict problem: most of the frame's code is entered once or a few times per frame.

## Rule

- Measure CPI and cache misses before optimising (hardware counters through the kernel helper module; never in an
  emulator).
- Prefer levers that remove code: ABI-mode translation, base-register masking, dead save/restore removal,
  branchless clamps, fewer helper calls.
- Mark never-run functions cold and place hot call chains together (`-ffunction-sections` and a section-ordering
  file).
- Replace work at an API level, or move it to the Media Engine, rather than tuning single functions.
- Smaller is not always faster: build and measure every lever (`-Os` was much slower).

## Evidence

Real PSP-3000, 333 MHz: CPI 2.65 to 2.87; about 50 % of busy cycles stalled on memory; 11.7 to 12.9 instruction-cache
misses and 6.0 to 7.0 data-cache misses per 1000 instructions. About 4.8 MB of code entered per frame. Function
layout (cold marking + call-chain clusters): -1.9 % frame time. Base-register masking: -6 %. `-Os`: 41 % slower
despite 34 % less code. A 13 to 20 KB native path called between pieces of game code cost 55 us per mesh on the
PSP and 13.5 us in PPSSPP (no cache model); deferring and batching it cut 30 to 13.6 ms per frame.

## Related

skills/psp-performance, [PPSSPP gives booleans](../workflow/ppsspp-booleans-hardware-numbers.md), `docs/PORTING_GUIDE.md` section 14
