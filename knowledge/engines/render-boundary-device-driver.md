# Render boundary at the engine's device-driver layer

- **Category:** engines
- **Summary:** Replace a PS2 renderer at its lowest stable software boundary (the driver layer) and draw with the GE; keep the engine's render logic translated.
- **Applies to:** 3D engines and middleware renderers that feed GS through VIF and VU1 microcode
- **Evidence:** real PSP-3000, PC host
- **Status:** confirmed

## Situation

The game draws through the GS, fed by VIF packets and VU1 microcode; the PSP has none of them, and the port shows
nothing.

## Cause

Emulating the VU1 needs exact pipeline latencies and puts all transform and lighting on the CPU; converting GIF
packets still needs the VU1; replacing high up at the game's own render functions means many entry points and lost
behaviour.

## Rule

- Find the driver layer: raster (texture) create, lock and destroy, native texture read, camera begin, end and clear,
  frame flip, render state, immediate-mode 2D and 3D calls, the per-mesh pipeline callback.
- Expect fast paths beside the middleware (custom batchers, post effects, water, mirrors, a texture defragmenter):
  each needs a hook.
- Order: logging hooks; host software rasteriser and frame dumps compared with PCSX2; GE for 2D; then 3D; keep the
  translated driver running behind the hooks until the GE path is validated, then skip it.
- Convert textures and meshes once to GE formats and cache them; never larger than the PS2 originals.

## Evidence

Real PSP-3000: GE time about 1.4 ms per frame for about 10,000 triangles; skipping the translated driver behind
validated hooks saved about 10 ms per frame; all runtime conversions together cost 0.27 to 0.6 ms per frame.

## Related

skills/hle-authoring section 4, [GE display-list safety](../hardware/ge-display-list-safety.md), `docs/PORTING_GUIDE.md` section 9
