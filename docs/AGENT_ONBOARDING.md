# Agent onboarding: the questions to ask before porting

An agent that ports a game with this kit (on top of PS2RC, the recompiler engine it downloads) goes through these
questions **before it does anything else**: no installs, no downloads, no builds, no reading of the disc image, no
memory-stick access. The only thing allowed before the answers is `python -m uprkit doctor`, which reads the machine
and downloads nothing. Ask in small
groups (one section at a time), in the user's language, and say why a question matters when the user asks. "I don't
know" is a valid answer: then use the default given below, find out together, or record Unknown. Record every answer
in `PORT_STATE.md` in the workspace's `work/` folder (template: `skills/ps2rc-port/port-state-template.md`), never in a
repository. Nothing in this kit knows a path of the user's machine: every folder below is asked, with a default.

Each question has **Why** (what changes with the answer) and **Default** (what to do if it stays unanswered). A
default of **stop** means: do not continue past this point without an answer.

## A. Working together

1. **Which language do you want me to use with you?**
   Why: every question, report and test instruction is in that language; files in the kit and the packs stay English ASCII.
   Default: the language of the user's first message.

## B. The game and the disc

2. **Which game?** (the title in your own words)
   Why: chooses the pack, the engine category and the knowledge notes that apply. The title stays in the private
   state file and never goes into anything public.
   Default: stop.
3. **Do you own this disc, and did you make the image yourself from it?**
   Why: the project works only from the user's own disc (Model A below). If the image came from someone else or
   from the internet, stop, explain, and do not help obtain one.
   Default: stop.
4. **Where is the disc image (or the extracted disc folder) on this PC?**
   Why: the only game input. Do not search the disk for it; ask.
   Default: stop before phase 2.
5. **Region and version, if you know them** (PAL / NTSC-U / NTSC-J, a later revision or budget re-release).
   Why: a different revision is different code - addresses, hooks and sizes change, so a pack is keyed by serial and
   version. The video mode decides the pacing: a PAL game run with 60 Hz timing ran 25 % too fast or too slow in the
   reference port until its 50 Hz constants were honoured. After the questionnaire, confirm serial, version and
   video mode from the image's `SYSTEM.CNF` and hash the boot program (`skills/ps2-recon/SKILL.md`); tell the user.
   Default: read it from `SYSTEM.CNF` in phase 2.
6. **Is there already a game pack for this game and version?** (PS2RC's `games/` after the setup, or a pack the user
   has from a source they trust)
   Why: with a pack the port is a conversion of minutes to hours; without one it is research of weeks to months. If
   PS2RC already ships a pack for this exact disc (today: one reserved game), the user converts their copy with PS2RC
   itself (its converter release or `python -m ps2rc.convert`) - no new pack is made.
   Default: assume no pack.

## C. The legal model (read it to the user)

7. **Do you agree to the model: your own disc, everything made from the game stays on your PC?**
   The model: the toolkit is generic; the user converts their own legally obtained copy on their own PC; nothing
   made from the game (disc files, generated C, objects, EBOOTs, converted movies or textures, modules generated from
   the game, listings of its code) is ever published, uploaded, sent or committed - not to a fork, not to an issue,
   not to one friend. Game titles, logos and cover art stay out of public artefacts.
   Also read: PS2RC's licence (PS2RC License 1.0, the same for this kit) is free of charge, asks forks and shared
   packs to carry the credit block, and lets SandstoneDev reserve a game (a `RESERVED.md`): nobody else makes,
   modifies or publishes a pack, build or conversion tool for a reserved game. A reserved pack may be read as an
   example of structure, never copied.
   Why: it is the only way this project works; `skills/legal-guard/SKILL.md` checks it before anything leaves the PC.
   This is not legal advice.
   Default: stop.
8. **Do you plan to share anything?** (toolkit fixes, game-neutral field notes, a pack of game-neutral data)
   Why: sharing goes through `skills/legal-guard/SKILL.md` and the user's explicit decision every time.
   Default: nothing leaves the PC.

## D. The PSP

9. **Which PSP model?** (the label under the battery, or System Settings > System Information)
   Why: the runtime needs the 64 MB models. Known state:
   - PSP-2000 and PSP-3000: supported; the reference port runs on a PSP-3000.
   - PSP-1000 (32 MB): not supported.
   - PSP Go (N1000) and PSP Street (E1000): Unknown (not tested).
   - PS Vita / PS TV with Adrenaline: Unknown, not supported yet (the large-memory mode, the kernel helper module and
     the Media Engine are untested there; a test build produced no log at all).
   Default: stop before phase 7.
10. **Does it run homebrew, and with which custom firmware and version?** (as its own menu or the system information
    shows it)
    Why: the runtime loads a kernel-mode helper module, uses kubridge, needs the large-memory mode and changes the
    clock only through the custom firmware's own interface. Do not install or change custom firmware for the user,
    and do not link to any.
    Default: Unknown; stop before phase 7.
11. **Is the extra-memory (64 MB) mode enabled in the firmware's settings?**
    Why: about 52 MB of user memory in that mode versus about 24 MB without it. The EBOOT's memory-size flag is only
    a request: one firmware honours it only when its own high-memory setting is not off, and it read its settings
    from internal flash instead of the memory stick when the stick mounted slowly (a damaged FAT), silently giving
    24 MB. The runtime checks free memory at start and exits with a message instead of crashing.
    Default: Unknown; check it on the first hardware run.
12. **Memory stick: size, free space, adapter type, and has it ever been unplugged during a copy?**
    Why: a port's folder with game data takes several GB; interrupted USB copies damaged a FAT once (repair it on the
    PC before deploying).
    Default: ask again before the first deploy.
13. **How does the PSP connect to this PC** (USB cable in USB mode, or a card reader), **and what is its drive or
    mount point?**
    Why: deploys copy file by file and verify every file by md5, because the PSP's USB link drops mid-write.
    Default: the user copies the folder by hand.
14. **Do you want to try a higher CPU clock later?**
    Why: the stock maximum is 333 MHz. 365 MHz gave about 9 % more frame rate on one PSP-3000, set only through the
    custom firmware's own clock interface at the very start, with a crash-safe fallback. Raw clock-register writes
    switched a console off. Unknown on other consoles.
    Default: 333 MHz, no overclock.

## E. This PC

15. **Operating system?** Windows (the PSP build runs natively with the bundled toolchain or in WSL2), Linux, macOS
    (host build Unknown: the host harness is written for x86-64 Linux).
    Why: decides the build shell and the doctor checks.
    Default: detect it, then confirm.
16. **What is installed?** Confirm with `python -m uprkit doctor` now and PS2RC's `python -m ps2rc doctor` after the
    setup (both read no game data and download nothing; `docs/DEPENDENCIES.md` lists the official source of each item):
    - Python 3.11 or newer, `pyelftools`, `pytest`, git (required);
    - the pspdev toolchain (psp-gcc 9 or newer; native or in WSL2), a native gcc, make and zlib headers (builds);
    - ffmpeg (movies, animated menu icon - optional);
    - PPSSPP (boolean checks - optional, recommended);
    - PCSX2 with a BIOS dumped from the user's own PS2 (reference runs - optional, needed for hard bugs);
    - an interactive disassembler of the user's choice (optional); a library signature database the user supplies.
    Why: what is missing decides the next installs - each one only with consent.
    Default: whatever doctor finds; ask before each install.
17. **Where should the workspace be, and how much disk space may it use?** (`skills/setup-ps2rc/SKILL.md`)
    Why: the workspace holds PS2RC, the user's packs and `work/` with everything made from the disc; plan at least
    10 GB per game plus the image. The path must be ASCII without spaces and outside every git repository.
    Default: the folder `setup_ps2rc.py setup --dry-run` proposes (`ps2rc-workspace` in the home folder, or at the top
    of the system drive when the home path has spaces or non-ASCII characters); confirm before creating it.
17a. **Which PS2RC version?**
    Why: the kit is checked against the releases pinned in `skills/setup-ps2rc/ps2rc.lock.json`; another version may
    not match the skills and notes.
    Default: the pinned default (`setup_ps2rc.py status` shows it); a newer unpinned tag only on the user's explicit
    choice.
17b. **May I download PS2RC now (about 2 MB), and on Windows the prebuilt converter with its PSP toolchain and ffmpeg
    (about 104 MB zip, 263 MB unpacked)?**
    Why: the kit contains no engine. The converter is the easiest toolchain on Windows; the build scripts additionally
    need WSL with pspdev (`docs/DEPENDENCIES.md`). Everything is checked against the pinned SHA-256 before use.
    Default: PS2RC yes after this answer; the converter only on a yes.
18. **How many CPU cores and how much RAM may the tools use?**
    Why: translation and compilation run in parallel; each compiler job needs several hundred MB.
    Default: half the cores, at most one job per 700 MB of free RAM.

## F. Reference documents

19. **Where should public reference documents be saved, and which sets?** (`skills/fetch-docs/SKILL.md`)
    Why: neither this kit nor PS2RC ships PS2 or PSP manuals; the agent fetches public sources (open SDKs, emulator sources,
    hardware notes) onto this PC and records each one in an index with its URL, date, licence and SHA-256. The
    recommended set is about 100 MB; emulator sources add about 1 GB.
    Default: `refdocs/` inside the workspace, the recommended set, after the user confirms the size.
20. **Do you have other documentation of your own** (books, manuals you legally obtained)?
    Why: the agent may read them where they are, if the user wants. It never downloads, copies into the repository,
    quotes or publishes them, and never cites them in public text.
    Default: none.

## G. The goal

21. **What do you want?** A boot test (does it start on the PC host and on the PSP), playable (menus, controls,
    sound, saving), as fast as possible, or work on a game that already runs.
    Why: sets the phases and how far to go before asking again.
    Default: boot test first, then ask.
22. **What matters most if not everything fits?** (frame rate, draw distance, number of characters and vehicles,
    movies, sound quality, loading times)
    Why: the biggest speed levers change the game (density halving saved about 19 ms per frame in the reference port);
    they are the user's choice and become run options that default to the original behaviour.
    Default: original behaviour, levers off.
23. **Which extras do you want?** (a settings file on the memory stick, own menu icon and music, movies, overclock
    option, controls remapping)
    Why: each is work and some cost memory.
    Default: none beyond what the pack already has.

## H. Testing on the PSP

24. **Who copies builds to the memory stick, and who runs them?**
    Why: the user always runs the PSP. If the agent copies: only the agreed folder, md5-verified, never other
    folders.
    Default: the user copies and runs; the agent prepares folders and numbered test steps.
25. **How do you want to test speed?**
    - one-run A/B: one folder, up to four variants switched inside one run in a random block order, a verdict with a
      confidence interval on screen and in a results file (about 5 minutes per verdict);
    - folder sets: one folder per variant plus a control and a control-again (3 to 5 minutes per folder).
    Why: hardware numbers are the only speed numbers; the method decides how folders and logs are prepared.
    Default: one-run A/B for options that can switch at run time, folder sets for everything else.
26. **How often and how long can you test, and how do logs come back?** (you copy `session.log` from the game's
    folder, or you allow the agent to read it from the stick)
    Default: the user copies the logs.

## I. Permissions (standing answers, recorded in the state file)

27. May the agent, without asking each time:
    - run long steps (translation 2 to 5 minutes, a full PSP build several minutes to a quarter of an hour, host
      runs);
    - start emulators (PPSSPP, PCSX2) - they open windows and take keyboard focus;
    - write to the memory stick (only the agreed folder, md5-verified);
    - download public reference documents into the agreed folder (`skills/fetch-docs/SKILL.md`);
    - update PS2RC to a newer pinned release (`setup_ps2rc.py update`; default: ask each time);
    - download or install packages, toolchains or images (default: ask each time);
    - make local git commits in the user's fork (pushing and publishing: always ask).
    Default: ask each time for every item.

## J. Expectations (say this before starting)

28. Tell the user plainly:
    - the first boot of a new game on the PC takes days to weeks of analysis and HLE work; a playable PSP build
      weeks to months; much of it is per-game work (the renderer boundary, the sound driver, fitting into memory);
    - speed, measured on the reference port (a large open-world 3D game) on a PSP-3000 at 333 MHz: about 30 fps
      indoors and 17 to 21 fps outdoors, after months of tuning and with the user's choice of density and draw
      distance; about 9 % more at 365 MHz. The PSP's CPU is the limit; a game that does less work per frame does
      better, a heavier one worse;
    - some games may not be portable without research (self-modifying code, heavy VU1 use, more memory than the
      PSP has);
    - nothing made from the game may be shared, ever, also not with friends.

    Ask: **"Do you want to continue on these terms?"** Start only on a clear yes.
