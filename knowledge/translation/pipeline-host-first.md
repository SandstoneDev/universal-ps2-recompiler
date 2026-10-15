# The pipeline: boot program to EBOOT, host first

- **Category:** translation
- **Summary:** Translate offline (R5900 -> C), replace the OS and hardware by name (HLE), reach the main loop on a PC host build first, then build for the PSP; everything game-derived is generated on the user's PC.
- **Applies to:** every port with PS2RC; PS2 games without run-time generated code
- **Evidence:** reference port (large 3D game): PC host, PPSSPP, real PSP-3000; converter timings on a desktop PC
- **Status:** confirmed

## Situation

A PS2 game is several MB of R5900 code plus overlays, IOP modules, VU microcode and the console's OS calls. The PSP
has a 333 MHz MIPS CPU and about 52 MB for everything: emulation is out of reach.

## Cause

Emulating the EE, VU1 and GS needs a host many times faster than the guest. A static translation runs the game's own
code natively; the parts the PSP lacks (EE kernel, IOP, GS/VIF/VU1, SPU2, CD/DVD) are replaced at function or driver
boundaries.

## Rule

1. **Analyse**: boot program from `SYSTEM.CNF`, overlays (their own units and a lookup registry; static constructors
   sit after `.text`), IOP module list, VU programs, Sony library names by signature. Check for run-time generated
   code: the code region must stay byte-identical to the file during boot and play (PCSX2 memory compare).
2. **Translate**: one guest function = one C function; width analysis (most 64/128-bit integer ops are really
   32-bit), liveness, ABI mode for ordinary functions, exact mode for the few non-ABI ones.
3. **HLE by name**: EE kernel (threads, semaphores, alarms, interrupts at safe points), Sony libraries, SIF RPC to an
   IOP model or a recompiled IOP module, disc by LSN, memory card as files; renderer at the engine's driver boundary.
4. **Host build first**: the same C + HLE on x86 with deterministic virtual time; gate every change on identical
   counters (milestone at a fixed virtual time, two runs guest-identical). Only then the PSP.
5. **PSP build**: psp-gcc, the runtime, the kernel helper module, the GE back-end; PPSSPP for booleans, the PSP for
   numbers.
6. **Distribution**: the converter runs steps 1-5 on the user's PC from the user's own disc. Nothing game-derived
   ships.

Test ladder, cheapest first: decoder vs objdump -> synthetic programs bit-exact vs PCSX2 -> real compiled functions
(ABI-observable state) -> VU0 vectors -> mutation (each rule switched off must turn named tests red) -> host gate ->
PPSSPP booleans -> hardware numbers.

## Evidence

Reference port: about 3,200 lines of HLE reached the main loop on the host in 2.8 s host time, deterministic run to
run; host and PSP milestone virtual times agreed (40.157 vs 40.156 s). Code size: v4 back-end 3.84x the guest code,
final generation 2.31x (11.9 MB for about 5 MB of guest code). Converter on a desktop PC: disc image -> PSP folder
in 6.4 to 9 minutes (translation 128-154 s with 4-5 processes, 157 compile units 132 s, link 1-2 s, staging 3.8 GB
10-18 s); a native Windows psp-gcc produced objects byte-identical to the Linux toolchain. Compile jobs need up to
445 MB each: cap jobs by free RAM (700 MB per job); too many jobs hung a 7 GB WSL machine.

## Related

[Boot to the first blocker](boot-to-first-blocker.md), [Function discovery](function-discovery-jump-tables.md),
[Translator levers](backend-levers-measured.md), `docs/PORTING_GUIDE.md`, skills/ps2rc-translate
