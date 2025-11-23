# Project Auto Architect – Part 1 (Phase Planner)

This repository is a **Part 1 / Phase Planner** for an automated project workflow:
from a single PDF master specification, it produces a set of **phase specs** and
per-phase **implementation prompts** that can later be consumed by a GitHub Agent
(Copilot / custom agent) to implement each phase.

## Overview

Flow for Part 1:

1. Put your main project spec PDF at:
   `docs/master-specs/project-master-spec.pdf`
2. Run the GitHub Action:
   `01 - Architecture: Split master spec into phases`.
3. The workflow will:
   - Extract the text from the PDF into `docs/phase-specs/master-spec.txt`.
   - (Optional / to be customized) Invoke a GitHub Agent that uses
     `.github/agents/architecture-planner.agent.md` to:
       - Read the extracted text.
       - Split it into multiple phases.
       - Generate YAML phase files in `docs/phase-specs/phases/`.
       - Generate `PLAN_OVERVIEW.md` and `VALIDATION_REPORT.md`.

After Part 1, you will have:

- A clear list of phases in `docs/phase-specs/PLAN_OVERVIEW.md`.
- One `.phase.yml` file per phase in `docs/phase-specs/phases/`.
- A validation report of the phases in `docs/phase-specs/VALIDATION_REPORT.md`.

## Requirements

- GitHub Actions enabled for the repository.
- Python 3.12+ (for the workflow runner) with `pypdf` installed.
- A mechanism to run a GitHub Agent (Copilot / GitHub Agents) that can read
  `.github/agents/architecture-planner.agent.md` and modify files in the repo.

The workflow file includes a placeholder step where you should plug in
your own GitHub Agent invocation command (CLI, `gh` extension, etc.).

## Usage

1. Copy this entire folder as a new Git repository or merge into your existing repo.
2. Commit and push to GitHub.
3. Upload your real project master specification PDF to:
   `docs/master-specs/project-master-spec.pdf`.
4. Go to **Actions** → `01 - Architecture: Split master spec into phases` →
   **Run workflow**, adjust inputs if needed.
5. Once the workflow finishes:
   - Check `docs/phase-specs/master-spec.txt` to see the extracted spec.
   - Use or customize the GitHub Agent step to actually generate the phases.
   - Inspect `docs/phase-specs/PLAN_OVERVIEW.md` and the `.phase.yml` files.

## Notes

- This repo focuses only on **Part 1 – Phase Planning**.
- Part 2 (Phase Executor) can iterate over the generated phase specs and
  dispatch coding tasks to another GitHub Agent using the `implementation_prompt`
  inside each phase file.
