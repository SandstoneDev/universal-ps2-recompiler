# A/B sets with a control and a control-again

- **Category:** workflow
- **Summary:** Compare variants on the PSP only against two control runs; their difference is the drift.
- **Applies to:** speed measurements on the real PSP
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

A variant looked several milliseconds faster or slower, and the result did not repeat.

## Cause

Run-to-run drift (warm-up, battery, card cache), and above all the game's path: a change that alters timing or random
numbers sends a scripted run into another situation that costs more or less.

## Rule

- One change per set; one EBOOT per variant differing only in what is measured; distinct XMB titles; thin folders.
- A control and a control-again (same EBOOT, two folders); same scripted input, same power state, fixed run length.
- Compare by game time over a fixed window, by medians of windows, and by profiler zones; first check that both
  variants did the same guest work.
- Keep profiling in a separate folder (it costs a few ms per frame).
- If the runtime has an in-run A/B (variants switched at window boundaries inside one run), prefer it for run-time
  switchable options.

## Evidence

Real PSP-3000: drift between two controls was small (87.7 vs 87.9 ms; 68.0 vs 68.0 ms), while one "faster" variant's
3.3 ms held about 2 ms of path effect. Per-iteration noise between two controls on the same path: sd 3.8 ms.

## Related

skills/psp-build-test section 5, [PPSSPP gives booleans](ppsspp-booleans-hardware-numbers.md)
