# What the reference port reached, honestly

- **Category:** workflow
- **Summary:** A large open-world 3D PS2 game reached about 30 fps indoors and 17-21 fps outdoors on a PSP-3000 at 333 MHz (about 9 % more at 365 MHz), starting from about 7 fps, with reduced density and draw distance; quote these numbers, not "full speed".
- **Applies to:** setting the user's expectations; choosing levers
- **Evidence:** real PSP-3000 (scripted runs, free play, mission runs)
- **Status:** confirmed

## Situation

Users (and agents) expect "it runs at full speed". The first gameplay build ran at 8.4 fps and 0.28x game speed.

## Cause

The PSP's main CPU runs the translated game code about as fast as it can (memory-bound); the PS2 game did its work on
a 295 MHz CPU plus two vector units, a GS with its own memory and an I/O processor.

## Rule

Tell the user these numbers before starting, and that a heavier game will do worse, a lighter one better:

| Where | Frame rate |
|---|---|
| First gameplay build | 8.4 fps (113 ms per frame) |
| Indoors, after skipping an invisible mirror pass | about 29-30 fps (34.3 ms, at the 30 fps cap) |
| Outdoors, on foot and driving, final builds | 17-21 fps |
| Missions with many characters | down to 9-10 fps |
| Same idle run at 365 MHz | -8.6 % frame time (about +9 % fps) |

The levers that changed the game the most - population density, draw distance, effects - are the user's choice and
stay run options. Without them the floor outdoors was about 51 ms (19.8 fps): 30 fps outdoors would need the
translated code about 1.5-2x faster, and no single known lever does that.

## Evidence

PSP-3000, 333 MHz unless stated: history about 7 -> 13-16 -> 17-21 fps outdoors; interior 53.1 -> 34.3 ms; scripted
route (house + walk + drive) 51.4 ms (19.5 fps); missions 57.7 ms average; free play at 365 MHz with a 30 fps cap:
session average 48.2 ms, last 100 iterations 33.5 ms (29.9 fps); 333 vs 365 MHz idle run 54.4 vs 49.7 ms.

## Related

[Where the frame goes](../hardware/where-the-frame-goes.md), [Translator levers](../translation/backend-levers-measured.md),
[Overclock](../hardware/overclock-cfw-api-only.md), `docs/AGENT_ONBOARDING.md` section J
