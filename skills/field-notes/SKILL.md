---
name: field-notes
description: "Search and add field notes in this kit's knowledge base (knowledge/): lessons that transfer to other PS2 ports, written as situation, cause, rule and evidence, per hardware topic, translation or HLE topic, workflow step or engine/middleware CATEGORY - never about one named game. Use before solving a problem from scratch (search first), after a fix that cost real debugging time, after a hardware measurement, or when the user says 'remember this', 'write it down', 'add a note'."
---

# Field notes

## Search first

```
python -m uprkit kb search <word> [<word> ...]     # notes containing all the words
python -m uprkit kb list
```

`knowledge/INDEX.md` lists every note by category.

## Add a note

Write a note when a lesson cost real time and would save time on another game: a hardware behaviour, a PPSSPP
difference, a translation pitfall, an HLE rule, a measuring method, a pattern of an engine category.

```
python -m uprkit kb new <category> <slug> "<Title>"   # categories: hardware translation hle engines workflow
# fill it in, then
python -m uprkit kb index
python -m uprkit kb check
```

Rules for a note:

- **One lesson per note**, as the template asks: Situation, Cause, Rule, Evidence, Related; fields Category, Summary,
  Applies to, Evidence, Status.
- **Evidence says where it was measured**: real PSP (model), PPSSPP (booleans only), PC host, PCSX2, or reasoning.
  Numbers with units. "Unknown" where you do not know; Status "open" if unconfirmed.
- **Game-neutral**: no game titles, publisher or middleware product names, character or place names, addresses of a
  game's code or data, disc file names, or code copied from a game. Write "a large 3D game", "the engine's
  device-driver layer". Hardware register addresses and Sony library function names are fine.
- Plain ASCII; no paths of anyone's machine; no personal data.
- Engine notes describe a CATEGORY (for example "middleware renderers with a VU1 microcode pipeline"), the boundary
  that worked and its hooks in neutral words.

## Share a note

Notes are part of this kit's repository; contributing one is a normal pull request to the kit, after legal-guard's
checks and only with the user's consent. Notes name PS2RC paths (`hle/psp/`) relative to the PS2RC checkout and
never a path of anyone's machine. The user decides whether to publish anything.
