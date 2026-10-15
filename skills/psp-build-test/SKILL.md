---
name: psp-build-test
description: "Check the environment, build the PSP EBOOT, stage the PSP folder, run boolean checks in PPSSPP, deploy to the user's memory stick with md5 verification (only with consent), read session.log back from the user's PSP, and run hardware A/B sets with PS2RC (through this kit). Use for 'python -m ps2rc doctor', building or packaging for the PSP, PPSSPP runs, copying to the memory stick, reading or comparing PSP logs and profiler output, or when the user reports what happened on their PSP."
---

# Build, test and deploy

**PPSSPP gives booleans, the real PSP gives numbers.** PPSSPP tells you whether a build boots, renders and plays. It
does not tell you speed or free memory: it reports about 5 MB more free memory than the device, allows more open
files, models no caches, charges almost nothing for the GE, has no Media Engine, paces the game itself, and tolerates
things that switch a real PSP off (`knowledge/workflow/ppsspp-booleans-hardware-numbers.md`).

## 1. Environment

First the kit's `python -m uprkit doctor` (Python, git, the PS2RC workspace, the PSP toolchain, WSL, host gcc,
optional emulators and ffmpeg, each with its official source in `docs/DEPENDENCIES.md`), then, inside
`<workspace>/PS2RC`, PS2RC's own `python -m ps2rc doctor` (add `--json` for a machine-readable answer). Both read no
game data and install nothing. A tool installed somewhere they do not look: ask the user for the folder and record it
in the workspace's `local.toml` `[tools]`.
For every missing item, show the user the hint and ask before installing. Then prove the toolchain with the example
pack (no game data):

```
python3 -m pytest -q -m "not wsl and not oracle and not psp and not slow and not needs_game"
bash mk/build.sh --pack example host && bash mk/run_host.sh --pack example
bash mk/build.sh --pack example psp
```

If the example does not build and run, nothing else will.

## 2. Build and stage

```
HLE_BUILD=<n> bash mk/build.sh --pack <pack> psp [JOBS]
python3 ps2rc/pipeline/stage.py --pack <pack> --out <work>/stage/<FOLDER> [--prx <ps2rc_exc.prx>] [--cfg key=value]
```

The user-facing alternative is the converter: `python -m ps2rc.convert <image> --out <dir>` (resumable steps,
finds or uses the toolchain, writes an md5 manifest of its output).

- **Build number +1 for every build you hand to the user**; it shows in the XMB title, the log header (`build=`) and
  on screen. Without it nobody knows which build a log came from.
- Job count: what the user allowed (shared machines: low). Each psp-gcc on the large generated units needs several
  hundred MB of RAM.
- Folder names under `PSP/GAME/` are neutral (no game title in anything that could be shared).

## 3. PPSSPP (booleans)

Ask first (it opens a window that takes keyboard focus; PC keyboard and pad input reach the game while it has focus).
On Windows: `python tools/dev/ppsspp_run.py <stage> --wait-file session.log --pattern "result=\w+ end="`
(PPSSPP folder from `local.toml` `[tools] ppsspp_dir`, which you ask the user for or take from the doctor; one run at
a time through a lock file). Elsewhere start PPSSPP
by hand on the staged folder. Read only booleans: `result=main_loop` or not, crash lines, "cannot open" lines.

## 4. The user's PSP

Only with the user's consent, and only into the folder agreed in the questionnaire.

1. **Archive before you delete**: copy the old folder's `session.log`, `session_prev.log` (and profiler files) to the
   work directory with the build number in the name.
2. **Copy file by file and verify every file's md5**, then verify the whole folder again at the end. The PSP's USB
   link drops in the middle of writes; a truncated EBOOT once passed a plain copy. On Windows:
   `powershell -ExecutionPolicy Bypass -File tools\dev\card_sync.ps1 -Src <stage folder> -Dst <memory stick>\PSP\GAME\<FOLDER>`.
   Elsewhere: copy, then compare `md5sum` of every file on both sides; recopy what differs.
3. Never touch other folders on the memory stick; never copy large trees from card to card.
4. Give the user numbered test steps: which folder, what to press, what they should see, how long to wait, how to
   exit (HOME, Exit), and that the log is written next to the EBOOT.

**Reading the log back.** Before analysing, check that it is the log of the build you deployed: `build=` in the header,
the run line (sequence, clock, battery where present), and the folder it came from - logs rotate
(`session.log` -> `session_prev.log`) and thin test folders read their data from another folder (`disc_dir=`) but
write logs next to their own EBOOT. Then grep, do not read whole: `result=`, `crash`, `cannot open`, `free_kb`, the
last lines. A log that stops early with no crash line: the console froze or switched off - ask the user what they saw.

## 5. Measuring on hardware

- One change per comparison. Every A/B set has a **control and a control-again** (same EBOOT, other folder); their
  difference is the drift (warm-up, battery, card cache). Distinct XMB titles per folder; same scripted input; same
  power state; fixed run length. Thin folders: EBOOT + run options + kernel module, game data through `disc_dir=`.
- Compare by game time and by profiler zones, not by iteration count; first check both variants did the same guest
  work. A change that alters gameplay (timing, random numbers, density) sends the scripted run elsewhere: compare
  zones, not totals.
- **A/B inside one run**: if your tree's runtime has the in-run A/B module (search `hle/` for `ab_v0`), the run
  options `ab_v0` .. `ab_v3` (`NAME key=value ...`) switch run-time keys at window boundaries in random block order and
  report the median difference to `ab_v0` with an interval. Only run-time switchable keys; a different EBOOT still
  needs folders. PPSSPP always reports "no difference" (it paces the frames).
- Profiler: zones on guest functions (the pack's zone list) and in HLE code; summaries every 10 s and final tables in
  `session.log`; a profiling folder runs a few ms per frame slower - keep it separate from timing folders. Hardware
  counters (CPI, cache misses) come from the kernel helper module: never enable them in an emulator.

## 6. Exit and power

Exit in order: audio and Media Engine, finish the GE list, counters, the kernel module (stop, then unload), then exit
the game. An unordered exit has switched consoles off. If the user reports a power-off, ask exactly when (during play,
at exit, after sleep) and archive the log before the next run.

## References

`docs/PORTING_GUIDE.md` sections 14-15, `knowledge/workflow/`, `knowledge/hardware/`.
