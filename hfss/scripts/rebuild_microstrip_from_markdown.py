#!/home/solarstatiion/.venvs/pyaedt-mcp/bin/python
"""Build the HFSS model from its Markdown spec and compare S-parameters."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import statistics
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path("/home/solarstatiion/aedt-mcp")
SPEC_PATH = ROOT / "specs" / "microstrip_50ohm_fr4.md"
REFERENCE_DIR = ROOT / "projects" / "microstrip_50ohm_fr4_20260802_162355"
REFERENCE_TOUCHSTONE = REFERENCE_DIR / "microstrip_50ohm_fr4.s2p"

for key, value in dotenv_values(ROOT / ".env").items():
    if value is not None:
        os.environ[key] = value

from ansys.aedt.core import Hfss


def load_spec(path: Path) -> dict:
    """Extract and validate the JSON source-of-truth block."""
    text = path.read_text()
    match = re.search(
        r"<!-- AEDT_SPEC_BEGIN -->\s*```json\s*(.*?)\s*```\s*"
        r"<!-- AEDT_SPEC_END -->",
        text,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"No machine-readable AEDT spec found in {path}")
    spec = json.loads(match.group(1))
    if spec.get("schema_version") != 1:
        raise ValueError(f"Unsupported schema version: {spec.get('schema_version')}")
    return spec


def pair_to_complex(a: float, b: float, data_format: str) -> complex:
    if data_format == "RI":
        return complex(a, b)
    magnitude = 10.0 ** (a / 20.0) if data_format == "DB" else a
    angle = math.radians(b)
    return magnitude * complex(math.cos(angle), math.sin(angle))


def parse_touchstone(path: Path) -> list[dict[str, float | complex]]:
    """Parse a Touchstone v1 two-port file."""
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
                elif field in {"RI", "MA", "DB"}:
                    data_format = field
            continue
        if not line.startswith("["):
            numeric_tokens.extend(float(token) for token in line.split())

    rows: list[dict[str, float | complex]] = []
    for offset in range(0, len(numeric_tokens), 9):
        values = numeric_tokens[offset : offset + 9]
        if len(values) != 9:
            break
        rows.append(
            {
                "frequency_hz": values[0] * unit_scale,
                "s11": pair_to_complex(values[1], values[2], data_format),
                "s21": pair_to_complex(values[3], values[4], data_format),
                "s12": pair_to_complex(values[5], values[6], data_format),
                "s22": pair_to_complex(values[7], values[8], data_format),
            }
        )
    if not rows:
        raise ValueError(f"No two-port data found in {path}")
    return rows


def db(value: complex) -> float:
    return 20.0 * math.log10(max(abs(value), 1e-15))


def phase(value: complex) -> float:
    return math.degrees(math.atan2(value.imag, value.real))


def wrapped_phase_delta(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def compare_touchstones(reference_path: Path, rebuilt_path: Path) -> tuple[dict, list[dict]]:
    reference = parse_touchstone(reference_path)
    rebuilt = parse_touchstone(rebuilt_path)
    if len(reference) != len(rebuilt):
        raise ValueError(
            f"Point-count mismatch: reference={len(reference)}, rebuilt={len(rebuilt)}"
        )

    detail_rows: list[dict] = []
    metric_values: dict[str, dict[str, list[float]]] = {
        name: {"db": [], "complex": [], "phase": []}
        for name in ("s11", "s21", "s12", "s22")
    }
    for old, new in zip(reference, rebuilt):
        frequency_delta = abs(float(old["frequency_hz"]) - float(new["frequency_hz"]))
        if frequency_delta > 1.0:
            raise ValueError(f"Frequency-grid mismatch of {frequency_delta} Hz")
        row = {"frequency_hz": float(old["frequency_hz"])}
        for name in metric_values:
            old_value = complex(old[name])
            new_value = complex(new[name])
            db_delta = db(new_value) - db(old_value)
            complex_delta = abs(new_value - old_value)
            phase_delta = wrapped_phase_delta(phase(new_value), phase(old_value))
            metric_values[name]["db"].append(db_delta)
            metric_values[name]["complex"].append(complex_delta)
            metric_values[name]["phase"].append(phase_delta)
            row[f"reference_{name}_db"] = db(old_value)
            row[f"rebuilt_{name}_db"] = db(new_value)
            row[f"delta_{name}_db"] = db_delta
            row[f"delta_{name}_complex"] = complex_delta
            row[f"delta_{name}_phase_deg"] = phase_delta
        detail_rows.append(row)

    metrics = {}
    for name, values in metric_values.items():
        metrics[name] = {
            "max_abs_db_delta": max(abs(value) for value in values["db"]),
            "rms_db_delta": math.sqrt(statistics.fmean(value * value for value in values["db"])),
            "max_complex_delta": max(values["complex"]),
            "rms_complex_delta": math.sqrt(
                statistics.fmean(value * value for value in values["complex"])
            ),
            "max_abs_phase_delta_deg": max(abs(value) for value in values["phase"]),
        }

    samples = {}
    for target_ghz in (1.0, 2.4, 5.0, 10.0):
        row = min(
            detail_rows,
            key=lambda item: abs(item["frequency_hz"] - target_ghz * 1e9),
        )
        samples[f"{target_ghz:g}GHz"] = {
            key: value for key, value in row.items() if key != "frequency_hz"
        }

    consistent = (
        all(metrics[name]["max_complex_delta"] <= 0.03 for name in metrics)
        and metrics["s21"]["max_abs_db_delta"] <= 0.2
        and metrics["s12"]["max_abs_db_delta"] <= 0.2
    )
    summary = {
        "reference_touchstone": str(reference_path),
        "rebuilt_touchstone": str(rebuilt_path),
        "point_count": len(detail_rows),
        "frequency_range_ghz": [
            detail_rows[0]["frequency_hz"] / 1e9,
            detail_rows[-1]["frequency_hz"] / 1e9,
        ],
        "metrics": metrics,
        "sample_comparisons": samples,
        "consistency_criteria": {
            "all_max_complex_delta_lte": 0.03,
            "s21_s12_max_abs_db_delta_lte": 0.2,
        },
        "numerically_consistent": consistent,
    }
    return summary, detail_rows


def write_comparison_report(path: Path, summary: dict) -> None:
    verdict = "PASS" if summary["numerically_consistent"] else "REVIEW"
    lines = [
        "# HFSS Markdown Rebuild Comparison",
        "",
        f"**Verdict: {verdict}**",
        "",
        f"- Compared points: {summary['point_count']}",
        f"- Frequency range: {summary['frequency_range_ghz'][0]:g}–"
        f"{summary['frequency_range_ghz'][1]:g} GHz",
        "- Comparison uses all four complex S-parameters.",
        "",
        "## Full-sweep difference metrics",
        "",
        "| Parameter | Max |ΔdB| | RMS ΔdB | Max complex Δ | RMS complex Δ | "
        "Max |Δphase| |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, values in summary["metrics"].items():
        lines.append(
            f"| {name.upper()} | {values['max_abs_db_delta']:.6g} | "
            f"{values['rms_db_delta']:.6g} | {values['max_complex_delta']:.6g} | "
            f"{values['rms_complex_delta']:.6g} | "
            f"{values['max_abs_phase_delta_deg']:.6g}° |"
        )

    lines.extend(
        [
            "",
            "## Selected-frequency dB comparison",
            "",
            "| Frequency | Parameter | Reference | Rebuilt | Δ |",
            "|---:|---|---:|---:|---:|",
        ]
    )
    for frequency, values in summary["sample_comparisons"].items():
        for name in ("s11", "s21", "s12", "s22"):
            lines.append(
                f"| {frequency} | {name.upper()} | "
                f"{values[f'reference_{name}_db']:.6f} dB | "
                f"{values[f'rebuilt_{name}_db']:.6f} dB | "
                f"{values[f'delta_{name}_db']:+.6f} dB |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The PASS criterion is intentionally based primarily on complex-wave "
            "difference and transmission magnitude. Reflection dB can show a large "
            "relative change near a very deep null even when the absolute complex "
            "difference is small. Fresh adaptive meshes are not expected to produce "
            "byte-identical Touchstone files.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    spec = load_spec(SPEC_PATH)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = ROOT / "projects" / f"microstrip_rebuilt_from_markdown_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    project_path = output_dir / "microstrip_rebuilt_from_markdown.aedt"
    touchstone_path = output_dir / "microstrip_rebuilt_from_markdown.s2p"
    comparison_json_path = output_dir / "comparison.json"
    comparison_csv_path = output_dir / "comparison_full_sweep.csv"
    comparison_md_path = output_dir / "comparison.md"
    copied_spec_path = output_dir / SPEC_PATH.name
    copied_spec_path.write_text(SPEC_PATH.read_text())

    application = spec["application"]
    project = spec["project"]
    materials = spec["materials"]
    geometry = spec["geometry_mm"]
    setup_spec = spec["setup"]
    sweep_spec = spec["sweep"]
    execution = spec["execution"]
    export_spec = spec["export"]

    line_l = float(geometry["line_length"])
    substrate_w = float(geometry["substrate_width"])
    substrate_h = float(geometry["substrate_height"])
    trace_w = float(geometry["trace_width"])
    copper_t = float(geometry["copper_thickness"])
    margin_x = float(geometry["air_margin_x"])
    margin_y = float(geometry["air_margin_y"])
    margin_below = float(geometry["air_margin_below"])
    margin_above = float(geometry["air_margin_above_trace"])

    hfss = None
    try:
        hfss = Hfss(
            project=str(project_path),
            design=project["design_name"],
            solution_type=application["solution_type"],
            version=application["version"],
            non_graphical=bool(execution["non_graphical"]),
            new_desktop=True,
            close_on_exit=False,
        )
        hfss.modeler.model_units = project["model_units"]

        hfss.modeler.create_box(
            [0, -substrate_w / 2, 0],
            [line_l, substrate_w, substrate_h],
            name="FR4_Substrate",
            material=materials["substrate"]["aedt_name"],
        )
        hfss.modeler.create_box(
            [0, -substrate_w / 2, -copper_t],
            [line_l, substrate_w, copper_t],
            name="Ground",
            material=materials["conductor"]["aedt_name"],
        )
        hfss.modeler.create_box(
            [0, -trace_w / 2, substrate_h],
            [line_l, trace_w, copper_t],
            name="Trace",
            material=materials["conductor"]["aedt_name"],
        )
        airbox = hfss.modeler.create_box(
            [-margin_x, -substrate_w / 2 - margin_y, -margin_below],
            [
                line_l + 2 * margin_x,
                substrate_w + 2 * margin_y,
                margin_below + substrate_h + copper_t + margin_above,
            ],
            name="AirBox",
            material=materials["surrounding"]["aedt_name"],
        )
        if not hfss.assign_radiation_boundary_to_objects(
            airbox, name=spec["boundary"]["name"]
        ):
            raise RuntimeError("Failed to assign Radiation to AirBox")

        port_height = substrate_h + copper_t
        for port_spec in spec["ports"]:
            x = float(port_spec["x_mm"])
            sheet = hfss.modeler.create_rectangle(
                port_spec["plane"],
                [x, -trace_w / 2, 0],
                [trace_w, port_height],
                name=port_spec["sheet_name"],
            )
            if not hfss.lumped_port(
                sheet,
                integration_line=[[x, 0, port_height], [x, 0, 0]],
                impedance=float(port_spec["impedance_ohm"]),
                name=port_spec["name"],
                renormalize=bool(port_spec["renormalize"]),
            ):
                raise RuntimeError(f"Failed to create {port_spec['name']}")

        setup = hfss.create_setup(setup_spec["name"])
        setup.props["Frequency"] = f"{setup_spec['adaptive_frequency_ghz']}GHz"
        setup.props["MaximumPasses"] = int(setup_spec["maximum_passes"])
        setup.props["MinimumPasses"] = int(setup_spec["minimum_passes"])
        setup.props["MinimumConvergedPasses"] = int(
            setup_spec["minimum_converged_passes"]
        )
        setup.props["MaxDeltaS"] = float(setup_spec["max_delta_s"])
        setup.update()

        sweep = hfss.create_linear_count_sweep(
            setup=setup_spec["name"],
            unit="GHz",
            start_frequency=float(sweep_spec["start_ghz"]),
            stop_frequency=float(sweep_spec["stop_ghz"]),
            num_of_freq_points=int(sweep_spec["point_count"]),
            name=sweep_spec["name"],
            save_fields=bool(sweep_spec["save_fields"]),
            sweep_type=sweep_spec["type"],
            interpolation_tol=float(sweep_spec["interpolation_tolerance"]),
            interpolation_max_solutions=int(
                sweep_spec["interpolation_max_solutions"]
            ),
        )
        if not sweep:
            raise RuntimeError("Failed to create Sweep1")

        hfss.save_project(str(project_path))
        if not hfss.analyze_setup(
            setup_spec["name"], cores=int(execution["cores"]), blocking=True
        ):
            raise RuntimeError("HFSS reported that the rebuilt setup failed")
        hfss.save_project(str(project_path))
        if not hfss.export_touchstone(
            setup=setup_spec["name"],
            sweep=sweep_spec["name"],
            output_file=str(touchstone_path),
            renormalization=bool(export_spec["renormalize"]),
            impedance=float(export_spec["impedance_ohm"]),
            gamma_impedance_comments=bool(
                export_spec["include_gamma_impedance_comments"]
            ),
        ):
            raise RuntimeError("Failed to export rebuilt Touchstone data")

        comparison, detail_rows = compare_touchstones(
            REFERENCE_TOUCHSTONE, touchstone_path
        )
        comparison.update(
            {
                "specification": str(SPEC_PATH),
                "copied_specification": str(copied_spec_path),
                "rebuilt_project": str(project_path),
                "comparison_csv": str(comparison_csv_path),
                "comparison_report": str(comparison_md_path),
            }
        )
        comparison_json_path.write_text(json.dumps(comparison, indent=2))
        with comparison_csv_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(detail_rows[0]))
            writer.writeheader()
            writer.writerows(detail_rows)
        write_comparison_report(comparison_md_path, comparison)
        print(json.dumps(comparison, indent=2))
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
