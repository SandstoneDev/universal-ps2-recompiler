# Dependencies: what a port needs and where to get it

Nothing here is assumed to be installed or to be in a particular folder. `python -m uprkit doctor` (or
`python skills/setup-ps2rc/setup_ps2rc.py doctor`) looks for each item in the environment variables that name it, on
PATH and in the standard install places of the operating system, and prints what is missing with the source below.
If a tool is installed somewhere it does not look, ask the user for the folder and record it in the workspace's
`local.toml` (`[tools]`).

**Ask before every download or install**: say what, from where, how big, and where it goes. Prefer the user's
package manager on Linux. Never download from mirrors or re-uploads when the official source works.

Supported systems: **Windows 10 / 11 x64 first** (as PS2RC: its converter release brings Python, the PSP toolchain and
ffmpeg), **Linux and WSL 2 second** (PS2RC's build scripts are shell scripts; on Windows they run in WSL). macOS:
Unknown (the host build harness is written for x86-64 Linux).

## Sources (checked 2026-10-15)

"Checked" values were read from the official release pages when this kit was released; the SHA-256 values are the ones
the source publishes. Newer versions are fine unless a note says otherwise: then compare the file with the SHA-256 the
release page shows at download time.

| Item | Need | Official source | Checked version, file, SHA-256 |
|---|---|---|---|
| PS2RC (the engine) | required | https://github.com/SandstoneDev/PS2RC/releases | pinned in `skills/setup-ps2rc/ps2rc.lock.json`: v0.2.1 (default; v0.2.0 and v0.1.1 still pinned), commit 8cd56bb6feee32f963d6e430ff0eda85565d1005, content hash there; installed by `setup_ps2rc.py setup` |
| PS2RC converter with the Windows PSP toolchain and ffmpeg | Windows, optional | same release page | `PS2RC_Converter_0.2.1_win64.zip`, 124,742,607 bytes, sha256 d3862664a8d9dc0d1124476feb4a5eed0ae602245b2debe12fba7a206b98b5e6 (`setup --with-converter`) |
| Python 3.11 or newer | required | https://www.python.org/downloads/ | any current 3.13 or 3.14 release; each release page lists the files' SHA-256 and Sigstore signatures. Windows: the 64-bit installer, tick "Add python.exe to PATH". Linux: the distribution's python3 |
| pyelftools, pytest | required | https://pypi.org/project/pyelftools/ , https://pypi.org/project/pytest/ | `python -m pip install --user pyelftools pytest` |
| git | recommended | https://git-scm.com/downloads | Windows: https://github.com/git-for-windows/git/releases/latest, release v2.56.0.windows.2, 64-bit .exe installer, 66,763,664 bytes, sha256 52188f917b378f00c70ec136bcf090005f30d44fbc4eba0bce759cc6592d60f6. Without git the setup uses the release's source zip |
| WSL 2 + Ubuntu | Windows, for the build scripts | https://learn.microsoft.com/windows/wsl/install | `wsl --install` in an elevated PowerShell, then restart Windows |
| PSP toolchain (pspdev: psp-gcc + PSPSDK) | required for PSP builds | https://github.com/pspdev/pspdev/releases/latest , guide https://pspdev.github.io/installation.html | v20261001: `pspdev-ubuntu-latest-x86_64.tar.gz` 172,980,272 bytes, sha256 a86efe624e770005290919617859e9df24bd8fcd3e364f4587f23ec7364b0acd; `pspdev-debian-latest.tar.gz` sha256 39b20efc7c8492cdbd9929178f45afc801dabb0967b7c882573520f22536920c; `pspdev-fedora-latest.tar.gz` sha256 7874d4d696f1abe58d3d17fd8ae365e9b129c4bea16b383bf708655037c0e21c. Unpack to `~/pspdev`, `export PSPDEV=$HOME/pspdev` and `PATH=$PSPDEV/bin:$PATH`. On Windows inside WSL (https://pspdev.github.io/installation/windows.html), or the converter's native toolchain |
| gcc, make, zlib headers | required for the PC host build | https://gcc.gnu.org/ | the distribution's packages: `sudo apt install build-essential zlib1g-dev` (Debian, Ubuntu, WSL) |
| ffmpeg, ffprobe | optional (movies, animated icon) | https://ffmpeg.org/download.html | Windows: inside the PS2RC converter, or a build linked from ffmpeg.org (https://github.com/BtbN/FFmpeg-Builds/releases/latest publishes `checksums.sha256`). Linux: the distribution's ffmpeg |
| PPSSPP | optional, recommended (yes/no boot checks) | https://www.ppsspp.org/download/ , https://github.com/hrydgard/ppsspp/releases | v1.20.4: `PPSSPP-v1.20.4-Windows-x64.zip` 20,390,334 bytes, sha256 fbc9cd2f5131b159a92424e5c458c35ce43ba603cdded64dfc98e4bd4f17ff93; `PPSSPP-v1.20.4-anylinux-x86_64.AppImage` sha256 661c098e6b7f7610171a57b7c533ce8bba6f2312b71e76d61e850461973eba21. Then `[tools] ppsspp_dir` in `local.toml` |
| PCSX2 | optional (reference runs) | https://pcsx2.net/downloads , https://github.com/PCSX2/pcsx2/releases | v2.8.2: `pcsx2-v2.8.2-windows-x64-installer.exe` 46,714,216 bytes, sha256 3422f3705ccc641b7e4fdf3f280d635d05c3c8b53a56c3af55d9df115bdcf768; `pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage` sha256 0c46bb6a88aa2782b10853a7b07cf3387ba99cbef2b966372cd2315b8571abea. Needs a BIOS dumped by the user from their own PS2: never download one |
| Public reference documents | optional | `skills/fetch-docs/SKILL.md` | its catalogue: URLs, licences, sizes; index with SHA-256 |

Never needed and never downloaded: game images, PS2 BIOS files, PSP firmware, keys, custom firmware, console-maker SDK
material. The user's PSP runs custom firmware they installed themselves; do not link to any.

## Order on a new machine

1. Python (and pip packages), git.
2. `setup_ps2rc.py setup --workspace <folder>` (PS2RC; on Windows optionally `--with-converter`).
3. Windows: WSL 2 with Ubuntu, then pspdev and build-essential inside it. Linux: pspdev and build-essential.
4. PS2RC's own check inside `<workspace>/PS2RC`: `python -m ps2rc doctor`, then the example pack
   (`skills/psp-build-test`).
5. Optional tools when a phase needs them: PPSSPP (phase 7), PCSX2 (hard HLE bugs), ffmpeg (movies, menu icon).

## When a link is dead or a version is gone

Do the research yourself, then tell the user what you found and ask before downloading:

1. Re-check the exact URL once (a temporary error is common); then open the project's official home page (the table's
   first column) and follow its own download link.
2. Moved repository: search the code host for the repository name and accept a new home only if it is the same
   project (same owner or an announcement from it). Release assets: the project's releases page lists every version;
   take the newest that matches the system, and its published SHA-256.
3. A page or document that disappeared: the Wayback Machine (`https://web.archive.org/web/2024*/<url>`, or
   `python skills/fetch-docs/fetch_docs.py wayback <url>`), then the project's own announcements.
4. Search queries that work: `"<project> releases"`, `"<project> download windows x64"`, `"<file name>"` with the
   exact name from the table, `site:github.com <project>`. Prefer the project's own domain and its code-host
   organisation over any third party.
5. Record what you used (URL, version, SHA-256, date) in `PORT_STATE.md`. If nothing official exists any more, say
   Unknown and ask the user; never take a binary from an unofficial host.
