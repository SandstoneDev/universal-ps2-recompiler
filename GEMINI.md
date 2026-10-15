# GEMINI.md

Read and follow [AGENTS.md](AGENTS.md): it is the single set of instructions for every coding agent in this
repository.

- First step of any port: the onboarding questionnaire in [docs/AGENT_ONBOARDING.md](docs/AGENT_ONBOARDING.md).
- This kit downloads the engine, PS2RC, into a workspace the user chooses: `skills/setup-ps2rc/SKILL.md`.
- The skills are in `skills/` (start with `skills/ps2rc-port/SKILL.md`); `python -m uprkit skills sync` also copies them
  to `.agents/skills` (git-ignored copies; edit only `skills/`).
- Nothing made from the user's game is ever committed, pushed or uploaded; nothing is ever made for a reserved game.
