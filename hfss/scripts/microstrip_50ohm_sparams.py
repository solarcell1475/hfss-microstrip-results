#!/home/solarstatiion/.venvs/pyaedt-mcp/bin/python
"""Build and solve a 50-ohm FR-4 microstrip and export its 2-port S matrix."""

from __future__ import annotations

import csv
import json
import math
import os
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path("/home/solarstatiion/aedt-mcp")
for key, value in dotenv_values(ROOT / ".env").items():
    if value is not None:
        os.environ[key] = value

from ansys.aedt.core import Hfss


def hammerstad_impedance(width_mm: float, height_mm: float, er: float) -> float:
    """Return the zero-thickness Hammerstad microstrip impedance estimate."""
    ratio = width_mm / height_mm
    correction = 0.04 * (1.0 - ratio) ** 2 if ratio < 1.0 else 0.0
    effective_er = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (
        1.0 / math.sqrt(1.0 + 12.0 / ratio) + correction
    )
    if ratio <= 1.0:
        return 60.0 / math.sqrt(effective_er) * math.log(8.0 / ratio + ratio / 4.0)
    return 120.0 * math.pi / (
        math.sqrt(effective_er)
        * (ratio + 1.393 + 0.667 * math.log(ratio + 1.444))
    )


def parse_touchstone(path: Path) -> list[dict[str, float]]:
    """Parse a Touchstone v1 two-port file into complex S-parameter rows."""
    unit_scale = 1e9
    data_format = "MA"
    numeric_tokens: list[float] = []

    for raw_line in path.read_text(errors="replace").splitlines():
        line = raw_line.split("!", 1)[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            fields = line[1:].upper().split()
            scales = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
            for field in fields:
                if field in scales:
                    unit_scale = scales[field]
                if field in {"RI", "MA", "DB"}:
                    data_format = field
            continue
        if line.startswith("["):
            continue
        numeric_tokens.extend(float(token) for token in line.split())

    def pair_to_complex(a: float, b: float) -> complex:
        if data_format == "RI":
            return complex(a, b)
        magnitude = 10.0 ** (a / 20.0) if data_format == "DB" else a
        angle = math.radians(b)
        return magnitude * complex(math.cos(angle), math.sin(angle))

    rows = []
    for offset in range(0, len(numeric_tokens), 9):
        values = numeric_tokens[offset : offset + 9]
        if len(values) != 9:
            break
        # Touchstone two-port ordering is S11, S21, S12, S22.
        s11 = pair_to_complex(values[1], values[2])
        s21 = pair_to_complex(values[3], values[4])
        s12 = pair_to_complex(values[5], values[6])
        s22 = pair_to_complex(values[7], values[8])
        row: dict[str, float] = {"frequency_hz": values[0] * unit_scale}
        for name, value in {"s11": s11, "s21": s21, "s12": s12, "s22": s22}.items():
            row[f"{name}_real"] = value.real
            row[f"{name}_imag"] = value.imag
            row[f"{name}_db"] = 20.0 * math.log10(max(abs(value), 1e-15))
            row[f"{name}_phase_deg"] = math.degrees(math.atan2(value.imag, value.real))
        rows.append(row)
    return rows


def main() -> int:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = ROOT / "projects" / f"microstrip_50ohm_fr4_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    project_path = output_dir / "microstrip_50ohm_fr4.aedt"
    touchstone_path = output_dir / "microstrip_50ohm_fr4.s2p"
    csv_path = output_dir / "microstrip_50ohm_full_s_matrix.csv"
    summary_path = output_dir / "summary.json"

    # Geometry in millimetres. W=3.07 mm gives about 50.1 ohm by Hammerstad
    # for zero-thickness copper; 35 um copper shifts it slightly lower.
    er = 4.4
    substrate_h = 1.6
    trace_w = 3.07
    copper_t = 0.035
    line_l = 50.0
    substrate_w = 20.0
    z0_estimate = hammerstad_impedance(trace_w, substrate_h, er)

    hfss = None
    try:
        hfss = Hfss(
            project=str(project_path),
            design="Microstrip50Ohm",
            solution_type="Modal",
            version=os.environ.get("AEDT_VERSION", "2025.1"),
            non_graphical=True,
            new_desktop=True,
            close_on_exit=False,
        )
        hfss.modeler.model_units = "mm"

        substrate = hfss.modeler.create_box(
            [0, -substrate_w / 2, 0],
            [line_l, substrate_w, substrate_h],
            name="FR4_Substrate",
            material="FR4_epoxy",
        )
        ground = hfss.modeler.create_box(
            [0, -substrate_w / 2, -copper_t],
            [line_l, substrate_w, copper_t],
            name="Ground",
            material="copper",
        )
        trace = hfss.modeler.create_box(
            [0, -trace_w / 2, substrate_h],
            [line_l, trace_w, copper_t],
            name="Trace",
            material="copper",
        )
        airbox = hfss.modeler.create_box(
            [-5, -substrate_w / 2 - 10, -10],
            [line_l + 10, substrate_w + 20, substrate_h + copper_t + 25],
            name="AirBox",
            material="air",
        )
        radiation = hfss.assign_radiation_boundary_to_objects(airbox, name="Radiation")
        if not radiation:
            raise RuntimeError("Failed to assign the radiation boundary.")

        port1_sheet = hfss.modeler.create_rectangle(
            "YZ",
            [0, -trace_w / 2, 0],
            [trace_w, substrate_h + copper_t],
            name="Port1Sheet",
        )
        port2_sheet = hfss.modeler.create_rectangle(
            "YZ",
            [line_l, -trace_w / 2, 0],
            [trace_w, substrate_h + copper_t],
            name="Port2Sheet",
        )
        port1 = hfss.lumped_port(
            port1_sheet,
            integration_line=[[0, 0, substrate_h + copper_t], [0, 0, 0]],
            impedance=50,
            name="Port1",
            renormalize=True,
        )
        port2 = hfss.lumped_port(
            port2_sheet,
            integration_line=[[line_l, 0, substrate_h + copper_t], [line_l, 0, 0]],
            impedance=50,
            name="Port2",
            renormalize=True,
        )
        if not port1 or not port2:
            raise RuntimeError("Failed to create both 50-ohm lumped ports.")

        setup = hfss.create_setup("Setup1")
        setup.props["Frequency"] = "10GHz"
        setup.props["MaximumPasses"] = 10
        setup.props["MinimumPasses"] = 2
        setup.props["MinimumConvergedPasses"] = 2
        setup.props["MaxDeltaS"] = 0.02
        setup.update()
        sweep = hfss.create_linear_count_sweep(
            setup="Setup1",
            unit="GHz",
            start_frequency=1.0,
            stop_frequency=10.0,
            num_of_freq_points=181,
            name="Sweep1",
            save_fields=False,
            sweep_type="Interpolating",
            interpolation_tol=0.25,
            interpolation_max_solutions=80,
        )
        if not sweep:
            raise RuntimeError("Failed to create the 1-10 GHz sweep.")

        hfss.save_project(str(project_path))
        if not hfss.analyze_setup("Setup1", cores=8, blocking=True):
            raise RuntimeError("HFSS reported that Setup1 did not solve successfully.")
        hfss.save_project(str(project_path))

        exported = hfss.export_touchstone(
            setup="Setup1",
            sweep="Sweep1",
            output_file=str(touchstone_path),
            renormalization=True,
            impedance=50,
            gamma_impedance_comments=True,
        )
        if not exported or not touchstone_path.exists():
            raise RuntimeError("HFSS did not export the Touchstone file.")

        rows = parse_touchstone(touchstone_path)
        if not rows:
            raise RuntimeError("No S-parameter rows were parsed from the Touchstone file.")
        with csv_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

        sample_rows = {}
        for target_ghz in (1.0, 2.4, 5.0, 10.0):
            row = min(rows, key=lambda item: abs(item["frequency_hz"] - target_ghz * 1e9))
            sample_rows[f"{target_ghz:g}GHz"] = {
                key: round(value, 6)
                for key, value in row.items()
                if key == "frequency_hz" or key.endswith("_db") or key.endswith("_phase_deg")
            }

        summary = {
            "success": True,
            "project": str(project_path),
            "touchstone": str(touchstone_path),
            "full_s_matrix_csv": str(csv_path),
            "frequency_range_ghz": [1.0, 10.0],
            "points": len(rows),
            "geometry_mm": {
                "line_length": line_l,
                "trace_width": trace_w,
                "copper_thickness": copper_t,
                "substrate_height": substrate_h,
                "substrate_width": substrate_w,
            },
            "substrate": {"material": "FR4_epoxy", "relative_permittivity_nominal": er},
            "port_impedance_ohm": 50,
            "hammerstad_z0_ohm": round(z0_estimate, 3),
            "samples": sample_rows,
            "worst_s11_db": round(max(row["s11_db"] for row in rows), 4),
            "worst_s22_db": round(max(row["s22_db"] for row in rows), 4),
            "minimum_s21_db": round(min(row["s21_db"] for row in rows), 4),
            "maximum_reciprocity_error_db": round(
                max(abs(row["s21_db"] - row["s12_db"]) for row in rows), 6
            ),
        }
        summary_path.write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return 0
    except Exception:
        traceback.print_exc()
        print(f"FAILURE: outputs retained under {output_dir}")
        return 1
    finally:
        if hfss:
            hfss.release_desktop(close_projects=True, close_desktop=True)


if __name__ == "__main__":
    raise SystemExit(main())
