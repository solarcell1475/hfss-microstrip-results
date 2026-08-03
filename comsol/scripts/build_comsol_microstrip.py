"""Build and solve a COMSOL equivalent of the HFSS 50-ohm microstrip."""

from __future__ import annotations

import csv
import json
import math
import os
import traceback
from datetime import datetime
from pathlib import Path

import mph
import numpy as np
from jpype import JArray
from jpype.types import JInt


ROOT = Path("/home/solarstatiion/COMSOL_Multiphysics_MCP")
HFSS_DIR = Path(
    "/home/solarstatiion/aedt-mcp/projects/microstrip_50ohm_fr4_20260802_162355"
)
QUICK = os.environ.get("COMSOL_QUICK", "0") == "1"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = ROOT / "models" / (
    f"microstrip_comsol_quick_{TIMESTAMP}"
    if QUICK
    else f"microstrip_comsol_181pt_{TIMESTAMP}"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ints(values: list[int]):
    return JArray(JInt)(values)


def vector(value) -> np.ndarray:
    return np.asarray(value).reshape(-1)


def evaluate_available(model: mph.Model, expressions: list[str]) -> dict[str, np.ndarray]:
    result = {}
    for expression in expressions:
        try:
            result[expression] = vector(model.evaluate(expression))
        except Exception as exc:
            print(f"Expression unavailable: {expression}: {exc}", flush=True)
    return result


def read_hfss_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="") as stream:
        return [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]


def db(value: complex) -> float:
    return 20.0 * math.log10(max(abs(value), 1e-15))


def align_and_compare(
    frequencies: np.ndarray,
    comsol_s: dict[str, np.ndarray],
    hfss_rows: list[dict[str, float]],
) -> tuple[list[dict], dict]:
    rows = []
    mapping = {
        "s11": "emw.S11",
        "s21": "emw.S21",
        "s12": "emw.S12",
        "s22": "emw.S22",
    }
    for index, frequency in enumerate(frequencies):
        reference = min(
            hfss_rows, key=lambda row: abs(row["frequency_hz"] - float(frequency))
        )
        if abs(reference["frequency_hz"] - float(frequency)) > 1.0:
            raise ValueError(f"No HFSS point aligned with COMSOL frequency {frequency}")
        row = {"frequency_hz": float(frequency)}
        for name, expression in mapping.items():
            if expression not in comsol_s or index >= len(comsol_s[expression]):
                continue
            new = complex(comsol_s[expression][index])
            old = complex(reference[f"{name}_real"], reference[f"{name}_imag"])
            row[f"hfss_{name}_db"] = db(old)
            row[f"comsol_{name}_db"] = db(new)
            row[f"delta_{name}_db"] = db(new) - db(old)
            row[f"delta_{name}_complex"] = abs(new - old)
        rows.append(row)

    metrics = {}
    for name in mapping:
        db_key = f"delta_{name}_db"
        complex_key = f"delta_{name}_complex"
        db_values = [row[db_key] for row in rows if db_key in row]
        complex_values = [row[complex_key] for row in rows if complex_key in row]
        if db_values:
            metrics[name] = {
                "max_abs_db_delta": max(abs(value) for value in db_values),
                "rms_db_delta": math.sqrt(
                    sum(value * value for value in db_values) / len(db_values)
                ),
                "max_complex_delta": max(complex_values),
            }
    return rows, metrics


def build_model() -> tuple[mph.Client, mph.Model]:
    client = mph.start(cores=8)
    model = client.create("HFSS_equivalent_microstrip")
    jm = model.java
    jm.label("HFSS-equivalent 50-ohm FR4 microstrip")

    component = jm.component().create("comp1", True)
    geom = component.geom().create("geom1", 3)
    geom.lengthUnit("mm")

    air = geom.feature().create("air", "Block")
    air.label("Air box")
    air.set("size", ["60", "40", "26.635"])
    air.set("pos", ["-5", "-20", "-10"])

    substrate = geom.feature().create("sub", "Block")
    substrate.label("FR4 substrate")
    substrate.set("size", ["50", "20", "1.6"])
    substrate.set("pos", ["0", "-10", "0"])

    for tag, label, plane, offset, pos, size in [
        ("wp_ground", "Ground plane", "xy", "0", ["0", "-10"], ["50", "20"]),
        (
            "wp_trace",
            "Microstrip trace",
            "xy",
            "1.6",
            ["0", "-1.535"],
            ["50", "3.07"],
        ),
        (
            "wp_port1",
            "Port 1 sheet",
            "yz",
            "0",
            ["-1.535", "0"],
            ["3.07", "1.6"],
        ),
        (
            "wp_port2",
            "Port 2 sheet",
            "yz",
            "50",
            ["-1.535", "0"],
            ["3.07", "1.6"],
        ),
    ]:
        workplane = geom.feature().create(tag, "WorkPlane")
        workplane.label(label)
        workplane.set("quickplane", plane)
        workplane.set("quickz" if plane == "xy" else "quickx", offset)
        rectangle = workplane.geom().feature().create("r1", "Rectangle")
        rectangle.set("pos", pos)
        rectangle.set("size", size)

    geom.run()

    material_air = component.material().create("mat_air", "Common")
    material_air.label("Air")
    material_air.selection().set(ints([1]))
    material_air.propertyGroup("def").set("relpermittivity", "1")
    material_air.propertyGroup("def").set("relpermeability", "1")
    material_air.propertyGroup("def").set("electricconductivity", "0[S/m]")

    material_fr4 = component.material().create("mat_fr4", "Common")
    material_fr4.label("FR-4, nominal epsilon_r 4.4, tan(delta) 0.02")
    material_fr4.selection().set(ints([2]))
    material_fr4.propertyGroup("def").set("relpermittivity", "4.4")
    material_fr4.propertyGroup("def").set("relpermeability", "1")
    material_fr4.propertyGroup("def").set(
        "electricconductivity",
        "2*pi*freq*epsilon0_const*4.4*0.02",
    )

    physics = component.physics().create(
        "emw", "ElectromagneticWaves", "geom1"
    )

    port1 = physics.create("lport1", "LumpedPort", 2)
    port1.label("50-ohm lumped port 1")
    port1.selection().set(ints([10]))
    port1.set("PortName", "1")
    port1.set("PortType", "Uniform")
    port1.set("PortExcitation", "on")
    port1.set("SourceType", "Power")
    port1.set("P0", "1[W]")
    port1.set("Zref", "50[ohm]")
    port1.set("hPort", "1.6[mm]")
    port1.set("wPort", "3.07[mm]")
    port1.set("ahPort", ["0", "0", "-1"])

    port2 = physics.create("lport2", "LumpedPort", 2)
    port2.label("50-ohm lumped port 2")
    port2.selection().set(ints([16]))
    port2.set("PortName", "2")
    port2.set("PortType", "Uniform")
    port2.set("PortExcitation", "off")
    port2.set("Zref", "50[ohm]")
    port2.set("hPort", "1.6[mm]")
    port2.set("wPort", "3.07[mm]")
    port2.set("ahPort", ["0", "0", "-1"])

    pec = physics.create("pec_microstrip", "PerfectElectricConductor", 2)
    pec.label("PEC trace and ground")
    pec.selection().set(ints([8, 11]))

    scattering = physics.create("sctr1", "Scattering", 2)
    scattering.label("Open air-box boundaries")
    scattering.selection().set(ints([1, 2, 3, 4, 5, 18]))
    scattering.set("Order", "SecondOrder")

    mesh = component.mesh().create("mesh1")
    size = mesh.feature().create("size1", "Size")
    size.selection().geom("geom1", 3)
    size.selection().all()
    size.set("custom", "on")
    size.set("hmax", "2.2[mm]")
    size.set("hmin", "0.18[mm]")
    size.set("hgrad", "1.35")
    size.set("hcurve", "0.35")
    size.set("hnarrow", "0.8")
    free_tet = mesh.feature().create("ftet1", "FreeTet")
    free_tet.selection().geom("geom1", 3)
    free_tet.selection().all()

    study = jm.study().create("std1")
    frequency = study.create("freq", "Frequency")
    frequency.set(
        "plist",
        "1[GHz]" if QUICK else "range(1[GHz],0.05[GHz],10[GHz])",
    )
    return client, model


def main() -> int:
    client = None
    model = None
    try:
        client, model = build_model()
        jm = model.java
        port1_project = OUTPUT_DIR / "microstrip_comsol_port1.mph"
        port2_project = OUTPUT_DIR / "microstrip_comsol_port2.mph"
        jm.component("comp1").mesh("mesh1").run()
        jm.study("std1").run()
        model.save(port1_project)

        expressions = [
            "freq",
            "emw.S11",
            "emw.S21",
            "emw.S12",
            "emw.S22",
            "emw.Lport_1",
            "emw.Lport_2",
        ]
        port1_results = evaluate_available(model, expressions)
        frequencies = vector(port1_results.pop("freq"))

        physics = jm.component("comp1").physics("emw")
        physics.feature("lport1").set("PortExcitation", "off")
        physics.feature("lport2").set("PortExcitation", "on")
        physics.feature("lport2").set("SourceType", "Power")
        physics.feature("lport2").set("P0", "1[W]")
        jm.study("std1").run()
        model.save(port2_project)
        port2_results = evaluate_available(model, expressions)
        port2_results.pop("freq", None)

        combined = {}
        combined["emw.S11"] = port1_results.get("emw.S11")
        combined["emw.S21"] = port1_results.get("emw.S21")
        combined["emw.S12"] = port2_results.get(
            "emw.S12", port2_results.get("emw.S21")
        )
        combined["emw.S22"] = port2_results.get(
            "emw.S22", port2_results.get("emw.S11")
        )
        combined = {key: value for key, value in combined.items() if value is not None}

        hfss_rows = read_hfss_csv(HFSS_DIR / "microstrip_50ohm_full_s_matrix.csv")
        comparison_rows, metrics = align_and_compare(
            frequencies, combined, hfss_rows
        )
        comparison_csv = OUTPUT_DIR / "hfss_comsol_comparison.csv"
        with comparison_csv.open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=sorted(
                    {key for row in comparison_rows for key in row},
                    key=lambda key: (key != "frequency_hz", key),
                ),
            )
            writer.writeheader()
            writer.writerows(comparison_rows)

        summary = {
            "success": True,
            "quick_validation": QUICK,
            "comsol_version": "6.4.0.293",
            "geometry": {
                "line_length_mm": 50.0,
                "trace_width_mm": 3.07,
                "substrate_height_mm": 1.6,
                "substrate_width_mm": 20.0,
                "air_box_mm": [60.0, 40.0, 26.635],
            },
            "modeling_differences_from_hfss": [
                "COMSOL uses zero-thickness PEC trace and ground surfaces.",
                "COMSOL uses scattering boundaries; HFSS uses a Radiation boundary.",
                "COMSOL FR-4 uses epsilon_r=4.4 and tan(delta)=0.02.",
                "COMSOL directly solves every frequency; HFSS used an interpolating sweep.",
            ],
            "frequencies_hz": [float(value) for value in frequencies],
            "points": len(frequencies),
            "available_expressions_port1": sorted(port1_results),
            "available_expressions_port2": sorted(port2_results),
            "comparison_metrics": metrics,
            "port1_model": str(port1_project),
            "port2_model": str(port2_project),
            "comparison_csv": str(comparison_csv),
        }
        (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return 0
    except Exception:
        traceback.print_exc()
        print(f"FAILURE: outputs retained under {OUTPUT_DIR}")
        return 1
    finally:
        if client is not None and model is not None:
            try:
                client.remove(model)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
