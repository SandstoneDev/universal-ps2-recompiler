# Where a frame goes on the PSP: the main CPU is the wall

- **Category:** hardware
- **Summary:** In a large translated 3D game the main CPU (memory-bound translated code) sets the frame time; the GE and the Media Engine's bus traffic were not the limit; reach 30 fps by doing less game work per frame.
- **Applies to:** PSP-2000/3000 at 333 MHz, large translated games
- **Evidence:** real PSP-3000 (profiler zones, hardware counters, serial GE probe, A/B sets)
- **Status:** confirmed

## Situation

After the obvious levers, scripted runs still took 55-62 ms per frame outdoors. Each new idea was a few percent.

## Cause

The CPU retires about 161 M instructions per second (CPI 2.6-2.9); about half of the busy cycles stall on memory
(about 80 cycles per miss); instruction-cache misses (11.7-14 per 1000 instructions) outnumber data-cache misses
(5.6-8). Translated game logic alone is 5.4-5.8 M instructions per frame. The profile is flat.

## Rule

- Profile by zones on the device before choosing levers; expect a flat profile.
- Do not chase the GE until a serial probe shows it (see [Measuring the GE](ge-busy-sampler-pitfall.md)).
- Moving work to the Media Engine helps when it removes main-core work (audio), not when it moves work around.
- Uncached single-word stores from the ME were not what slowed the main core here; judge by the main core's total.
- Host instruction counts are hypotheses: three levers that cut render-list calls by 40 % on the host gave no
  measurable change on the PSP.
- The remaining large levers change the game (density, draw distance, detail): offer them to the user as options.

## Evidence

PSP-3000, scripted runs, ms per frame:

| Part | Driving | On foot |
|---|---|---|
| Whole frame | 61.9 | 55.7 |
| 3D back-end (hook) | 17.4 | 17.2 |
| Render-list walk (translated) | 14.1 | 13.3 |
| Game logic (translated) | 14.6 | 13.2 |
| Effects / HUD | 9.2 | 8.5 |
| HLE / system | 4.1 | 2.7 |
| Streaming | 2.4 | 0.7 |

Real GE time 6.4 ms (interior) to 12.7 ms (route); waiting for the GE at the flip 0.7-1.0 ms. ME writing 61 MB of
uncached GE words per run: game-logic zone 39.69 vs 39.61 ms (no cost); an earlier "+11 ms" was hook work counted in
another zone. Floor with every visual cut and zero traffic: 50.6 ms (19.8 fps) - 30 fps outdoors would need the
translated code about 1.5-2x faster. One moving actor costs about 1 ms (AI, animation, draw); density 50 % saved
18.6 ms. Speed-adaptive far clip while driving -2.7 ms; reusing the camera's collision cast -1.5 ms.

## Related

[Memory-bound CPU](memory-bound-cpu-icache.md), [Off-screen passes](../engines/offscreen-passes-double-work.md),
[Reference port results](../workflow/reference-port-results.md), skills/psp-performance
