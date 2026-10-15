# Boot to the first blocker, strict

- **Category:** translation
- **Summary:** Run strict, fix the first fatal line, look past it only with named experiment switches that never become defaults.
- **Applies to:** the host build of a new game
- **Evidence:** PC host
- **Status:** confirmed

## Situation

A new game stops early on the host with a fatal line, and it is tempting to stub everything until it runs.

## Cause

Unknown RPC servers, syscalls and hardware accesses are fatal by design: they show what is not replaced yet. Silent
stubs hide the real problem until much later, where it is far harder to find.

## Rule

- Read the fatal line and its call chain; locate the layer; fix with one tool.
- To see what lies behind a blocker, add a named experiment switch (for example answering every VU0 micro call with a
  neutral result), look at the next blockers, then implement the real thing and remove the switch.
- Record each blocker and each try; after three identical failures stop, compare with a reference run, ask the user.
- Gates after every change: fixed milestone, zero escapes, two runs guest-identical.

## Evidence

PC host: about 3,200 lines of HLE reached the main loop of a large 3D game in 2.8 s of host time; one experiment switch
exposed three hidden bugs (a scratchpad DMA chain, overlay constructors, missed jump tables).

## Related

skills/ps2rc-translate section 3, [Reference runs](../hle/reference-run-first-divergence.md)
