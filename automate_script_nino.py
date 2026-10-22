#!/usr/bin/env python3
"""One-shot El Niño updater kept for compatibility with local launchers."""

from lottery_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main(["update", "nino", "--confirm-year", "2027"]))
