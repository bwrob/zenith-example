#!/usr/bin/env python3
"""Deterministic structural linter for ASD-STE100 Simplified Technical English.

Modularized and adapted for Zenith repository conventions, reflowed Markdown,
GitHub alerts, Zensical admonitions, frontmatter descriptions, and inline suppressions.

Original creator: Dustin Yuchen Teng (https://github.com/danyuchn/asd-ste100-skill)
Licensed under the MIT License.
"""

import sys
from pathlib import Path

# Ensure 'scripts' is on sys.path so 'import ste' works when executed directly
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ste.cli import main

if __name__ == "__main__":
    sys.exit(main())
