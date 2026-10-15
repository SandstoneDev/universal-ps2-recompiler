# Reference runs: find the first divergence

- **Category:** hle
- **Summary:** Run the original in PCSX2 and the port to the same point; the first register or memory difference is the bug.
- **Applies to:** any behaviour difference between the port and the original
- **Evidence:** PCSX2 (reference), PC host
- **Status:** confirmed

## Situation

The port does something different from the original and the cause is not visible in the fatal line or the log.

## Cause

Guessing from the symptom fixes the wrong layer. The original running in PCSX2 is the ground truth for registers and
memory at any point.

## Rule

1. Bring both to the same point: a breakpoint at the function's entry in PCSX2, a trace or log line in the port.
2. Record the registers and the memory the function reads, on both sides.
3. Run to the return; record the result and the memory written.
4. A wrong entry state means the caller (or its translation); a correct entry and a wrong result means the function or
   its HLE.
5. Compare against PCSX2's interpreter and its recompiler where floating point is involved: they can disagree.

## Evidence

PCSX2 over PINE: bit-exact tests of synthetic programs and of a VU0 program over 11,264 vectors (0 differences
against the interpreter). The BIOS comes from the user's own console.

## Related

skills/hle-authoring section 5, `ps2rc/oracle/pcsx2.py`
