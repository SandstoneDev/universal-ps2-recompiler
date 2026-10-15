# An on-device profiler: zones, per-thread clocks, hashed sampling, counters from a kernel thread

- **Category:** hardware
- **Summary:** Wrap translated functions in zones with one clock per guest thread, sample short hot functions with a hashed 1-in-N choice, keep everything integer, read the hardware counters only from a kernel thread, and report the profiler's own cost.
- **Applies to:** PSP builds of translated games; the kernel helper module
- **Evidence:** real PSP-3000; PPSSPP (crash behaviour); PC host (line-level counts)
- **Status:** confirmed

## Situation

Early per-call costs were off by 100-1000x for some short functions; a counter read killed a thread; PPSSPP crashed.

## Cause

A fixed 1-in-N sample aliases with call patterns that repeat with the same period. Coroutine switches leak time into
the wrong zones unless each guest thread has its own clock. Floating-point timers run in the game thread's guest FPU
mode and distort costs. One word of the hardware counter block is not safe to read. PPSSPP does not emulate the
counters.

## Rule

- Zones: rename the generated function at build time and wrap it; generated callers stay unchanged; account per
  caller edge, recursion once.
- One clock per guest thread; integer microseconds only.
- Short hot functions: hashed 1-in-16 or 1-in-64 sampling, never a fixed stride.
- Hardware counters: a kernel thread reads them in 50 ms windows, never resets them, never reads the one unsafe word
  (it killed the thread on a PSP-3000); detect the emulator first; stop the thread and clear the counters before the
  module unloads.
- Log the profiler's cost in every run and keep profiling in its own A/B folder.
- Parse explicit fields (video rate, build) from logs: a tool that read a 50 Hz log as 60 Hz overstated fps by 20 %.

## Evidence

PSP-3000: instrument cost 3.2-4.4 ms per frame; counter reads through kubridge about 65 us each; counters showed CPI
2.6-2.9 and about 50 % memory stalls. Host line-level profiles (counter per generated C line attributed through debug
info) are reliable in totals, noisy per function.

## Related

[Where the frame goes](where-the-frame-goes.md), [PPSSPP gives booleans](../workflow/ppsspp-booleans-hardware-numbers.md),
`hle/psp/hle_prof_psp.c`, `hle/core/hle_prof.c`
