# code-scanner

A **shell-first, `uv`-native** toolkit for scanning repositories for supply-chain and
injection attacks — **before** you fully install them, and **before** you give an LLM/agent
access to them.

The common workflow: you clone or download a repo (a dependency, a sample, something an agent
wants to read) and run `cscan` against it first. It orchestrates several best-in-class scanners,
aggregates their findings into one report, and gives you a pass/fail verdict so you can decide
whether it's safe to install or expose to an LLM.

## How it works

- **Primary UX is shell** — interactive [`gum`](https://github.com/charmbracelet/gum)-driven
  scripts under `scripts/`, launched via `bin/cscan`.
- **A thin Python helper** (import package `code_scanner`, managed entirely by `uv`) does the
  part shell is bad at: parsing each tool's SARIF/JSON output, merging it into a unified
  report, and applying a severity gate.
- **External scanners run in isolation** — Go binaries via Homebrew, Python tools via `uvx`
  (ephemeral), so nothing heavy is baked into this project's environment.

## Scanners orchestrated

| Tool | Detects | How it's run |
| --- | --- | --- |
| [gitleaks](https://github.com/gitleaks/gitleaks) | secrets / credentials | `brew` binary |
| [semgrep](https://semgrep.dev) | SAST / pattern rules | `uvx semgrep` |
| [osv-scanner](https://github.com/google/osv-scanner) | vulnerable dependencies (CVEs) | `brew` binary |
| [guarddog](https://github.com/DataDog/guarddog) | malicious PyPI/npm packages | `uvx guarddog` |
| [heckler](https://pypi.org/project/heckler/) | invisible-unicode / trojan-source / Glassworm / tag-char prompt-injection | `uvx heckler` |
| anti-trojan-source *(optional)* | trojan-source (second opinion) | `npx` (user-provided) |

## Requirements

- **uv ≥ 0.11.8** (`uv self update`) — required for the 3-day supply-chain cooldown.
- **gum** — `brew install gum`
- **Homebrew** — for `gitleaks` and `osv-scanner`
- Python **3.12+** (uv will manage it)
- *(optional)* Node/`npx` if you enable the `anti-trojan-source` adapter

Run `scripts/doctor.sh` (or `cscan` → *Doctor*) to check what's installed.

## Quick start

```bash
# 1. Install/verify the external scanners (detects + offers to install)
bin/cscan            # then choose "Install / check tools"

# 2. Scan a target repository
bin/cscan            # then choose "Scan a repo" and point it at a path

# Non-interactive equivalents also work, e.g.:
scripts/scan.sh /path/to/target
```

Each scan writes raw tool output into `<target>/.cscan/` (git-ignored), then the helper merges
it and prints a summary, exiting non-zero if findings exceed the configured severity gate.

## Supply-chain cooldown (the 3-day rule)

To avoid pulling freshly published — and not-yet-detected — malicious releases, `uv` is
configured in [`pyproject.toml`](pyproject.toml) to **never resolve a distribution younger than
3 days**:

```toml
[tool.uv]
required-version = ">=0.11.8"
exclude-newer = "3 days"
```

- The same cooldown is applied to `uvx`-run scanners because `scripts/shell-setup.sh` exports
  `UV_EXCLUDE_NEWER="3 days"`.
- Need an urgent CVE fix sooner? Exempt a single package with
  `exclude-newer-package = { somepkg = false }`.
- Before installing any external tool, `scripts/doctor.sh` / `scripts/install-tools.sh` query
  the [OSV database](https://osv.dev) and refuse versions with known advisories.

## Layout

```
bin/cscan            # gum launcher (main entry point)
scripts/             # gum-driven shell UX + shared libs
scanners/            # one adapter per tool (detect / install / run)
config/scanners.toml # declarative tool registry
src/code_scanner/    # thin Python helper (parse + merge + report)
tests/               # helper tests
```

## Development

```bash
uv sync                       # resolve under the 3-day cooldown
uv run cscan-helper --help    # the Python helper CLI
uv run pytest                 # tests
uv run ruff check .           # lint
```

Dependencies are always managed with `uv add` / `uv add --dev` so `pyproject.toml` and
`uv.lock` stay in sync.

## Contributing: commits, changelog & releases

### Sample Flow

**Step 1**: One-time setup: turn on the commit template
This makes git (and Tower) pre-fill the Conventional Commits guidance whenever you commit.
```bash
git config commit.template .gitmessage.txt
```

**Step 2**: See what you're about to commit
```bash
git status
```
Files shown in red are untracked (brand new) or modified but not yet staged. To see a summary of changes to already-tracked files:

**Step 3**: Stage the changes
"Staging" selects what goes into the next commit. To stage everything (new, modified, deleted):
```bash
git add -A
```

**Step 4** — Write the commit (pick ONE method)
Method A — Guided, with commitizen (recommended!)
```bash
uv run cz commit
```
It asks a series of questions. Example answers for a feature commit.
•  type: feat
•  scope: (leave blank, press Enter)
•  summary: scaffold shell-first cscan toolkit
•  longer description (body): (optional) uv-native package + gum scripts orchestrating gitleaks/semgrep/osv-scanner/guarddog/heckler, 3-day cooldown, towncrier+commitizen changelog, CI guards
•  breaking change? no
•  issues / footer: (leave blank)

### The Docs Have More Use Cases (Tower, etc.)
See [docs/commits.md](docs/commits.md).

### Nutshell
- **Every change adds a news fragment** under [`changelog.d/`](changelog.d/) via
  `cscan changelog`; the human-readable `CHANGELOG.md` is compiled by towncrier.
  See [docs/changelog.md](docs/changelog.md).
- **Releases:** `cscan release` builds the changelog, then bumps and tags the
  version (keeping `pyproject.toml` and `uv.lock` in sync) via commitizen.
- **CI** ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs lint + tests,
  and on PRs guards that a changelog fragment exists (`towncrier check`) and that
  commit messages are valid (`cz check`).

## TODO

- Choose and add a `LICENSE` before any public distribution (currently `license = "TODO"`).
- Populate custom `semgrep` rules under `config/semgrep/`.
- Optional: add a CI step that self-scans this repo with `cscan`.
