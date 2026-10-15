# Sound: the IOP driver in lockstep with virtual time, samples rendered on the Media Engine

- **Category:** hle
- **Summary:** Run the game's IOP sound driver (recompiled or modelled) on the game thread in step with virtual time, mix through an integer SPU2 model, stretch the output when the game runs below real time, and move sample rendering to the Media Engine.
- **Applies to:** games with their own IOP sound driver and SPU2 voices; PSP-2000/3000 with kubridge
- **Evidence:** PC host and PPSSPP (determinism, bit-exact mixes); real PSP-3000 (costs)
- **Status:** confirmed

## Situation

The sound driver runs on the IOP (a MIPS R3000) and talks to the game over SIF RPC; the game waits for exact replies
at exact times. On the PSP the audio first cost 7.5 ms per frame on the game thread.

## Cause

The game's logic depends on the driver's replies (voice states, stream positions). A model that answers
approximately, or at other times, changes the game. Mixing in floating point or on the main core costs CPU the frame
does not have.

## Rule

- Keep R3000 arithmetic (32-bit wrap, its divide-by-zero results); turn IOP threads into resumable state machines on
  their original semaphores; copy, handle, then service in the IOP's order. Prefer generating the module from the
  user's disc with the IOP recompiler (`ps2rc/iop`).
- Step the driver with virtual time on the game thread: replies become deterministic and equal on host and PSP
  (fingerprint them every 1,024 RPCs).
- SPU2 model integer only, ADPCM bit-exact; a voice limit is allowed only if the IOP-visible state stays exact.
- The game runs below real time on the PSP: play the output through a time-stretch (WSOLA) instead of dropping it.
- Media Engine: the main core keeps the driver state; the ME renders samples from a small command ring. Qualify in
  three steps (heartbeat, shadow mode comparing results, live); keep the main-core path behind a run option.
- Prove "no sound" bugs with data (a stream trace), not by ear.

## Evidence

Host: replies matched PCSX2 save states field by field; 48 kHz mix bit-identical host vs PPSSPP; a 16-voice limit
kept replies identical (output differed in 0.1 % of frames by at most 4 LSB). PSP-3000: bit-identical speedups of the
driver loop -5.7 ms per frame; samples on the ME -5.8 ms per frame and x1.073 game speed, shadow mode 0 mismatches
over 53,852 blocks. Dropping the IOP stream buffers saved 540 KB (driver total about 2.4 MB, of which 2 MB is the SPU
RAM image). A "missing voices" report was a cutscene silent by design for its first 46.8 s.

## Related

[IOP replies must be exact](iop-replies-exact-virtual-time.md), [Media Engine rules](../hardware/media-engine-rules.md),
`audio/`, `ps2rc/iop/`
