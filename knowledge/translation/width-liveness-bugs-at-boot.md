# Width and liveness bugs show only when the game boots

- **Category:** translation
- **Summary:** Narrowing and liveness must be whole-program and run to a fixpoint; syscalls, HLE calls, tail calls and hooks read more than the guest body shows.
- **Applies to:** width analysis, argument and return liveness, hooks
- **Evidence:** PC host boot of the reference game (each bug was a difference between an exact and a narrowed translation of one function)
- **Status:** confirmed

## Situation

Unit tests and bit-exact vectors passed, yet the booted game started a thread at string bytes, put every placed
object at the origin, and looped its loading screen forever.

## Cause

- A syscall reads a0-a3, t0-t3 and v1; liveness that ignored this dropped an argument.
- An HLE call that writes the guest context (for example a COP0 read) needs a reload afterwards.
- A 64-bit value passed through tail calls must stay wide: a narrowed double return lost its high word; a 64-bit
  timer wrapped at 2^32.
- Overlay static constructors were never translated.
- Stopping the argument fixpoint after 3 rounds was unsound: 1,443 functions got different sets.
- A hooked function's C replacement may read arguments the guest body never reads.

## Rule

- Width facts per argument register over the whole program (least fixpoint), across overlays in both directions.
- Run every fixpoint to convergence.
- Hooked functions get full argument liveness and no one-word write-backs; translate again when the hook list
  changes.
- When a booted run diverges, translate the suspect function exact and compare; bisect by function.

## Evidence

Host: four defects of this kind, each found as "exact version works, narrowed one does not" inside one function. The
whole-program width fix cost +0.54 % code. 41 main-program functions needed width facts from overlays.

## Related

[Boot to the first blocker](boot-to-first-blocker.md), [Reference runs](../hle/reference-run-first-divergence.md),
[Translator levers](backend-levers-measured.md)
