# D7 isolation tuning round

Dr Strange Engine round `d7-t4-isolation-mx-001` targets `S21 < -20 dB` at 600 MHz for `600MHz_slot couple_F4B_1X2_3`.

The selected converged candidate changes `mx` from 190 mm to 210 mm. See [result-card.md](result-card.md) for the engineering decision, [summary.json](summary.json) for machine-readable provenance, and the CSV files for verified HFSS values.

The tuned AEDT working copy remains local because it includes solver result data; this directory publishes the reproducible parameter change and extracted evidence. The original AEDT source SHA-256 is recorded in `summary.json` and was not modified.
