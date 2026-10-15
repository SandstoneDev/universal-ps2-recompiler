# Port state (keep this file in the workspace's work/ folder, never in a repository)

Read at the start of every session and after every error. Update after every milestone.

## Rules for this port (copied from the questionnaire)
- Standing permissions: <long builds yes/no> <emulator runs yes/no> <memory stick writes: who copies>
  <downloads/installs: ask each time / allowed list>
- The user tests on: <PSP model, firmware, memory stick path as the user names it>
- Goal: <boot test / playable / performance>

## Game
- Title (the user's words, private):
- Serial / version / region / video mode (from SYSTEM.CNF):
- Boot program: <file name>, <size> bytes, SHA-256 <...>
- Disc image / extracted disc (path on this machine):
- Pack: <workspace>/packs/<serial>_v<version>/ (local; PS2RC sees it as games/<serial>_v<version>)

## Environment
- Workspace: <folder>; PS2RC <tag> commit <...> (setup_ps2rc.py status); converter <yes/no>
- Kit doctor summary (date):
- PS2RC doctor summary (date):
- Build shell / toolchain / psp-gcc version:
- Work dir: <workspace>/work (local.toml [paths] work)
- Reference documents: <folder>, index DOCS_INDEX.md, last fetch <date> (skills/fetch-docs)
- The user's own documents (read in place only): <where, or none>

## Current phase
- Phase <n> (<name>), entered <date>. Exit condition: <...>

## Commands that work (verbatim)
- translate:
- host build / run:
- PSP build:
- stage / deploy:

## Milestones
| Date | Where (host / PPSSPP / PSP) | What (virtual time, frame, log line) |
|---|---|---|

## Open blockers
| # | Symptom (fatal line) | Layer | Tries | Status |
|---|---|---|---|---|

## Experiment switches in use (remove before the exit of a phase)

## Lessons ("X causes Y, fix with Z")

## Session log
