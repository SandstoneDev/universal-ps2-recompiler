# Knowledge base

Field notes from real ports: lessons that transfer from one PS2 game to the next. Each note is one lesson (situation,
cause, rule, evidence) with the place it was measured. Notes are game-neutral: they are written per hardware topic,
per translation or HLE topic, per workflow step, or per engine/middleware **category** - never about one named game.

- Index of every note: [INDEX.md](INDEX.md) (generated: `python -m uprkit kb index`)
- Search: `python -m uprkit kb search <words>`
- New note: `python -m uprkit kb new <category> <slug> "<Title>"` from [TEMPLATE.md](TEMPLATE.md); how to write one:
  the `field-notes` skill (`skills/field-notes/SKILL.md`)
- Check: `python -m uprkit kb check` (fields, sections, ASCII, index up to date)

| Folder | What |
|---|---|
| `hardware/` | the PSP (and PS2) as measured: CPU, caches, memory, memory stick, GE, Media Engine, kernel |
| `translation/` | analysing and translating R5900 code |
| `hle/` | replacing the PS2 kernel, libraries, IOP and devices |
| `engines/` | engine and middleware categories: render boundaries that worked |
| `workflow/` | testing, deploying, measuring, working with the user |

## Quick lookup: topic -> where to read

| You meet | Read |
|---|---|
| Unknown syscall, RPC server or hardware access on the host | `skills/ps2rc-translate/SKILL.md` section 3, then `skills/hle-authoring/SKILL.md` |
| The port and the original disagree | [Reference runs: find the first divergence](hle/reference-run-first-divergence.md) |
| Sound driver replies, IOP modules | [IOP replies must be exact and in step](hle/iop-replies-exact-virtual-time.md) |
| Floating-point results differ | [The R5900 FPU is not IEEE](translation/r5900-fpu-not-ieee.md) |
| "Functions" made of case labels, dispatch errors | [Function discovery and jump tables](translation/function-discovery-jump-tables.md) |
| Stuck on a blocker | [Boot to the first blocker](translation/boot-to-first-blocker.md) |
| Choosing how to replace the renderer | [Render boundary at the device-driver layer](engines/render-boundary-device-driver.md) |
| Slow on the PSP, flat profile | [Memory-bound CPU: the I-cache dominates](hardware/memory-bound-cpu-icache.md) |
| Free memory, heap size | [Free memory on the 64 MB models](hardware/free-memory-64mb-models.md), [Streaming budget thrash](hardware/streaming-budget-thrash.md) |
| Console switches off at the first file access | [Coroutine stacks inside the PSP thread stack](hardware/coroutine-stacks-in-thread-stack.md) |
| Log stops while the game runs on | [Open-file limit on the memory stick](hardware/memory-stick-open-file-limit.md) |
| Empty or truncated log after a crash | [The file size is recorded on close](hardware/fat-size-recorded-on-close.md) |
| Frame-time spikes | [Log writes and disc reads as spikes](hardware/hitches-log-and-disc.md) |
| GE hangs, garbage, missing primitives | [GE display-list safety](hardware/ge-display-list-safety.md) |
| Media Engine | [Media Engine rules](hardware/media-engine-rules.md) |
| Power-off at exit | [Exit order](hardware/exit-order.md), [Kernel module must export module_stop](hardware/kernel-module-export-module-stop.md) |
| PPSSPP says it works, the PSP does not | [PPSSPP gives booleans, the PSP gives numbers](workflow/ppsspp-booleans-hardware-numbers.md) |
| Copying to the memory stick | [Copy file by file, verify md5](workflow/deploy-md5-verify.md) |
| Which log is this? | [Verify the log you read](workflow/log-path-verification.md) |
| Is it faster? | [A/B sets with a control and a control-again](workflow/ab-sets-control-again.md), [One-run interleaved A/B](workflow/one-run-interleaved-ab.md) |
| The whole pipeline, host first | [The pipeline](translation/pipeline-host-first.md) |
| Which back-end levers pay | [Translator levers measured on hardware](translation/backend-levers-measured.md) |
| Boots wrong after narrowing | [Width and liveness bugs](translation/width-liveness-bugs-at-boot.md) |
| VU0 macro or micro code | [VU0 macro and micro](hle/vu0-macro-micro.md) |
| Sound driver, audio cost | [Sound driver in lockstep, samples on the ME](hle/sound-driver-lockstep-me.md) |
| Game too fast, too slow, sped-up loading music | [Virtual time and pacing](hle/virtual-time-pacing.md) |
| One scene much slower than others | [Off-screen passes](engines/offscreen-passes-double-work.md), [Where the frame goes](hardware/where-the-frame-goes.md) |
| Is the GE the limit? | [Measuring the GE](hardware/ge-busy-sampler-pitfall.md), [GE 3D back-end costs](hardware/ge-3d-backend-costs.md) |
| Textures: format, cost, mipmaps | [Textures: fetch traffic is the cost](hardware/texture-fetch-traffic.md) |
| Overclocking | [Overclock only through the firmware's call](hardware/overclock-cfw-api-only.md) |
| Only 24 MB free, allocation fails | [The 64 MB mode is a request](hardware/large-memory-mode-check.md) |
| Console switches off at exit | [Power-offs around exit](hardware/power-off-around-exit.md) |
| Building a profiler | [On-device profiler](hardware/profiler-on-device.md) |
| What frame rate to expect | [What the reference port reached](workflow/reference-port-results.md) |
| Several agents on one port | [Lead session, specialised agents, gates](workflow/agent-team-workflow.md) |
| Need a manual or SDK reference | `skills/fetch-docs/SKILL.md` (public sources, fetched onto your machine) |

Credit: the topic router, the phase table with entry and exit criteria and the circuit breaker in the skills adapt
ideas from the MIT-licensed agent skill "ps2-recomp-Agent-SKILL" (see NOTICE.md).
