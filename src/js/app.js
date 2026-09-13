/* WinMate – script builder. No dependencies. */
(function () {
  "use strict";

  var ENGINE = "__ENGINE__";
  var SITE_URL = "__SITE_URL__";
  var PM_LABEL = { winget: "winget", scoop: "Scoop", choco: "Chocolatey" };
  var STORE_KEY = "wm-selection-v2";

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };
  function fmt(s, vars) { return s.replace(/\{(\w+)\}/g, function (_, k) { return vars[k] != null ? vars[k] : ""; }); }

  /* ---------------------------------------------------------------- theme */
  $$("[data-theme-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var root = document.documentElement;
      var current = root.dataset.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
      var next = current === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      store.set("wm-theme", next);
    });
  });

  /* ---------------------------------------------------------------- toast + clipboard */
  var toastTimer;
  function toast(msg) {
    var el = $("#toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast"; el.className = "toast"; el.setAttribute("role", "status");
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.hidden = false;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); setTimeout(function () { el.hidden = true; }, 250); }, 3200);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var label = btn.querySelector("span");
      var old = label ? label.textContent : "";
      copyText(btn.getAttribute("data-copy")).then(function () {
        if (label) { label.textContent = document.documentElement.lang === "de" ? "Kopiert!" : "Copied!"; }
        btn.classList.add("done");
        setTimeout(function () { if (label) label.textContent = old; btn.classList.remove("done"); }, 1600);
      });
    });
  });

  /* ---------------------------------------------------------------- catalog */
  var catalog = $("#apps .catalog-main");
  if (!catalog) return;

  var L = JSON.parse($("#wm-i18n").textContent);
  var cards = $$(".card", catalog);
  var byId = {};
  cards.forEach(function (card) {
    card._check = card.querySelector(".card-check");
    card._text = (card.dataset.name + " " + card.dataset.id + " " + (card.dataset.winget || "") + " " +
      card.querySelector(".card-desc").textContent).toLowerCase();
    byId[card.dataset.id] = card;
  });

  var state = { pm: "winget", selected: [] };
  var saved = null;
  try { saved = JSON.parse(store.get(STORE_KEY) || "null"); } catch (e) { saved = null; }
  if (saved && Array.isArray(saved.selected)) {
    state.selected = saved.selected.filter(function (id) { return byId[id]; });
    if (PM_LABEL[saved.pm]) state.pm = saved.pm;
  }

  // URL parameters: ?apps=a,b (replace), ?add=a (append), ?preset=gaming, ?pm=scoop
  var params = new URLSearchParams(location.search);
  if (params.has("apps")) {
    state.selected = params.get("apps").split(",").filter(function (id) { return byId[id]; });
  }
  if (params.has("add")) {
    params.get("add").split(",").forEach(function (id) { if (byId[id] && state.selected.indexOf(id) < 0) state.selected.push(id); });
  }
  if (params.has("pm") && PM_LABEL[params.get("pm")]) state.pm = params.get("pm");
  if (params.has("apps") || params.has("add") || params.has("pm")) {
    history.replaceState(null, "", location.pathname + location.hash);
  }

  function save() { store.set(STORE_KEY, JSON.stringify(state)); }
  function isSelected(id) { return state.selected.indexOf(id) >= 0; }
  function available(card, pm) { return !!card.dataset[pm || state.pm]; }

  function setSelected(id, on) {
    var i = state.selected.indexOf(id);
    if (on && i < 0) state.selected.push(id);
    if (!on && i >= 0) state.selected.splice(i, 1);
  }

  /* --- rendering */
  var selbar = $("#selbar");
  var search = $("#search");
  var onlySelected = $("#onlySelected");

  function renderCards() {
    cards.forEach(function (card) {
      var on = isSelected(card.dataset.id);
      var avail = available(card);
      card._check.checked = on;
      card._check.disabled = !avail && !on;
      card.classList.toggle("selected", on);
      card.classList.toggle("unavailable", !avail);
      card.querySelector(".na-note").hidden = avail;
    });
  }

  function renderSelbar() {
    var n = state.selected.length;
    selbar.hidden = n === 0;
    document.body.classList.toggle("has-selbar", n > 0);
    $("#selCount").textContent = n;
    $("#selLabel").textContent = n === 1 ? L.selected_one : L.selected;
    var icons = $("#selIcons");
    icons.textContent = "";
    state.selected.slice(-8).forEach(function (id) {
      var img = byId[id].querySelector(".tile img");
      var clone = document.createElement("img");
      clone.src = img.getAttribute("src"); clone.alt = ""; clone.width = 22; clone.height = 22;
      icons.appendChild(clone);
    });
  }

  function renderPm() {
    $$("[data-pm]").forEach(function (b) { b.setAttribute("aria-checked", String(b.dataset.pm === state.pm)); });
    $$("[data-pm-hint]").forEach(function (p) { p.hidden = p.dataset.pmHint !== state.pm; });
  }

  function applyFilter() {
    var q = (search.value || "").trim().toLowerCase();
    var terms = q ? q.split(/\s+/) : [];
    var only = onlySelected.checked;
    var shown = 0;
    cards.forEach(function (card) {
      var match = terms.every(function (t) { return card._text.indexOf(t) >= 0; });
      if (only && !isSelected(card.dataset.id)) match = false;
      card.hidden = !match;
      if (match) shown++;
    });
    $$(".cat", catalog).forEach(function (sec) {
      sec.hidden = !sec.querySelector(".card:not([hidden])");
    });
    $("#emptyState").hidden = shown > 0;
    $("#resultCount").textContent = (q || only) ? fmt(L.result_count, { shown: shown, total: cards.length }) : "";
  }

  function renderAll() { renderPm(); renderCards(); renderSelbar(); applyFilter(); }

  /* --- events */
  catalog.addEventListener("change", function (e) {
    if (!e.target.classList.contains("card-check")) return;
    var card = e.target.closest(".card");
    setSelected(card.dataset.id, e.target.checked);
    card.classList.toggle("selected", e.target.checked);
    if (!e.target.checked && !available(card)) e.target.disabled = true;
    save(); renderSelbar();
    if (onlySelected.checked) applyFilter();
  });

  $$("[data-pm]").forEach(function (btn) {
    btn.addEventListener("click", function () { state.pm = btn.dataset.pm; save(); renderAll(); });
    btn.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      var btns = $$("[data-pm]");
      var next = btns[(btns.indexOf(btn) + (e.key === "ArrowRight" ? 1 : btns.length - 1)) % btns.length];
      next.focus(); next.click();
    });
  });

  $$("[data-preset]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var ids = btn.dataset.apps.split(",");
      var added = 0;
      ids.forEach(function (id) { if (byId[id] && !isSelected(id)) { state.selected.push(id); added++; } });
      save(); renderCards(); renderSelbar(); applyFilter();
      toast(fmt(L.preset_added, { name: btn.textContent.trim(), n: added }));
    });
  });

  search.addEventListener("input", applyFilter);
  onlySelected.addEventListener("change", applyFilter);
  document.addEventListener("keydown", function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(tag) && !e.ctrlKey && !e.metaKey) {
      e.preventDefault(); search.focus(); search.select();
    } else if (e.key === "Escape" && document.activeElement === search && search.value) {
      search.value = ""; applyFilter();
    }
  });

  $("#clearSel").addEventListener("click", function () {
    state.selected = []; save(); renderCards(); renderSelbar(); applyFilter();
  });

  // Highlight the category currently in view.
  if ("IntersectionObserver" in window) {
    var links = {};
    $$("[data-cat-link]").forEach(function (a) { links[a.dataset.catLink] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        Object.keys(links).forEach(function (k) { links[k].classList.remove("active"); });
        var a = links[en.target.id.replace("cat-", "")];
        if (a) a.classList.add("active");
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    $$(".cat", catalog).forEach(function (s) { io.observe(s); });
  }

  /* ---------------------------------------------------------------- script generation */
  function ps(s) { return "'" + String(s).replace(/'/g, "''") + "'"; }
  function ascii(s) {
    return String(s).replace(/[–—]/g, "-").normalize("NFKD").replace(/[^\x20-\x7E]/g, "");
  }

  function selection() {
    var apps = [], skipped = [];
    state.selected.forEach(function (id) {
      var card = byId[id];
      (available(card) ? apps : skipped).push(card);
    });
    return { apps: apps, skipped: skipped };
  }

  function buildScript(pm, apps) {
    var entries = [], buckets = [];
    // Runtimes (Visual C++, .NET, DirectX, ...) first, so apps that depend on them install cleanly.
    apps = apps.filter(function (c) { return c.dataset.cat === "runtimes"; })
      .concat(apps.filter(function (c) { return c.dataset.cat !== "runtimes"; }));
    apps.forEach(function (card) {
      var name = ascii(card.dataset.name);
      var noAdmin = card.hasAttribute("data-noadmin");
      if (pm === "winget") {
        var ids = card.dataset.winget.split(",");
        ids.forEach(function (id) {
          var isStore = id.indexOf("msstore:") === 0;
          var parts = ["Name = " + ps(ids.length > 1 ? name.replace(/\s*\(.*\)$/, "") + " - " + id : name), "Id = " + ps(isStore ? id.slice(8) : id)];
          if (isStore) parts.push("Source = 'msstore'");
          if (noAdmin) parts.push("NoAdmin = $true");
          entries.push("        @{ " + parts.join("; ") + " }");
        });
      } else if (pm === "scoop") {
        var bucket = card.dataset.scoop.split("/")[0];
        if (bucket !== "main" && buckets.indexOf(bucket) < 0) buckets.push(bucket);
        entries.push("        @{ Name = " + ps(name) + "; Id = " + ps(card.dataset.scoop) + " }");
      } else {
        entries.push("        @{ Name = " + ps(name) + "; Id = " + ps(card.dataset.choco) + " }");
      }
    });
    var today = new Date().toISOString().slice(0, 10);
    return [
      "# ============================================================================",
      "#  WinMate install script - " + SITE_URL,
      "#  Generated " + today + " - " + apps.length + " app(s) with " + PM_LABEL[pm],
      "#  Run: double-click WinMate-Install.cmd, or paste this script into PowerShell.",
      "#  Only one administrator prompt is shown. Review the script before running it.",
      "#  Source code: https://github.com/baba537/WinMate",
      "# ============================================================================",
      "& {",
      "    param([string]$Phase, [string]$ResultFile, [switch]$NoPause)",
      "",
      "    $PackageManager = " + ps(pm),
      "    $Buckets = @(" + buckets.map(ps).join(", ") + ")",
      "    $Apps = @(",
      entries.join("\n"),
      "    )",
      "",
      ENGINE.replace(/\s+$/, ""),
      "}",
      ""
    ].join("\n");
  }

  function cmdWrapper(script) {
    var head = [
      "<# :",
      "@echo off",
      "setlocal",
      "title WinMate installer",
      "set \"WM_SELF=%~f0\"",
      "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"$s=[IO.File]::ReadAllText($env:WM_SELF); & ([ScriptBlock]::Create($s))\"",
      "exit /b %errorlevel%",
      "#>",
      ""
    ].join("\n");
    return (head + script).replace(/\r?\n/g, "\r\n");
  }

  function download(name, text) {
    var blob = new Blob([text], { type: "application/octet-stream" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    toast(L.downloaded);
  }

  function shareUrl() {
    var u = location.origin + location.pathname + "?pm=" + state.pm + "&apps=" + state.selected.join(",") + "#apps";
    return u;
  }

  var dialog = $("#scriptDialog");
  var current = "";

  function names(list) { return list.map(function (c) { return c.dataset.name; }).join(", "); }

  function openDialog() {
    var sel = selection();
    if (!state.selected.length) { toast(L.select_first); return; }
    var warnings = [];
    if (sel.skipped.length) warnings.push(["warn", fmt(L.warn_unavailable, { n: sel.skipped.length, pm: PM_LABEL[state.pm], names: names(sel.skipped) })]);
    if (state.pm === "winget") {
      var storeApps = sel.apps.filter(function (c) { return c.dataset.winget.indexOf("msstore:") >= 0; });
      var noAdmin = sel.apps.filter(function (c) { return c.hasAttribute("data-noadmin"); });
      if (storeApps.length) warnings.push(["info", fmt(L.warn_store, { names: names(storeApps) })]);
      if (noAdmin.length) warnings.push(["info", fmt(L.warn_noadmin, { names: names(noAdmin) })]);
    }
    if (state.pm === "scoop") {
      warnings.push(["info", L.warn_scoop_admin]);
      var np = sel.apps.filter(function (c) { return c.dataset.scoop.indexOf("nonportable/") === 0; });
      if (np.length) warnings.push(["warn", fmt(L.warn_nonportable, { names: names(np) })]);
    }
    var ul = $("#dlgWarnings");
    ul.textContent = "";
    warnings.forEach(function (w) {
      var li = document.createElement("li");
      li.className = w[0]; li.textContent = w[1];
      ul.appendChild(li);
    });
    var hasApps = sel.apps.length > 0;
    $("#dlgSummary").textContent = hasApps ? fmt(L.summary, { n: sel.apps.length, pm: PM_LABEL[state.pm] }) : fmt(L.nothing_for_pm, { pm: PM_LABEL[state.pm] });
    ["#dlCmd", "#copyPs", "#dlPs"].forEach(function (s) { $(s).disabled = !hasApps; });
    current = hasApps ? buildScript(state.pm, sel.apps) : "";
    $("#scriptPreview").textContent = current;
    if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
  }

  $("#openScript").addEventListener("click", openDialog);
  $("#dlCmd").addEventListener("click", function () { download("WinMate-Install.cmd", cmdWrapper(current)); });
  $("#dlPs").addEventListener("click", function () { download("WinMate-Install.ps1", current.replace(/\r?\n/g, "\r\n")); });
  $("#copyPs").addEventListener("click", function () { copyText(current).then(function () { toast(L.copied); }); });
  $("#copyLink").addEventListener("click", function () { copyText(shareUrl()).then(function () { toast(L.link_copied); }); });
  dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });

  renderAll();
  save();
  // Links like /?add=vlc#apps: jump to the catalog once the cards are rendered.
  if (location.hash === "#apps" && (params.has("apps") || params.has("add"))) {
    requestAnimationFrame(function () { $("#apps").scrollIntoView({ behavior: "instant" }); });
  }
})();
