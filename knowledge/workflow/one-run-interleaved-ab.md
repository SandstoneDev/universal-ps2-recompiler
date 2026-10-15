# One-run interleaved A/B: up to four variants in one boot, a verdict with a confidence interval

- **Category:** workflow
- **Summary:** Switch run-time options between variants every few iterations inside one run, in seeded random block order, and decide by paired window differences with a sign-test interval; it removes the game-path noise that separate folders suffer from.
- **Applies to:** speed decisions on the real PSP for options that can change at run time
- **Evidence:** real PSP-3000 (validated against a known lever; A/A checks)
- **Status:** confirmed

## Situation

Separate-folder A/B sets took about 30 minutes of the tester's time per verdict, and a "-3.3 ms" result held about
2 ms of path effect: the scripted run had gone another way.

## Cause

On the PSP the per-iteration repeatability is good; the noise is the game's path (traffic, streaming, what the camera
sees). Two folders never see the same path.

## Rule

- Up to 4 variants per run, one of them a control-again (an A/A check). Cut the run into windows of 6 iterations;
  each block runs every variant once in a seeded random order; do not count the first 2 iterations of a window
  (settle). Options that carry state between windows (draw distance, streaming) need longer windows (12, settle 4).
- Verdict: the median of paired window-median differences with a 95 % sign-test interval; also print the t-test
  mean. "Faster" or "slower" only when the interval excludes 0.
- Only options that every consumer re-reads at run time can be interleaved; boot-time options (density, memory
  layout) still need separate folders with a control and a control-again.
- The run reports itself: a results file next to the EBOOT, the final screen as an image, one game frame per
  variant (taken in a settle iteration - the display lags at least 2 iterations).
- Check what the scenario exercises: a scripted walk once left the player standing for most measured windows.
- PPSSPP always says "no difference" (its own pacing): hardware only.

## Evidence

PSP-3000: a known lever measured -1.5 ms, interval -2.29..-1.01, where the folder method had said -3.3 ms. Resolution
about 0.7 ms with 3 variants over 2,400 iterations. Tester time per verdict about 30 -> 5.5 minutes. Per-iteration sd
3.8 ms, A/A mean -0.11 ms; one A/A check came out "slower" (+1.08 ms, interval +0.25..+2.22): treat a lone interval
edge near 1 ms with care.

## Related

[A/B sets with a control and a control-again](ab-sets-control-again.md),
[PPSSPP gives booleans](ppsspp-booleans-hardware-numbers.md), skills/psp-build-test
