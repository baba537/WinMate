#!/usr/bin/env python3
"""Download and normalize app icons into src/icons/.

Every app in data/apps.json has an "icon" source spec:

  dash:<name>          homarr-labs/dashboard-icons (SVG, falls back to PNG)
  flathub:<app-id>     official app icon published on Flathub
  url:<url>[#RRGGBB]   direct image URL (optional fill colour for monochrome SVGs)
  site:<url>           best icon declared by a website (apple-touch-icon, SVG favicon, ...)
  gen:<text>           generated placeholder tile, for tools without an official logo

Usage:
  python tools/fetch_icons.py              # fetch icons that are missing
  python tools/fetch_icons.py --force      # re-fetch everything
  python tools/fetch_icons.py vlc obs      # (re-)fetch specific apps

Requires Pillow for raster images: pip install pillow
"""
import html
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "src" / "icons"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WinMate-icon-fetcher (+https://github.com/baba537/WinMate)"}
SIZE = 128


def http_get(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.geturl()


def is_svg(body):
    head = body[:4000].lstrip().lower()
    return b"<svg" in head and not head.startswith(b"<!doctype html") and b"<html" not in head


def clean_svg(body, fill=None):
    svg = body.decode("utf-8", "replace")
    svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r"<script.*?</script>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"\son\w+=\"[^\"]*\"", "", svg)
    svg = re.sub(r"<metadata.*?</metadata>", "", svg, flags=re.S)
    m = re.search(r"<svg\b[^>]*>", svg)
    tag = m.group(0)
    if "viewBox" not in tag:
        w = re.search(r'\swidth="([\d.]+)', tag)
        h = re.search(r'\sheight="([\d.]+)', tag)
        if w and h:
            tag2 = tag[:-1] + f' viewBox="0 0 {w.group(1)} {h.group(1)}">'
            svg = svg.replace(tag, tag2, 1)
            tag = tag2
    # Let CSS control the rendered size.
    tag2 = re.sub(r'\s(width|height)="[^"]*"', "", tag)
    if fill:
        tag2 = tag2[:-1] + f' fill="{fill}">'
    svg = svg.replace(tag, tag2, 1)
    return svg.strip() + "\n"


def to_webp(body):
    from PIL import Image  # imported lazily so SVG-only runs work without Pillow

    im = Image.open(io.BytesIO(body))
    if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
        # pick the largest frame (ICO files contain several sizes)
        best = None
        for size in sorted(getattr(im, "info", {}).get("sizes", []) or [im.size], reverse=True):
            try:
                im.size = size  # ICO plugin
            except Exception:
                pass
            best = im
            break
        im = best or im
    im = im.convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2))
    if side > SIZE:
        canvas = canvas.resize((SIZE, SIZE), Image.LANCZOS)
    out = io.BytesIO()
    canvas.save(out, "WEBP", quality=90, method=6)
    return out.getvalue(), min(side, SIZE)


def site_icon(page_url):
    """Return the best icon URL a website declares, largest first, SVG preferred."""
    body, _, final = http_get(page_url)
    doc = body.decode("utf-8", "replace")
    found = []
    for tag in re.findall(r"<link\b[^>]*>", doc, flags=re.I):
        rel = re.search(r'rel=["\']([^"\']+)', tag, re.I)
        href = re.search(r'href=["\']([^"\']+)', tag, re.I)
        if not rel or not href or "icon" not in rel.group(1).lower() or "mask" in rel.group(1).lower():
            continue
        url = urllib.parse.urljoin(final, html.unescape(href.group(1)))
        sizes = re.search(r'sizes=["\'](\d+)x', tag, re.I)
        score = int(sizes.group(1)) if sizes else (1000 if url.lower().split("?")[0].endswith(".svg") else 32)
        if "apple-touch-icon" in rel.group(1).lower() and not sizes:
            score = 180
        found.append((score, url))
    for _, url in sorted(found, reverse=True):
        yield url
    host = urllib.parse.urlparse(final)
    yield f"https://www.google.com/s2/favicons?domain_url={urllib.parse.quote(host.scheme + '://' + host.netloc)}&sz=128"


def gen_svg(text):
    """Neutral tile for tools without an official square logo. A leading '>' draws a terminal prompt."""
    prompt = text.startswith(">")
    text = text.lstrip(">")
    size = {1: 34, 2: 28, 3: 22, 4: 17}.get(len(text), 14)
    t = html.escape(text)
    deco = (
        '<path d="M11 13l5 4-5 4" fill="none" stroke="#7dd3fc" stroke-width="2.5" stroke-linecap="square"/>'
        '<rect x="19" y="19" width="8" height="2.5" fill="#7dd3fc"/>'
        if prompt else ""
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect x="2" y="2" width="60" height="60" rx="12" fill="#101a33"/>'
        '<rect x="2" y="2" width="60" height="60" rx="12" fill="none" stroke="#3b82f6" stroke-width="3"/>'
        f'{deco}<text x="32" y="{(44 if prompt else 42) if len(text) < 3 else 43}" text-anchor="middle" '
        f'font-family="Consolas,Menlo,monospace" font-weight="700" font-size="{size}" fill="#e2e9ff">{t}</text></svg>\n'
    )


def candidates(spec):
    kind, _, rest = spec.partition(":")
    if kind == "dash":
        yield f"https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/{rest}.svg", None
        yield f"https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/{rest}.png", None
    elif kind == "flathub":
        body, _, _ = http_get(f"https://flathub.org/api/v2/appstream/{rest}")
        data = json.loads(body)
        icons = sorted(data.get("icons") or [], key=lambda i: int(i.get("width") or 0), reverse=True)
        for icon in icons:
            yield icon["url"], None
        if data.get("icon"):
            yield data["icon"], None
    elif kind == "url":
        url, _, color = rest.partition("#")
        yield url, (f"#{color}" if color else None)
    elif kind == "site":
        for url in site_icon(rest):
            yield url, None
    else:
        raise ValueError(f"unknown icon spec {spec!r}")


def fetch(app, force=False):
    slug, spec = app["id"], app["icon"]
    existing = [p for p in ICON_DIR.glob(f"{slug}.*")]
    if existing and not force:
        return slug, "skip", existing[0].name
    for p in existing:
        p.unlink()
    if spec.startswith("gen:"):
        (ICON_DIR / f"{slug}.svg").write_text(gen_svg(spec[4:]), encoding="utf-8", newline="\n")
        return slug, "ok", "generated"
    errors = []
    try:
        for url, fill in candidates(spec):
            try:
                body, ctype, _ = http_get(url)
            except Exception as e:  # try the next candidate
                errors.append(f"{url}: {e}")
                continue
            if is_svg(body):
                (ICON_DIR / f"{slug}.svg").write_text(clean_svg(body, fill), encoding="utf-8", newline="\n")
                return slug, "ok", url
            if "html" in ctype or len(body) < 200:
                errors.append(f"{url}: not an image")
                continue
            try:
                data, side = to_webp(body)
            except Exception as e:
                errors.append(f"{url}: {e}")
                continue
            (ICON_DIR / f"{slug}.webp").write_bytes(data)
            return slug, ("ok" if side >= 64 else f"small({side}px)"), url
    except Exception as e:
        errors.append(str(e))
    return slug, "FAIL", "; ".join(errors)[-300:]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv or bool(args)
    apps = json.loads((ROOT / "data" / "apps.json").read_text(encoding="utf-8"))
    if args:
        apps = [a for a in apps if a["id"] in args]
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda a: fetch(a, force), apps))
    bad = 0
    for slug, status, info in results:
        if status != "skip":
            print(f"{status:12} {slug:28} {info}")
        bad += status not in ("ok", "skip")
    known = {a["id"] for a in json.loads((ROOT / "data" / "apps.json").read_text(encoding="utf-8"))}
    for p in ICON_DIR.iterdir():
        if p.stem not in known:
            print(f"orphan       {p.name}")
    print(f"\n{len(results)} apps, {bad} need attention")
    return 1 if any(s == "FAIL" for _, s, _ in results) else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
