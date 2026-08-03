# HFSS Markdown Rebuild Comparison

**Verdict: PASS**

- Compared points: 181
- Frequency range: 1–10 GHz
- Comparison uses all four complex S-parameters.

## Full-sweep difference metrics

| Parameter | Max |ΔdB| | RMS ΔdB | Max complex Δ | RMS complex Δ | Max |Δphase| |
|---|---:|---:|---:|---:|---:|
| S11 | 1.95278e-10 | 4.07527e-11 | 6.00688e-13 | 1.92369e-13 | 1.0896e-09° |
| S21 | 2.52556e-11 | 4.40888e-12 | 3.21968e-12 | 6.29902e-13 | 9.10063e-11° |
| S12 | 2.51932e-11 | 4.39063e-12 | 3.22185e-12 | 6.28714e-13 | 9.10063e-11° |
| S22 | 1.74175e-10 | 4.86251e-11 | 8.70398e-13 | 2.63959e-13 | 1.05359e-09° |

## Selected-frequency dB comparison

| Frequency | Parameter | Reference | Rebuilt | Δ |
|---:|---|---:|---:|---:|
| 1GHz | S11 | -29.460069 dB | -29.460069 dB | -0.000000 dB |
| 1GHz | S21 | -0.188860 dB | -0.188860 dB | +0.000000 dB |
| 1GHz | S12 | -0.188860 dB | -0.188860 dB | +0.000000 dB |
| 1GHz | S22 | -29.524168 dB | -29.524168 dB | -0.000000 dB |
| 2.4GHz | S11 | -33.801796 dB | -33.801796 dB | -0.000000 dB |
| 2.4GHz | S21 | -0.438883 dB | -0.438883 dB | -0.000000 dB |
| 2.4GHz | S12 | -0.438883 dB | -0.438883 dB | -0.000000 dB |
| 2.4GHz | S22 | -33.402976 dB | -33.402976 dB | +0.000000 dB |
| 5GHz | S11 | -25.914736 dB | -25.914736 dB | +0.000000 dB |
| 5GHz | S21 | -0.906308 dB | -0.906308 dB | +0.000000 dB |
| 5GHz | S12 | -0.906308 dB | -0.906308 dB | +0.000000 dB |
| 5GHz | S22 | -25.843924 dB | -25.843924 dB | +0.000000 dB |
| 10GHz | S11 | -25.387489 dB | -25.387489 dB | +0.000000 dB |
| 10GHz | S21 | -2.087660 dB | -2.087660 dB | +0.000000 dB |
| 10GHz | S12 | -2.087660 dB | -2.087660 dB | +0.000000 dB |
| 10GHz | S22 | -27.721217 dB | -27.721217 dB | -0.000000 dB |

## Interpretation

The PASS criterion is intentionally based primarily on complex-wave difference and transmission magnitude. Reflection dB can show a large relative change near a very deep null even when the absolute complex difference is small. Fresh adaptive meshes are not expected to produce byte-identical Touchstone files.
