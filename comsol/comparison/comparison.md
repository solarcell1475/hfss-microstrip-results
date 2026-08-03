# COMSOL–HFSS Microstrip Comparison

The same nominal 50-ohm FR-4 microstrip geometry was solved in COMSOL 6.4 and HFSS 2025 R1 at 181 frequencies from 1 to 10 GHz.

## Important formulation differences

- COMSOL uses zero-thickness PEC trace and ground surfaces; HFSS used 35 µm finite-conductivity copper solids.
- COMSOL uses second-order scattering boundaries; HFSS used a Radiation boundary.
- COMSOL uses εr=4.4 and tanδ=0.02; HFSS used its `FR4_epoxy` library material.
- COMSOL directly solved all frequencies; HFSS used an interpolating sweep.

## Full-sweep differences

| Parameter | Max |ΔdB| | RMS ΔdB | Max |Δphase| | RMS Δphase | Max complex Δ |
|---|---:|---:|---:|---:|---:|
| S11 | 9.916293 | 4.734506 | 64.876210° | 19.964144° | 0.056250 |
| S21 | 0.061883 | 0.038097 | 14.197596° | 8.782444° | 0.194211 |
| S12 | 0.061885 | 0.038094 | 14.197956° | 8.782491° | 0.194216 |
| S22 | 10.683931 | 4.722894 | 74.291772° | 21.809246° | 0.055220 |

## Selected-frequency magnitude comparison

| Frequency | Parameter | HFSS | COMSOL | Δ |
|---:|---|---:|---:|---:|
| 1GHz | S11 | -29.460069 dB | -24.351592 dB | +5.108478 dB |
| 1GHz | S21 | -0.188860 dB | -0.143661 dB | +0.045199 dB |
| 1GHz | S12 | -0.188860 dB | -0.143660 dB | +0.045201 dB |
| 1GHz | S22 | -29.524168 dB | -24.307115 dB | +5.217054 dB |
| 2.4GHz | S11 | -33.801796 dB | -26.760617 dB | +7.041179 dB |
| 2.4GHz | S21 | -0.438883 dB | -0.386737 dB | +0.052146 dB |
| 2.4GHz | S12 | -0.438883 dB | -0.386733 dB | +0.052150 dB |
| 2.4GHz | S22 | -33.402976 dB | -26.838037 dB | +6.564939 dB |
| 5GHz | S11 | -25.914736 dB | -23.763982 dB | +2.150754 dB |
| 5GHz | S21 | -0.906308 dB | -0.880977 dB | +0.025331 dB |
| 5GHz | S12 | -0.906308 dB | -0.880970 dB | +0.025338 dB |
| 5GHz | S22 | -25.843924 dB | -24.139919 dB | +1.704005 dB |
| 10GHz | S11 | -25.387489 dB | -25.874148 dB | -0.486658 dB |
| 10GHz | S21 | -2.087660 dB | -2.100914 dB | -0.013254 dB |
| 10GHz | S12 | -2.087660 dB | -2.100898 dB | -0.013238 dB |
| 10GHz | S22 | -27.721217 dB | -26.509097 dB | +1.212120 dB |

## Interpretation

Transmission magnitudes agree closely: the worst S21/S12 magnitude difference is under 0.062 dB. Reflection differs more because S11/S22 are highly sensitive to the conductor, port, mesh, and absorbing-boundary formulations. Complex-wave differences also include phase accumulated over the 50 mm line.
