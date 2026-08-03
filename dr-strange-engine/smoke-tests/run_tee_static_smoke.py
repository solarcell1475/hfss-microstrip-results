#!/usr/bin/env python3
"""Run the S0 static Dr Strange smoke test against Tee.aedt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_SHA256 = "4e243d6f602eab3b9e2e3efcb7b7eb6ffb99b9a212afa361a6bfd4fa62123fc8"
EXPECTED_OBJECTS = ("Tee", "Tee_1", "Tee_2", "Septum")
EXPECTED_PORTS = ("Port1", "Port2", "Port3")


def check(report: dict, check_id: str, passed: bool, evidence: str) -> None:
    report["checks"].append(
        {"check_id": check_id, "passed": passed, "evidence": evidence}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "aedt_file",
        nargs="?",
        type=Path,
        default=(
            Path(__file__).resolve().parents[1]
            / "vectors"
            / "tee-waveguide"
            / "Tee.aedt"
        ),
    )
    parser.add_argument("--vector-file", type=Path)
    args = parser.parse_args()

    data = args.aedt_file.read_bytes()
    text = data.decode(errors="replace")
    digest = hashlib.sha256(data).hexdigest()
    report = {
        "vector_id": "aedt-tee-structure-smoke-001",
        "test_level": "S0",
        "source": str(args.aedt_file),
        "checks": [],
        "findings": [],
    }

    check(report, "FILE_HASH", digest == EXPECTED_SHA256, digest)
    check(
        report,
        "DESIGN",
        "Name='TeeModel'" in text,
        "Expected design TeeModel",
    )
    check(
        report,
        "SOLUTION_TYPE",
        "SolutionType='HFSS Hybrid Modal Network'" in text,
        "Expected HFSS Hybrid Modal Network",
    )
    check(report, "MODEL_UNITS", "Units='in'" in text, "Expected inches")

    for name in EXPECTED_OBJECTS:
        check(
            report,
            f"OBJECT_{name.upper()}",
            f"Name='{name}'" in text,
            name,
        )

    for name in EXPECTED_PORTS:
        port_pattern = re.compile(
            rf"\$begin '{name}'.*?BoundType='Wave Port'.*?NumModes=1",
            re.DOTALL,
        )
        check(
            report,
            f"PORT_{name.upper()}",
            bool(port_pattern.search(text)),
            f"{name}: single-mode Wave Port",
        )

    variable = re.search(
        r"VariableProp\('offset'.*?'(?P<current>-?[\d.]+)in'.*?"
        r"Min='(?P<minimum>-?[\d.]+)in'.*?"
        r"Max='(?P<maximum>-?[\d.]+)in'",
        text,
    )
    check(report, "OFFSET_VARIABLE", variable is not None, "offset")

    dependency = "YPosition='offset-.05in'" in text
    check(
        report,
        "OFFSET_SEPTUM_DEPENDENCY",
        dependency,
        "Septum.YPosition = offset-.05in",
    )

    check(
        report,
        "SETUP",
        all(
            token in text
            for token in (
                "$begin 'Setup1'",
                "Frequency='10GHz'",
                "MaximumPasses=12",
                "MaxDeltaS=0.02",
            )
        ),
        "Setup1 at 10 GHz",
    )
    check(
        report,
        "SWEEP",
        all(
            token in text
            for token in (
                "$begin 'Sweep1'",
                "RangeStart='8GHz'",
                "RangeEnd='10GHz'",
                "RangeStep='0.05GHz'",
                "Type='Interpolating'",
            )
        ),
        "Sweep1: 8-10 GHz, 0.05 GHz step, 41 points",
    )

    if variable:
        current = float(variable.group("current"))
        minimum = float(variable.group("minimum"))
        maximum = float(variable.group("maximum"))
        outside = current < minimum or current > maximum
        if outside:
            report["findings"].append(
                {
                    "finding_id": "OFFSET_OUTSIDE_DECLARED_RANGE",
                    "severity": "warning",
                    "message": (
                        f"offset={current:g}in is outside "
                        f"[{minimum:g}, {maximum:g}]in"
                    ),
                }
            )
        check(
            report,
            "EXPECTED_RANGE_WARNING",
            outside,
            "The known warning was detected",
        )

    required_choices = {
        "A",
        "B",
        "C",
        "OTHER",
        "STOP",
    }
    vector_path = args.vector_file or args.aedt_file.with_name("smoke-vector.json")
    if vector_path.is_file():
        vector = json.loads(vector_path.read_text())
        actual_choices = {
            item["choice_id"]
            for item in vector["required_choice_card"]["direction_options"]
        }
        check(
            report,
            "CHOICE_CARD",
            required_choices.issubset(actual_choices),
            ", ".join(sorted(actual_choices)),
        )
    else:
        check(report, "CHOICE_CARD", False, f"Missing {vector_path}")

    report["passed"] = all(item["passed"] for item in report["checks"])
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
