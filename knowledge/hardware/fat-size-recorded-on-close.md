# The file size is recorded on close

- **Category:** hardware
- **Summary:** A log that is only flushed stays empty after a crash: open, append, write and close on every commit.
- **Applies to:** PSP memory stick file system
- **Evidence:** real PSP-3000
- **Status:** confirmed

## Situation

After a crash the log file existed with 0 bytes, although it had been flushed many times.

## Cause

The memory stick's file system records a file's size when the file is closed; data written and flushed into an open
file is lost from view if the console crashes or switches off.

## Rule

Every log commit opens the file for append, writes and closes. During boot commit every line at once, so the last
line names the step that crashed. In the main loop buffer the lines and commit them from another thread (spikes).
Crash-safe saves: write a temporary file, close it, then rename it into place.

## Evidence

Real PSP-3000: a 0-byte log after a crash with flush-only logging; complete logs after switching to
open-append-close.

## Related

[Log writes and disc reads as spikes](hitches-log-and-disc.md), [Verify the log you read](../workflow/log-path-verification.md)
