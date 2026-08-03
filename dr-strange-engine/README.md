# Dr Strange Engine

Version: Framework V1.1

The Dr Strange Engine is a human-guided simulation tuning framework for HFSS,
COMSOL, and other engineering solvers. Like exploring alternative futures, the
engine evaluates several controlled tuning directions, explains their expected
responses and trade-offs, and asks the engineer to choose the next branch.

It is not an autonomous optimizer that silently changes a model. The human
remains responsible for objectives, constraints, structural direction, and
acceptance of every result.

## Core principles

1. **Show choices instead of hiding decisions.**
2. **Use one explicit mini-target per round.**
3. **Protect global constraints during local tuning.**
4. **Always provide an `Other / Custom` choice.**
5. **Explain structural parameters before changing them.**
6. **Separate predictions from solver-verified responses.**
7. **Keep every branch reversible and traceable.**
8. **Treat previous-user presets as evidence, not universal truth.**

## Human mental model

The system is presented in four layers:

```text
Intent
  What the engineer wants to improve
     ↓
Structure
  Components, features, parameters, dependencies and presets
     ↓
Execution
  HFSS/COMSOL model changes, sweeps and solves
     ↓
Evidence
  Responses, constraints, comparisons and decision history
```

## Tuning state machine

```text
UNDERSTAND_STRUCTURE
        ↓
CHOOSE_MINI_TARGET
        ↓
CONFIRM_GLOBAL_GUARDRAILS
        ↓
GENERATE_CHOICE_CARD
        ↓
HUMAN_SELECTS_BRANCH
        ↓
PLAN_SMALL_EXPERIMENT
        ↓
PREFLIGHT_VALIDATE
        ↓
RUN_SOLVER_BATCH
        ↓
VALIDATE_AND_COMPARE
        ↓
PRESENT_RESULT_CARD
        ↓
ACCEPT / REVERT / REFINE / SWITCH / CUSTOM
        └───────────────────────────────↺
```

No transition into solver execution is allowed without a recorded human
selection.

## Structure understanding

Before optimization, the engine builds a structural map:

```text
System
├── Components
├── Structural features
├── Editable parameters
├── Parameter dependencies
├── Manufacturing and physics constraints
└── Previous validated presets
```

Every editable parameter has a parameter card:

```yaml
parameter_id: edge_width
display_name: Radiating-edge width
location: Patch outer edge
current_value: 2.0
unit: mm
allowed_range: [1.2, 3.5]
linked_parameters:
  - feed_gap
  - total_patch_width
expected_responses:
  impedance_matching:
    sensitivity: high
    direction: unknown_until_local_sweep
evidence:
  - run_027
confidence: medium
```

The engine must not claim that increasing a dimension always causes a
particular RF response. Direction is geometry-dependent and must be supported
by local sensitivity data or an applicable validated preset.

## Mini-target contract

Each round has one primary measurable objective:

```yaml
mini_target:
  metric: S11
  operator: less_than
  target: -15
  unit: dB
  frequency: 2.45
  frequency_unit: GHz
```

Local tuning is evaluated against persistent guardrails:

```yaml
global_guardrails:
  - metric: realized_gain
    operator: greater_than
    target: 4
    unit: dBi
  - metric: radiation_efficiency
    operator: greater_than
    target: 70
    unit: percent
  - parameter: antenna_height
    operator: less_than
    target: 8
    unit: mm
```

A candidate that improves the mini-target but violates a guardrail is clearly
marked and cannot be recommended without explicit human override.

## Choice Card

For every round the engine presents three to five technically distinct options
plus a custom option:

| Field | Meaning |
|---|---|
| Direction | Structural family to modify |
| Parameters | Exact dimensions or properties involved |
| Rationale | Why this direction may affect the target |
| Evidence | Prior runs, RAG sources, or sensitivity data |
| Expected response | Predicted effects, with uncertainty |
| Trade-offs | Metrics that may degrade |
| Experiment | Proposed sweep or DOE |
| Cost | Estimated solver runs/resources |
| Reversible | Whether the change can be cleanly reverted |
| Confidence | Low, medium, or high |

Required choices:

```text
A. Local structural parameter sweep
B. Alternative structural direction
C. Previous validated preset
D. Coupled-parameter experiment
E. Other / Custom
F. Stop tuning
```

The engine may highlight a recommendation, but it must not preselect it.

## Experiment strategies

The human can choose among:

- **Intuition mode** — engineer selects the parameter and direction.
- **Assisted mode** — engine proposes directions; engineer selects one.
- **Local sweep** — small one-dimensional sensitivity experiment.
- **Coupled sweep** — two or more interacting parameters.
- **DOE mode** — structured design-of-experiments sampling.
- **Optimizer mode** — Bayesian or Pareto candidate generation.
- **Preset mode** — start from a validated historical configuration.
- **Custom mode** — engineer supplies the complete experiment.

One-factor-at-a-time sweeps are useful for human understanding but can miss
parameter interactions. The engine therefore recommends a coupled sweep when
the experiment ledger indicates strong interaction.

## Previous-user presets

A preset includes its applicability and provenance:

```yaml
preset_id: P03
structure_family: patch_antenna_v2
validated_band_ghz: [2.40, 2.50]
parameters:
  edge_width_mm: 2.35
  antenna_height_mm: 6.0
  feed_gap_mm: 0.45
observed_results:
  s11_at_2_45_ghz_db: -18.7
  realized_gain_dbi: 4.3
source_run: run_027
solver: HFSS
solver_version: "2025.1"
trust_level: validated
```

Before offering a preset, the engine reports:

- Structural-family similarity.
- Material, frequency, boundary, and port compatibility.
- Parameters that differ.
- Whether the preset is directly applicable or only a starting point.

Personal identities are excluded unless contributors explicitly opt in.

## Result Card

After solving, the engine shows the baseline and all candidate futures:

| Candidate | Mini-target | Guardrails | Solver status | Verdict |
|---|---:|---|---|---|
| Baseline | −11.2 dB | Pass | Converged | Reference |
| A1 | −14.8 dB | Pass | Converged | Improved |
| A2 | −18.1 dB | Pass | Converged | Recommended |
| A3 | −20.0 dB | Efficiency fail | Converged | Override required |

The human then chooses:

```text
1. Accept a candidate
2. Refine around a candidate
3. Revert to the previous accepted state
4. Change structural direction
5. Run a coupled experiment
6. Modify the target or guardrails
7. Other / Custom
8. Stop and export
```

## Proposed MCP interface

```text
dr_strange_structure_map
dr_strange_parameter_explain
dr_strange_preset_search
dr_strange_round_start
dr_strange_choice_generate
dr_strange_choice_record
dr_strange_experiment_plan
dr_strange_preflight_validate
dr_strange_result_record
dr_strange_result_card
dr_strange_branch_accept
dr_strange_branch_revert
dr_strange_session_export
```

The existing HFSS and COMSOL MCP servers remain responsible for model creation
and execution. The Dr Strange Engine stores decisions, validates plans, and
coordinates the human-in-the-loop sequence.

## Trust and self-growth

Knowledge follows three levels:

1. **Observed** — captured from a run but not trusted for recommendation.
2. **Candidate** — extracted lesson or preset awaiting regression tests.
3. **Validated** — passed benchmark checks and approved for reuse.

The engine can automatically record observations and propose candidates. It
cannot promote a recipe, modify the live MCP server, or silently alter global
constraints without approval.

## Initial benchmark

The 50-ohm FR-4 microstrip project is the first benchmark:

- Structure: line length, trace width, substrate dimensions, ports and air box.
- HFSS reference and Markdown-driven rebuild.
- COMSOL equivalent model.
- 181-point, 1–10 GHz S-matrix comparison.
- Known cross-solver formulation differences.

The first tuning exercise should vary trace width while preserving substrate,
line length, port impedance, frequency sweep, and solver convergence criteria.

## Framework acceptance criteria

The initial engine is acceptable when it can:

- Explain every editable structural parameter.
- Present multiple directions and an unrestricted custom option.
- Record an explicit mini-target and global guardrails.
- Refuse unapproved solver execution.
- Detect guardrail violations after a solve.
- Compare candidates against the accepted baseline.
- Revert any unaccepted branch.
- Retrieve presets with provenance and applicability warnings.
- Export the full Q&A and simulation decision history.
