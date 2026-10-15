# Off-screen passes the port never shows can double the frame

- **Category:** engines
- **Summary:** Find render passes (mirrors, reflections, render-to-texture, batch renderers whose output the HLE drops) that still run in translated code; skipping them was the biggest single scene win.
- **Applies to:** engines that render a scene twice (mirror or reflection rasters) or prepare draw data the port's GE back-end never consumes
- **Evidence:** real PSP-3000 (A/B with controls, profiler zones), identical screenshots
- **Status:** confirmed

## Situation

One indoor scene ran at 53 ms per frame while similar rooms ran near 35 ms. The GE was idle most of the frame.

## Cause

A mirror in the room made the engine render the whole room a second time into an off-screen raster, through the slow
translated PS2 pipeline - every character drawn twice. The port's GE back-end never displayed that raster. The same
pattern held for several batch renderers whose packets the HLE discards.

## Rule

- Per scene, list the passes the engine runs and what the GE back-end actually draws; a pass with no visible output
  in the port is a candidate.
- Skip it at the engine's own entry (a hook that returns early), keep the bookkeeping the game reads, and compare
  screenshots before and after.
- When a skipped renderer drew something visible (shadows, particles, trails), draw those entry types natively.
- Make each skip a run option and verify on hardware with a control and a control-again.

## Evidence

PSP-3000: skipping the mirror pass, interior 53.1 -> 34.3 ms (-18.4 ms, CI -22.0..-16.3), whole route -12.6 ms,
outdoors unchanged, pictures identical. Skipping batch renderers and immediate-mode passes the HLE drops: -10 ms per
frame. Skipping an invisible vegetation manager: -1.9 ms. Native replacements of the dropped effects cost about
0.34 ms per frame by day.

## Related

[Render boundary at the device-driver layer](render-boundary-device-driver.md),
[Where the frame goes](../hardware/where-the-frame-goes.md), skills/psp-performance
