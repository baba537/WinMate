#!/usr/bin/env python3
"""Sanity checks for the built site in dist/ (used by CI).

- every internal link and asset exists
- no duplicate element IDs on a page
- JSON files parse, build-info hashes match the files
- the published engine matches the hash that scripts and the CLI embed

Usage: python tools/check_site.py
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent / "dist"


def main():
    errors = []
    pages = list(DIST.rglob("*.html"))
    for page in pages:
        text = page.read_text(encoding="utf-8")
        dupes = [i for i, n in Counter(re.findall(r'\sid="([^"]+)"', text)).items() if n > 1]
        if dupes:
            errors.append(f"{page.relative_to(DIST)}: duplicate ids {dupes[:5]}")
        for ref in re.findall(r'(?:href|src)="(/[^"#?]*)', text):
            target = DIST / ref.lstrip("/")
            if ref.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(DIST)}: broken link {ref}")

    for name in ("apps.json", "build-info.json", "site.webmanifest"):
        try:
            json.loads((DIST / name).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")

    info = json.loads((DIST / "build-info.json").read_text(encoding="utf-8"))
    for rel, digest in info["files"].items():
        if hashlib.sha256((DIST / rel).read_bytes()).hexdigest() != digest:
            errors.append(f"build-info.json: hash mismatch for {rel}")
    engine = (DIST / "engine.ps1").read_text(encoding="utf-8").rstrip()
    if hashlib.sha256(engine.encode("utf-8")).hexdigest() != info["engineSha256"]:
        errors.append("engine.ps1 does not match engineSha256")
    if info["engineSha256"] not in (DIST / "winmate.ps1").read_text(encoding="utf-8"):
        errors.append("winmate.ps1 does not embed the engine hash")

    for e in errors[:50]:
        print(e)
    print(f"{len(pages)} pages checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
