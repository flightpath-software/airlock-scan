"""Enable ``python -m code_scanner`` (delegates to the CLI)."""

from __future__ import annotations

import sys

from code_scanner.cli import main

if __name__ == "__main__":
    sys.exit(main())
