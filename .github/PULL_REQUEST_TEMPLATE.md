<!--
Thanks for the PR! Keep this short — fill in what applies, delete what doesn't.
-->

## Summary
<!-- What does this change, and why? One or two sentences is plenty. -->

## Closes
<!--
If this closes a tracked issue, put it here as `Closes #N` — not in the description
above. Leave as "N/A" if there's no tracked issue.
-->
N/A

## Changelog
<!--
Does this change user-facing behavior (feature, fix, scanner, CLI change,
deprecation, removal, security)? Add a fragment under `changelog.d/` — run
`cscan changelog` or see docs/changelog.md. If not (docs/CI/refactor/tests only),
apply the `skip-changelog` label instead.
-->

## Verification
<!--
Attest what a HUMAN checked. AI assistance is assumed on this project and isn't the point —
what matters is that a person verified the change. Delete lines that don't apply; for a
docs/CI-only PR, "N/A — no runtime change" is fine.
-->
- [ ] I ran lint + tests locally and they pass (`uv run ruff check .` && `uv run pytest -q`).
- [ ] Shell entry points still parse (`bash -n bin/cscan scripts/*.sh scripts/lib/*.sh scanners/*.sh`).
- [ ] I reviewed every line of this diff and can explain why each change is correct.
- [ ] New/changed behavior is covered by tests (or this is docs/CI/refactor-only).
