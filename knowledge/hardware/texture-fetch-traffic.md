# Textures: keep the palette indices, convert at load; fetch traffic is the cost

- **Category:** hardware
- **Summary:** Convert PS2 PAL4/PAL8 textures in place at load time (un-swizzle + GE swizzle, CLUT reorder, alpha doubling); what costs frame time is texture fetch traffic on the bus, so half-resolution or generated mipmaps pay, pre-converted files do not.
- **Applies to:** GS PSMT4/PSMT8 textures with CLUTs on the PSP GE
- **Evidence:** census of a full disc's textures; byte-exact model tests; real PSP-3000 A/B sets and serial GE probes
- **Status:** confirmed

## Situation

Textures were 87 % 4-bit and 12.6 % 8-bit palettised. An install-time converter with a second asset format looked
attractive; so did shrinking textures to save GE time.

## Cause

PS2 textures arrive as the pre-swizzled GS transfer stream (8-bit uploaded as 32-bit at half width and height, 4-bit
as 16-bit); 8-bit CLUTs are in CSM1 order (index bits 3 and 4 swapped within 32-entry groups); alpha runs 0..128.
The PSP payload is never larger than the PS2 one, so load-time conversion fits in memory. On the PSP the GE's texture
reads compete with the memory-bound CPU for the bus.

## Rule

- Keep indices: T4/T8 with an 8888 CLUT; one fused permutation from GS swizzle to GE swizzle (about 2.3 instructions
  per texel); alpha as min(255, 2a) and double the alpha-test reference.
- Convert at load with a cache large enough for the working set; measure first-use spikes.
- Keep mip levels down to the swizzle floor (T4 32 px, T8 16 px); map single-level textures that ask for trilinear
  filtering to linear.
- To cut frame time, cut texels fetched: half resolution for large 3D textures (128 px and up, never HUD or fonts),
  or full resolution with generated mipmaps (2:1 point decimation keeping the palette indices). Note: more than one
  level splits the 8 KB texture cache; measure.
- Do not build install-time pre-converted files before measuring the conversion share.

## Evidence

Disc census: 32,525 textures; PSP payload 245.0 vs 254.8 MiB on the PS2; converter byte-exact against a reference
model on every texture, 21 planted defects caught. PSP-3000: load-time conversion 0.27-0.6 ms per frame (install-time
files would have saved 0.4-0.9 %: not built); 2,380 first-use conversions, 413 ms in total, max 8.5 ms. Half-resolution
3D textures: -3.1 ms (CI -5.0..-2.0), real GE time 12.7 -> 8.7 ms, working set 1,122 -> 484 KB per frame; halving
again: nothing more. Full resolution + generated mipmaps: same speed as half resolution (+0.08 ms, CI -0.49..+1.20)
and sharper - the shipped choice.

## Related

[GE back-end costs](ge-3d-backend-costs.md), [Measuring the GE](ge-busy-sampler-pitfall.md); the converter itself is
engine-level code and lives in the game pack
