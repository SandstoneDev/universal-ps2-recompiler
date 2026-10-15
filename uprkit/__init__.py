"""uprkit - the command line of the universal-ps2-recompiler agent kit (skills, knowledge base, PS2RC workspace).

Standard library only. It reads this checkout and the machine's tool installation; downloads happen only in
`setup` / `update` (PS2RC releases, verified against skills/setup-ps2rc/ps2rc.lock.json)."""
import os


def repo_root():
    """The kit checkout: the folder that holds AGENTS.md and skills/ above this package."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_dir(name):
    return os.path.join(repo_root(), name)


def find_file(name):
    p = os.path.join(repo_root(), name)
    return p if os.path.isfile(p) else None


def setup_script_dir():
    return os.path.join(repo_root(), "skills", "setup-ps2rc")
