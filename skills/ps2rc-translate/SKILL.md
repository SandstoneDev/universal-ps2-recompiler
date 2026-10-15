---
name: ps2rc-translate
description: "Translate a PS2 game's EE program to C with PS2RC (through this kit) and boot it on the PC host first: function discovery, jump tables, non-ABI exemptions, width analysis, back-end variants (v0 exact first), the prepare step, the host harness, virtual time, gates, and the strict boot-to-the-first-blocker loop. Use when the pack's [id]/[memory] are filled and the user wants to translate, build or run the host build, or when a host run stops with a fatal line, a dispatch error, a deadlock or a crash backtrace."
---

# Translate and boot on the PC

The host build compiles the same generated C and the same HLE with the PC's gcc. It finds most problems in seconds,
and a crash backtrace there is the guest call chain. Boot on the host first; go to the PSP only when the host reaches
the main loop with the gates at zero.

## 1. Translate

```
python3 ps2rc/pipeline/translate.py --pack <pack>              # defaults from the pack's [translate]
bash mk/build.sh --pack <pack> host                            # prepare + compile the host harness
bash mk/run_host.sh --pack <pack> 120 0 first                  # run up to 120 s, verbosity 0, tag "first"
```

Ask the user before the first translation and build (minutes; the work directory grows by gigabytes). On Windows the
shell steps run in WSL; use at most the job count the user allowed.

- Start with `variant = "v0"` (exact everywhere). Switch to the ABI variants (`v4`, `v5s*`) only after v0 boots;
  each variant must reach the same milestones, guest-identical.
- **Function discovery** (`ps2rc/analysis/functions.py`) seeds from the entry point and call targets (strong starts),
  plus tail calls, data pointers and gaps (weak starts; functions may share code). Save the set once
  (`functions = "{work}/functions.pkl"`) so the user's machine does not recompute it.
- **Jump tables** are recovered backwards from the `jr` to the guard compare. A missed table shows up later as
  "functions" made of case labels and a fatal dispatch error at run time.
- **Non-ABI functions** (`ps2rc/analysis/abi.py`): code entered by `j` that reads registers the caller set, callee-saved
  registers left changed, `eret` handlers, thunks with the target in `t9`, the return address used as data. Typically
  a dozen in ten thousand; they are translated exact (`non_abi`, `exempt = true`).
- **Translate again whenever the hook list changes**: hooked functions get full argument liveness at translation time.

## 2. The prepare step and the host harness

`mk/build.sh` renames hooked functions to `fn_<addr>__guest`, inserts a safe point at loop back-edges (without them
polling loops never see interrupts), applies the trap set, zones and text patches, and generates the dispatch table.
`mk/run_host.sh` writes into the run directory: `host_<tag>.log`, `alias_<tag>.txt` (plain accessors that saw a
hardware address - must be empty), `mmio_<tag>.txt` (functions that reached the register model), `disc_<tag>.txt`
(disc files read). Useful harness options (after the tag): `--mainloop-limit N`, `--max-seconds S`, `--mmio-profile`,
`--alias-report`, `--disc-usage`, `--watch`, `--sample`, `--pad` (scripted input), `--memcard DIR`, `--prof-summary`.

**Virtual time.** The game never sees the host clock: time advances by fixed costs (syscall, register access,
back-edge, file read by size) and jumps to the next event when every guest thread waits. Two runs of the same build
are guest-identical - that is your regression test.

## 3. Boot to the first blocker (the loop)

1. Run strict. Unknown RPC servers, unknown syscalls and unexpected hardware accesses are fatal by design.
2. Read the fatal line and its call chain (grep the log; never read megabytes of it).
3. Locate the layer (skills/ps2rc-port section 1): translator bug, missing core HLE, missing pack hook, platform.
4. To see further, add a *named* experiment switch that steps over the blocker (for example answering every VU0 micro
   call with a neutral result), look at the next blockers, fix them, then implement the real thing and remove the
   switch. An experiment never becomes a default.
5. Record each blocker in `PORT_STATE.md` (symptom, layer, tries). Third identical failure: circuit breaker
   (ps2rc-port section 6).

Lessons that each cost a debugging session in the reference port:

- a `syscall` reads `a0`-`a3`, `t0`-`t3` and `v1`: all live;
- 64-bit values through wrappers (a double returned by a tail call, a 64-bit timer) must stay wide across calls;
- the EE decodes some instructions with non-zero "must be zero" fields as their base operation; the decoder must too;
- an overlay's static constructors must be discovered from its constructor table;
- check the video mode first: PAL given 60 Hz VBlanks runs the whole game at the wrong speed.

## 4. Gates (after every change)

- the game reaches a fixed milestone (for example "first main-loop iteration at virtual time T, frame N");
- `alias check: 0`, no masked access escaped the window, nothing wrote into the code region;
- two runs of the same build are guest-identical;
- the data-free tests pass: `python -m pytest -q -m "not wsl and not oracle and not psp and not slow and not needs_game"`.

## 5. Exactness rules you must not "optimise away"

The R5900 FPU is not IEEE (operands with exponent 0 are zero, exponent 255 is the largest finite value, round toward
zero, multiply-add rounds the product first); the PSP FPU runs round-toward-zero with flush but uses denormal inputs,
so operand clamping stays. Build with `-frounding-math -ffp-contract=off`. VU0 macro mode follows the same rules; the
PSP's VFPU cannot reproduce VU0 results. Details: `docs/PORTING_GUIDE.md` sections 5 and 6.

## References

`docs/PORTING_GUIDE.md` sections 5-7, `docs/ARCHITECTURE.md`, knowledge notes in `knowledge/translation/`.
