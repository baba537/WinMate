# Security policy

WinMate generates PowerShell scripts that run installers with administrator rights. This document explains
what those scripts do, what protects users, the threat model, known limits and how to report a vulnerability.
A user-facing version lives at <https://winmate.baba537.workers.dev/security/>.

## Reporting a vulnerability

Please **do not open a public issue**. Report privately via
[GitHub security advisories](https://github.com/baba537/WinMate/security/advisories/new).

- You get a first response within 7 days.
- Confirmed issues are fixed in a new release; the advisory is published after the fix, with credit if you want it.
- Wrong or outdated package IDs are not security issues – use the normal [issue tracker](https://github.com/baba537/WinMate/issues).

Supported: only the latest release and the live website.

## What a generated script does

1. Runs `winget`, `scoop` or `choco` for exactly the packages in its configuration block, using exact IDs
   (`--exact`) and a fixed source (`--source winget` / `msstore`).
2. Relaunches itself **once** with administrator rights. Packages whose installer refuses elevation run as the
   signed-in user through a temporary scheduled task that is deleted afterwards. Scoop never elevates.
3. Downloads nothing from WinMate. Installers come from the locations in the package manifests.
4. Writes logs and a run record to `%LOCALAPPDATA%\WinMate\` and, after an install, an undo script that removes
   only the packages this run newly installed.
5. Sends no telemetry. The website stores the selection only in the browser's `localStorage`.

Optional behaviour is visible in the configuration block: `$Mode` (install/upgrade/uninstall), `$DryRun`,
`$RestorePoint`, `$Proxy` and pinned `Version` entries.

## Verifying scripts and releases

Every script = configuration block (`# >>> config` … `# <<< config`) + engine (`# >>> engine` … `# <<< engine`).
The engine is identical for everyone; its SHA-256 is published on the security page, in `build-info.json` and in
every GitHub release.

- `winmate.ps1 -Verify <script>` compares the engine block with the hash and prints the configuration.
- Release files (`winmate.ps1`, `engine.ps1`, site zip, `SHA256SUMS`) are built by the public
  [release workflow](.github/workflows/release.yml) and carry a build provenance attestation:
  `gh attestation verify winmate.ps1 --repo baba537/WinMate`
- The website build is reproducible: dates come from the last commit, so rebuilding a commit produces identical
  files. CI builds twice and fails if the outputs differ.

## How packages are verified

| Source | Upstream protection | Added by WinMate |
|---|---|---|
| winget | Manifests validated and scanned before merge in `microsoft/winget-pkgs`; winget checks every installer's SHA-256 against the manifest | Weekly ID check against the official index, recorded versions, optional pinning |
| Microsoft Store | Delivered and signed through the Store | – |
| Chocolatey | Community moderation, virus scanning, checksums for downloaded installers | Weekly ID check, deprecated/stale package warnings, optional pinning |
| Scoop | Hashes in manifests checked after download, buckets changed through reviewed pull requests | Weekly manifest existence check |

## Threat model

| Threat | Mitigation | Remaining risk |
|---|---|---|
| Website or hosting compromised, modified script served | Open source; reproducible build in public CI; script preview; engine hash + `-Verify` against attested release; strict CSP and security headers | Users running scripts without looking at or verifying them |
| Package source or manifest compromised | Upstream review, scanning and hash checks; optional version pinning; dry run | A malicious package accepted upstream cannot be detected by WinMate |
| Wrong or malicious ID added to the catalog | PR review; CI validation against official indexes; IDs visible on app pages and in scripts | Reviewer overlooks a look-alike ID |
| Typosquatting / ambiguous names | Exact IDs and fixed sources instead of name search | Low |
| Abuse of the elevated session | Single elevation for listed packages; no services or persistent tasks; temporary files deleted | Installers run with full rights by nature |
| Failed or unwanted installation | Optional restore point, run record, undo script, retry, logs | Undo relies on each app's uninstaller |
| Supply chain of this repository | Minimal dependencies (Python stdlib, no npm); pinned GitHub Actions major versions updated by Dependabot | Compromise of the maintainer account |

## Known limits

- Scripts are generated per selection in the browser and are therefore **not Authenticode-signed**.
- **No independent security audit** has been performed yet. Reviews are welcome.
- Single maintainer; parts of the project were written with AI assistance. All code is public for review.
- Not an enterprise deployment tool: no central management, offline mirror or compliance reporting.
