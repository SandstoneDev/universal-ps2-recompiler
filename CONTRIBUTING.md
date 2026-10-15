# Contributing

Thank you for helping. Every change goes through review.

## How changes get in

1. Fork the repository and work on a branch of your fork.
2. Open a pull request against `main`: what changed, why, and how you checked it (`python -m pytest -q`; for a skill
   or note, which port and which hardware the lesson came from).
3. One topic per pull request.

Changes to the engine (translator, runtime, HLE, converter, pack format) belong in PS2RC
(https://github.com/SandstoneDev/PS2RC), not here.

## What a change must never contain

- **Only your own work**, or text whose licence allows it here (say so, and add it to `NOTICE.md`). Nothing from
  confidential documentation or console-maker SDKs, no citations of them.
- **No game data and no code recovered from a game**: no files, tables, listings, generated C or builds, not even one
  function as an example. Knowledge notes are game-neutral (`skills/field-notes/SKILL.md`).
- **Nothing for a reserved game** (PS2RC License 2(e)): no pack, patch or instructions for it beyond what PS2RC
  itself documents.
- **Nothing machine-specific**: no paths of your machine, drive letters, user or host names, tool locations, e-mail
  addresses, tokens. `tests/test_portability.py` checks the tree; every location is asked from the user or discovered
  at run time.
- **New download sources** only from the official project (its own site or its code-host organisation), checked
  reachable, with the version and the SHA-256 the source publishes, in `docs/DEPENDENCIES.md` and the doctor.

## House style

Plain ASCII, short sentences, neutral names. Skills: `python -m uprkit skills check`. Notes: `python -m uprkit kb
check` and `kb index`. Scripts: Python standard library only, Windows and Linux.
