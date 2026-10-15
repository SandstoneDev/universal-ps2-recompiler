# Log writes and disc reads as frame-time spikes

- **Category:** hardware
- **Summary:** Keep a frame-time histogram; buffer the log and read the disc asynchronously, answering the game's polls.
- **Applies to:** PSP-2000/3000, any port
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

Average frame time was acceptable but the game stuttered: single frames took two or three times the median.

## Cause

Synchronous work on the game thread: log writes to the memory stick, synchronous disc reads, the game's own streaming
loads, first-use conversions of textures or meshes.

## Rule

- Track a 1 ms histogram of frame times and the top sources of the slowest frames.
- Buffer the log in the main loop and commit it from a watchdog thread; boot, milestones, crashes and exit still
  commit at once.
- A disc reader thread at a priority just above the game thread; answer the game's read, status and sync polls as
  the PS2 drive would.
- Never dump images or per-line debug output to the card on hardware.

## Evidence

Real PSP-3000: one in-frame log write took 107 ms; buffered logging moved log time on the game thread from 0.60 to
0.00 ms per frame. With the async reader: mean 68.0 to 64.8 ms, 99.9th percentile 183 to 119 ms, disc time 3.16 to
0.04 ms per frame.

## Related

[Open-file limit](memory-stick-open-file-limit.md), [File size recorded on close](fat-size-recorded-on-close.md), `hle/core/hle_hitch.c`
