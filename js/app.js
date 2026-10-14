(() => {
  "use strict";

  const app = document.getElementById("app");
  const DATA_FILES = { plants: "data/plants.csv", regions: "data/regions.csv", photos: "data/photos.csv" };
  const TYPE_LABEL = { species: "原生種", hybrid: "雜交種" };
  const SIZES = { S: "小型", M: "中型", L: "大型", XL: "巨型" };
  const POSTURES = { up: "直立", spread: "斜展", pendant: "下垂" };
  // 0–5 分的欄位（空白 = 未知）
  const SCORE_FIELDS = ["difficulty", "shield_height", "shield_vein", "shield_hair",
    "fertile_split", "fertile_width", "fertile_hair", "light", "water", "humidity"];
  const toScore = (v) => (v === "" || v == null || isNaN(Number(v)) ? null : Math.min(5, Math.max(0, Math.round(Number(v)))));

  let ITEMS = [];          // 全部品種
  let BY_ID = new Map();
  let REGIONS = {};
  const state = { q: "", type: "all", region: "all", scrollY: 0 };

  /* ---------------- 工具 ---------------- */
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const splitList = (s) => String(s || "").split("|").map((x) => x.trim()).filter(Boolean);

  // 支援引號、逗號、換行與 UTF-8 BOM 的 CSV 解析
  function parseCSV(text) {
    text = text.replace(/^﻿/, "");
    const rows = [];
    let row = [], field = "", inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else inQuotes = false;
        } else field += c;
      } else if (c === '"') inQuotes = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field); rows.push(row); row = []; field = "";
      } else field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }

    const nonEmpty = rows.filter((r) => r.some((v) => v.trim() !== ""));
    const [head = [], ...body] = nonEmpty;
    const keys = head.map((h) => h.trim());
    return body.map((r) => Object.fromEntries(keys.map((k, i) => [k, (r[i] ?? "").trim()])));
  }

  async function fetchCSV(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    return parseCSV(await res.text());
  }

  async function loadData() {
    const [plants, regions, photos] = await Promise.all([
      fetchCSV(DATA_FILES.plants), fetchCSV(DATA_FILES.regions), fetchCSV(DATA_FILES.photos)
    ]);

    REGIONS = Object.fromEntries(regions.map((r) => [r.key, { label: r.label, color: r.color || "#6b7d72" }]));

    const photosById = new Map();
    for (const p of photos) {
      if (!p.id || !p.src) continue;
      if (!photosById.has(p.id)) photosById.set(p.id, []);
      photosById.get(p.id).push({ src: p.src, caption: p.caption, credit: p.credit, license: p.license, source: p.source });
    }

    ITEMS = plants.filter((p) => p.id).map((p) => {
      const it = {
        ...p,
        type: p.type === "hybrid" ? "hybrid" : "species",
        aka: splitList(p.aka),
        parents: splitList(p.parents),
        posture: splitList(p.fertile_posture),
        size: SIZES[p.size] ? p.size : "",
        photos: photosById.get(p.id) || []
      };
      for (const k of SCORE_FIELDS) it[k] = toScore(p[k]);
      for (const k of ["min_temp", "max_temp"]) it[k] = p[k] === "" || p[k] == null || isNaN(Number(p[k])) ? null : Number(p[k]);
      return it;
    });
    BY_ID = new Map(ITEMS.map((it) => [it.id, it]));
  }

  const regionOf = (it) => REGIONS[it.region] || { label: it.region || "未分類", color: "#6b7d72" };
  const childrenOf = (id) => ITEMS.filter((it) => it.parents.includes(id));

  // 短名：去掉「鹿角蕨」；只剩一個字時保留「鹿角」避免歧義（銀鹿角蕨 → 銀鹿角）
  function shortZh(it) {
    if (!it.zh) return it.name;
    const s = it.zh.replace(/鹿角蕨$/, "");
    if (!s) return it.zh;
    return s.length === 1 ? `${s}鹿角` : s;
  }
  // 交配式：原生種用短名；親本若是雜交種，有俗名用俗名，否則加括號展開
  function crossOf(it, depth = 0) {
    return it.parents.map((pid) => {
      const p = BY_ID.get(pid);
      if (!p) return pid;
      if (p.type === "species") return shortZh(p);
      if (p.zh || depth > 4) return p.zh || p.name;
      return `(${crossOf(p, depth + 1)})`;
    }).join(" × ");
  }
  // 標題：原生種 → 短名；雜交種 → 俗名（A × B × …），沒有俗名就只顯示交配式
  function titleOf(it) {
    if (it.type === "species" || !it.parents.length) return shortZh(it);
    const cross = crossOf(it);
    return it.zh ? `${it.zh}（${cross}）` : cross;
  }
  // 副標：英文名（與標題重複時省略）
  const enOf = (it) => (it.en && it.en !== it.zh ? it.en : "");

  /* ---------------- 佔位圖（沒有照片時） ---------------- */
  const placeholderCache = new Map();
  function placeholder(it) {
    if (placeholderCache.has(it.id)) return placeholderCache.get(it.id);
    const c = regionOf(it).color;
    const label = it.name.replace(/^Platycerium\s+/, "P. ");
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
      <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="${c}"/><stop offset="1" stop-color="${c}" stop-opacity=".55"/>
      </linearGradient></defs>
      <rect width="400" height="300" fill="url(#g)"/>
      <g transform="translate(140 52) scale(3.75)" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M16 30V17M16 17l-6-6M16 17l6-6M10 11L6 4M10 11l-1-8M22 11l4-7M22 11l1-8M16 24c-5 0-9-2-11-5M16 24c5 0 9-2 11-5"/>
      </g>
      <text x="200" y="282" text-anchor="middle" fill="#fff" fill-opacity=".9" font-family="Georgia, serif" font-style="italic" font-size="18">${esc(label)}</text>
    </svg>`;
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    placeholderCache.set(it.id, url);
    return url;
  }
  const coverOf = (it) => it.photos[0]?.src || placeholder(it);

  /* ---------------- 共用元件 ---------------- */
  const icon = (name, cls = "") => `<svg class="ic ${cls}" aria-hidden="true"><use href="#i-${name}"/></svg>`;

  // 圖示評分：例如 ★★★☆☆、☀☀☀☀☆
  function iconRating(n, iconName, label, max = 5) {
    if (n == null) return `<span class="rating unknown" title="${esc(label)}：未知">—</span>`;
    return `<span class="rating r-${iconName}" title="${esc(label)} ${n}/${max}" aria-label="${esc(label)} ${n}/${max}">${
      Array.from({ length: max }, (_, i) => icon(iconName, i < n ? "on" : "")).join("")}</span>`;
  }
  const stars = (n, label = "栽培難度") => iconRating(n, "star", label);

  // 分段量表：左右兩端文字 + 5 格
  function meter(n, lo, hi, label) {
    if (n == null) return `<span class="muted">未知</span>`;
    return `<div class="meter" role="img" aria-label="${esc(label)} ${n}/5（${esc(lo)} → ${esc(hi)}）">
      <span class="m-lo">${esc(lo)}</span>
      <span class="m-bar">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</span>
      <span class="m-hi">${esc(hi)}</span>
    </div>`;
  }

  const sizeBadge = (it) => it.size
    ? `<span class="size-badge" title="尺寸：${SIZES[it.size]}">${icon("size")}${it.size}</span>` : "";

  const regionTag = (it) => {
    const r = regionOf(it);
    return `<span class="region"><span class="dot" style="background:${esc(r.color)}"></span>${esc(r.label)}</span>`;
  };

  // Google 搜尋：以小視窗開啟（被瀏覽器擋下時退回一般新分頁）
  const searchQuery = (it) => it.name.replace(/\bP\.\s/g, "Platycerium ");
  const googleURL = (it) => "https://www.google.com/search?q=" + encodeURIComponent(searchQuery(it));
  const googleLink = (it, cls = "") =>
    `<a class="gsearch ${cls}" href="${esc(googleURL(it))}" target="_blank" rel="noopener" data-gsearch
        title="在 Google 搜尋「${esc(searchQuery(it))}」" aria-label="Google 搜尋 ${esc(searchQuery(it))}">${icon("google")}</a>`;

  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-gsearch]");
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    const w = Math.min(960, screen.availWidth - 40), h = Math.min(820, screen.availHeight - 60);
    const left = Math.round((screen.availWidth - w) / 2), top = Math.round((screen.availHeight - h) / 2);
    const win = window.open(a.href, "platycerium-gsearch", `popup=yes,width=${w},height=${h},left=${left},top=${top}`);
    if (win) { e.preventDefault(); win.focus(); }
  });

  function cardHTML(it, hint = "") {
    const en = enOf(it);
    const href = `#/p/${encodeURIComponent(it.id)}`;
    return `
      <article class="card">
        <div class="thumb">
          <img src="${esc(coverOf(it))}" alt="" loading="lazy" decoding="async">
          <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>
          ${hint ? `<span class="sort-hint">${esc(hint)}</span>` : ""}
          ${it.photos.length > 1 ? `<span class="count">${it.photos.length} 張</span>` : ""}
        </div>
        <div class="card-body">
          <div class="card-title">
            <a class="card-link card-zh" href="${href}">${esc(titleOf(it))}</a>
            ${googleLink(it)}
          </div>
          <div class="card-latin">${esc(it.name)}</div>
          ${en ? `<div class="card-en">${esc(en)}</div>` : ""}
          <div class="card-meta push">${regionTag(it)}${sizeBadge(it)}</div>
          <div class="card-meta">${stars(it.difficulty)}</div>
        </div>
      </article>`;
  }

  /* ---------------- 首頁：特徵篩選 ---------------- */
  // mode "any"：同組選項任一符合（例如 小型 或 中型）；"all"：須全部符合（例如 銀白多毛 且 高聳盾葉）
  const opt = (v, label, test) => ({ v, label, test });
  const FEATURE_GROUPS = [
    { key: "size", label: "尺寸", icon: "size", mode: "any",
      options: Object.entries(SIZES).map(([k, lbl]) => opt(k, `${lbl} ${k}`, (it) => it.size === k)) },
    { key: "difficulty", label: "栽培難度", icon: "star", mode: "any", options: [
      opt("easy", "入門・容易", (it) => it.difficulty != null && it.difficulty <= 2),
      opt("mid", "中等", (it) => it.difficulty === 3),
      opt("hard", "進階・挑戰", (it) => it.difficulty >= 4)] },
    { key: "posture", label: "孢子葉姿態", icon: "hand", mode: "any",
      options: Object.entries(POSTURES).map(([k, lbl]) => opt(k, lbl, (it) => it.posture.includes(k))) },
    { key: "pups", label: "繁殖方式", icon: "pups", mode: "any", options: [
      opt("yes", "群生型（會長側芽）", (it) => it.pups === "yes"),
      opt("no", "單株型（孢子繁殖）", (it) => it.pups === "no")] },
    { key: "light", label: "光照需求", icon: "sun", mode: "any", options: [
      opt("low", "耐陰", (it) => it.light != null && it.light <= 2),
      opt("mid", "中等", (it) => it.light === 3),
      opt("high", "喜強光", (it) => it.light >= 4)] },
    { key: "look", label: "外觀特徵", icon: "shield", mode: "all", options: [
      opt("silver", "銀白多毛", (it) => it.fertile_hair >= 4),
      opt("tall", "高聳盾葉", (it) => it.shield_height >= 4),
      opt("veined", "葉脈隆起", (it) => it.shield_vein >= 4),
      opt("wide", "寬葉", (it) => it.fertile_width >= 4),
      opt("fewsplit", "少分岔", (it) => it.fertile_split != null && it.fertile_split <= 1),
      opt("manysplit", "多回分岔", (it) => it.fertile_split >= 4),
      opt("dormant", "有休眠期", (it) => it.dormancy === "yes")] }
  ];
  state.feat = Object.fromEntries(FEATURE_GROUPS.map((g) => [g.key, new Set()]));
  state.featOpen = false;

  // 環境溫度（雙頭拉桿）：品種的 最低溫 ≤ 環境低溫 且 最高溫 ≥ 環境高溫 才算適合
  const TEMP_MIN = 0, TEMP_MAX = 40;
  const ENV_PRESETS = [
    { label: "台灣平地", lo: 10, hi: 35 },
    { label: "台灣中海拔", lo: 5, hi: 30 },
    { label: "室內空調", lo: 18, hi: 30 }
  ];
  state.env = { on: false, lo: 10, hi: 35 };
  const envFits = (it) => it.min_temp != null && it.max_temp != null &&
    it.min_temp <= state.env.lo && it.max_temp >= state.env.hi;

  const activeFeatCount = () => Object.values(state.feat).reduce((n, s) => n + s.size, 0) + (state.env.on ? 1 : 0);

  function matchesFeatures(it, skipKey) {
    if (state.env.on && skipKey !== "env" && !envFits(it)) return false;
    return FEATURE_GROUPS.every((g) => {
      const sel = state.feat[g.key];
      if (g.key === skipKey || !sel.size) return true;
      const tests = g.options.filter((o) => sel.has(o.v));
      return g.mode === "all" ? tests.every((o) => o.test(it)) : tests.some((o) => o.test(it));
    });
  }

  /* ---------------- 首頁：排序 ---------------- */
  // get：取排序值（null = 未知，一律排最後）；hint：排序時顯示在卡片照片上的值
  const SIZE_RANK = { S: 1, M: 2, L: 3, XL: 4 };
  const score = (key, label) => ({ key, label, hint: (it) => `${label} ${it[key]}/5` });
  const SORTS = [
    { key: "default", label: "預設順序" },
    { key: "name", label: "名稱", get: (it) => titleOf(it), dirLabels: ["正序", "反序"] },
    { key: "size", label: "尺寸", get: (it) => SIZE_RANK[it.size] ?? null,
      hint: (it) => `${SIZES[it.size]} ${it.size}`, dirLabels: ["小 → 大", "大 → 小"] },
    { key: "difficulty", label: "栽培難度", hint: (it) => `難度 ${"★".repeat(it.difficulty)}`, dirLabels: ["易 → 難", "難 → 易"] },
    { ...score("light", "光照"), label: "光照需求" },
    { ...score("water", "澆水"), label: "澆水量" },
    { ...score("humidity", "濕度"), label: "空氣濕度" },
    { key: "min_temp", label: "耐寒性（最低溫度）", hint: (it) => `最低 ${it.min_temp}°C`, dirLabels: ["耐寒優先", "怕冷優先"] },
    { key: "max_temp", label: "耐熱性（最高溫度）", hint: (it) => `最高 ${it.max_temp}°C`, dirLabels: ["怕熱優先", "耐熱優先"], defaultDir: "desc" },
    { ...score("shield_height", "冠高"), label: "盾葉冠高" },
    { ...score("shield_vein", "脈紋"), label: "盾葉脈紋" },
    { ...score("shield_hair", "盾葉絨毛"), label: "盾葉絨毛" },
    { ...score("fertile_split", "分岔"), label: "孢子葉分岔" },
    { ...score("fertile_width", "葉寬"), label: "孢子葉寬度" },
    { ...score("fertile_hair", "絨毛"), label: "孢子葉絨毛" },
    { key: "photos", label: "照片數量", get: (it) => it.photos.length, hint: (it) => `${it.photos.length} 張照片`, defaultDir: "desc" }
  ];
  state.sort = "default";
  state.dir = "asc";
  const sortDef = () => SORTS.find((s) => s.key === state.sort) || SORTS[0];
  const sortValue = (s, it) => (s.get ? s.get(it) : it[s.key]) ?? null;
  const sortHint = (it) => {
    const s = sortDef();
    return sortValue(s, it) == null ? "未知" : s.hint(it);
  };

  function sortList(list) {
    const s = sortDef();
    if (s.key === "default") return list;
    const sign = state.dir === "asc" ? 1 : -1;
    const order = new Map(ITEMS.map((it, i) => [it.id, i]));
    return [...list].sort((a, b) => {
      const va = sortValue(s, a), vb = sortValue(s, b);
      if (va == null || vb == null) return va == null && vb == null ? order.get(a.id) - order.get(b.id) : va == null ? 1 : -1;
      const c = typeof va === "string" ? va.localeCompare(vb, "zh-Hant") : va - vb;
      return c * sign || order.get(a.id) - order.get(b.id);
    });
  }
  // 目前畫面上的清單（篩選 + 排序），詳細頁的上一個／下一個也用這個順序
  const visibleList = () => sortList(filtered());

  /* ---------------- 首頁：列表 ---------------- */
  // skipKey：計算某組選項的數量時，忽略該組本身的條件
  function filtered(skipKey) {
    const q = state.q.trim().toLowerCase();
    return ITEMS.filter((it) => {
      if (state.type !== "all" && it.type !== state.type) return false;
      if (state.region !== "all" && it.region !== state.region) return false;
      if (!matchesFeatures(it, skipKey)) return false;
      if (!q) return true;
      const hay = [it.id, it.name, titleOf(it), it.en, ...it.aka, regionOf(it).label, it.origin,
        ...it.parents.map((p) => BY_ID.get(p)?.name || p)].join(" ").toLowerCase();
      return hay.includes(q);
    });
  }

  function chip(group, value, label, dotColor) {
    const pressed = state[group] === value;
    const dot = dotColor ? `<span class="dot" style="background:${esc(dotColor)}"></span>` : "";
    return `<button class="chip" data-group="${group}" data-value="${esc(value)}" aria-pressed="${pressed}">${dot}${esc(label)}</button>`;
  }

  function renderList() {
    document.title = "鹿角蕨圖鑑";
    const nSpecies = ITEMS.filter((i) => i.type === "species").length;
    const nHybrid = ITEMS.length - nSpecies;

    app.innerHTML = `
      <div class="toolbar" id="toolbar">
        <div class="search-row">
          <label class="search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <input id="q" type="search" placeholder="搜尋學名、中文名、別名、產地…" value="${esc(state.q)}" autocomplete="off" enterkeyhint="search">
          </label>
          <button class="feat-toggle" id="feat-toggle" aria-expanded="${state.featOpen}" aria-controls="feat-panel">
            ${icon("filter")}<span class="lbl">特徵篩選</span><span class="n" id="feat-n"></span>
          </button>
        </div>
        <div class="chips" role="group" aria-label="類型">
          ${chip("type", "all", `全部 ${ITEMS.length}`)}
          ${chip("type", "species", `原生種 ${nSpecies}`)}
          ${chip("type", "hybrid", `雜交種 ${nHybrid}`)}
        </div>
        <div class="chips" role="group" aria-label="地區">
          ${chip("region", "all", "所有地區")}
          ${Object.entries(REGIONS).map(([k, r]) => chip("region", k, r.label, r.color)).join("")}
        </div>
        <div class="feat-panel" id="feat-panel" ${state.featOpen ? "" : "hidden"}>
          ${envHTML()}
          <div class="fgroups" id="fgroups"></div>
          <div class="feat-actions">
            <button class="link-btn" data-feat-clear id="feat-clear">清除特徵篩選</button>
            <button class="done-btn" data-feat-close>完成</button>
          </div>
        </div>
      </div>
      <div class="result-bar">
        <p class="result-count" id="count"></p>
        <div class="sort">
          <label for="sort">排序</label>
          <select id="sort">${SORTS.map((s) =>
            `<option value="${s.key}" ${s.key === state.sort ? "selected" : ""}>${esc(s.label)}</option>`).join("")}</select>
          <button class="dir-btn" id="sort-dir"></button>
        </div>
      </div>
      <div class="active-filters" id="active-filters"></div>
      <div class="grid" id="grid"></div>
      <footer class="footer">資料僅供參考，栽培條件會因個體與環境而異。點選卡片可查看詳細資訊、親本與雜交後代。<br>
        照片來自 <a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">Wikimedia Commons</a>，作者與授權標示於各照片下方。</footer>`;

    updateGrid();

    app.querySelector("#q").addEventListener("input", (e) => { state.q = e.target.value; updateGrid(); });
    app.querySelectorAll(".chip[data-group]").forEach((btn) => btn.addEventListener("click", () => {
      state[btn.dataset.group] = btn.dataset.value;
      app.querySelectorAll(`.chip[data-group="${btn.dataset.group}"]`).forEach((b) =>
        b.setAttribute("aria-pressed", String(b === btn)));
      updateGrid();
    }));

    app.querySelector("#feat-toggle").addEventListener("click", () => setFeatOpen(!state.featOpen));

    // 環境溫度拉桿：拖動時即時更新，並自動啟用
    const lo = app.querySelector("#env-lo"), hi = app.querySelector("#env-hi");
    const onSlide = (which) => {
      let l = Number(lo.value), h = Number(hi.value);
      if (l > h) { if (which === "lo") h = l; else l = h; }
      Object.assign(state.env, { on: true, lo: l, hi: h });
      syncEnvUI();
      updateGrid();
    };
    lo.addEventListener("input", () => onSlide("lo"));
    hi.addEventListener("input", () => onSlide("hi"));
    app.querySelector("#env-on").addEventListener("change", (e) => {
      state.env.on = e.target.checked;
      syncEnvUI();
      updateGrid();
    });
    app.querySelectorAll("[data-env-preset]").forEach((b) => b.addEventListener("click", () => {
      const p = ENV_PRESETS[Number(b.dataset.envPreset)];
      Object.assign(state.env, { on: true, lo: p.lo, hi: p.hi });
      syncEnvUI();
      updateGrid();
    }));
    syncEnvUI();
    app.querySelector("#sort").addEventListener("change", (e) => {
      state.sort = e.target.value;
      state.dir = sortDef().defaultDir || "asc";
      updateGrid();
    });
    app.querySelector("#sort-dir").addEventListener("click", () => {
      state.dir = state.dir === "asc" ? "desc" : "asc";
      updateGrid();
    });

    const toolbar = app.querySelector("#toolbar");
    const sentinel = document.createElement("div");
    toolbar.before(sentinel);
    new IntersectionObserver(([e]) => toolbar.classList.toggle("stuck", !e.isIntersecting),
      { rootMargin: `-${parseFloat(getComputedStyle(toolbar).top) + 1}px 0px 0px 0px` }).observe(sentinel);

    requestAnimationFrame(() => window.scrollTo(0, state.scrollY));
  }

  const pct = (v) => ((v - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)) * 100;

  function envHTML() {
    const ticks = [0, 10, 20, 30, 40];
    return `
      <section class="env" id="env">
        <div class="env-head">
          <label class="switch">
            <input type="checkbox" id="env-on">
            <span class="sw" aria-hidden="true"></span>
            ${icon("thermo")}<span>依我的環境溫度篩選</span>
          </label>
          <span class="env-count" id="env-count"></span>
        </div>
        <div class="env-body">
          <div class="env-vals">
            <span>冬季最低 <b id="env-lo-v"></b>°C</span>
            <span>夏季最高 <b id="env-hi-v"></b>°C</span>
          </div>
          <div class="range" id="env-range">
            <div class="track"><div class="shade l"></div><div class="shade r"></div></div>
            <input type="range" id="env-lo" min="${TEMP_MIN}" max="${TEMP_MAX}" step="1" aria-label="環境最低溫度">
            <input type="range" id="env-hi" min="${TEMP_MIN}" max="${TEMP_MAX}" step="1" aria-label="環境最高溫度">
          </div>
          <div class="range-scale">${ticks.map((t) => `<span style="left:${pct(t)}%">${t}°</span>`).join("")}</div>
          <div class="env-presets">
            ${ENV_PRESETS.map((p, i) => `<button class="chip" data-env-preset="${i}">${esc(p.label)} ${p.lo}–${p.hi}°C</button>`).join("")}
          </div>
          <p class="env-help">只顯示「撐得過你環境的最低溫，也耐得住最高溫」的品種。各品種的溫度上下限為估計值。</p>
        </div>
      </section>`;
  }

  function syncEnvUI() {
    const box = app.querySelector("#env");
    if (!box) return;
    const { on, lo, hi } = state.env;
    box.classList.toggle("off", !on);
    box.querySelector("#env-on").checked = on;
    box.querySelector("#env-lo").value = lo;
    box.querySelector("#env-hi").value = hi;
    box.querySelector("#env-lo-v").textContent = lo;
    box.querySelector("#env-hi-v").textContent = hi;
    const range = box.querySelector("#env-range");
    range.style.setProperty("--lo", pct(lo) + "%");
    range.style.setProperty("--hi", pct(hi) + "%");
    // 兩個把手重疊時，讓可往外拖的那個在上層
    box.querySelector("#env-lo").style.zIndex = lo >= TEMP_MAX - 1 ? 4 : 3;
  }

  function setFeatOpen(open) {
    state.featOpen = open;
    const panel = app.querySelector("#feat-panel");
    if (!panel) return;
    panel.hidden = !open;
    app.querySelector("#feat-toggle").setAttribute("aria-expanded", String(open));
  }

  // 特徵選項、清除、移除標籤：內容會隨篩選重繪，所以在 app 上做一次性的事件委派
  app.addEventListener("click", (e) => {
    const f = e.target.closest("[data-feat]");
    if (f) {
      const sel = state.feat[f.dataset.feat];
      sel.has(f.dataset.v) ? sel.delete(f.dataset.v) : sel.add(f.dataset.v);
      updateGrid();
    } else if (e.target.closest("[data-feat-clear]")) {
      Object.values(state.feat).forEach((s) => s.clear());
      state.env.on = false;
      syncEnvUI();
      updateGrid();
    } else if (e.target.closest("[data-env-off]")) {
      state.env.on = false;
      syncEnvUI();
      updateGrid();
    } else if (e.target.closest("[data-feat-close]")) {
      setFeatOpen(false);
    }
  });

  function renderFeatures() {
    const n = activeFeatCount();
    app.querySelector("#feat-n").textContent = n || "";

    const current = filtered();
    const envN = filtered("env").filter(envFits).length;
    app.querySelector("#env-count").textContent = state.env.on ? `符合 ${envN} 個` : `可符合 ${envN} 個`;
    app.querySelector("#feat-clear").disabled = !n;

    // 只重繪選項群組，溫度拉桿保持不動，拖曳才不會中斷
    app.querySelector("#fgroups").innerHTML = `
        ${FEATURE_GROUPS.map((g) => {
          const base = g.mode === "any" ? filtered(g.key) : current;
          return `<div class="fgroup">
            <div class="fg-h">${icon(g.icon)}${esc(g.label)}<small>${g.mode === "all" ? "須全部符合" : "可複選"}</small></div>
            <div class="fg-opts">${g.options.map((o) => {
              const on = state.feat[g.key].has(o.v);
              const count = base.filter(o.test).length;
              return `<button class="chip" data-feat="${g.key}" data-v="${o.v}" aria-pressed="${on}" ${!on && !count ? "disabled" : ""}>
                ${esc(o.label)}<span class="cnt">${count}</span></button>`;
            }).join("")}</div>
          </div>`;
        }).join("")}`;

    const envTag = state.env.on
      ? [`<button class="ftag" data-env-off aria-label="移除環境溫度篩選">
          <span class="k">環境溫度</span>${state.env.lo}–${state.env.hi}°C<span class="x" aria-hidden="true">✕</span></button>`]
      : [];
    const tags = envTag.concat(FEATURE_GROUPS.flatMap((g) => g.options.filter((o) => state.feat[g.key].has(o.v)).map((o) =>
      `<button class="ftag" data-feat="${g.key}" data-v="${o.v}" aria-label="移除 ${esc(g.label)}：${esc(o.label)}">
        <span class="k">${esc(g.label)}</span>${esc(o.label)}<span class="x" aria-hidden="true">✕</span></button>`)));
    app.querySelector("#active-filters").innerHTML = tags.length
      ? tags.join("") + `<button class="link-btn" data-feat-clear>全部清除</button>` : "";
  }

  function updateGrid() {
    renderFeatures();
    const list = visibleList();
    const s = sortDef();
    app.querySelector("#count").textContent = `共 ${list.length} 個品種`;

    const dirBtn = app.querySelector("#sort-dir");
    const [ascLbl, descLbl] = s.dirLabels || ["由低到高", "由高到低"];
    dirBtn.disabled = s.key === "default";
    dirBtn.innerHTML = `${state.dir === "asc" ? "↑" : "↓"} ${state.dir === "asc" ? ascLbl : descLbl}`;
    dirBtn.setAttribute("aria-label", `排序方向：${state.dir === "asc" ? ascLbl : descLbl}，點選切換`);

    const showHint = s.key !== "default" && s.key !== "name";
    app.querySelector("#grid").innerHTML = list.length
      ? list.map((it) => cardHTML(it, showHint ? sortHint(it) : "")).join("")
      : `<div class="empty">找不到符合的品種，試試其他關鍵字吧。</div>`;
  }

  /* ---------------- 詳細頁 ---------------- */
  function renderDetail(id) {
    const it = BY_ID.get(id);
    if (!it) {
      app.innerHTML = `<div class="empty">找不到「${esc(id)}」。<br><br><a class="back-btn" href="#/">← 回到列表</a></div>`;
      return;
    }
    document.title = `${titleOf(it)}｜鹿角蕨圖鑑`;
    const en = enOf(it);

    // 上一個 / 下一個：若在目前篩選結果中就沿用篩選順序
    const visible = visibleList();
    const list = visible.some((x) => x.id === id) ? visible : ITEMS;
    const idx = list.findIndex((x) => x.id === id);
    const prev = list[idx - 1], next = list[idx + 1];

    const hasPhotos = it.photos.length > 0;
    const thumbs = it.photos.length > 1
      ? `<div class="thumbs">${it.photos.map((p, i) =>
          `<button data-idx="${i}" aria-current="${i === 0}" aria-label="第 ${i + 1} 張"><img src="${esc(p.src)}" alt="" loading="lazy"></button>`).join("")}</div>`
      : "";

    const facts = [["原產地", it.origin], ["生長習性", it.growth]].filter(([, v]) => v);

    const parentsHTML = it.type === "hybrid" && it.parents.length ? `
      <section class="section">
        <h2>親本 <small>點選可前往</small></h2>
        <div class="parents">
          ${it.parents.map((pid) => BY_ID.has(pid) ? cardHTML(BY_ID.get(pid)) : `<div class="empty">${esc(pid)}</div>`)
            .join(`<span class="x">×</span>`)}
        </div>
      </section>` : "";

    const children = childrenOf(id);
    const childrenHTML = children.length ? `
      <section class="section">
        <h2>雜交後代 <small>${children.length} 個以此為親本</small></h2>
        <div class="rail">${children.map(cardHTML).join("")}</div>
      </section>` : "";

    const shown = new Set([id, ...it.parents, ...children.map((c) => c.id)]);
    const siblings = ITEMS.filter((x) => x.region === it.region && !shown.has(x.id));
    const siblingsHTML = siblings.length ? `
      <section class="section">
        <h2>同地區的其他品種 <small>${esc(regionOf(it).label)}</small></h2>
        <div class="rail">${siblings.map(cardHTML).join("")}</div>
      </section>` : "";

    app.innerHTML = `
      <nav class="crumbs">
        <a class="back-btn" href="#/">‹ 列表</a>
        <span>/</span><span>${TYPE_LABEL[it.type]}</span>
        <button class="back-btn graph-link" data-graph-reveal="${esc(it.id)}">${icon("graph")}在關係圖中查看</button>
      </nav>

      <article class="detail">
        <div class="gallery">
          <div class="gallery-main ${hasPhotos ? "" : "placeholder"}" id="gmain" role="${hasPhotos ? "button" : "img"}" tabindex="${hasPhotos ? 0 : -1}" aria-label="${hasPhotos ? "放大檢視照片" : "尚無照片"}">
            <img id="gimg" src="${esc(coverOf(it))}" alt="${esc(titleOf(it))}">
          </div>
          <div class="gallery-cap" id="gcap">${hasPhotos ? photoCaption(it.photos[0]) : "尚無照片，可在 data/photos.csv 新增"}</div>
          ${thumbs}
        </div>

        <div>
          <div class="title-block">
            <div class="tags">
              <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>
              ${regionTag(it)}
            </div>
            <h1>${esc(titleOf(it))}${googleLink(it, "lg")}</h1>
            <p class="latin">${esc(it.name)}</p>
            ${en ? `<p class="en">${esc(en)}</p>` : ""}
            ${it.aka.length ? `<div class="aka">別名：${it.aka.map(esc).join("、")}</div>` : ""}
          </div>
          ${it.desc ? `<p class="desc">${esc(it.desc)}</p>` : ""}
          ${it.note ? `<div class="note">${esc(it.note)}</div>` : ""}
          ${statsHTML(it)}
          ${traitsHTML(it)}
          ${facts.length ? `<dl class="facts">
            ${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join("")}
          </dl>` : ""}
        </div>
      </article>

      ${parentsHTML}
      ${childrenHTML}
      ${siblingsHTML}

      <nav class="pager">
        ${prev ? `<a class="prev" href="#/p/${encodeURIComponent(prev.id)}"><span class="dir">← 上一個</span><span class="nm">${esc(titleOf(prev))}</span></a>` : ""}
        ${next ? `<a class="next" href="#/p/${encodeURIComponent(next.id)}"><span class="dir">下一個 →</span><span class="nm">${esc(titleOf(next))}</span></a>` : ""}
      </nav>`;

    // 縮圖切換
    let current = 0;
    const setPhoto = (i) => {
      current = i;
      app.querySelector("#gimg").src = it.photos[i].src;
      app.querySelector("#gcap").innerHTML = photoCaption(it.photos[i]);
      app.querySelectorAll(".thumbs button").forEach((b, j) => b.setAttribute("aria-current", String(i === j)));
    };
    app.querySelectorAll(".thumbs button").forEach((b) =>
      b.addEventListener("click", () => setPhoto(Number(b.dataset.idx))));

    if (hasPhotos) {
      const gmain = app.querySelector("#gmain");
      const open = () => lightbox.open(it.photos, current, setPhoto);
      gmain.addEventListener("click", open);
      gmain.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    }

    detailNav = { prev, next };
    window.scrollTo(0, 0);
  }

  /* ---------- 詳細頁：快速指標 ---------- */
  const DIFF_LABEL = ["", "入門", "容易", "中等", "進階", "挑戰"];

  // 溫度範圍：數字 + 0–40°C 色條上標出可耐受區間
  function tempRange(it) {
    const { min_temp: lo, max_temp: hi } = it;
    if (lo == null && hi == null) return `<span class="muted">未知</span>`;
    const text = `<span class="big">${lo ?? "?"}–${hi ?? "?"}°C</span>`;
    if (lo == null || hi == null) return text;
    return `<div class="trange">${text}
      <span class="tbar" role="img" aria-label="可耐受 ${lo} 到 ${hi}°C">
        <i style="left:${pct(lo)}%;right:${100 - pct(hi)}%"></i>
      </span></div>`;
  }

  function statsHTML(it) {
    const tile = (iconName, label, value, sub) => `
      <div class="stat">
        <div class="stat-head">${icon(iconName)}<span>${label}</span></div>
        <div class="stat-val">${value}</div>
        ${sub ? `<div class="stat-sub">${esc(sub)}</div>` : ""}
      </div>`;

    const sizeScale = it.size
      ? `<span class="size-scale" aria-label="尺寸 ${SIZES[it.size]}">${Object.keys(SIZES).map((k) =>
          `<span class="${k === it.size ? "on" : ""}">${icon("size")}<b>${k}</b></span>`).join("")}</span>`
      : `<span class="muted">未知</span>`;

    const tiles = [
      tile("size", "尺寸", sizeScale, [SIZES[it.size], it.size_note].filter(Boolean).join("・")),
      tile("star", "栽培難度", stars(it.difficulty), DIFF_LABEL[it.difficulty || 0]),
      tile("sun", "光照需求", iconRating(it.light, "sun", "光照"), it.light_note),
      tile("drop", "澆水量", iconRating(it.water, "drop", "澆水"), it.water_note),
      tile("humid", "空氣濕度", iconRating(it.humidity, "humid", "濕度"), ""),
      tile("thermo", "適合溫度", tempRange(it), it.temp_note),
      tile("pups", "繁殖方式",
        it.pups === "yes" ? "群生型" : it.pups === "no" ? "單株型" : `<span class="muted">未知</span>`,
        it.pups === "yes" ? "會長側芽，可分株" : it.pups === "no" ? "不長側芽，以孢子繁殖" : ""),
      tile("moon", "休眠期",
        it.dormancy === "yes" ? "有" : it.dormancy === "no" ? "無明顯休眠" : `<span class="muted">未知</span>`,
        it.dormancy === "yes" ? "休眠期需減少澆水" : "")
    ];
    return `<section class="block">
      <h2 class="block-h">快速指標</h2>
      <div class="stats">${tiles.join("")}</div>
    </section>`;
  }

  /* ---------- 詳細頁：盾葉（臉）／孢子葉（手） ---------- */
  function traitsHTML(it) {
    const row = (label, html) => html ? `<div><dt>${label}</dt><dd>${html}</dd></div>` : "";
    const text = (v) => (v ? esc(v) : "");

    const posture = it.posture.length
      ? `<span class="posture">${Object.entries(POSTURES).map(([k, lbl]) =>
          `<span class="${it.posture.includes(k) ? "on" : ""}">${icon("p-" + k)}${lbl}</span>`).join("")}</span>`
      : "";

    const shield = [
      row("冠形", text(it.shield_form)),
      row("冠高", meter(it.shield_height, "貼伏", "高聳", "冠高")),
      row("顏色", text(it.shield_color)),
      row("脈紋", meter(it.shield_vein, "平滑", "隆起", "脈紋")),
      row("絨毛", meter(it.shield_hair, "光滑", "密毛", "絨毛")),
      row("概述", text(it.shield))
    ].join("");

    const fertile = [
      row("姿態", posture),
      row("長度", text(it.fertile_length)),
      row("分岔", meter(it.fertile_split, "不分岔", "多回", "分岔程度")),
      row("葉寬", meter(it.fertile_width, "細", "寬", "葉寬")),
      row("顏色", text(it.fertile_color)),
      row("絨毛", meter(it.fertile_hair, "光滑", "密毛", "絨毛")),
      row("孢子囊", text(it.spore)),
      row("概述", text(it.fertile))
    ].join("");

    return `
      <div class="traits">
        <section class="block trait">
          <h2 class="block-h">${icon("shield")}盾葉 <small>臉・營養葉</small></h2>
          <dl>${shield}</dl>
        </section>
        <section class="block trait">
          <h2 class="block-h">${icon("hand")}孢子葉 <small>手・生殖葉</small></h2>
          <dl>${fertile}</dl>
        </section>
      </div>
      <p class="hint">評分為品種間的相對比較（1–5），實際表現會因個體、品系與環境而異。</p>`;
  }

  // 照片說明：說明文字 · 作者 · 授權，作者連到原始出處
  function photoCaption(p) {
    const parts = [];
    if (p.caption) parts.push(esc(p.caption));
    const who = esc(p.credit || "來源");
    if (p.source) {
      const safe = /^https?:\/\//i.test(p.source) ? p.source : "#";
      parts.push(`📷 <a href="${esc(safe)}" target="_blank" rel="noopener">${who}</a>`);
    } else if (p.credit) parts.push(`📷 ${who}`);
    if (p.license) parts.push(esc(p.license));
    return parts.join(" · ");
  }

  /* ---------------- 燈箱 ---------------- */
  const lightbox = (() => {
    const el = document.getElementById("lightbox");
    const img = document.getElementById("lb-img");
    const cap = document.getElementById("lb-cap");
    let photos = [], i = 0, onChange = null, lastFocus = null;

    const show = () => {
      img.src = photos[i].src;
      img.alt = photos[i].caption || "";
      cap.innerHTML = `${photoCaption(photos[i])}${photos.length > 1 ? `　${i + 1} / ${photos.length}` : ""}`;
      el.querySelectorAll(".lb-nav").forEach((b) => (b.hidden = photos.length < 2));
      onChange?.(i);
    };
    const step = (d) => { if (photos.length > 1) { i = (i + d + photos.length) % photos.length; show(); } };
    const close = () => { el.hidden = true; document.body.style.overflow = ""; lastFocus?.focus(); };

    el.addEventListener("click", (e) => {
      const act = e.target.closest("[data-lb]")?.dataset.lb;
      if (act === "close" || e.target === el) close();
      else if (act === "prev") step(-1);
      else if (act === "next") step(1);
    });
    let x0 = null;
    el.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
    el.addEventListener("touchend", (e) => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
      x0 = null;
    });

    return {
      get isOpen() { return !el.hidden; },
      open(list, start, cb) {
        photos = list; i = start; onChange = cb; lastFocus = document.activeElement;
        el.hidden = false; document.body.style.overflow = "hidden";
        show();
        el.querySelector(".lb-close").focus();
      },
      close, step
    };
  })();

  /* ---------------- 版面：左關係圖 ／ 右圖鑑，可各自關閉 ---------------- */
  const graphPane = document.getElementById("graph-pane");
  const contentPane = document.getElementById("content-pane");
  const stacked = () => matchMedia("(max-width: 759px)").matches; // 手機雙開時上下排列
  // sticky 元素都接在頂欄下方，頂欄高度會隨字型、換行改變，所以用量的
  const topbar = document.querySelector(".topbar");
  new ResizeObserver(() => document.documentElement.style.setProperty("--topbar-h", topbar.offsetHeight + "px")).observe(topbar);
  const panes = (() => {
    try {
      const v = JSON.parse(localStorage.getItem("panes"));
      if (v && (v.graph || v.content)) return { graph: !!v.graph, content: !!v.content };
    } catch (e) { /* 無痕模式等 */ }
    return { graph: false, content: true };
  })();

  function setPanes(next) {
    Object.assign(panes, next);
    if (!panes.graph && !panes.content) panes.content = true; // 至少留一個
    document.body.dataset.layout = panes.graph && panes.content ? "split" : panes.graph ? "graph" : "content";
    graphPane.hidden = !panes.graph;
    contentPane.hidden = !panes.content;
    document.querySelectorAll("[data-pane-toggle]").forEach((b) =>
      b.setAttribute("aria-pressed", String(panes[b.dataset.paneToggle])));
    try { localStorage.setItem("panes", JSON.stringify(panes)); } catch (e) { /* 無痕模式等 */ }
    if (panes.graph) graph.show(); else graph.hide();
  }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-pane-toggle], [data-pane-close], [data-graph-reveal]");
    if (!t) return;
    if (t.dataset.paneToggle) {
      const k = t.dataset.paneToggle, other = k === "graph" ? "content" : "graph";
      if (panes[k] && !panes[other]) return; // 唯一開著的面板不能關
      setPanes({ [k]: !panes[k] });
    } else if (t.dataset.paneClose) {
      setPanes({ [t.dataset.paneClose]: false });
    } else {
      setPanes({ graph: true });
      graph.reveal(t.dataset.graphReveal);
      if (stacked()) window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });

  /* ---------------- 親種關係圖（D3 力導向，第一次開啟時才載入） ---------------- */
  // 節點之間用彈簧（link）與斥力（charge）拉開，親本偏上、後代偏下；
  // 模擬不完全停止，加上微小的漂移力，讓節點有輕微的懸浮感。拖曳放開後會彈回。
  const graph = (() => {
    const D3_SRC = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js";
    const FONT = getComputedStyle(document.body).fontFamily;
    const NODE_H = 34, LEVEL_GAP = 130;
    const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const box = document.getElementById("cy");
    const msg = document.getElementById("graph-msg");
    const isoBtn = graphPane.querySelector("[data-graph-iso]");
    let d3 = null, svg = null, root = null, zoom = null, sim = null, loading = null;
    let nodes = [], links = [], byId = new Map(), up = new Map(), down = new Map();
    let selected = null, hovering = null, warming = false;
    let userMoved = false; // 使用者自己縮放／拖曳過就不再自動全覽
    let showIsolated = true;
    try { showIsolated = localStorage.getItem("graph-isolated") !== "0"; } catch (e) { /* 無痕模式等 */ }

    const loadScript = (src) => new Promise((ok, fail) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = ok;
      s.onerror = () => fail(new Error(`無法載入 ${src}`));
      document.head.append(s);
    });

    const showMsg = (html) => { msg.innerHTML = html; msg.hidden = !html; };

    // 節點標籤：原生種用短名；雜交種用俗名，沒有俗名就用交配式
    const nodeLabel = (it) => (it.type === "species" ? shortZh(it) : it.zh || crossOf(it));

    const measure = (() => {
      const ctx = document.createElement("canvas").getContext("2d");
      return (text) => { ctx.font = `600 14px ${FONT}`; return ctx.measureText(text).width; };
    })();

    // 世代：原生種 0，雜交種 = 最深的親本 + 1（之後有多代雜交也能分層）
    const genCache = new Map();
    function gen(id, depth = 0) {
      if (genCache.has(id)) return genCache.get(id);
      const it = BY_ID.get(id);
      const g = !it || !it.parents.length || depth > 10 ? 0 : 1 + Math.max(...it.parents.map((p) => gen(p, depth + 1)));
      genCache.set(id, g);
      return g;
    }

    function graphData() {
      const linked = new Set();
      for (const it of ITEMS) if (it.parents.length) [it.id, ...it.parents].forEach((id) => linked.add(id));

      const list = [], edges = [], missing = new Set();
      const add = (id, label, type, color) =>
        list.push({ id, label, type, color, linked: linked.has(id), gen: gen(id),
          w: Math.ceil(measure(label)) + (type === "hybrid" ? 40 : 26) });

      for (const it of ITEMS) {
        if (!showIsolated && !linked.has(it.id) && it.id !== selected) continue;
        add(it.id, nodeLabel(it), it.type, regionOf(it).color);
      }
      for (const it of ITEMS) for (const pid of it.parents) {
        if (!BY_ID.has(pid) && !missing.has(pid)) {
          missing.add(pid);
          console.warn(`[關係圖] ${it.id} 的親本「${pid}」不存在於 plants.csv`);
          add(pid, pid, "missing", "");
        }
        edges.push({ id: `${pid}→${it.id}`, source: pid, target: it.id });
      }
      return { list, edges };
    }

    // 外形：原生種圓角矩形、雜交種六角形
    function shapePath(d) {
      const hw = d.w / 2, hh = NODE_H / 2;
      if (d.type === "hybrid") {
        const c = 12;
        return `M${-hw},0L${-hw + c},${-hh}L${hw - c},${-hh}L${hw},0L${hw - c},${hh}L${-hw + c},${hh}Z`;
      }
      const r = 9;
      return `M${-hw + r},${-hh}H${hw - r}Q${hw},${-hh} ${hw},${-hh + r}V${hh - r}Q${hw},${hh} ${hw - r},${hh}` +
        `H${-hw + r}Q${-hw},${hh} ${-hw},${hh - r}V${-hh + r}Q${-hw},${-hh} ${-hw + r},${-hh}Z`;
    }

    // 線段從節點邊緣出發、停在另一個節點邊緣（箭頭才不會被蓋住）
    function edgePoint(n, dx, dy, gap) {
      const hw = n.w / 2 + gap, hh = NODE_H / 2 + gap;
      const t = Math.min(dx ? hw / Math.abs(dx) : Infinity, dy ? hh / Math.abs(dy) : Infinity);
      return [n.x + dx * t, n.y + dy * t];
    }

    let linkSel = null, nodeSel = null;
    function draw() {
      linkSel.each(function (l) {
        const dx = l.target.x - l.source.x, dy = l.target.y - l.source.y;
        if (!dx && !dy) return;
        const [x1, y1] = edgePoint(l.source, dx, dy, 0);
        const [x2, y2] = edgePoint(l.target, -dx, -dy, 3);
        this.setAttribute("d", `M${x1},${y1}L${x2},${y2}`);
      });
      nodeSel.attr("transform", (d) => `translate(${d.x},${d.y})`);
    }

    // 漂移力：每個節點以不同相位緩慢晃動，振幅只有幾 px
    function wander() {
      if (warming || calm) return;
      const t = performance.now() / 1000;
      for (const n of nodes) {
        if (n.fx != null) continue;
        n.vx += Math.sin(t * 0.7 + n.phase) * 0.014;
        n.vy += Math.cos(t * 0.55 + n.phase * 1.7) * 0.014;
      }
    }

    function build() {
      const { list, edges } = graphData();
      const maxGen = Math.max(0, ...list.map((d) => d.gen));
      const old = new Map(nodes.map((n) => [n.id, n]));
      const fresh = !nodes.length;

      // 起始位置：每個家族（連通分量）排在自己的欄位，同家族的節點靠在一起，模擬才不會纏在一起
      const family = new Map(list.map((d) => [d.id, d.id]));
      const findF = (x) => (family.get(x) === x ? x : findF(family.get(x)));
      for (const e of edges) if (family.has(e.source) && family.has(e.target)) family.set(findF(e.source), findF(e.target));
      const famIds = [...new Set(list.filter((d) => d.linked).map((d) => findF(d.id)))];
      const famSlot = new Map(famIds.map((f, i) => [f, i - (famIds.length - 1) / 2]));
      const loners = list.filter((d) => !d.linked);
      const seen = new Map(); // 同家族同世代的第幾個
      const seed = (d) => {
        if (!d.linked) return { x: (loners.indexOf(d) - (loners.length - 1) / 2) * 90, y: (maxGen / 2 + .85) * LEVEL_GAP };
        const key = `${findF(d.id)}:${d.gen}`, k = seen.get(key) || 0;
        seen.set(key, k + 1);
        return { x: famSlot.get(findF(d.id)) * 190 + (k % 2 ? 1 : -1) * Math.ceil(k / 2) * 70,
          y: (d.gen - maxGen / 2) * LEVEL_GAP };
      };
      nodes = list.map((d, i) => Object.assign(old.get(d.id) || { ...seed(d), phase: i * 2.399 /* 黃金角，相位錯開 */ }, d));
      byId = new Map(nodes.map((n) => [n.id, n]));
      links = edges.filter((e) => byId.has(e.source) && byId.has(e.target));
      up = new Map(); down = new Map();
      for (const l of links) {
        (up.get(l.target) || up.set(l.target, []).get(l.target)).push(l.source);
        (down.get(l.source) || down.set(l.source, []).get(l.source)).push(l.target);
      }

      // 親本偏上、後代偏下；孤立原生種漂在最下方一帶
      const levelY = (d) => (d.linked ? d.gen - maxGen / 2 : maxGen / 2 + .85) * LEVEL_GAP;
      sim.nodes(nodes);
      sim.force("link").links(links);
      sim.force("y").y(levelY).strength((d) => (d.linked ? .22 : .08));
      sim.force("collide").radius((d) => d.w / 2 + 8);

      linkSel = root.select(".g-links").selectAll("path").data(links, (l) => l.id)
        .join("path").attr("class", "g-link");
      nodeSel = root.select(".g-nodes").selectAll("g.g-node").data(nodes, (d) => d.id)
        .join((enter) => {
          const g = enter.append("g");
          g.append("path").attr("class", "g-shape");
          g.append("text");
          return g;
        })
        .attr("class", (d) => `g-node ${d.type}`)
        .attr("style", (d) => (d.color ? `--c:${d.color}` : null))
        .call(dragBehavior());
      nodeSel.select(".g-shape").attr("d", shapePath);
      nodeSel.select("text").text((d) => d.label);

      if (fresh) {
        // 先在背景算到大致穩定，第一次顯示時不會亂飛
        warming = true;
        sim.alpha(1);
        for (let i = 0; i < 320; i++) sim.tick();
        warming = false;
        draw();
        fit();
      } else {
        sim.alpha(.6);
      }
      if (!calm) sim.restart();
      mark();
    }

    function dragBehavior() {
      return d3.drag()
        .clickDistance(4)
        .on("start", (e, d) => {
          if (!e.active) sim.alphaTarget(.25).restart();
          d.fx = d.x; d.fy = d.y;
          dragging = true;
          hideTip();
        })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; if (calm) { d.x = e.x; d.y = e.y; draw(); } })
        .on("end", (e, d) => {
          if (!e.active) sim.alphaTarget(calm ? 0 : .02);
          d.fx = null; d.fy = null; // 放開後由彈簧拉回
          dragging = false;
          if (calm) sim.alpha(.3).restart();
        });
    }

    // 懸浮框：滑過節點時顯示照片與基本資料，跟著滑鼠走，靠近面板邊緣時翻到另一側
    const tip = document.getElementById("graph-tip");
    let tipId = null, dragging = false;
    function showTip(id, e) {
      const it = BY_ID.get(id);
      if (!it || dragging) return hideTip();
      if (tipId !== id) {
        const en = enOf(it);
        tip.innerHTML = `
          <div class="g-tip-img ${it.photos.length ? "" : "ph"}">
            <img src="${esc(coverOf(it))}" alt="" decoding="async">
            <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>
            ${it.photos.length > 1 ? `<span class="count">${it.photos.length} 張</span>` : ""}
          </div>
          <div class="g-tip-body">
            <b>${esc(titleOf(it))}</b>
            <i>${esc(it.name)}</i>
            ${en ? `<small>${esc(en)}</small>` : ""}
            <div class="g-tip-meta">${regionTag(it)}${sizeBadge(it)}</div>
            <dl class="g-tip-facts">
              <div><dt>難度</dt><dd>${stars(it.difficulty)}</dd></div>
              <div><dt>光照</dt><dd>${iconRating(it.light, "sun", "光照")}</dd></div>
              <div><dt>澆水</dt><dd>${iconRating(it.water, "drop", "澆水")}</dd></div>
              <div><dt>溫度</dt><dd>${it.min_temp != null || it.max_temp != null
                ? `${it.min_temp ?? "?"}–${it.max_temp ?? "?"}°C` : `<span class="muted">未知</span>`}</dd></div>
            </dl>
          </div>`;
      }
      tipId = id;
      tip.classList.add("on");
      moveTip(e);
    }
    function moveTip(e) {
      const r = graphPane.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight, gap = 16;
      let x = e.clientX - r.left + gap, y = e.clientY - r.top + gap;
      if (x + tw > r.width - 8) x = e.clientX - r.left - tw - gap;
      if (y + th > r.height - 8) y = e.clientY - r.top - th - gap;
      tip.style.transform = `translate(${Math.max(8, x)}px, ${Math.max(8, y)}px)`;
    }
    function hideTip() { tipId = null; tip.classList.remove("on"); }

    function lineage(id) {
      const set = new Set([id]);
      const walk = (map, x) => (map.get(x) || []).forEach((y) => { if (!set.has(y)) { set.add(y); walk(map, y); } });
      walk(up, id);
      walk(down, id);
      return set;
    }

    // 目前的品種：外框高亮，連到祖先／後代的線上色
    function mark() {
      if (!nodeSel) return;
      const set = selected && byId.has(selected) ? lineage(selected) : null;
      nodeSel.classed("sel", (d) => d.id === selected);
      linkSel.classed("lit", (l) => !!set && set.has(l.source.id ?? l.source) && set.has(l.target.id ?? l.target));
      nodeSel.filter((d) => d.id === selected).raise();
    }

    // 滑過時只留下該品種的祖先與後代
    function focus(id) {
      hovering = id;
      const set = id ? lineage(id) : null;
      nodeSel.classed("faded", (d) => !!set && !set.has(d.id));
      linkSel.classed("faded", (l) => !!set && !(set.has(l.source.id) && set.has(l.target.id)));
    }

    const size = () => [box.clientWidth, box.clientHeight];
    const go = (t, dur) => (dur && !calm ? svg.transition().duration(dur).ease(d3.easeCubicInOut) : svg).call(zoom.transform, t);

    function fitTo(list, { dur = 0, pad = 36, maxK = 1.4 } = {}) {
      const [w, h] = size();
      if (!w || !list.length) return;
      const x1 = Math.min(...list.map((n) => n.x - n.w / 2)), x2 = Math.max(...list.map((n) => n.x + n.w / 2));
      const y1 = Math.min(...list.map((n) => n.y - NODE_H / 2)), y2 = Math.max(...list.map((n) => n.y + NODE_H / 2));
      const k = Math.max(.2, Math.min(maxK, (w - pad * 2) / (x2 - x1 || 1), (h - pad * 2) / (y2 - y1 || 1)));
      go(d3.zoomIdentity.translate(w / 2, h / 2).scale(k).translate(-(x1 + x2) / 2, -(y1 + y2) / 2), dur);
    }
    const fit = (dur = 0) => fitTo(nodes, { dur });

    // 把指定品種平移到畫面正中央（縮放維持不變，太小時放大到 0.9）
    function center(id, dur = 650) {
      const n = byId.get(id);
      const [w, h] = size();
      if (!n || !w) return;
      const k = Math.max(d3.zoomTransform(svg.node()).k, .9);
      go(d3.zoomIdentity.translate(w / 2, h / 2).scale(k).translate(-n.x, -n.y), dur);
    }

    async function init() {
      showMsg("關係圖載入中…");
      await loadScript(D3_SRC);
      d3 = window.d3;
      showMsg("");

      svg = d3.select(box).append("svg").attr("class", "g-svg");
      svg.append("defs").html(["", "-lit"].map((s) =>
        `<marker id="g-arrow${s}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="10" markerHeight="10"
          markerUnits="userSpaceOnUse" orient="auto"><path class="g-arrow${s}" d="M0,0L10,5L0,10z"/></marker>`).join(""));
      root = svg.append("g");
      root.append("g").attr("class", "g-links");
      root.append("g").attr("class", "g-nodes");

      zoom = d3.zoom().scaleExtent([.2, 3])
        .on("zoom", (e) => {
          root.attr("transform", e.transform);
          if (e.sourceEvent) { userMoved = true; hideTip(); }
        });
      svg.call(zoom).on("dblclick.zoom", null);

      sim = d3.forceSimulation()
        .force("link", d3.forceLink().id((d) => d.id).distance(85).strength(1))
        .force("charge", d3.forceManyBody().strength(-320).distanceMax(420))
        .force("x", d3.forceX(0).strength(.045))
        .force("y", d3.forceY())
        .force("collide", d3.forceCollide().strength(.9))
        .force("wander", wander)
        .alphaTarget(calm ? 0 : .02) // 不完全停下，維持輕微漂浮
        .on("tick", draw);
      if (calm) sim.stop();

      root.select(".g-nodes")
        .on("click", (e) => {
          const g = e.target.closest(".g-node");
          const id = g && d3.select(g).datum().id;
          if (!id || !BY_ID.has(id)) return;
          if (!panes.content) setPanes({ content: true });
          const hash = `#/p/${encodeURIComponent(id)}`;
          scrollToContent = true;
          if (location.hash === hash) route(); else location.hash = hash;
        })
        .on("pointerover", (e) => {
          const g = e.target.closest(".g-node");
          if (e.pointerType !== "mouse" || !g) return;
          const id = d3.select(g).datum().id;
          focus(id);
          showTip(id, e);
        })
        .on("pointermove", (e) => { if (tipId) moveTip(e); })
        .on("pointerout", (e) => {
          if (e.pointerType !== "mouse" || e.relatedTarget?.closest?.(".g-node")) return;
          focus(null);
          hideTip();
        });
      // 滑鼠第一次進到關係圖時，先在背景載入各品種的封面照，懸浮框才不會等圖
      svg.on("pointerenter.preload", () => {
        svg.on("pointerenter.preload", null);
        ITEMS.forEach((it) => { if (it.photos[0]) new Image().src = it.photos[0].src; });
      });

      new ResizeObserver(() => {
        if (!box.clientWidth) return; // 面板隱藏中
        if (selected && byId.has(selected)) center(selected, 0);
        else if (!userMoved) fit();
      }).observe(box);
      document.addEventListener("visibilitychange", () => {
        if (calm) return;
        if (document.hidden || graphPane.hidden) sim.stop(); else sim.restart();
      });

      graphPane.querySelector("#graph-legend").innerHTML = `
        <span><i class="lg-sp"></i>原生種</span><span><i class="lg-hy"></i>雜交種</span>
        ${Object.values(REGIONS).map((r) => `<span><i class="dot" style="background:${esc(r.color)}"></i>${esc(r.label)}</span>`).join("")}`;
      build();
      if (selected) center(selected, 0);
    }

    isoBtn.setAttribute("aria-pressed", String(showIsolated));
    isoBtn.addEventListener("click", () => {
      showIsolated = !showIsolated;
      isoBtn.setAttribute("aria-pressed", String(showIsolated));
      try { localStorage.setItem("graph-isolated", showIsolated ? "1" : "0"); } catch (e) { /* 無痕模式等 */ }
      if (!sim) return;
      build();
      userMoved = false;
      setTimeout(() => fit(500), 350); // 等新加入的節點稍微就位再全覽
    });
    graphPane.querySelector("[data-graph-fit]").addEventListener("click", () => { userMoved = false; fit(500); });

    return {
      // 面板打開時呼叫：第一次才載入 D3
      show() {
        if (!ITEMS.length) return;
        if (!loading) loading = init().catch((err) => {
          console.error(err);
          showMsg(`關係圖載入失敗：${esc(err.message)}<br>請確認網路連線後重新整理。`);
        });
        else if (sim && !calm) sim.restart();
      },
      hide() { sim?.stop(); },
      // 路由切換時同步目前的品種，並把它移到畫面中央
      select(id) {
        const prev = selected;
        selected = id;
        if (!sim) return;
        const isolated = (x) => x && BY_ID.has(x) && !BY_ID.get(x).parents.length && !childrenOf(x).length;
        if (!showIsolated && (isolated(prev) || isolated(id))) build(); else mark();
        if (id && !graphPane.hidden) center(id);
      },
      // 「在關係圖中查看」：縮放到該品種的整個家族
      async reveal(id) {
        selected = id;
        this.show();
        await loading;
        if (!sim) return;
        if (!byId.has(id)) build(); else mark();
        userMoved = true;
        fitTo([...lineage(id)].map((x) => byId.get(x)).filter(Boolean), { dur: 600, pad: 60, maxK: 1.3 });
      }
    };
  })();

  /* ---------------- 鍵盤 ---------------- */
  let detailNav = null;
  document.addEventListener("keydown", (e) => {
    if (lightbox.isOpen) {
      if (e.key === "Escape") lightbox.close();
      else if (e.key === "ArrowLeft") lightbox.step(-1);
      else if (e.key === "ArrowRight") lightbox.step(1);
      return;
    }
    if (!detailNav || !panes.content || e.target.matches("input, textarea")) return;
    if (e.key === "ArrowLeft" && detailNav.prev) location.hash = `#/p/${encodeURIComponent(detailNav.prev.id)}`;
    else if (e.key === "ArrowRight" && detailNav.next) location.hash = `#/p/${encodeURIComponent(detailNav.next.id)}`;
    else if (e.key === "Escape") location.hash = "#/";
  });

  /* ---------------- 路由 ---------------- */
  let onList = false;
  let scrollToContent = false; // 手機上下排列時，點關係圖節點後捲到圖鑑
  function route() {
    if (lightbox.isOpen) lightbox.close();
    const m = location.hash.match(/^#\/p\/(.+)$/);
    if (onList) state.scrollY = window.scrollY; // 離開列表時記住捲動位置
    if (m) {
      onList = false;
      const id = decodeURIComponent(m[1]);
      renderDetail(id);
      graph.select(id);
    } else {
      onList = true;
      detailNav = null;
      renderList();
      graph.select(null);
    }
    if (scrollToContent) {
      scrollToContent = false;
      if (stacked() && panes.graph) requestAnimationFrame(() =>
        window.scrollTo({ top: contentPane.offsetTop - parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-h")) }));
    }
  }

  /* ---------------- 主題：自動 → 淺色 → 深色 ---------------- */
  const THEMES = { auto: ["auto", "自動"], light: ["sun", "淺色"], dark: ["moon", "深色"] };
  const themeBtn = document.getElementById("theme-btn");
  function applyTheme(t) {
    if (t === "auto") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = t;
    const [ic, lbl] = THEMES[t];
    themeBtn.innerHTML = `${icon(ic)}<span>${lbl}</span>`;
    themeBtn.setAttribute("aria-label", `主題：${lbl}，點選切換`);
    try { t === "auto" ? localStorage.removeItem("theme") : localStorage.setItem("theme", t); } catch (e) { /* 無痕模式等 */ }
  }
  themeBtn.addEventListener("click", () => {
    const order = Object.keys(THEMES);
    const cur = document.documentElement.dataset.theme || "auto";
    applyTheme(order[(order.indexOf(cur) + 1) % order.length]);
  });
  applyTheme(document.documentElement.dataset.theme || "auto");

  /* ---------------- 啟動 ---------------- */
  setPanes({});
  loadData()
    .then(() => {
      if (panes.graph) graph.show();
      window.addEventListener("hashchange", route);
      route();
    })
    .catch((err) => {
      console.error(err);
      const isFile = location.protocol === "file:";
      app.innerHTML = `<div class="empty">
        <p>資料載入失敗：${esc(err.message)}</p>
        ${isFile ? `<p>瀏覽器不允許直接以檔案（file://）讀取 CSV。<br>請在專案資料夾執行 <code>python3 -m http.server</code>，<br>再開啟 <code>http://localhost:8000</code>。</p>` : ""}
      </div>`;
    });
})();
