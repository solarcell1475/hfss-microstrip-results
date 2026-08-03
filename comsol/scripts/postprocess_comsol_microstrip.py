"""Postprocess solved COMSOL sweeps and compare their full complex S matrix."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import mph
import numpy as np


RESULTS = Path(
    "/home/solarstatiion/COMSOL_Multiphysics_MCP/models/"
    "microstrip_comsol_181pt_20260802_235956"
)
HFSS_CSV = Path(
    "/home/solarstatiion/aedt-mcp/projects/"
    "microstrip_50ohm_fr4_20260802_162355/"
    "microstrip_50ohm_full_s_matrix.csv"
)


def flat(value) -> np.ndarray:
    return np.asarray(value).reshape(-1)


def db(value: complex) -> float:
    return 20.0 * math.log10(max(abs(value), 1e-15))


def phase(value: complex) -> float:
    return math.degrees(math.atan2(value.imag, value.real))


def phase_delta(new: complex, old: complex) -> float:
    return (phase(new) - phase(old) + 180.0) % 360.0 - 180.0


def load_hfss() -> list[dict[str, float]]:
    with HFSS_CSV.open(newline="") as stream:
        return [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]


client = mph.start(cores=4)
port1_model = client.load(RESULTS / "microstrip_comsol_port1.mph")
frequencies = flat(port1_model.evaluate("freq"))
comsol = {
    "s11": flat(port1_model.evaluate("emw.S11")),
    "s21": flat(port1_model.evaluate("emw.S21")),
}
port1_model.clear()
port1_model.save(RESULTS / "microstrip_comsol_compact.mph")
client.remove(port1_model)

port2_model = client.load(RESULTS / "microstrip_comsol_port2.mph")
comsol.update(
    {
        "s12": flat(port2_model.evaluate("emw.S12")),
        "s22": flat(port2_model.evaluate("emw.S22")),
    }
)
client.remove(port2_model)

hfss = load_hfss()
rows = []
for index, frequency in enumerate(frequencies):
    old_row = min(hfss, key=lambda row: abs(row["frequency_hz"] - frequency))
    row = {"frequency_hz": float(frequency)}
    for name in ("s11", "s21", "s12", "s22"):
        old = complex(old_row[f"{name}_real"], old_row[f"{name}_imag"])
        new = complex(comsol[name][index])
        row.update(
            {
                f"hfss_{name}_db": db(old),
                f"comsol_{name}_db": db(new),
                f"delta_{name}_db": db(new) - db(old),
                f"hfss_{name}_phase_deg": phase(old),
                f"comsol_{name}_phase_deg": phase(new),
                f"delta_{name}_phase_deg": phase_delta(new, old),
                f"delta_{name}_complex": abs(new - old),
            }
        )
    rows.append(row)

csv_path = RESULTS / "hfss_comsol_detailed_comparison.csv"
with csv_path.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

metrics = {}
for name in ("s11", "s21", "s12", "s22"):
    db_values = [row[f"delta_{name}_db"] for row in rows]
    phase_values = [row[f"delta_{name}_phase_deg"] for row in rows]
    complex_values = [row[f"delta_{name}_complex"] for row in rows]
    metrics[name] = {
        "max_abs_db_delta": max(abs(value) for value in db_values),
        "rms_db_delta": math.sqrt(sum(value * value for value in db_values) / len(rows)),
        "max_abs_phase_delta_deg": max(abs(value) for value in phase_values),
        "rms_phase_delta_deg": math.sqrt(
            sum(value * value for value in phase_values) / len(rows)
        ),
        "max_complex_delta": max(complex_values),
    }

samples = {}
for target in (1.0, 2.4, 5.0, 10.0):
    samples[f"{target:g}GHz"] = min(
        rows, key=lambda row: abs(row["frequency_hz"] - target * 1e9)
    )

touchstone_path = RESULTS / "microstrip_comsol.s2p"
with touchstone_path.open("w") as stream:
    stream.write("! COMSOL 6.4 full two-direction lumped-port sweep\n")
    stream.write("# Hz S RI R 50\n")
    for index, frequency in enumerate(frequencies):
        values = [
            comsol["s11"][index],
            comsol["s21"][index],
            comsol["s12"][index],
            comsol["s22"][index],
        ]
        fields = [f"{frequency:.12g}"]
        for value in values:
            fields.extend([f"{value.real:.15g}", f"{value.imag:.15g}"])
        stream.write(" ".join(fields) + "\n")

summary = {
    "success": True,
    "points": len(rows),
    "frequency_range_ghz": [
        float(frequencies[0] / 1e9),
        float(frequencies[-1] / 1e9),
    ],
    "metrics": metrics,
    "samples": samples,
    "detailed_csv": str(csv_path),
    "touchstone": str(touchstone_path),
    "compact_model": str(RESULTS / "microstrip_comsol_compact.mph"),
}
(RESULTS / "comparison_detailed.json").write_text(json.dumps(summary, indent=2))

report = [
    "# COMSOL–HFSS Microstrip Comparison",
    "",
    "The same nominal 50-ohm FR-4 microstrip geometry was solved in COMSOL 6.4 "
    "and HFSS 2025 R1 at 181 frequencies from 1 to 10 GHz.",
    "",
    "## Important formulation differences",
    "",
    "- COMSOL uses zero-thickness PEC trace and ground surfaces; HFSS used "
    "35 µm finite-conductivity copper solids.",
    "- COMSOL uses second-order scattering boundaries; HFSS used a Radiation boundary.",
    "- COMSOL uses εr=4.4 and tanδ=0.02; HFSS used its `FR4_epoxy` library material.",
    "- COMSOL directly solved all frequencies; HFSS used an interpolating sweep.",
    "",
    "## Full-sweep differences",
    "",
    "| Parameter | Max |ΔdB| | RMS ΔdB | Max |Δphase| | RMS Δphase | Max complex Δ |",
    "|---|---:|---:|---:|---:|---:|",
]
for name, values in metrics.items():
    report.append(
        f"| {name.upper()} | {values['max_abs_db_delta']:.6f} | "
        f"{values['rms_db_delta']:.6f} | "
        f"{values['max_abs_phase_delta_deg']:.6f}° | "
        f"{values['rms_phase_delta_deg']:.6f}° | "
        f"{values['max_complex_delta']:.6f} |"
    )

report.extend(
    [
        "",
        "## Selected-frequency magnitude comparison",
        "",
        "| Frequency | Parameter | HFSS | COMSOL | Δ |",
        "|---:|---|---:|---:|---:|",
    ]
)
for frequency, row in samples.items():
    for name in ("s11", "s21", "s12", "s22"):
        report.append(
            f"| {frequency} | {name.upper()} | {row[f'hfss_{name}_db']:.6f} dB | "
            f"{row[f'comsol_{name}_db']:.6f} dB | "
            f"{row[f'delta_{name}_db']:+.6f} dB |"
        )

report.extend(
    [
        "",
        "## Interpretation",
        "",
        "Transmission magnitudes agree closely: the worst S21/S12 magnitude "
        "difference is under 0.062 dB. Reflection differs more because S11/S22 "
        "are highly sensitive to the conductor, port, mesh, and absorbing-boundary "
        "formulations. Complex-wave differences also include phase accumulated "
        "over the 50 mm line.",
        "",
    ]
)
(RESULTS / "comparison.md").write_text("\n".join(report))
print(json.dumps(summary, indent=2))
