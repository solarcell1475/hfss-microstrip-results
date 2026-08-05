# Rejected folded-edge compact-array branch

This Dr Strange experiment implemented 100 mm element-center spacing, a 3 mm projected facing-edge gap, and two 17.5 mm patch-edge sections folded 90 degrees downward into the dielectric.

HFSS completed the adaptive and 550–750 MHz sweep, but reported invalid lumped-port conductor topology. The original 165 mm feedline spans overlap by 65 mm at this spacing. S11 is nearly 0 dB and only 0.31% of incident Port 1 power is accepted, so the apparent low S21 is not useful isolation.

See [result-card.md](result-card.md) for the decision and next structural choices. The copied AEDT project remains local; its SHA-256 and source provenance are recorded in [summary.json](summary.json).
