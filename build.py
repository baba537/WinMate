#!/usr/bin/env python3
"""Build the static WinMate site into ./dist.

Standard library only, so it runs on Cloudflare Pages without extra dependencies:
  Build command:     python3 build.py
  Output directory:  dist

Set SITE_URL (env var) to your production origin, e.g. SITE_URL=https://winmate.pages.dev
"""
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path

import pixel
from i18n import FAQ, T

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DATA = ROOT / "data"
DIST = ROOT / "dist"
SITE_URL = os.environ.get("SITE_URL", "https://winmate.pages.dev").rstrip("/")
REPO_URL = "https://github.com/baba537/WinMate"
LANGS = ("en", "de")
PMS = ("winget", "scoop", "choco")
PM_LABEL = {"winget": "winget", "scoop": "Scoop", "choco": "Chocolatey"}
TODAY = dt.date.today().isoformat()

esc = html.escape


# ----------------------------------------------------------------------------- data
def load_data():
    apps = json.loads((DATA / "apps.json").read_text(encoding="utf-8"))
    cats = json.loads((DATA / "categories.json").read_text(encoding="utf-8"))
    presets = json.loads((DATA / "presets.json").read_text(encoding="utf-8"))
    cat_ids = {c["id"] for c in cats}
    app_ids = set()
    icons = {p.stem: p.name for p in (SRC / "icons").iterdir()}
    for a in apps:
        assert a["id"] not in app_ids, f"duplicate app id {a['id']}"
        app_ids.add(a["id"])
        assert a["category"] in cat_ids, f"{a['id']}: unknown category {a['category']}"
        assert a["id"] in icons, f"{a['id']}: icon missing, run tools/fetch_icons.py"
        assert any(a.get(pm) for pm in PMS), f"{a['id']}: no package manager id"
        w = a.get("winget")
        a["winget"] = [w] if isinstance(w, str) else (w or [])
        a["iconFile"] = icons[a["id"]]
    for p in presets:
        for aid in p["apps"]:
            assert aid in app_ids, f"preset {p['id']}: unknown app {aid}"
    by_cat = {c["id"]: [a for a in apps if a["category"] == c["id"]] for c in cats}
    return apps, cats, presets, by_cat


# ----------------------------------------------------------------------------- helpers
def url(lang, path=""):
    """Site-relative URL for a page path like 'apps/vlc/'."""
    return ("/de/" if lang == "de" else "/") + path


def abs_url(lang, path=""):
    return SITE_URL + url(lang, path)


def asset(name):
    return "/" + ASSETS[name]


def pm_commands(app):
    """Install commands per package manager, as shown on app pages."""
    out = {}
    if app["winget"]:
        lines = []
        for wid in app["winget"]:
            if wid.startswith("msstore:"):
                lines.append(f"winget install --id {wid[8:]} --source msstore --accept-package-agreements")
            else:
                lines.append(f"winget install --id {wid} --exact --source winget")
        out["winget"] = "\n".join(lines)
    if app.get("scoop"):
        bucket = app["scoop"].split("/")[0]
        cmd = f"scoop install {app['scoop']}"
        out["scoop"] = cmd if bucket == "main" else f"scoop bucket add {bucket}\n{cmd}"
    if app.get("choco"):
        out["choco"] = f"choco install {app['choco']} -y"
    return out


def winget_display(app):
    return ", ".join(w.replace("msstore:", "") for w in app["winget"])


def json_ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


ICONS = {
    "github": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .5a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.7-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17.3 4.7 18.3 5 18.3 5c.7 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .5z"/></svg>',
    "theme": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M10 2h4v3h-4zM10 19h4v3h-4zM2 10h3v4H2zM19 10h3v4h-3zM5 4h3v3H5zM16 17h3v3h-3zM16 4h3v3h-3zM5 17h3v3H5zM8 8h8v8H8z"/></svg>',
    "search": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 2h8v2H4zM2 4h2v8H2zM12 4h2v8h-2zM4 12h8v2H4zM14 14h2v2h-2zM16 16h2v2h-2zM18 18h2v2h-2zM20 20h2v2h-2z"/></svg>',
    "copy": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 2h12v2H8zM20 4h2v12h-2zM6 4h2v2H6zM2 8h12v2H2zM2 10h2v12H2zM4 20h10v2H4zM14 10h2v12h-2zM18 16h2v2h-2z"/></svg>',
    "download": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M11 2h2v12h-2zM7 10h2v2H7zM15 10h2v2h-2zM9 12h2v2H9zM13 12h2v2h-2zM3 16h2v4H3zM19 16h2v4h-2zM5 20h14v2H5z"/></svg>',
    "external": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M14 2h8v8h-2V6h-2V4h-4zM16 6h2v2h-2zM14 8h2v2h-2zM12 10h2v2h-2zM2 4h8v2H4v14h14v-6h2v8H2z"/></svg>',
}


# ----------------------------------------------------------------------------- layout
def head(lang, *, title, description, path, alt_path=None, og_type="website", extra_ld=(), noindex=False):
    t = T[lang]
    alt_path = path if alt_path is None else alt_path
    other = "de" if lang == "en" else "en"
    canonical = abs_url(lang, path)
    parts = [
        "<!doctype html>",
        f'<html lang="{lang}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<link rel="canonical" href="{canonical}">',
    ]
    if noindex:
        parts.append('<meta name="robots" content="noindex">')
    else:
        parts += [
            f'<link rel="alternate" hreflang="{lang}" href="{canonical}">',
            f'<link rel="alternate" hreflang="{other}" href="{abs_url(other, alt_path)}">',
            f'<link rel="alternate" hreflang="x-default" href="{abs_url("en", path if lang == "en" else alt_path)}">',
        ]
    parts += [
        '<meta name="theme-color" content="#0b1020" media="(prefers-color-scheme: dark)">',
        '<meta name="theme-color" content="#f4f6fb" media="(prefers-color-scheme: light)">',
        '<meta name="color-scheme" content="dark light">',
        f'<meta property="og:type" content="{og_type}">',
        '<meta property="og:site_name" content="WinMate">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{SITE_URL}/img/og-image.png">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{t["locale"]}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="icon" href="/favicon.ico" sizes="48x48">',
        '<link rel="icon" href="/img/favicon-32.png" type="image/png" sizes="32x32">',
        '<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
        f'<link rel="preload" href="{asset("fonts/silkscreen-400.woff2")}" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="{asset("css/style.css")}">',
        # Apply the saved theme before first paint to avoid a flash.
        "<script>try{var t=localStorage.getItem('wm-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>",
        f'<script src="{asset("js/app.js")}" defer></script>',
        f'<link rel="alternate" type="text/plain" title="LLM summary" href="{SITE_URL}/llms.txt">',
    ]
    parts += list(extra_ld)
    parts += ["</head>", "<body>"]
    return "\n".join(parts)


def header(lang, alt_path, home_page=False):
    t = T[lang]
    other = "de" if lang == "en" else "en"
    home = url(lang)
    help_btn = (f'<button class="icon-btn key-btn" type="button" data-help-open aria-label="{t["keys_dialog_title"]}" '
                f'title="{t["keys_dialog_title"]} (?)">?</button>') if home_page else ""
    return f"""<a class="skip" href="#main">{t['skip']}</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{home}" aria-label="WinMate {t['home']}">
      <img src="/img/mascot-64.webp" width="32" height="38" alt="">
      <span class="brand-name">WinMate</span>
    </a>
    <nav class="nav" aria-label="{t['nav_label']}">
      <a href="{home}#apps">{t['nav_apps']}</a>
      <a href="{url(lang, 'about/')}">{t['nav_about']}</a>
      <a href="{url(lang, 'about/')}#faq">FAQ</a>
    </nav>
    <div class="header-actions">
      {help_btn}
      <a class="btn-ghost lang-switch" href="{url(other, alt_path)}" hreflang="{other}" lang="{other}" title="{T[other]['lang_name']}">{other.upper()}</a>
      <button class="icon-btn" type="button" data-theme-toggle aria-label="{t['toggle_theme']}" title="{t['toggle_theme']}">{ICONS['theme']}</button>
      <a class="icon-btn" href="{REPO_URL}" rel="noopener" aria-label="GitHub" title="GitHub">{ICONS['github']}</a>
    </div>
  </div>
</header>"""


def footer(lang, cats, presets):
    t = T[lang]
    cat_links = "".join(f'<li><a href="{url(lang, "category/" + c["id"] + "/")}">{esc(c[lang]["name"])}</a></li>' for c in cats)
    preset_links = "".join(f'<li><a href="{url(lang, "bundle/" + p["id"] + "/")}">{esc(p[lang]["name"])}</a></li>' for p in presets)
    return f"""<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-about">
      <a class="brand" href="{url(lang)}"><img src="/img/mascot-64.webp" width="32" height="38" alt=""><span class="brand-name">WinMate</span></a>
      <p>{t['footer_about']}</p>
      <p class="muted small">{t['footer_disclaimer']}</p>
    </div>
    <nav aria-label="{t['footer_categories']}"><h2>{t['footer_categories']}</h2><ul class="footer-cats">{cat_links}</ul></nav>
    <nav aria-label="{t['footer_bundles']}"><h2>{t['footer_bundles']}</h2><ul>{preset_links}</ul>
      <h2>{t['footer_project']}</h2>
      <ul>
        <li><a href="{REPO_URL}" rel="noopener">GitHub</a></li>
        <li><a href="{REPO_URL}/issues" rel="noopener">{t['footer_report']}</a></li>
        <li><a href="{url(lang, 'about/')}">{t['nav_about']}</a></li>
        <li><a href="{url(lang, 'privacy/')}">{t['privacy']}</a></li>
        <li><a href="/llms.txt">llms.txt</a> · <a href="/apps.json">apps.json</a></li>
      </ul>
    </nav>
  </div>
  <div class="wrap footer-bottom muted small">© {dt.date.today().year} WinMate · MIT License · {t['footer_made']} · {t['footer_inspired']}</div>
</footer>"""


def page(lang, body, *, title, description, path, alt_path=None, cats, presets, extra_ld=(), og_type="website", noindex=False, home_page=False):
    alt = path if alt_path is None else alt_path
    return (
        head(lang, title=title, description=description, path=path, alt_path=alt, extra_ld=extra_ld, og_type=og_type, noindex=noindex)
        + "\n" + pixel.background()
        + "\n" + header(lang, alt, home_page)
        + f'\n<main id="main">\n{body}\n</main>\n'
        + footer(lang, cats, presets)
        + "\n</body>\n</html>\n"
    )


def breadcrumbs(lang, items):
    """items: list of (label, path or None)."""
    lis = []
    ld = []
    for i, (label, path) in enumerate(items, 1):
        if path is None:
            lis.append(f'<li aria-current="page">{esc(label)}</li>')
        else:
            lis.append(f'<li><a href="{url(lang, path)}">{esc(label)}</a></li>')
        ld.append({"@type": "ListItem", "position": i, "name": label, **({"item": abs_url(lang, path)} if path is not None else {})})
    nav = f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'
    return nav, json_ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld})


# ----------------------------------------------------------------------------- components
def icon_img(app, size=40, lazy=True):
    loading = 'loading="lazy" ' if lazy else ""
    return f'<img src="/icons/{app["iconFile"]}" width="{size}" height="{size}" alt="" {loading}decoding="async">'


def card(lang, app):
    t = T[lang]
    attrs = [f'data-id="{app["id"]}"', f'data-name="{esc(app["name"])}"', f'data-cat="{app["category"]}"']
    if app["winget"]:
        attrs.append(f'data-winget="{esc(",".join(app["winget"]))}"')
    if app.get("scoop"):
        attrs.append(f'data-scoop="{esc(app["scoop"])}"')
    if app.get("choco"):
        attrs.append(f'data-choco="{esc(app["choco"])}"')
    if app.get("noAdmin"):
        attrs.append("data-noadmin")
    badges = "".join(f'<span class="pm-dot pm-{pm}" title="{PM_LABEL[pm]}"></span>' for pm in PMS if (app["winget"] if pm == "winget" else app.get(pm)))
    return (
        f'<li class="card" {" ".join(attrs)}>'
        f'<input type="checkbox" class="card-check" id="app-{app["id"]}" aria-describedby="d-{app["id"]}">'
        f'<label for="app-{app["id"]}" class="card-body">'
        f'<span class="tile">{icon_img(app)}</span>'
        f'<span class="card-text"><span class="card-name">{esc(app["name"])}</span>'
        f'<span class="card-desc" id="d-{app["id"]}">{esc(app["description"][lang])}</span></span>'
        f'<span class="check" aria-hidden="true"></span></label>'
        f'<span class="card-foot"><span class="pms" aria-hidden="true">{badges}</span>'
        f'<span class="na-note" hidden>{t["not_available_short"]}</span><span class="via" hidden></span>'
        f'<a class="card-more" href="{url(lang, "apps/" + app["id"] + "/")}">{t["details"]}</a></span>'
        "</li>"
    )


def command_block(lang, app):
    t = T[lang]
    cmds = pm_commands(app)
    rows = []
    for pm in PMS:
        if pm not in cmds:
            rows.append(f'<div class="cmd cmd-missing"><div class="cmd-head"><span class="pm-dot pm-{pm}"></span>{PM_LABEL[pm]}</div>'
                        f'<p class="muted small">{t["not_available_pm"].format(pm=PM_LABEL[pm])}</p></div>')
            continue
        rows.append(
            f'<div class="cmd"><div class="cmd-head"><span class="pm-dot pm-{pm}"></span>{PM_LABEL[pm]}'
            f'<button type="button" class="btn-small" data-copy="{esc(cmds[pm])}">{ICONS["copy"]}<span>{t["copy"]}</span></button></div>'
            f'<pre><code>{esc(cmds[pm])}</code></pre></div>'
        )
    return '<div class="cmds">' + "".join(rows) + "</div>"


def mini_list(lang, apps):
    return '<ul class="mini-list">' + "".join(
        f'<li><a href="{url(lang, "apps/" + a["id"] + "/")}"><span class="tile tile-sm">{icon_img(a, 28)}</span>'
        f'<span>{esc(a["name"])}</span></a></li>' for a in apps) + "</ul>"


# ----------------------------------------------------------------------------- pages
BUNDLE_GROUPS = ("basics", "play", "tech")


def bundle_sidebar(lang, presets):
    t = T[lang]
    groups = []
    for g in BUNDLE_GROUPS:
        tiles = "".join(
            f'<li><button type="button" class="bundle-tile g-{g}" data-bundle="{p["id"]}" data-apps="{",".join(p["apps"])}" '
            f'data-name="{esc(p[lang]["name"])}" data-title="{esc(p[lang]["title"])}" data-intro="{esc(p[lang]["intro"])}" '
            f'data-group="{esc(t["bundle_groups"][g])}" data-url="{url(lang, "bundle/" + p["id"] + "/")}" aria-haspopup="dialog">'
            f'<span class="bt-icon">{pixel.svg(p["icon"])}</span><span class="bt-name">{esc(p[lang]["name"])}</span>'
            f'<span class="bt-count">{len(p["apps"])}</span></button></li>'
            for p in presets if p["group"] == g)
        groups.append(f'<div class="bundle-group"><h4 class="group-title g-{g}">{esc(t["bundle_groups"][g])}</h4><ul class="bundle-grid">{tiles}</ul></div>')
    return "".join(groups)


def home_page(lang, apps, cats, presets, by_cat):
    t = T[lang]
    n = len(apps)
    cat_nav = "".join(
        f'<li><a href="#cat-{c["id"]}" data-cat-link="{c["id"]}"><span>{esc(c[lang]["name"])}</span><span class="count">{len(by_cat[c["id"]])}</span></a></li>'
        for c in cats)
    sections = []
    for c in cats:
        items = "".join(card(lang, a) for a in by_cat[c["id"]])
        sections.append(
            f'<section class="cat" id="cat-{c["id"]}" aria-labelledby="h-{c["id"]}">'
            f'<div class="cat-head"><h2 id="h-{c["id"]}">{esc(c[lang]["name"])} <span class="count">{len(by_cat[c["id"]])}</span></h2>'
            f'<a class="cat-link small" href="{url(lang, "category/" + c["id"] + "/")}">{t["category_page"]}</a></div>'
            f'<ul class="cards">{items}</ul></section>')
    keys_short = "".join(f"<li><kbd>{esc(k)}</kbd><span>{esc(v)}</span></li>" for k, v in t["keys_short"])
    keys_all = "".join(f"<li><kbd>{esc(k)}</kbd><span>{esc(v)}</span></li>" for k, v in t["keys_all"])

    body = f"""
<section class="marquee">
  <div class="wrap marquee-inner">
    <div class="marquee-copy">
      <h1><span class="h1-pixel">WinMate</span> {esc(t['hero_title'])}</h1>
      <p class="lead">{esc(t['hero_lead'].format(n=n))}</p>
    </div>
    <dl class="hud">
      <div class="hud-cell"><dt>{t['hud_apps']}</dt><dd>{n:03d}</dd></div>
      <div class="hud-cell hud-sel"><dt>{t['hud_selected']}</dt><dd id="hudSel">000</dd></div>
      <div class="hud-cell"><dt>{t['hud_bundles']}</dt><dd>{len(presets):03d}</dd></div>
      <div class="hud-cell"><dt>{t['hud_pm']}</dt><dd id="hudPm">WINGET</dd></div>
    </dl>
  </div>
</section>

<section id="apps" class="catalog" aria-label="{t['catalog_title']}">
  <div class="wrap">
    <div class="catalog-layout">
      <aside class="sidebar" aria-label="{t['filters']}">
        <div class="panel">
          <h2 class="panel-title" id="pm-label">{t['pm_title']}</h2>
          <div class="segmented" role="radiogroup" aria-labelledby="pm-label">
            <button type="button" role="radio" aria-checked="true" data-pm="winget">winget</button>
            <button type="button" role="radio" aria-checked="false" data-pm="scoop">Scoop</button>
            <button type="button" role="radio" aria-checked="false" data-pm="choco">Chocolatey</button>
          </div>
          <p class="pm-hint small muted" data-pm-hint="winget">{t['pm_hint_winget']}</p>
          <p class="pm-hint small muted" data-pm-hint="scoop" hidden>{t['pm_hint_scoop']}</p>
          <p class="pm-hint small muted" data-pm-hint="choco" hidden>{t['pm_hint_choco']}</p>
        </div>
        <div class="panel" id="bundles">
          <h2 class="panel-title">{t['presets_title']}</h2>
          {bundle_sidebar(lang, presets)}
        </div>
        <nav class="panel cat-nav" aria-label="{t['footer_categories']}">
          <h2 class="panel-title">{t['footer_categories']}</h2>
          <ul>{cat_nav}</ul>
        </nav>
        <div class="panel keys-panel">
          <h2 class="panel-title">{t['keys_title']}</h2>
          <ul class="keys">{keys_short}</ul>
        </div>
      </aside>
      <div class="catalog-main">
        <div class="toolbar">
          <label class="search">
            <span class="sr-only">{t['search_label']}</span>
            {ICONS['search']}
            <input type="search" id="search" placeholder="{t['search_placeholder'].format(n=n)}" autocomplete="off" spellcheck="false">
            <kbd class="search-kbd" aria-hidden="true">/</kbd>
          </label>
          <label class="toggle"><input type="checkbox" id="onlySelected"><span>{t['only_selected']}</span></label>
          <span class="result-count muted small" id="resultCount" aria-live="polite"></span>
        </div>
        <p class="empty" id="emptyState" hidden>{t['no_results']}</p>
        <noscript><p class="notice">{t['noscript']}</p></noscript>
        {''.join(sections)}
      </div>
    </div>
  </div>
</section>

<div class="selbar" id="selbar" hidden>
  <div class="wrap selbar-inner">
    <div class="selbar-info">
      <strong id="selCount" class="coin">0</strong>
      <span class="selbar-text"><span id="selLabel">{t['selected']}</span> <span class="muted small" id="selBreakdown"></span></span>
      <span class="selbar-bundles" id="selBundles"></span>
    </div>
    <div class="selbar-actions">
      <button type="button" class="btn-ghost" id="clearSel">{t['clear']} <kbd>C</kbd></button>
      <button type="button" class="btn btn-primary btn-start" id="openScript">{t['get_script']} <kbd>S</kbd></button>
    </div>
  </div>
</div>

<dialog class="dialog" id="scriptDialog" aria-labelledby="dlg-title">
  <form method="dialog" class="dialog-close-form"><button class="icon-btn dialog-close" aria-label="{t['close']}">✕</button></form>
  <h2 id="dlg-title">{t['dlg_title']}</h2>
  <p class="muted" id="dlgSummary"></p>
  <ul class="dlg-warnings" id="dlgWarnings"></ul>
  <div class="dlg-actions">
    <button type="button" class="btn btn-primary" id="dlCmd">{ICONS['download']}<span>{t['dl_cmd']}</span> <kbd>D</kbd></button>
    <button type="button" class="btn" id="copyPs">{ICONS['copy']}<span>{t['copy_ps']}</span> <kbd>Y</kbd></button>
    <button type="button" class="btn-ghost" id="dlPs">{t['dl_ps1']}</button>
    <button type="button" class="btn-ghost" id="copyLink">{t['copy_link']}</button>
  </div>
  <ol class="dlg-steps">{''.join(f'<li>{s}</li>' for s in t['run_steps'])}</ol>
  <details class="dlg-script"><summary>{t['show_script']}</summary><pre><code id="scriptPreview"></code></pre></details>
</dialog>

<dialog class="dialog bundle-dialog" id="bundleDialog" aria-labelledby="bd-title">
  <form method="dialog" class="dialog-close-form"><button class="icon-btn dialog-close" aria-label="{t['close']}">✕</button></form>
  <div class="bd-head">
    <span class="bd-icon" id="bdIcon"></span>
    <div>
      <p class="eyebrow" id="bdGroup"></p>
      <h2 id="bd-title"></h2>
      <p class="muted" id="bdIntro"></p>
    </div>
  </div>
  <p class="bd-meta"><strong id="bdCount"></strong> <span class="muted" id="bdHint"></span> <a id="bdPage" class="small" href="#">{t['details']} →</a></p>
  <ul class="bd-list" id="bdList"></ul>
  <div class="bd-actions" id="bdActions"></div>
</dialog>

<dialog class="dialog help-dialog" id="helpDialog" aria-labelledby="help-title">
  <form method="dialog" class="dialog-close-form"><button class="icon-btn dialog-close" aria-label="{t['close']}">✕</button></form>
  <h2 id="help-title">{t['keys_dialog_title']}</h2>
  <ul class="keys keys-all">{keys_all}</ul>
</dialog>
<div class="toast" id="toast" role="status" aria-live="polite" hidden></div>
<script type="application/json" id="wm-i18n">{json.dumps(t['js'], ensure_ascii=False)}</script>
"""
    ld = [
        json_ld({
            "@context": "https://schema.org", "@type": "WebSite", "name": "WinMate", "url": abs_url(lang),
            "inLanguage": lang, "description": t["meta_description"].format(n=n),
        }),
        json_ld({
            "@context": "https://schema.org", "@type": "WebApplication", "name": "WinMate",
            "url": abs_url(lang), "applicationCategory": "UtilitiesApplication", "operatingSystem": "Windows 10, Windows 11",
            "browserRequirements": "Requires JavaScript", "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            "description": t["meta_description"].format(n=n), "inLanguage": lang,
            "license": "https://opensource.org/licenses/MIT", "codeRepository": REPO_URL,
            "featureList": t["hero_points_plain"], "image": f"{SITE_URL}/img/og-image.png",
        }),
        json_ld({
            "@context": "https://schema.org", "@type": "ItemList", "name": t["presets_title"],
            "itemListElement": [{"@type": "ListItem", "position": i, "name": p[lang]["title"], "url": abs_url(lang, "bundle/" + p["id"] + "/")}
                                for i, p in enumerate(presets, 1)],
        }),
    ]
    return page(lang, body, title=t["meta_title"], description=t["meta_description"].format(n=n), path="",
                cats=cats, presets=presets, extra_ld=ld, home_page=True)


def about_page(lang, apps, cats, presets):
    t = T[lang]
    steps = "".join(f'<li class="step"><span class="step-no">{i}</span><h3>{esc(h)}</h3><p>{p}</p></li>' for i, (h, p) in enumerate(t["steps"], 1))
    faq_html = "".join(f'<details class="faq-item"><summary><h3>{esc(q)}</h3></summary><div class="faq-a">{a}</div></details>' for q, a in FAQ[lang])
    compare_rows = "".join(f"<tr><th scope=\"row\">{esc(r[0])}</th><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>" for r in t["compare_rows"])
    nav, bc_ld = breadcrumbs(lang, [("WinMate", ""), (t["about_title"], None)])
    body = f"""
<div class="wrap page about">
  {nav}
  <header class="list-hero">
    <h1>{t['about_title']}</h1>
    <p class="lead">{t['about_lead']}</p>
    <p><a class="btn btn-primary" href="{url(lang)}#apps">{t['nav_apps']} →</a></p>
  </header>
  <section aria-labelledby="how-title">
    <h2 id="how-title">{t['how_title']}</h2>
    <ol class="steps">{steps}</ol>
    <div class="callout" id="one-prompt"><h3>{t['admin_title']}</h3><p>{t['admin_text']}</p></div>
  </section>
  <section aria-labelledby="compare-title" class="section-sm">
    <h2 id="compare-title">{t['compare_title']}</h2>
    <p class="muted">{t['compare_lead']}</p>
    <div class="table-wrap"><table class="compare">
      <thead><tr><th scope="col"></th><th scope="col">winget</th><th scope="col">Scoop</th><th scope="col">Chocolatey</th></tr></thead>
      <tbody>{compare_rows}</tbody>
    </table></div>
  </section>
  <section id="faq" aria-labelledby="faq-title" class="section-sm">
    <h2 id="faq-title">{t['faq_title']}</h2>
    <div class="faq">{faq_html}</div>
  </section>
  <section aria-labelledby="credits-title" class="section-sm">
    <h2 id="credits-title">{t['credits_title']}</h2>
    <p>{t['credits_html']}</p>
  </section>
</div>"""
    ld = [
        bc_ld,
        json_ld({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in FAQ[lang]],
        }),
        json_ld({
            "@context": "https://schema.org", "@type": "HowTo", "name": t["how_title"],
            "step": [{"@type": "HowToStep", "position": i, "name": h, "text": re.sub(r"<[^>]+>", "", p)} for i, (h, p) in enumerate(t["steps"], 1)],
        }),
    ]
    return page(lang, body, title=f"{t['about_title']} – FAQ | WinMate", description=t["about_meta"], path="about/",
                cats=cats, presets=presets, extra_ld=ld)


def app_page(lang, app, apps, cats, presets, by_cat):
    t = T[lang]
    cat = next(c for c in cats if c["id"] == app["category"])
    path = f"apps/{app['id']}/"
    nav, bc_ld = breadcrumbs(lang, [("WinMate", ""), (cat[lang]["name"], f"category/{cat['id']}/"), (app["name"], None)])
    related = [a for a in by_cat[cat["id"]] if a["id"] != app["id"]][:12]
    notes = []
    if any(w.startswith("msstore:") for w in app["winget"]):
        notes.append(t["note_msstore"])
    if app.get("noAdmin"):
        notes.append(t["note_noadmin"].format(name=esc(app["name"])))
    if app.get("scoop", "").startswith("nonportable/"):
        notes.append(t["note_nonportable"])
    ids = []
    if app["winget"]:
        ids.append(f"<dt>winget</dt><dd><code>{esc(winget_display(app))}</code></dd>")
    if app.get("scoop"):
        ids.append(f"<dt>Scoop</dt><dd><code>{esc(app['scoop'])}</code></dd>")
    if app.get("choco"):
        ids.append(f"<dt>Chocolatey</dt><dd><code>{esc(app['choco'])}</code></dd>")
    title = t["app_title"].format(name=app["name"])
    desc = t["app_meta"].format(name=app["name"], desc=app["description"][lang].rstrip("."))
    body = f"""
<div class="wrap narrow page">
  {nav}
  <article class="app-page">
    <header class="app-hero">
      <span class="tile tile-lg">{icon_img(app, 72, lazy=False)}</span>
      <div>
        <h1>{esc(t['app_h1'].format(name=app['name']))}</h1>
        <p class="lead">{esc(app['description'][lang])}</p>
        <p class="app-links">
          <a class="btn btn-primary" href="{url(lang)}?add={app['id']}#apps">{t['add_to_script']}</a>
          <a class="btn-ghost" href="{esc(app['homepage'])}" rel="noopener nofollow">{t['official_site']} {ICONS['external']}</a>
        </p>
      </div>
    </header>
    {''.join(f'<p class="notice">{n}</p>' for n in notes)}
    <h2>{t['install_commands']}</h2>
    <p class="muted">{t['install_commands_lead'].format(name=esc(app['name']))}</p>
    {command_block(lang, app)}
    <h2>{t['package_ids']}</h2>
    <dl class="ids"><dt>{t['category']}</dt><dd><a href="{url(lang, 'category/' + cat['id'] + '/')}">{esc(cat[lang]['name'])}</a></dd>{''.join(ids)}</dl>
    <div class="callout">
      <h2>{t['bulk_title'].format(name=esc(app['name']))}</h2>
      <p>{t['bulk_text']}</p>
      <a class="btn btn-primary" href="{url(lang)}?add={app['id']}#apps">{t['add_to_script']}</a>
    </div>
    {f'<h2>{t["related"].format(cat=esc(cat[lang]["name"]))}</h2>' + mini_list(lang, related) if related else ''}
  </article>
</div>"""
    ld = [bc_ld, json_ld({
        "@context": "https://schema.org", "@type": "SoftwareApplication", "name": app["name"],
        "description": app["description"][lang], "operatingSystem": "Windows",
        "applicationCategory": t["schema_category"].get(cat["id"], "UtilitiesApplication"),
        "url": abs_url(lang, path), "sameAs": app["homepage"], "image": f"{SITE_URL}/icons/{app['iconFile']}",
        "installUrl": app["homepage"],
    })]
    return page(lang, body, title=title, description=desc, path=path, cats=cats, presets=presets, extra_ld=ld, og_type="article")


def list_page(lang, *, kind, item, list_apps, apps, cats, presets, title, h1, intro):
    t = T[lang]
    path = f"{kind}/{item['id']}/"
    nav, bc_ld = breadcrumbs(lang, [("WinMate", ""), (h1, None)])
    rows = []
    for a in list_apps:
        cmds = pm_commands(a)
        first = cmds.get("winget") or cmds.get("scoop") or cmds.get("choco")
        rows.append(
            f'<li class="list-app"><a class="list-app-head" href="{url(lang, "apps/" + a["id"] + "/")}">'
            f'<span class="tile">{icon_img(a)}</span><span><strong>{esc(a["name"])}</strong>'
            f'<span class="muted small">{esc(a["description"][lang])}</span></span></a>'
            f'<pre><code>{esc(first)}</code></pre></li>')
    ids = ",".join(a["id"] for a in list_apps)
    select_href = f'{url(lang)}?bundle={item["id"]}#apps' if kind == "bundle" else f"{url(lang)}?apps={ids}#apps"
    icon = f'<span class="list-hero-icon g-{item["group"]}">{pixel.svg(item["icon"])}</span>' if kind == "bundle" else ""
    other_lists = (
        "".join(f'<li><a class="chip" href="{url(lang, "category/" + c["id"] + "/")}">{esc(c[lang]["name"])}</a></li>' for c in cats if c["id"] != item["id"])
        if kind == "category" else
        "".join(f'<li><a class="chip bundle-chip g-{p["group"]}" href="{url(lang, "bundle/" + p["id"] + "/")}">{pixel.svg(p["icon"])} {esc(p[lang]["name"])}</a></li>' for p in presets if p["id"] != item["id"])
    )
    body = f"""
<div class="wrap narrow page">
  {nav}
  <header class="list-hero">
    {icon}<h1>{esc(h1)}</h1>
    <p class="lead">{esc(intro)}</p>
    <p><a class="btn btn-primary" href="{select_href}">{t['select_all_in_winmate'].format(n=len(list_apps))}</a></p>
  </header>
  <ol class="list-apps">{''.join(rows)}</ol>
  <h2>{t['more_categories'] if kind == 'category' else t['more_bundles']}</h2>
  <ul class="chips">{other_lists}</ul>
</div>"""
    ld = [bc_ld, json_ld({
        "@context": "https://schema.org", "@type": "ItemList", "name": h1,
        "itemListElement": [{"@type": "ListItem", "position": i, "url": abs_url(lang, "apps/" + a["id"] + "/"), "name": a["name"]} for i, a in enumerate(list_apps, 1)],
    })]
    return page(lang, body, title=title, description=intro[:300], path=path, cats=cats, presets=presets, extra_ld=ld)


def privacy_page(lang, cats, presets):
    t = T[lang]
    body = f'<div class="wrap narrow page prose"><h1>{t["privacy"]}</h1>{t["privacy_html"]}</div>'
    return page(lang, body, title=f'{t["privacy"]} | WinMate', description=t["privacy_meta"], path="privacy/", cats=cats, presets=presets)


def not_found_page(cats, presets):
    t = T["en"]
    body = f"""<div class="wrap narrow page center"><p class="big-code">404</p><h1>{t['nf_title']}</h1><p>{t['nf_text']}</p>
<p><a class="btn btn-primary" href="/">{t['nf_home']}</a> <a class="btn" href="/de/">Deutsch</a></p></div>"""
    return page("en", body, title="404 | WinMate", description=t["nf_title"], path="404", alt_path="", cats=cats, presets=presets, noindex=True)


# ----------------------------------------------------------------------------- machine-readable
def llms_txt(apps, cats, presets):
    lines = [
        "# WinMate",
        "",
        f"> WinMate ({SITE_URL}) is a free, open-source web app that generates one PowerShell/CMD script to install many Windows programs at once "
        f"with winget, Scoop or Chocolatey. It lists {len(apps)} curated apps in {len(cats)} categories, verified against the official package repositories. "
        "The script asks for administrator rights only once, installs everything silently, retries failures and prints a summary.",
        "",
        "Key facts:",
        "- Price: free, MIT licensed, no account, no tracking. Scripts are generated locally in the browser.",
        "- Supported: Windows 10 and Windows 11. winget is the default; Scoop and Chocolatey are optional.",
        "- Output: `WinMate-Install.cmd` (double-click), a `.ps1` file, or a PowerShell snippet to paste.",
        "- One UAC prompt: the script relaunches itself elevated once; apps that refuse elevation (e.g. Spotify) run as the normal user.",
        "- Bundles: curated sets such as Essentials, Gaming PC, Retro Gaming, Streamer, Developer, Server Admin and Homeserver.",
        "- Keyboard shortcuts: / search, arrow keys navigate, Space select, S script, ? help.",
        "- Languages: English (/) and German (/de/).",
        "- Inspired by TuxMate (https://tuxmate.com), the bulk app installer for Linux.",
        "",
        "## Main pages",
        f"- [App catalog and script builder]({SITE_URL}/#apps): select apps, choose a package manager, download the script",
        f"- [How it works]({SITE_URL}/about/): single admin prompt, package manager comparison",
        f"- [FAQ]({SITE_URL}/about/#faq)",
        f"- [German version]({SITE_URL}/de/)",
        "",
        "## Data",
        f"- [Full catalog with install commands]({SITE_URL}/llms-full.txt): every app with winget, Scoop and Chocolatey commands",
        f"- [apps.json]({SITE_URL}/apps.json): machine-readable catalog (id, name, category, package ids, homepage, descriptions)",
        f"- [Source code]({REPO_URL})",
        "",
        "## Categories",
    ]
    lines += [f"- [{c['en']['name']}]({SITE_URL}/category/{c['id']}/): {c['en']['intro']}" for c in cats]
    lines += ["", "## Bundles"]
    lines += [f"- [{p['en']['title']}]({SITE_URL}/bundle/{p['id']}/): {p['en']['intro']}" for p in presets]
    lines += ["", "## Optional", "- Update everything later with `winget upgrade --all`, `scoop update *` or `choco upgrade all -y`.", ""]
    return "\n".join(lines)


def llms_full_txt(apps, cats, by_cat):
    out = [f"# WinMate app catalog", "", f"{len(apps)} Windows apps with verified package IDs. Generated {TODAY}. Source: {SITE_URL}", ""]
    for c in cats:
        out += [f"## {c['en']['name']}", "", c["en"]["intro"], ""]
        for a in by_cat[c["id"]]:
            out.append(f"### {a['name']}")
            out.append(a["description"]["en"])
            out.append(f"- Homepage: {a['homepage']}")
            out.append(f"- Details: {SITE_URL}/apps/{a['id']}/")
            for pm, cmd in pm_commands(a).items():
                out.append(f"- {PM_LABEL[pm]}: `{cmd.replace(chr(10), ' && ')}`")
            if a.get("noAdmin"):
                out.append("- Note: installer refuses to run as administrator; WinMate installs it as the normal user.")
            out.append("")
    return "\n".join(out)


def apps_json(apps, cats):
    return json.dumps({
        "generated": TODAY, "site": SITE_URL, "source": REPO_URL,
        "categories": [{"id": c["id"], "name": c["en"]["name"], "name_de": c["de"]["name"]} for c in cats],
        "apps": [{
            "id": a["id"], "name": a["name"], "category": a["category"], "homepage": a["homepage"],
            "winget": a["winget"], "scoop": a.get("scoop"), "choco": a.get("choco"),
            "noAdmin": bool(a.get("noAdmin")), "description": a["description"],
            "icon": f"{SITE_URL}/icons/{a['iconFile']}", "url": f"{SITE_URL}/apps/{a['id']}/",
        } for a in apps],
    }, ensure_ascii=False, indent=1)


def sitemap(paths):
    today = TODAY
    entries = []
    for p, prio in paths:
        en, de = abs_url("en", p), abs_url("de", p)
        for loc in (en, de):
            entries.append(
                f"<url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{prio}</priority>"
                f'<xhtml:link rel="alternate" hreflang="en" href="{en}"/>'
                f'<xhtml:link rel="alternate" hreflang="de" href="{de}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{en}"/></url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(entries) + "\n</urlset>\n")


# ----------------------------------------------------------------------------- assets
ASSETS = {}


def hashed_copy(rel, content=None):
    """Copy src/<rel> to dist with a content hash in the file name (cache-busting)."""
    data = content if content is not None else (SRC / rel).read_bytes()
    digest = hashlib.sha256(data).hexdigest()[:10]
    p = Path(rel)
    out_rel = str(p.with_name(f"{p.stem}.{digest}{p.suffix}")).replace("\\", "/")
    (DIST / out_rel).parent.mkdir(parents=True, exist_ok=True)
    (DIST / out_rel).write_bytes(data)
    ASSETS[rel] = out_rel


def write(rel, text):
    p = DIST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def build():
    apps, cats, presets, by_cat = load_data()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # static assets
    shutil.copytree(SRC / "icons", DIST / "icons")
    shutil.copytree(SRC / "img", DIST / "img")
    shutil.copy(SRC / "img" / "favicon.ico", DIST / "favicon.ico")
    for f in ("fonts/silkscreen-400.woff2", "fonts/silkscreen-700.woff2"):
        hashed_copy(f)
    css = (SRC / "css" / "style.css").read_text(encoding="utf-8").replace("/*__STARS__*/", pixel.star_css())
    for f in ("fonts/silkscreen-400.woff2", "fonts/silkscreen-700.woff2"):
        css = css.replace(f"../{f}", "/" + ASSETS[f])
    hashed_copy("css/style.css", css.encode("utf-8"))
    engine = (SRC / "ps" / "engine.ps1").read_text(encoding="utf-8").replace("https://winmate.pages.dev", SITE_URL)
    js = (SRC / "js" / "app.js").read_text(encoding="utf-8")
    js = js.replace('"__ENGINE__"', json.dumps(engine)).replace('"__SITE_URL__"', json.dumps(SITE_URL))
    hashed_copy("js/app.js", js.encode("utf-8"))

    paths = [("", "1.0"), ("about/", "0.7")]
    for lang in LANGS:
        prefix = "de/" if lang == "de" else ""
        write(prefix + "index.html", home_page(lang, apps, cats, presets, by_cat))
        write(prefix + "privacy/index.html", privacy_page(lang, cats, presets))
        write(prefix + "about/index.html", about_page(lang, apps, cats, presets))
        for a in apps:
            write(f"{prefix}apps/{a['id']}/index.html", app_page(lang, a, apps, cats, presets, by_cat))
        for c in cats:
            t = T[lang]
            write(f"{prefix}category/{c['id']}/index.html", list_page(
                lang, kind="category", item=c, list_apps=by_cat[c["id"]], apps=apps, cats=cats, presets=presets,
                title=t["cat_title"].format(name=c[lang]["name"]), h1=t["cat_h1"].format(name=c[lang]["name"]), intro=c[lang]["intro"]))
        for p in presets:
            write(f"{prefix}bundle/{p['id']}/index.html", list_page(
                lang, kind="bundle", item=p, list_apps=[next(a for a in apps if a["id"] == aid) for aid in p["apps"]],
                apps=apps, cats=cats, presets=presets, title=f"{p[lang]['title']} | WinMate", h1=p[lang]["title"], intro=p[lang]["intro"]))
    paths += [(f"apps/{a['id']}/", "0.6") for a in apps]
    paths += [(f"category/{c['id']}/", "0.8") for c in cats]
    paths += [(f"bundle/{p['id']}/", "0.8") for p in presets]
    paths += [("privacy/", "0.2")]

    write("404.html", not_found_page(cats, presets))
    write("sitemap.xml", sitemap(paths))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("llms.txt", llms_txt(apps, cats, presets))
    write("llms-full.txt", llms_full_txt(apps, cats, by_cat))
    write("apps.json", apps_json(apps, cats))
    write("site.webmanifest", json.dumps({
        "name": "WinMate – Windows bulk installer", "short_name": "WinMate", "start_url": "/", "display": "standalone",
        "background_color": "#0b1020", "theme_color": "#0b1020",
        "icons": [{"src": "/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/img/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, indent=1))
    write("_headers", HEADERS)
    write("_redirects", "/de /de/ 301\n/index.html / 301\n/de/index.html /de/ 301\n")
    n_pages = sum(1 for _ in DIST.rglob("*.html"))
    print(f"Built {n_pages} pages, {len(apps)} apps, {len(cats)} categories -> {DIST}")


HEADERS = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  X-Frame-Options: DENY
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self' 'sha256-THEME_HASH'; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'

/css/*
  Cache-Control: public, max-age=31536000, immutable
/js/*
  Cache-Control: public, max-age=31536000, immutable
/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/icons/*
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400
/img/*
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400
/*.txt
  Content-Type: text/plain; charset=utf-8
"""

if __name__ == "__main__":
    import base64
    theme_js = "try{var t=localStorage.getItem('wm-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}"
    HEADERS = HEADERS.replace("THEME_HASH", base64.b64encode(hashlib.sha256(theme_js.encode()).digest()).decode())
    build()
