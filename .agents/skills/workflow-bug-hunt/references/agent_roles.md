# Agent Roles & Handoff Contracts

This reference defines the five roles in `workflow-bug-hunt`, their isolation modes, scale budgets, and handoff contracts.

---

## 1. Coordinator

- **Mode**: Main session agent.
- **Write Scope**: Writes `.temp/bug-hunt/scope.md` and `.temp/bug-hunt/summary.md`.
- **Context Budget Rule**: Never read all `BH-*.md` files into context at once on large repositories. Index metadata lines with `rg "^- \*\*(Location|Bug Class|Status|Verdict)\*\*:" .temp/bug-hunt/findings/`.
- **Responsibilities**:
  1. Map entrypoints from `pyproject.toml` and module boundaries from `tach.toml` (if present).
  2. Rank modules by sink density (`rg -c`) and 90-day git churn.
  3. Partition slices (`S01`, `S02`) of at most 15 files or 4,000 lines in `.temp/bug-hunt/scope.md`.
  4. Budget at most 3 scout waves (15 slices) per run starting with `Tier 1` slices. Track slice status (`PENDING | SCOUTED | TRIAGED | ARBITRATED | PATCHED`).
  5. Deduplicate candidates via `rg` indexing and triage every `RAW` finding before Stage 5. Shard `CONFIRMED` findings into batches of 8 per arbiter.
  6. Dispatch concurrent Patchers on non-overlapping targets, verify compatibility in `.temp/worktrees/integration`, run `uv sync` at root, and merge approved pull requests sequentially.

---

## 2. Scout Swarm

- **Count**: Waves of 3 to 5 parallel agents.
- **Mode**: Read-only (`research` subagent or `swarm` worker with `workspace: "inherit"`).
- **Write Scope**: Writes `.temp/bug-hunt/findings/BH-<slice>-<nn>.md` only (or returns markdown for the Coordinator to write when running as a sandboxed `research` subagent). Never edits tracked files.
- **Three Audit Lenses**: Audit boundary sinks, spec-vs-code drift (`specs/`, docstrings, types), and partial state mutation on error.
- **1-Hop Boundary & Guard Rule**: Report bugs only inside the assigned slice. Read 1-hop callers and callees to trace upstream guards and record `Upstream Guards Audited`.
- **Candidate Cap**: Emit at most 5 highest-confidence findings per scout using `templates/finding_report.md`.

---

## 3. Triage & Repro Agents

- **Mode**: Clustered detached Git worktree (`git worktree add --detach .temp/worktrees/repro-<cluster>` or `workspace: "share"`), with at most 4 active worktrees.
- **Write Scope**: Experiment inside the worktree, save tests to `<root>/.temp/bug-hunt/repro/test_bh_<slice>_<nn>.py`, and update Triage fields in `.temp/bug-hunt/findings/`. Never edit the main working tree.
- **Execution Rule**: Pin `PYTHONPATH="$PWD:$PWD/src"`, `UV_PROJECT_ENVIRONMENT="<root>/${UV_PROJECT_ENVIRONMENT:-.venv}"`, and `-c pytest.ini --rootdir="$PWD"` with `uv run --no-sync pytest --no-cov` so `.venv` is not rebuilt and `rootdir` or `fail_under = 100` does not mask results.
- **Attempt Budget**: Stop after 3 failed reproduction attempts per candidate and mark `UNREPRODUCED`.
- **Responsibilities**:
  1. Enter the assigned cluster worktree.
  2. Translate up to 4 cluster candidates into minimal failing `pytest` or `@given(...)` `hypothesis` tests (`@settings(max_examples=100, deadline=None)`) in `<root>/.temp/bug-hunt/repro/`.
  3. Record command output, stack trace, attempt count, and status (`CONFIRMED`, `UNREPRODUCED`, or `FALSE_POSITIVE`).
  4. Remove `.temp/worktrees/repro-<cluster>` immediately when the cluster finishes.

---

## 4. Arbiter

- **Count**: 1 independent agent per shard of at most 8 `CONFIRMED` findings (never reuse a scout or triage agent for its own finding).
- **Mode**: Read-only, executing batched reproducers from `.temp/bug-hunt/repro/`.
- **Write Scope**: Updates only Arbiter fields in `.temp/bug-hunt/findings/BH-<slice>-<nn>.md` (or returns verdicts for the Coordinator to write when running as a sandboxed `research` subagent).
- **Disprove-First Mandate**: Act as an adversarial disprover. Prove whether public callers can bypass upstream guards before accepting any finding.
- **Responsibilities**:
  1. Re-run the shard's `CONFIRMED` reproducers in one batch with `pytest --no-cov`.
  2. Audit each failure trace against the claimed root cause by reading target lines ±30 lines.
  3. Run the 3-step semantic variant sweep (`rg -n` and `rg -U`) across source roots for accepted root causes.
  4. Merge duplicate findings and issue `ACCEPT`, `REJECT`, or `NEEDS_MORE_EVIDENCE` (at most 1 retry round).

---

## 5. Patcher (Optional)

- **Count**: Up to 4 concurrent agents per wave (1 agent = 1 finding = 1 branch = 1 pull request).
- **Mode**: Isolated branch worktree (`git worktree add -b fix/bh-<id> .temp/worktrees/patch-<id>` or `workspace: "share"`).
- **Write Scope**: Only the target module, its in-slice sibling variants, `tests/test_<module>.py` inside `.temp/worktrees/patch-<id>`, and `.temp/bug-hunt/findings/BH-<id>.md`.
- **Patch Soundness Rule**: Fix the root cause directly within the target function without touching unrelated code. Never mask failures with broad exception handlers or silent fallback returns.
- **Responsibilities**:
  1. Implement minimal fixes inside `.temp/worktrees/patch-<id>` while preserving public API contracts.
  2. Add a typed regression test (`from __future__ import annotations`, `-> None`, `Bug / Root cause / Fix` docstring) in `tests/test_<module>.py`.
  3. Test both the blocked trigger input and valid boundary inputs with portable assertions across supported platforms.
  4. Run file-scoped `pytest -c pytest.ini --rootdir="$PWD" --no-cov`, `ruff check`, `ruff format --check`, and `pyrefly check` on modified files using `PYTHONPATH="$PWD:$PWD/src"` and `UV_PROJECT_ENVIRONMENT="<root>/${UV_PROJECT_ENVIRONMENT:-.venv}"`.
  5. Stage explicit files (`git add <files>`), commit to `fix/bh-<id>`, and remove `.temp/worktrees/patch-<id>` immediately.
  6. Push `fix/bh-<id>` (`git push -u origin fix/bh-<id>`), open a dedicated pull request (`gh pr create --head fix/bh-<id> --body-file - <<'EOF'`), and exit immediately without running `gh run watch`.
