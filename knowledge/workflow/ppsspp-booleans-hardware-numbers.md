# PPSSPP gives booleans, the PSP gives numbers

- **Category:** workflow
- **Summary:** Use PPSSPP to answer does it boot, render and play; take every timing and memory number from the real PSP.
- **Applies to:** every port
- **Evidence:** real PSP-3000 compared with PPSSPP
- **Status:** confirmed

## Situation

A build that runs well in PPSSPP freezes, switches off, runs out of memory or runs much slower on the PSP; or an
optimisation that helps in PPSSPP does nothing on the PSP.

## Cause

PPSSPP emulates behaviour, not the hardware's costs and limits. Seen differences: about 5 MB more free memory; more
open files allowed; coroutine stacks outside the thread stack accepted; GE cost close to zero; no cache model; no
Media Engine; the frame pace is its own; access to the hardware counter registers crashes it; it forwards the PC's
keyboard and pad to the game while its window has focus; CPU reads of VRAM after GE drawing can be stale with some
back-ends.

## Rule

- PPSSPP runs answer yes/no questions: boots to the main loop, renders, plays, no crash lines.
- Never take a time, a speed-up or a memory figure from it.
- Disable the hardware counters and the Media Engine when an emulator is detected.
- Do not touch the PC while an unattended PPSSPP run has focus.

## Evidence

Same EBOOT: about 5,120 KB more free memory in PPSSPP; 13.5 us vs 55 us per mesh for a native path (PPSSPP vs real
PSP-3000); an in-run A/B in PPSSPP always reports no difference because it paces the frames.

## Related

skills/psp-build-test, [Memory-bound CPU](../hardware/memory-bound-cpu-icache.md)
