# A kernel module must export module_stop

- **Category:** hardware
- **Summary:** Without an exported module_stop the kernel never runs it; unloading then frees handlers the kernel still uses.
- **Applies to:** PSP kernel-mode PRX built with the homebrew SDK
- **Evidence:** real PSP-3000 (symptom); the fix's verdict is open
- **Status:** partly confirmed

## Situation

The console sometimes switched off after the game exited, although unloading the kernel helper module reported
success.

## Cause

The module was linked with the SDK's default export object, which exports only `module_start` and `module_info`. The
kernel finds the stop entry through the exports, so stopping the module returned success without running anything,
and unloading it freed code the kernel still pointed at (an exception handler, a system-event handler, a replaced
driver handler). Whatever called them later executed freed memory. Whether this was the only cause of the power-off:
Unknown.

## Rule

Give every kernel module an exports file that lists `module_start`, `module_stop` and `module_info`, and make
`module_stop` undo every registration (handlers, hooks, hardware registers). Verify after unloading that the module is
gone (query its info).

## Evidence

Real PSP-3000: intermittent power-off after exit with the default exports. The fixed module lists its exports in
`psp_exc/exports.exp`; a hardware A/B verdict is still open.

## Related

`psp_exc/exports.exp`, [Exit order](exit-order.md)
