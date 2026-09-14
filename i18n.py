"""UI texts for the WinMate site (English and German)."""

SCHEMA_CATEGORY = {
    "browsers": "BrowserApplication", "communication": "CommunicationApplication", "media": "MultimediaApplication",
    "av": "MultimediaApplication", "graphics": "DesignApplication", "gaming": "GameApplication",
    "office": "BusinessApplication", "notes": "BusinessApplication", "cloud": "UtilitiesApplication",
    "files": "UtilitiesApplication", "utilities": "UtilitiesApplication", "customization": "UtilitiesApplication",
    "hardware": "UtilitiesApplication", "security": "SecurityApplication", "vpn": "SecurityApplication",
    "remote": "UtilitiesApplication", "runtimes": "UtilitiesApplication", "ai": "UtilitiesApplication",
    "editors": "DeveloperApplication", "terminal": "DeveloperApplication", "devtools": "DeveloperApplication",
    "languages": "DeveloperApplication", "cli": "DeveloperApplication", "virtualization": "UtilitiesApplication",
    "selfhost": "UtilitiesApplication",
}

T = {
    "en": {
        "locale": "en_US",
        "lang_name": "English",
        "skip": "Skip to content",
        "home": "home",
        "nav_label": "Main",
        "nav_apps": "Apps",
        "nav_how": "How it works",
        "nav_bundles": "Bundles",
        "toggle_theme": "Toggle dark/light mode",
        "meta_title": "WinMate – Install all your Windows apps at once (winget, Scoop, Chocolatey)",
        "meta_description": "Pick from {n} Windows apps and get one script that installs them all silently with winget, Scoop or Chocolatey. Free, open source, no account – perfect after a fresh Windows install.",
        "hero_title": "Install all your Windows apps at once",
        "hero_lead": "Pick from {n} verified apps or start with a bundle, then get one script for winget, Scoop or Chocolatey – with a single admin prompt.",
        "hero_points_plain": "One admin prompt, verified package IDs, winget/Scoop/Chocolatey, bundles, keyboard shortcuts, English and German, no account",
        "hud_apps": "Apps",
        "hud_selected": "Selected",
        "hud_bundles": "Bundles",
        "hud_pm": "Via",
        "bundle_groups": {"basics": "Basics", "play": "Play & Create", "tech": "Tech & Server"},
        "keys_title": "Keyboard",
        "keys_short": [("/", "Search"), ("↑↓←→", "Navigate"), ("Space", "Select"), ("S", "Get script"), ("?", "All shortcuts")],
        "keys_all": [
            ("/", "Focus search"), ("Esc", "Clear search / close dialog"), ("↑ ↓ ← →", "Move between apps"),
            ("Space / Enter", "Select or deselect the focused app"), ("A", "Select all visible apps"),
            ("C", "Clear the selection"), ("U", "Undo the last clear"), ("B", "Jump to the bundles"),
            ("P or 1 2 3", "Switch package manager"), ("S", "Open the install script"),
            ("Y", "Copy the script for PowerShell"), ("D", "Download WinMate-Install.cmd"), ("?", "Show this help"),
        ],
        "keys_dialog_title": "Keyboard shortcuts",
        "nav_about": "How it works",
        "nav_security": "Security",
        "toggle_fx": "Turn animations on/off",
        "sources_title": "Package sources",
        "sources_lead": "WinMate installs exactly these packages. Versions are the latest ones found by the automated catalog check on {date}; pinned installs use them.",
        "col_manager": "Package manager",
        "col_package": "Package",
        "col_version": "Verified version",
        "col_manifest": "Source",
        "manifest_link": "Manifest",
        "opt_title": "Options",
        "opt_mode": "What should the script do?",
        "mode_install": "Install",
        "mode_upgrade": "Update",
        "mode_uninstall": "Uninstall",
        "opt_dry": "Dry run – only show what would happen, change nothing",
        "opt_restore": "Create a System Restore point first",
        "opt_pin": "Pin the versions verified on {date} (winget, Chocolatey)",
        "opt_proxy": "Proxy (optional, e.g. http://proxy:8080)",
        "dl_winget_json": "winget import file",
        "engine_info": "WinMate {version} · engine SHA-256 <code>{sha}</code> · <a href=\"{href}\">How to verify</a>",
        "profile_title": "Profile",
        "profile_hint": "Save your selection as a file and load it later – also works with winmate.ps1.",
        "profile_export": "Export",
        "profile_import": "Import",
        "security_title": "Security & trust",
        "security_meta": "What the WinMate script does with administrator rights, how packages are verified, the threat model, known limits and how to verify a script yourself.",
        "security_lead": "WinMate scripts run installers with administrator rights. This page explains exactly what they do, what protects you, where the limits are – and how to check everything yourself instead of trusting us.",
        "security_html": """<section id="what"><h2>What a WinMate script does</h2>
<ul>
<li>It only runs <code>winget</code>, <code>scoop</code> or <code>choco</code> for the packages listed at the top of the script. You see that list in the preview before downloading.</li>
<li>It asks for administrator rights <b>once</b>. Apps that refuse elevation run as your normal user through a temporary scheduled task that is removed afterwards.</li>
<li>It downloads nothing from WinMate. Installers come from the vendors, as described in the package manifests.</li>
<li>It writes logs and a run record to <code>%LOCALAPPDATA%\\WinMate</code> and, after installing, an undo script that removes only the apps this run added.</li>
<li>There is no telemetry. The website stores your selection only in your browser (<a href="{privacy}">privacy</a>).</li>
</ul></section>
<section id="verify"><h2>Verify a script</h2>
<dl class="ids"><dt>Current version</dt><dd>{version}</dd><dt>Engine SHA-256</dt><dd><code>{sha}</code></dd><dt>Built from commit</dt><dd><a href="{commit_url}" rel="noopener"><code>{commit}</code></a></dd></dl>
<p>Every generated script consists of a short configuration block (your apps) and the engine, which is identical for everyone. To check that nobody changed the engine:</p>
<ol>
<li>Download <code>winmate.ps1</code> from the <a href="{repo}/releases/latest" rel="noopener">latest GitHub release</a>. Releases are built by public GitHub Actions and carry a build provenance attestation: <code>gh attestation verify winmate.ps1 --repo baba537/WinMate</code></li>
<li>Run <code>.\\winmate.ps1 -Verify .\\WinMate-Install.cmd</code>. It prints the apps the script will install and reports <b>OK</b> only if the engine matches the published hash.</li>
<li>Or compare the engine block by hand with <a href="{repo}/blob/main/src/ps/engine.ps1" rel="noopener">src/ps/engine.ps1</a>. The website is built reproducibly from the repository, so anyone can rebuild it and compare (<code>build-info.json</code> lists the hashes).</li>
</ol>
<p>Prefer not to download anything? Use <b>Dry run</b> first: it only lists what would be installed.</p></section>
<section id="packages"><h2>How packages are verified</h2>
<ul>
<li><b>winget</b>: manifests in <a href="https://github.com/microsoft/winget-pkgs" rel="noopener">microsoft/winget-pkgs</a> are validated and scanned by Microsoft before they are published. winget checks the SHA-256 hash of every installer against its manifest and refuses to run a mismatching file. Store apps are delivered by the Microsoft Store.</li>
<li><b>Chocolatey</b>: community packages are moderated and virus-scanned; downloaded installers must carry checksums.</li>
<li><b>Scoop</b>: manifests contain hashes that Scoop checks after downloading; buckets change through reviewed pull requests.</li>
<li><b>WinMate</b>: a scheduled job checks every package ID against the official indexes each week (last check: {checked}) and records the latest versions. Scripts use <code>--exact</code> IDs and a fixed source, can pin those verified versions and can run as a dry run.</li>
</ul></section>
<section id="threats"><h2>Threat model</h2>
<div class="table-wrap"><table class="compare"><thead><tr><th scope="col">Threat</th><th scope="col">Mitigation</th><th scope="col">Remaining risk</th></tr></thead><tbody>
<tr><th scope="row">The website or hosting is compromised and serves a modified script</th><td>Open source, reproducible build in public CI, script preview, engine hash with <code>-Verify</code> against an attested release, strict Content-Security-Policy</td><td>Users who run scripts without looking at or verifying them</td></tr>
<tr><th scope="row">A package source or manifest is compromised</th><td>Review, scanning and hash checks by winget, Chocolatey and Scoop; optional version pinning; dry run</td><td>WinMate cannot detect a malicious package that the upstream repository accepted</td></tr>
<tr><th scope="row">A wrong or malicious package ID enters the catalog</th><td>Pull request review, CI validation against the official indexes, IDs visible on every app page and in the script</td><td>A reviewer overlooks a similar-looking ID</td></tr>
<tr><th scope="row">Typosquatting and ambiguous names</th><td>Exact package IDs (<code>--exact</code>) and a fixed source (<code>--source winget</code>) instead of name searches</td><td>Low</td></tr>
<tr><th scope="row">Abuse of the administrator session</th><td>One elevation for the listed packages only; no services, no persistent tasks; temporary files are deleted</td><td>Installers themselves run with full rights – inherent to installing software</td></tr>
<tr><th scope="row">A broken installation</th><td>Optional restore point, run record, undo script for newly installed apps, retry, detailed logs</td><td>Undo cannot revert changes an installer makes outside its own uninstaller</td></tr>
</tbody></table></div></section>
<section id="limits"><h2>Known limits – honestly</h2>
<ul>
<li><b>No Authenticode signature.</b> Scripts are generated in your browser for your selection, so they cannot be code-signed. Release files instead carry GitHub build provenance, and the engine hash is published.</li>
<li><b>No independent security audit yet.</b> Reviews and audits are very welcome – the code is small and readable.</li>
<li><b>Young project, single maintainer, built with AI assistance.</b> Everything is public so it can be checked; please report problems.</li>
<li><b>Not a full lifecycle or enterprise deployment tool.</b> WinMate installs, updates and removes apps and can export a winget import file, but it has no central management, offline mirror or compliance reporting. See the roadmap.</li>
</ul></section>
<section id="report"><h2>Report a vulnerability</h2>
<p>Please report security issues privately via <a href="{repo}/security/advisories/new" rel="noopener">GitHub security advisories</a>, not in public issues. Details are in <a href="{repo}/blob/main/SECURITY.md" rel="noopener">SECURITY.md</a>. Wrong package IDs and other bugs can go to the <a href="{repo}/issues" rel="noopener">issue tracker</a>.</p></section>""",
        "about_title": "How WinMate works",
        "about_meta": "How WinMate installs all your Windows apps with one script and a single admin prompt, which package manager to choose, and answers to common questions.",
        "about_lead": "WinMate turns your app selection into one install script. Here is what happens behind the scenes – and answers to the most common questions.",
        "credits_title": "Inspiration",
        "credits_html": "WinMate is inspired by <a href=\"https://tuxmate.com/\" rel=\"noopener\">TuxMate</a>, the bulk app installer for Linux by <a href=\"https://github.com/abusoww/tuxmate\" rel=\"noopener\">abusoww</a>. WinMate brings the same idea to Windows with winget, Scoop and Chocolatey.",
        "footer_inspired": "Inspired by <a href=\"https://tuxmate.com/\" rel=\"noopener\">TuxMate</a> for Linux.",
        "catalog_title": "Choose your apps",
        "catalog_lead": "Select apps, pick a package manager and get your install script. Your selection is saved in this browser.",
        "filters": "Filters",
        "pm_title": "Package manager",
        "pm_hint_winget": "Recommended. Built into Windows 10 and 11, official Microsoft repository incl. Store apps.",
        "pm_hint_scoop": "Portable installs in your user folder without admin rights. Great for developer tools.",
        "pm_hint_choco": "Large community repository. Always installs system-wide with admin rights.",
        "presets_title": "Bundles",
        "search_label": "Search apps",
        "search_placeholder": "Search {n} apps…",
        "only_selected": "Selected only",
        "no_results": "No apps match your search.",
        "noscript": "JavaScript is required to build the install script. You can still browse all apps and copy the install commands from each app page.",
        "category_page": "Category page →",
        "not_available_short": "Not available",
        "details": "Details",
        "selected": "apps selected",
        "clear": "Clear",
        "get_script": "Get install script",
        "close": "Close",
        "dlg_title": "Your install script",
        "dl_cmd": "Download WinMate-Install.cmd",
        "copy_ps": "Copy for PowerShell",
        "dl_ps1": "Download .ps1",
        "copy_link": "Copy share link",
        "show_script": "Show the script",
        "run_steps": [
            "Double-click <code>WinMate-Install.cmd</code>. If SmartScreen appears, click <b>More info → Run anyway</b>.",
            "Confirm the <b>single</b> administrator prompt. All installers then run silently.",
            "Wait for the summary. Failed apps can be retried by running the script again.",
        ],
        "how_title": "How it works",
        "how_lead": "From a fresh Windows to a fully set up PC in four steps.",
        "steps": [
            ("Pick your apps", "Browse by category, search, or start with a bundle like <em>Essentials</em> or <em>Gaming PC</em>."),
            ("Choose a package manager", "winget is built into Windows and recommended. Scoop and Chocolatey are installed automatically if you pick them."),
            ("Download and run", "Double-click <code>WinMate-Install.cmd</code> or paste the script into PowerShell. You can read every line before running it."),
            ("Done", "All apps install silently one after another. A summary shows what worked, what needs a restart and what failed."),
        ],
        "admin_title": "Why you only see one admin prompt",
        "admin_text": "Normally every installer asks for administrator rights on its own. The WinMate script restarts itself <b>once</b> with administrator rights and runs all installers from that elevated window, so they inherit the permission. Apps that refuse to install as administrator (such as Spotify) are installed afterwards as your normal user.",
        "compare_title": "winget vs. Scoop vs. Chocolatey",
        "compare_lead": "All three are free command-line package managers for Windows. Not sure? Use winget.",
        "compare_rows": [
            ("Setup", "Built into Windows 10/11", "Installed automatically", "Installed automatically"),
            ("Admin rights", "Once (WinMate)", "Not needed", "Required"),
            ("Install location", "Normal installers (Program Files)", "Portable, in your user folder", "System-wide"),
            ("Repository", "Official Microsoft repo + Store", "Community buckets", "Community repository"),
            ("Best for", "Everyone", "Developers, portable tools", "IT admins, wide catalog"),
            ("Update all apps", "<code>winget upgrade --all</code>", "<code>scoop update *</code>", "<code>choco upgrade all -y</code>"),
        ],
        "bundles_title": "Ready-made bundles",
        "bundles_lead": "Start from a curated set and adjust it to your needs.",
        "n_apps": "{n} apps",
        "faq_title": "Frequently asked questions",
        "footer_about": "WinMate generates install scripts for Windows so you can set up a new or reinstalled PC in minutes.",
        "footer_disclaimer": "WinMate is not affiliated with Microsoft or any listed software vendor. All product names, logos and trademarks belong to their respective owners. Always review scripts before running them.",
        "footer_categories": "Categories",
        "footer_bundles": "Bundles",
        "footer_project": "Project",
        "footer_report": "Report a wrong package",
        "footer_made": "Made for everyone who reinstalls Windows.",
        "privacy": "Privacy",
        "privacy_meta": "WinMate does not use cookies, tracking or analytics. Your app selection stays in your browser.",
        "privacy_html": """<p>WinMate is a static website. It has no user accounts, no cookies, no analytics and no advertising.</p>
<h2>What is stored</h2><p>Your app selection, the chosen package manager and your theme preference are stored in your browser's <code>localStorage</code> so they are still there next time. This data never leaves your device. You can delete it at any time by clearing your browser data for this site.</p>
<h2>Generated scripts</h2><p>Install scripts are generated entirely in your browser. Nothing about your selection is sent to a server. The script itself only contacts the package manager you chose (winget, Scoop or Chocolatey) and the download servers of the software vendors.</p>
<h2>Hosting</h2><p>The site is hosted on Cloudflare Pages. Like every web host, Cloudflare processes technical data such as IP addresses to deliver the site and protect it from abuse. See the <a href="https://www.cloudflare.com/privacypolicy/" rel="noopener">Cloudflare privacy policy</a>.</p>
<h2>External links</h2><p>App pages link to the official websites of the software vendors. Their privacy policies apply once you visit them.</p>""",
        "note_msstore": "This app is installed from the Microsoft Store through winget (<code>--source msstore</code>). No Microsoft account is required for free apps.",
        "note_noadmin": "{name}'s installer refuses to run with administrator rights. The WinMate script automatically installs it as your normal user.",
        "note_nonportable": "The Scoop package comes from the <em>nonportable</em> bucket and may ask for administrator rights itself.",
        "app_title": "Install {name} on Windows – winget, Scoop & Chocolatey | WinMate",
        "app_meta": "{desc}. Install {name} silently on Windows 10/11 with winget, Scoop or Chocolatey – or bundle it with other apps into one script.",
        "app_h1": "Install {name} on Windows",
        "add_to_script": "Add to my install script",
        "official_site": "Official website",
        "install_commands": "Install commands",
        "install_commands_lead": "Open PowerShell or Windows Terminal and run one of these commands to install {name}.",
        "not_available_pm": "Not available in the {pm} repository.",
        "copy": "Copy",
        "package_ids": "Package details",
        "category": "Category",
        "bulk_title": "Install {name} together with your other apps",
        "bulk_text": "Setting up a new PC? Add this app to your WinMate selection and install everything with one script and a single administrator prompt.",
        "related": "More {cat}",
        "schema_category": SCHEMA_CATEGORY,
        "categories": "Categories",
        "bundles": "Bundles",
        "cat_title": "{name} for Windows – install with winget, Scoop or Chocolatey | WinMate",
        "cat_h1": "{name} for Windows",
        "select_all_in_winmate": "Select all {n} apps in WinMate",
        "more_categories": "More categories",
        "more_bundles": "More bundles",
        "nf_title": "Page not found",
        "nf_text": "This page does not exist (anymore). The app you are looking for is probably still in the catalog.",
        "nf_home": "Back to the catalog",
        "js": {
            "selected": "apps selected", "selected_one": "app selected",
            "summary": "{n} apps · installed with {pm}",
            "warn_unavailable": "{n} selected app(s) are not available for {pm} and will be skipped: {names}",
            "warn_store": "Installed from the Microsoft Store via winget: {names}",
            "warn_noadmin": "Installed without admin rights (their installers require this): {names}",
            "warn_nonportable": "These Scoop packages may ask for admin rights themselves: {names}",
            "warn_scoop_admin": "Scoop installs apps into your user folder – no administrator prompt needed.",
            "copied": "Script copied. Paste it into PowerShell and press Enter.",
            "link_copied": "Share link copied.",
            "downloaded": "Download started.",
            "preset_added": "{name}: {n} apps added",
            "result_count": "{shown} of {total} apps",
            "select_first": "Select at least one app first.",
            "nothing_for_pm": "None of the selected apps is available for {pm}.",
            "copy_done": "Copied!",
            "own": "{n} own", "via_bundles": "{n} from bundles",
            "bundle_apps": "{sel} of {total} apps selected", "bundle_hint": "Untick apps you don't want.",
            "bundle_select": "Select bundle", "bundle_switch": "Switch to this bundle", "bundle_switch_hint": "Replaces {old}. Apps you picked yourself stay selected.",
            "bundle_add": "Add to my selection", "bundle_add_hint": "Keeps everything you already selected.",
            "bundle_only": "Only this bundle", "bundle_only_hint": "Deselects everything else.",
            "bundle_update": "Update bundle", "bundle_remove": "Remove bundle", "cancel": "Cancel",
            "tag_own": "your pick", "tag_na": "not on {pm}", "tag_other": "in {name}",
            "bundle_added": "{name} selected", "bundle_removed": "{name} removed",
            "cleared": "Selection cleared – press U to undo.", "undone": "Selection restored.",
            "all_selected": "{n} visible apps selected", "pm_now": "Package manager: {pm}", "remove_bundle": "Remove {name}",
            "summary_mode": {"install": "{n} apps · install with {pm}", "upgrade": "{n} apps · update with {pm}", "uninstall": "{n} apps · uninstall with {pm}"},
            "dry_suffix": " · dry run",
            "dl_cmd_label": "Download {file}",
            "warn_uninstall": "Uninstall mode removes the selected apps from this PC.",
            "warn_pin_scoop": "Scoop cannot pin versions; the latest versions are used.",
            "warn_pin_missing": "No verified version for: {names} – the latest version is used.",
            "profile_exported": "Profile saved.", "profile_imported": "Profile loaded: {n} apps.", "profile_invalid": "This file is not a WinMate profile.",
        },
    },
    "de": {
        "locale": "de_DE",
        "lang_name": "Deutsch",
        "skip": "Zum Inhalt springen",
        "home": "Startseite",
        "nav_label": "Hauptmenü",
        "nav_apps": "Apps",
        "nav_how": "So funktioniert's",
        "nav_bundles": "Pakete",
        "toggle_theme": "Hell/Dunkel umschalten",
        "meta_title": "WinMate – Alle Windows-Programme auf einmal installieren (winget, Scoop, Chocolatey)",
        "meta_description": "Wähle aus {n} Windows-Programmen und erhalte ein Skript, das alle automatisch mit winget, Scoop oder Chocolatey installiert. Kostenlos, Open Source, ohne Konto – ideal nach einer Windows-Neuinstallation.",
        "hero_title": "Alle Windows-Programme auf einmal installieren",
        "hero_lead": "Wähle aus {n} geprüften Apps oder starte mit einem Bundle – und erhalte ein Skript für winget, Scoop oder Chocolatey mit nur einer Admin-Abfrage.",
        "hero_points_plain": "Eine Admin-Abfrage, geprüfte Paket-IDs, winget/Scoop/Chocolatey, Bundles, Tastenkürzel, Deutsch und Englisch, ohne Konto",
        "hud_apps": "Apps",
        "hud_selected": "Gewählt",
        "hud_bundles": "Bundles",
        "hud_pm": "Via",
        "bundle_groups": {"basics": "Basics", "play": "Spielen & Kreativ", "tech": "Technik & Server"},
        "keys_title": "Tastatur",
        "keys_short": [("/", "Suche"), ("↑↓←→", "Navigieren"), ("Leertaste", "Auswählen"), ("S", "Skript holen"), ("?", "Alle Kürzel")],
        "keys_all": [
            ("/", "Suche fokussieren"), ("Esc", "Suche leeren / Dialog schließen"), ("↑ ↓ ← →", "Zwischen Apps wechseln"),
            ("Leertaste / Enter", "Fokussierte App an- oder abwählen"), ("A", "Alle sichtbaren Apps auswählen"),
            ("C", "Auswahl leeren"), ("U", "Leeren rückgängig machen"), ("B", "Zu den Bundles springen"),
            ("P oder 1 2 3", "Paketmanager wechseln"), ("S", "Installationsskript öffnen"),
            ("Y", "Skript für PowerShell kopieren"), ("D", "WinMate-Install.cmd herunterladen"), ("?", "Diese Hilfe anzeigen"),
        ],
        "keys_dialog_title": "Tastenkürzel",
        "nav_about": "So funktioniert's",
        "nav_security": "Sicherheit",
        "toggle_fx": "Animationen an/aus",
        "sources_title": "Paketquellen",
        "sources_lead": "WinMate installiert genau diese Pakete. Die Versionen sind die neuesten, die der automatische Katalog-Check am {date} gefunden hat; gepinnte Installationen verwenden sie.",
        "col_manager": "Paketmanager",
        "col_package": "Paket",
        "col_version": "Geprüfte Version",
        "col_manifest": "Quelle",
        "manifest_link": "Manifest",
        "opt_title": "Optionen",
        "opt_mode": "Was soll das Skript tun?",
        "mode_install": "Installieren",
        "mode_upgrade": "Aktualisieren",
        "mode_uninstall": "Deinstallieren",
        "opt_dry": "Probelauf – nur anzeigen, was passieren würde, nichts ändern",
        "opt_restore": "Vorher einen Systemwiederherstellungspunkt erstellen",
        "opt_pin": "Am {date} geprüfte Versionen festschreiben (winget, Chocolatey)",
        "opt_proxy": "Proxy (optional, z. B. http://proxy:8080)",
        "dl_winget_json": "winget-Importdatei",
        "engine_info": "WinMate {version} · Engine-SHA-256 <code>{sha}</code> · <a href=\"{href}\">So prüfst du das Skript</a>",
        "profile_title": "Profil",
        "profile_hint": "Speichere deine Auswahl als Datei und lade sie später wieder – funktioniert auch mit winmate.ps1.",
        "profile_export": "Exportieren",
        "profile_import": "Importieren",
        "security_title": "Sicherheit & Vertrauen",
        "security_meta": "Was das WinMate-Skript mit Administratorrechten tut, wie Pakete geprüft werden, das Bedrohungsmodell, bekannte Grenzen und wie du ein Skript selbst verifizierst.",
        "security_lead": "WinMate-Skripte führen Installer mit Administratorrechten aus. Diese Seite erklärt genau, was sie tun, was dich schützt, wo die Grenzen liegen – und wie du alles selbst prüfst, statt uns zu vertrauen.",
        "security_html": """<section id="what"><h2>Was ein WinMate-Skript tut</h2>
<ul>
<li>Es führt nur <code>winget</code>, <code>scoop</code> oder <code>choco</code> für die Pakete aus, die oben im Skript stehen. Diese Liste siehst du vor dem Download in der Vorschau.</li>
<li>Es fragt <b>einmal</b> nach Administratorrechten. Apps, die keine Adminrechte vertragen, laufen über eine temporäre geplante Aufgabe als normaler Benutzer; die Aufgabe wird danach gelöscht.</li>
<li>Es lädt nichts von WinMate herunter. Die Installer kommen von den Herstellern, wie in den Paket-Manifesten beschrieben.</li>
<li>Es schreibt Protokolle und einen Lauf-Datensatz nach <code>%LOCALAPPDATA%\\WinMate</code> und nach der Installation ein Undo-Skript, das nur die in diesem Lauf neu installierten Apps entfernt.</li>
<li>Es gibt keine Telemetrie. Die Website speichert deine Auswahl nur in deinem Browser (<a href="{privacy}">Datenschutz</a>).</li>
</ul></section>
<section id="verify"><h2>Ein Skript verifizieren</h2>
<dl class="ids"><dt>Aktuelle Version</dt><dd>{version}</dd><dt>Engine-SHA-256</dt><dd><code>{sha}</code></dd><dt>Gebaut aus Commit</dt><dd><a href="{commit_url}" rel="noopener"><code>{commit}</code></a></dd></dl>
<p>Jedes erzeugte Skript besteht aus einem kurzen Konfigurationsblock (deine Apps) und der Engine, die für alle identisch ist. So prüfst du, dass niemand die Engine verändert hat:</p>
<ol>
<li>Lade <code>winmate.ps1</code> aus dem <a href="{repo}/releases/latest" rel="noopener">neuesten GitHub-Release</a>. Releases werden von öffentlichen GitHub Actions gebaut und tragen einen Herkunftsnachweis (Build Provenance): <code>gh attestation verify winmate.ps1 --repo baba537/WinMate</code></li>
<li>Führe <code>.\\winmate.ps1 -Verify .\\WinMate-Install.cmd</code> aus. Es zeigt die Apps, die das Skript installiert, und meldet nur dann <b>OK</b>, wenn die Engine zum veröffentlichten Hash passt.</li>
<li>Oder vergleiche den Engine-Block von Hand mit <a href="{repo}/blob/main/src/ps/engine.ps1" rel="noopener">src/ps/engine.ps1</a>. Die Website wird reproduzierbar aus dem Repository gebaut, jeder kann sie nachbauen und vergleichen (<code>build-info.json</code> enthält die Hashes).</li>
</ol>
<p>Du willst erst gar nichts ausführen? Nutze zuerst den <b>Probelauf</b>: Er zeigt nur, was installiert würde.</p></section>
<section id="packages"><h2>Wie Pakete geprüft werden</h2>
<ul>
<li><b>winget</b>: Manifeste in <a href="https://github.com/microsoft/winget-pkgs" rel="noopener">microsoft/winget-pkgs</a> werden von Microsoft vor der Veröffentlichung validiert und gescannt. winget prüft den SHA-256-Hash jedes Installers gegen das Manifest und führt abweichende Dateien nicht aus. Store-Apps liefert der Microsoft Store.</li>
<li><b>Chocolatey</b>: Community-Pakete werden moderiert und auf Viren gescannt; heruntergeladene Installer brauchen Prüfsummen.</li>
<li><b>Scoop</b>: Manifeste enthalten Hashes, die Scoop nach dem Download prüft; Buckets ändern sich nur über geprüfte Pull Requests.</li>
<li><b>WinMate</b>: Ein geplanter Job prüft jede Woche alle Paket-IDs gegen die offiziellen Indizes (letzte Prüfung: {checked}) und speichert die neuesten Versionen. Skripte nutzen exakte IDs (<code>--exact</code>) und eine feste Quelle, können diese geprüften Versionen festschreiben und als Probelauf laufen.</li>
</ul></section>
<section id="threats"><h2>Bedrohungsmodell</h2>
<div class="table-wrap"><table class="compare"><thead><tr><th scope="col">Bedrohung</th><th scope="col">Schutzmaßnahme</th><th scope="col">Restrisiko</th></tr></thead><tbody>
<tr><th scope="row">Website oder Hosting werden kompromittiert und liefern ein verändertes Skript</th><td>Open Source, reproduzierbarer Build in öffentlicher CI, Skriptvorschau, Engine-Hash mit <code>-Verify</code> gegen ein nachweislich gebautes Release, strenge Content-Security-Policy</td><td>Nutzer, die Skripte ungeprüft ausführen</td></tr>
<tr><th scope="row">Eine Paketquelle oder ein Manifest wird kompromittiert</th><td>Prüfung, Scans und Hash-Kontrollen durch winget, Chocolatey und Scoop; optionales Festschreiben von Versionen; Probelauf</td><td>WinMate kann kein bösartiges Paket erkennen, das das Upstream-Repository akzeptiert hat</td></tr>
<tr><th scope="row">Eine falsche oder bösartige Paket-ID gelangt in den Katalog</th><td>Review von Pull Requests, CI-Prüfung gegen die offiziellen Indizes, IDs auf jeder App-Seite und im Skript sichtbar</td><td>Ein Reviewer übersieht eine ähnlich aussehende ID</td></tr>
<tr><th scope="row">Typosquatting und mehrdeutige Namen</th><td>Exakte Paket-IDs (<code>--exact</code>) und feste Quelle (<code>--source winget</code>) statt Namenssuche</td><td>Gering</td></tr>
<tr><th scope="row">Missbrauch der Administratorsitzung</th><td>Nur eine Rechteerhöhung für die aufgelisteten Pakete; keine Dienste, keine dauerhaften Aufgaben; temporäre Dateien werden gelöscht</td><td>Installer selbst laufen mit vollen Rechten – das liegt in der Natur von Softwareinstallationen</td></tr>
<tr><th scope="row">Eine Installation geht schief</th><td>Optionaler Wiederherstellungspunkt, Lauf-Datensatz, Undo-Skript für neu installierte Apps, Wiederholung, ausführliche Logs</td><td>Undo kann Änderungen außerhalb des jeweiligen Deinstallers nicht zurücknehmen</td></tr>
</tbody></table></div></section>
<section id="limits"><h2>Bekannte Grenzen – ehrlich gesagt</h2>
<ul>
<li><b>Keine Authenticode-Signatur.</b> Skripte werden in deinem Browser für deine Auswahl erzeugt und können daher nicht signiert werden. Release-Dateien haben stattdessen einen GitHub-Herkunftsnachweis, und der Engine-Hash ist veröffentlicht.</li>
<li><b>Noch kein unabhängiges Sicherheitsaudit.</b> Reviews und Audits sind sehr willkommen – der Code ist klein und gut lesbar.</li>
<li><b>Junges Projekt, ein Maintainer, mit KI-Unterstützung gebaut.</b> Alles ist öffentlich und damit überprüfbar; bitte melde Probleme.</li>
<li><b>Kein vollständiges Lifecycle- oder Enterprise-Deployment-Tool.</b> WinMate installiert, aktualisiert und entfernt Apps und exportiert winget-Importdateien, hat aber keine zentrale Verwaltung, keinen Offline-Spiegel und kein Compliance-Reporting. Siehe Roadmap.</li>
</ul></section>
<section id="report"><h2>Sicherheitslücke melden</h2>
<p>Bitte melde Sicherheitsprobleme vertraulich über <a href="{repo}/security/advisories/new" rel="noopener">GitHub Security Advisories</a>, nicht in öffentlichen Issues. Details stehen in <a href="{repo}/blob/main/SECURITY.md" rel="noopener">SECURITY.md</a>. Falsche Paket-IDs und andere Fehler gehören in den <a href="{repo}/issues" rel="noopener">Issue-Tracker</a>.</p></section>""",
        "about_title": "So funktioniert WinMate",
        "about_meta": "Wie WinMate alle Windows-Programme mit einem Skript und nur einer Admin-Abfrage installiert, welcher Paketmanager passt und Antworten auf häufige Fragen.",
        "about_lead": "WinMate macht aus deiner App-Auswahl ein einziges Installationsskript. Hier siehst du, was dabei passiert – und Antworten auf die häufigsten Fragen.",
        "credits_title": "Inspiration",
        "credits_html": "WinMate ist inspiriert von <a href=\"https://tuxmate.com/\" rel=\"noopener\">TuxMate</a>, dem Massen-Installer für Linux von <a href=\"https://github.com/abusoww/tuxmate\" rel=\"noopener\">abusoww</a>. WinMate überträgt die Idee mit winget, Scoop und Chocolatey auf Windows.",
        "footer_inspired": "Inspiriert von <a href=\"https://tuxmate.com/\" rel=\"noopener\">TuxMate</a> für Linux.",
        "catalog_title": "Wähle deine Apps",
        "catalog_lead": "Apps auswählen, Paketmanager festlegen und Installationsskript holen. Deine Auswahl wird in diesem Browser gespeichert.",
        "filters": "Filter",
        "pm_title": "Paketmanager",
        "pm_hint_winget": "Empfohlen. In Windows 10 und 11 integriert, offizielles Microsoft-Repository inkl. Store-Apps.",
        "pm_hint_scoop": "Portable Installation im Benutzerordner ohne Adminrechte. Ideal für Entwickler-Tools.",
        "pm_hint_choco": "Großes Community-Repository. Installiert immer systemweit mit Adminrechten.",
        "presets_title": "Bundles",
        "search_label": "Apps durchsuchen",
        "search_placeholder": "{n} Apps durchsuchen…",
        "only_selected": "Nur ausgewählte",
        "no_results": "Keine App passt zu deiner Suche.",
        "noscript": "Für das Installationsskript wird JavaScript benötigt. Alle Apps und ihre Installationsbefehle findest du trotzdem auf den jeweiligen App-Seiten.",
        "category_page": "Zur Kategorie →",
        "not_available_short": "Nicht verfügbar",
        "details": "Details",
        "selected": "Apps ausgewählt",
        "clear": "Leeren",
        "get_script": "Installationsskript holen",
        "close": "Schließen",
        "dlg_title": "Dein Installationsskript",
        "dl_cmd": "WinMate-Install.cmd herunterladen",
        "copy_ps": "Für PowerShell kopieren",
        "dl_ps1": ".ps1 herunterladen",
        "copy_link": "Link zum Teilen kopieren",
        "show_script": "Skript anzeigen",
        "run_steps": [
            "Doppelklick auf <code>WinMate-Install.cmd</code>. Erscheint SmartScreen, klicke auf <b>Weitere Informationen → Trotzdem ausführen</b>.",
            "Bestätige die <b>einzige</b> Administrator-Abfrage. Danach laufen alle Installationen still im Hintergrund.",
            "Warte auf die Zusammenfassung. Fehlgeschlagene Apps kannst du durch erneutes Ausführen nachinstallieren.",
        ],
        "how_title": "So funktioniert's",
        "how_lead": "Vom frischen Windows zum fertig eingerichteten PC in vier Schritten.",
        "steps": [
            ("Apps auswählen", "Nach Kategorien stöbern, suchen oder mit einem Paket wie <em>Grundausstattung</em> oder <em>Gaming-PC</em> starten."),
            ("Paketmanager wählen", "winget ist in Windows integriert und empfohlen. Scoop und Chocolatey werden bei Bedarf automatisch installiert."),
            ("Herunterladen und starten", "Doppelklick auf <code>WinMate-Install.cmd</code> oder das Skript in PowerShell einfügen. Jede Zeile ist vorher lesbar."),
            ("Fertig", "Alle Apps werden nacheinander still installiert. Eine Zusammenfassung zeigt, was geklappt hat, was einen Neustart braucht und was fehlgeschlagen ist."),
        ],
        "admin_title": "Warum nur eine Admin-Abfrage erscheint",
        "admin_text": "Normalerweise fragt jeder Installer einzeln nach Administratorrechten. Das WinMate-Skript startet sich <b>einmal</b> mit Adminrechten neu und führt alle Installationen aus diesem Fenster aus – sie erben die Berechtigung. Apps, die sich nicht als Administrator installieren lassen (z. B. Spotify), werden danach mit deinem normalen Benutzerkonto installiert.",
        "compare_title": "winget vs. Scoop vs. Chocolatey",
        "compare_lead": "Alle drei sind kostenlose Kommandozeilen-Paketmanager für Windows. Unsicher? Nimm winget.",
        "compare_rows": [
            ("Einrichtung", "In Windows 10/11 integriert", "Wird automatisch installiert", "Wird automatisch installiert"),
            ("Adminrechte", "Einmal (WinMate)", "Nicht nötig", "Erforderlich"),
            ("Installationsort", "Normale Installer (Programme)", "Portabel im Benutzerordner", "Systemweit"),
            ("Repository", "Offizielles Microsoft-Repo + Store", "Community-Buckets", "Community-Repository"),
            ("Ideal für", "Alle", "Entwickler, portable Tools", "IT-Admins, große Auswahl"),
            ("Alles aktualisieren", "<code>winget upgrade --all</code>", "<code>scoop update *</code>", "<code>choco upgrade all -y</code>"),
        ],
        "bundles_title": "Fertige Pakete",
        "bundles_lead": "Starte mit einer kuratierten Auswahl und passe sie an.",
        "n_apps": "{n} Apps",
        "faq_title": "Häufige Fragen",
        "footer_about": "WinMate erstellt Installationsskripte für Windows, damit ein neuer oder frisch installierter PC in wenigen Minuten eingerichtet ist.",
        "footer_disclaimer": "WinMate steht in keiner Verbindung zu Microsoft oder den aufgeführten Softwareherstellern. Alle Produktnamen, Logos und Marken gehören ihren jeweiligen Inhabern. Prüfe Skripte immer, bevor du sie ausführst.",
        "footer_categories": "Kategorien",
        "footer_bundles": "Pakete",
        "footer_project": "Projekt",
        "footer_report": "Falsches Paket melden",
        "footer_made": "Für alle, die Windows neu installieren.",
        "privacy": "Datenschutz",
        "privacy_meta": "WinMate nutzt keine Cookies, kein Tracking und keine Analyse-Tools. Deine App-Auswahl bleibt in deinem Browser.",
        "privacy_html": """<p>WinMate ist eine statische Website. Es gibt keine Benutzerkonten, keine Cookies, keine Analyse-Tools und keine Werbung.</p>
<h2>Was gespeichert wird</h2><p>Deine App-Auswahl, der gewählte Paketmanager und dein Farbschema werden im <code>localStorage</code> deines Browsers gespeichert, damit sie beim nächsten Besuch noch da sind. Diese Daten verlassen dein Gerät nicht. Du kannst sie jederzeit löschen, indem du die Browserdaten für diese Seite entfernst.</p>
<h2>Erzeugte Skripte</h2><p>Installationsskripte werden vollständig in deinem Browser erzeugt. Deine Auswahl wird an keinen Server übertragen. Das Skript selbst kontaktiert nur den gewählten Paketmanager (winget, Scoop oder Chocolatey) und die Download-Server der Softwarehersteller.</p>
<h2>Hosting</h2><p>Die Seite wird über Cloudflare Pages ausgeliefert. Wie jeder Webhoster verarbeitet Cloudflare dabei technische Daten wie IP-Adressen, um die Seite bereitzustellen und vor Missbrauch zu schützen. Details in der <a href="https://www.cloudflare.com/de-de/privacypolicy/" rel="noopener">Datenschutzerklärung von Cloudflare</a>.</p>
<h2>Externe Links</h2><p>App-Seiten verlinken auf die offiziellen Websites der Hersteller. Beim Besuch gelten deren Datenschutzbestimmungen.</p>""",
        "note_msstore": "Diese App wird über winget aus dem Microsoft Store installiert (<code>--source msstore</code>). Für kostenlose Apps ist kein Microsoft-Konto nötig.",
        "note_noadmin": "Der Installer von {name} verweigert die Ausführung mit Adminrechten. Das WinMate-Skript installiert die App deshalb automatisch mit deinem normalen Benutzerkonto.",
        "note_nonportable": "Das Scoop-Paket stammt aus dem <em>nonportable</em>-Bucket und fragt eventuell selbst nach Adminrechten.",
        "app_title": "{name} unter Windows installieren – winget, Scoop & Chocolatey | WinMate",
        "app_meta": "{desc}. {name} unter Windows 10/11 still mit winget, Scoop oder Chocolatey installieren – oder zusammen mit anderen Apps in einem Skript.",
        "app_h1": "{name} unter Windows installieren",
        "add_to_script": "Zu meinem Installationsskript hinzufügen",
        "official_site": "Offizielle Website",
        "install_commands": "Installationsbefehle",
        "install_commands_lead": "Öffne PowerShell oder Windows Terminal und führe einen dieser Befehle aus, um {name} zu installieren.",
        "not_available_pm": "Im {pm}-Repository nicht verfügbar.",
        "copy": "Kopieren",
        "package_ids": "Paketdetails",
        "category": "Kategorie",
        "bulk_title": "{name} zusammen mit deinen anderen Apps installieren",
        "bulk_text": "Du richtest einen neuen PC ein? Füge die App deiner WinMate-Auswahl hinzu und installiere alles mit einem Skript und nur einer Admin-Abfrage.",
        "related": "Weitere Apps: {cat}",
        "schema_category": SCHEMA_CATEGORY,
        "categories": "Kategorien",
        "bundles": "Pakete",
        "cat_title": "{name} für Windows – mit winget, Scoop oder Chocolatey installieren | WinMate",
        "cat_h1": "{name} für Windows",
        "select_all_in_winmate": "Alle {n} Apps in WinMate auswählen",
        "more_categories": "Weitere Kategorien",
        "more_bundles": "Weitere Pakete",
        "nf_title": "Seite nicht gefunden",
        "nf_text": "Diese Seite gibt es nicht (mehr). Die gesuchte App ist wahrscheinlich trotzdem im Katalog.",
        "nf_home": "Zurück zum Katalog",
        "js": {
            "selected": "Apps ausgewählt", "selected_one": "App ausgewählt",
            "summary": "{n} Apps · Installation mit {pm}",
            "warn_unavailable": "{n} ausgewählte App(s) gibt es nicht für {pm}, sie werden übersprungen: {names}",
            "warn_store": "Wird über winget aus dem Microsoft Store installiert: {names}",
            "warn_noadmin": "Wird ohne Adminrechte installiert (der Installer verlangt das): {names}",
            "warn_nonportable": "Diese Scoop-Pakete fragen eventuell selbst nach Adminrechten: {names}",
            "warn_scoop_admin": "Scoop installiert in deinen Benutzerordner – es ist keine Admin-Abfrage nötig.",
            "copied": "Skript kopiert. In PowerShell einfügen und Enter drücken.",
            "link_copied": "Link zum Teilen kopiert.",
            "downloaded": "Download gestartet.",
            "preset_added": "{name}: {n} Apps hinzugefügt",
            "result_count": "{shown} von {total} Apps",
            "select_first": "Wähle zuerst mindestens eine App aus.",
            "nothing_for_pm": "Keine der ausgewählten Apps ist für {pm} verfügbar.",
            "copy_done": "Kopiert!",
            "own": "{n} eigene", "via_bundles": "{n} aus Bundles",
            "bundle_apps": "{sel} von {total} Apps ausgewählt", "bundle_hint": "Hake Apps ab, die du nicht willst.",
            "bundle_select": "Bundle auswählen", "bundle_switch": "Zu diesem Bundle wechseln", "bundle_switch_hint": "Ersetzt {old}. Deine selbst gewählten Apps bleiben ausgewählt.",
            "bundle_add": "Zur Auswahl hinzufügen", "bundle_add_hint": "Behält alles, was du schon ausgewählt hast.",
            "bundle_only": "Nur dieses Bundle", "bundle_only_hint": "Alles andere wird abgewählt.",
            "bundle_update": "Bundle aktualisieren", "bundle_remove": "Bundle entfernen", "cancel": "Abbrechen",
            "tag_own": "selbst gewählt", "tag_na": "nicht bei {pm}", "tag_other": "in {name}",
            "bundle_added": "{name} ausgewählt", "bundle_removed": "{name} entfernt",
            "cleared": "Auswahl geleert – U drücken zum Rückgängigmachen.", "undone": "Auswahl wiederhergestellt.",
            "all_selected": "{n} sichtbare Apps ausgewählt", "pm_now": "Paketmanager: {pm}", "remove_bundle": "{name} entfernen",
            "summary_mode": {"install": "{n} Apps · Installation mit {pm}", "upgrade": "{n} Apps · Aktualisierung mit {pm}", "uninstall": "{n} Apps · Deinstallation mit {pm}"},
            "dry_suffix": " · Probelauf",
            "dl_cmd_label": "{file} herunterladen",
            "warn_uninstall": "Im Deinstallationsmodus werden die ausgewählten Apps von diesem PC entfernt.",
            "warn_pin_scoop": "Scoop kann keine Versionen festschreiben; es werden die neuesten Versionen verwendet.",
            "warn_pin_missing": "Keine geprüfte Version für: {names} – es wird die neueste Version verwendet.",
            "profile_exported": "Profil gespeichert.", "profile_imported": "Profil geladen: {n} Apps.", "profile_invalid": "Diese Datei ist kein WinMate-Profil.",
        },
    },
}

FAQ = {
    "en": [
        ("Is WinMate free and safe to use?",
         "Yes. WinMate is free and open source (MIT license). The script is generated in your browser and only contains commands for the official package managers winget, Scoop or Chocolatey, which download the installers from the software vendors. You can open and read the script before running it."),
        ("Why does the script ask for administrator rights only once?",
         "Most installers need administrator rights and would each show their own UAC prompt. The WinMate script relaunches itself once with administrator rights and runs all installers from there. Apps that must not be installed as administrator, like Spotify, are installed afterwards as your normal user."),
        ("Which package manager should I choose?",
         "Use <b>winget</b> if you are unsure: it is built into Windows 10 and 11, uses Microsoft's official repository and can also install Microsoft Store apps. <b>Scoop</b> installs portable apps into your user folder without admin rights, which developers love. <b>Chocolatey</b> has a large community catalog and installs everything system-wide."),
        ("Does it work on a brand-new Windows installation?",
         "Yes, that is what WinMate is made for. winget ships with Windows 11 and up-to-date Windows 10. If it is not registered yet, the script registers it automatically or opens the App Installer page in the Microsoft Store. Scoop and Chocolatey are installed by the script when you choose them."),
        ("Windows says \"Windows protected your PC\". What now?",
         "SmartScreen shows this for files downloaded from the internet that are not signed. Click <b>More info</b> and then <b>Run anyway</b>. Alternatively, use <b>Copy for PowerShell</b> and paste the script into a PowerShell window – no file needed."),
        ("What happens with apps that are already installed?",
         "winget checks each app. If it is already installed, it is updated when a newer version exists, otherwise it is skipped. The summary marks these apps as already installed."),
        ("Which runtimes should I install on a fresh Windows?",
         "Many games and programs need the <b>Visual C++ Redistributables</b> and the <b>.NET Desktop Runtime</b>. Older games may also need <b>DirectX</b>, <b>XNA</b> or <b>OpenAL</b>. You find them in the category <i>Runtimes &amp; Dependencies</i> and in the <i>Gaming PC</i> bundle."),
        ("An app failed to install. What can I do?",
         "Simply run the script again – already installed apps are skipped. Some failures are temporary (for example when a vendor has just released a new version). The full log is saved to <code>%TEMP%\\WinMate-install.log</code>. If a package ID is wrong, please open an issue on GitHub."),
        ("How do I update all apps later?",
         "Run <code>winget upgrade --all</code>, <code>scoop update *</code> or <code>choco upgrade all -y</code> in PowerShell, depending on the package manager you used."),
        ("Can I preview, update or uninstall apps with WinMate?",
         "Yes. In the script dialog choose <b>Install</b>, <b>Update</b> or <b>Uninstall</b>, and tick <b>Dry run</b> to only see what would happen. After an installation WinMate saves an undo script in <code>%LOCALAPPDATA%\\WinMate\\runs</code> that removes exactly the apps that run added. The command-line version <code>winmate.ps1</code> offers the same options."),
        ("How can I check that a script was not tampered with?",
         "Every script contains the same engine, whose SHA-256 hash is published on the <a href=\"../security/#verify\">security page</a> and in each GitHub release. Run <code>winmate.ps1 -Verify WinMate-Install.cmd</code> to compare it and to list the apps the script will install."),
        ("Does WinMate collect any data?",
         "No. There are no cookies, no analytics and no accounts. Your selection is only stored in your own browser (localStorage) and can be shared via a link that contains the app names."),
    ],
    "de": [
        ("Ist WinMate kostenlos und sicher?",
         "Ja. WinMate ist kostenlos und Open Source (MIT-Lizenz). Das Skript wird in deinem Browser erzeugt und enthält nur Befehle für die offiziellen Paketmanager winget, Scoop oder Chocolatey, die die Installer direkt von den Herstellern laden. Du kannst das Skript vor dem Ausführen öffnen und lesen."),
        ("Warum fragt das Skript nur einmal nach Administratorrechten?",
         "Die meisten Installer brauchen Adminrechte und würden jeweils eine eigene UAC-Abfrage zeigen. Das WinMate-Skript startet sich einmal mit Adminrechten neu und führt von dort aus alle Installationen aus. Apps, die nicht als Administrator installiert werden dürfen, etwa Spotify, werden anschließend mit deinem normalen Benutzerkonto installiert."),
        ("Welchen Paketmanager soll ich wählen?",
         "Im Zweifel <b>winget</b>: Es ist in Windows 10 und 11 integriert, nutzt das offizielle Microsoft-Repository und kann auch Microsoft-Store-Apps installieren. <b>Scoop</b> installiert portable Apps ohne Adminrechte in deinen Benutzerordner – beliebt bei Entwicklern. <b>Chocolatey</b> hat einen großen Community-Katalog und installiert alles systemweit."),
        ("Funktioniert das auf einem frisch installierten Windows?",
         "Ja, genau dafür ist WinMate gemacht. winget ist bei Windows 11 und aktuellem Windows 10 dabei. Ist es noch nicht registriert, erledigt das Skript das automatisch oder öffnet die App-Installer-Seite im Microsoft Store. Scoop und Chocolatey installiert das Skript bei Bedarf selbst."),
        ("Windows meldet \"Der Computer wurde durch Windows geschützt\". Was tun?",
         "SmartScreen zeigt das bei unsignierten Dateien aus dem Internet. Klicke auf <b>Weitere Informationen</b> und dann auf <b>Trotzdem ausführen</b>. Alternativ nutzt du <b>Für PowerShell kopieren</b> und fügst das Skript in ein PowerShell-Fenster ein – ganz ohne Datei."),
        ("Was passiert mit Apps, die schon installiert sind?",
         "winget prüft jede App. Ist sie bereits installiert, wird sie aktualisiert, falls es eine neuere Version gibt, sonst übersprungen. In der Zusammenfassung erscheinen diese Apps als bereits installiert."),
        ("Welche Laufzeiten sollte ich auf einem neuen Windows installieren?",
         "Viele Spiele und Programme brauchen die <b>Visual C++ Redistributables</b> und die <b>.NET Desktop Runtime</b>. Ältere Spiele benötigen teilweise auch <b>DirectX</b>, <b>XNA</b> oder <b>OpenAL</b>. Du findest sie in der Kategorie <i>Laufzeiten &amp; Abhängigkeiten</i> und im Paket <i>Gaming-PC</i>."),
        ("Eine App ließ sich nicht installieren. Was kann ich tun?",
         "Führe das Skript einfach noch einmal aus – bereits installierte Apps werden übersprungen. Manche Fehler sind vorübergehend, etwa wenn ein Hersteller gerade eine neue Version veröffentlicht hat. Das vollständige Protokoll liegt unter <code>%TEMP%\\WinMate-install.log</code>. Ist eine Paket-ID falsch, melde es bitte auf GitHub."),
        ("Wie aktualisiere ich später alle Apps?",
         "Führe in PowerShell je nach Paketmanager <code>winget upgrade --all</code>, <code>scoop update *</code> oder <code>choco upgrade all -y</code> aus."),
        ("Kann ich mit WinMate Apps vorab prüfen, aktualisieren oder deinstallieren?",
         "Ja. Wähle im Skript-Dialog <b>Installieren</b>, <b>Aktualisieren</b> oder <b>Deinstallieren</b> und hake <b>Probelauf</b> an, um nur zu sehen, was passieren würde. Nach einer Installation speichert WinMate unter <code>%LOCALAPPDATA%\\WinMate\\runs</code> ein Undo-Skript, das genau die in diesem Lauf hinzugefügten Apps entfernt. Die Kommandozeilen-Version <code>winmate.ps1</code> bietet dieselben Optionen."),
        ("Wie prüfe ich, dass ein Skript nicht manipuliert wurde?",
         "Jedes Skript enthält dieselbe Engine, deren SHA-256-Hash auf der <a href=\"../security/#verify\">Sicherheitsseite</a> und in jedem GitHub-Release veröffentlicht ist. Mit <code>winmate.ps1 -Verify WinMate-Install.cmd</code> vergleichst du ihn und siehst, welche Apps das Skript installiert."),
        ("Sammelt WinMate Daten?",
         "Nein. Es gibt keine Cookies, keine Analyse-Tools und keine Konten. Deine Auswahl wird nur in deinem eigenen Browser (localStorage) gespeichert und lässt sich per Link teilen, der die App-Namen enthält."),
    ],
}
