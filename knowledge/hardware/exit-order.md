# Exit order

- **Category:** hardware
- **Summary:** Leave the game in a fixed order: audio and Media Engine, GE, counters, kernel module, then exit; log each step first.
- **Applies to:** PSP-2000/3000 with a kernel helper module, the Media Engine and the GE in use
- **Evidence:** real PSP-3000
- **Status:** partly confirmed

## Situation

The console switched off after `sceKernelExitGame` in some sessions; HOME and Exit did nothing in an early build.

## Cause

Threads, callbacks and handlers that point into the program's or the module's code were still active while that code
was released. A plain test program also switched off once, so part of the cause is Unknown.

## Rule

- Register the exit callback right at start, on a thread with a higher priority than the game thread.
- Exit sequence, each step committing a log line first: stop audio and any Media Engine loop; finish the open GE list
  (wait briefly, else break it) and terminate the GU library; stop the counter thread and check it returned; restore
  hardware registers; stop and unload the kernel module and verify; then exit the game.
- A successful unload returns the module id: do not log it as a failure.

## Evidence

Real PSP-3000: power-off after exit in 2 of 5 sessions with hardware counters on; a dedicated exit test was clean
after the ordered sequence with the register restore.

## Related

[Kernel module must export module_stop](kernel-module-export-module-stop.md), [Media Engine rules](media-engine-rules.md)
