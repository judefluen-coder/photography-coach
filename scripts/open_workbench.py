"""Skill entry point; resolves the bundled app independently of the caller's cwd."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.launcher import main


if __name__ == "__main__":
    raise SystemExit(main())
