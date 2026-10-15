"""fetch_docs.py - fetch PUBLIC PS2 / PSP reference material onto the user's machine and index it.

Part of the fetch-docs skill (skills/fetch-docs/SKILL.md). Python 3.11+, standard library and git only.

    python skills/fetch-docs/fetch_docs.py list [--group G] [--json]
    python skills/fetch-docs/fetch_docs.py check [ID ...]              reachability of the catalogue (no download)
    python skills/fetch-docs/fetch_docs.py plan --dest DIR [ID ... | --set NAME]
    python skills/fetch-docs/fetch_docs.py fetch --dest DIR [ID ... | --set NAME] [--full-history]
    python skills/fetch-docs/fetch_docs.py file --dest DIR --url URL --name NAME --licence TEXT
    python skills/fetch-docs/fetch_docs.py wayback URL                 closest archived copy of a dead page
    python skills/fetch-docs/fetch_docs.py verify --dest DIR           re-hash everything in the index
    python skills/fetch-docs/fetch_docs.py index --dest DIR            rewrite DOCS_INDEX.md from docs_index.json

Rules built in: only public sources (the catalogue below, or one page the user names), robots.txt is honoured for
single files, one request at a time with a pause, nothing behind a login, sites that refuse automated clients are
never requested (kind "online", DENY_HOSTS), nothing is fetched without --dest (the user chooses the folder). Every fetched item is recorded in DIR/docs_index.json and DIR/DOCS_INDEX.md with its URL, the
date, the licence or terms as published, the commit (repositories) and SHA-256 hashes.

This tool never fetches console SDKs, firmware, BIOS files, keys or game images, and it has no entry for any of them.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = "ps2rc-fetch-docs/1 (+https://github.com/SandstoneDev/universal-ps2-recompiler)"
PAUSE_S = 2.0
INDEX_JSON = "docs_index.json"
INDEX_MD = "DOCS_INDEX.md"

# kind: git    = shallow clone of a public repository (git required);
#       file   = one public page or PDF saved as is (robots.txt honoured);
#       online = read in a browser by the user, never fetched by this tool (the site refuses automated clients,
#                or it is an archive or directory to browse, not one document).
# size_mb: rough size (GitHub's figure for a repository, the file size for a file); `plan` shows it before anything
#          is fetched. checked: the date this entry was last confirmed reachable, and the result.
# verify: how to know you have the right version.
CATALOGUE = [
    # ---- PS2 ---------------------------------------------------------------------------------------------------
    dict(id="ps2sdk", group="ps2", kind="git", url="https://github.com/ps2dev/ps2sdk",
         good_for="open PS2 SDK: EE kernel and syscalls, IOP module sources (iop/), SIF RPC, libraries - the "
                  "names and behaviour HLE must match", licence="AFL-2.0 (LICENSE in the repository)", size_mb=31,
         set=("recommended", "ps2"), checked="2026-10-14 OK",
         verify="changes almost daily: record the commit; v2.0.0 is the last tag"),
    dict(id="ps2sdk-docs", group="ps2", kind="file", url="https://ps2dev.github.io/ps2sdk/",
         good_for="generated API reference of ps2sdk (front page saved; read the rest online)",
         licence="as ps2sdk (AFL-2.0)", size_mb=0.1, set=("ps2",), checked="2026-10-14 OK",
         verify="build date on the page; it follows ps2sdk master"),
    dict(id="ps2toolchain", group="ps2", kind="git", url="https://github.com/ps2dev/ps2toolchain",
         good_for="how the open EE / IOP toolchain is built (its objdump decodes R5900 code for golden tests)",
         licence="BSD-2-Clause", size_mb=1, set=("ps2",), checked="2026-10-14 OK", verify="tag v2.0.0 or commit"),
    dict(id="ps2tek", group="ps2", kind="file", url="https://psi-rockin.github.io/ps2tek/",
         good_for="PS2 hardware notes: EE, DMAC, GIF, GS, VIF, VU, IPU, INTC registers, IOP and SPU2 maps",
         licence="none stated: personal reference, rewrite in your own words, never copy text",
         size_mb=1, set=("recommended", "ps2"), checked="2026-10-14 OK",
         verify="no version: record the date (source history: github.com/PSI-Rockin/ps2tek)"),
    dict(id="pcsx2", group="ps2", kind="git", url="https://github.com/PCSX2/pcsx2",
         good_for="the reference PS2 emulator: how EE, FPU, VU, VIF, GIF, GS, IOP and SPU2 behave as implemented; "
                  "explains reference-run results", licence="GPL-3.0: read to understand, never copy code",
         size_mb=332, set=("ps2", "big"), checked="2026-10-14 OK",
         verify="the tag of the PCSX2 build you run reference runs with (stable v2.8.2 when checked)"),
    dict(id="play", group="ps2", kind="git", url="https://github.com/jpd002/Play-",
         good_for="second PS2 emulator: EE / VU recompiler and IOP high-level emulation, another reading of the "
                  "same hardware", licence="BSD-2-Clause", size_mb=23, set=("ps2", "big"),
         checked="2026-10-14 OK", verify="tag (0.77 when checked) or commit"),
    dict(id="dobiestation", group="ps2", kind="git", url="https://github.com/PSI-Rockin/DobieStation",
         good_for="compact PS2 emulator (EE, VU, GS, IOP), easier to read than the large ones",
         licence="GPL-3.0: read only", size_mb=4, set=("ps2",), checked="2026-10-14 OK",
         verify="commit (dormant since 2021)"),
    dict(id="psx-spx", group="ps2", kind="file", url="https://problemkaputt.de/psx-spx.htm",
         good_for="PS1 hardware: the R3000A CPU and the SPU, the ancestors of the PS2's IOP and SPU2",
         licence="none stated: personal reference", size_mb=3, set=("ps2",), checked="2026-10-14 OK",
         verify="record the date"),
    dict(id="ps2dev-forums", group="ps2", kind="online",
         url="https://web.archive.org/web/2010/http://forums.ps2dev.org/",
         good_for="archived ps2dev / pspdev forum threads (hardware experiments, clocks, kernel behaviour); open "
                  "single threads through the Wayback Machine", licence="archive.org terms; posts belong to "
                  "their authors", size_mb=0, set=("ps2",), checked="2026-10-14 OK (through the Wayback Machine)",
         verify="the snapshot timestamp in the archived URL"),
    dict(id="psdevwiki", group="ps2", kind="online", url="https://www.psdevwiki.com/",
         good_for="community wiki of PS2 and PSP models, file formats, SYSTEM.CNF, PARAM.SFO - the USER reads it "
                  "in a browser", licence="the site reserves its content against automated and AI use "
                  "(robots.txt): never fetch, never copy; skip its pages on keys and firmware", size_mb=0,
         set=("ps2", "psp"), checked="2026-10-14 refuses automated clients",
         verify="page history of the page read"),
    # ---- PSP ---------------------------------------------------------------------------------------------------
    dict(id="pspsdk", group="psp", kind="git", url="https://github.com/pspdev/pspsdk",
         good_for="the open PSPSDK: headers, libraries and samples (sceGu, sceKernel, sceIo, audio) the PSP build "
                  "uses", licence="BSD-style (LICENSE in the repository)", size_mb=15, set=("recommended", "psp"),
         checked="2026-10-14 OK", verify="no tags: the commit your toolchain was built from"),
    dict(id="pspdev", group="psp", kind="git", url="https://github.com/pspdev/pspdev",
         good_for="how the PSP toolchain is built and released (archives, container image)", licence="MIT",
         size_mb=1, set=("recommended", "psp"), checked="2026-10-14 OK",
         verify="the release you installed (v20261001 when checked)"),
    dict(id="pspdev-docs", group="psp", kind="file", url="https://pspdev.github.io/",
         good_for="toolchain installation, first programs, debugging tips; API reference at "
                  "https://pspdev.github.io/pspsdk/", licence="Unlicense (site source)", size_mb=0.1,
         set=("recommended", "psp"), checked="2026-10-14 OK", verify="record the date"),
    dict(id="ppsspp", group="psp", kind="git", url="https://github.com/hrydgard/ppsspp",
         good_for="PSP emulator source: GE commands (GPU/ge_constants.h), VFPU (Core/MIPS/MIPSVFPUUtils.cpp), "
                  "kernel HLE; shows what the emulator does not model", licence="GPL-2.0-or-later: read only",
         size_mb=360, set=("psp", "big"), checked="2026-10-14 OK",
         verify="the tag of the PPSSPP you test with (v1.20.4 when checked)"),
    dict(id="ppsspp-diffs", group="psp", kind="file",
         url="https://www.ppsspp.org/docs/development/known-differences/",
         good_for="where PPSSPP is not exact (VFPU and more); the bit-exact VFPU work is credited in "
                  "https://www.ppsspp.org/news/release-1.16/", licence="see the site", size_mb=0.1,
         set=("psp",), checked="2026-10-14 OK", verify="record the date"),
    dict(id="uofw", group="psp", kind="git", url="https://github.com/uofw/uofw",
         good_for="open re-implementation of PSP firmware modules: kernel, interrupts, power, Media Engine boot",
         licence="MIT with BSD parts (README)", size_mb=21, set=("recommended", "psp"),
         checked="2026-10-14 OK", verify="no tags: record the commit"),
    dict(id="psptek", group="psp", kind="file", url="http://daifukkat.su/docs/psptek/",
         good_for="PSP hardware at register level: memory and I/O maps, Media Engine control, GE, DMA, interrupts",
         licence="none stated: personal reference; cross-check its numbers (some are wrong)", size_mb=0.3,
         set=("recommended", "psp"), checked="2026-10-14 OK (plain HTTP only)",
         verify="the 'Last Updated' line on the page"),
    dict(id="yapspd", group="psp", kind="online", url="https://hitmen.c02.at/files/yapspd/",
         good_for="'Yet another PSP documentation' (2006): early hardware and format notes; save single files "
                  "with the `file` command", licence="none stated: personal reference", size_mb=0, set=("psp",),
         checked="2026-10-14 OK", verify="file dates in the listing"),
    dict(id="mcidclan-me", group="psp", kind="git", url="https://github.com/mcidclan/psp-media-engine-reload",
         good_for="Media Engine bring-up, memory map, eDRAM, DMA; the same author's other me-* repositories cover "
                  "spinlocks, soft interrupts and DMACplus", licence="MIT", size_mb=1, set=("psp",),
         checked="2026-10-14 OK", verify="commit"),
    dict(id="psp-developer", group="psp", kind="git", url="https://github.com/SandstoneDev/psp-developer",
         good_for="companion agent skill: PSP homebrew, GE rendering, Media Engine, VFPU, real-hardware pitfalls",
         licence="see the repository", size_mb=1, set=("recommended", "psp"),
         checked="2026-10-14 not public yet (404): skip it until it is", verify="commit"),
    # ---- CPU instruction sets (vendor documents hosted publicly; never redistribute them) -------------------------
    dict(id="mips-iv", group="isa", kind="file",
         url="https://www.cs.ucf.edu/courses/cda4150/fall05/MIPSIV_3_2.pdf",
         good_for="MIPS IV instruction set, revision 3.2: the base of the R5900's non-multimedia instructions",
         licence="vendor copyright, publicly hosted copy: personal reference only", size_mb=1.2,
         set=("recommended", "isa"), checked="2026-10-14 OK", verify="revision 3.2 on the title page"),
    dict(id="r4000", group="isa", kind="file",
         url="https://groups.csail.mit.edu/cag/raw/documents/R4400_Uman_book_Ed2.pdf",
         good_for="MIPS R4000 microprocessor book, 2nd edition: pipeline, caches, TLB, exceptions, CP0 - the "
                  "background for both the R5900 and the Allegrex", licence="vendor copyright, publicly hosted "
                  "copy: personal reference only", size_mb=2.1, set=("isa",), checked="2026-10-14 OK",
         verify="2nd edition on the title page"),
    dict(id="tx79", group="isa", kind="file",
         url="https://bitsavers.org/components/toshiba/_dataSheet/TMPR79xx-um-r2.0_200104.pdf",
         good_for="Toshiba TX79 core (derived from the R5900): 128-bit multimedia instructions, pipeline",
         licence="vendor copyright, archived copy: personal reference only", size_mb=3.9,
         set=("recommended", "isa"), checked="2026-10-14 OK", verify="revision 2.0 on the title page"),
    dict(id="mips32", group="isa", kind="file",
         url="https://www.cs.cornell.edu/courses/cs3410/2008fa/MIPS_Vol2.pdf",
         good_for="MIPS32 instruction set (volume II): the base of the PSP's Allegrex", licence="vendor "
                  "copyright, publicly hosted copy: personal reference only", size_mb=2.3, set=("isa",),
         checked="2026-10-14 OK", verify="revision on the title page"),
    # ---- prior work (design references, read only) ----------------------------------------------------------------
    dict(id="ps2recomp", group="prior", kind="git", url="https://github.com/ran-j/PS2Recomp",
         good_for="another PS2 static recompiler: compare designs, never copy", licence="GPL-3.0: read only",
         size_mb=6, set=("prior",), checked="2026-10-14 OK", verify="tag (v0.4 when checked) or commit"),
    dict(id="n64recomp", group="prior", kind="git", url="https://github.com/N64Recomp/N64Recomp",
         good_for="a mature static recompiler of another MIPS console: function discovery, overlays, runtime split",
         licence="MIT", size_mb=1, set=("prior",), checked="2026-10-14 OK", verify="commit"),
]
GROUPS = ("ps2", "psp", "isa", "prior")
# Hosts this tool never requests: they reserve their content against automated or AI use.
DENY_HOSTS = ("psdevwiki.com",)
SETS = sorted({s for e in CATALOGUE for s in e["set"]} | {"all"})


def by_id():
    return {e["id"]: e for e in CATALOGUE}


def select(ids, set_name):
    cat = by_id()
    if ids:
        bad = [i for i in ids if i not in cat]
        if bad:
            raise SystemExit("unknown id(s): %s (see `list`)" % ", ".join(bad))
        return [cat[i] for i in ids]
    if set_name:
        if set_name not in SETS:
            raise SystemExit("unknown set %r; sets: %s" % (set_name, ", ".join(SETS)))
        return [e for e in CATALOGUE if set_name == "all" or set_name in e["set"]]
    raise SystemExit("name IDs or --set (sets: %s)" % ", ".join(SETS))


# ---- network helpers -------------------------------------------------------------------------------------------
def denied(url):
    host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
    return any(host == h or host.endswith("." + h) for h in DENY_HOSTS)


def http_get(url, limit=None, method="GET", timeout=30):
    if denied(url):
        raise SystemExit("%s reserves its content against automated use: the user reads it in a browser" % url)
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(limit) if limit else r.read()
        return r.status, r.geturl(), dict(r.headers), data


def robots_allows(url, fetch=None):
    """True if robots.txt of the URL's host allows our user agent (a missing robots.txt allows)."""
    p = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    robots = urllib.parse.urlunsplit((p.scheme, p.netloc, "/robots.txt", "", ""))
    try:
        if fetch is None:
            _s, _u, _h, data = http_get(robots, limit=512 * 1024)
        else:
            data = fetch(robots)
        rp.parse(data.decode("utf-8", "replace").splitlines())
    except urllib.error.HTTPError as e:
        return e.code in (404, 410)
    except (urllib.error.URLError, OSError):
        return False
    return rp.can_fetch(UA, url)


def wayback_lookup(url):
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    _s, _u, _h, data = http_get(api)
    snap = json.loads(data.decode("utf-8")).get("archived_snapshots", {}).get("closest")
    return snap if snap and snap.get("available") else None


# ---- index -----------------------------------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_index(dest):
    p = os.path.join(dest, INDEX_JSON)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"format": 1, "items": []}


def save_index(dest, idx):
    idx["items"].sort(key=lambda r: r["id"])
    tmp = os.path.join(dest, INDEX_JSON + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(idx, f, indent=1, ensure_ascii=True)
        f.write("\n")
    os.replace(tmp, os.path.join(dest, INDEX_JSON))
    write_md(dest, idx)


def write_md(dest, idx):
    lines = ["# Reference documents on this machine", "",
             "Written by skills/fetch-docs/fetch_docs.py. Public sources only; licences as published by each source.",
             "Never commit or redistribute this folder: keep it next to your work, not inside a repository.", "",
             "| ID | Fetched (UTC) | Source | Version | Licence / terms | SHA-256 | Path |",
             "|---|---|---|---|---|---|---|"]
    for r in idx["items"]:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["fetched_utc"], r["url"], r.get("commit") or "-", r["licence"],
            (r.get("sha256") or "-")[:16], r["path"]))
    lines += ["", "Full hashes (every file of a page, the tree listing of a repository): %s" % INDEX_JSON, ""]
    with open(os.path.join(dest, INDEX_MD), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def record(dest, entry, path, extra):
    idx = load_index(dest)
    idx["items"] = [r for r in idx["items"] if r["id"] != entry["id"]]
    r = {"id": entry["id"], "url": entry["url"], "kind": entry["kind"], "licence": entry["licence"],
         "fetched_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "path": os.path.relpath(path, dest).replace(os.sep, "/")}
    r.update(extra)
    idx["items"].append(r)
    save_index(dest, idx)
    return r


def git_tree_sha256(repo):
    """SHA-256 over `git ls-tree -r HEAD` (mode, blob id, path of every file): one hash for the whole checkout."""
    out = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "HEAD"], capture_output=True, check=True).stdout
    return hashlib.sha256(out).hexdigest()


# ---- commands --------------------------------------------------------------------------------------------------
def cmd_list(a):
    rows = [e for e in CATALOGUE if not a.group or e["group"] == a.group]
    if a.json:
        print(json.dumps(rows, indent=1, default=list))
        return 0
    for e in rows:
        print("%-14s %-5s %-6s ~%5s MB  %s" % (e["id"], e["group"], e["kind"], e["size_mb"], e["url"]))
        print("%-14s %s" % ("", e["good_for"]))
        print("%-14s licence: %s | checked %s" % ("", e["licence"], e["checked"]))
    print("\nsets: %s" % ", ".join(SETS))
    return 0


def cmd_check(a):
    bad = 0
    for e in (select(a.ids, None) if a.ids else CATALOGUE):
        if e["kind"] == "online":
            print("SKIP %-14s %s (read in a browser; not requested by this tool)" % (e["id"], e["url"]))
            continue
        try:
            st, final, _h, _d = http_get(e["url"], limit=4096)
            note = "" if final.rstrip("/") == e["url"].rstrip("/") else " -> %s" % final
            print("OK   %-14s %s %s%s" % (e["id"], st, e["url"], note))
        except (urllib.error.URLError, OSError) as ex:
            bad += 1
            print("DEAD %-14s %s (%s)" % (e["id"], e["url"], getattr(ex, "code", None) or ex))
        time.sleep(PAUSE_S / 4)
    if bad:
        print("\n%d unreachable: try `wayback URL`, then the search queries in SKILL.md section 4." % bad)
    return 1 if bad else 0


def free_mb(path):
    p = os.path.abspath(path)
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return shutil.disk_usage(p).free / 1e6


def cmd_plan(a):
    sel = select(a.ids, a.set)
    total = sum(e["size_mb"] for e in sel if e["kind"] != "online")
    for e in sel:
        size = "browser" if e["kind"] == "online" else "~%s MB" % e["size_mb"]
        print("%-14s %-6s %9s  %s" % (e["id"], e["kind"], size, e["licence"]))
    print("\ntotal about %.0f MB; free on the destination drive: %.0f MB; destination: %s"
          % (total, free_mb(a.dest), os.path.abspath(a.dest)))
    print("nothing was downloaded. Ask the user, then run `fetch` with the same arguments.")
    return 0


def fetch_git(dest, e, full):
    target = os.path.join(dest, e["group"], e["id"])
    if os.path.isdir(os.path.join(target, ".git")):
        subprocess.run(["git", "-C", target, "pull", "--ff-only"], check=True)
    else:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        cmd = ["git", "clone"] + ([] if full else ["--depth", "1"]) + [e["url"] + ".git", target]
        subprocess.run(cmd, check=True)
    commit = subprocess.run(["git", "-C", target, "rev-parse", "HEAD"], capture_output=True, text=True,
                            check=True).stdout.strip()
    return target, {"commit": commit, "sha256": git_tree_sha256(target), "hash_of": "git ls-tree -r HEAD"}


def safe_name(url):
    p = urllib.parse.urlsplit(url)
    base = (p.netloc + p.path).rstrip("/") or p.netloc
    name = "".join(c if c.isalnum() or c in "._-" else "_" for c in base)
    return (name[:120] or "page") + ("" if os.path.splitext(name)[1] in (".htm", ".html", ".pdf", ".txt")
                                       else ".html")


def fetch_page(dest, e):
    if not robots_allows(e["url"]):
        raise SystemExit("robots.txt of %s does not allow fetching %s - read it in a browser instead"
                         % (urllib.parse.urlsplit(e["url"]).netloc, e["url"]))
    time.sleep(PAUSE_S)
    st, final, headers, data = http_get(e["url"])
    target = os.path.join(dest, e["group"], e["id"], safe_name(final))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(data)
    return target, {"final_url": final, "http_status": st, "bytes": len(data), "sha256": sha256_file(target),
                    "content_type": headers.get("Content-Type", "")}


def cmd_fetch(a):
    sel = select(a.ids, a.set)
    os.makedirs(a.dest, exist_ok=True)
    if sel and any(e["kind"] == "git" for e in sel) and not shutil.which("git"):
        raise SystemExit("git not found; install git or fetch only pages")
    for e in sel:
        print("== %s (%s)" % (e["id"], e["url"]))
        if e["kind"] == "online":
            print("   not fetched: read it in a browser (SKILL.md section 3)")
            continue
        try:
            path, extra = fetch_git(a.dest, e, a.full_history) if e["kind"] == "git" else fetch_page(a.dest, e)
        except (subprocess.CalledProcessError, urllib.error.URLError, OSError) as ex:
            print("   FAILED: %s - see SKILL.md section 4 (fallbacks)" % ex)
            continue
        r = record(a.dest, e, path, extra)
        print("   saved %s  sha256 %s" % (r["path"], r["sha256"][:16]))
    print("index: %s" % os.path.join(os.path.abspath(a.dest), INDEX_MD))
    return 0


def cmd_file(a):
    if not a.url.lower().startswith(("https://", "http://")):
        raise SystemExit("only http(s) URLs")
    if not all(c.isalnum() or c in "-_" for c in a.name):
        raise SystemExit("--name: letters, digits, '-' and '_' only")
    e = {"id": a.name, "group": "extra", "kind": "file", "url": a.url, "licence": a.licence}
    path, extra = fetch_page(a.dest, e)
    r = record(a.dest, e, path, extra)
    print("saved %s  sha256 %s" % (r["path"], r["sha256"][:16]))
    return 0


def cmd_wayback(a):
    snap = wayback_lookup(a.url)
    if not snap:
        print("no archived copy; search the title of the page instead (SKILL.md section 4)")
        return 1
    print("%s  (archived %s)" % (snap["url"], snap.get("timestamp", "?")))
    return 0


def cmd_verify(a):
    idx = load_index(a.dest)
    bad = 0
    for r in idx["items"]:
        p = os.path.join(a.dest, r["path"])
        if not os.path.exists(p):
            bad += 1
            print("MISSING %s %s" % (r["id"], r["path"]))
            continue
        now = git_tree_sha256(p) if r["kind"] == "git" else sha256_file(p)
        ok = now == r.get("sha256")
        bad += not ok
        print("%s %s" % ("OK     " if ok else "CHANGED", r["id"]))
    return 1 if bad else 0


def cmd_index(a):
    write_md(a.dest, load_index(a.dest))
    print(os.path.join(os.path.abspath(a.dest), INDEX_MD))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--group", choices=GROUPS)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("check")
    p.add_argument("ids", nargs="*")
    for name in ("plan", "fetch"):
        p = sub.add_parser(name)
        p.add_argument("--dest", required=True)
        p.add_argument("ids", nargs="*")
        p.add_argument("--set")
        if name == "fetch":
            p.add_argument("--full-history", action="store_true", help="full clone instead of --depth 1")
    p = sub.add_parser("file")
    for k in ("--dest", "--url", "--name", "--licence"):
        p.add_argument(k, required=True)
    sub.add_parser("wayback").add_argument("url")
    sub.add_parser("verify").add_argument("--dest", required=True)
    sub.add_parser("index").add_argument("--dest", required=True)
    a = ap.parse_args(argv)
    return {"list": cmd_list, "check": cmd_check, "plan": cmd_plan, "fetch": cmd_fetch, "file": cmd_file,
            "wayback": cmd_wayback, "verify": cmd_verify, "index": cmd_index}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
