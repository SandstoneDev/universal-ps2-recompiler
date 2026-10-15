---
name: game-pack
description: "Create and fill a PS2RC game pack for one version of one PS2 game: make it from PS2RC's games/_template with setup_ps2rc.py new-pack (in the workspace's packs/, linked into PS2RC/games/), fill pack.toml ([id], [verify], [memory], [overlays], [runtime], [translate], [build], [run], [stage], [convert]), the hook list, zones, text patches, the converter recipe and its generators, and the user's own XMB assets (icon, background, music). Use when starting a pack after recon, when the converter says 'no game pack', when a pack value must change, or when the user wants their own menu icon or title."
---

# The game pack

A pack describes one version of one game: how to recognise the disc, where the code is, which functions the HLE
replaces, the C modules that replace them, and how the converter stages the game. It contains **no game data**: no
files from the disc, no code or tables copied from the game, nothing translated from it. A pack for a game the user is
porting stays local unless a legal check says otherwise (legal-guard).

## 1. Create

```
python skills/setup-ps2rc/setup_ps2rc.py new-pack <SERIAL> <VERSION> [--region R] [--git]   # e.g. SLUS-12345 1.00
cd <workspace>/PS2RC
python3 ps2rc/pack.py get <SERIAL>_v<VERSION> id.serial    # how the build scripts see a value
```

`new-pack` copies only PS2RC's `games/_template` to `<workspace>/packs/<SERIAL>_v<VERSION>/` and links it into
`PS2RC/games/` (why: `docs/WORKSPACE.md`). Edit the pack in `packs/` (with a copy instead of a link, run
`setup_ps2rc.py link` after each edit). `games/_template/pack.toml` documents every key; `games/example/` is a
complete pack of a small test program to compare with; `PS2RC/docs/GAME_PACK_FORMAT.md` is the reference.

**Listed discs.** A pack in PS2RC's `games/` with a `DISTRIBUTION.md` is for a disc whose work based on PS2RC only the
PS2RC project distributes (licence 2(e); not a claim of any right in the game). You may
read it to see how a real pack is organised (which tables a large game needed, how hooks and zones are laid out).
Never copy its code, hook lists, addresses, lists or values into another pack, and never make or change a pack for that
game. `setup_ps2rc.py check-pack <name>` fails on copied files or runs of copied lines; run it after every larger edit
and before anything is shared. Path values: `{work}/x` (work directory), `{disc}/x` (the user's
extracted disc), `{repo}/x` (checkout), plain = inside the pack.

## 2. Fill in order

1. `[id]`, `[verify]`: serial, version, region, boot program, `system_cnf_boot2`, boot program size and SHA-256 (from
   ps2-recon). A disc with another hash is refused with a clear message.
2. `[memory]`: code range, data end, BSS end, `ram_end_psp` (the guest RAM the PSP provides; the game heap must fit).
3. `[overlays]` if the game has code overlays.
4. Hook list (`hooks.def`): the Sony library functions found by the signature scan (by the names the core implements),
   then the game's own functions as the HLE needs them (hle-authoring). A `TRACE` of the main-loop function and its
   label in `[runtime] main_loop`.
5. `[translate]` (start with `variant = "v0"`), `[build]`, `[run]` (disc map, same-size file overrides).
6. `[stage]`: which disc files go to the PSP folder, same-size text replacements, movies.
7. `[convert]`: the steps the PC converter runs on the user's machine (analysis commands, translation, extras) and the
   **generators** that make game-derived modules there (IOP modules, VU0 programs). Everything game-derived must be
   reproducible on the user's PC from their own disc.

Labels and comments are neutral descriptions ("frame end", "texture upload"), never names taken from the game.

## 3. The user's own menu assets

The PSP menu shows ICON0 (144x80 PNG), ICON1 (animated, 144x80 video), PIC0 (310x180 PNG), PIC1 (480x272 PNG
background) and SND0 (ATRAC3plus music; ICON1 + SND0 together about 500 KB at most - commonly used values). The
repository ships only neutral placeholders. The user may supply their own pictures for their own copy:

```
python -m ps2rc.pbp pack --eboot EBOOT.PBP --out <folder> --title "<title>" --icon0 icon.png --pic1 back.png
python -m ps2rc.convert <image> --out <dir> --title "<title>" --icon0 icon.png --pic0 info.png --pic1 back.png
```

`ps2rc/pbp/README.md` has every option. Set an own `DISC_ID` (the converter does). The user's title and pictures stay
in their own build: never put a game title, logo or cover art into anything public.

## 4. Check

- `python3 ps2rc/pack.py get <pack> <key>` for each key the build uses;
- every `HOOK` name has a definition (the test suite checks it) and the translation was redone after hook changes;
- the pack contains no game files, no game names in labels, no generated C;
- `python skills/setup-ps2rc/setup_ps2rc.py check-pack <SERIAL>_v<VERSION>` reports 0 findings.
