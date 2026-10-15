# GE display-list safety

- **Category:** hardware
- **Summary:** A malformed display list freezes the console; guard every list, keep caches coherent and key caches by content.
- **Applies to:** PSP GE, render HLE modules
- **Evidence:** real PSP-3000, PPSSPP
- **Status:** confirmed

## Situation

Hangs with no error screen, stale or garbage geometry, primitives that vanish near the screen edges.

## Cause

- The GE reports no errors on a retail console: a bad list hangs it.
- The GE reads memory behind the CPU's data cache.
- The GE drops primitives with a vertex outside its 0 to 4095 screen window; there is no X/Y clipping.
- GE state persists across lists.
- A cache keyed by the address of a game object drew stale data after the game reused the address for something else.

## Rule

- Guards: primitive counts in range, call nesting at most 2, every address range-checked, a start-up self-test of the
  hand encoder against the library's own output, and a run-option kill switch.
- Write display lists through the uncached alias; write back the data cache before a list references new textures or
  vertices; never rewrite memory an open list may still read; never mix cached and uncached data in one 64-byte line.
- Reset the full state at each list start. Keep geometry inside the guard band, clip the rest on the CPU, keep clip
  planes on.
- Key caches by content (size, counts, a hash), not by object address. Kick the GE in batches: every kick is a
  system call.

## Evidence

Real PSP-3000: about 1.4 ms of GE time per frame for about 10,000 triangles. Batching CALL words into the open list
and kicking every 16 meshes cut kicks from about 151,000 to 27,000 (PPSSPP count). Texture limits: 512 x 512 at most,
8 KB texture cache, 16-byte alignment.

## Related

skills/hle-authoring section 4, [Render boundary](../engines/render-boundary-device-driver.md)
