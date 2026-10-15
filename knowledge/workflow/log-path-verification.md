# Verify the log you read

- **Category:** workflow
- **Summary:** Before analysing a log, prove it is the run of the build you deployed: build number, run sequence, folder.
- **Applies to:** every hardware test
- **Evidence:** real PSP-3000 test rounds
- **Status:** confirmed

## Situation

Conclusions drawn from a log that belonged to another build, another folder or the previous run.

## Cause

Logs rotate (`session.log` becomes `session_prev.log`), thin test folders read their game data from another folder
but write logs next to their own EBOOT, and several folders of an A/B set look alike. An analysis script also misread
a changed log line and computed frame rates 1.2 times too high.

## Rule

- Every build handed to the user gets a new build number, shown in the XMB title, the log header and on screen.
- The log header carries build number, translation tag, model, firmware and clocks; each run writes a run sequence
  number, the PSP clock time and the battery state.
- Archive logs with the folder name and build number in the file name.
- Before reading: check `build=` and the run line; analysis tools parse explicit fields, never positions in a line.

## Evidence

Real PSP-3000 test rounds: a compare script read 50 Hz logs as 60 Hz after a log text change; folders of an A/B set
were run in any order and identified only by their run sequence numbers.

## Related

skills/psp-build-test section 4, [File size recorded on close](../hardware/fat-size-recorded-on-close.md)
