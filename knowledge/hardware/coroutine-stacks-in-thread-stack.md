# Coroutine stacks must live inside the PSP thread's own stack

- **Category:** hardware
- **Summary:** Guest threads run as coroutines; their stacks must be carved from the stack of the PSP thread that runs them.
- **Applies to:** PSP-2000/3000, any runtime that switches stacks inside one kernel thread
- **Evidence:** real PSP-3000; PPSSPP did not show it
- **Status:** confirmed

## Situation

The log stopped at the first file-system call made from a coroutine, and the console switched itself off. The same
build ran without complaint in PPSSPP.

## Cause

The coroutine stacks were allocated as a separate memory block. The PSP kernel kills a thread whose stack pointer is
outside its registered stack; it was observed around system calls. The exact kernel check is Unknown.

## Rule

Create one PSP thread with a large stack and carve every coroutine stack from its bottom. Check the real stack size
with `sceKernelReferThreadStatus` and log whether the stack pointer is inside it at each switch. Keep a small test
program for exactly this case.

## Evidence

Real PSP-3000: power-off at the first `sceIo` call from a coroutine with stacks elsewhere; fixed by a 256 KB own
stack plus a pool (1 MB main coroutine, 10 x 256 KB). Measured high-water marks were 5 KB of 1 MB and 3 KB of 256 KB,
so the pool can shrink. PPSSPP accepted the broken layout.

## Related

`hle/psp/hle_ctx.S`, `hle/psp/hle_psp.c`, [PPSSPP gives booleans](../workflow/ppsspp-booleans-hardware-numbers.md)
