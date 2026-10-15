#!/usr/bin/env python3
"""doctor.py - what this machine has for a PS2 -> PSP port with PS2RC, what is missing, and where to get it.

    python doctor.py [--workspace DIR] [--json] [--wsl] [--online]

Reads nothing of any game, installs nothing, downloads nothing (--online only asks GitHub whether the PS2RC release
page answers). Every tool is looked for in the environment variables that name it, on PATH and in the standard
install places of this OS; nothing is assumed to be anywhere. For each missing item it prints the official source,
the version this kit was checked with and the SHA-256 the source publishes, when it publishes one. Always ask the
user before downloading or installing anything; say what, from where and how big.

--wsl   on Windows: also look inside the default WSL distribution (pspdev, gcc, make); starts WSL if it is stopped.
"""
import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = os.name == "nt"

# Official sources, checked when this kit was released (docs/DEPENDENCIES.md has the same table and the research
# procedure for a link that died). "sha256" is copied from what the source itself publishes.
DEPS = {
    "python": dict(what="Python 3.11 or newer (PS2RC's tools; 3.13 / 3.14 recommended)",
                   url="https://www.python.org/downloads/",
                   how_win="the 64-bit Windows installer from python.org (tick 'Add python.exe to PATH'); the release "
                           "page lists each file's SHA-256 and Sigstore signature",
                   how_linux="the distribution's package (python3, python3-pip, python3-venv); python.org for sources"),
    "pymods": dict(what="pyelftools and pytest (Python packages PS2RC uses)",
                   url="https://pypi.org/project/pyelftools/",
                   how_win="python -m pip install --user pyelftools pytest",
                   how_linux="python3 -m pip install --user pyelftools pytest (or the distribution's python3-pyelftools "
                             "python3-pytest)"),
    "git": dict(what="git (downloads PS2RC, keeps your pack's history)",
                url="https://git-scm.com/downloads",
                how_win="Git for Windows from https://github.com/git-for-windows/git/releases/latest (checked: "
                        "release v2.56.0.windows.2, its 64-bit .exe installer, 66,763,664 bytes, sha256 "
                        "52188f917b378f00c70ec136bcf090005f30d44fbc4eba0bce759cc6592d60f6); without git the setup "
                        "uses the release's source zip",
                how_linux="the distribution's package (git)"),
    "ps2rc": dict(what="PS2RC, the recompiler engine (in the workspace)",
                  url="https://github.com/SandstoneDev/PS2RC/releases",
                  how_win="python skills/setup-ps2rc/setup_ps2rc.py setup --workspace <folder>",
                  how_linux="python3 skills/setup-ps2rc/setup_ps2rc.py setup --workspace <folder>"),
    "psp-toolchain": dict(what="PSP toolchain (psp-gcc + PSPSDK)",
                          url="https://github.com/pspdev/pspdev/releases/latest",
                          how_win="easiest: the PS2RC converter release with its own native toolchain "
                                  "(setup_ps2rc.py setup|update --with-converter, about 104 MB, sha256 pinned in "
                                  "ps2rc.lock.json); for the build scripts (mk/*.sh): WSL with Ubuntu + pspdev as "
                                  "https://pspdev.github.io/installation/windows.html describes",
                          how_linux="pspdev release v20261001 (checked): pspdev-ubuntu-latest-x86_64.tar.gz "
                                    "(172,980,272 bytes, sha256 "
                                    "a86efe624e770005290919617859e9df24bd8fcd3e364f4587f23ec7364b0acd) or "
                                    "pspdev-debian-latest.tar.gz (sha256 "
                                    "39b20efc7c8492cdbd9929178f45afc801dabb0967b7c882573520f22536920c); unpack into "
                                    "~/pspdev and export PSPDEV=$HOME/pspdev; PATH=$PSPDEV/bin:$PATH "
                                    "(https://pspdev.github.io/installation.html)"),
    "wsl": dict(what="WSL 2 with a Linux distribution (runs PS2RC's shell build scripts on Windows)",
                url="https://learn.microsoft.com/windows/wsl/install",
                how_win="wsl --install in an elevated PowerShell (installs Ubuntu), then restart Windows",
                how_linux="not needed on Linux"),
    "host-gcc": dict(what="native gcc, make and zlib headers (the PC host build of a translated game)",
                     url="https://gcc.gnu.org/",
                     how_win="inside WSL: sudo apt install build-essential zlib1g-dev",
                     how_linux="sudo apt install build-essential zlib1g-dev (Debian / Ubuntu) or the "
                               "distribution's gcc, make, zlib-devel"),
    "ffmpeg": dict(what="ffmpeg and ffprobe (intro movies, animated menu icon) - optional",
                   url="https://ffmpeg.org/download.html",
                   how_win="the PS2RC converter release brings its own (--with-converter); or a Windows build linked "
                           "from ffmpeg.org (https://github.com/BtbN/FFmpeg-Builds/releases/latest publishes "
                           "checksums.sha256)",
                   how_linux="the distribution's package (ffmpeg)"),
    "ppsspp": dict(what="PPSSPP emulator (yes/no boot checks only) - optional, recommended",
                   url="https://www.ppsspp.org/download/",
                   how_win="v1.20.4 (checked): PPSSPP-v1.20.4-Windows-x64.zip from "
                           "https://github.com/hrydgard/ppsspp/releases (20,390,334 bytes, sha256 "
                           "fbc9cd2f5131b159a92424e5c458c35ce43ba603cdded64dfc98e4bd4f17ff93) or the installer on "
                           "ppsspp.org; then set [tools] ppsspp_dir in the workspace's local.toml",
                   how_linux="PPSSPP-v1.20.4-anylinux-x86_64.AppImage from https://github.com/hrydgard/ppsspp/releases "
                             "(sha256 661c098e6b7f7610171a57b7c533ce8bba6f2312b71e76d61e850461973eba21), or Flathub "
                             "org.ppsspp.PPSSPP"),
    "pcsx2": dict(what="PCSX2 emulator (reference runs; needs a BIOS dumped from the user's own PS2) - optional",
                  url="https://pcsx2.net/downloads",
                  how_win="v2.8.2 (checked): pcsx2-v2.8.2-windows-x64-installer.exe from "
                          "https://github.com/PCSX2/pcsx2/releases (46,714,216 bytes, sha256 "
                          "3422f3705ccc641b7e4fdf3f280d635d05c3c8b53a56c3af55d9df115bdcf768)",
                  how_linux="pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage from https://github.com/PCSX2/pcsx2/releases "
                            "(sha256 0c46bb6a88aa2782b10853a7b07cf3387ba99cbef2b966372cd2315b8571abea), or Flathub "
                            "net.pcsx2.PCSX2"),
}


class Check:
    def __init__(self, id, need, state, found="", note=""):
        self.id, self.need, self.state, self.found, self.note = id, need, state, found, note

    def hint(self):
        d = DEPS.get(self.id)
        if not d or self.state == "ok":
            return ""
        s = "%s. Get it: %s (%s)" % (d["what"], d["how_win"] if WIN else d["how_linux"], d["url"])
        if self.id in ("ppsspp", "pcsx2", "ffmpeg", "psp-toolchain", "git"):
            s += ". Installed somewhere else? Ask the user for the folder and record it (local.toml [tools])"
        return s

    def as_dict(self):
        return dict(id=self.id, need=self.need, state=self.state, found=self.found, note=self.note, hint=self.hint())


def run(argv, timeout=20, inp=None):
    try:
        r = subprocess.run(argv, input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return r.returncode, r.stdout
    except (OSError, subprocess.SubprocessError):
        return -1, b""


def which_any(names, extra_dirs=()):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    for d in extra_dirs:
        for n in names:
            for p in glob.glob(os.path.join(d, n)):
                if os.path.isfile(p):
                    return p
    return None


def env_dirs(*parts_list):
    """Standard Windows install folders built from environment variables (never fixed drive letters)."""
    out = []
    for var, sub in parts_list:
        base = os.environ.get(var)
        if base:
            out.append(os.path.join(base, *sub.split("/")))
    return out


def os_info():
    rel = platform.release()
    wsl = False
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/version", encoding="utf-8", errors="replace") as f:
                wsl = "microsoft" in f.read().lower()
        except OSError:
            pass
    kind = "windows" if WIN else ("wsl" if wsl else ("linux" if sys.platform.startswith("linux") else sys.platform))
    return dict(kind=kind, system=platform.system(), release=rel, version=platform.version(),
                machine=platform.machine(), python=platform.python_version())


def load_manifest(ws):
    p = os.path.join(ws, "ps2rc-workspace.json") if ws else None
    if p and os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def lock_default():
    try:
        with open(os.path.join(HERE, "ps2rc.lock.json"), encoding="utf-8") as f:
            return json.load(f)["default"]
    except (OSError, ValueError, KeyError):
        return None


def local_toml_tool(ws, key):
    p = os.path.join(ws, "local.toml") if ws else None
    if not p or not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        m = re.search(r'^\s*%s\s*=\s*"([^"]+)"' % re.escape(key), f.read(), re.M)
    return m.group(1) if m else None


def wsl_probe():
    """(distro list, shell script output) from the default WSL distribution, or (None, '')."""
    if not shutil.which("wsl.exe") and not shutil.which("wsl"):
        return None, ""
    rc, out = run(["wsl.exe", "-l", "-q"], timeout=20)
    if rc != 0:
        return [], ""
    names = [x.strip() for x in out.decode("utf-16-le", "replace").replace("\x00", "").splitlines() if x.strip()]
    script = ('for d in "$PSPDEV" "$HOME/pspdev" /usr/local/pspdev; do [ -x "$d/bin/psp-gcc" ] && '
              'echo "pspdev=$d" && "$d/bin/psp-gcc" -dumpversion | sed "s/^/pspgcc=/" && break; done; '
              'command -v gcc >/dev/null && echo "gcc=$(gcc -dumpversion)"; '
              'command -v make >/dev/null && echo make=yes; '
              '[ -f /usr/include/zlib.h ] && echo zlib=yes; true\n')
    rc, out = run(["wsl.exe", "-e", "bash", "-s"], timeout=60, inp=script.encode())
    return names, out.decode("utf-8", "replace") if rc == 0 else ""


def checks(ws=None, use_wsl=False, online=False):
    out = []
    info = os_info()
    v = sys.version_info
    out.append(Check("python", "required", "ok" if v >= (3, 11) else "old", sys.executable,
                     "Python %d.%d.%d%s" % (v[0], v[1], v[2], "" if v >= (3, 11) else ": PS2RC needs 3.11+")))
    missing = []
    for mod, name in (("elftools", "pyelftools"), ("pytest", "pytest")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(name)
    out.append(Check("pymods", "required", "missing" if missing else "ok", "",
                     ("missing: " + ", ".join(missing)) if missing else "pyelftools, pytest"))
    git = which_any(["git"], env_dirs(("ProgramFiles", "Git/cmd")) if WIN else ())
    out.append(Check("git", "recommended", "ok" if git else "missing", git or ""))

    m = load_manifest(ws)
    if not ws:
        out.append(Check("ps2rc", "required", "missing", "", "no workspace given (--workspace or UPR_WORKSPACE)"))
    elif not m:
        out.append(Check("ps2rc", "required", "missing", ws, "not a workspace yet"))
    else:
        r = m.get("ps2rc") or {}
        want = lock_default()
        st = "ok" if os.path.isdir(os.path.join(ws, "PS2RC")) else "missing"
        note = "PS2RC %s (commit %s, %s)" % (r.get("tag"), (r.get("commit") or "?")[:12],
                                           "pinned" if r.get("pinned") else "unpinned")
        if want and r.get("tag") != want:
            note += "; the kit pins %s: setup_ps2rc.py update" % want
            st = "old" if st == "ok" else st
        out.append(Check("ps2rc", "required", st, os.path.join(ws, "PS2RC"), note))
        try:
            free = shutil.disk_usage(ws).free / 1e9
            out.append(Check("disk", "required", "ok" if free >= 10 else "low", ws,
                             "%.0f GB free (plan at least 10 GB per game plus the disc image)" % free))
        except OSError:
            pass

    # PSP toolchain: explicit variables first, then the workspace's converter, then PATH and standard folders
    tc, how = None, ""
    exe = "psp-gcc.exe" if WIN else "psp-gcc"
    cands = [("PS2RC_TOOLCHAIN", os.environ.get("PS2RC_TOOLCHAIN"))]
    if m and m.get("converter") and m["converter"].get("toolchain"):
        cands.append(("workspace converter", os.path.join(ws, m["converter"]["toolchain"])))
    cands += [("PSPDEV", os.environ.get("PSPDEV")), ("~/pspdev", os.path.expanduser("~/pspdev"))]
    if not WIN:
        cands.append(("/usr/local/pspdev", "/usr/local/pspdev"))
    for label, d in cands:
        if d and os.path.isfile(os.path.join(d, "bin", exe)):
            tc, how = os.path.join(d, "bin", exe), label
            break
    if not tc and shutil.which("psp-gcc"):
        tc, how = shutil.which("psp-gcc"), "PATH"
    wsl_out = ""
    if WIN:
        names = None
        if use_wsl:
            names, wsl_out = wsl_probe()
        wsl_ok = bool(shutil.which("wsl.exe"))
        out.append(Check("wsl", "recommended", "ok" if (names if use_wsl else wsl_ok) else "missing",
                         ", ".join(names) if names else ("wsl.exe" if wsl_ok else ""),
                         "" if use_wsl else "distributions not probed (add --wsl)"))
        mm = re.search(r"pspdev=(\S+)", wsl_out)
        if not tc and mm:
            tc, how = "WSL:" + mm.group(1), "WSL"
    out.append(Check("psp-toolchain", "required", "ok" if tc else "missing", tc or "", how))

    if WIN:
        if use_wsl:
            ok = "gcc=" in wsl_out and "make=yes" in wsl_out and "zlib=yes" in wsl_out
            out.append(Check("host-gcc", "required", "ok" if ok else "missing", "WSL",
                             " ".join(x for x in wsl_out.split() if x.startswith(("gcc=", "make=", "zlib=")))))
        else:
            out.append(Check("host-gcc", "required", "unknown", "", "runs inside WSL: add --wsl to look"))
    else:
        gcc, make = shutil.which("gcc"), shutil.which("make")
        zlib = os.path.exists("/usr/include/zlib.h")
        out.append(Check("host-gcc", "required", "ok" if gcc and make and zlib else "missing", gcc or "",
                         "gcc %s, make %s, zlib.h %s" % (bool(gcc), bool(make), zlib)))

    conv = os.path.join(ws, "converter") if ws else None
    ff = which_any(["ffmpeg"], glob.glob(os.path.join(conv, "*", "tools", "ffmpeg")) if conv else ())
    if not ff and local_toml_tool(ws, "ffmpeg"):
        ff = local_toml_tool(ws, "ffmpeg") if os.path.exists(local_toml_tool(ws, "ffmpeg")) else None
    out.append(Check("ffmpeg", "optional", "ok" if ff else "missing", ff or ""))

    pp_dirs = []
    if WIN:
        pp_dirs = env_dirs(("ProgramFiles", "PPSSPP"), ("ProgramFiles(x86)", "PPSSPP"),
                           ("LOCALAPPDATA", "Programs/PPSSPP"))
    lt = local_toml_tool(ws, "ppsspp_dir")
    if lt:
        pp_dirs.insert(0, lt)
    pp = which_any(["PPSSPPWindows64.exe", "PPSSPPWindows.exe", "PPSSPPSDL", "PPSSPPQt", "ppsspp", "ppsspp-emu",
                    "PPSSPP*.AppImage"], pp_dirs + ([os.path.expanduser("~/Applications"), "/snap/bin"]
                                                     if not WIN else []))
    if not pp and not WIN and shutil.which("flatpak"):
        rc, _o = run(["flatpak", "info", "org.ppsspp.PPSSPP"])
        pp = "flatpak org.ppsspp.PPSSPP" if rc == 0 else None
    out.append(Check("ppsspp", "optional", "ok" if pp else "missing", pp or "",
                     "" if (lt or not pp or not WIN) else "set [tools] ppsspp_dir = \"%s\" in the workspace's "
                     "local.toml" % os.path.dirname(pp).replace("\\", "/")))
    px_dirs = env_dirs(("ProgramFiles", "PCSX2"), ("LOCALAPPDATA", "Programs/PCSX2")) if WIN else \
        [os.path.expanduser("~/Applications")]
    px = which_any(["pcsx2-qt.exe", "pcsx2-qt", "pcsx2", "pcsx2*.AppImage"], px_dirs)
    if not px and not WIN and shutil.which("flatpak"):
        rc, _o = run(["flatpak", "info", "net.pcsx2.PCSX2"])
        px = "flatpak net.pcsx2.PCSX2" if rc == 0 else None
    out.append(Check("pcsx2", "optional", "ok" if px else "missing", px or ""))

    if online:
        try:
            req = urllib.request.Request("https://github.com/SandstoneDev/PS2RC/releases", method="HEAD",
                                         headers={"User-Agent": "universal-ps2-recompiler-doctor/1"})
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
        except Exception as e:                                  # noqa: BLE001 - any failure is the answer
            code = getattr(e, "code", None) or str(e)
        out.append(Check("github", "required", "ok" if code == 200 else "unreachable", "github.com/SandstoneDev/PS2RC",
                         "HTTP %s%s" % (code, "" if code == 200 else ": private, renamed or no network")))
    return info, out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="doctor.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--workspace")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--wsl", action="store_true")
    ap.add_argument("--online", action="store_true")
    a = ap.parse_args(argv)
    ws = a.workspace or os.environ.get("UPR_WORKSPACE")
    ws = os.path.abspath(os.path.expanduser(ws)) if ws else None
    info, cs = checks(ws, a.wsl, a.online)
    if a.json:
        print(json.dumps(dict(os=info, checks=[c.as_dict() for c in cs]), indent=2))
    else:
        print("machine: %s %s %s (%s), Python %s" % (info["kind"], info["release"], info["machine"],
                                                     info["version"][:40], info["python"]))
        if info["kind"] not in ("windows", "linux", "wsl"):
            print("  note: PS2RC targets Windows 10/11 x64 first and Linux/WSL second; this OS is Unknown")
        for c in cs:
            tag = {"ok": "ok  ", "missing": "MISS", "old": "OLD ", "low": "LOW ", "unknown": "??  "}.get(c.state, "!!  ")
            if c.state != "ok" and c.need == "optional":
                tag = "opt "
            print("[%s] %-14s %s%s" % (tag, c.id, c.found or "-", ("  (" + c.note + ")") if c.note else ""))
            if c.hint():
                print("        " + c.hint())
    bad = [c for c in cs if c.need == "required" and c.state not in ("ok", "unknown")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
