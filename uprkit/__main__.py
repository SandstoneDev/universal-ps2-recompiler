"""Command line of the universal-ps2-recompiler agent kit.

    python -m uprkit setup|status|verify|update|new-pack|link|check-pack ...
                                 the PS2RC workspace (skills/setup-ps2rc/setup_ps2rc.py; --help on each command)
    python -m uprkit doctor [--workspace DIR] [--json] [--wsl] [--online]
                                 what this machine has and lacks for a port, and the official source of each item
    python -m uprkit skills list|check|sync [--target DIR ...]
                                 the agent skills in skills/ (sync copies them where agents look)
    python -m uprkit kb list | search WORDS | new CATEGORY SLUG TITLE | index [--check] | check
                                 the knowledge base of field notes in knowledge/

The engine itself is PS2RC, downloaded into the workspace by `setup`: run its commands (python -m ps2rc doctor,
bash mk/build.sh, python -m ps2rc.convert ...) inside <workspace>/PS2RC.
"""
import importlib.util
import os
import sys

from . import setup_script_dir


def _load(name):
    path = os.path.join(setup_script_dir(), name + ".py")
    spec = importlib.util.spec_from_file_location("uprkit_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, setup_script_dir())
    spec.loader.exec_module(mod)
    return mod


SETUP_CMDS = ("setup", "status", "verify", "update", "new-pack", "link", "check-pack")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in SETUP_CMDS:
        return _load("setup_ps2rc").main([cmd] + rest)
    if cmd == "doctor":
        return _load("doctor").main(rest)
    if cmd == "skills":
        from . import skills
        return skills.main(rest)
    if cmd in ("kb", "knowledge"):
        from . import kb
        return kb.main(rest)
    print("unknown command %r (try: python -m uprkit --help)" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
