---
name: ps2-recon
description: "Identify and survey a PS2 game from the user's own disc image before porting it with PS2RC (through this kit): read SYSTEM.CNF (serial, version, video mode, boot program), hash the boot ELF, find code overlays, list IOP modules, find VU microcode, name Sony library functions with a user-supplied signature database, detect the engine or middleware category, and give the user an honest estimate. Use after onboarding when the user points at a disc image or disc folder, or asks 'can this game be ported', 'what is on this disc', 'which version is my disc'."
---

# Recon: what is on the user's disc

Everything here reads the user's own disc image on the user's machine. Outputs go to the work directory, never into
the repository. Never ask the user to send you files, and never fetch a disc, BIOS or file from anywhere.

## 1. Identify (read, do not guess)

1. Open the image or the extracted folder. The converter's reader works on both and prints the identity:
   `python -m ps2rc.convert <image or folder> --out <work dir>/convert --estimate`. Without a pack for the game it
   stops with "no game pack for ..." and names the serial, the boot program and the version: that is the identity.
   In Python: `from ps2rc.convert import disc; d = disc.open_disc(path); d.system_cnf()`.
2. `SYSTEM.CNF`: `BOOT2` names the boot program (its file name is the serial, e.g. `SLUS_123.45`), `VER` the revision,
   `VMODE` the video mode (PAL 50 Hz or NTSC 60 Hz - the VBlank rate drives the game's clock; get it right on day one).
3. Size and SHA-256 of the boot program: they identify the version for the pack's `[verify]` table. They never prove
   ownership - ownership is the user's statement in the questionnaire.
4. A different revision of the same game is a different pack. Tell the user which revision they have.

Record serial, version, region, video mode, boot program, size and hash in `PORT_STATE.md`.

## 2. Survey the program

The analysis tools take the boot program (extracted to the work directory) as an argument:

| Tool | Answers |
|---|---|
| `tools/ps2elf/census.py BOOT [OVERLAYS...] --out DIR` | where the code is; which R5900 instructions, syscalls and COP0 operations it uses |
| `ps2rc/image.py` (library) | loadable segments, BSS, `$gp`, symbols and relocations when present, overlay slots |
| `ps2rc/overlay.py` (library) | Metrowerks overlays (`MWo3` header) and whether each fits its slot |
| `tools/ps2elf/find_vu.py BOOT` | VU microcode inside the program (VIF MPG packets, raw microcode runs) |
| `tools/ps2elf/vu_programs.py`, `tools/ps2elf/vudis.py` | which VU programs are uploaded and what they do |
| `tools/ps2elf/sce_sigscan.py BOOT DB` | which functions are Sony library functions (needs a signature database) |
| `python -m ps2rc.iop info|list MODULE.IRX` | the IOP modules: imports, exports, whether the recompiler accepts them |

What to look for and write down:

- **Code range, data end, BSS end** (the pack's `[memory]`), and whether the program was stripped.
- **Overlays**: loadable segments without file data that share one address. An overlay's static constructors can sit
  after its `.text`; an overlay built for another revision looks plausible and is wrong. Another overlay scheme than
  `MWo3` needs a new loader (Unknown effort).
- **Self-modifying code**: compare the code region in memory (a PCSX2 run) with the file during boot and play. If the
  game writes code, static translation needs extra work there - tell the user.
- **IOP modules** (IRX files, sometimes packed in a replacement image): Sony's standard modules are covered by the core
  HLE; each custom one (sound, streaming) is an RPC server to translate with the IOP recompiler or model.
- **VU usage**: VU0 macro mode (COP2 in EE code) is translated; VU0 micro programs go through the microcode translator;
  heavy VU1 use means the game's renderer must be replaced at a boundary (hle-authoring) - the largest per-game cost.
- **Instruction mix**: most "exotic" 64/128-bit instructions are compiler idioms; real wide arithmetic is a few
  percent of functions. Only a few dozen functions should touch hardware directly.

## 3. Name the Sony library functions

The repository ships no signature database. The user supplies one (for example a database from an open-source PS2
recompiler project) and checks its licence; set its path in `local.toml` under `[tools] sce_signature_db`. Accept only
matches with enough fixed bits and a single possible name; name call targets from relocations only when every
matching record agrees; cross-check syscall wrappers against the syscall numbers they issue. Those names are what the
pack's hook list binds to the core HLE (game-pack).

## 4. Engine or middleware category

From strings, library names and the render path, decide the category: a known middleware renderer, an in-house
engine, a 2D engine, an FMV-heavy game. Write the category, never a product name, in public notes. Search the
knowledge base first: `python -m uprkit kb search engines <words>` - a category someone already covered is much less
work.

## 5. Checkpoint with the user

Give a short, honest report: identity, size of the program, overlays, IOP modules, VU programs, render path, number of
library functions found, anything unusual (self-modifying code, a second executable, unknown overlay scheme), and the
estimate from `skills/ps2rc-port/SKILL.md` section 7 adjusted by what you found. Ask whether to continue.

## Optional tools

An interactive disassembler of the user's choice helps to read functions and cross references; keep its database
and listings in the work directory: they contain the game's code and are never committed. PCSX2 (with a BIOS dumped
from the user's own console) is the reference for how the original behaves (hle-authoring, "Reference runs").
