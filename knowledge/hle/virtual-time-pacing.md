# Virtual time and pacing: follow the real clock, forgive lag

- **Category:** hle
- **Summary:** Advance virtual time by fixed charges, honour the game's video mode and frame limiter, let virtual time follow the real clock while the guest works (forgive lag instead of paying it back), pace the boot in real time, and freeze time during movies.
- **Applies to:** the HLE clock, VBlank delivery, frame limiters, loading screens, movies
- **Evidence:** real PSP-3000 (game-clock ratios, audio drops), PC host simulation
- **Status:** confirmed

## Situation

On the PSP the game ran 20-30 % too fast above its frame cap and in slow motion below it; loading-screen music played
at 5.65x tempo; after a movie the game ran unpaced for about 105 s; a PAL game ran 25 % off speed.

## Cause

- Pacing that only ever waits never forgives lag: the slow boot left virtual time about 30 s behind the real clock,
  so the main loop never waited again.
- The PAL game was given 60 Hz VBlanks (swapped video-mode constants).
- Loading screens are paced by VBlanks while the boot is slow: virtual time ran 4-6x real time.
- Movies take real time while virtual time stood still.

## Rule

- Virtual time advances by fixed charges, never from the host clock (for example syscall 500, register access 50,
  back-edge 8, Count read 64 cycles); when every thread waits, jump to the next event. Interrupts only at safe points.
- Read the video mode from the disc and honour it (50 Hz for PAL) before measuring anything.
- While the guest works, let virtual time follow the real clock like a PS2 dropping frames; forgive jumps over about
  250 ms (a long streaming stall should pause the game, not fast-forward it).
- Find the game's frame limiter (often "VBlanks per flip") and make the cap a run option; on a 60 Hz LCD prefer caps
  that divide 60 (30, 20, 15): 25 fps judders (frames shown 2-3-2-3 refreshes).
- Pace the boot in real time when loading screens play audio; skip that pacing in automated test runs (saves 5-6.5 s).
- Freeze virtual time during movies and shift the pacing afterwards; the movie's audio is its clock.

## Evidence

PSP-3000: PAL at 50 Hz instead of 60: +25 % game speed. Forgiving pacing: game clock x0.986-0.989 of real time,
physics x1.000, 29.3-29.7 fps windows, against x0.89-0.92 before. Real-time boot pacing: loading-screen audio drops
84 -> 10, the boot not longer (main loop at 74.5 vs 74.8 s real). Host simulation of the old pacing: x2.09 game speed
at 10 ms frames, x0.66 at 60 ms. A 60 fps cap made frame-counting game logic run twice as often: experimental only.

## Related

[Log writes and disc reads as spikes](../hardware/hitches-log-and-disc.md), [IOP replies](iop-replies-exact-virtual-time.md),
skills/hle-authoring
