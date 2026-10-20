---
name: ps2rc-port
description: "Start here to recompile a PS2 game the user owns for the PSP with PS2RC through this agent kit. Orchestrates the whole port: the mandatory onboarding questionnaire, machine check, the PS2RC workspace (download, verify, update), environment check, disc identification, game pack, translation, HLE, PSP build and hardware tests, performance, field notes. Use when the user says port / recompile / convert a PS2 game to PSP, 'make my PS2 disc run on my PSP', continue a port, or names a PS2 game together with the PSP. Asks the user before anything that installs, downloads, runs long, writes to the memory stick or publishes."
---

# Port a PS2 game to the PSP (orchestrator)

You drive a port with PS2RC, the recompiler engine this kit downloads into the user's workspace. The user brings a
PS2 disc they legally own and a PSP that runs homebrew; you do the work on their machine, step by step, and you ask
before every step listed under "Ask first". Read `AGENTS.md` at the kit's root once per session if you have not (its
"Two trees" table says which paths are the kit's and which are PS2RC's).

## 0. Before anything: the onboarding questionnaire

Do not install, build, read the disc or touch the memory stick before the questionnaire in
`docs/AGENT_ONBOARDING.md` is answered. Ask the questions in small groups, in the user's language, and accept
"I don't know" (then find out or mark it Unknown). Record the answers in the port state file (section 2).

After the questionnaire:

1. `python -m uprkit doctor` (what the machine has and lacks; `docs/DEPENDENCIES.md` for the sources);
2. the workspace and PS2RC (`skills/setup-ps2rc/SKILL.md`): the folder the user chose, the pinned PS2RC release,
   verified; on Windows optionally the prebuilt converter with its toolchain (ask, give the size);
3. offer the public reference documents (`skills/fetch-docs/SKILL.md`): it asks where to save them and which sets,
   shows the sizes, and records everything in an index. Neither the kit nor PS2RC ships manuals.

If PS2RC already supports the user's exact disc (a pack in its `games/`), there is no port to do: the user converts
their own copy with PS2RC's converter (improvements to that pack go to PS2RC as pull requests).

Stop and explain if the answers show any of these: the user does not own the disc or got the image from someone else;
the user wants to share the result (builds, EBOOTs, converted files) with others; the PSP is a 32 MB model
(PSP-1000) - not supported, the runtime needs the 64 MB large-memory mode; the target is a PS Vita (Adrenaline) -
Unknown, not supported yet; the user expects a playable result in hours.

## 1. Fix tools: where a change belongs

Every problem is fixed by exactly one of these. If you cannot name which one, you have not understood the problem yet.

| Tool | What it is | When |
|---|---|---|
| Pack data | `pack.toml`, the hook list, zones, text patches, lists of the game's pack (local) | addresses, sizes, which functions to hook or trace, heap size patch |
| Pack C module | C in the pack's `src/` (local, game-specific) | the game's render boundary, its own functions that need a replacement |
| Core HLE | PS2RC's `hle/core/`, `hle/psp/`, `audio/` (generic) | a Sony library function, syscall, kernel object or device every game could hit |
| Translator | PS2RC's `ps2rc/` analysis or back-end (generic) | the generated C does not do what the R5900 code does; then translate again |

A core HLE or translator change is a change to PS2RC: keep it small, record it in the state file, and offer it to the
user as a pull request to PS2RC (their consent; legal-guard first). `setup_ps2rc.py update` refuses to replace a
checkout with local edits, so they are never lost silently.

Never edit the generated C in the work directory by hand: it is regenerated. A small change to it goes through the
pack's text patches.

## 2. The port state file

Keep one file, `PORT_STATE.md`, in the workspace's `work/` folder (never in a repository: it holds facts about the
game and paths of the user's machine). Create it from `skills/ps2rc-port/port-state-template.md` after the questionnaire. Read it at the start of
every session and after every error; update it after every milestone, with each lesson as "X causes Y, fix with Z".
Commands that worked are copied into it verbatim and reused verbatim.

## 3. The workflow

Each phase has an entry and an exit. Do not start a phase whose entry is not met. Tell the user at each exit what was
reached, what is next and how long it may take.

| # | Phase | Skill | Entry | Exit |
|---|---|---|---|---|
| 0 | Public research | ps2-recon (section 0) | questionnaire done | what is publicly known about the game (ports, recompilations, source-reconstruction projects, wikis, addresses, earlier PSP ports, licences) recorded with sources in `PORT_STATE.md`, summary given to the user (onboarding section K) |
| 1 | Environment | setup-ps2rc, psp-build-test | questionnaire done, phase 0 done or declined | workspace made, PS2RC verified (`setup_ps2rc.py verify`); `python -m ps2rc doctor` in `PS2RC/` shows what the chosen goal needs; the example pack builds and runs on the host (`games/example`) |
| 2 | Identify the disc | ps2-recon | the user gave the image path and confirmed ownership | serial, version, region and boot program read from the user's `SYSTEM.CNF`; boot program size and SHA-256 recorded |
| 3 | Recon | ps2-recon | phase 2 | overlays, IOP modules, VU programs, library functions and the engine category listed; an honest estimate given to the user (checkpoint: continue or stop) |
| 4 | Game pack | setup-ps2rc, game-pack | phase 3 | `setup_ps2rc.py new-pack <SERIAL> <VERSION>` made `packs/<SERIAL>_v<VERSION>` (seen by PS2RC as `games/<SERIAL>_v<VERSION>`), filled with `[id]`, `[verify]`, `[memory]`, Sony library hooks; `check-pack` clean |
| 5 | Translate and boot on the PC | ps2rc-translate | phase 4 | the host build runs to the first blocker, then further, each blocker recorded |
| 6 | Replace what the PSP lacks | hle-authoring | blockers that need HLE | the game reaches its main loop on the host; gates at zero; two runs guest-identical |
| 7 | PSP build and hardware | psp-build-test | phase 6 | PPSSPP: boots to the main loop (boolean); the user's PSP: boots, log read back |
| 8 | Speed and memory | psp-performance | phase 7 on hardware | measured on the user's PSP, one lever at a time, with A/B sets |
| 9 | Record | field-notes | any lesson that transfers to other games | a note in `knowledge/` (game-neutral) |

Before anything leaves the user's machine (a commit to a public fork, a pull request, an upload, a message with
files), load `legal-guard`.

## 4. Ask first (explicit consent, every time unless the user gave a standing answer in the questionnaire)

- installing anything or downloading anything (toolchain, packages, emulators, Docker images);
- a step that runs longer than a few minutes (a translation, a full PSP build, a long host run);
- starting an emulator (it opens a window and takes keyboard focus);
- writing to, or deleting from, the memory stick or any folder outside the workspace;
- updating PS2RC to another release (`setup_ps2rc.py update`);
- changing the user's system or emulator settings;
- git commits, pushes, pull requests, publishing anything;
- a change that alters what the game does (density, draw distance, skipped work): it is the user's game.

The user runs the PSP: you prepare the folder and the test steps, they copy (or approve your copy), run and give you
the log.

## 5. Refuse (and say why)

- downloading a game image, a PS2 BIOS, PSP firmware, keys or custom firmware, or telling the user where to get them;
- working from a disc image the user does not own or got from someone else;
- breaking encryption, DRM or ownership checks;
- sharing, uploading or committing anything made from the game: disc files, generated C, objects, EBOOTs, the pack's
  game-derived modules, converted movies or textures - also "just for one tester";
- putting a game title, publisher name, logo or cover art in a public artefact (repository, release, XMB title of a
  shared build);
- any paywall, sale or early access around a port.

## 6. Guardrails

**Reasoning loop for every problem.** Observe (the exact fatal line, call chain, log) - locate the layer (translation,
core HLE, pack module, platform, hardware) - understand what the original code does (static analysis, a reference
run in PCSX2) - decide on one fix tool (section 1) - verify with the gates. If the fix fails, go back to observe with
new data, never with the same guess.

**Circuit breaker.** The same failure three times without new information: stop. Re-read `PORT_STATE.md`, search the
knowledge base (`python -m uprkit kb search <words>`), compare with a reference run (hle-authoring, "Reference runs"),
then ask the user a precise question: what you know, what you tried, what you suspect.

**Claims need evidence.** "It builds" means you read the build output and the exit code. "It boots" means the log says
so. "It is faster" means a hardware A/B set says so. PPSSPP answers yes or no, never how fast or how much memory.

**Context.** Generated C is about a hundred files of a megabyte each, logs grow to megabytes: never read them whole.
Grep, read the tail, read one function. Re-read this skill and the state file after long stretches of work.

**Unknown.** If you do not know, say Unknown and find out; do not guess hardware behaviour, firmware support or
timings.

## 7. Honest expectations to give the user

- First boot of a new game to its main loop on the PC: days to weeks of analysis and HLE work. A playable PSP build:
  weeks to months. Much of it is per-game work (the render boundary, the sound driver binding, memory fitting).
- Speed: the reference port (a large open-world 3D game) reached about 30 fps indoors and 17 to 21 fps outdoors on
  a PSP-3000 at 333 MHz (about 9 % more at 365 MHz), after months of tuning and with reduced density and draw
  distance; it started at about 7 fps. The PSP's CPU is the limit; a game that does much less work per frame does
  better (`knowledge/workflow/reference-port-results.md`).
- Nothing is guaranteed: some games use techniques (self-modifying code, heavy VU1 use, more than the PSP's memory)
  that need research before a port is possible.

## References

- Kit: `docs/AGENT_ONBOARDING.md` (questionnaire), `docs/WORKSPACE.md`, `docs/DEPENDENCIES.md`
- PS2RC: `PS2RC/docs/PORTING_GUIDE.md` (the method), `PS2RC/docs/ARCHITECTURE.md`, `PS2RC/docs/GAME_PACK_FORMAT.md`
- Skills: setup-ps2rc, ps2-recon, ps2rc-translate, hle-authoring, psp-build-test, psp-performance, game-pack,
  legal-guard, field-notes, fetch-docs
- `knowledge/INDEX.md` - search it before solving a problem from scratch
