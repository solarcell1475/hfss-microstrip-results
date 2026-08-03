# AEDT/HFSS Reproducible Model Specification

## Purpose

This document is the human-readable and machine-readable source of truth for
rebuilding the solved `microstrip_50ohm_fr4.aedt` project. It describes a
two-port, nominally 50-ohm microstrip transmission line on FR-4 and its
1–10 GHz S-parameter simulation.

The rebuild utility reads the JSON block between `AEDT_SPEC_BEGIN` and
`AEDT_SPEC_END`. Descriptive text outside that block explains the choices but
does not change the generated model.

## AEDT project structure

An `.aedt` file is AEDT's native project container. Its internal representation
is owned by Ansys and should be manipulated through AEDT/PyAEDT rather than by
editing the file as text. The logical project tree generated from this
specification is:

```text
microstrip_rebuilt_from_markdown.aedt
└── HFSS design: Microstrip50Ohm
    ├── Model
    │   ├── FR4_Substrate  (solid box, FR4_epoxy)
    │   ├── Ground         (solid box, copper)
    │   ├── Trace          (solid box, copper)
    │   ├── AirBox         (solid box, air)
    │   ├── Port1Sheet     (YZ rectangle)
    │   └── Port2Sheet     (YZ rectangle)
    ├── Boundaries
    │   └── Radiation      (assigned to AirBox outer faces)
    ├── Excitations
    │   ├── Port1          (50-ohm lumped port, renormalized)
    │   └── Port2          (50-ohm lumped port, renormalized)
    └── Analysis
        └── Setup1         (adaptive solve at 10 GHz)
            └── Sweep1     (1–10 GHz interpolating sweep, 181 points)
```

## Coordinate system and geometry

- Global Cartesian coordinates are used, with all dimensions in millimetres.
- Propagation is along +X. The line begins at X=0 and ends at X=50 mm.
- Width is along Y. The structure is centred on Y=0.
- Height is along Z.
- The substrate occupies Z=0 to 1.6 mm.
- The 35 µm ground conductor is directly below the substrate.
- The 35 µm trace is directly above the substrate.
- The air box extends 5 mm beyond both line ends, 10 mm beyond each substrate
  side, 10 mm below the ground reference plane, and to 15 mm above the top of
  the trace.

Object extents:

| Object | Origin (X, Y, Z), mm | Size (X, Y, Z), mm | Material |
|---|---:|---:|---|
| FR4_Substrate | (0, -10, 0) | (50, 20, 1.6) | FR4_epoxy |
| Ground | (0, -10, -0.035) | (50, 20, 0.035) | copper |
| Trace | (0, -1.535, 1.6) | (50, 3.07, 0.035) | copper |
| AirBox | (-5, -20, -10) | (60, 40, 26.635) | air |

The nominal substrate relative permittivity is 4.4. The AEDT library material
`FR4_epoxy` is used so all of its installed loss and dispersion properties are
retained. A zero-thickness Hammerstad estimate for W=3.07 mm, H=1.6 mm, and
εr=4.4 is 50.126 ohms.

## Boundaries and excitations

`Radiation` is assigned to the air box. Conductors use the AEDT library
`copper` material and are solved as finite-conductivity solids.

Each port is a YZ-oriented rectangle spanning only the trace width, from the
ground plane at Z=0 to the trace top at Z=1.635 mm:

- `Port1Sheet`: X=0, Y=-1.535 to +1.535 mm.
- `Port2Sheet`: X=50 mm, Y=-1.535 to +1.535 mm.
- Integration lines run downward from the trace top to ground at Y=0.
- Both ports use 50-ohm impedance and 50-ohm renormalization.

## Solver and sweep

- Solver: HFSS Modal.
- Adaptive frequency: 10 GHz.
- Maximum passes: 10.
- Minimum passes: 2.
- Minimum converged passes: 2.
- Maximum delta S: 0.02.
- Sweep: interpolating, 1–10 GHz, 181 linearly spaced points.
- Interpolation tolerance: 0.25.
- Maximum interpolation solutions: 80.
- Sweep fields are not saved.
- Solve uses 8 CPU cores.
- Export format: Touchstone two-port magnitude/angle, renormalized to 50 ohms.

No explicit local mesh operation is defined. HFSS's adaptive tetrahedral mesh
and the setup convergence criteria control mesh refinement.

## Machine-readable source of truth

<!-- AEDT_SPEC_BEGIN -->
```json
{
  "schema_version": 1,
  "application": {
    "product": "Ansys Electronics Desktop",
    "version": "2025.1",
    "solver": "HFSS",
    "solution_type": "Modal"
  },
  "project": {
    "design_name": "Microstrip50Ohm",
    "model_units": "mm"
  },
  "materials": {
    "substrate": {
      "aedt_name": "FR4_epoxy",
      "nominal_relative_permittivity": 4.4
    },
    "conductor": {
      "aedt_name": "copper"
    },
    "surrounding": {
      "aedt_name": "air"
    }
  },
  "geometry_mm": {
    "line_length": 50.0,
    "substrate_width": 20.0,
    "substrate_height": 1.6,
    "trace_width": 3.07,
    "copper_thickness": 0.035,
    "air_margin_x": 5.0,
    "air_margin_y": 10.0,
    "air_margin_below": 10.0,
    "air_margin_above_trace": 15.0
  },
  "objects": [
    {
      "name": "FR4_Substrate",
      "kind": "box",
      "material_ref": "substrate"
    },
    {
      "name": "Ground",
      "kind": "box",
      "material_ref": "conductor"
    },
    {
      "name": "Trace",
      "kind": "box",
      "material_ref": "conductor"
    },
    {
      "name": "AirBox",
      "kind": "box",
      "material_ref": "surrounding"
    }
  ],
  "boundary": {
    "name": "Radiation",
    "type": "radiation",
    "object": "AirBox"
  },
  "ports": [
    {
      "name": "Port1",
      "sheet_name": "Port1Sheet",
      "plane": "YZ",
      "x_mm": 0.0,
      "impedance_ohm": 50.0,
      "renormalize": true,
      "integration_line_direction": "trace_top_to_ground"
    },
    {
      "name": "Port2",
      "sheet_name": "Port2Sheet",
      "plane": "YZ",
      "x_mm": 50.0,
      "impedance_ohm": 50.0,
      "renormalize": true,
      "integration_line_direction": "trace_top_to_ground"
    }
  ],
  "mesh": {
    "explicit_operations": [],
    "strategy": "HFSS adaptive tetrahedral mesh controlled by Setup1"
  },
  "setup": {
    "name": "Setup1",
    "adaptive_frequency_ghz": 10.0,
    "maximum_passes": 10,
    "minimum_passes": 2,
    "minimum_converged_passes": 2,
    "max_delta_s": 0.02
  },
  "sweep": {
    "name": "Sweep1",
    "type": "Interpolating",
    "start_ghz": 1.0,
    "stop_ghz": 10.0,
    "point_count": 181,
    "save_fields": false,
    "interpolation_tolerance": 0.25,
    "interpolation_max_solutions": 80
  },
  "execution": {
    "cores": 8,
    "non_graphical": true
  },
  "export": {
    "touchstone": true,
    "renormalize": true,
    "impedance_ohm": 50.0,
    "include_gamma_impedance_comments": true
  }
}
```
<!-- AEDT_SPEC_END -->

## Reproducibility expectations

A fresh adaptive solve need not produce bit-identical results because meshing
and interpolation can vary slightly between runs. The comparison therefore
reports differences over the full complex two-port S matrix rather than
requiring byte-identical Touchstone files. Large discrepancies indicate a
geometry, material, excitation, boundary, setup, or software-version mismatch.
