# Notices

universal-ps2-recompiler is under the PS2RC License (`LICENSE`). It contains no third-party code and no game data.

## PS2RC (downloaded, not included)

The engine, PS2RC (https://github.com/SandstoneDev/PS2RC), is downloaded onto the user's machine by
`skills/setup-ps2rc/setup_ps2rc.py`; it is not part of this repository. It comes with its own `LICENSE` (the same
PS2RC License) and `NOTICE.md` (the third-party code inside it, and the licences of its converter release:
the PSP toolchain, ffmpeg, Qt, atracdenc). Read them in the downloaded checkout.

## Tools and documents named here

`docs/DEPENDENCIES.md` and `skills/fetch-docs/SKILL.md` name tools and public documents by their official URLs.
Nothing of them is included: the user downloads them on their own machine, under their own licences, after the agent
asks.

## Agent kit

The agent instructions (`AGENTS.md`, `skills/`, `knowledge/`) adapt ideas from the agent skill
**ps2-recomp-Agent-SKILL** (MIT License; written for the PS2Recomp PC project): a decision router table that sends
the agent to the right document, a circuit breaker after three identical failures, operational phases with entry and
exit criteria, a reasoning loop for diagnosis, reference-run comparison against PCSX2, and a topic index of reference
notes. The text here is our own; no text, manuals or images of that skill are included. We credit it because its
ideas shaped ours.

The repository pattern (one `AGENTS.md` with thin per-agent pointers, `skills/` in the Agent Skills format with copies
for each agent, a `knowledge/` base of field notes with a template and an index, an onboarding step before any work)
follows the open-source project universal-modder (https://github.com/rehan-remade/universal-modder).
