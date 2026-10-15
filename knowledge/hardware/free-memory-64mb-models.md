# Free memory on the 64 MB models

- **Category:** hardware
- **Summary:** Plan with about 51 MB for the program in large-memory mode; PPSSPP reports about 5 MB more than the device.
- **Applies to:** PSP-2000/3000 with custom firmware large-memory mode (other 64 MB models: Unknown)
- **Evidence:** real PSP-3000, PPSSPP
- **Status:** confirmed

## Situation

Memory budgets taken from PPSSPP did not fit on the device.

## Cause

PPSSPP reports a constant extra amount of free memory compared with the device. The 32 MB PSP-1000 cannot provide
the large user partition the runtime needs.

## Rule

- Take memory budgets only from hardware logs; log free memory and the largest free block after every boot step.
- Allocate the guest RAM window as one block early, with guard areas.
- Code size is RAM: the translated code competes with the game's heap.
- Reuse the guest's own code region (never read as data) for display lists, textures and vertex caches.

## Evidence

Real PSP-3000: about 32,000 KB free at start with a 19 MB program; a 28,416 KB guest window left about 3,600 KB.
PPSSPP showed about 5,120 KB more free memory for the same EBOOT. Shrinking the translated code from 20.9 to 14.2 MB
freed about 8.5 MB on the device (projected).

## Related

[Streaming budget thrash](streaming-budget-thrash.md), skills/psp-performance
