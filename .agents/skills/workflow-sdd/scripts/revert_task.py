#!/usr/bin/env python3
"""Revert a completed SDD task by commit SHA and reset its status in plan.md.

Implements safe rollback of flawed or rejected tasks:
1. Identifies the target task in .specs/<feature-id>/plan.md by recorded SHA or selects the most recent completed task.
2. Verifies the commit exists in Git.
3. Executes a clean `git revert --no-edit <sha>`.
4. Resets the task status from [x] back to [ ] in plan.md.
5. Commits the plan update.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TaskRevertTarget:
    """Metadata for a task targeted for Git reversion."""

    task_title: str
    sha: str
    original_line: str
    reset_line: str


def find_revertable_tasks(plan_content: str) -> list[TaskRevertTarget]:
    """Parse plan.md content to find all completed tasks with recorded commit SHAs."""
    targets: list[TaskRevertTarget] = []
    # Matches: - [x] **Task 1: Title** (a1b2c3d) or - [x] Task 1: Title (a1b2c3d)
    pattern = re.compile(
        r"^([ \t]*-\s*\[x\]\s*(.+?))\s*\(([0-9a-fA-F]{7,40})\)[ \t]*$",
        re.MULTILINE,
    )

    for match in pattern.finditer(plan_content):
        full_line = match.group(0)
        prefix_and_title = match.group(1)
        task_title = match.group(2).strip()
        sha = match.group(3).strip()

        # Build reset line: replace [x] with [ ] and strip the (sha) suffix
        reset_line = re.sub(r"-\s*\[x\]", "- [ ]", prefix_and_title)

        targets.append(
            TaskRevertTarget(
                task_title=task_title,
                sha=sha,
                original_line=full_line,
                reset_line=reset_line,
            )
        )

    return targets


def revert_task(
    feature_id: str,
    target_sha: str | None = None,
    specs_root: Path = Path(".specs"),
    repo_root: Path | None = None,
    *,
    dry_run: bool = False,
) -> int:
    """Revert a task commit and reset its status in plan.md."""
    try:
        resolved_specs = specs_root.resolve()
        resolved_source = (specs_root / feature_id).resolve()
        if not resolved_source.is_relative_to(resolved_specs) or resolved_source == resolved_specs:
            print(f"❌ Security violation: invalid feature identifier '{feature_id}' traverses outside {specs_root}", file=sys.stderr)
            return 1
    except (ValueError, RuntimeError):
        print(f"❌ Invalid path for feature directory: {specs_root / feature_id}", file=sys.stderr)
        return 1

    effective_repo = repo_root.resolve() if repo_root is not None else resolved_specs.parent

    plan_file = resolved_source / "plan.md"
    if not plan_file.is_file():
        print(f"❌ Implementation plan not found: {plan_file}", file=sys.stderr)
        return 1

    try:
        plan_content = plan_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"❌ Failed to read plan file: {exc}", file=sys.stderr)
        return 1

    targets = find_revertable_tasks(plan_content)
    if not targets:
        print(
            f"❌ No completed tasks with recorded commit SHAs found in {plan_file}.\n"
            "   Ensure completed tasks are recorded as '- [x] Task Title (<sha>)'.",
            file=sys.stderr,
        )
        return 1

    selected_target: TaskRevertTarget | None = None
    if target_sha:
        clean_sha = target_sha.strip().lower()
        for t in targets:
            if t.sha.lower().startswith(clean_sha) or clean_sha.startswith(t.sha.lower()):
                selected_target = t
                break
        if not selected_target:
            print(f"❌ No task with recorded commit SHA matching '{target_sha}' found in {plan_file}.", file=sys.stderr)
            return 1
    else:
        # Default to the most recent completed task (last in document)
        selected_target = targets[-1]

    # Verify commit exists in git
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", f"{selected_target.sha}^0"],
        capture_output=True,
        text=True,
        check=False,
        cwd=effective_repo,
    )
    if proc.returncode != 0:
        print(f"❌ Commit '{selected_target.sha}' does not exist in local Git history.", file=sys.stderr)
        return 1

    if dry_run:
        print(f"[Dry Run] Would revert commit '{selected_target.sha}' for task '{selected_target.task_title}'.")
        print(f"[Dry Run] Would update {plan_file} to reset task status to pending: [ ].")
        return 0

    # Execute git revert
    revert_proc = subprocess.run(
        ["git", "revert", "--no-edit", selected_target.sha],
        capture_output=True,
        text=True,
        check=False,
        cwd=effective_repo,
    )
    if revert_proc.returncode != 0:
        subprocess.run(["git", "revert", "--abort"], capture_output=True, check=False, cwd=effective_repo)
        print(
            f"❌ Failed to revert commit {selected_target.sha} due to conflict.\n"
            "   Revert aborted to preserve clean repository state.\n"
            f"   Details: {revert_proc.stderr.strip() or revert_proc.stdout.strip()}",
            file=sys.stderr,
        )
        return 1

    # Update plan.md
    updated_content = plan_content.replace(
        selected_target.original_line,
        selected_target.reset_line,
        1,
    )
    try:
        plan_file.write_text(updated_content, encoding="utf-8")
    except OSError as exc:
        print(f"❌ Failed to write updated plan: {exc}", file=sys.stderr)
        return 1

    # Commit plan reset
    subprocess.run(["git", "add", str(plan_file)], check=False, cwd=effective_repo)
    subprocess.run(
        ["git", "commit", "-m", f"docs(plan): reset '{selected_target.task_title}' after revert of {selected_target.sha}"],
        capture_output=True,
        check=False,
        cwd=effective_repo,
    )

    print(f"✓ Successfully reverted commit {selected_target.sha} for task '{selected_target.task_title}'")
    print(f"✓ Reset task status to pending in {plan_file}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for SDD task revert."""
    parser = argparse.ArgumentParser(
        description="Revert a completed SDD task commit and reset its status in plan.md."
    )
    parser.add_argument("feature_id", type=str, help="Feature identifier (e.g. user-auth)")
    parser.add_argument("sha", nargs="?", default=None, help="Optional commit SHA to revert (defaults to last completed task)")
    parser.add_argument("--specs-dir", type=Path, default=Path(".specs"), help="Path to .specs directory")
    parser.add_argument("--repo-dir", type=Path, default=None, help="Path to Git repository root")
    parser.add_argument("--dry-run", action="store_true", help="Inspect revert target without executing git revert")
    args = parser.parse_args(argv)

    return revert_task(
        args.feature_id,
        target_sha=args.sha,
        specs_root=args.specs_dir,
        repo_root=args.repo_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
