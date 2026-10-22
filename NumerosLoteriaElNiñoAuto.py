"""Legacy entry point: stage the complete El Niño candidate safely."""

from pathlib import Path

from lottery_pipeline import main

if __name__ == "__main__":
    destination = Path(__file__).resolve().parent / ".lottery-staging" / "nino-2027"
    raise SystemExit(main(["stage", "nino", "--destination", str(destination)]))
