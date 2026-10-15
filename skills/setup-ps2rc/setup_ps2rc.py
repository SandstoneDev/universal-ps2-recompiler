#!/usr/bin/env python3
"""setup_ps2rc.py - download PS2RC (the recompiler engine) into a workspace and keep the user's game packs next to it.

    python setup_ps2rc.py setup   [--workspace DIR] [--tag TAG] [--method auto|git|zip] [--with-converter]
                                  [--source GIT_URL_OR_DIR] [--zip FILE] [--converter-zip FILE] [--dry-run] [--yes]
    python setup_ps2rc.py status  [--workspace DIR] [--json]
    python setup_ps2rc.py verify  [--workspace DIR]
    python setup_ps2rc.py update  [--workspace DIR] [--tag TAG] [--accept-backup] [--dry-run] (+ setup's source options)
    python setup_ps2rc.py new-pack SERIAL VERSION [--region R] [--workspace DIR] [--git]
    python setup_ps2rc.py link    [--workspace DIR] [--copy]
    python setup_ps2rc.py check-pack NAME [--workspace DIR]
    python setup_ps2rc.py doctor  [--workspace DIR] [--json] [--wsl] [--online]   (doctor.py next to this script)

A workspace is one folder on the user's PC:

    <workspace>/
      ps2rc-workspace.json   the manifest: PS2RC version, commit, how it was verified, packs, history
      PS2RC/                 the engine checkout at a pinned release (replaced by `update`, never edited for a port)
      packs/<SERIAL>_v<VER>/ the user's own game packs (made from PS2RC's games/_template), linked into PS2RC/games/
      work/                  everything made from the user's disc (PS2RC's local.toml [paths] work) - never shared
      refdocs/               public reference documents (skills/fetch-docs)
      downloads/             release archives with their SHA-256
      converter/             optional: the prebuilt PS2RC converter (with the Windows PSP toolchain)
      local.toml             PS2RC's per-machine settings (copied into PS2RC/ by setup / update / link)
      env.sh env.ps1 env.cmd environment for shells (PS2RC_LOCAL, PS2RC_TOOLCHAIN)

Only the Python standard library is used (git is used when it is installed). Everything that is downloaded is checked
against ps2rc.lock.json next to this script: the release tag must point at the pinned commit and the downloaded tree
must have the pinned content hash. Nothing is uploaded or sent anywhere. No game data is read or written here.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(HERE, "ps2rc.lock.json")
MANIFEST = "ps2rc-workspace.json"
CHECKOUT = "PS2RC"
FILELIST = ".ps2rc-files.sha256"
COPY_STAMP = ".uprkit-pack-copy"
LOCAL_HEADER = "# Copy of the workspace's local.toml, written by setup_ps2rc.py. Edit the workspace's file, then run link."
UA = "universal-ps2-recompiler-setup/1 (+https://github.com/SandstoneDev/universal-ps2-recompiler)"
SERIAL_RX = re.compile(r"^[A-Z]{4}-\d{5}$")
VERSION_RX = re.compile(r"^\d{1,2}\.\d{2}$")
REGIONS = ("NTSC-U", "NTSC-J", "PAL", "NTSC-K", "NTSC-C")
GENERATED = ("__pycache__", ".pytest_cache")
EXIT_PRIVATE = 4


class SetupError(Exception):
    def __init__(self, msg, code=1):
        Exception.__init__(self, msg)
        self.code = code


def say(*a):
    print(*a)
    sys.stdout.flush()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")


def fwd(p):
    return os.path.abspath(p).replace("\\", "/")


# ---------------------------------------------------------------- lock, manifest

def load_lock(path=None):
    with open(path or LOCK_FILE, encoding="utf-8") as f:
        lock = json.load(f)
    if lock.get("format") != 1:
        raise SetupError("%s: unknown lock format" % (path or LOCK_FILE))
    return lock


def release(lock, tag, allow_unpinned=False):
    rel = lock["releases"].get(tag)
    if rel:
        return dict(rel, tag=tag, pinned=True)
    if not allow_unpinned:
        raise SetupError("PS2RC %s is not pinned in this kit (pinned: %s). Update the kit (git pull) to get a newer "
                         "lock, or pass --allow-unpinned to trust the tag as it is now (recorded as unpinned)."
                         % (tag, ", ".join(sorted(lock["releases"]))))
    return {"tag": tag, "pinned": False, "commit": None, "tree_sha256": None, "assets": {},
            "source_zip": {"url": "%s/archive/refs/tags/%s.zip" % (lock["url"], tag)}}


def manifest_path(ws):
    return os.path.join(ws, MANIFEST)


def load_manifest(ws, required=True):
    p = manifest_path(ws)
    if not os.path.exists(p):
        if required:
            raise SetupError("%s is not a PS2RC workspace (no %s). Run: setup_ps2rc.py setup --workspace <dir>"
                             % (ws, MANIFEST))
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(ws, m):
    p = manifest_path(ws)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, p)


def find_workspace(arg):
    """--workspace, else UPR_WORKSPACE, else the current folder or a parent that holds a manifest."""
    if arg:
        return os.path.abspath(os.path.expanduser(arg))
    env = os.environ.get("UPR_WORKSPACE")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    d = os.getcwd()
    while True:
        if os.path.exists(os.path.join(d, MANIFEST)):
            return d
        up = os.path.dirname(d)
        if up == d:
            raise SetupError("no workspace given: pass --workspace DIR (or set UPR_WORKSPACE)")
        d = up


# ---------------------------------------------------------------- hashing

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tree_hash(rows):
    """rows: [(path, sha256)] -> SHA-256 of '<sha256>  <path>\\n' lines sorted by path."""
    return hashlib.sha256("".join("%s  %s\n" % (h, p) for p, h in sorted(rows)).encode("utf-8")).hexdigest()


def zip_rows(zpath):
    """[(path below the top folder, sha256)], top folder, zip comment. Refuses links and unsafe names."""
    rows, tops = [], set()
    with zipfile.ZipFile(zpath) as z:
        comment = z.comment.decode("ascii", "replace").strip()
        for i in z.infolist():
            name = i.filename
            if name.startswith("/") or "\\" in name or re.match(r"^[A-Za-z]:", name) or ".." in name.split("/"):
                raise SetupError("%s: unsafe member name %r" % (zpath, name))
            if stat.S_ISLNK((i.external_attr >> 16) & 0xFFFF):
                raise SetupError("%s: symbolic link %r in the archive (refused)" % (zpath, name))
            top, _, rel = name.partition("/")
            tops.add(top)
            if i.is_dir() or not rel:
                continue
            rows.append((rel, hashlib.sha256(z.read(i)).hexdigest()))
    if len(tops) != 1:
        raise SetupError("%s: expected one top folder, found %d" % (zpath, len(tops)))
    return rows, tops.pop(), comment


def safe_extract(zpath, dest, strip_top=True):
    with zipfile.ZipFile(zpath) as z:
        for i in z.infolist():
            name = i.filename
            if name.startswith("/") or "\\" in name or ".." in name.split("/") or re.match(r"^[A-Za-z]:", name):
                raise SetupError("%s: unsafe member name %r" % (zpath, name))
            if stat.S_ISLNK((i.external_attr >> 16) & 0xFFFF):
                raise SetupError("%s: symbolic link %r in the archive (refused)" % (zpath, name))
            rel = name.split("/", 1)[1] if strip_top else name
            if not rel:
                continue
            out = os.path.join(dest, *rel.split("/"))
            if not os.path.abspath(out).startswith(os.path.abspath(dest) + os.sep):
                raise SetupError("%s: member %r leaves the destination" % (zpath, name))
            if i.is_dir():
                os.makedirs(out, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with z.open(i) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)


# ---------------------------------------------------------------- downloads

def http_get(url, dest, expect_size=None, say=say):
    """Download url to dest (via dest.part). Raises SetupError with a plain message (private repo, missing tag)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    part = dest + ".part"
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0) or expect_size or 0
            got, last = 0, -1
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
                got += len(b)
                pct = int(got * 100 / total) if total else -1
                if total and pct // 10 != last // 10:
                    say("  %3d %%  %.1f / %.1f MB" % (pct, got / 1e6, total / 1e6))
                    last = pct
    except urllib.error.HTTPError as e:
        _rm(part)
        if e.code in (401, 403, 404):
            raise SetupError(private_message(url, "HTTP %d" % e.code), EXIT_PRIVATE)
        raise SetupError("download failed: %s: HTTP %d" % (url, e.code))
    except (urllib.error.URLError, OSError) as e:
        _rm(part)
        raise SetupError("download failed: %s: %s (no network? a proxy?)" % (url, e))
    os.replace(part, dest)
    return dest


def private_message(where, detail):
    return ("cannot get PS2RC from %s (%s).\n"
            "  The PS2RC repository may be private (not public yet), the release tag may not exist, or you have no\n"
            "  access. What to do: wait until github.com/SandstoneDev/PS2RC is public, or ask its maintainer for\n"
            "  access (then sign in to git), or point this script at a copy you already have:\n"
            "  --source <git URL or local clone> or --zip <the release's source zip>." % (where, detail))


def _rm(p):
    try:
        os.remove(p)
    except OSError:
        pass


def have_git():
    return shutil.which("git") is not None


def git(*args, cwd=None, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never", LC_ALL="C")
    r = subprocess.run(["git"] + list(args), cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    if check and r.returncode != 0:
        raise SetupError("git %s: %s" % (" ".join(args[:2]), err.strip() or out.strip()))
    return r.returncode, out, err


# ---------------------------------------------------------------- fetching one release

def source_url(lock, source):
    if not source:
        return lock["url"] + ".git"
    if os.path.isdir(source):
        return "file://" + fwd(source) if not fwd(source).startswith("/") else "file://" + fwd(source)
    return source


def fetch_git(lock, rel, dest, source=None, say=say):
    url = source_url(lock, source)
    say("git clone --depth 1 --branch %s %s" % (rel["tag"], url))
    rc, out, err = git("-c", "advice.detachedHead=false", "clone", "--quiet", "--depth", "1", "--single-branch",
                       "--branch", rel["tag"], url, dest, check=False)
    if rc != 0:
        low = err.lower()
        if any(s in low for s in ("not found", "authentication", "could not read username", "access denied",
                                   "403", "401", "terminal prompts disabled", "does not appear to be a git")):
            raise SetupError(private_message(url, err.strip().splitlines()[-1] if err.strip() else "git error"),
                             EXIT_PRIVATE)
        if "remote branch" in low and "not found" in low:
            raise SetupError("tag %s does not exist in %s" % (rel["tag"], url))
        raise SetupError("git clone failed: %s" % err.strip())
    _, head, _ = git("rev-parse", "HEAD", cwd=dest)
    head = head.strip()
    # content hash from the commit itself (the same bytes as the release's source archive)
    tmpz = os.path.join(os.path.dirname(dest), ".ps2rc-verify-%s.zip" % stamp())
    try:
        git("archive", "--format=zip", "--prefix=PS2RC/", "-o", tmpz, "HEAD", cwd=dest)
        rows, _top, _c = zip_rows(tmpz)
    finally:
        _rm(tmpz)
    return {"method": "git", "commit": head, "rows": rows, "zip_sha256": None, "source": url}


def fetch_zip(lock, rel, dest, downloads, zip_file=None, say=say):
    sz = rel.get("source_zip") or {}
    if zip_file:
        zpath = os.path.abspath(zip_file)
        origin = "local file"
    else:
        os.makedirs(downloads, exist_ok=True)
        zpath = os.path.join(downloads, "PS2RC-%s-source.zip" % rel["tag"])
        say("download %s" % sz["url"])
        http_get(sz["url"], zpath, sz.get("size"), say=say)
        origin = sz["url"]
    rows, top, comment = zip_rows(zpath)
    os.makedirs(dest)
    safe_extract(zpath, dest)
    zsha = sha256_file(zpath)
    commit = comment if re.match(r"^[0-9a-f]{40}$", comment) else None
    return {"method": "zip", "commit": commit, "rows": rows, "zip_sha256": zsha, "zip_path": zpath, "source": origin}


def verify_fetch(rel, got, say=say):
    """Compare a fetched tree with the lock. Returns a list of notes; raises SetupError on a mismatch."""
    notes = []
    th = tree_hash(got["rows"])
    got["tree_sha256"] = th
    if rel["pinned"]:
        if got["commit"] and got["commit"] != rel["commit"]:
            raise SetupError("PS2RC %s points to commit %s, this kit pins %s: refused (a moved tag is a re-release "
                             "or tampering; update the kit or ask the maintainers)" % (rel["tag"], got["commit"],
                                                                                        rel["commit"]))
        if th != rel["tree_sha256"]:
            raise SetupError("PS2RC %s: content hash %s differs from the pinned %s: refused"
                             % (rel["tag"], th, rel["tree_sha256"]))
        if got["commit"] is None:
            notes.append("the archive names no commit; its content matches the pinned commit %s" % rel["commit"])
            got["commit"] = rel["commit"]
        want = (rel.get("source_zip") or {}).get("sha256")
        if got["method"] == "zip" and want and got["zip_sha256"] != want:
            notes.append("the zip's bytes differ from the pinned archive (sha256 %s, pinned %s) but its content "
                         "hash matches the pinned release" % (got["zip_sha256"], want))
        notes.append("verified: commit %s, content hash %s (%d files)" % (got["commit"], th, len(got["rows"])))
    else:
        notes.append("UNPINNED: %s accepted as it is now (commit %s, content hash %s); not checked against a lock"
                     % (rel["tag"], got["commit"], th))
    for n in notes:
        say("  " + n)
    return notes


# ---------------------------------------------------------------- workspace checks

def check_workspace_dir(ws):
    p = os.path.abspath(ws)
    if not p.isascii():
        raise SetupError("%s: use a path with plain ASCII letters only (the PSP toolchain and the build scripts break "
                         "on other characters)" % p)
    if " " in p:
        raise SetupError("%s: use a path without spaces (the build scripts are shell scripts)" % p)
    if os.path.dirname(p) == p:
        raise SetupError("%s: a drive or file-system root is not a workspace; choose a folder" % p)
    home = os.path.abspath(os.path.expanduser("~"))
    if p == home:
        raise SetupError("%s is your home folder: choose a dedicated folder inside it" % p)
    d = p
    while True:                                    # never inside another git work tree (game data could get committed)
        if os.path.exists(os.path.join(d, ".git")):
            raise SetupError("%s is inside the git work tree %s: choose a folder outside every repository (the "
                             "workspace holds files made from your disc, which must never be committed)" % (p, d))
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    if os.path.isdir(p) and os.listdir(p) and not os.path.exists(manifest_path(p)):
        raise SetupError("%s is not empty and not a workspace: choose an empty or new folder" % p)


def default_workspace(kit_dir=None):
    home = os.path.expanduser("~")
    cand = os.path.join(home, "ps2rc-workspace")
    if cand.isascii() and " " not in cand:
        return cand
    if os.name == "nt":
        return os.path.join(os.environ.get("SystemDrive", "C:") + os.sep, "ps2rc-workspace")
    return "/opt/ps2rc-workspace"


def ask(question, default):
    if not sys.stdin or not sys.stdin.isatty():
        raise SetupError("%s\n  no terminal to ask: pass the answer as an option (the agent asks the user first)"
                         % question)
    a = input("%s [%s]: " % (question, default)).strip()
    return a or default


# ---------------------------------------------------------------- links of packs into the checkout

def is_junction(p):
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return bool(getattr(st, "st_reparse_tag", 0) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", -1))


def is_link(p):
    return os.path.islink(p) or is_junction(p)


def remove_link(p):
    """Remove a symlink / junction / copy made by link() - never the target's contents."""
    if is_junction(p):
        os.rmdir(p)
    elif os.path.islink(p):
        os.unlink(p)
    elif os.path.isdir(p) and os.path.exists(os.path.join(p, COPY_STAMP)):
        shutil.rmtree(p)
    elif os.path.exists(p):
        raise SetupError("%s exists and was not made by this script: not touched" % p)


def make_link(target, link, copy=False):
    """-> 'junction' | 'symlink' | 'copy'"""
    if not copy:
        if os.name == "nt":
            try:
                import _winapi
                _winapi.CreateJunction(os.path.abspath(target), os.path.abspath(link))
                return "junction"
            except Exception:
                r = subprocess.run(["cmd", "/c", "mklink", "/J", os.path.abspath(link), os.path.abspath(target)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if r.returncode == 0:
                    return "junction"
        else:
            try:
                os.symlink(os.path.abspath(target), link, target_is_directory=True)
                return "symlink"
            except OSError:
                pass
    shutil.copytree(target, link, ignore=shutil.ignore_patterns(".git", *GENERATED))
    with open(os.path.join(link, COPY_STAMP), "w", encoding="utf-8", newline="\n") as f:
        f.write("A copy of the pack in the workspace's packs/ folder. Edit that one, then run setup_ps2rc.py link.\n")
    return "copy"


def git_exclude(checkout, lines):
    ex = os.path.join(checkout, ".git", "info", "exclude")
    if not os.path.isdir(os.path.dirname(ex)):
        return
    have = open(ex, encoding="utf-8").read().splitlines() if os.path.exists(ex) else []
    add = [x for x in lines if x not in have]
    if add:
        with open(ex, "a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(add) + "\n")


def write_local_toml(ws, m):
    src = os.path.join(ws, "local.toml")
    if not os.path.exists(src):
        work = fwd(os.path.join(ws, m["paths"]["work"]))
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write("# PS2RC per-machine settings of this workspace (PS2RC reads [paths], [games.\"<pack>\"], [tools]).\n"
                    "# Edit this file, then run setup_ps2rc.py link (it copies it into PS2RC/local.toml).\n"
                    "# Everything below work/ is made from your disc: it never leaves this PC.\n\n"
                    "[paths]\nwork = \"%s\"\nanalysis = \"%s/analysis\"\n\n"
                    "# [games.\"SLUS-12345_v1.00\"]\n# disc = \"<the extracted disc folder of your own copy>\"\n"
                    % (work, work))
    dst = os.path.join(ws, CHECKOUT, "local.toml")
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            cur = f.read()
        if not cur.startswith(LOCAL_HEADER):
            keep = dst + ".user-" + stamp()
            os.replace(dst, keep)
            say("  kept your own PS2RC/local.toml as %s" % os.path.basename(keep))
    with open(src, encoding="utf-8") as f:
        body = f.read()
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(LOCAL_HEADER + "\n" + body)


def write_env(ws, m):
    local = os.path.join(ws, "local.toml")
    tc = m.get("converter", {}) and m["converter"].get("toolchain")
    tc = os.path.join(ws, tc) if tc else None
    with open(os.path.join(ws, "env.sh"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# source this file: . env.sh\nexport UPR_WORKSPACE='%s'\nexport PS2RC_LOCAL='%s'\n"
                % (fwd(ws), fwd(local)))
        if tc:
            f.write("export PS2RC_TOOLCHAIN='%s'\n" % fwd(tc))
    with open(os.path.join(ws, "env.ps1"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("# dot-source this file: . .\\env.ps1\n$env:UPR_WORKSPACE = '%s'\n$env:PS2RC_LOCAL = '%s'\n"
                % (os.path.abspath(ws), os.path.abspath(local)))
        if tc:
            f.write("$env:PS2RC_TOOLCHAIN = '%s'\n" % os.path.abspath(tc))
    with open(os.path.join(ws, "env.cmd"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("@rem call env.cmd\nset \"UPR_WORKSPACE=%s\"\nset \"PS2RC_LOCAL=%s\"\n"
                % (os.path.abspath(ws), os.path.abspath(local)))
        if tc:
            f.write("set \"PS2RC_TOOLCHAIN=%s\"\n" % os.path.abspath(tc))


def link_all(ws, m, copy=False, say=say):
    checkout = os.path.join(ws, CHECKOUT)
    games = os.path.join(checkout, "games")
    excl = []
    for p in m["packs"]:
        target = os.path.join(ws, p["dir"])
        link = os.path.join(games, p["name"])
        if not os.path.isdir(target):
            say("  pack %s: %s is missing (moved or deleted?) - not linked" % (p["name"], p["dir"]))
            continue
        if os.path.lexists(link):
            if is_link(link) or os.path.exists(os.path.join(link, COPY_STAMP)):
                remove_link(link)
            else:
                raise SetupError("PS2RC/games/%s already exists and is part of PS2RC: rename your pack" % p["name"])
        p["link"] = make_link(target, link, copy=copy)
        excl.append("/games/%s" % p["name"])
        say("  pack %s -> PS2RC/games/%s (%s)" % (p["name"], p["name"], p["link"]))
        if p["link"] == "copy":
            say("    a copy (links are not possible here): edit packs/%s, then run link again" % p["name"])
    git_exclude(checkout, excl + ["/local.toml.user-*"])
    write_local_toml(ws, m)
    write_env(ws, m)


def unlink_all(ws, m):
    for p in m["packs"]:
        link = os.path.join(ws, CHECKOUT, "games", p["name"])
        if os.path.lexists(link):
            remove_link(link)


# ---------------------------------------------------------------- integrity of an installed checkout

def checkout_changes(ws, m):
    """Files of the PS2RC checkout that differ from the release (the user's edits), as a list of strings."""
    checkout = os.path.join(ws, CHECKOUT)
    linked = set("games/%s" % p["name"] for p in m["packs"])
    if m["ps2rc"]["method"] == "git" and os.path.isdir(os.path.join(checkout, ".git")) and have_git():
        _, head, _ = git("rev-parse", "HEAD", cwd=checkout)
        out = []
        if head.strip() != m["ps2rc"]["commit"]:
            out.append("HEAD is %s, not the installed %s" % (head.strip()[:12], m["ps2rc"]["commit"][:12]))
        _, st, _ = git("status", "--porcelain", "--untracked-files=no", cwd=checkout)
        out += [ln.strip() for ln in st.splitlines() if ln.strip()]
        return out
    listp = os.path.join(ws, FILELIST)
    if not os.path.exists(listp):
        return ["no file list to compare with (%s missing)" % FILELIST]
    out = []
    with open(listp, encoding="utf-8") as f:
        for line in f:
            h, _, rel = line.rstrip("\n").partition("  ")
            if any(rel == x or rel.startswith(x + "/") for x in linked):
                continue
            p = os.path.join(checkout, *rel.split("/"))
            if not os.path.exists(p):
                out.append("D " + rel)
            elif sha256_file(p) != h:
                out.append("M " + rel)
    return out


def reserved_serials(lock, checkout=None):
    out = set(r["serial"] for r in lock.get("reserved", []))
    games = os.path.join(checkout, "games") if checkout else None
    if games and os.path.isdir(games):
        for name in os.listdir(games):
            rp = os.path.join(games, name, "RESERVED.md")
            if os.path.isfile(rp):
                with open(rp, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.lstrip().startswith("|"):
                            out.update(re.findall(r"\b[A-Z]{4}-\d{5}\b", line))
    return out


def reserved_pack_dirs(checkout):
    games = os.path.join(checkout, "games")
    out = []
    for name in sorted(os.listdir(games)) if os.path.isdir(games) else []:
        if os.path.isfile(os.path.join(games, name, "RESERVED.md")) and not is_link(os.path.join(games, name)):
            out.append(os.path.join(games, name))
    return out


# ---------------------------------------------------------------- commands

def install_release(ws, lock, rel, a, dest, say=say):
    """Fetch + verify one release into dest (must not exist). -> (info dict, notes)."""
    method = a.method
    if method == "auto":
        method = "zip" if a.zip else ("git" if have_git() else "zip")
    if method == "git" and not have_git():
        raise SetupError("--method git: git is not installed (use --method zip)")
    if method == "git":
        got = fetch_git(lock, rel, dest, a.source, say=say)
    else:
        got = fetch_zip(lock, rel, dest, os.path.join(ws, "downloads"), a.zip, say=say)
    try:
        notes = verify_fetch(rel, got, say=say)
    except SetupError:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return got, notes


def write_filelist(ws, rows):
    with open(os.path.join(ws, FILELIST), "w", encoding="utf-8", newline="\n") as f:
        for p, h in sorted(rows):
            f.write("%s  %s\n" % (h, p))


def get_converter(ws, lock, rel, a, say=say):
    asset = (rel.get("assets") or {}).get("converter-win64")
    if not asset:
        raise SetupError("PS2RC %s has no pinned prebuilt converter in this kit" % rel["tag"])
    if os.name != "nt" and not a.any_platform:
        raise SetupError("the prebuilt converter (with its PSP toolchain) is for Windows; on Linux/WSL install pspdev "
                         "(see PS2RC/README.md) or pass --any-platform to download it anyway")
    dl = os.path.join(ws, "downloads")
    os.makedirs(dl, exist_ok=True)
    zpath = os.path.abspath(a.converter_zip) if a.converter_zip else os.path.join(dl, asset["name"])
    if not a.converter_zip and not (os.path.exists(zpath) and sha256_file(zpath) == asset["sha256"]):
        say("download %s (%.0f MB)" % (asset["url"], asset["size"] / 1e6))
        http_get(asset["url"], zpath, asset["size"], say=say)
    h = sha256_file(zpath)
    if h != asset["sha256"]:
        raise SetupError("%s: sha256 %s differs from the pinned %s: refused" % (zpath, h, asset["sha256"]))
    say("  verified %s sha256 %s" % (asset["name"], h))
    dest = os.path.join(ws, "converter")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    safe_extract(zpath, dest, strip_top=False)
    tc = asset.get("toolchain")
    if tc and not os.path.isdir(os.path.join(dest, *tc.split("/"))):
        tc = None
    return {"tag": rel["tag"], "asset": asset["name"], "sha256": h, "dir": "converter",
            "toolchain": ("converter/" + asset["toolchain"]) if tc else None, "installed_utc": now()}


def cmd_setup(a, lock):
    ws = a.workspace
    if not ws:
        if a.yes or a.dry_run:
            ws = default_workspace()
        else:
            ws = ask("Where should the PS2RC workspace go?", default_workspace())
    ws = os.path.abspath(os.path.expanduser(ws))
    existing = load_manifest(ws, required=False)
    if existing and os.path.isdir(os.path.join(ws, CHECKOUT)):
        raise SetupError("%s already has PS2RC %s: use `status`, or `update --tag <tag>`"
                         % (ws, existing["ps2rc"]["tag"]))
    check_workspace_dir(ws)
    tag = a.tag or lock["default"]
    rel = release(lock, tag, a.allow_unpinned)
    method = a.method if a.method != "auto" else ("zip" if a.zip else ("git" if have_git() else "zip"))
    conv = (rel.get("assets") or {}).get("converter-win64")
    if a.dry_run:
        say("plan (nothing is written or downloaded):")
        say("  workspace   %s" % ws)
        say("  PS2RC       %s (%s), commit %s, via %s from %s" % (tag, "pinned" if rel["pinned"] else "UNPINNED",
                                                                rel.get("commit"), method,
                                                                a.zip or a.source or lock["url"]))
        if method == "zip" and not a.zip:
            say("  download    %s (%.1f MB)" % (rel["source_zip"]["url"], (rel["source_zip"].get("size") or 0) / 1e6))
        if a.with_converter and conv:
            say("  converter   %s (%.0f MB, sha256 %s...)" % (conv["name"], conv["size"] / 1e6, conv["sha256"][:16]))
        say("  folders     PS2RC/ packs/ work/ refdocs/ downloads/%s" % (" converter/" if a.with_converter else ""))
        return 0
    os.makedirs(ws, exist_ok=True)
    m = existing or {"format": 1, "created_utc": now(), "kit": {"name": "universal-ps2-recompiler"},
                     "paths": {"checkout": CHECKOUT, "packs": "packs", "work": "work", "refdocs": "refdocs",
                               "downloads": "downloads"},
                     "ps2rc": None, "converter": None, "packs": [], "history": []}
    for d in ("packs", "work", "refdocs", "downloads"):
        os.makedirs(os.path.join(ws, d), exist_ok=True)
    say("PS2RC %s -> %s" % (tag, os.path.join(ws, CHECKOUT)))
    tmp = os.path.join(ws, ".PS2RC.new")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    got, notes = install_release(ws, lock, rel, a, tmp)
    os.replace(tmp, os.path.join(ws, CHECKOUT))
    write_filelist(ws, got["rows"])
    m["ps2rc"] = ps2rc_record(rel, got)
    m["history"].append({"utc": now(), "action": "setup", "tag": tag, "commit": got["commit"]})
    if a.with_converter:
        m["converter"] = get_converter(ws, lock, rel, a)
        m["history"].append({"utc": now(), "action": "converter", "tag": tag})
    save_manifest(ws, m)
    link_all(ws, m)
    save_manifest(ws, m)
    write_readme(ws)
    say("workspace ready: %s" % ws)
    say("  next: cd %s && python -m ps2rc doctor" % os.path.join(ws, CHECKOUT))
    say("  new pack: python %s new-pack <SERIAL> <VERSION> --workspace %s" % (os.path.abspath(__file__), ws))
    if sys.version_info < (3, 11):
        say("  note: PS2RC itself needs Python 3.11 or newer (this is %d.%d)" % sys.version_info[:2])
    return 0


def ps2rc_record(rel, got):
    return {"tag": rel["tag"], "commit": got["commit"], "pinned": rel["pinned"], "method": got["method"],
            "source": got["source"], "tree_sha256": got["tree_sha256"], "files": len(got["rows"]),
            "zip_sha256": got.get("zip_sha256"), "installed_utc": now()}


def write_readme(ws):
    p = os.path.join(ws, "WORKSPACE.txt")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("PS2RC workspace (made by universal-ps2-recompiler's setup_ps2rc.py)\n\n"
                "PS2RC/      the engine at a pinned release - do not port inside it; `setup_ps2rc.py update` replaces it\n"
                "packs/      your game packs (linked into PS2RC/games/) - your own work\n"
                "work/       files made from your disc - never share, upload or commit anything from here\n"
                "refdocs/    public reference documents\n"
                "downloads/  release archives\n"
                "local.toml  PS2RC settings (edit here, then `setup_ps2rc.py link`)\n"
                "ps2rc-workspace.json  what is installed and how it was verified\n")


def cmd_status(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    checkout = os.path.join(ws, CHECKOUT)
    r = m["ps2rc"] or {}
    info = {"workspace": ws, "checkout": checkout, "ps2rc": r, "converter": m.get("converter"),
            "packs": [], "local_toml": None, "latest_pinned": lock["default"]}
    for p in m["packs"]:
        link = os.path.join(checkout, "games", p["name"])
        ok = os.path.isfile(os.path.join(link, "pack.toml"))
        info["packs"].append(dict(p, linked=ok))
    lt = os.path.join(checkout, "local.toml")
    if os.path.exists(lt) and os.path.exists(os.path.join(ws, "local.toml")):
        with open(lt, encoding="utf-8") as f1, open(os.path.join(ws, "local.toml"), encoding="utf-8") as f2:
            info["local_toml"] = "in sync" if f1.read() == LOCAL_HEADER + "\n" + f2.read() else "differs: run link"
    if a.json:
        print(json.dumps(info, indent=2))
        return 0
    say("workspace  %s" % ws)
    say("PS2RC      %s, commit %s, %s, via %s, installed %s" % (r.get("tag"), (r.get("commit") or "?")[:12],
                                                            "pinned" if r.get("pinned") else "UNPINNED",
                                                            r.get("method"), r.get("installed_utc")))
    if lock["default"] != r.get("tag"):
        say("           the kit pins %s: `update` installs it" % lock["default"])
    c = m.get("converter")
    say("converter  %s" % ("%s (toolchain %s)" % (c["asset"], c.get("toolchain")) if c else "not installed"))
    for p in info["packs"]:
        say("pack       %s  packs/%s  %s%s" % (p["name"], p["name"], p.get("link"), "" if p["linked"] else
                                              "  NOT LINKED: run link"))
    if not info["packs"]:
        say("pack       none yet (new-pack SERIAL VERSION)")
    say("local.toml %s" % info["local_toml"])
    return 0


def cmd_verify(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    ch = checkout_changes(ws, m)
    bad = 0
    if ch:
        say("PS2RC checkout differs from %s:" % m["ps2rc"]["tag"])
        for c in ch[:50]:
            say("  " + c)
        bad = 1
    else:
        say("PS2RC checkout matches %s (commit %s)" % (m["ps2rc"]["tag"], m["ps2rc"]["commit"]))
    c = m.get("converter")
    if c:
        rel = lock["releases"].get(c["tag"], {})
        want = ((rel.get("assets") or {}).get("converter-win64") or {}).get("sha256", c["sha256"])
        zp = os.path.join(ws, "downloads", c["asset"])
        if os.path.exists(zp):
            ok = sha256_file(zp) == want
            say("converter archive %s: %s" % (c["asset"], "OK" if ok else "CHANGED"))
            bad |= not ok
    return bad


def cmd_update(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    old = m["ps2rc"]
    tag = a.tag or lock["default"]
    rel = release(lock, tag, a.allow_unpinned)
    if old and old["tag"] == tag and old["commit"] == rel.get("commit") and not a.reinstall:
        say("PS2RC %s is already installed (use --reinstall to fetch it again)" % tag)
        return 0
    ch = checkout_changes(ws, m) if old else []
    if ch and not a.accept_backup:
        say("Your PS2RC checkout has changes against %s:" % old["tag"])
        for c in ch[:30]:
            say("  " + c)
        raise SetupError("update refused: the new checkout would not carry these changes. Send engine fixes as pull "
                         "requests to PS2RC, or pass --accept-backup (the old checkout is kept as a backup folder)")
    if a.dry_run:
        say("plan: PS2RC %s -> %s in %s; packs kept: %s; nothing written" %
            (old and old["tag"], tag, ws, ", ".join(p["name"] for p in m["packs"]) or "none"))
        return 0
    tmp = os.path.join(ws, ".PS2RC.new")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    say("PS2RC %s -> %s" % (old and old["tag"], tag))
    got, notes = install_release(ws, lock, rel, a, tmp)
    checkout = os.path.join(ws, CHECKOUT)
    backup = None
    unlink_all(ws, m)                                  # the packs' links go first: the old tree is moved aside whole
    for d in m["packs"]:
        if not os.path.isdir(os.path.join(ws, d["dir"])):
            raise SetupError("pack folder %s is missing; nothing was changed" % d["dir"])
    if os.path.isdir(checkout):
        backup = os.path.join(ws, "%s.backup-%s-%s" % (CHECKOUT, old["tag"] if old else "old", stamp()))
        os.replace(checkout, backup)
    try:
        os.replace(tmp, checkout)
    except OSError:
        if backup:
            os.replace(backup, checkout)
        link_all(ws, m)
        raise
    write_filelist(ws, got["rows"])
    m["ps2rc"] = ps2rc_record(rel, got)
    m["history"].append({"utc": now(), "action": "update", "from": old and old["tag"], "tag": tag,
                         "commit": got["commit"], "backup": os.path.basename(backup) if backup else None})
    if a.with_converter:
        m["converter"] = get_converter(ws, lock, rel, a)
    save_manifest(ws, m)
    link_all(ws, m)
    save_manifest(ws, m)
    pf = rel.get("pack_format")
    for p in m["packs"]:
        f = pack_format(os.path.join(ws, p["dir"]))
        if pf and f and f != pf:
            say("  pack %s has format %s, PS2RC %s reads format %s: see PS2RC/docs/GAME_PACK_FORMAT.md"
                % (p["name"], f, tag, pf))
    say("updated to PS2RC %s; your packs were not touched%s" %
        (tag, "; the old checkout is in %s (delete it when you no longer need it)" % os.path.basename(backup)
         if backup else ""))
    return 0


def pack_format(d):
    p = os.path.join(d, "pack.toml")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as f:
        mm = re.search(r"^format\s*=\s*(\d+)", f.read(), re.M)
    return int(mm.group(1)) if mm else None


def boot_elf_of(serial):
    a, b = serial.split("-")
    return "%s_%s.%s" % (a, b[:3], b[3:])


def cmd_new_pack(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    checkout = os.path.join(ws, CHECKOUT)
    serial, version = a.serial.upper(), a.version
    if not SERIAL_RX.match(serial):
        raise SetupError("serial %r: expected four letters, a hyphen and five digits (as SYSTEM.CNF names the boot "
                         "program, e.g. SLUS-12345)" % a.serial)
    if not VERSION_RX.match(version):
        raise SetupError("version %r: expected the SYSTEM.CNF VER value, e.g. 1.00" % version)
    if a.region and a.region not in REGIONS:
        raise SetupError("region %r: one of %s" % (a.region, ", ".join(REGIONS)))
    if serial in reserved_serials(lock, checkout):
        raise SetupError("%s is a Reserved Game under the PS2RC License (section 2(e), its RESERVED.md): only "
                         "SandstoneDev ports it. Use PS2RC's own pack and converter for your copy; do not make, "
                         "modify or publish a pack for it." % serial, 3)
    name = "%s_v%s" % (serial, version)
    if any(p["name"] == name for p in m["packs"]):
        raise SetupError("pack %s already exists in packs/" % name)
    if os.path.exists(os.path.join(checkout, "games", name)):
        raise SetupError("PS2RC already ships a pack named %s (games/%s): use it" % (name, name))
    tpl = os.path.join(checkout, "games", "_template")
    if not os.path.isfile(os.path.join(tpl, "pack.toml")):
        raise SetupError("PS2RC/games/_template is missing: run verify / update")
    dest = os.path.join(ws, "packs", name)
    if os.path.exists(dest):
        raise SetupError("%s exists already" % dest)
    shutil.copytree(tpl, dest, ignore=shutil.ignore_patterns(*GENERATED))
    os.replace(os.path.join(dest, "README.md"), os.path.join(dest, "TEMPLATE_GUIDE.md"))
    pt = os.path.join(dest, "pack.toml")
    with open(pt, encoding="utf-8") as f:
        t = f.read()
    boot = boot_elf_of(serial)
    reps = [(r'^serial = "[^"]*"', 'serial = "%s"' % serial), (r'^version = "[^"]*"', 'version = "%s"' % version),
            (r'^boot_elf = "[^"]*"', 'boot_elf = "%s"' % boot),
            (r"^system_cnf_boot2 = '[^']*'", "system_cnf_boot2 = 'cdrom0:\\%s;1'" % boot),
            (r'^psp_title = "[^"]*"', 'psp_title = "PS2RC %s"' % serial)]
    if a.region:
        reps.append((r'^region = "[^"]*"', 'region = "%s"' % a.region))
    for rx, new in reps:
        t, n = re.subn(rx, new.replace("\\", "\\\\"), t, count=1, flags=re.M)
        if n != 1:
            say("  note: %s not found in the template's pack.toml (fill it by hand)" % rx)
    with open(pt, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)
    with open(os.path.join(dest, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PACK_README % {"name": name, "tag": m["ps2rc"]["tag"]})
    with open(os.path.join(dest, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PACK_GITIGNORE)
    with open(os.path.join(dest, "pack-origin.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"made_from": "PS2RC games/_template", "ps2rc_tag": m["ps2rc"]["tag"],
                   "ps2rc_commit": m["ps2rc"]["commit"], "made_utc": now()}, f, indent=2)
        f.write("\n")
    m["packs"].append({"name": name, "dir": "packs/%s" % name, "serial": serial, "version": version,
                       "link": None, "created_utc": now(), "from_tag": m["ps2rc"]["tag"]})
    m["history"].append({"utc": now(), "action": "new-pack", "pack": name})
    link_all(ws, m)
    save_manifest(ws, m)
    if a.git and have_git():
        git("init", "--quiet", cwd=dest)
        say("  packs/%s is a git repository (local; nothing is pushed)" % name)
    say("new pack packs/%s (from PS2RC %s games/_template); PS2RC sees it as games/%s"
        % (name, m["ps2rc"]["tag"], name))
    say("  next: fill [verify] and [memory] from your disc (skills/ps2-recon), set [games.\"%s\"] disc in "
        "local.toml, then link" % name)
    return 0


PACK_README = """# %(name)s - a PS2RC game pack

A game pack for one version of one PS2 game, made from PS2RC's `games/_template` (PS2RC %(tag)s). How to fill it:
`TEMPLATE_GUIDE.md`, PS2RC's `docs/GAME_PACK_FORMAT.md` and `games/example/`.

This pack contains no game data and never may: no files from the disc, no code or tables copied or translated from
the game, no generated C, no builds. Everything made from the disc lives in the workspace's `work/` folder.

If you ever publish this pack (only after your own legal check), keep it free of charge and carry this credit:

    Based on PS2RC by SandstoneDev
    https://github.com/SandstoneDev/PS2RC
    Community: https://discord.gg/wV8x46ZTDu

The parts that come from PS2RC stay under the PS2RC License 1.0 (keep PS2RC's LICENSE and NOTICE.md with them).
"""

PACK_GITIGNORE = """# never in a pack: anything from the disc or made from it
*.iso
*.ISO
*.cso
*.elf
*.ELF
*.irx
*.IRX
*.pss
*.PSS
*.PBP
*.prx
*.o
*.a
*.log
work/
disc/
build/
__pycache__/
"""


TEXT_EXT = (".c", ".h", ".S", ".s", ".py", ".toml", ".def", ".txt", ".tsv", ".md", ".ld", ".json", ".sh", ".inc")
SUSPECT_EXT = (".iso", ".cso", ".elf", ".irx", ".pss", ".pbp", ".prx", ".bin", ".img", ".at3", ".vag", ".pmf", ".o",
               ".a")


def _norm_lines(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        out = []
        for ln in f:
            s = " ".join(ln.split())
            if len(s) >= 8 and not re.match(r"^(#|//|/\*|\*|--)", s):
                out.append(s)
        return out


def _windows(lines, n):
    return set(hashlib.sha1("\n".join(lines[i:i + n]).encode()).hexdigest() for i in range(len(lines) - n + 1))


def check_pack(pack_dir, checkout, lock, window=6):
    """Findings for a user's pack: reserved serial, files or runs of lines shared with a reserved pack, disc-like
    files. [] = clean."""
    finds = []
    serials = reserved_serials(lock, checkout)
    common = set()
    for d in ("_template", "example"):
        base = os.path.join(checkout, "games", d)
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                if fn.endswith(TEXT_EXT):
                    common |= _windows(_norm_lines(os.path.join(dp, fn)), window)
    res_files, res_windows = {}, {}
    for rd in reserved_pack_dirs(checkout):
        for dp, _dn, fns in os.walk(rd):
            for fn in fns:
                p = os.path.join(dp, fn)
                res_files[sha256_file(p)] = os.path.relpath(p, checkout).replace(os.sep, "/")
                if fn.endswith(TEXT_EXT):
                    for w in _windows(_norm_lines(p), window) - common:
                        res_windows.setdefault(w, os.path.relpath(p, checkout).replace(os.sep, "/"))
    for dp, dns, fns in os.walk(pack_dir):
        dns[:] = [d for d in dns if d not in (".git",) + GENERATED]
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, pack_dir).replace(os.sep, "/")
            low = fn.lower()
            if low.endswith(SUSPECT_EXT) or low == "system.cnf":
                finds.append("%s: a disc or build file type - never in a pack" % rel)
            if os.path.getsize(p) > 512 * 1024:
                finds.append("%s: larger than 512 KB - a pack holds descriptions, not data" % rel)
            h = sha256_file(p)
            if h in res_files:
                finds.append("%s: identical to the reserved pack's %s - never copy it" % (rel, res_files[h]))
                continue
            if fn.endswith(TEXT_EXT):
                lines = _norm_lines(p)
                hits = set()
                for i in range(len(lines) - window + 1):
                    w = hashlib.sha1("\n".join(lines[i:i + window]).encode()).hexdigest()
                    if w in res_windows:
                        hits.add(res_windows[w])
                if hits:
                    finds.append("%s: %d+ lines in a row shared with %s - write your own (reading the reserved pack "
                                 "as an example of structure is fine, copying it is not)" % (rel, window,
                                                                                            ", ".join(sorted(hits))))
                with open(p, encoding="utf-8", errors="replace") as f:
                    txt = f.read()
                for s in serials:
                    if s in txt:
                        finds.append("%s: names the reserved serial %s" % (rel, s))
    return finds


def cmd_check_pack(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    p = next((x for x in m["packs"] if x["name"] == a.name), None)
    d = os.path.join(ws, p["dir"]) if p else (a.name if os.path.isdir(a.name) else None)
    if not d:
        raise SetupError("no pack %s in this workspace" % a.name)
    finds = check_pack(d, os.path.join(ws, CHECKOUT), lock)
    for f in finds:
        say("FAIL " + f)
    say("%s: %d findings" % (a.name, len(finds)))
    return 1 if finds else 0


def cmd_link(a, lock):
    ws = find_workspace(a.workspace)
    m = load_manifest(ws)
    link_all(ws, m, copy=a.copy)
    save_manifest(ws, m)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="setup_ps2rc.py", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lock", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("--workspace", help="the workspace folder (default: UPR_WORKSPACE or a parent with a manifest)")

    def source(p):
        p.add_argument("--tag", help="PS2RC release tag (default: the kit's pinned default)")
        p.add_argument("--method", choices=("auto", "git", "zip"), default="auto",
                       help="git clone --depth 1 (when git is installed) or the release's source zip")
        p.add_argument("--source", help="git URL or local clone to clone from instead of GitHub")
        p.add_argument("--zip", help="use this source zip instead of downloading it (offline)")
        p.add_argument("--allow-unpinned", action="store_true", help="accept a tag this kit does not pin")
        p.add_argument("--with-converter", action="store_true",
                       help="also download the prebuilt converter with its PSP toolchain (Windows, about 104 MB)")
        p.add_argument("--converter-zip", help="use this converter zip instead of downloading it")
        p.add_argument("--any-platform", action="store_true", help=argparse.SUPPRESS)
        p.add_argument("--dry-run", action="store_true", help="print the plan, write and download nothing")

    s = sub.add_parser("setup", help="create a workspace and download PS2RC")
    common(s)
    source(s)
    s.add_argument("--yes", action="store_true", help="accept the default workspace folder without asking")
    st = sub.add_parser("status", help="what is installed")
    common(st)
    st.add_argument("--json", action="store_true")
    v = sub.add_parser("verify", help="check the checkout against the installed release")
    common(v)
    u = sub.add_parser("update", help="replace the checkout with another pinned release; packs are kept")
    common(u)
    source(u)
    u.add_argument("--accept-backup", action="store_true", help="update although the checkout has changes")
    u.add_argument("--reinstall", action="store_true")
    n = sub.add_parser("new-pack", help="a new game pack in packs/ from PS2RC's games/_template")
    common(n)
    n.add_argument("serial")
    n.add_argument("version")
    n.add_argument("--region", help="one of: " + ", ".join(REGIONS))
    n.add_argument("--git", action="store_true", help="make the pack a local git repository")
    lk = sub.add_parser("link", help="(re)link packs into PS2RC/games and copy local.toml")
    common(lk)
    lk.add_argument("--copy", action="store_true", help="copy packs instead of linking them")
    sub.add_parser("doctor", help="what this machine has and lacks, and where to get it (doctor.py)")
    c = sub.add_parser("check-pack", help="check a pack: reserved game, copied code, disc files")
    common(c)
    c.add_argument("name")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["doctor"]:
        sys.path.insert(0, HERE)
        import doctor
        return doctor.main(argv[1:])
    ap = build_parser()
    a = ap.parse_args(argv)
    if not a.cmd:
        a = ap.parse_args(["setup"] + argv)
    try:
        lock = load_lock(a.lock)
        fn = {"setup": cmd_setup, "status": cmd_status, "verify": cmd_verify, "update": cmd_update,
              "new-pack": cmd_new_pack, "link": cmd_link, "check-pack": cmd_check_pack}[a.cmd]
        return fn(a, lock)
    except SetupError as e:
        print("setup_ps2rc: %s" % e, file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        print("setup_ps2rc: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
