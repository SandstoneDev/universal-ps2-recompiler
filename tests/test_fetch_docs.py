"""The fetch-docs skill: catalogue and index logic (no network, no game data)."""
import importlib.util
import json
import os
import re
import pytest

from uprkit import repo_root

ROOT = repo_root()
SKILL_DIR = os.path.join(ROOT, "skills", "fetch-docs")


def load_tool():
    spec = importlib.util.spec_from_file_location("fetch_docs", os.path.join(SKILL_DIR, "fetch_docs.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


fd = load_tool()


def test_catalogue_fields_and_skill_table():
    ids = [e["id"] for e in fd.CATALOGUE]
    assert len(ids) == len(set(ids))
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    for e in fd.CATALOGUE:
        assert re.match(r"^[a-z0-9-]+$", e["id"]), e["id"]
        assert e["kind"] in ("git", "file", "online") and e["group"] in fd.GROUPS and e["checked"]
        assert e["url"].startswith(("https://", "http://")) and e["licence"] and e["good_for"] and e["verify"]
        assert "`%s`" % e["id"] in skill, "SKILL.md does not list %s" % e["id"]
        assert e["url"] in skill, "SKILL.md does not show the URL of %s" % e["id"]
    assert "recommended" in fd.SETS and "all" in fd.SETS


def test_select_and_errors():
    assert [e["id"] for e in fd.select(["pspsdk"], None)] == ["pspsdk"]
    assert len(fd.select([], "all")) == len(fd.CATALOGUE)
    assert all("recommended" in e["set"] for e in fd.select([], "recommended"))
    with pytest.raises(SystemExit):
        fd.select(["no-such-source"], None)
    with pytest.raises(SystemExit):
        fd.select([], None)


def test_robots_parser_respected():
    deny = b"User-agent: *\nDisallow: /private/\n"
    assert fd.robots_allows("https://pspdev.github.io/docs/a.html", fetch=lambda u: deny)
    assert not fd.robots_allows("https://pspdev.github.io/private/a.html", fetch=lambda u: deny)


def test_record_and_verify_page(tmp_path):
    dest = tmp_path / "refdocs"
    f = dest / "psp" / "x" / "page.html"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"<html>public page</html>")
    e = {"id": "x", "url": "https://pspdev.github.io/page", "kind": "file", "licence": "see the page", "group": "psp"}
    r = fd.record(str(dest), e, str(f), {"sha256": fd.sha256_file(str(f))})
    assert r["path"] == "psp/x/page.html"
    idx = json.loads((dest / fd.INDEX_JSON).read_text(encoding="utf-8"))
    assert idx["items"][0]["sha256"] == fd.sha256_file(str(f))
    md = (dest / fd.INDEX_MD).read_text(encoding="utf-8")
    assert "https://pspdev.github.io/page" in md and md.isascii()
    assert fd.main(["verify", "--dest", str(dest)]) == 0
    f.write_bytes(b"changed")
    assert fd.main(["verify", "--dest", str(dest)]) == 1


def test_git_tree_hash_is_sha256_of_ls_tree(monkeypatch):
    listing = b"100644 blob deadbeef\ta.txt\n"

    class R:
        stdout = listing

    monkeypatch.setattr(fd.subprocess, "run", lambda *a, **k: R())
    assert fd.git_tree_sha256("repo") == fd.hashlib.sha256(listing).hexdigest()


def test_plan_downloads_nothing(tmp_path, capsys):
    dest = tmp_path / "nowhere"
    assert fd.main(["plan", "--dest", str(dest), "--set", "recommended"]) == 0
    assert not dest.exists()
    assert "nothing was downloaded" in capsys.readouterr().out


def test_safe_name():
    assert fd.safe_name("https://pspdev.github.io/docs/psptek/") == "pspdev.github.io_docs_psptek.html"
    assert fd.safe_name("https://pspdev.github.io/a.htm") == "pspdev.github.io_a.htm"


def test_denied_hosts_never_requested():
    assert fd.denied("https://www.psdevwiki.com/ps2/Main_Page")
    assert not fd.denied("https://pspdev.github.io/")
    with pytest.raises(SystemExit):
        fd.http_get("https://www.psdevwiki.com/psp/")
    for e in fd.CATALOGUE:
        if fd.denied(e["url"]):
            assert e["kind"] == "online", e["id"]
