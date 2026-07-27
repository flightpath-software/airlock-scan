"""Enable ``python -m airlock_scan`` (delegates to the CLI)."""

from __future__ import annotations

import sys

from airlock_scan.cli import main

if __name__ == "__main__":
    sys.exit(main())
