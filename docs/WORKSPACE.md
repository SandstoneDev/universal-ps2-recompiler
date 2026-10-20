# The workspace: PS2RC underneath, the user's work on top

This kit is the instructions; PS2RC (https://github.com/SandstoneDev/PS2RC) is the engine. The kit never copies the
engine: on the user's machine `skills/setup-ps2rc/setup_ps2rc.py` downloads PS2RC at the release pinned in
`skills/setup-ps2rc/ps2rc.lock.json`, verifies it and builds a workspace around it.

```
<workspace>/                    a folder the user chooses: ASCII path, no spaces, outside every git repository
  ps2rc-workspace.json          manifest: PS2RC tag, commit, method (git / zip), content hash, packs, history
  WORKSPACE.txt                 the same layout in two lines per folder, for the user
  PS2RC/                        the engine checkout at the pinned release
    games/_template, example    from PS2RC
    games/<SERIAL>_v<VER>       PS2RC's own packs (read-only here; change them in a fork of PS2RC)
    games/<SERIAL>_v<VER>  -->  link to packs/<SERIAL>_v<VER> (junction on Windows, symlink elsewhere, else a copy)
    local.toml                  copy of ../local.toml
  packs/<SERIAL>_v<VER>/        the user's own pack (from PS2RC's games/_template), optionally its own git repository
  work/                         everything made from the user's disc: translation, builds, stages, logs, PORT_STATE.md
  refdocs/                      public reference documents (skills/fetch-docs)
  downloads/                    the release archives
  converter/                    optional: the prebuilt PS2RC converter (Windows, with its PSP toolchain and ffmpeg)
  local.toml                    PS2RC's per-machine settings: [paths] work, [games."<pack>"] disc, [tools]
  env.sh, env.ps1, env.cmd      UPR_WORKSPACE, PS2RC_LOCAL (and PS2RC_TOOLCHAIN with the converter)
```

## Why the pack lives in `packs/` and is linked into `PS2RC/games/`

- PS2RC looks for packs only in its own `games/` folder: `ps2rc/pack.py` (`games_dir`), the C source index in
  `ps2rc/config.py` and the converter's `ps2rc/convert/identify.py` all scan `<checkout>/games`. A pack elsewhere would
  be invisible to the build scripts and to the converter.
- The checkout is replaceable: `update` puts a new verified release in place and links the packs again. A pack inside
  the checkout would have to survive that replacement; in `packs/` it is never touched.
- The pack is the user's own work: it can be its own small git repository that contains neither PS2RC nor any other
  game's pack, which is exactly what may be shared later, if the user decides so after a legal check.
- Links are excluded from the checkout's git status (`.git/info/exclude`), so the engine checkout stays clean and
  `verify` reports only real changes to the engine.

If links are impossible (some file systems, some WSL mounts of Windows folders), `link --copy` copies the pack instead;
then edit only `packs/<name>` and run `link` again before each build. Check from the shell that builds (WSL, Linux)
that `PS2RC/games/<name>/pack.toml` is readable; if it is not, use `--copy`.

## Versions and updates

- `ps2rc.lock.json` pins each PS2RC release this kit was checked with: tag, commit, content hash of the source tree,
  SHA-256 of the source archive and of the release assets, the pack format. `default` is the release `setup` installs.
- `update` installs the kit's default (or `--tag`), verified the same way; the old checkout is kept as
  `PS2RC.backup-<tag>-<time>` until the user deletes it. It refuses when the checkout has local edits (engine fixes go
  to PS2RC as pull requests) unless `--accept-backup`.
- A release the kit does not pin needs `--allow-unpinned` and is recorded as unpinned: ask the user first.
- After an update: PS2RC's `python -m ps2rc doctor`, the example pack, then the user's pack (host build first).

## What never leaves the workspace

`work/` (everything made from the disc), `local.toml` (paths of this machine), `PORT_STATE.md`, logs, the disc image.
`packs/` leaves the machine only by the user's explicit decision after `skills/legal-guard` and
`setup_ps2rc.py check-pack`.
