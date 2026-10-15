# Overclock only through the custom firmware's own call, at the very start, with a crash-safe fallback

- **Category:** hardware
- **Summary:** Above 333 MHz, only the custom firmware's own clock call at the first line of main() survived; writing the PLL register yourself switched the console off every time; keep a state file that steps the clock down after a crash.
- **Applies to:** PSP-2000/3000 with custom firmware that exports a clock call; not the PSP Street; other boards Unknown
- **Evidence:** real PSP-3000 (one board), dozens of runs
- **Status:** partly confirmed (one console)

## Situation

The game is CPU-bound at the stock maximum (CPU 333 MHz, bus 166 MHz). Players ask for an overclock option.

## Cause

The official clock interface stops at 333 MHz; anything higher writes an undocumented PLL multiplier. The bus and
DDR are already at their maximum, so a higher CPU clock helps only the CPU-bound part of the frame. The official
interface cannot see a PLL overclock (it keeps reporting 333). The firmware's MHz scale is wrong on some boards (a
requested 483 gave a real 365, a requested 443 gave the stock 333). A clock change while the GE, the Media Engine or
memory-stick DMA run is unsafe.

## Rule

- Never write the PLL register yourself.
- Call the custom firmware's own clock export at the **first line of main()**: before the debug screen, threads, the
  log, the kernel module, the ME, the GE and any volatile memory. Never change the clock later at run time.
- Refuse in an emulator, without the expected firmware, or when the PLL is not in its measured idle state; verify the
  result on the register and measure the real clock with an inline-assembly loop (a C loop was optimised away and
  read "1 us").
- Crash-safe state file (one line, written and synced in the data folder): write `pending` before the call; `ok`
  after 60 s of play or a clean exit; a boot that finds `pending` skips the overclock, counts a failure and steps
  down (365 -> 342); a second failure disables it; changing the setting re-arms it. A power-off after the last exit
  step finds `ok` and does not count.
- Make it a player setting, default off. Never write voltages.

## Evidence

PSP-3000, idle scripted run: 333 MHz 54.4 ms; 342 MHz 53.0 ms (-2.6 %); 365 MHz 49.7 ms (-8.6 %, boot 33.5 -> 31.2 s);
in play about 9 % more frame rate at 365 MHz. Own PLL writes: 4 of 4 power-offs (multi-step ramp, single step to
400, two other step shapes); an older engine died in 6 of 11 clock changes (memory-stick I/O next to the write was the
prime suspect). The firmware's call: 0 deaths in about 28 runs of a ladder; at 365 MHz stable once called at the first
line of main(). 401 MHz played on one board, 452 switched it off. A pure CPU overclock moved GE time by 0 %.

## Related

[Exit order](exit-order.md), [Power-offs around exit](power-off-around-exit.md), skills/psp-performance section 6
