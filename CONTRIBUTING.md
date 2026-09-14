# Contributing to WinMate

Thanks for helping! The most valuable contributions are **reports of wrong or outdated packages**, new app
suggestions, security reviews and tests on real Windows installations.

- Bugs, wrong packages and app requests: [open an issue](https://github.com/baba537/WinMate/issues/new/choose)
- Security problems: see [SECURITY.md](SECURITY.md) – please report privately
- Be kind: [Code of Conduct](CODE_OF_CONDUCT.md)

## Development setup

Requirements: Python 3.11+ (standard library only), Windows PowerShell 5.1 for the engine tests,
Pillow only for `tools/fetch_icons.py`.

```bash
python build.py                       # build dist/
python tools/check_site.py            # links, IDs, hashes
python tools/test_script.py           # engine and CLI tests (Windows)
python tools/test_script.py --run     # plus safe real runs that change nothing
python -m http.server 8000 -d dist    # preview
```

## Adding or fixing an app

Read the [catalog policy](docs/catalog-policy.md) first. Then:

1. Edit `data/apps.json` (format in the [README](README.md#adding-or-fixing-an-app)).
2. `python tools/validate_packages.py --elevation` – must report 0 errors.
3. `python tools/fetch_icons.py <id>` and check the icon on the page.
4. `python build.py && python tools/check_site.py`.
5. Open a pull request. CI validates the catalog again.

## Changing the engine

`src/ps/engine.ps1` runs with administrator rights, so changes get extra scrutiny:

- keep it ASCII and compatible with Windows PowerShell 5.1
- no network access except through the package managers
- run `python tools/test_script.py --run` on Windows and describe what you tested manually
- update `CHANGELOG.md`; the engine hash changes with every edit

## Releases

1. Update `VERSION` and `CHANGELOG.md`.
2. Commit, then tag: `git tag v$(cat VERSION) && git push origin v$(cat VERSION)`.
3. The release workflow builds the files, attests them and publishes the GitHub release.

Note: every push to `main` deploys the website.
