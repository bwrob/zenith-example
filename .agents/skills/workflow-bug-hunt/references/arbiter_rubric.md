# Arbiter Evaluation Rubric

The arbiter acts as an independent gatekeeper between dynamic triage and final reporting or patching.
Each arbiter shard processes at most 8 `CONFIRMED` findings so context remains focused.
Every `CONFIRMED` finding must pass all four audits before receiving an `ACCEPT` verdict.

---

## 1. Adversarial Disprover & Root-Cause Alignment Audit

Adopt an adversarial disprover stance and try to falsify each finding first:

- Can an external caller reach the target line, or do `Upstream Guards Audited` reject the trigger input?
- Does the reproducer use real project types and public interfaces rather than broken mocks or bypassed constructors?
- Did the command run with `PYTHONPATH="$PWD:$PWD/src"` and `--rootdir="$PWD"` so Python imported the worktree code?
- Did the test fail on the bug assertion or unhandled exception rather than a `fail_under = 100` coverage exit code?
- Does the stack trace match the exact line and mechanism described in the finding (inspect target lines ±30 lines)?

If upstream guards block the path or the failure stems from broken fixtures or coverage settings, issue `REJECT` or `NEEDS_MORE_EVIDENCE`.

---

## 2. Deduplication & 3-Step Variant Sweep

Merge two findings into one canonical entry when any of these conditions hold:

- Both reproducers fail in the same root-cause function or missing guard.
- Fixing one finding automatically resolves the other.
- Multiple CLI or API entrypoints funnel into the same unvalidated helper.

Keep the highest-severity trigger path as the primary reproducer and list sibling entrypoints in the notes.
Run a 3-step semantic variant sweep across source roots for each accepted root cause:

1. **Extract Exact Pattern**: Identify the defective operation and missing guard in the original finding.
2. **Abstract Structural Pattern**: Generalize variable and helper names into a structural regex (`rg -n` or `rg -U`) across source roots.
3. **Triage Sibling Call Sites**: Audit each match for upstream guards and record unguarded `file:line` locations under `Sibling Variants`.

---

## 3. Severity Rating

Assign severity based on reachability from external or public boundaries and concrete impact:

| Severity | Criteria |
|---|---|
| **Critical** | Unauthenticated or untrusted input triggers arbitrary code execution, command injection, path traversal, or auth bypass. |
| **High** | Reachable bug causes data corruption, silent wrong results, privilege boundary bypass, or unhandled crash on valid input. |
| **Medium** | Bug triggers on unusual edge-case inputs, degrades availability, or leaks internal state. |
| **Low** | Minor invariant violation, resource leak on error path, or non-critical edge case with limited impact. |

---

## 4. Arbiter Verdicts

- **`ACCEPT`**: The reproducer is deterministic, and the arbiter verifies the root cause, sibling variants, and severity. Ready to report or patch.
- **`NEEDS_MORE_EVIDENCE`**: Hypothesis looks plausible, but the reproducer is flaky or relies on questionable assumptions. Return the finding to triage at most once, then issue `ACCEPT` or `REJECT`.
- **`REJECT`**: False positive, unreachable dead code, or reproducer triggers an unrelated error. Exclude from the final report.

---

## 5. Patch Soundness Audit (When Fixes Are Requested)

Verify each candidate patch against both soundness rules before approving merge:

- Verify that the patch fixes the root cause rather than swallowing exceptions or returning silent defaults.
- Verify that the regression test asserts both the blocked trigger input and adjacent valid boundary inputs.
