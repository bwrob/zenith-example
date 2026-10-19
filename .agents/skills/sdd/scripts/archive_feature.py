#!/usr/bin/env python3
"""Archive approved feature specifications from .specs/ into permanent docs/specs/.

Implements the OpenSpec 'Propose -> Apply -> Archive' pattern:
1. Validates that .specs/<feature-id>/review.md declares an Approved verdict.
2. Copies spec.md, plan.md, and review.md into docs/specs/<feature-id>/.
3. Registers the feature in docs/specs/index.md for long-term project memory.
4. Removes the temporary .specs/<feature-id>/ directory.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def archive_feature(
    feature_id: str,
    specs_root: Path = Path(".specs"),
    docs_root: Path = Path("docs/specs"),
    *,
    force: bool = False,
    keep_temp: bool = False,
) -> int:
    """Archive approved feature specification into permanent documentation."""
    try:
        resolved_specs = specs_root.resolve()
        resolved_source = (specs_root / feature_id).resolve()
        if not resolved_source.is_relative_to(resolved_specs) or resolved_source == resolved_specs:
            print(f"❌ Security violation: invalid feature identifier '{feature_id}' traverses outside {specs_root}", file=sys.stderr)
            return 1
    except (ValueError, RuntimeError):
        print(f"❌ Invalid path for feature directory: {specs_root / feature_id}", file=sys.stderr)
        return 1

    source_dir = resolved_source
    if not source_dir.is_dir():
        print(f"❌ Feature directory not found: {source_dir}", file=sys.stderr)
        return 1

    review_file = source_dir / "review.md"
    if not force:
        if not review_file.is_file():
            print(f"❌ Cannot archive: missing review report at {review_file}. Pass --force to bypass.", file=sys.stderr)
            return 1

        review_content = review_file.read_text(encoding="utf-8")
        if not re.search(r"\*{0,2}Verdict\*{0,2}:\s*Approved(?!\s*\|)", review_content, re.IGNORECASE):
            print("❌ Cannot archive: review.md verdict is not 'Approved'. Pass --force to bypass.", file=sys.stderr)
            return 1

    target_dir = docs_root / feature_id
    target_dir.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    for filename in ("spec.md", "plan.md", "review.md"):
        src = source_dir / filename
        if src.is_file():
            dst = target_dir / filename
            shutil.copy2(src, dst)
            copied_files.append(filename)

    # Register in docs/specs/index.md
    index_file = docs_root / "index.md"
    if not index_file.is_file():
        index_file.write_text(
            "# Feature Specifications Registry\n\n"
            "Permanent archive of approved and delivered Spec-Driven Development (SDD) features.\n\n"
            "| Feature Identifier | Specification | Implementation Plan | Review Audit |\n"
            "| :--- | :--- | :--- | :--- |\n",
            encoding="utf-8",
        )

    index_content = index_file.read_text(encoding="utf-8")
    entry_line = (
        f"| `{feature_id}` | [spec.md](./{feature_id}/spec.md) | "
        f"[plan.md](./{feature_id}/plan.md) | [review.md](./{feature_id}/review.md) |\n"
    )

    if f"`{feature_id}`" not in index_content:
        with open(index_file, "a", encoding="utf-8") as f:
            if index_content and not index_content.endswith("\n"):
                f.write("\n")
            f.write(entry_line)

    if not keep_temp:
        shutil.rmtree(source_dir)

    print(f"✓ Archived feature '{feature_id}' to {target_dir} ({', '.join(copied_files)})")
    print(f"✓ Registered in {index_file}")
    if not keep_temp:
        print(f"✓ Cleaned up temporary directory {source_dir}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for feature specification archival."""
    parser = argparse.ArgumentParser(
        description="Archive approved feature specifications from .specs/ into docs/specs/."
    )
    parser.add_argument("feature_id", type=str, help="Feature identifier (e.g. user-auth, csv-export)")
    parser.add_argument("--specs-dir", type=Path, default=Path(".specs"), help="Path to .specs directory")
    parser.add_argument("--docs-dir", type=Path, default=Path("docs/specs"), help="Path to docs/specs directory")
    parser.add_argument("--force", action="store_true", help="Bypass requirement for Approved review verdict")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files in .specs/ after archiving")
    args = parser.parse_args(argv)

    return archive_feature(
        feature_id=args.feature_id,
        specs_root=args.specs_dir,
        docs_root=args.docs_dir,
        force=args.force,
        keep_temp=args.keep_temp,
    )


if __name__ == "__main__":
    sys.exit(main())
