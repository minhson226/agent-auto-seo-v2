# Phase Output Schema (v1)

Each phase is stored in a YAML file with extension `.phase.yml`.

## Required structure

```yaml
phase:
  id: "PHASE-001"                # Unique ID, incremental: PHASE-001, PHASE-002, ...
  slug: "short-kebab-title"      # Short, kebab-case, used for filenames and references
  title: "Human-readable title"  # Clear title for the phase

  summary: |                     # 2–4 sentences describing what this phase does
    ...

  goal: |                        # Single clear goal / DONE state for this phase
    ...

  from_master_spec:
    sections:                    # Which parts of the master spec this phase covers
      - "1.1 Project Overview"
      - "2.3 Functional Requirements / Login"

  scope:
    included:
      - "..."
    excluded:
      - "..."

  dependencies:                  # List of phase IDs that must be completed first
    - "PHASE-000"                # Or [] if none

  inputs:
    - name: "Existing repo"
      type: "codebase"
      location: "."
    - name: "Environment"
      type: "ci"
      location: ".github/workflows"

  outputs:
    - name: "Code changes"
      type: "code"
      description: "..."
      location_hint: "src/..."
    - name: "Tests"
      type: "tests"
      description: "..."
      location_hint: "tests/..."

  implementation_prompt: |       # Prompt that will be used by the coding agent
    (auto-generated; see template in the agent spec)

  acceptance_criteria:
    - "..."
    - "..."

  non_goals:
    - "..."

  notes:
    - "..."
```

### Required fields

The following fields are **mandatory** for each phase:

- `phase.id`
- `phase.slug`
- `phase.title`
- `phase.summary`
- `phase.goal`
- `phase.scope.included`
- `phase.outputs`
- `phase.implementation_prompt`
- `phase.acceptance_criteria`

If any of these are missing, the phase is considered **invalid**.
