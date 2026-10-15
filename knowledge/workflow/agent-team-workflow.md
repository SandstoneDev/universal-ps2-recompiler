# Working with several agents: a lead session, specialised agents, reports with a resume point, gates

- **Category:** workflow
- **Summary:** One lead session owns the plan, shared files and the memory stick; each specialised agent owns named paths, writes a report with a WORK IN PROGRESS section, keeps backups, builds in its own folders and proves results with the gates before anything counts.
- **Applies to:** long ports driven by AI coding agents, alone or several in parallel
- **Evidence:** the reference port: about 70 agent tasks over weeks, with pauses and resumes
- **Status:** confirmed

## Situation

A port runs for weeks, through usage limits, parallel experiments and restarts. Work got lost when two agents
edited the same file, when a stale object was linked, or when a session ended mid-edit.

## Cause

Shared files without an owner, builds that share output folders, results claimed without a gate, and no written
resume point.

## Rule

- **Lead session**: owns the plan, the board of who owns what, shared headers, the memory stick and every deploy.
  Agents never deploy, never push, never touch the memory stick.
- **One agent per topic** (translator back-end, GE 3D, audio, memory, measuring, ...), each with the paths it may
  change, its own build and package folders, and a report file whose first section is WORK IN PROGRESS: what is done,
  what is half done, the exact resume step.
- **Backups**: copy a shared file with its md5 before editing it; record the md5 in the report.
- **Gates before a result counts**: (1) host deterministic gate - main loop at a fixed virtual time and frame, error
  counters zero, two runs guest-identical; (2) PPSSPP boolean - boots to the main loop; (3) the data-free test suite;
  (4) for speed, a hardware A/B with a control and a control-again (or the one-run interleaved A/B).
- **Pause safely**: on a stop request each agent finishes or rolls back its edit, leaves the tree building and
  updates its WORK IN PROGRESS; the lead writes one resume document.
- **Stale builds**: a copy that keeps older objects can link yesterday's code; grep the binary for a new log string
  or clean the object folder.
- **One numbered build per deploy**: the build number is in the menu title, the log header and on screen; logs are
  archived before old folders are deleted; two logs kept per folder.

## Evidence

Reference port: parallel agents on separate topics delivered most levers listed in this knowledge base; regressions
were caught by the host gate (counter or virtual-time change) before any hardware run; two stale-object incidents
were found by grepping the EBOOT for a new string.

## Related

[Verify the log you read](log-path-verification.md), [Deploy with md5](deploy-md5-verify.md),
[One-run interleaved A/B](one-run-interleaved-ab.md), skills/ps2rc-port
