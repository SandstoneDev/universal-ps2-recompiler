---
name: legal-guard
description: "Check what may and may not leave the user's machine in a PS2RC port made with this kit, before any git commit to a public fork, push, pull request, upload, release, shared screenshot of code, or message with files: never game data, generated C, EBOOTs or game-derived modules; no game titles or logos in public artefacts; licence credit; no paywalls; the takedown policy. Use when the user asks 'can I share / upload / publish this', 'can I send my build to a friend', 'is this legal', before git push or a pull request, and when choosing names, titles or icons. Not legal advice."
---

# Legal guard (not legal advice)

The project's model: we publish tools; the user's machine makes every game-derived byte from the user's own legally
owned copy, and nothing derived from the game leaves that machine. A recompiled or translated game is a derivative of
the game even when the user supplied the disc; asking for the user's disc does not make sharing the result lawful.

## 1. Never commit, upload, publish or send (to anyone, also "one tester")

- game files or anything extracted or converted from them: code, IOP modules, VU microcode, textures, models, audio,
  movies, text, tables;
- generated C, object files, ELF/EBOOT/PRX built from a game's code, staged PSP folders, patches or deltas of them;
- modules the generators made from the game (IOP recompiler, VU0 microcode translator output);
- hand translations of the game's code, and listings or databases of an interactive disassembler;
- a PS2 BIOS, PSP firmware, keys, custom firmware or links to them; help to obtain a game image;
- Sony SDK material (headers, libraries, documentation, citations of it) and middleware SDK material;
- personal data: paths of the user's machine, names, e-mail addresses (other than a project's public contact);
- a game title, publisher name, logo, cover art or screenshot in a repository name, release name, XMB title or icon of
  anything shared.

- anything for a **reserved game** (a `RESERVED.md` in a SandstoneDev repository, PS2RC License 2(e)): a pack, a
  modified pack, a patch, a build, a conversion tool, a release from a fork - and code, lists or values copied from a
  reserved pack into another pack.

Facts needed for interoperability (hardware register addresses, Sony library function names, sizes and hashes that
identify a version) are not game data; still keep public packs minimal and neutral, and decide per game with a
lawyer whether a pack is published at all.

## 2. Before every commit or push to a public repository

1. `git status` and `git diff --cached --name-only`: only the user's own code and documentation.
2. Search the staged files for: drive-letter paths, home-directory paths, the game's title or serial, long hex
   tables, base64 blobs, binary files, files over 512 KB. Any hit: stop and ask.
3. No game-derived file in the history either: a file once committed stays in the history; if it happened, stop and
   tell the user (the history must be rewritten or the repository recreated before anything is pushed).
4. Push only on the user's explicit "push". Never force-push without their explicit consent.

## 3. Licence and credit

The `LICENSE` of this kit and of PS2RC decides (the same PS2RC License 1.0; PS2RC's `NOTICE.md` lists third-party
licences). In short: free of charge (voluntary donations that gate nothing are allowed; no selling, renting, paywalls,
subscriptions or early access); every fork, shared pack and release page carries the credit block from the README;
PS2RC's code stays under the same licence; no game data; a game declared reserved by SandstoneDev is not ported by
anyone else, and a GitHub fork of a SandstoneDev repository is only for pull requests to it.

**What may be shared, if the user decides so after these checks:** a fix to PS2RC as a pull request to PS2RC; a
game-neutral field note as a pull request to this kit; the user's own pack for a non-reserved game as its own
repository (only the pack folder: never a copy of PS2RC with it, never the workspace, never `work/`), after
`setup_ps2rc.py check-pack` reports 0 and section 2 is clean. Conservative legal
advice is stricter about money: any income around a port raises the risk - tell the user.

## 4. Wording

- Requirements: "a PSP-2000 or PSP-3000 that runs homebrew (custom firmware)". Never bundle, host or link custom
  firmware.
- One plain-text compatibility line is fine ("works with the user's own copy of game X"), with a non-affiliation
  disclaimer; never in titles, icons or splash screens.
- A version hash identifies the version, never ownership. Do not claim the tool or a port is "legal".

## 5. Takedown

If a rightholder sends a takedown or removal notice: remove the named material promptly (target: within a day), do not
publish it again, no re-uploads, no mirrors, no reflex counter-notice; record what was removed; tell the user to talk
to a lawyer. Complying limits harm; it does not make earlier publication lawful - section 1 decides what is published
in the first place. PS2RC's own policy: its `TAKEDOWN.md`.

## 6. Red flags: stop and ask the user

Game bytes or transcriptions in a public path; a plan to publish an EBOOT, a game module or a patch, or to send a build
to anyone; decryption, DRM removal, keys or firmware links; SDK material; game names or art in titles, icons or pages;
money around a port; a letter from a rightholder.
