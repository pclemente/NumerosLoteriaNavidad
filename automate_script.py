#!/usr/bin/env python3
"""One-shot Navidad updater kept for compatibility with local launchers."""

from lottery_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main(["update", "navidad", "--confirm-year", "2026"]))
