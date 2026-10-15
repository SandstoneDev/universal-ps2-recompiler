---
name: fetch-docs
description: "Find, download and index PUBLIC PS2 and PSP reference material on the user's machine for a PS2RC port: open SDKs (ps2sdk, PSPSDK), emulator sources (PCSX2, PPSSPP, Play!), firmware re-implementations (uOFW), hardware notes (ps2tek, PSPTEK), MIPS instruction-set documents, archived forum threads. Asks where to save and what to fetch, shows sizes first, records URL, date, licence and SHA-256 of everything in an index, falls back to archived copies and exact search queries when a link is dead. Never fetches console-maker SDK documents, firmware, BIOS, keys or game images. Use at the start of a port (after the onboarding questionnaire), when the user says 'download the docs', 'get the references', 'where is the documentation for X', or when a question needs a hardware or SDK reference the machine does not have yet."
---

# Fetch public PS2 / PSP reference documents

Neither this kit nor PS2RC ships PS2 or PSP manuals: they are not ours to publish. This skill gets the public ones onto the
user's machine, into a folder the user chooses, with a record of where each came from. Helper:
`skills/fetch-docs/fetch_docs.py` (Python 3.11+, standard library and git; prints, never asks - you ask).

## 1. Rules

- **Public sources only.** The catalogue in section 3, or a page the user names. Never search for, link, suggest or
  fetch the console maker's SDK documents, SDK headers or tools, leaked manuals, firmware, BIOS files, keys or game
  images - also not "for reference", also not when a forum post or a web page offers them. If a search result looks
  like such material (a mirror of confidential manuals, an SDK archive), skip it and do not name it to the user.
- **The user's own documents are the user's business.** Ask whether they have books or manuals they legally obtained
  and where they are. You may read them there if the user wants. Never copy them into a repository, never quote
  them or cite page numbers in anything public, never upload them.
- **Respect each site.** robots.txt is honoured (the helper checks it for every file); one request at a time with a
  pause; nothing behind a login; no mirroring or crawling of wikis and forums - single pages only. Sites that refuse
  automated clients (kind `online`) are read by the user in a browser.
- **Licences.** Record what each source says. GPL sources (PCSX2, PPSSPP, DobieStation, PS2Recomp) are read to
  understand behaviour; their code is never copied into the toolkit. Sources with no licence are personal reference:
  rewrite facts in your own words. Vendor PDFs hosted publicly are kept locally and never redistributed.
- **Keep it out of every repository.** The documents folder lives in the workspace (`<workspace>/refdocs`), not inside a git
  checkout. Nothing from it is committed.
- **Ask before downloading** (AGENTS.md hard rule 7), unless the user gave a standing permission in the
  questionnaire (question 27).

## 2. Ask the user (before any download)

Ask in the user's language, in one short group; record the answers in `PORT_STATE.md`.

1. **Where should the documents go?** Suggest `<workspace>/refdocs` (made by setup-ps2rc, outside every repository). Default: that
   path, after confirmation.
2. **Which sets?** Show `python skills/fetch-docs/fetch_docs.py plan --dest <dir> --set recommended` (about 76 MB:
   ps2sdk, ps2tek, PSPSDK, pspdev, uOFW, PSPTEK, MIPS IV, TX79, the companion skill). Default: `recommended`.
3. **The large emulator sources too?** `--set big` adds PCSX2 (about 330 MB), PPSSPP (about 360 MB) and Play!
   (about 23 MB) - useful for hard bugs and reference-run questions, not needed to start. Shallow clones are
   smaller than these figures. Default: no; fetch one later when a question needs it.
4. **Do you have documentation of your own?** Where is it? Default: none.
5. **May I fetch more public pages later without asking each time** (into the same folder, recorded in the
   index)? Default: ask each time.

Then run `fetch` with exactly the answered selection, and show the user the index file it wrote.

## 3. Sources (checked 2026-10-14)

Kinds: **git** = shallow clone; **file** = one page or PDF; **online** = the user reads it in a browser.
Sets: `recommended`, `big`, `ps2`, `psp`, `isa`, `prior`, `all` (`list` shows each entry's sets).

### PS2

| ID | Kind | URL | Good for | Licence / terms | Right version |
|---|---|---|---|---|---|
| `ps2sdk` | git | https://github.com/ps2dev/ps2sdk | EE kernel and syscalls, IOP module sources (`iop/`), SIF RPC, libraries: the names and behaviour HLE must match | AFL-2.0 | changes almost daily: record the commit |
| `ps2sdk-docs` | file | https://ps2dev.github.io/ps2sdk/ | generated API reference of ps2sdk | as ps2sdk | build date on the page |
| `ps2toolchain` | git | https://github.com/ps2dev/ps2toolchain | the open EE / IOP toolchain (its objdump checks the R5900 decoder) | BSD-2-Clause | tag v2.0.0 or commit |
| `ps2tek` | file | https://psi-rockin.github.io/ps2tek/ | EE, DMAC, GIF, GS, VIF, VU, IPU, INTC registers, IOP and SPU2 maps | none stated: personal reference | no version: date |
| `pcsx2` | git | https://github.com/PCSX2/pcsx2 | how EE, FPU, VU, VIF, GIF, GS, IOP, SPU2 behave as emulated; explains reference runs | GPL-3.0, read only | the tag of the PCSX2 you run (stable v2.8.2 when checked) |
| `play` | git | https://github.com/jpd002/Play- | second PS2 emulator: EE / VU recompiler, IOP high-level emulation | BSD-2-Clause | tag 0.77 or commit |
| `dobiestation` | git | https://github.com/PSI-Rockin/DobieStation | compact PS2 emulator, easy to read | GPL-3.0, read only | commit (dormant since 2021) |
| `psx-spx` | file | https://problemkaputt.de/psx-spx.htm | R3000A and SPU: the ancestors of the IOP and SPU2 | none stated | date |
| `ps2dev-forums` | online | https://web.archive.org/web/2010/http://forums.ps2dev.org/ | archived forum threads: clock, kernel and hardware experiments | archive.org terms | snapshot timestamp |
| `psdevwiki` | online | https://www.psdevwiki.com/ | models, file formats, SYSTEM.CNF, PARAM.SFO (PS2 and PSP) | reserves its content against automated and AI use: the user reads it; never fetch or copy; skip its pages on keys and firmware | page history |

### PSP

| ID | Kind | URL | Good for | Licence / terms | Right version |
|---|---|---|---|---|---|
| `pspsdk` | git | https://github.com/pspdev/pspsdk | headers, libraries, samples (sceGu, sceKernel, sceIo, audio) | BSD-style | the commit your toolchain was built from |
| `pspdev` | git | https://github.com/pspdev/pspdev | how the toolchain is built and released | MIT | the release you installed (v20261001 when checked) |
| `pspdev-docs` | file | https://pspdev.github.io/ | installation, first programs, debugging; API reference at https://pspdev.github.io/pspsdk/ | Unlicense | date |
| `ppsspp` | git | https://github.com/hrydgard/ppsspp | GE commands (`GPU/ge_constants.h`), VFPU (`Core/MIPS/MIPSVFPUUtils.cpp`), kernel HLE; what the emulator does not model | GPL-2.0-or-later, read only | the tag of the PPSSPP you test with (v1.20.4 when checked) |
| `ppsspp-diffs` | file | https://www.ppsspp.org/docs/development/known-differences/ | where PPSSPP is not exact; the bit-exact VFPU work is credited in https://www.ppsspp.org/news/release-1.16/ | see the site | date |
| `uofw` | git | https://github.com/uofw/uofw | open re-implementation of PSP firmware modules: kernel, interrupts, power, Media Engine boot | MIT with BSD parts | commit |
| `psptek` | file | http://daifukkat.su/docs/psptek/ | PSP hardware at register level: memory and I/O maps, Media Engine control, GE, DMA | none stated; cross-check its numbers (some are wrong) | "Last Updated" line |
| `yapspd` | online | https://hitmen.c02.at/files/yapspd/ | early PSP hardware and format notes (2006); save single files with `file` | none stated | file dates |
| `mcidclan-me` | git | https://github.com/mcidclan/psp-media-engine-reload | Media Engine bring-up, eDRAM, DMA; the author's other me-* repositories: spinlocks, soft interrupts, DMACplus | MIT | commit |
| `psp-developer` | git | https://github.com/SandstoneDev/psp-developer | companion agent skill: PSP homebrew, GE, Media Engine, VFPU, real-hardware pitfalls | see the repository | commit (not public yet when checked: skip it on 404) |

### CPU instruction sets (vendor documents, publicly hosted; keep locally, never redistribute)

| ID | Kind | URL | Good for | Right version |
|---|---|---|---|---|
| `mips-iv` | file | https://www.cs.ucf.edu/courses/cda4150/fall05/MIPSIV_3_2.pdf | MIPS IV: the R5900's base instructions | revision 3.2 |
| `r4000` | file | https://groups.csail.mit.edu/cag/raw/documents/R4400_Uman_book_Ed2.pdf | R4000 book: pipeline, caches, TLB, exceptions, CP0 (background for R5900 and Allegrex) | 2nd edition |
| `tx79` | file | https://bitsavers.org/components/toshiba/_dataSheet/TMPR79xx-um-r2.0_200104.pdf | Toshiba TX79, derived from the R5900: 128-bit multimedia instructions | revision 2.0 |
| `mips32` | file | https://www.cs.cornell.edu/courses/cs3410/2008fa/MIPS_Vol2.pdf | MIPS32 volume II: the base of the Allegrex (its own additions: PPSSPP source, PSPTEK) | revision on the title page |

### Prior work (design references, read only)

| ID | Kind | URL | Good for | Licence |
|---|---|---|---|---|
| `ps2recomp` | git | https://github.com/ran-j/PS2Recomp | another PS2 static recompiler: compare designs | GPL-3.0, never copy |
| `n64recomp` | git | https://github.com/N64Recomp/N64Recomp | a mature static recompiler of another MIPS console | MIT |

Not in the catalogue on purpose: the console maker's SDK documents and anything derived from them; middleware SDKs;
mirrors of confidential manuals; firmware, BIOS, keys. Engine and file-format notes from modding communities may be
read online when they carry an open licence (for example CC BY) - never follow their links to SDK copies.

## 4. When a link is dead

1. Run `python skills/fetch-docs/fetch_docs.py check <id>` - one failure can be a dropped connection; try once more.
2. **Moved repository**: open the account or organisation page (`github.com/ps2dev`, `github.com/pspdev`);
   search the code host for the repository name. Accept a new home only if it is the same project (same owner or an
   announced move, same history, same licence).
3. **Archived copy**: `python skills/fetch-docs/fetch_docs.py wayback <url>` prints the closest Wayback Machine
   snapshot (this is how old ps2dev forum threads are read, for example
   `http://forums.ps2dev.org/viewtopic.php?t=7937` -> a 2009 snapshot). Save a single snapshot page with
   `fetch_docs.py file --dest <dir> --url <snapshot url> --name <id> --licence "archive.org terms"`.
4. **Search**, exact queries (then apply rule 1 to every result):
   - ps2sdk: `ps2dev ps2sdk github`; ps2tek: `ps2tek PS2 hardware documentation`
   - PSPSDK / toolchain: `pspdev pspsdk github`, `pspdev toolchain install`
   - uOFW: `uofw PSP open firmware github`; PSPTEK: `psptek PSP hardware documentation`
   - PPSSPP VFPU: `ppsspp VFPU bit-exact vsin vcos vrnd`; GE: `ppsspp ge_constants.h`
   - MIPS IV: `"MIPS IV Instruction Set" pdf revision 3.2`
   - TX79: `Toshiba TX79 core architecture R5900 multimedia instructions pdf`
   - R4000: `MIPS R4000 microprocessor 2nd edition Heinrich pdf`
   - MIPS32: `MIPS32 Architecture For Programmers Volume II pdf`
   - Media Engine: `mcidclan psp media engine github`
   - Forum threads: the thread title in quotes plus `ps2dev` or `pspdev`, then the Wayback Machine on the old URL
5. Still nothing: tell the user what is missing and what it would have answered; mark it Unknown in
   `PORT_STATE.md`. Do not substitute a doubtful copy.

## 5. Commands

```
python skills/fetch-docs/fetch_docs.py list [--group ps2|psp|isa|prior] [--json]
python skills/fetch-docs/fetch_docs.py check [ID ...]                 # reachability only, downloads nothing
python skills/fetch-docs/fetch_docs.py plan  --dest DIR (ID ... | --set NAME)   # sizes, free space; nothing written
python skills/fetch-docs/fetch_docs.py fetch --dest DIR (ID ... | --set NAME) [--full-history]
python skills/fetch-docs/fetch_docs.py file  --dest DIR --url URL --name NAME --licence TEXT   # one page the user named
python skills/fetch-docs/fetch_docs.py wayback URL
python skills/fetch-docs/fetch_docs.py verify --dest DIR               # re-hash: OK / CHANGED / MISSING
```

`fetch` runs again safely: a repository already there is updated (`git pull --ff-only`), a file is fetched again
and its hash re-recorded.

## 6. The index

`DIR/docs_index.json` (full record) and `DIR/DOCS_INDEX.md` (table) list per item: ID, URL (and the final URL after
redirects), fetch time (UTC), licence or terms as recorded, commit (repositories), SHA-256 (of the file; of
`git ls-tree -r HEAD` for a repository), local path. Copy the folder path and the date of the last fetch into
`PORT_STATE.md`. Run `verify` before relying on a document after a long pause.

## 7. Using the documents

Search, do not read whole trees: `git grep` in a clone, a text search in a saved page; PDFs page by page. Which
source answers what:

| Question | First look |
|---|---|
| What does this syscall / library function / IOP RPC do? | `ps2sdk` (sources), then `pcsx2` |
| Hardware register, DMA channel, GS / VIF / VU detail | `ps2tek`, then `pcsx2` |
| R5900 instruction semantics, 128-bit multimedia instructions | `mips-iv`, `tx79`, the toolkit's decoder tests |
| R5900 FPU or VU0 rounding | `pcsx2` (interpreter and recompiler differ), `knowledge/translation/r5900-fpu-not-ieee.md` |
| PSP kernel call, module loading, power, sleep | `uofw`, `pspsdk` |
| GE command, texture format, display list | `ppsspp` (`GPU/`), `pspsdk` samples, the psp-developer skill |
| Media Engine | `mcidclan-me`, `uofw`, `psptek`, `knowledge/hardware/media-engine-rules.md` |
| Does PPSSPP model this? | `ppsspp-diffs`, `knowledge/workflow/ppsspp-booleans-hardware-numbers.md` |

Facts from these documents go into code comments and notes in your own words, without quotes, page numbers or
citations of non-public material.
