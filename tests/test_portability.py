"""The kit must work on anyone's machine: no absolute paths, drive letters, home folders, user or machine names, tool
locations or names of the authors' private files anywhere in the tree. Every location is asked or discovered at run
time.

Optional: UPR_AUDIT=<path of a release audit script> (and UPR_PS2RC_REF=<a PS2RC checkout> for the engine paths the
documents name) also runs that audit over the tree and expects 0 blocking hits."""
import hashlib
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".agents", ".claude"}

# Windows drive paths, home folders, WSL mounts of a drive, UNC shares.
PATH_RULES = [
    ("drive-path", re.compile(r"(?<![A-Za-z0-9_%])[A-Za-z]:[\\/][A-Za-z0-9_]")),
    ("home-path", re.compile(r"(?i)(?:/home/|/Users/|\\Users\\)[A-Za-z0-9_.-]+")),
    ("wsl-drive", re.compile(r"/mnt/[a-z]/[A-Za-z0-9_]")),
    ("unc-path", re.compile(r"\\\\[A-Za-z0-9_-]+\\[A-Za-z0-9_$]")),
    ("private-report", re.compile(r"\b[A-Z]{1,2}_[a-z0-9]+(?:_[a-z0-9]+)*\.md\b")),
    ("agent-letter", re.compile(r"\bagents? [A-Z]{1,2}\b(?![a-z])")),
]
# (rule, exact match) -> why it is allowed. Empty: nothing is.
ALLOWED_MATCHES = {}

# SHA-256 prefixes of lower-case words that must never appear: the authors' user, machine, folder and private file
# names (stored hashed so this public test does not publish them).
DENY_HASHES = {
    "dde9a01be8091c8e025a", "3d11b077e1dfc1e318fc", "2a33352a9d84e2c810db", "df87b787d0028b62b01f",
    "2b3d4ca3d1124eceded8", "ea3cb6b2c97f40924045", "7bd099cbdb191eb793e1", "5fe0ea16c6aecfb1cc7c",
    "7230e8928ffd5e34e389", "025ff027f87e101c2f06", "414b29e5114c4cb830d7", "775a3e6ecce48fa03fbb",
    "a2c8c93103170a4a5b1f", "a59e622baf578b736682", "276ae4047bca70765ad3", "d2f910373e4c092ba30b",
}
WORD = re.compile(r"[A-Za-z0-9_-]+")


def tree_files():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            p = os.path.join(dp, fn)
            yield os.path.relpath(p, ROOT).replace(os.sep, "/"), p


def text_of(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def hashed(word):
    return hashlib.sha256(word.encode("utf-8")).hexdigest()[:20]


def test_rules_fire_on_samples():
    # built from pieces, so that the release audit does not read them as real paths, names or links
    samples = {"drive-path": "see D" + ":\\games\\x", "home-path": "/home" + "/someone/x", "wsl-drive": "/mnt" + "/c/Tools",
               "unc-path": "\\\\server\\share", "private-report": "read XY_some_report.md",
               "agent-letter": "agent " + "AB did it"}
    for name, rx in PATH_RULES:
        assert rx.search(samples[name]), name
    assert not PATH_RULES[0][1].search("%SystemDrive%\\x and " + "https://" + "example.org/a:b")
    assert hashed("example") not in DENY_HASHES


def test_no_machine_specific_text():
    bad = []
    for rel, p in tree_files():
        if rel == "tests/test_portability.py":
            continue
        text = text_of(p)
        if text is None:
            bad.append("%s: binary file" % rel)
            continue
        for ln, line in enumerate(text.splitlines(), 1):
            for name, rx in PATH_RULES:
                for m in rx.finditer(line):
                    if (name, m.group(0)) not in ALLOWED_MATCHES:
                        bad.append("%s:%d %s %r" % (rel, ln, name, m.group(0)))
            for w in WORD.findall(line):
                lw = w.lower()
                for part in {lw} | set(re.split(r"[-_]", lw)):
                    if part and hashed(part) in DENY_HASHES:
                        bad.append("%s:%d private name (a word whose hash is denied)" % (rel, ln))
    assert not bad, "\n".join(bad[:40])


def test_text_is_ascii_and_lf():
    bad = []
    for rel, p in tree_files():
        text = text_of(p)
        if text is None:
            continue
        if not text.isascii():
            bad.append("%s: non-ASCII" % rel)
        if "\r\n" in text and not rel.endswith((".ps1", ".cmd")):
            bad.append("%s: CRLF line endings" % rel)
    assert not bad, "\n".join(bad)


@pytest.mark.skipif(not os.environ.get("UPR_AUDIT"), reason="set UPR_AUDIT to a release audit script to run it")
def test_release_audit_clean():
    cmd = [sys.executable, os.environ["UPR_AUDIT"], ROOT]
    if os.environ.get("UPR_PS2RC_REF"):
        cmd += ["--ref-tree", os.environ["UPR_PS2RC_REF"]]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace")
    assert r.returncode == 0 and "TOTAL BLOCKING HITS: 0" in out, out[-4000:]
