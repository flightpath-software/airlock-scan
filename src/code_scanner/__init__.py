"""code_scanner: thin Python helper for the shell-first ``cscan`` toolkit.

The shell layer (``bin/cscan`` + ``scripts/``) drives the user experience and runs the
external scanners. This package handles what shell is poor at: parsing each tool's
SARIF/JSON output into a unified :class:`~code_scanner.findings.Finding` model, merging
the results, rendering a summary, and applying a pass/fail severity gate.
"""

from __future__ import annotations

from code_scanner.findings import Finding, Severity

__all__ = ["Finding", "Severity", "__version__"]

__version__ = "0.2.0"
