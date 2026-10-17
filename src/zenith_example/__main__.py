"""Entry point for running zenith-example via `python -m zenith_example`."""

from zenith_example.cli import app, main

__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
