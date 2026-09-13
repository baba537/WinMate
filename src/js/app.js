/* WinMate – script builder. No dependencies. */
(function () {
  "use strict";

  var ENGINE = "__ENGINE__";
  var SITE_URL = "__SITE_URL__";
  var PM_LABEL = { winget: "winget", scoop: "Scoop", choco: "Chocolatey" };
  var PMS = ["winget", "scoop", "choco"];
  var STORE_KEY = "wm-selection-v3";

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };
  function fmt(s, vars) { return s.replace(/\{(\w+)\}/g, function (_, k) { return vars[k] != null ? vars[k] : ""; }); }
  function uniq(list) { return list.filter(function (v, i) { return list.indexOf(v) === i; }); }
  function without(list, remove) { return list.filter(function (v) { return remove.indexOf(v) < 0; }); }
  function replay(el, cls) {
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

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
    replay(el, "show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); setTimeout(function () { el.hidden = true; }, 250); }, 3200);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { if (document.execCommand("copy")) resolve(); else reject(); } catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var label = btn.querySelector("span");
      var old = label ? label.textContent : "";
      copyText(btn.getAttribute("data-copy")).then(function () {
        if (label) label.textContent = document.documentElement.lang === "de" ? "Kopiert!" : "Copied!";
        btn.classList.add("done");
        setTimeout(function () { if (label) label.textContent = old; btn.classList.remove("done"); }, 1600);
      });
    });
  });

  /* ---------------------------------------------------------------- catalog setup */
  var catalog = $("#apps .catalog-main");
  if (!catalog) return;

  var L = JSON.parse($("#wm-i18n").textContent);
  var cards = $$(".card", catalog);
  var byId = {};
  cards.forEach(function (card) {
    card._check = card.querySelector(".card-check");
    card._via = card.querySelector(".via");
    card._text = (card.dataset.name + " " + card.dataset.id + " " + (card.dataset.winget || "") + " " +
      card.querySelector(".card-desc").textContent).toLowerCase();
    byId[card.dataset.id] = card;
  });

  var bundles = {};
  $$("[data-bundle]").forEach(function (tile) {
    bundles[tile.dataset.bundle] = {
      id: tile.dataset.bundle, tile: tile, name: tile.dataset.name, title: tile.dataset.title, intro: tile.dataset.intro,
      group: tile.dataset.group, url: tile.dataset.url, icon: tile.querySelector(".bt-icon").innerHTML,
      groupClass: (tile.className.match(/g-\w+/) || [""])[0],
      apps: tile.dataset.apps.split(",").filter(function (id) { return byId[id]; })
    };
  });

  /* State: apps picked by hand, active bundles, and bundle apps the user deselected. */
  var state = { pm: "winget", manual: [], bundles: [], excluded: [] };
  var undoState = null;

  function loadState() {
    var saved = null;
    try { saved = JSON.parse(store.get(STORE_KEY) || "null"); } catch (e) { saved = null; }
    if (!saved) {
      try {
        var v2 = JSON.parse(store.get("wm-selection-v2") || "null");
        if (v2) saved = { pm: v2.pm, manual: v2.selected };
      } catch (e) { saved = null; }
    }
    if (!saved) return;
    if (PM_LABEL[saved.pm]) state.pm = saved.pm;
    state.manual = (saved.manual || []).filter(function (id) { return byId[id]; });
    state.bundles = (saved.bundles || []).filter(function (id) { return bundles[id]; });
    state.excluded = (saved.excluded || []).filter(function (id) { return byId[id]; });
  }
  function save() { store.set(STORE_KEY, JSON.stringify(state)); }
  function snapshot() { return JSON.parse(JSON.stringify(state)); }

  function bundleApps(ids) {
    var out = [];
    (ids || state.bundles).forEach(function (b) { out = out.concat(bundles[b].apps); });
    return uniq(out);
  }
  function selectedIds() {
    return uniq(state.manual.concat(without(bundleApps(), state.excluded)));
  }
  function isSelected(id) {
    return state.manual.indexOf(id) >= 0 || (bundleApps().indexOf(id) >= 0 && state.excluded.indexOf(id) < 0);
  }
  function bundleOf(id) {
    for (var i = 0; i < state.bundles.length; i++) {
      if (bundles[state.bundles[i]].apps.indexOf(id) >= 0) return bundles[state.bundles[i]];
    }
    return null;
  }
  function available(card, pm) { return !!card.dataset[pm || state.pm]; }

  function setApp(id, on) {
    var inBundle = bundleApps().indexOf(id) >= 0;
    if (on) {
      if (inBundle) state.excluded = without(state.excluded, [id]);
      else if (state.manual.indexOf(id) < 0) state.manual.push(id);
    } else {
      state.manual = without(state.manual, [id]);
      if (inBundle && state.excluded.indexOf(id) < 0) state.excluded.push(id);
    }
  }

  // URL parameters: ?apps=a,b (replace), ?add=a (append), ?pm=scoop, ?bundle=gaming (opens the bundle dialog)
  loadState();
  var params = new URLSearchParams(location.search);
  if (params.has("apps")) {
    state.manual = params.get("apps").split(",").filter(function (id) { return byId[id]; });
    state.bundles = []; state.excluded = [];
  }
  if (params.has("add")) {
    params.get("add").split(",").forEach(function (id) { if (byId[id] && !isSelected(id)) setApp(id, true); });
  }
  if (params.has("pm") && PM_LABEL[params.get("pm")]) state.pm = params.get("pm");
  var openBundleOnLoad = params.has("bundle") && bundles[params.get("bundle")] ? params.get("bundle") : null;
  if (params.has("apps") || params.has("add") || params.has("pm") || params.has("bundle")) {
    history.replaceState(null, "", location.pathname + location.hash);
  }

  /* ---------------------------------------------------------------- rendering */
  var selbar = $("#selbar");
  var search = $("#search");
  var onlySelected = $("#onlySelected");
  var hudSel = $("#hudSel");
  var lastCount = -1;

  function renderCards() {
    cards.forEach(function (card) {
      var id = card.dataset.id;
      var on = isSelected(id);
      var avail = available(card);
      var via = on && state.manual.indexOf(id) < 0 ? bundleOf(id) : null;
      card._check.checked = on;
      card._check.disabled = !avail && !on;
      card.classList.toggle("selected", on);
      card.classList.toggle("via-bundle", !!via);
      card.classList.toggle("unavailable", !avail);
      card.querySelector(".na-note").hidden = avail;
      if (card._via) {
        card._via.hidden = !via;
        card._via.textContent = via ? via.name : "";
      }
    });
  }

  function renderBundles() {
    Object.keys(bundles).forEach(function (id) {
      var active = state.bundles.indexOf(id) >= 0;
      bundles[id].tile.classList.toggle("active", active);
      bundles[id].tile.setAttribute("aria-pressed", String(active));
    });
  }

  function renderSelbar() {
    var ids = selectedIds();
    var n = ids.length;
    var own = state.manual.length;
    selbar.hidden = n === 0;
    document.body.classList.toggle("has-selbar", n > 0);
    $("#selCount").textContent = n;
    $("#selLabel").textContent = n === 1 ? L.selected_one : L.selected;
    $("#selBreakdown").textContent = state.bundles.length ? "(" + fmt(L.own, { n: own }) + " · " + fmt(L.via_bundles, { n: n - own }) + ")" : "";
    var wrap = $("#selBundles");
    wrap.textContent = "";
    state.bundles.forEach(function (id) {
      var b = bundles[id];
      var chip = document.createElement("span");
      chip.className = "sel-chip " + b.groupClass;
      chip.innerHTML = b.icon;
      chip.appendChild(document.createTextNode(" " + b.name + " "));
      var x = document.createElement("button");
      x.type = "button"; x.textContent = "✕"; x.setAttribute("aria-label", fmt(L.remove_bundle, { name: b.name }));
      x.addEventListener("click", function () { removeBundle(id); });
      chip.appendChild(x);
      wrap.appendChild(chip);
    });
    if (hudSel) {
      hudSel.textContent = ("00" + n).slice(-3);
      if (lastCount >= 0 && n !== lastCount) { replay(hudSel, "bump"); replay($("#selCount"), "bump"); }
    }
    lastCount = n;
  }

  function renderPm() {
    $$("[data-pm]").forEach(function (b) { b.setAttribute("aria-checked", String(b.dataset.pm === state.pm)); });
    $$("[data-pm-hint]").forEach(function (p) { p.hidden = p.dataset.pmHint !== state.pm; });
    var hudPm = $("#hudPm");
    if (hudPm) hudPm.textContent = PM_LABEL[state.pm].toUpperCase();
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
    $$(".cat", catalog).forEach(function (sec) { sec.hidden = !sec.querySelector(".card:not([hidden])"); });
    $("#emptyState").hidden = shown > 0;
    $("#resultCount").textContent = (q || only) ? fmt(L.result_count, { shown: shown, total: cards.length }) : "";
  }

  function renderAll() { renderPm(); renderCards(); renderBundles(); renderSelbar(); applyFilter(); }
  function commit() { save(); renderCards(); renderBundles(); renderSelbar(); if (onlySelected.checked) applyFilter(); }

  /* ---------------------------------------------------------------- card + toolbar events */
  catalog.addEventListener("change", function (e) {
    if (!e.target.classList.contains("card-check")) return;
    var card = e.target.closest(".card");
    setApp(card.dataset.id, e.target.checked);
    replay(card, "pop");
    commit();
  });

  function setPm(pm) {
    state.pm = pm; save(); renderAll();
  }
  $$("[data-pm]").forEach(function (btn) {
    btn.addEventListener("click", function () { setPm(btn.dataset.pm); });
    btn.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault(); e.stopPropagation();
      var btns = $$("[data-pm]");
      var next = btns[(btns.indexOf(btn) + (e.key === "ArrowRight" ? 1 : btns.length - 1)) % btns.length];
      next.focus(); next.click();
    });
  });

  search.addEventListener("input", applyFilter);
  onlySelected.addEventListener("change", applyFilter);

  $("#clearSel").addEventListener("click", clearAll);
  function clearAll() {
    if (!selectedIds().length) return;
    undoState = snapshot();
    state.manual = []; state.bundles = []; state.excluded = [];
    commit(); applyFilter();
    toast(L.cleared);
  }
  function undo() {
    if (!undoState) return;
    state = undoState; undoState = null;
    commit(); applyFilter();
    toast(L.undone);
  }

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

  /* ---------------------------------------------------------------- dialogs */
  function openDialog(d) { if (typeof d.showModal === "function") d.showModal(); else d.setAttribute("open", ""); }
  $$("dialog").forEach(function (d) {
    d.addEventListener("click", function (e) { if (e.target === d) d.close(); });
  });

  var helpDialog = $("#helpDialog");
  $$("[data-help-open]").forEach(function (b) { b.addEventListener("click", function () { openDialog(helpDialog); }); });
  var keysPanel = $(".keys-panel");
  if (keysPanel) keysPanel.addEventListener("click", function () { openDialog(helpDialog); });

  /* ---------------------------------------------------------------- bundles */
  var bundleDialog = $("#bundleDialog");
  var currentBundle = null;

  function removeBundle(id) {
    state.bundles = without(state.bundles, [id]);
    var still = bundleApps();
    state.excluded = state.excluded.filter(function (a) { return still.indexOf(a) >= 0; });
    commit();
    toast(fmt(L.bundle_removed, { name: bundles[id].name }));
  }

  function bundleCheckedIds() {
    return $$("input", $("#bdList")).filter(function (i) { return i.checked; }).map(function (i) { return i.value; });
  }

  function updateBundleCount() {
    $("#bdCount").textContent = fmt(L.bundle_apps, { sel: bundleCheckedIds().length, total: currentBundle.apps.length });
  }

  function actionButton(label, hint, cls, handler) {
    var wrap = document.createElement("div");
    wrap.className = "bd-action";
    var btn = document.createElement("button");
    btn.type = "button"; btn.className = cls; btn.textContent = label;
    btn.addEventListener("click", handler);
    wrap.appendChild(btn);
    if (hint) {
      var small = document.createElement("span");
      small.className = "small muted"; small.textContent = hint;
      wrap.appendChild(small);
    }
    return wrap;
  }

  function applyBundle(mode) {
    var b = currentBundle;
    var ticked = bundleCheckedIds();
    var unticked = without(b.apps, ticked);
    if (mode === "remove") { bundleDialog.close(); removeBundle(b.id); return; }
    if (mode === "only") { state.manual = []; state.bundles = [b.id]; state.excluded = unticked; }
    else if (mode === "switch") { state.bundles = [b.id]; state.excluded = unticked; }
    else if (mode === "update") { state.excluded = without(state.excluded, b.apps).concat(unticked); }
    else { // add
      if (state.bundles.indexOf(b.id) < 0) state.bundles.push(b.id);
      state.excluded = without(state.excluded, ticked).concat(unticked);
    }
    state.excluded = uniq(state.excluded);
    commit(); applyFilter();
    bundleDialog.close();
    replay(b.tile, "pop");
    toast(fmt(L.bundle_added, { name: b.name }));
  }

  function openBundle(id) {
    var b = bundles[id];
    currentBundle = b;
    var active = state.bundles.indexOf(id) >= 0;
    var others = without(state.bundles, [id]);
    $("#bdIcon").innerHTML = b.icon;
    $("#bdIcon").className = "bd-icon " + b.groupClass;
    $("#bdGroup").textContent = b.group;
    $("#bd-title").textContent = b.title;
    $("#bdIntro").textContent = b.intro;
    $("#bdHint").textContent = L.bundle_hint;
    $("#bdPage").href = b.url;

    var list = $("#bdList");
    list.textContent = "";
    b.apps.forEach(function (appId) {
      var card = byId[appId];
      var own = state.manual.indexOf(appId) >= 0;
      var li = document.createElement("li");
      var label = document.createElement("label");
      var input = document.createElement("input");
      input.type = "checkbox"; input.value = appId;
      input.checked = own || !(active && state.excluded.indexOf(appId) >= 0);
      input.disabled = own;
      input.addEventListener("change", updateBundleCount);
      var tile = document.createElement("span");
      tile.className = "tile tile-xs";
      var img = document.createElement("img");
      img.src = card.querySelector(".tile img").getAttribute("src"); img.alt = ""; img.width = 20; img.height = 20;
      tile.appendChild(img);
      var text = document.createElement("span");
      text.className = "bd-text";
      var name = document.createElement("span");
      name.className = "bd-name"; name.textContent = card.dataset.name;
      text.appendChild(name);
      label.appendChild(input); label.appendChild(tile); label.appendChild(text);
      var tags = [];
      if (own) tags.push(["own", L.tag_own]);
      if (!available(card)) tags.push(["na", fmt(L.tag_na, { pm: PM_LABEL[state.pm] })]);
      var other = others.filter(function (o) { return bundles[o].apps.indexOf(appId) >= 0; })[0];
      if (other && !own) tags.push(["other", fmt(L.tag_other, { name: bundles[other].name })]);
      tags.forEach(function (t) {
        var tag = document.createElement("span");
        tag.className = "tag tag-" + t[0]; tag.textContent = t[1];
        text.appendChild(tag);
      });
      li.appendChild(label);
      list.appendChild(li);
    });
    updateBundleCount();

    var actions = $("#bdActions");
    actions.textContent = "";
    var hasOwn = state.manual.length > 0;
    if (active) {
      actions.appendChild(actionButton(L.bundle_update, "", "btn btn-primary", function () { applyBundle("update"); }));
      actions.appendChild(actionButton(L.bundle_remove, "", "btn", function () { applyBundle("remove"); }));
    } else if (others.length) {
      var oldNames = others.map(function (o) { return bundles[o].name; }).join(", ");
      actions.appendChild(actionButton(L.bundle_switch, fmt(L.bundle_switch_hint, { old: oldNames }), "btn btn-primary", function () { applyBundle("switch"); }));
      actions.appendChild(actionButton(L.bundle_add, L.bundle_add_hint, "btn", function () { applyBundle("add"); }));
      actions.appendChild(actionButton(L.bundle_only, L.bundle_only_hint, "btn-ghost", function () { applyBundle("only"); }));
    } else if (hasOwn) {
      actions.appendChild(actionButton(L.bundle_add, L.bundle_add_hint, "btn btn-primary", function () { applyBundle("add"); }));
      actions.appendChild(actionButton(L.bundle_only, L.bundle_only_hint, "btn", function () { applyBundle("only"); }));
    } else {
      actions.appendChild(actionButton(L.bundle_select, "", "btn btn-primary", function () { applyBundle("add"); }));
    }
    actions.appendChild(actionButton(L.cancel, "", "btn-ghost", function () { bundleDialog.close(); }));
    openDialog(bundleDialog);
    var primary = actions.querySelector(".btn-primary");
    if (primary) primary.focus();
  }

  Object.keys(bundles).forEach(function (id) {
    bundles[id].tile.addEventListener("click", function () { openBundle(id); });
  });

  /* ---------------------------------------------------------------- script generation */
  function ps(s) { return "'" + String(s).replace(/'/g, "''") + "'"; }
  function ascii(s) {
    return String(s).replace(/[–—]/g, "-").normalize("NFKD").replace(/[^\x20-\x7E]/g, "");
  }

  function selection() {
    var apps = [], skipped = [];
    cards.forEach(function (card) {
      if (!isSelected(card.dataset.id)) return;
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
    return location.origin + location.pathname + "?pm=" + state.pm + "&apps=" + selectedIds().join(",") + "#apps";
  }

  function currentScript() {
    var sel = selection();
    return sel.apps.length ? buildScript(state.pm, sel.apps) : "";
  }

  var scriptDialog = $("#scriptDialog");
  var current = "";

  function names(list) { return list.map(function (c) { return c.dataset.name; }).join(", "); }

  function openScript() {
    var sel = selection();
    if (!selectedIds().length) { toast(L.select_first); return; }
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
    current = currentScript();
    $("#scriptPreview").textContent = current;
    openDialog(scriptDialog);
  }

  function copyScript() {
    var text = currentScript();
    if (!text) { toast(L.select_first); return; }
    copyText(text).then(function () { toast(L.copied); });
  }
  function downloadCmd() {
    var text = currentScript();
    if (!text) { toast(L.select_first); return; }
    download("WinMate-Install.cmd", cmdWrapper(text));
  }

  $("#openScript").addEventListener("click", openScript);
  $("#dlCmd").addEventListener("click", downloadCmd);
  $("#dlPs").addEventListener("click", function () { download("WinMate-Install.ps1", current.replace(/\r?\n/g, "\r\n")); });
  $("#copyPs").addEventListener("click", copyScript);
  $("#copyLink").addEventListener("click", function () { copyText(shareUrl()).then(function () { toast(L.link_copied); }); });

  /* ---------------------------------------------------------------- keyboard */
  function visibleCards() { return cards.filter(function (c) { return !c.hidden && !c.closest(".cat[hidden]"); }); }

  function focusCard(card) {
    if (!card) return;
    if (card._check.disabled) card.querySelector(".card-more").focus(); else card._check.focus();
    card.scrollIntoView({ block: "nearest" });
  }

  function navigate(key) {
    var list = visibleCards();
    if (!list.length) return false;
    var cur = document.activeElement && document.activeElement.closest ? document.activeElement.closest(".card") : null;
    if (!cur) {
      if (key === "ArrowDown" || key === "ArrowRight") { focusCard(list[0]); return true; }
      return false;
    }
    var r = cur.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var best = null, bestScore = Infinity;
    list.forEach(function (card) {
      if (card === cur) return;
      var c = card.getBoundingClientRect(), ccx = c.left + c.width / 2, ccy = c.top + c.height / 2;
      var d = -1;
      if (key === "ArrowUp" && c.bottom <= r.top + 2) d = (r.top - c.bottom) + Math.abs(cx - ccx) * 2;
      if (key === "ArrowDown" && c.top >= r.bottom - 2) d = (c.top - r.bottom) + Math.abs(cx - ccx) * 2;
      if (key === "ArrowLeft" && c.right <= r.left + 2 && Math.abs(cy - ccy) < r.height) d = r.left - c.right;
      if (key === "ArrowRight" && c.left >= r.right - 2 && Math.abs(cy - ccy) < r.height) d = c.left - r.right;
      if (d >= 0 && d < bestScore) { bestScore = d; best = card; }
    });
    if (!best && (key === "ArrowLeft" || key === "ArrowRight")) {
      best = list[list.indexOf(cur) + (key === "ArrowRight" ? 1 : -1)] || null;
    }
    if (best) focusCard(best);
    return true;
  }

  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var el = document.activeElement;
    var tag = el && el.tagName;
    var typing = (tag === "INPUT" && el.type !== "checkbox" && el.type !== "radio") || tag === "TEXTAREA" || tag === "SELECT";
    var open = $("dialog[open]");
    var key = e.key;
    var lower = key.length === 1 ? key.toLowerCase() : key;

    if (open) {
      if (open === scriptDialog && !typing) {
        if (lower === "y") { e.preventDefault(); copyScript(); }
        else if (lower === "d") { e.preventDefault(); downloadCmd(); }
      }
      return; // Esc closes dialogs natively
    }

    if (typing) {
      if (el === search && key === "Escape") { search.value = ""; applyFilter(); search.blur(); }
      if (el === search && key === "ArrowDown") { e.preventDefault(); search.blur(); focusCard(visibleCards()[0]); }
      return;
    }

    if (key === "?") { e.preventDefault(); openDialog(helpDialog); return; }
    if (key.indexOf("Arrow") === 0) {
      if (navigate(key)) e.preventDefault();
      return;
    }
    if (key === "Enter" && el && el.classList && el.classList.contains("card-check")) {
      e.preventDefault(); el.click(); return;
    }
    switch (lower) {
      case "/": e.preventDefault(); search.focus(); search.select(); break;
      case "a": {
        var added = 0;
        visibleCards().forEach(function (c) {
          if (available(c) && !isSelected(c.dataset.id)) { setApp(c.dataset.id, true); added++; }
        });
        commit(); toast(fmt(L.all_selected, { n: added }));
        break;
      }
      case "c": clearAll(); break;
      case "u": undo(); break;
      case "b": {
        var first = $(".bundle-tile");
        if (first) { first.focus(); first.scrollIntoView({ block: "nearest" }); }
        break;
      }
      case "p": setPm(PMS[(PMS.indexOf(state.pm) + 1) % PMS.length]); toast(fmt(L.pm_now, { pm: PM_LABEL[state.pm] })); break;
      case "1": case "2": case "3": setPm(PMS[+lower - 1]); toast(fmt(L.pm_now, { pm: PM_LABEL[state.pm] })); break;
      case "s": e.preventDefault(); openScript(); break;
      case "y": copyScript(); break;
      case "d": downloadCmd(); break;
      default: return;
    }
  });

  renderAll();
  save();
  if (openBundleOnLoad) openBundle(openBundleOnLoad);
  else if (location.hash === "#apps" && (params.has("apps") || params.has("add"))) {
    requestAnimationFrame(function () { $("#apps").scrollIntoView({ behavior: "instant" }); });
  }
})();
