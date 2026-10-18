#!/usr/bin/env python3
"""Pre-flight verification for built wheel distributions.

Installs the built wheel in an isolated, temporary virtual environment and
verifies that all package modules and console script entry points can be
imported cleanly without missing runtime dependencies.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def find_wheel(dist_dir: Path, explicit_path: Path | None = None) -> Path:
    """Locate the wheel file to verify, building it if none exists."""
    if explicit_path is not None:
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Specified wheel does not exist: {explicit_path}")
        return explicit_path

    dist_dir.mkdir(parents=True, exist_ok=True)
    wheels = sorted(
        dist_dir.glob("*.whl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not wheels:
        print(
            "📦 No wheel found in dist/. Building with `uv build --wheel`...",
            flush=True,
        )
        subprocess.run(["uv", "build", "--wheel"], check=True)
        wheels = sorted(
            dist_dir.glob("*.whl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not wheels:
            raise FileNotFoundError(f"No .whl files found in {dist_dir} after build.")

    return wheels[0]


def inspect_wheel(wheel_path: Path) -> tuple[str, list[str], list[str]]:
    """Inspect wheel archive to extract distribution name, python modules, and console scripts.

    Returns:
        tuple of (distribution_name, list_of_module_names, list_of_console_scripts)
    """
    with zipfile.ZipFile(wheel_path, "r") as zf:
        namelist = zf.namelist()

        # Find .dist-info directory
        dist_info = next(
            (
                name.split("/")[0]
                for name in namelist
                if name.endswith(".dist-info/")
                or "/.dist-info/" in name
                or (name.split("/")[0].endswith(".dist-info") and "/" in name)
            ),
            "",
        )

        # Extract distribution name from METADATA if available
        dist_name = ""
        metadata_file = f"{dist_info}/METADATA" if dist_info else None
        if metadata_file and metadata_file in namelist:
            metadata_content = zf.read(metadata_file).decode("utf-8", errors="replace")
            for line in metadata_content.splitlines():
                if line.startswith("Name:"):
                    dist_name = line.split(":", 1)[1].strip()
                    break

        if not dist_name:
            dist_name = wheel_path.name.split("-")[0].replace("_", "-")

        # Discover all python modules
        modules: list[str] = []
        for name in namelist:
            if name.endswith(".py"):
                parts = name.split("/")
                # Skip .dist-info and .data directories
                if parts[0].endswith(".dist-info") or parts[0].endswith(".data"):
                    continue
                if parts[-1] == "__init__.py":
                    mod_parts = parts[:-1]
                else:
                    mod_parts = parts[:-1] + [parts[-1][:-3]]
                if mod_parts:
                    modules.append(".".join(mod_parts))

        # Sort so parent packages are imported first
        modules = sorted(set(modules), key=lambda m: (m.count("."), m))

        # Discover console script entry points
        entry_points: list[str] = []
        ep_file = f"{dist_info}/entry_points.txt" if dist_info else None
        if ep_file and ep_file in namelist:
            ep_content = zf.read(ep_file).decode("utf-8", errors="replace")
            in_console_scripts = False
            for line in ep_content.splitlines():
                stripped = line.strip()
                if stripped == "[console_scripts]":
                    in_console_scripts = True
                    continue
                if stripped.startswith("["):
                    in_console_scripts = False
                    continue
                if (
                    in_console_scripts
                    and stripped
                    and not stripped.startswith("#")
                    and "=" in stripped
                ):
                    entry_points.append(stripped)

    return dist_name, modules, entry_points


def create_isolated_environment(tmp_dir: Path) -> Path:
    """Create a temporary virtual environment using uv or standard venv."""
    venv_dir = tmp_dir / ".venv"
    if shutil.which("uv") is not None:
        subprocess.run(
            ["uv", "venv", "--no-project", str(venv_dir)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    else:
        import venv

        venv.create(venv_dir, with_pip=True)

    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        raise FileNotFoundError(f"Python interpreter not found in venv at {python_exe}")
    return python_exe


def install_wheel_in_env(python_exe: Path, wheel_path: Path) -> None:
    """Install the wheel and its declared dependencies into the isolated environment."""
    if shutil.which("uv") is not None:
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python_exe),
                "--no-config",
                str(wheel_path.resolve()),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    else:
        subprocess.run(
            [str(python_exe), "-m", "pip", "install", str(wheel_path.resolve())],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


def verify_in_venv(
    python_exe: Path,
    modules: Sequence[str],
    entry_points: Sequence[str],
    cwd: Path,
) -> None:
    """Run module import and entry-point checks inside the isolated venv."""
    test_code = """
import importlib
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

modules = [m for m in sys.argv[1].split(",") if m]
entry_points = [e for e in sys.argv[2].split(",") if e]

failed = False

print(f"Testing {len(modules)} module(s)...")
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"  ✓ {mod}")
    except Exception as exc:
        print(f"  ✗ {mod}: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        failed = True

if entry_points:
    print(f"Testing {len(entry_points)} console script entry point(s)...")
    for ep_str in entry_points:
        try:
            name, target = ep_str.split("=", 1)
            name = name.strip()
            target = target.strip()
            mod_name, func_name = target.split(":", 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            if not callable(func):
                raise TypeError(f"Target '{target}' is not callable")
            print(f"  ✓ {name} -> {target}")
        except Exception as exc:
            print(f"  ✗ {ep_str}: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            failed = True

if failed:
    sys.exit(1)
"""
    result = subprocess.run(
        [
            str(python_exe),
            "-X",
            "utf8",
            "-I",
            "-c",
            test_code,
            ",".join(modules),
            ",".join(entry_points),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise RuntimeError(
            f"Wheel verification failed with exit code {result.returncode}"
        )


def run_distribution_tests(
    python_exe: Path,
    project_root: Path,
    temp_dir: Path,
) -> None:
    """Run pytest suite against the installed wheel distribution in an isolated environment."""
    print("🧪 Installing test dependencies into isolated environment...")
    test_packages = [
        "hypothesis>=6.125.0",
        "pytest>=9.0.0",
        "pytest-cov>=7.0.0",
        "pytest-randomly>=3.16.0",
        "pytest-sugar>=1.0.0",
        "pytest-xdist>=3.8.0",
        "syrupy>=6.1.0",
    ]
    if shutil.which("uv") is not None:
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python_exe),
                "--no-config",
                *test_packages,
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    else:
        subprocess.run(
            [
                str(python_exe),
                "-m",
                "pip",
                "install",
                *test_packages,
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        print(f"ℹ️ No tests directory found at {tests_dir}; skipping test execution.")
        return

    print("🚀 Executing pytest against installed wheel distribution...")
    env = os.environ.copy()
    env["PYTHONWARNDEFAULTENCODING"] = "1"
    pytest_ini = project_root / "pytest.ini"
    cmd = [
        str(python_exe),
        "-I",
        "-m",
        "pytest",
    ]
    if pytest_ini.is_file():
        cmd.extend(["-c", str(pytest_ini.resolve())])
    cmd.extend(
        [
            "-o",
            f"testpaths={tests_dir.resolve()}",
            str(tests_dir.resolve()),
        ]
    )
    result = subprocess.run(
        cmd,
        cwd=str(temp_dir),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise RuntimeError(
            f"Distribution pytest execution failed with exit code {result.returncode}"
        )
    print("✅ Distribution test suite passed successfully!")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify clean module imports and entry points in a built wheel.",
    )
    parser.add_argument(
        "wheel",
        nargs="?",
        type=Path,
        default=None,
        help="Path to .whl file (default: newest file in dist/)",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory to search for wheels (default: dist/)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run pytest test suite against the installed distribution in the isolated environment",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Preserve temporary virtual environment for inspection",
    )
    args = parser.parse_args(argv)

    try:
        wheel_path = find_wheel(dist_dir=args.dist_dir, explicit_path=args.wheel)
        print(f"🔍 Inspecting wheel: {wheel_path}")
        _dist_name, modules, entry_points = inspect_wheel(wheel_path)

        if not modules:
            print(f"⚠️ Warning: No Python modules found in {wheel_path.name}")

        temp_dir = Path(tempfile.mkdtemp(prefix="wheel_verify_"))
        try:
            print("📦 Installing into isolated virtual environment...")
            python_exe = create_isolated_environment(temp_dir)
            install_wheel_in_env(python_exe, wheel_path)

            print("🧪 Verifying module imports and entry points...")
            verify_in_venv(python_exe, modules, entry_points, cwd=temp_dir)
            print(
                f"✅ Wheel verification successful! All {len(modules)} module(s) and "
                f"{len(entry_points)} entry point(s) imported cleanly."
            )

            if args.run_tests:
                project_root = Path(__file__).resolve().parent.parent
                run_distribution_tests(python_exe, project_root, temp_dir)

            return 0
        finally:
            if args.no_cleanup:
                print(f"ℹ️ Temporary environment preserved at: {temp_dir}")
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as exc:
        print(f"❌ Verification failed: {exc}", file=sys.stderr)
        guidance = (
            "\n💡 Diagnostic guidance:\n"
            "  - Missing dependencies? Check [project.dependencies] in pyproject.toml.\n"
            "  - For packaging workflows, see .agents/skills/tool-uv/SKILL.md.\n"
            "  - For architecture layer contracts, see .agents/skills/tool-tach/SKILL.md.\n"
        )
        print(guidance, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
