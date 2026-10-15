"""The agent kit: skills, knowledge base, AGENTS.md and the pointers (no network, no game data)."""
import os

from uprkit import find_file, kb, repo_root, skills

ROOT = repo_root()


def test_skills_valid():
    assert skills.problems() == []
    names = [n for n, _p, _fm in skills.load()]
    for want in ("ps2rc-port", "setup-ps2rc", "ps2-recon", "ps2rc-translate", "hle-authoring", "psp-build-test", "psp-performance",
                 "game-pack", "legal-guard", "field-notes"):
        assert want in names


def test_frontmatter_parser():
    fm = skills.parse_frontmatter('---\nname: a-b\ndescription: "x: y"\n---\n# T\n')
    assert fm == {"name": "a-b", "description": "x: y"}
    assert skills.parse_frontmatter("# no front matter\n") is None


def test_agents_md_lists_every_skill_and_pointers_exist():
    agents = find_file("AGENTS.md")
    assert agents, "AGENTS.md missing"
    text = open(agents, encoding="utf-8").read()
    for name, _p, _fm in skills.load():
        assert "skills/%s/SKILL.md" % name in text, name
    for f in ("CLAUDE.md", "GEMINI.md"):
        p = find_file(f)
        assert p and "AGENTS.md" in open(p, encoding="utf-8").read()
    for d in ("AGENT_ONBOARDING.md", "WORKSPACE.md", "DEPENDENCIES.md"):
        assert find_file(os.path.join("docs", d)), d


def test_knowledge_base_consistent():
    assert kb.notes(), "no knowledge notes"
    assert kb.problems() == []


def test_skills_sync_to_tmp(tmp_path):
    t = tmp_path / "agent" / "skills"
    (t / "user-own").mkdir(parents=True)
    (t / "user-own" / "SKILL.md").write_text("---\nname: user-own\ndescription: x\n---\n", encoding="utf-8")
    skills.sync([str(t)], say=lambda s: None)
    assert skills.stale(str(t)) == []
    assert (t / ".gitignore").read_text(encoding="utf-8").strip().endswith("*")
    assert (t / "user-own" / "SKILL.md").exists()            # a skill sync did not make is kept
    skills.sync([str(t)], say=lambda s: None)                  # idempotent
    assert skills.stale(str(t)) == []


def test_uprkit_cli_help_and_unknown(capsys):
    from uprkit.__main__ import main
    assert main(["--help"]) == 0
    assert "setup" in capsys.readouterr().out
    assert main(["no-such-command"]) == 2


def test_readme_carries_credit_and_licence():
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for s in ("Based on PS2RC by SandstoneDev", "https://github.com/SandstoneDev/PS2RC", "https://discord.gg/wV8x46ZTDu",
              "not affiliated", "No game data"):
        assert s in readme, s
    lic = open(os.path.join(ROOT, "LICENSE"), encoding="utf-8").read()
    assert lic.startswith("PS2RC License, version 1.1")
