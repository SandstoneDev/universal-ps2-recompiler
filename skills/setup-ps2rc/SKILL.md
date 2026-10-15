---
name: setup-ps2rc
description: "Set up, check and update the PS2RC workspace on the user's machine: ask where it goes, download PS2RC (the recompiler engine) at the release this kit pins and verify it (commit and content hash, SHA-256 of archives), optionally download the prebuilt converter with its PSP toolchain, create the user's own game pack from PS2RC's games/_template, link it into the checkout, check it, and report what the machine still lacks (doctor). Use on the first run after the onboarding questions, when PS2RC is missing or outdated, when the user asks to update PS2RC, when a new game pack is needed, or when a tool is missing."
---

# Set up the PS2RC workspace

This kit does not contain the engine. PS2RC (https://github.com/SandstoneDev/PS2RC) is downloaded onto the user's
machine into a **workspace**, at the release pinned in `ps2rc.lock.json` (next to this file), and every port happens
on top of it. One script does it all, standard library only, Windows 10/11 x64 first, Linux and WSL second:

```
python skills/setup-ps2rc/setup_ps2rc.py <command> ...      # or: python -m uprkit <command> ... in the kit checkout
```

Use `python3` where `python` is not Python 3. Every command prints what it did; read the output and the exit code.

## 1. Before anything

The onboarding questions (`docs/AGENT_ONBOARDING.md`) come first. From them you need: the workspace folder, the PS2RC
version (default: the pinned one), whether the prebuilt converter may be downloaded, and the standing permissions for
downloads. **Ask before every download** and say what, from where and how big:

| What | Size | When |
|---|---|---|
| PS2RC source (git clone of one tag, or the tag's source zip) | about 2 MB zip, 5 MB checked out | always |
| prebuilt converter with its Windows PSP toolchain (`--with-converter`) | about 104 MB zip, 263 MB unpacked | Windows, if the user wants the converter or has no toolchain |
| third-party sources of the converter (`converter-sources` in the lock) | about 249 MB | only on request (licence source offer) |

## 2. Check the machine

```
python skills/setup-ps2rc/setup_ps2rc.py doctor [--workspace DIR] [--wsl] [--online]
```

It looks for every tool in the variables that name it, on PATH and in the standard install places of this OS, and
prints for each missing item the official source, the version this kit was checked with and the published SHA-256
(table: `docs/DEPENDENCIES.md`). It never assumes a tool is installed or where. If a tool is installed somewhere it
does not look, ask the user for the folder and record it in the workspace's `local.toml` (`[tools]`). `--wsl` (Windows)
also looks inside the default WSL distribution; `--online` asks GitHub whether the PS2RC release page answers. Once
PS2RC is installed, also run PS2RC's own `python -m ps2rc doctor` inside `<workspace>/PS2RC`.

## 3. Create the workspace

Ask: **"Where should the PS2RC workspace go?"** Propose the default the script prints with `--dry-run` (a folder named
`ps2rc-workspace` in the user's home folder, or at the top of the system drive when the home path has spaces or
non-ASCII characters). The folder must be empty or new, have an ASCII path without spaces, and lie outside every git
repository (it will hold files made from the user's disc).

```
python skills/setup-ps2rc/setup_ps2rc.py setup --workspace <folder> --dry-run          # the plan, nothing written
python skills/setup-ps2rc/setup_ps2rc.py setup --workspace <folder> [--with-converter]
```

- With git installed it runs `git clone --depth 1 --branch <tag>`; without git it downloads the tag's source zip.
  Force one with `--method git|zip`.
- Verification: the tag must point at the pinned commit, and the content hash of the downloaded tree must equal the
  pinned `tree_sha256` (the same value for the clone and the zip). A mismatch deletes the download and stops. A zip
  whose bytes differ but whose content matches is accepted with a note (the host may recompress archives).
- The prebuilt converter is checked against the pinned size and SHA-256 before it is unpacked.
- Offline or behind a firewall: `--zip <the tag's source zip>` or `--source <a local clone or another git URL>`;
  `--converter-zip <file>`. The same checks apply.
- **Private or missing repository**: if PS2RC is not public (yet), the tag does not exist, or the user has no access,
  the script stops with exit code 4 and says so. Tell the user plainly: wait until it is public, or ask the maintainer
  for access and sign in to git, or give a copy they already have. Never work around access control.

The result (`ps2rc-workspace.json` records everything, `WORKSPACE.txt` explains it to a human):

```
<workspace>/PS2RC/      the engine checkout - never port inside it; `update` replaces it
<workspace>/packs/      the user's game packs, linked into PS2RC/games/
<workspace>/work/       everything made from the disc (PS2RC's [paths] work) - never leaves the machine
<workspace>/refdocs/    public documents (skills/fetch-docs)
<workspace>/local.toml  PS2RC settings; copied into PS2RC/local.toml by setup, update and link
<workspace>/env.sh env.ps1 env.cmd   UPR_WORKSPACE, PS2RC_LOCAL, PS2RC_TOOLCHAIN for a shell
```

Run PS2RC's commands inside `<workspace>/PS2RC` (for example `python -m ps2rc doctor`,
`bash mk/build.sh --pack example host`). Paths in the skills such as `ps2rc/`, `hle/`, `mk/`, `games/`, `tools/` and
`PS2RC/docs/...` are paths in that checkout.

## 4. The user's game pack

```
python skills/setup-ps2rc/setup_ps2rc.py new-pack <SERIAL> <VERSION> [--region PAL|NTSC-U|NTSC-J] [--git]
```

- Copies **only** PS2RC's `games/_template` to `<workspace>/packs/<SERIAL>_v<VERSION>/`, fills `[id]`, writes a pack
  README with the credit block and a `.gitignore` for disc and build files, and links the pack into
  `PS2RC/games/<name>` (a directory junction on Windows, a symbolic link elsewhere; a copy if neither works - then
  edit `packs/` and run `link` again).
- Why outside the checkout: PS2RC finds packs only under its `games/` folder (`ps2rc/pack.py`, the source index in
  `ps2rc/config.py`, the converter's `ps2rc/convert/identify.py`), so the pack must appear there; keeping the real
  folder in `packs/` lets `update` replace the engine without touching the user's work, and lets the pack be its own
  small git repository (`--git`) that never contains PS2RC or a listed disc's pack.
- Refused: a serial that a `DISTRIBUTION.md` in PS2RC (or the lock's `listed` list) names; PS2RC v0.1.1 and earlier
  name that notice `RESERVED.md`, which is still detected. Work based on PS2RC for a listed disc is distributed only
  by the PS2RC project; the user converts their own copy with PS2RC's own pack and converter.
- Check a pack at any time, and always before anything is shared:

  ```
  python skills/setup-ps2rc/setup_ps2rc.py check-pack <SERIAL>_v<VERSION>
  ```

  It fails on: a listed serial, a file identical to one of a listed disc's pack, six or more lines in a row shared
  with such a pack (beyond what `_template` and `example` also contain), disc or build file types, files over 512 KB.
  You may **read** a listed disc's pack to see how a real pack is structured; never copy its code, lists, hooks or values
  into another pack.

## 5. Status, verify, link, update

```
python skills/setup-ps2rc/setup_ps2rc.py status [--json]     # versions, packs, links, local.toml in sync
python skills/setup-ps2rc/setup_ps2rc.py verify              # the checkout against the installed release
python skills/setup-ps2rc/setup_ps2rc.py link [--copy]       # after editing local.toml, or when a link is missing
python skills/setup-ps2rc/setup_ps2rc.py update [--tag vX.Y.Z] [--dry-run] [--with-converter]
```

`update` installs another pinned release (default: the kit's default; `git pull` the kit first to get newer pins):
it fetches and verifies the new tree next to the old one, removes only the pack links, moves the old checkout to
`PS2RC.backup-<tag>-<time>`, puts the new one in place, links the packs again and copies `local.toml`. The packs in
`packs/` are never touched. It refuses when the old checkout has changes (the user's edits to the engine) unless
`--accept-backup`; engine fixes belong in pull requests to PS2RC. A tag the kit does not pin needs
`--allow-unpinned` and is recorded as unpinned - ask the user first. After an update: PS2RC's doctor, the example
pack, then the user's pack's host build (`skills/ps2rc-translate`).

The workspace is found from `--workspace`, else `UPR_WORKSPACE` (set by `env.*`), else the current folder or a parent
with `ps2rc-workspace.json`. Record the workspace path in `PORT_STATE.md`.
