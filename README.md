# HFSS 50-ohm FR-4 microstrip results

![Solved HFSS microstrip model](assets/hfss_microstrip_final_capture.png)

A solved Ansys HFSS 2025 R1 model of a 50-ohm microstrip line on FR-4, with a 1–10 GHz interpolating sweep (181 points).

## Geometry

- Trace: 3.07 mm wide, 50 mm long, 0.035 mm thick
- Substrate: FR4_epoxy, 1.6 mm thick, 20 mm wide, nominal εr = 4.4
- Ports: two 50-ohm lumped ports
- Hammerstad impedance estimate: 50.126 ohms

## Key results

| Frequency | S11 | S21 |
|---:|---:|---:|
| 1 GHz | -29.46 dB | -0.189 dB |
| 2.4 GHz | -33.80 dB | -0.439 dB |
| 5 GHz | -25.91 dB | -0.906 dB |
| 10 GHz | -25.39 dB | -2.088 dB |

The full model, Touchstone data, S-matrix CSV, and JSON summary are included in this repository.
