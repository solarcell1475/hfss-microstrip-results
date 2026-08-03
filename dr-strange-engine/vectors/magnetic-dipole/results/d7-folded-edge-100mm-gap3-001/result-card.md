# Dr Strange Result Card: Folded Edge at 100 mm

## Geometry tested

- Element/feed center spacing: **100 mm**
- Facing patch-edge gap: **3 mm**
- Fold: **90° downward**
- Embedded fold depth: **17.5 mm**, from substrate top `z=55 mm` to `z=37.5 mm`

The geometry was created in a copied AEDT project; neither the original vector nor the accepted `mx=210 mm` project was modified.

## Result at 600 MHz

| Candidate | S11 | S21 | Peak realized gain | Accepted input power |
|---|---:|---:|---:|---:|
| Accepted `mx=210 mm` | -19.639 dB | -20.737 dB | 7.057 dBi | 98.91% |
| Folded, 100 mm, 3 mm gap | -0.013 dB | -55.566 dB | -17.104 dBi | 0.31% |

## Decision: reject

The apparent S21 of -55.566 dB is **not useful isolation**. S11 is nearly 0 dB, so only 0.31% of Port 1 incident power is accepted. Peak realized gain falls by 24.161 dB.

The structural cause is feed topology, not solver failure. At 100 mm spacing, the two original 165 mm buried feedline spans overlap by **65 mm**, and Port 2 falls inside the first feed region. HFSS reports that only one conductor touches each lumped port.

## Next choice card

- **A — Outward shortened feeds:** retain the 100 mm centers and folded edges, but reroute both feeds away from the central overlap.
- **B — Independent local probes:** replace both buried crossing feeds with local coax/probe feeds.
- **C — Larger spacing:** retain the existing feed topology and use at least 168 mm center spacing.
- **OTHER — Custom**
- **STOP — Keep the accepted 210 mm candidate**
