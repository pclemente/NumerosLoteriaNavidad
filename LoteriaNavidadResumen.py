"""Legacy entry point: stage the complete Navidad candidate safely."""

from pathlib import Path

from lottery_pipeline import main

if __name__ == "__main__":
    destination = Path(__file__).resolve().parent / ".lottery-staging" / "navidad-2026"
    raise SystemExit(main(["stage", "navidad", "--destination", str(destination)]))
