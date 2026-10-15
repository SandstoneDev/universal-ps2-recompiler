# Open-file limit on the memory stick

- **Category:** hardware
- **Summary:** Keep at most about 8 files open; on an open failure close the least recently used file and retry.
- **Applies to:** PSP-2000/3000 memory stick; PPSSPP allows more open files
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

For several builds the session log stopped at the same line while the game kept running to the end.

## Cause

Once the game's data files were open, the log's own open failed: the memory stick driver allows only a small number
of open files. PPSSPP allows more, so it never showed the problem.

## Rule

- Keep game files open in a small LRU cache (at most 8 entries) and count open failures.
- On any open failure other than "not found", close the least recently used file and retry.
- Give the log the same recovery.
- Opening is expensive too: keep files open; never add a second card request per streaming read.

## Evidence

Real PSP-3000: the log stopped after the same line in four builds; fixed by an LRU of 8 (it was 10) with retry.
`sceIoOpen` took 17 to 34 ms; sequential reads ran at about 15.5 MB/s.

## Related

[The file size is recorded on close](fat-size-recorded-on-close.md), [Log writes and disc reads as spikes](hitches-log-and-disc.md)
