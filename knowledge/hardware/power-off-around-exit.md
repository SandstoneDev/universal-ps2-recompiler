# Power-offs around exit are kernel hangs: fix what you can, measure with five runs per arm

- **Category:** hardware
- **Summary:** A PSP that switches itself off is usually a kernel hang the watchdog ends; remove the known causes (handlers over freed memory, automatic exits, clock writes) and judge exit fixes over at least five runs per variant.
- **Applies to:** PSP-2000/3000 with a kernel helper module, Media Engine takeover, overclock
- **Evidence:** real PSP-3000, about 40-50 exits logged
- **Status:** partly confirmed (a residual rate remains, cause Unknown)

## Situation

After the Media Engine takeover about one exit in ten switched the console off, always after the last logged exit
step, during the reboot into the system menu.

## Cause

"Power-off" means interrupts stayed off or a wait never returned, the watchdog stopped being fed and the power
controller cut power. Known causes found: a kernel module unloaded without an exported `module_stop` left exception and
sleep-event handlers registered over freed memory; an automatic exit call in a test harness switched a console off;
own clock-register writes. A plain test program without the ME or the module also powered off once, so a part of the
rate may belong to the console itself (Unknown).

## Rule

- Export `module_stop` and undo every registration there; or keep the module loaded until the reboot and give the
  exception handler back first.
- Follow a fixed exit order and log each step before taking it ([Exit order](exit-order.md)).
- Test programs wait for a button before exiting; never exit automatically.
- Hold the power lock (taken with the volatile memory) until the reboot.
- With a 10-30 % fault rate, one to three runs per variant separate nothing: use at least five per arm.

## Evidence

PSP-3000: 5 power-offs in about 40-50 exits after the ME takeover (about 10-12 %), all on mains power, all after the
last exit step. The robust exit mode removed a real defect (0 sleep events seen during exit, by a marker in ME RAM)
but not every power-off.

## Related

[Kernel module must export module_stop](kernel-module-export-module-stop.md), [Media Engine rules](media-engine-rules.md),
[Overclock](overclock-cfw-api-only.md)
