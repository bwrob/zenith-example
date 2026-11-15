# Bug Hunt Finding Report Template

Store each finding at `.temp/bug-hunt/findings/BH-<slice>-<nn>.md` and update sections in place across stages.
Keep `- **Location**:`, `- **Bug Class**:`, `- **Status**:`, and `- **Verdict**:` at the top level so `rg` indexes findings cleanly.

---

## Summary Table

| ID | Slice | Title | Location | Severity | Triage Status | Arbiter Verdict |
|---|---|---|---|---|---|---|
| `BH-S01-01` | `S01` | `<short-title>` | `<path>:<line>` | `<Critical\|High\|Medium\|Low>` | `<CONFIRMED\|UNREPRODUCED\|FALSE_POSITIVE>` | `<ACCEPT\|REJECT\|NEEDS_MORE_EVIDENCE>` |

---

## Finding Detail (`BH-<slice>-<nn>`)

- **Title**: `<concise summary of the bug or vulnerability>`
- **Slice**: `S<nn>`
- **Location**: `<file_path>:<start_line>-<end_line>` (`<symbol_name>`)
- **Bug Class**: `<input-validation | injection | path-traversal | concurrency | state | resource-leak | logic>`
- **Status**: `<RAW | CONFIRMED | UNREPRODUCED | FALSE_POSITIVE>`
- **Verdict**: `<PENDING | ACCEPT | REJECT | NEEDS_MORE_EVIDENCE>`
- **Severity**: `<Critical | High | Medium | Low>`
- **Scout Hypothesis**:
  - **Bug Lens**: `<sink-boundary | spec-drift | state-corruption>`
  - **Entrypoint**: `<public function, CLI command, or API route>`
  - **Upstream Guards Audited**: `<1-hop callers inspected and why they do not block the trigger input>`
  - **Trigger Input**: `<concrete input or state sequence>`
  - **Suspected Root Cause**: `<why the current code fails>`
- **Triage & Reproducer**:
  - **Attempts**: `<1 | 2 | 3>`
  - **Worktree**: `.temp/worktrees/repro-<cluster>/`
  - **Repro File**: `.temp/bug-hunt/repro/test_bh_<slice>_<nn>.py`
  - **Repro Command**: `PYTHONPATH="$PWD:$PWD/src" UV_PROJECT_ENVIRONMENT="<root>/${UV_PROJECT_ENVIRONMENT:-.venv}" uv run --no-sync pytest -c pytest.ini --rootdir="$PWD" --no-cov <root>/.temp/bug-hunt/repro/test_bh_<slice>_<nn>.py`
  - **Observed Output**: `<exact error, assertion failure, or unexpected output>`
- **Arbiter Review**:
  - **Disprover Notes**: `<why upstream guards and type contracts failed to block the trigger path>`
  - **Sibling Variants**: `<none | list of file_path:line sharing the same root cause>`
  - **Rationale**: `<root-cause alignment audit and deduplication notes>`
- **Candidate Fix (If Requested)**:
  - **Patch Worktree & Branch**: `.temp/worktrees/patch-<slice>-<nn>/` (`fix/bh-<slice>-<nn>`)
  - **Patch Summary**: `<minimal change description including sibling variants>`
  - **Regression Test**: `<tests/test_<module>.py::test_name>`
  - **Soundness Check**: `<how the regression test covers both the trigger input and valid boundary inputs>`
