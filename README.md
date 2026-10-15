# universal-ps2-recompiler

> **Read [LICENSE](LICENSE) before you use it.** Free, source-available, the same licence as PS2RC. **No game data is
> included here** and none may ever be added: you bring a PS2 disc you legally own, and everything made from it stays
> on your PC.

**universal-ps2-recompiler is an agent kit**: instructions, skills, a knowledge base and setup scripts that let an AI
coding agent (Claude Code, or any agent that reads `AGENTS.md` and Agent Skills) port a PlayStation 2 game you own to
your Sony PSP with **[PS2RC](https://github.com/SandstoneDev/PS2RC)**, a static recompiler that turns a PS2 game's
program into C and builds it for the PSP with a runtime for what the PSP lacks.

The kit does not contain the engine. On your machine it **downloads PS2RC** at a release it was checked with, verifies
it, and works on top of it:

```
universal-ps2-recompiler (this kit)          <workspace>/ (on your PC, a folder you choose)
  AGENTS.md, skills/, knowledge/      -->      PS2RC/          the engine, pinned release, verified
  skills/setup-ps2rc (downloads,               packs/<game>/   your game pack, linked into PS2RC/games/
  verifies, updates PS2RC)                     work/           everything made from your disc - never shared
```

## Quick start

Requirements: Windows 10/11 x64 (first) or Linux / WSL 2, Python 3.11 or newer, git recommended. Everything else is
found or fetched step by step, always after asking you: `python -m uprkit doctor` shows what your PC has and where to
get what is missing ([docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)).

```bash
git clone https://github.com/SandstoneDev/universal-ps2-recompiler.git
cd universal-ps2-recompiler
python -m uprkit doctor            # what this PC has and lacks (reads no game data, downloads nothing)
python -m uprkit skills sync       # optional: copies skills/ into .claude/skills and .agents/skills (git-ignored)
claude                             # start Claude Code here; it reads CLAUDE.md -> AGENTS.md
```

Use `python3` where `python` is not Python 3. To have the skills in every project, copy them into your personal
skills folder: `python -m uprkit skills sync --target ~/.claude/skills` (run it again after `git pull`). Other agents:
point them at `AGENTS.md` (a `GEMINI.md` pointer is included).

**What happens on the first run.** Ask the agent to port a PS2 game you own to your PSP. Before it installs, downloads
or builds anything it:

1. asks the onboarding questions ([docs/AGENT_ONBOARDING.md](docs/AGENT_ONBOARDING.md), in small groups, each with
   the reason and a default): your language, the game, region and version, that you own the disc, the legal model,
   your PSP model and firmware, your PC, **where to put the workspace**, **which PS2RC version**, your goal, and what
   it may do without asking;
2. checks your PC (`python -m uprkit doctor`) and tells you what is missing, with the official source, size and
   checksum of each item;
3. creates the workspace and downloads PS2RC (`skills/setup-ps2rc`): a shallow `git clone` of the pinned release tag,
   or its source zip without git; the commit and a content hash of every file are checked against
   `skills/setup-ps2rc/ps2rc.lock.json`. On Windows it can also fetch PS2RC's prebuilt converter with its own PSP
   toolchain (about 104 MB, SHA-256 checked);
4. offers to fetch public reference documents into the workspace (`skills/fetch-docs`: open SDKs, emulator sources,
   hardware notes; sizes first, an index with URL, licence and SHA-256);
5. creates your game pack from PS2RC's `games/_template` (`setup_ps2rc.py new-pack <SERIAL> <VERSION>`) and follows
   the port workflow (`skills/ps2rc-port`), asking before every long run, install, emulator start or memory-stick
   write.

Updating the engine later: `python -m uprkit update` (after `git pull` of this kit, which brings newer pins). Your
packs and your work folder are never touched; the old checkout is kept as a backup folder.

Without an agent, the same scripts work by hand:

```bash
python -m uprkit setup --workspace <folder>          # PS2RC into <folder>/PS2RC (add --dry-run to see the plan)
python -m uprkit new-pack SLUS-12345 1.00 --workspace <folder>   # your disc's serial and version
python -m uprkit status --workspace <folder>
```

## What is in this repository

| Path | What |
|---|---|
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | the instructions every agent follows (the pointers lead to `AGENTS.md`) |
| `docs/AGENT_ONBOARDING.md` | the questions to ask before any work |
| `docs/WORKSPACE.md` | the workspace layout, why packs live next to the engine, updates |
| `docs/DEPENDENCIES.md` | every tool a port needs, its official source, checked version and SHA-256, and what to do when a link dies |
| `skills/` | 11 skills in the Agent Skills format: port orchestrator, PS2RC setup, recon, translation, HLE, PSP build and test, performance, game pack, legal guard, field notes, reference documents |
| `knowledge/` | field notes from a real port with hardware numbers, game-neutral (`python -m uprkit kb search <words>`) |
| `uprkit/` | the kit's command line (standard library only): setup, doctor, skills, knowledge base |
| `tests/` | tests of the kit (no network, no game data) |

What the engine can do, and how honest the expectations are (days to weeks to a first boot of a new game, months to a
playable build, about 30 fps indoors and 17 to 21 fps outdoors in the reference port on a PSP-3000), is in PS2RC's
README and `knowledge/workflow/reference-port-results.md`. A PSP-2000 or PSP-3000 with custom firmware is needed; other
models: Unknown.

## Relationship to PS2RC and psp-developer

- **[PS2RC](https://github.com/SandstoneDev/PS2RC)** is the engine (translator, runtime, HLE, converter, game pack
  format) and the converter for the one game it supports. That game is **reserved** under the licence: only
  SandstoneDev ports it, and forks of PS2RC are for pull requests only. This kit never makes, modifies or copies a
  pack for a reserved game; it ports **other** games. Fixes to the engine go to PS2RC as pull requests.
- **[psp-developer](https://github.com/SandstoneDev/psp-developer)** is the companion skill for general PSP development
  (homebrew, rendering, Media Engine, real-hardware pitfalls).

## Licence and credit

This kit is under the **PS2RC License 1.0** ([LICENSE](LICENSE), the same text as PS2RC's; here "PS2RC" covers the
kit's instructions, skills, notes, scripts and tests too). In short: free of charge (voluntary donations that gate
nothing are fine), forks and anything you publish carry the credit block below, the code stays under the same
licence, no game data ever, no work for a reserved game. Third-party notes: [NOTICE.md](NOTICE.md).

```
Based on PS2RC by SandstoneDev
https://github.com/SandstoneDev/PS2RC
Community: https://discord.gg/wV8x46ZTDu
```

## Community

**Join the community** on Discord: [discord.gg/wV8x46ZTDu](https://discord.gg/wV8x46ZTDu) - questions, progress
reports, help with your port (send logs, never game files). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
Security problems: [SECURITY.md](SECURITY.md). Other contact: GitHub issues, the Discord, or sandstonedevpsp@gmail.com.

Rightsholders can reach the maintainer the same way; on a takedown notice the named material is removed promptly and
not published again.

This project is not affiliated with Sony Interactive Entertainment or any game publisher. "PlayStation", "PS2" and
"PSP" are trademarks of Sony Interactive Entertainment Inc.
