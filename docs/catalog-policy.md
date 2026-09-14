# Catalog policy

How apps get into WinMate, how they are kept correct and when they are removed.

## Inclusion criteria

An app is added when **all** of these apply:

1. It is a desktop application, runtime or command-line tool for Windows 10/11 that people commonly install on a
   new PC.
2. It is available in at least one supported package manager – preferably winget, the default.
3. The package is published by the vendor or maintained in the official community repository
   (`microsoft/winget-pkgs`, Microsoft Store, ScoopInstaller buckets or `Calinou/scoop-games`, Chocolatey
   Community Repository).
4. It is actively maintained (release or package update within roughly the last three years) or is a runtime
   that intentionally no longer changes (e.g. DirectX End-User Runtime, XNA).
5. It is not malware, adware, a crack or a tool whose main purpose is piracy.

Paid apps are allowed when they are widely used; descriptions mention subscriptions or trials.

## Package IDs

- IDs are taken from the official indexes, never guessed, and checked with `tools/validate_packages.py`.
- winget IDs are exact; Store apps use `msstore:<ProductId>`.
- Scoop IDs always include the bucket (`extras/vlc`).
- `noAdmin` is set only when a winget manifest declares `ElevationRequirement: elevationProhibited`.
- Apps with several packages (e.g. Visual C++ 2005–2022) list all IDs explicitly.

## Icons

Every icon has a reproducible source in `data/apps.json` (official Flathub icon, dashboard-icons, vendor
website or package icon) and is reviewed visually. Tools without an official square logo get a neutral
generated tile instead of a wrong logo.

## Keeping the catalog correct

- **Weekly**: the catalog-check workflow validates every ID against the official indexes, reports
  deprecated or stale Chocolatey packages and proposes updated verified versions (`data/versions.json`)
  as a pull request. Broken packages open an issue.
- **On every pull request** that touches `data/apps.json` the same check runs.
- Pinned installs use the versions from the last merged check.

## Removal

An app is removed or its package ID dropped when the package disappears from all supported sources, is
deprecated without a replacement, or the project is abandoned for several years. Removals are listed in
`CHANGELOG.md`.
