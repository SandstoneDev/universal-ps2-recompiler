# The 64 MB mode is a request: check it at start; use the volatile 4 MB carefully

- **Category:** hardware
- **Summary:** The EBOOT's memory-size flag only asks the custom firmware for the extended user memory; detect the 24 MB fallback at start and exit with a message; the volatile 4 MB block can hold GE lists, textures and the movie decoder if it is locked and released correctly.
- **Applies to:** PSP-2000/3000 with custom firmware, large-memory homebrew
- **Evidence:** real PSP-3000 (free memory per boot step, stack addresses), PPSSPP for the fallback path
- **Status:** confirmed

## Situation

A build that had run for weeks suddenly failed to allocate its guest RAM window on the same console.

## Cause

The firmware honours the memory-size flag only when its own high-memory setting is not off. It read its settings
from internal flash instead of the memory stick because the stick mounted slowly - the stick's FAT had been damaged by
interrupted USB copies - and the stored setting there was off: silently about 24 MB. The program cannot enlarge the
partition after start.

## Rule

- At start, log free memory and the largest free block before any big allocation, and the main thread's stack
  address. If free memory is 24 MB or less, show "extra memory is off - check the firmware setting and the memory
  stick" and exit cleanly instead of crashing. Keep a test switch that fakes the low value (testable in PPSSPP).
- Budget from the device, never from PPSSPP (it reports about 5 MB more).
- The volatile 4 MB block: lock it (this takes a power lock), touch every page before trusting its size, release it
  before any system dialog; while it is locked the power switch and sleep wait, and a switch moved while locked fires
  at unlock. PPSSPP has no power lock (the call fails there).
- Repair a damaged memory stick (on the PC, or format on the PSP after a backup) before chasing memory bugs.

## Evidence

PSP-3000, 64 MB mode: 35,571 KB free at start; minus the 14 MB EBOOT (12.5 MB code) and the 28.4 MB guest window ->
7.0 MB; minus a 2.8 MB audio block -> 4.2 MB; 2.8 MB during a movie (1.3 MB decoder block); the profiler capture
takes about 900 KB more. PPSSPP: 40,685 KB at the same point. Moving GE lists, the texture arena and the movie decoder
into the volatile block freed about 4.1 MB; the game heap grew by 4,288 KB, and with a larger streaming budget that
saved 3.8 ms per frame (streaming busy 60 -> 38 %). 6.8 MB of translated functions never ran in a profiled session
(headroom for future paging).

## Related

[Free memory on the 64 MB models](free-memory-64mb-models.md), [Streaming budget](streaming-budget-thrash.md),
[Deploy with md5](../workflow/deploy-md5-verify.md)
