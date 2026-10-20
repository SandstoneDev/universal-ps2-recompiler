---
name: psp-performance
description: "Make a recompiled PS2 game fit and run faster on the PSP with PS2RC (through this kit): memory budget of the 64 MB models, game heap and streaming budget, code size and layout (the I-cache), back-end levers, GE costs, Media Engine offload, frame-time spikes (hitches), clocks, and density / draw-distance levers that change the game (only with the user's consent). Use when the port runs on the user's PSP but is slow, stutters, runs out of memory, or when the user asks how to make it faster."
---

# Speed and memory on the PSP

Measure on the user's PSP only (psp-build-test section 5). Profile before you optimise; one lever per A/B set.
**Performance numbers (fps, frame time, CPU or GE milliseconds, free memory) are trusted only from the real console.**
PPSSPP, PCSX2 and the PC host build answer correctness questions (boots, renders, this log line appears) - booleans
and hints, never a speed or memory figure; do not report their numbers as performance and do not choose a lever by
them.

## 1. Know where the frame goes

Typical result for a large 3D game: the CPU is the limit, and it is **memory-bound**: CPI around 2.6-2.9, about half
the cycles stalled on memory, instruction-cache misses (12-13 per 1000 instructions) dominating data-cache misses
(6-7). The 16 KB I-cache cannot hold the megabytes of code a frame touches. The GE needed about 1.4 ms for about
10,000 triangles - it is rarely the limit. See `knowledge/hardware/memory-bound-cpu-icache.md`.

Consequences:

- **Code size and layout are speed.** Back-end levers that remove code (ABI mode, base-register masking, dead save
  removal, branchless clamps) were worth 5-6 % each on hardware; marking never-run functions cold and ordering hot call
  chains together about 2 %. Smaller is not always faster: `-Os` was 41 % slower; "smaller" flag sets were slower too.
- Hand-optimised C of the hottest functions gained little (the profile is flat). Replacing work at an API level and
  moving work to the Media Engine gained much more.
- Never trust an estimate: build it, run an A/B set.

## 2. Memory (64 MB models, large-memory mode)

About 51 MB are available to the program. The guest RAM window, the translated code, HLE buffers and the game's heap
share it.

- Code size is RAM: every lever that removes code frees memory.
- The guest's code region is never read as data by most games (verify statically and with PCSX2 memory breakpoints);
  the translated program does not need it, so it is reused for display lists, textures and vertex caches.
- **Game heap**: many games take "end of RAM minus end of BSS minus stack" with one allocation at start-up. Patch that
  one constant to the runtime's RAM end (pack text patch) and size the streaming budget with the game's own
  configuration (served as a same-size replacement file). Heap = resident data + streaming budget + 1.6 to 2 MB
  headroom. A budget below the working set makes the loader evict and reload the same data every frame (in the
  reference port: about 9 ms per frame, even standing still) - `knowledge/hardware/streaming-budget-thrash.md`.
- Log free memory after every boot step; PPSSPP's numbers are about 5 MB too optimistic.

## 3. Frame-time spikes are a separate problem

Keep a frame-time histogram and the top sources of the slowest frames. Usual sources: synchronous log writes (one
in-frame write cost 107 ms), synchronous disc reads, the game's own streaming loads, first-use texture or mesh
conversions. Fixes: buffer the log and commit it from another thread; read the disc asynchronously answering the
game's polls the PS2 way; convert at load time with a large enough cache (measure before building install-time
pre-converted files - in the reference port they would not have paid).

## 4. Media Engine

Offloading sample rendering to the ME saved about 6 ms per frame. Rules: start it through a kernel call (kubridge);
its caches are not coherent with the main CPU (write back, sync, then publish; small flags uncached); no libc calls
in ME code (check by disassembly); park it on suspend (the kernel helper replaces the sleep handler); taking it over
stops the firmware's video and ATRAC decoders - start it after the movies; qualify it on hardware in three steps
(heartbeat, shadow mode comparing results, live). Judge an offload by the main core's total frame time: moving more
work there once cost as much on the main core as it saved. `knowledge/hardware/media-engine-rules.md`.

## 5. Levers that change the game - ask the user

Fewer people and vehicles, a shorter draw distance, lower detail, skipping work the port does not display, simulating
far entities less often: these were the biggest single gains (tens of ms) but they change the user's game. Present the
trade-off, make each one a run option, default to the original behaviour unless the user chooses otherwise.

## 6. Clock

Ship at 333 MHz (the stock maximum) by default. An overclock is a player option, set only through the custom
firmware's own clock call at the first line of `main()`, with a crash-safe state file that steps down after a crash;
365 MHz gave -8.6 % frame time on one PSP-3000. Writing the PLL register yourself switched that console off every
time. The bus and the GE do not speed up with the CPU. Unknown on other consoles: do not promise it.
`knowledge/hardware/overclock-cfw-api-only.md`.

## 7. Before you optimise further

- Look for off-screen passes the port never shows (a mirror pass doubled one scene: -18.4 ms when skipped) -
  `knowledge/engines/offscreen-passes-double-work.md`.
- Measure GE time with a serial probe, not a busy sampler - `knowledge/hardware/ge-busy-sampler-pitfall.md`.
- Texture cost is fetch traffic: half resolution or generated mipmaps (-3.1 ms), not pre-converted files -
  `knowledge/hardware/texture-fetch-traffic.md`.
- Pacing that never forgives lag makes the game too fast or too slow - `knowledge/hle/virtual-time-pacing.md`.
- Decide with the one-run interleaved A/B where the option switches at run time -
  `knowledge/workflow/one-run-interleaved-ab.md`. Honest targets: `knowledge/workflow/reference-port-results.md`.

## References

`docs/PORTING_GUIDE.md` sections 13-14, `knowledge/hardware/`, `knowledge/translation/`.
