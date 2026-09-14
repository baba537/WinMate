<div align="center">

<img src="src/img/logo-full.png" alt="WinMate – Windows Bulk Installer" width="360">

**Reinstalled Windows? Get all your apps back in one go.**

WinMate builds one install script for Windows from 373 verified apps.<br>
Pick apps, pick a package manager, check the script, run it.

[![CI](https://github.com/baba537/WinMate/actions/workflows/ci.yml/badge.svg)](https://github.com/baba537/WinMate/actions/workflows/ci.yml)
[![Catalog check](https://github.com/baba537/WinMate/actions/workflows/catalog-check.yml/badge.svg)](https://github.com/baba537/WinMate/actions/workflows/catalog-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Apps](https://img.shields.io/badge/apps-373-orange)
![Languages](https://img.shields.io/badge/lang-EN%20%C2%B7%20DE-lightgrey)

**[→ winmate.baba537.workers.dev](https://winmate.baba537.workers.dev)** · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Roadmap](docs/ROADMAP.md)

</div>

---

## Features

**Choosing apps**
- **373 apps in 25 categories**, including runtimes such as Visual C++ Redistributables, .NET, DirectX, XNA and Java.
- **16 bundles** in three groups (Basics · Play & Create · Tech & Server). A dialog lists the apps first; untick
  what you don't want, then add the bundle, switch bundles or select only that bundle. Your own picks are
  tracked separately.
- **Profiles**: export and import your selection as JSON, share it as a link, reuse it in the CLI.
- **Keyboard first:** `/` search, arrow keys, `Space` select, `A` all visible, `C` clear, `U` undo, `B` bundles,
  `P`/`1`–`3` package manager, `S` script, `Y` copy, `D` download, `?` help.

**The script**
- **One administrator prompt** for all installers; apps that refuse elevation (e.g. Spotify) run as the normal user.
- **Install, update or uninstall**, and a **dry run** that only shows what would happen.
- **Undo script** after every install (removes only apps that run added), optional **restore point**,
  pending-reboot check and restart prompt, **proxy** setting, runtimes installed first, one retry, summary.
- **Version pinning** to the versions verified by the weekly catalog check (winget, Chocolatey).
- Run as `WinMate-Install.cmd` (double-click), `.ps1`, pasted into PowerShell – or as a **winget import file**.
- Logs and run records in `%LOCALAPPDATA%\WinMate`.

**Command line: `winmate.ps1`**

```powershell
.\winmate.ps1 -List -Search browser                 # browse the catalog
.\winmate.ps1 -Apps firefox,vlc,7zip -DryRun        # preview
.\winmate.ps1 -Bundle gaming -RestorePoint          # install a bundle
.\winmate.ps1 -ProfilePath .\winmate-profile.json -Mode upgrade
.\winmate.ps1 -Verify .\WinMate-Install.cmd         # check a downloaded script
.\winmate.ps1 -Logs                                 # run history, logs, undo scripts
```

Download it from the [latest release](https://github.com/baba537/WinMate/releases/latest) (with build
provenance) or from the website (`/winmate.ps1`). The catalog is embedded; nothing is sent anywhere.

## Trust and transparency

A tool that installs software with administrator rights has to earn trust. What WinMate does about it:

| Concern | What is in place |
|---|---|
| Is the script manipulated? | Every script contains the same engine; its SHA-256 is published. `winmate.ps1 -Verify` checks it and prints what the script will do. |
| Where do the files come from? | Releases are built by the public [release workflow](.github/workflows/release.yml) and carry a signed build provenance attestation (`gh attestation verify`). |
| Can I rebuild it? | Builds are reproducible (dates come from the commit); [CI](.github/workflows/ci.yml) builds twice and fails on any difference. `build-info.json` lists version, commit and hashes. |
| Are the packages right? | IDs are checked against the official winget, Scoop and Chocolatey indexes on every catalog change and [every week](.github/workflows/catalog-check.yml); each app page shows manifest links and verified versions. |
| Who verifies installers? | winget checks installer hashes against manifests, Chocolatey moderates and scans packages, Scoop checks manifest hashes. Details and limits in [SECURITY.md](SECURITY.md). |
| What if something breaks? | Dry run first, restore point, undo script, logs. |
| Data? | No telemetry, no cookies, no accounts. The selection stays in your browser. See the [privacy page](https://winmate.baba537.workers.dev/privacy/). |

**Honest limits:** scripts are not Authenticode-signed, there has been no independent security audit yet, and
the project has a single maintainer and was built with AI assistance. Reviews, audits and bug reports are very
welcome – see [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## How the single admin prompt works

```
WinMate-Install.cmd (normal user)
 ├─ registers winget if needed, warns about a pending restart
 ├─ starts ONE elevated PowerShell  ──►  optional restore point, installs all normal apps silently
 │                                        (they inherit the rights), writes results to %TEMP%
 ├─ runs "noAdmin" apps as the normal user (e.g. Spotify)
 ├─ prints the summary, saves run record + undo script
 └─ asks to restart if an installer needs it
```

If the script already runs as administrator, "noAdmin" apps are started as the signed-in user through a
one-time scheduled task. Scoop never needs admin rights.

## Project structure

```
data/
  apps.json          app catalog (the file you edit)
  categories.json    category names and intros (EN/DE)
  presets.json       bundles with group, pixel icon and apps (EN/DE)
  versions.json      versions verified by the catalog check
src/
  ps/engine.ps1      PowerShell engine embedded into every script
  ps/cli.ps1         template of winmate.ps1
  js/app.js          script builder (no dependencies)
  css/style.css      styles (dark/light, animations can be turned off)
  icons/, img/, fonts/
build.py             static site generator -> dist/
i18n.py, pixel.py    texts (EN/DE), pixel icons and background
tools/
  validate_packages.py   checks package IDs, records verified versions
  fetch_icons.py         downloads and normalizes icons
  test_script.py         engine and CLI tests
  check_site.py          links, IDs and hashes of the built site
docs/                    roadmap, catalog policy
.github/                 CI, catalog check, releases, issue templates
```

## Local development

Requires Python 3.11+ (standard library only).

```bash
python build.py                       # builds dist/
python tools/check_site.py
python tools/test_script.py --run     # Windows: engine and CLI tests
python -m http.server 8000 -d dist    # open http://localhost:8000
```

## Deployment

The site is hosted on Cloudflare (Workers static assets). Build command `python3 build.py`, output directory
`dist`. `_headers` (security + caching), `_redirects`, `sitemap.xml`, `robots.txt` and `llms.txt` are generated.
Set `SITE_URL` if the site moves to another domain. Every push to `main` deploys.

## Adding or fixing an app

1. Add an entry to `data/apps.json` – see the [catalog policy](docs/catalog-policy.md):

   ```json
   {"id": "vlc", "name": "VLC media player", "category": "media", "homepage": "https://www.videolan.org/vlc/",
    "winget": "VideoLAN.VLC", "scoop": "extras/vlc", "choco": "vlc", "icon": "flathub:org.videolan.VLC",
    "description": {"en": "Plays almost every audio and video format.", "de": "Spielt fast jedes Audio- und Videoformat ab."}}
   ```

   - `winget`: a string or a list of IDs. Microsoft Store apps use `msstore:<ProductId>`.
   - `scoop`: always `bucket/name`.
   - `noAdmin: true` for installers that refuse to run elevated (the validator tells you).
   - `icon`: `dash:<name>`, `flathub:<app-id>`, `url:<image-url>`, `site:<homepage>` or `gen:<text>`.
2. Run `python tools/validate_packages.py --elevation`, `python tools/fetch_icons.py <id>` (needs Pillow) and
   `python build.py`.
3. Check the icon on the page and open a pull request. More in [CONTRIBUTING.md](CONTRIBUTING.md).

## Inspiration

WinMate is inspired by [TuxMate](https://tuxmate.com/) ([abusoww/tuxmate](https://github.com/abusoww/tuxmate)),
the bulk app installer for Linux. WinMate brings the same idea to Windows with winget, Scoop and Chocolatey.
No code was copied.

## Disclaimer

WinMate was built with the help of Claude AI by Anthropic. It is not affiliated with Microsoft or any listed
software vendor. All product names, logos and trademarks belong to their respective owners. Packages are
provided by the winget, Scoop and Chocolatey communities – always review a script before running it.

## License

MIT – see [LICENSE](LICENSE).
