#!/usr/bin/env python3
"""Check every package ID in data/apps.json against the real repositories.

  winget      official source index (cdn.winget.microsoft.com/cache/source2.msix)
  Scoop       manifests in the ScoopInstaller buckets and Calinou/scoop-games
  Chocolatey  community.chocolatey.org OData API
  msstore     skipped (needs winget: `winget show --id <id> -s msstore`)

Usage:
  python tools/validate_packages.py            # report problems, exit code 1 if something is missing
  python tools/validate_packages.py --elevation  # also read winget manifests and report ElevationRequirement

Standard library only. Downloads are cached in .cache/ for one day.
"""
import concurrent.futures as cf
import difflib
import io
import json
import re
import sqlite3
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
UA = {"User-Agent": "WinMate-validator (+https://github.com/baba537/WinMate)"}
BUCKETS = {
    "main": "ScoopInstaller/Main", "extras": "ScoopInstaller/Extras", "versions": "ScoopInstaller/Versions",
    "java": "ScoopInstaller/Java", "nonportable": "ScoopInstaller/Nonportable", "games": "Calinou/scoop-games",
}


def fetch(url, cache_name=None, max_age=86400, timeout=120):
    if cache_name:
        p = CACHE / cache_name
        if p.exists() and time.time() - p.stat().st_mtime < max_age:
            return p.read_bytes()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        data = r.read()
    if cache_name:
        CACHE.mkdir(exist_ok=True)
        (CACHE / cache_name).write_bytes(data)
    return data


def winget_index():
    data = fetch("https://cdn.winget.microsoft.com/cache/source2.msix", "source2.msix")
    db_path = CACHE / "winget-index.db"
    db_path.write_bytes(zipfile.ZipFile(io.BytesIO(data)).read("Public/index.db"))
    con = sqlite3.connect(db_path)
    rows = {r[0]: (r[1], r[2]) for r in con.execute("select id, name, latest_version from packages")}
    con.close()
    return rows


def scoop_manifests():
    found = {}
    for bucket, repo in BUCKETS.items():
        tree = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1", f"scoop-{bucket}.json"))
        for item in tree.get("tree", []):
            m = re.match(r"bucket/(.+)\.json$", item["path"])
            if m:
                found[f"{bucket}/{m.group(1)}".lower()] = f"{bucket}/{m.group(1)}"
    return found


def choco_package(pid):
    url = f"https://community.chocolatey.org/api/v2/Packages()?$filter=tolower(Id)%20eq%20'{pid.lower()}'%20and%20IsLatestVersion"
    for attempt in range(3):
        try:
            x = fetch(url, timeout=60).decode("utf-8", "replace")
            if "<entry>" not in x:
                return None
            title = re.search(r"<d:Title>(.*?)</d:Title>", x)
            published = re.search(r"<d:Published[^>]*>(.*?)</d:Published>", x)
            return {"title": title.group(1) if title else "", "published": (published.group(1) if published else "")[:10]}
        except Exception as e:  # network hiccup, retry
            err = e
            time.sleep(2)
    return {"error": str(err)}


def winget_elevation(pid, version):
    path = "/".join(pid.split("."))
    url = f"https://raw.githubusercontent.com/microsoft/winget-pkgs/master/manifests/{pid[0].lower()}/{path}/{version}/{pid}.installer.yaml"
    try:
        y = fetch(url, timeout=30).decode("utf-8", "replace")
        return sorted(set(re.findall(r"ElevationRequirement:\s*(\S+)", y)))
    except Exception as e:
        return [f"error: {e}"]


def main():
    apps = json.loads((ROOT / "data" / "apps.json").read_text(encoding="utf-8"))
    print("Loading winget index, Scoop buckets and Chocolatey data...")
    wg = winget_index()
    wg_lower = {k.lower(): k for k in wg}
    scoop = scoop_manifests()
    choco_ids = sorted({a["choco"] for a in apps if a.get("choco")})
    with cf.ThreadPoolExecutor(8) as pool:
        choco = dict(zip(choco_ids, pool.map(choco_package, choco_ids)))

    problems = 0
    warnings = 0
    for a in apps:
        msgs = []
        ids = a.get("winget") or []
        ids = [ids] if isinstance(ids, str) else ids
        for wid in ids:
            if wid.startswith("msstore:"):
                continue
            if wid in wg:
                continue
            if wid.lower() in wg_lower:
                msgs.append(("warn", f"winget id case differs: {wid} -> {wg_lower[wid.lower()]}"))
            else:
                sug = difflib.get_close_matches(wid, wg.keys(), n=3, cutoff=0.6)
                by_name = [k for k, v in wg.items() if a["name"].split(" (")[0].lower() == v[0].lower()][:3]
                msgs.append(("error", f"winget id not found: {wid}  suggestions: {sug + by_name}"))
        if a.get("scoop") and a["scoop"].lower() not in scoop:
            short = a["scoop"].split("/")[-1].lower()
            sug = [v for k, v in scoop.items() if k.split("/")[-1] == short] or difflib.get_close_matches(a["scoop"].lower(), scoop.keys(), n=3)
            msgs.append(("error", f"scoop manifest not found: {a['scoop']}  suggestions: {sug}"))
        if a.get("choco"):
            info = choco[a["choco"]]
            if info is None:
                msgs.append(("error", f"chocolatey package not found: {a['choco']}"))
            elif "error" in info:
                msgs.append(("warn", f"chocolatey check failed: {info['error']}"))
            elif "deprecated" in info["title"].lower():
                msgs.append(("error", f"chocolatey package is deprecated: {a['choco']}"))
            elif info["published"] and info["published"] < str(time.gmtime().tm_year - 3):
                msgs.append(("warn", f"chocolatey package last published {info['published']}: {a['choco']}"))
        for level, msg in msgs:
            print(f"[{level.upper():5}] {a['id']:24} {msg}")
            problems += level == "error"
            warnings += level == "warn"

    if "--elevation" in sys.argv:
        print("\nReading winget installer manifests...")
        pairs = [(wid, wg[wid][1]) for a in apps for wid in ([a["winget"]] if isinstance(a.get("winget"), str) else a.get("winget") or [])
                 if wid in wg]
        with cf.ThreadPoolExecutor(12) as pool:
            for (wid, _), elev in zip(pairs, pool.map(lambda p: winget_elevation(*p), pairs)):
                app = next(a for a in apps if wid in ([a["winget"]] if isinstance(a.get("winget"), str) else a.get("winget") or []))
                if "elevationProhibited" in elev and not app.get("noAdmin"):
                    print(f"[ERROR] {app['id']:24} {wid} is elevationProhibited: set \"noAdmin\": true")
                    problems += 1
                elif app.get("noAdmin") and "elevationProhibited" not in elev:
                    print(f"[WARN ] {app['id']:24} noAdmin is set but manifest says {elev or 'nothing'}")
                    warnings += 1

    print(f"\n{len(apps)} apps checked: {problems} error(s), {warnings} warning(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
