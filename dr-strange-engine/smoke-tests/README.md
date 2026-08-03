# Dr Strange Engine smoke tests

A smoke test is a fast, shallow test that checks whether the essential workflow
is alive. It is not a full accuracy, convergence, regression, or optimization
test.

For the Dr Strange Engine, a smoke test answers:

1. Can the engine read the registered model?
2. Can it identify the solver, design, geometry, ports, variables, and setup?
3. Can it explain which structural feature a variable controls?
4. Can it detect obvious inconsistencies?
5. Can it generate valid human choices?
6. Can it stop without changing or solving the model?

## Test levels

| Level | Purpose | AEDT launch | Solve |
|---|---|---:|---:|
| S0 | Static file/inventory inspection | No | No |
| S1 | Open project read-only and verify API inventory | Yes | No |
| S2 | Minimal setup validation or one cheap solve | Yes | Optional |
| Regression | Compare complete known outputs | Yes | Yes |
| Tuning | Execute a human-approved branch | Yes | Yes |

The first registered vector permits S0 and S1 only.

## First vector: three-port waveguide tee

- [Native AEDT project](vectors/tee-waveguide/Tee.aedt)
- [Machine-readable vector definition](vectors/tee-waveguide/smoke-vector.json)

`Tee.aedt` was selected from eight locally discovered AEDT files because it is:

- Small enough for a fast test.
- Nontrivial: four geometry objects and three wave ports.
- Parametric: `offset` controls the Y position of `Septum`.
- Equipped with `Setup1` and an 8–10 GHz interpolating sweep.
- Useful for validation: its current `offset=0in` lies outside its declared
  optimization range of 0.1–0.3 in.

The file named `hfss_smoke_test.aedt` was rejected as the structural test vector
because it contains no 3D geometry. The 600 MHz magnetic-dipole project is a
strong later benchmark, but its 29 MB size and large parameter set make it
unsuitable for the first shallow test.

## Expected smoke-test sequence

```text
Verify file hash
    ↓
Read/open project without mutation
    ↓
Find TeeModel
    ↓
Extract geometry, ports, variable, setup and sweep
    ↓
Map offset → Septum.YPosition
    ↓
Report offset-range warning
    ↓
Generate target and direction choices
    ↓
Stop and export inspection report
```

Passing this smoke test does not prove that the model is physically correct or
that AEDT will converge. It only proves that the minimum human-guided structural
understanding path works.
