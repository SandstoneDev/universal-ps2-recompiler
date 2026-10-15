# A streaming budget below the working set thrashes every frame

- **Category:** hardware
- **Summary:** Size the game heap as resident data + streaming budget + 1.6 to 2 MB headroom, from load counters.
- **Applies to:** games that stream models and textures into a fixed budget
- **Evidence:** PC host (load counters), real PSP-3000 (time)
- **Status:** confirmed

## Situation

After shrinking the game heap so the port fits, the game loaded data in every frame, even standing still, and frame
time rose by several milliseconds.

## Cause

The streaming budget was below the working set of the scene: the loader evicted data it needed again in the next
frames and reloaded it (and converted it again for the GE).

## Rule

Measure the loader's busy share and reload counts on the host first. Every MB of heap given back becomes budget. Keep
1.6 to 2 MB of headroom; reduce the budget through the game's own configuration file (served as a same-size
replacement) rather than by patching the allocator.

## Evidence

PC host: with a budget about 4.5 MB below the original, the loader read in 100 % of frames and reloaded the same
models 10 to 23 times in 45 s. Real PSP-3000: about 9.1 ms per frame (4.75 ms conversion + 3.9 ms synchronous
reads). Giving back 1.5 MB brought the loader to 32 to 38 % busy and saved about 7.5 ms per frame.

## Related

[Free memory on the 64 MB models](free-memory-64mb-models.md), skills/psp-performance
