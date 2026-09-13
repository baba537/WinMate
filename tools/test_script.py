#!/usr/bin/env python3
"""Smoke-test the PowerShell engine without changing the system.

1. Generates scripts for winget, Scoop and Chocolatey exactly like the website does
   (via the built dist/js/app.js is not possible without a JS runtime, so the header is mirrored here).
2. Parses all of them with the PowerShell parser.
3. Optionally (--run) runs the winget variant for packages that are already installed and marked NoAdmin,
   so winget only reports "no upgrade available" and no UAC prompt is triggered.

Usage: python tools/test_script.py [--run]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = (ROOT / "src" / "ps" / "engine.ps1").read_text(encoding="utf-8")


def ps(s):
    return "'" + s.replace("'", "''") + "'"


def script(pm, apps, buckets=()):
    lines = [
        "& {",
        "    param([string]$Phase, [string]$ResultFile, [switch]$NoPause)",
        f"    $PackageManager = {ps(pm)}",
        "    $Buckets = @(" + ", ".join(ps(b) for b in buckets) + ")",
        "    $Apps = @(",
    ]
    for a in apps:
        parts = [f"Name = {ps(a['Name'])}", f"Id = {ps(a['Id'])}"]
        if a.get("Source"):
            parts.append(f"Source = {ps(a['Source'])}")
        if a.get("NoAdmin"):
            parts.append("NoAdmin = $true")
        lines.append("        @{ " + "; ".join(parts) + " }")
    lines += ["    )", ENGINE.rstrip(), "}", ""]
    return "\n".join(lines)


def cmd_wrapper(text):
    head = "\n".join([
        "<# :", "@echo off", "setlocal", "title WinMate installer", 'set "WM_SELF=%~f0"',
        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:WM_SELF); & ([ScriptBlock]::Create($s))"',
        "exit /b %errorlevel%", "#>", "",
    ])
    return (head + text).replace("\n", "\r\n")


def run_ps(code, timeout=600):
    return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code],
                          capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="winmate-test-"))
    variants = {
        "winget": script("winget", [{"Name": "Firefox", "Id": "Mozilla.Firefox"}, {"Name": "WhatsApp", "Id": "9NKSQGP7F2NH", "Source": "msstore"},
                                    {"Name": "Spotify", "Id": "Spotify.Spotify", "NoAdmin": True}]),
        "scoop": script("scoop", [{"Name": "7-Zip", "Id": "main/7zip"}, {"Name": "VLC", "Id": "extras/vlc"}], ["extras"]),
        "choco": script("choco", [{"Name": "7-Zip", "Id": "7zip"}]),
    }
    ok = True
    for name, text in variants.items():
        f = tmp / f"{name}.ps1"
        f.write_text(text, encoding="utf-8")
        r = run_ps(f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{f}', [ref]$null, [ref]$e); $e | ForEach-Object {{ $_.ToString() }}")
        status = "OK" if not r.stdout.strip() and r.returncode == 0 else "PARSE ERROR"
        ok &= status == "OK"
        print(f"{status:12} {name}  {r.stdout.strip()[:500]}")

    if "--run" in sys.argv:
        # Already installed, up-to-date packages marked NoAdmin: no elevation, no changes.
        text = script("winget", [{"Name": "VC++ 2012 x64", "Id": "Microsoft.VCRedist.2012.x64", "NoAdmin": True},
                                 {"Name": "Does not exist", "Id": "WinMate.DoesNotExist", "NoAdmin": True}])
        f = tmp / "run.ps1"
        result = tmp / "result.json"
        print("\n--- main flow (-NoPause) ---")
        f.write_text(text.rstrip()[:-1] + "} -NoPause\n", encoding="utf-8-sig")
        r = run_ps(f"& '{f}'")
        print(r.stdout[-2500:], r.stderr[-1500:])
        print("--- phase flow (-Phase user) ---")
        # Same invocation the engine writes in New-PhaseScript.
        f.write_text(text.rstrip()[:-1] + f"}} -Phase 'user' -ResultFile '{result}'\n", encoding="utf-8-sig")
        r = run_ps(f"& '{f}'")
        print(r.stderr[-800:])
        data = json.loads(result.read_text(encoding="utf-8-sig"))
        print(json.dumps(data, indent=1))
        ok &= [d["Status"] for d in data] == ["uptodate", "failed"]
        print("--- .cmd wrapper ---")
        c = tmp / "WinMate-Install.cmd"
        c.write_text(cmd_wrapper(text.replace("[switch]$NoPause)", "[switch]$NoPause = $true)")), encoding="utf-8")
        r = subprocess.run(["cmd.exe", "/c", str(c)], capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace")
        print(r.stdout[-1200:], r.stderr[-800:])
        ok &= "Summary" in r.stdout
    print("\nALL OK" if ok else "\nFAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
