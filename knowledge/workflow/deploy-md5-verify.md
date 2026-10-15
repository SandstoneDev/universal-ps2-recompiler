# Copy to the memory stick file by file and verify md5

- **Category:** workflow
- **Summary:** The PSP's USB link drops mid-write: copy file by file, hash every file on both sides, verify again at the end.
- **Applies to:** PSP connected over USB as a mass-storage device
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

A build failed strangely on the PSP; the EBOOT on the memory stick was shorter than the one on the PC, although the
copy had reported success.

## Cause

The USB link between the PC and the PSP dropped in the middle of writes several times; a copy tool does not always
notice.

## Rule

- Archive the old folder's logs to the PC before deleting anything.
- Copy file by file; hash each copied file and compare with the source; retry a few times; at the end hash the whole
  folder again.
- Never make large card-to-card copies; never touch folders that are not yours.
- Only with the user's consent, into the folder the user agreed to.
- Eject safely. After an interrupted copy, check and repair the stick's file system on the PC before the next run:
  a damaged FAT mounted slowly, and the custom firmware then read its settings from internal flash (extended memory
  off) - see [The 64 MB mode is a request](../hardware/large-memory-mode-check.md).
- Each test folder gets a distinct menu title (short, with the build number) and stays thin (EBOOT, settings file,
  kernel module) pointing to one shared data folder.

## Evidence

Real PSP-3000: several dropped transfers; once a truncated EBOOT, once a file whose md5 differed on the final
re-read after a per-file "OK". Interrupted copies left a broken folder and 150 lost chains on one stick. `tools/dev/card_sync.ps1` (Windows)
does the per-file md5 copy with retries.

## Related

`tools/dev/card_sync.ps1`, skills/psp-build-test section 4
