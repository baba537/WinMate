# Roadmap

Plans change with feedback – suggestions are welcome in the [issue tracker](https://github.com/baba537/WinMate/issues).

## Done (2.2.0)

- Install, update, uninstall and dry-run modes; undo script; restore point; reboot handling; proxy
- `winmate.ps1` CLI with script verification and run history
- Profiles, winget import file, version pinning
- Public CI, reproducible builds, weekly catalog check, releases with build provenance
- Security page, threat model, catalog policy

## Next

- **Tested on clean Windows**: an automated end-to-end install run in Windows Sandbox or a CI VM, including the
  administrator path.
- **WinGet Configuration (DSC) export** (`winget configure`) for repeatable, declarative setups.
- **Scheduled updates** as an opt-in: a script that registers a weekly `winmate.ps1 -Mode upgrade` task and an
  equally simple way to remove it.
- **Better failure details**: map common installer exit codes to readable hints.
- **Accessibility review** of the website with screen readers.

## Later / ideas

- Offline packages: `winget download` into a folder plus an offline install script.
- Custom package lists that are not part of the catalog.
- More languages for the website.

## Out of scope

- Central management of many PCs (use Intune, Configuration Manager or similar).
- Hosting or mirroring installers.
- Collecting telemetry.
