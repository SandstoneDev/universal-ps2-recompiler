# Media Engine rules

- **Category:** hardware
- **Summary:** The second CPU pays off for audio, but only with explicit cache handling, no libc, a sleep handler and step-wise qualification.
- **Applies to:** PSP-2000/3000 with custom firmware and kubridge
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

Moving work to the Media Engine (ME) can save milliseconds per frame, and can also hang or switch off the console.

## Cause

The ME's caches are not coherent with the main CPU; an exception on the ME is a silent hang; the operating system's
own ME driver and decoders expect to own it; PPSSPP does not emulate it.

## Rule

- Start it through a kernel call (kubridge) that installs a reset stub; accept it only after a heartbeat ticks.
- Producer: write, write back, sync, publish. Consumer: invalidate, read. Flags and counters uncached.
- ME code calls no libc (compilers turn loops and struct copies into memcpy/memset calls): check by disassembling it.
- Park it on suspend; replace the suspend handler from the kernel helper module.
- Taking it over stops the firmware's video and ATRAC decoders: start it after the movies.
- Qualify in steps: heartbeat, shadow mode (both CPUs compute and compare), live; gate it with a run option and keep
  the main-CPU path.
- Judge an offload by the main CPU's total frame time.

## Evidence

Real PSP-3000: audio rendering on the ME saved about 5.8 ms per frame (shadow mode: 0 mismatches). Moving more render
work there once shrank the moved parts but grew the main CPU's game code from 59.9 to 70.9 ms (bus contention
suspected, Unknown). The ME's CP0 Count read a constant until written, then ran at about 454 MHz.

## Related

`hle/psp/hle_me.c`, `psp_exc/exc_me.c`, skills/psp-performance section 4
