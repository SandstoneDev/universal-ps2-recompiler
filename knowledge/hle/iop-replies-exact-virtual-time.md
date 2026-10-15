# IOP replies must be exact and in step with virtual time

- **Category:** hle
- **Summary:** Whatever stands in for a game's IOP module must answer every RPC exactly as the original, at the same virtual time.
- **Applies to:** games with their own IOP sound or streaming modules
- **Evidence:** PC host, PCSX2, PPSSPP, real PSP-3000
- **Status:** confirmed

## Situation

Boot hangs at a preload, music never starts, or the game behaves differently on the PSP than on the host.

## Cause

The EE side reads the sound driver's state back every frame (loaded banks, play positions, track state). A stub that
answers zeros breaks initialisation; a model that advances on real time makes the replies depend on the PSP's speed.

## Rule

- Translate the module on the user's PC with the IOP recompiler, or model it; run it inside the RPC on the game
  thread, advanced by the virtual time since the last call.
- Fingerprint every reply (a hash logged every 1024 RPCs) and compare host, PPSSPP and PSP.
- Validate against PCSX2 field by field; keep IOP arithmetic exact (32-bit wrap, truncating division).
- Keep sample rendering separate from the state machine, so it can move to the Media Engine without changing replies.

## Evidence

PPSSPP vs PC host: reply fingerprints equal after 1,024, 2,048 and 2,458 RPCs and a bit-identical mix for 60 s. The
generated module was bit-exact with a hand model over 3,958 replayed RPCs (PC host).

## Related

skills/hle-authoring section 2, `audio/`, [Media Engine rules](../hardware/media-engine-rules.md)
