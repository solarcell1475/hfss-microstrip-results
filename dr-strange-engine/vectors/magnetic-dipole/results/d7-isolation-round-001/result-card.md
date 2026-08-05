# Dr Strange Result Card: D7 Isolation

## Decision

Select **`mx = 210 mm`** as the D7 isolation candidate.

The converged HFSS result meets the mini-target at 600 MHz:

- **S21 = -20.737 dB**, passing the `< -20 dB` target by **0.737 dB**.
- S11 changes from -19.348 to -19.639 dB, so matching is preserved.
- Peak realized gain changes from 7.630 to 7.057 dBi: a **-0.573 dB** trade-off.
- `mx` increases from 190 to 210 mm, adding 20 mm (10.53%) to the element translation.

## Candidate comparison at 600 MHz

| Candidate | mx | Solver status | S11 | S21 | Peak realized gain | Target |
|---|---:|---|---:|---:|---:|---|
| Baseline | 190 mm | Converged | -19.348 dB | -15.375 dB | 7.630 dBi | Fail |
| Selected | 210 mm | Converged | -19.639 dB | -20.737 dB | 7.057 dBi | Pass |
| Wider-spacing probe | 230 mm | Preliminary; 10-pass run did not converge | -19.848 dB | -27.238 dB | 6.585 dBi | Pass, not acceptance-quality |

Both accepted comparison points were rerun with `MaximumPasses = 20` and completed without the earlier non-convergence warning.

## Sweep behavior

Across 550–750 MHz in 25 MHz steps, the selected candidate meets S21 < -20 dB at 8 of 9 points. The only failing point is 550 MHz (-19.494 dB).

## Dr Strange decision

**Accept as a candidate, not as a production freeze.** The isolation target and S11 guardrail pass. The engineer should explicitly accept the 0.573 dB gain trade-off and 20 mm spacing increase before promoting this branch.
