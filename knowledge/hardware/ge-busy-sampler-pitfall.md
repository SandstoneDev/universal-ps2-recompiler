# Measuring the GE: the busy sampler lies, use a serial probe

- **Category:** hardware
- **Summary:** Polling the GE's draw-sync state reports "drawing" while a list is merely open; measure GE time by replaying one captured frame with the CPU idle.
- **Applies to:** PSP-2000/3000 GE, any port that asks "is the GE the limit?"
- **Evidence:** real PSP-3000 (147,390 samples; serial probe per scene)
- **Status:** confirmed

## Situation

A sampler polling `sceGeDrawSync(1)` every 1 ms said the GE was busy 15-35 ms per frame, which suggested the GE was
the wall.

## Cause

The sampler never saw a stalled state; its "drawing" share equals the time a frame's display list is open, which is
the CPU's render phase, not GE work. PPSSPP never reports "drawing" at all, so the instrument looks plausible on one
side and empty on the other.

## Rule

- Measure real GE time serially: build one frame's list in a capture mode, then execute it with the CPU waiting,
  split by drawing category.
- Report the GE wait at the flip separately (time the CPU actually blocks on the GE).
- Treat any always-on GE busy figure as the list-open time until proven otherwise.

## Evidence

PSP-3000: interior real GE time 6.4 ms vs 15 ms from the sampler; a house + walk + drive route 12.5-12.7 ms vs 28 ms;
the same route with half-resolution textures 8.7 ms. GE wait at the flip 0.7-1.0 ms plus about 0.65 ms of mid-frame
resyncs. An asynchronous flip with a presenter thread: no gain (+0.43 ms, CI -3.0..+2.6). Post-processing passes on
the GE: 1.27 ms per frame.

## Related

[Where the frame goes](where-the-frame-goes.md), [GE back-end costs](ge-3d-backend-costs.md),
[Textures](texture-fetch-traffic.md)
