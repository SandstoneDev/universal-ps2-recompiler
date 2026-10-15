# Function discovery and jump tables

- **Category:** translation
- **Summary:** Strong starts cut functions, weak starts do not; recover jump tables backwards from the jr to its guard.
- **Applies to:** translating compiled PS2 programs
- **Evidence:** PC host (a program with symbols as the check)
- **Status:** confirmed

## Situation

"Functions" made of case labels, functions that end in the middle of nowhere, a fatal dispatch error at run time, or
a start-up loop that runs once and returns.

## Cause

A missed jump table leaves its case bodies unowned; loop heads reached by `j` registered as function starts split real
functions; the bound check of a table sits in many places (after a shift, on a register copy, in a delay slot, far
above, or nowhere).

## Rule

- Strong starts (entry point, explicit seeds, direct call targets) cut functions; weak starts (tail calls, data
  pointers, gaps) do not; functions may share code.
- A `j` into a function's own body is a loop, not a call.
- Recover tables along the unique-predecessor path with value numbering; accept a guard only if its in-range side
  reaches the `jr`; without a guard take the run of code pointers.
- Check discovery on a program that has symbols (a homebrew or a debug build) before trusting it.

## Evidence

PC host: 300 to 309 tables recovered and 8 fragments to 0 after the backward walk; on a program with symbols, recall
0.9998 and precision 0.9979.

## Related

`ps2rc/analysis/functions.py`, skills/ps2rc-translate
