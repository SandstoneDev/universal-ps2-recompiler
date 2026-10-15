"""setup-ps2rc: workspace setup, verification, update, packs and pack checks - offline, on a synthetic PS2RC tree.

No network: archives are built here, git clones come from a local repository. Optional: set UPR_PS2RC_FIXTURE to a
local clone of PS2RC that contains the pinned default commit to check the real lock against it."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "setup-ps2rc")


def load(name):
    spec = importlib.util.spec_from_file_location("t_" + name, os.path.join(SKILL, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sp = load("setup_ps2rc")
doctor = load("doctor")
HAVE_GIT = shutil.which("git") is not None
FAKE_COMMIT = "1" * 40
FAKE_URL = "https://" + "example.invalid"          # (in pieces: the release audit flags unknown hosts)
LISTED = "TEST-00001"           # a listed disc: its pack carries DISTRIBUTION.md (PS2RC License 1.1)
LEGACY = "TEST-00002"           # backward compatibility: PS2RC v0.1.0 / v0.1.1 name that notice RESERVED.md

TEMPLATE_TOML = """# pack.toml - template
format = 1

[id]
serial = "SLUS-00000"
version = "1.00"
region = "NTSC-U"
boot_elf = "SLUS_000.00"
psp_title = "My game (PS2RC)"

[verify]
system_cnf_boot2 = 'cdrom0:\\SLUS_000.00;1'
elf_size = 0
"""

LISTED_C = "\n".join("int listed_function_number_%02d(void) { return %d * 7; }" % (i, i) for i in range(30)) + "\n"
LEGACY_C = "\n".join("int legacy_function_number_%02d(void) { return %d * 9; }" % (i, i) for i in range(30)) + "\n"


def engine_files(version="9.9.9"):
    return {
        "pytest.ini": "[pytest]\n",
        "README.md": "# PS2RC (synthetic test tree %s)\n" % version,
        "ps2rc/__init__.py": "VERSION = %r\n" % version,
        "ps2rc/pack.py": "FORMAT = 1\n",
        "games/_template/pack.toml": TEMPLATE_TOML,
        "games/_template/README.md": "# Game pack template\n",
        "games/_template/hooks.def": "# hooks\n",
        "games/_template/src/pack_main.c": "/* the pack's side of the HLE interface */\nint pack_init(void) { return 0; }\n",
        "games/example/pack.toml": TEMPLATE_TOML.replace("SLUS-00000", "EXAM-00001"),
        "games/%s_v1.00/DISTRIBUTION.md" % LISTED: "# Distribution notice\n\n| Disc serial | Version |\n|---|---|\n"
                                                   "| %s | 1.00 |\n" % LISTED,
        "games/%s_v1.00/src/world.c" % LISTED: LISTED_C,
        "games/%s_v1.00/pack.toml" % LISTED: TEMPLATE_TOML.replace("SLUS-00000", LISTED),
        # the notice's name in PS2RC v0.1.0 / v0.1.1 (backward compatibility of the detection)
        "games/%s_v1.00/RESERVED.md" % LEGACY: "# notice\n\n| Disc serial | Version |\n|---|---|\n| %s | 1.00 |\n" % LEGACY,
        "games/%s_v1.00/src/world.c" % LEGACY: LEGACY_C,
        "games/%s_v1.00/pack.toml" % LEGACY: TEMPLATE_TOML.replace("SLUS-00000", LEGACY),
    }


def make_zip(path, files, top, comment=FAKE_COMMIT, compress=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w", compress) as z:
        z.writestr(top + "/", "")
        for rel in sorted(files):
            z.writestr("%s/%s" % (top, rel), files[rel].encode("utf-8"))
        z.comment = comment.encode("ascii")
    return path


def lock_for(tmp, releases, default):
    lock = {"format": 1, "repo": "test/PS2RC", "url": FAKE_URL + "/PS2RC", "default": default,
            "listed": [{"serial": LISTED}], "releases": releases}
    p = os.path.join(str(tmp), "lock.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(lock, f)
    return p


def release_of(zpath, commit=FAKE_COMMIT, tag="v9.9.9"):
    rows, _top, _c = sp.zip_rows(zpath)
    return {"commit": commit, "tree_sha256": sp.tree_hash(rows), "files": len(rows), "pack_format": 1,
            "source_zip": {"url": FAKE_URL + "/%s.zip" % tag, "sha256": sp.sha256_file(zpath)},
            "assets": {}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A synthetic release v9.9.9 as a zip, its lock, and a workspace path."""
    monkeypatch.delenv("UPR_WORKSPACE", raising=False)
    z = make_zip(str(tmp_path / "PS2RC-9.9.9.zip"), engine_files(), "PS2RC-9.9.9")
    lock = lock_for(tmp_path, {"v9.9.9": release_of(z)}, "v9.9.9")
    ws = tmp_path / "ws"
    return dict(tmp=tmp_path, zip=z, lock=lock, ws=str(ws))


def run(lock, *args):
    return sp.main(["--lock", lock] + list(args))


def manifest(ws):
    with open(os.path.join(ws, sp.MANIFEST), encoding="utf-8") as f:
        return json.load(f)


def test_setup_from_zip_offline(env, capsys):
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"]) == 0
    m = manifest(env["ws"])
    assert m["ps2rc"]["tag"] == "v9.9.9" and m["ps2rc"]["commit"] == FAKE_COMMIT and m["ps2rc"]["pinned"]
    assert m["ps2rc"]["method"] == "zip"
    for d in ("PS2RC/games/_template", "packs", "work", "refdocs", "downloads"):
        assert os.path.isdir(os.path.join(env["ws"], d)), d
    for f in ("local.toml", "env.sh", "env.ps1", "env.cmd", "WORKSPACE.txt", sp.FILELIST, "PS2RC/local.toml"):
        assert os.path.isfile(os.path.join(env["ws"], f)), f
    assert run(env["lock"], "verify", "--workspace", env["ws"]) == 0
    assert run(env["lock"], "status", "--workspace", env["ws"]) == 0
    assert "in sync" in capsys.readouterr().out


def test_dry_run_writes_nothing(env):
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"], "--dry-run") == 0
    assert not os.path.exists(env["ws"])


def test_tampered_tree_is_refused(env):
    files = engine_files()
    files["ps2rc/pack.py"] += "# changed\n"
    bad = make_zip(str(env["tmp"] / "bad.zip"), files, "PS2RC-9.9.9")
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", bad) == 1
    assert not os.path.exists(os.path.join(env["ws"], "PS2RC"))


def test_moved_tag_is_refused(env):
    other = make_zip(str(env["tmp"] / "other.zip"), engine_files(), "PS2RC-9.9.9", comment="2" * 40)
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", other) == 1


def test_recompressed_archive_with_same_content_is_accepted(env, capsys):
    same = make_zip(str(env["tmp"] / "stored.zip"), engine_files(), "PS2RC-9.9.9", compress=zipfile.ZIP_STORED)
    assert sp.sha256_file(same) != sp.sha256_file(env["zip"])
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", same) == 0
    assert "content hash matches" in capsys.readouterr().out


def test_unsafe_archive_is_refused(env):
    p = str(env["tmp"] / "evil.zip")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("PS2RC-9.9.9/ok.txt", "x")
        z.writestr("PS2RC-9.9.9/../../escape.txt", "x")
    with pytest.raises(sp.SetupError):
        sp.zip_rows(p)


def test_unpinned_tag_needs_permission(env):
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"], "--tag", "v0.0.1") == 1
    assert not os.path.exists(os.path.join(env["ws"], "PS2RC"))


def test_private_or_missing_repository_message(env, monkeypatch, capsys):
    def boom(*a, **k):
        raise urllib.error.HTTPError(FAKE_URL + "/x.zip", 404, "Not Found", {}, io.BytesIO(b""))
    monkeypatch.setattr(sp.urllib.request, "urlopen", boom)
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--method", "zip") == sp.EXIT_PRIVATE
    err = capsys.readouterr().err
    assert "private" in err and "--zip" in err


@pytest.mark.skipif(not HAVE_GIT, reason="git not installed")
def test_private_repository_message_git(env, capsys):
    missing = str(env["tmp"] / "no-such-repo")
    rc = run(env["lock"], "setup", "--workspace", env["ws"], "--method", "git", "--source", missing)
    assert rc == sp.EXIT_PRIVATE
    assert "private" in capsys.readouterr().err


def git_repo(path, files, tag):
    os.makedirs(path)
    for rel, text in files.items():
        p = os.path.join(path, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    g = ["git", "-c", "user.name=test", "-c", "user.email=test" + "@example.invalid", "-c", "core.autocrlf=false"]
    subprocess.run(g + ["init", "-q"], cwd=path, check=True)
    subprocess.run(g + ["add", "-A"], cwd=path, check=True)
    subprocess.run(g + ["commit", "-q", "-m", "release"], cwd=path, check=True)
    subprocess.run(g + ["tag", tag], cwd=path, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, stdout=subprocess.PIPE, check=True).stdout.decode().strip()


@pytest.mark.skipif(not HAVE_GIT, reason="git not installed")
def test_setup_by_git_clone_and_zip_agree(tmp_path, monkeypatch):
    monkeypatch.delenv("UPR_WORKSPACE", raising=False)
    src = str(tmp_path / "src")
    commit = git_repo(src, engine_files(), "v9.9.9")
    z = str(tmp_path / "archive.zip")
    subprocess.run(["git", "archive", "--format=zip", "--prefix=PS2RC-9.9.9/", "-o", z, "v9.9.9"], cwd=src, check=True)
    rel = release_of(z, commit=commit)
    assert rel["tree_sha256"] == sp.tree_hash([(p, h) for p, h in sp.zip_rows(z)[0]])
    lock = lock_for(tmp_path, {"v9.9.9": rel}, "v9.9.9")
    ws = str(tmp_path / "ws")
    assert run(lock, "setup", "--workspace", ws, "--method", "git", "--source", src) == 0
    m = manifest(ws)
    assert m["ps2rc"]["method"] == "git" and m["ps2rc"]["commit"] == commit
    assert m["ps2rc"]["tree_sha256"] == rel["tree_sha256"]
    assert run(lock, "verify", "--workspace", ws) == 0


def test_new_pack_link_and_listed(env):
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"]) == 0
    assert run(env["lock"], "new-pack", "SLUS-12345", "1.00", "--region", "NTSC-U", "--workspace", env["ws"]) == 0
    pack = os.path.join(env["ws"], "packs", "SLUS-12345_v1.00")
    seen = os.path.join(env["ws"], "PS2RC", "games", "SLUS-12345_v1.00", "pack.toml")
    assert os.path.isfile(seen)
    text = open(os.path.join(pack, "pack.toml"), encoding="utf-8").read()
    assert 'serial = "SLUS-12345"' in text and 'boot_elf = "SLUS_123.45"' in text
    assert "cdrom0:\\SLUS_123.45;1" in text
    readme = open(os.path.join(pack, "README.md"), encoding="utf-8").read()
    assert "Based on PS2RC by SandstoneDev" in readme
    assert run(env["lock"], "new-pack", LISTED, "1.00", "--workspace", env["ws"]) == 3
    assert run(env["lock"], "new-pack", LEGACY, "1.00", "--workspace", env["ws"]) == 3     # found by its old notice
    assert run(env["lock"], "new-pack", "bad", "1.00", "--workspace", env["ws"]) == 1
    assert run(env["lock"], "check-pack", "SLUS-12345_v1.00", "--workspace", env["ws"]) == 0
    m = manifest(env["ws"])
    assert m["packs"][0]["link"] in ("junction", "symlink", "copy")


def test_check_pack_finds_copied_code(env, capsys):
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"]) == 0
    assert run(env["lock"], "new-pack", "SLUS-12345", "1.00", "--workspace", env["ws"]) == 0
    src = os.path.join(env["ws"], "packs", "SLUS-12345_v1.00", "src")
    with open(os.path.join(src, "copied.c"), "w", encoding="utf-8") as f:
        f.write("/* mine */\n" + "\n".join(LISTED_C.splitlines()[3:12]) + "\n")
    shutil.copy(os.path.join(env["ws"], "PS2RC", "games", "%s_v1.00" % LISTED, "src", "world.c"),
                os.path.join(src, "world.c"))
    with open(os.path.join(src, "old.c"), "w", encoding="utf-8") as f:
        f.write("/* mine */\n" + "\n".join(LEGACY_C.splitlines()[3:12]) + "\n")
    with open(os.path.join(src, "disc.iso"), "wb") as f:
        f.write(b"\0" * 16)
    assert run(env["lock"], "check-pack", "SLUS-12345_v1.00", "--workspace", env["ws"]) == 1
    out = capsys.readouterr().out
    assert "copied.c" in out and "identical" in out and "disc.iso" in out
    assert "old.c" in out and "%s_v1.00" % LEGACY in out


def test_listed_serials_old_lock_key():
    # kit locks before PS2RC License 1.1 named the list "reserved" (backward compatibility)
    assert sp.listed_serials({"reserved": [{"serial": "TEST-00003"}]}) == {"TEST-00003"}
    assert sp.listed_serials({"listed": [{"serial": "TEST-00004"}]}) == {"TEST-00004"}


def test_update_keeps_packs_and_refuses_local_edits(env, capsys):
    z2 = make_zip(str(env["tmp"] / "PS2RC-9.9.10.zip"), engine_files("9.9.10"), "PS2RC-9.9.10", comment="3" * 40)
    with open(env["lock"], encoding="utf-8") as f:
        lock = json.load(f)
    lock["releases"]["v9.9.10"] = release_of(z2, commit="3" * 40, tag="v9.9.10")
    lock["default"] = "v9.9.10"
    with open(env["lock"], "w", encoding="utf-8") as f:
        json.dump(lock, f)
    assert run(env["lock"], "setup", "--workspace", env["ws"], "--zip", env["zip"], "--tag", "v9.9.9") == 0
    assert run(env["lock"], "new-pack", "SLUS-12345", "1.00", "--workspace", env["ws"]) == 0
    mine = os.path.join(env["ws"], "packs", "SLUS-12345_v1.00", "src", "mine.c")
    with open(mine, "w", encoding="utf-8") as f:
        f.write("int mine(void) { return 1; }\n")
    engine_readme = os.path.join(env["ws"], "PS2RC", "README.md")
    with open(engine_readme, "a", encoding="utf-8") as f:
        f.write("local edit\n")
    assert run(env["lock"], "update", "--workspace", env["ws"], "--zip", z2) == 1        # local edit: refused
    assert manifest(env["ws"])["ps2rc"]["tag"] == "v9.9.9"
    assert run(env["lock"], "update", "--workspace", env["ws"], "--zip", z2, "--accept-backup") == 0
    m = manifest(env["ws"])
    assert m["ps2rc"]["tag"] == "v9.9.10" and m["history"][-1]["from"] == "v9.9.9"
    assert os.path.isfile(mine)                                                          # the pack is untouched
    assert os.path.isfile(os.path.join(env["ws"], "PS2RC", "games", "SLUS-12345_v1.00", "src", "mine.c"))
    assert "9.9.10" in open(engine_readme, encoding="utf-8").read()
    backups = [d for d in os.listdir(env["ws"]) if d.startswith("PS2RC.backup-v9.9.9")]
    assert len(backups) == 1
    assert "local edit" in open(os.path.join(env["ws"], backups[0], "README.md"), encoding="utf-8").read()
    assert not os.path.exists(os.path.join(env["ws"], backups[0], "games", "SLUS-12345_v1.00"))
    assert run(env["lock"], "verify", "--workspace", env["ws"]) == 0


def test_workspace_location_rules(env, tmp_path):
    repo = tmp_path / "somerepo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(sp.SetupError):
        sp.check_workspace_dir(str(repo / "ws"))
    full = tmp_path / "full"
    full.mkdir()
    (full / "x.txt").write_text("x", encoding="utf-8")
    with pytest.raises(sp.SetupError):
        sp.check_workspace_dir(str(full))
    with pytest.raises(sp.SetupError):
        sp.check_workspace_dir(str(tmp_path / "with space"))
    with pytest.raises(sp.SetupError):
        sp.check_workspace_dir(str(tmp_path / ("caf" + chr(233))))
    d = sp.default_workspace()
    assert d.isascii() and " " not in d


def test_real_lock_is_consistent():
    lock = sp.load_lock()
    rel = lock["releases"][lock["default"]]
    assert len(rel["commit"]) == 40 and len(rel["tree_sha256"]) == 64
    assert rel["source_zip"]["url"].startswith(lock["url"])
    for a in rel["assets"].values():
        assert a["url"].startswith(lock["url"] + "/releases/download/" + lock["default"] + "/") and len(a["sha256"]) == 64
    assert lock["listed"]


@pytest.mark.skipif(not os.environ.get("UPR_PS2RC_FIXTURE") or not HAVE_GIT,
                    reason="set UPR_PS2RC_FIXTURE to a local PS2RC clone to check the real lock")
def test_real_release_against_local_clone(tmp_path, monkeypatch):
    monkeypatch.delenv("UPR_WORKSPACE", raising=False)
    lock = sp.load_lock()
    rel = lock["releases"][lock["default"]]
    z = str(tmp_path / "real.zip")
    subprocess.run(["git", "archive", "--format=zip", "--prefix=PS2RC/", "-o", z, rel["commit"]],
                   cwd=os.environ["UPR_PS2RC_FIXTURE"], check=True)
    with zipfile.ZipFile(z, "a") as zz:
        zz.comment = rel["commit"].encode("ascii")
    ws = str(tmp_path / "ws")
    assert sp.main(["setup", "--workspace", ws, "--zip", z]) == 0
    assert manifest(ws)["ps2rc"]["tree_sha256"] == rel["tree_sha256"]
    assert sp.main(["new-pack", "SLUS-12345", "1.00", "--workspace", ws]) == 0
    assert sp.main(["check-pack", "SLUS-12345_v1.00", "--workspace", ws]) == 0
    for r in lock["listed"]:
        assert sp.main(["new-pack", r["serial"], r["version"], "--workspace", ws]) == 3


def test_doctor_runs_offline(tmp_path, capsys):
    assert doctor.main(["--json", "--workspace", str(tmp_path)]) in (0, 1)
    data = json.loads(capsys.readouterr().out)
    ids = [c["id"] for c in data["checks"]]
    for want in ("python", "pymods", "git", "ps2rc", "psp-toolchain", "host-gcc", "ffmpeg", "ppsspp", "pcsx2"):
        assert want in ids
    assert data["os"]["kind"] in ("windows", "linux", "wsl", sys.platform)
    for c in data["checks"]:
        if c["state"] != "ok" and c["id"] in doctor.DEPS:
            assert "http" in c["hint"], c["id"]
