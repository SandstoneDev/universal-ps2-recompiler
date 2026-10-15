"""python -m uprkit skills - the agent skills of this kit.

    python -m uprkit skills list                 name and description of every skill in skills/
    python -m uprkit skills check                validate every SKILL.md (and report stale copies)
    python -m uprkit skills sync [--target DIR]  copy skills/ into the folders where agents look for skills

skills/ is the only source. `sync` copies it, by default, into .agents/skills (read by several agents) and into the
skills folder of the agent that reads CLAUDE.md; --target adds or replaces destinations (relative to the checkout or
absolute). Each destination gets a .gitignore so the copies are never committed, and a stamp file listing the skills
it wrote: sync replaces and removes only those, never skills the user put there.
"""
import argparse
import os
import re
import shutil
import sys

from . import find_dir, repo_root

NAME_RX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STAMP = ".uprkit-skills-sync"


def default_targets():
    root = repo_root()
    return [os.path.join(root, ".agents", "skills"), os.path.join(root, ".claude", "skills")]


def source_dir():
    return find_dir("skills")


def parse_frontmatter(text):
    """{key: value} of the YAML front matter (simple 'key: value' lines; quoted values unquoted), or None."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    out = {}
    for line in text[3:end].strip("\n").splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out[m.group(1)] = v
    return out


def load(src=None):
    """[(folder name, path of SKILL.md, frontmatter or None)] sorted by name."""
    src = src or source_dir()
    out = []
    for name in sorted(os.listdir(src)) if os.path.isdir(src) else []:
        p = os.path.join(src, name, "SKILL.md")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                out.append((name, p, parse_frontmatter(f.read())))
    return out


def problems(src=None):
    """Every rule a skill breaks: [(skill, message)]."""
    bad = []
    skills = load(src)
    if not skills:
        bad.append(("-", "no skills found in %s" % (src or source_dir())))
    for name, path, fm in skills:
        if fm is None:
            bad.append((name, "SKILL.md has no front matter (--- name / description ---)"))
            continue
        if fm.get("name") != name:
            bad.append((name, "front matter name %r differs from the folder name" % fm.get("name")))
        if not NAME_RX.match(name) or len(name) > 64:
            bad.append((name, "name must be lowercase words joined by '-', at most 64 characters"))
        d = fm.get("description", "")
        if not d:
            bad.append((name, "description missing"))
        elif len(d) > 1024:
            bad.append((name, "description longer than 1024 characters (%d)" % len(d)))
        if "<" in d or ">" in d:
            bad.append((name, "description must not contain angle brackets"))
    return bad


def _files(d):
    out = {}
    for dp, _dns, fns in os.walk(d):
        for fn in fns:
            p = os.path.join(dp, fn)
            with open(p, "rb") as f:
                out[os.path.relpath(p, d).replace(os.sep, "/")] = f.read()
    return out


def stale(target, src=None):
    """Skill names whose copy in target differs from the source (or is missing there)."""
    src = src or source_dir()
    out = []
    for name, _p, _fm in load(src):
        if not os.path.isdir(os.path.join(target, name)) or \
                _files(os.path.join(src, name)) != _files(os.path.join(target, name)):
            out.append(name)
    return out


def sync(targets=None, src=None, say=print):
    src = src or source_dir()
    bad = problems(src)
    if bad:
        for n, m in bad:
            say("  %s: %s" % (n, m))
        raise SystemExit("skills: fix the problems above before syncing")
    names = [n for n, _p, _fm in load(src)]
    for t in targets or default_targets():
        os.makedirs(t, exist_ok=True)
        stamp = os.path.join(t, STAMP)
        before = []
        if os.path.exists(stamp):
            with open(stamp, encoding="utf-8") as f:
                before = [x.strip() for x in f if x.strip()]
        for old in before:
            if old not in names and NAME_RX.match(old) and os.path.isdir(os.path.join(t, old)):
                shutil.rmtree(os.path.join(t, old))
                say("  removed %s/%s (no longer in skills/)" % (t, old))
        for n in names:
            dst = os.path.join(t, n)
            if os.path.isdir(dst) and n not in before:
                say("  kept %s: a skill of that name was already there and was not made by sync" % dst)
                continue
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(os.path.join(src, n), dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        with open(stamp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(names) + "\n")
        gi = os.path.join(t, ".gitignore")
        if not os.path.exists(gi):
            with open(gi, "w", encoding="utf-8", newline="\n") as f:
                f.write("# copies made by python -m uprkit skills sync (the source is skills/): never committed\n*\n")
        say("  %d skills -> %s" % (len(names), t))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m uprkit skills", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("list", "check", "sync"))
    ap.add_argument("--target", action="append", help="destination folder (repeatable; default: the agent folders)")
    a = ap.parse_args(argv)
    root = repo_root()
    targets = [os.path.join(root, t) for t in (os.path.expanduser(x) for x in a.target)] if a.target else None
    if a.action == "list":
        for name, _p, fm in load():
            d = (fm or {}).get("description", "?")
            print("%-18s %s" % (name, d if len(d) < 160 else d[:157] + "..."))
        return 0
    if a.action == "check":
        bad = problems()
        for n, m in bad:
            print("FAIL %s: %s" % (n, m))
        for t in targets or default_targets():
            if os.path.isdir(t):
                st = stale(t)
                print("%s %s%s" % ("stale" if st else "ok   ", t, (": " + ", ".join(st)) if st else ""))
        print("%d skills, %d problems" % (len(load()), len(bad)))
        return 1 if bad else 0
    sync(targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
