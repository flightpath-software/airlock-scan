# Security Policy

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

Report privately through GitHub's **Private Vulnerability Reporting**:

1. Go to the repository's **Security** tab → **Report a vulnerability**
   (direct link: <https://github.com/flightpath-software/code-scanner/security/advisories/new>).
2. Describe the issue, the affected version/commit, and — if possible — reproduction steps and impact.

This opens a private security advisory visible only to you and the maintainers.

### What to expect

- **Acknowledgement** within **3 business days** of your report.
- An initial assessment and a remediation plan (or a request for more information) within **10 business days**.
- For confirmed **high/critical** issues, we aim to ship a fix or documented mitigation within **30 days**.
- We practise **coordinated disclosure**: we will agree on a disclosure timeline with you and publish an advisory
  once a fix is available. Reporters are credited unless you ask to remain anonymous.

If you do not receive an acknowledgement within the window above, please re-submit — a missed notification is
far more likely than a decision to ignore a report.

## Supported versions

`code-scanner` is pre-1.0 and evolving. Security fixes are applied to the **latest release** (and the default
branch); older pre-1.0 versions are not separately patched. Once the project reaches 1.0 this policy will
define a supported range.

| Version | Supported |
|---|---|
| latest release / default branch | ✅ |
| older pre-1.0 | ❌ (upgrade to latest) |

## Security posture

`code-scanner` is a tool for vetting **untrusted** repositories and skills, so its own supply chain and
handling of untrusted input are held to a visible, checkable standard — not a promise. Here's where we are;
all of it is verifiable in this repository.

### In place today

- **The deterministic tier is authoritative and never executes the target.** `cscan` runs non-LLM scanners
  (gitleaks, semgrep, osv-scanner, guarddog, heckler) against a target as *data*, normalizes their output into
  one `Finding` model, and applies a severity gate — without running the scanned code. That core is, by
  construction, immune to prompt injection, and the advisory LLM tier can **never clear or downgrade a Tier-1
  finding** (see `docs/adr/0001-deterministic-tier-authoritative.md` and `gate.py`).
- **Untrusted content is read in a quarantine.** The optional Tier-2 reviewer is a Dual-LLM, no-functional-tools,
  one-file-per-call design with canary (NOOP) tripwires; any tool invocation is, by construction, evidence of an
  attempted injection and is logged. Tier-1-detected secrets are redacted before any Tier-2 call.
- **Reports stay local to the user.** Artifacts are written to a user-local store (`~/cscan/`), never into the
  scanned repo. The only data that leaves the machine is a deliberately-configured Tier-2 cloud call (avoidable
  with the local backend) or an explicit export (see `docs/adr/0002-local-only-reports.md`).
- **Dependency cooldown.** `uv` is pinned to a rolling **3-day** window (`exclude-newer = "3 days"`), so a
  compromised or typosquatted release has a quarantine period to be caught before it can reach our lockfile.
  The same cooldown is applied to `uvx`-run scanners via `UV_EXCLUDE_NEWER`.
- **OSV pre-install check.** Before installing an external scanner, `scripts/doctor.sh` / `install-tools.sh`
  query the [OSV database](https://osv.dev) and refuse versions with known advisories.
- **Static analysis + dependency + secret scanning on every PR.** CodeQL (`codeql.yml`) and Bandit
  (`security.yml`) scan the code; `pip-audit` (OSV) audits locked dependencies; a hardened gitleaks workflow
  (`gitleaks.yml`, pinned + checksum-verified binary) scans for secrets — all on each pull request and
  periodically, with findings surfaced in the repository's Security tab.
- **Automated dependency updates.** Dependabot watches the Python lockfile and our GitHub Actions weekly and
  opens update PRs for code-owner review.
- **Every change is reviewed and CI-gated.** The default branch and release branches are protected by branch
  rulesets: no direct pushes, no force-pushes, required human review via `CODEOWNERS`, and required status
  checks — with no bypass for anyone, maintainers included.
- **Least-privilege CI.** Workflows run with a read-only token by default and request write scopes only where a
  job genuinely needs them (e.g. uploading SARIF to code scanning).

### Planned / in progress
- **Pinning all GitHub Actions by commit SHA** (not floating tags), maintained by Dependabot.
- **A network-isolated dynamic-analysis tier** for the "suspicious-but-unclear" minority Tier-1 flags, gated
  behind a protected CI environment (see `docs/project-plan-public.md` §4.3 and `docs/future-work.md`).
- **Signed, provenance-backed releases** via PyPI Trusted Publishing if/when we publish packages.

## Scope

This policy covers the `code-scanner` package and this repository. Vulnerabilities in third-party dependencies
or in the external scanners `cscan` orchestrates should be reported upstream; if such an issue affects
`code-scanner` users, we welcome a heads-up via the private channel above so we can pin or patch.

## No warranty

The security measures described here are provided on a **best-effort basis** to improve the project's
trustworthiness. They are **not a guarantee** of security, and nothing in this policy creates a warranty or
liability beyond what the license permits. `code-scanner` is distributed **"AS IS"** under the
[Apache-2.0 LICENSE](LICENSE) — see the **Disclaimer of Warranty (§7)** and **Limitation of Liability (§8)**.
You remain responsible for assessing the software's suitability and security for your own use.
