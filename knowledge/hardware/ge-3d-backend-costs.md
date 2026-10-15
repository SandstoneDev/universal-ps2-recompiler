# GE 3D back-end: batch on the CPU side, key caches by content

- **Category:** hardware
- **Summary:** Convert the game's vertex streams once per mesh into GE sub-lists, cache them by content, batch the per-mesh CPU work, write commands into the open list and kick rarely; per-mesh CPU cost on the PSP is 4x PPSSPP's.
- **Applies to:** a GE back-end replacing a PS2 renderer at its driver boundary (VU1 vertex streams), PSP-2000/3000
- **Evidence:** real PSP-3000 and PPSSPP timings, pixel comparisons
- **Status:** confirmed

## Situation

The 3D back-end first cost 30 ms per 3D frame on the PSP and about a quarter of that in PPSSPP; after streaming,
some meshes drew stale geometry.

## Cause

- The back-end's own 20 KB of code and its tables evict the game's code and data from the 16 KB caches between
  pieces of game code; PPSSPP has no cache model.
- The game reuses the same resource addresses for different meshes after streaming: a cache keyed by address returns
  the old mesh (and a re-bake can overrun its block, a GE hang risk).
- Each GE kick is a system call.

## Rule

- Convert once per mesh into a GE vertex block plus a sub-list (CALL); key the cache by content, evict by window,
  not single victims.
- Batch per-mesh preparation at the flush, not at hook time (cold I-cache per call).
- Write CALL words straight into the open list; kick every 16 meshes.
- Camera-relative matrices on the CPU (the GE keeps about 24-bit floats); 16-bit depth: the near plane is the lever.
- Lighting as GE state instead of re-baking vertices; GE near-plane clipping; the CPU clipper only for primitives
  straddling the guard band (Y span of 2730.6 px or more misrenders).
- Skin weights must sum to exactly 128 (u8) or 32768 (u16): the GE does not normalise; at most 8 bones per draw.
- Mirror and reflection passes reuse the camera: include the view matrix in any camera cache key.
- At start-up, compare your own command encoder's words against the PSPSDK library's for every state sequence; on a
  mismatch keep the feature off.

## Evidence

PSP-3000: per mesh 55 us vs 13.5 us in PPSSPP (texture lookups x6); hook 30.0 -> 13.6 ms per 3D frame (fast integer
converter, GE lighting, GE clipping, window eviction: host conversions 552 k -> 2.5 k); GE kicks 151 k -> 27 k (PPSSPP
count); per-atomic preparation at hook time +33 % (7.59 vs 5.69 ms) against batched. 3D lists built on the Media
Engine: -3.2 ms. Later per-draw costs: about 320 us per lit or skinned mesh, 23 us per static building mesh; each
system-clock read 456 ns (about 540 per frame).

## Related

[GE display-list safety](ge-display-list-safety.md), [Render boundary](../engines/render-boundary-device-driver.md),
psp-developer skill (GE rules), `hle/psp/`
