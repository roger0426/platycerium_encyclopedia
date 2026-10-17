(() => {
  "use strict";

  const app = document.getElementById("app");
  const DATA_FILES = { plants: "data/plants.csv", regions: "data/regions.csv", photos: "data/photos.csv", features: "data/features.csv" };
  const TYPE_LABEL = { species: "原生種", hybrid: "雜交種", cultivar: "品系" };
  // 資料可信度：親本、來源等說法的出處等級（原生種通常留空）
  const CONFIDENCE = { documented: "有文獻", vendor: "業者・玩家說法", unknown: "來源待查" };
  // 品系沒填的栽培欄位沿用 base（選拔來源）；形態欄位不沿用，因為品系本來就是外觀不同才被選出來
  const INHERIT_FIELDS = ["region", "difficulty", "pups", "dormancy", "light", "light_note",
    "water", "water_note", "humidity", "min_temp", "max_temp", "temp_note"];
  const SIZES = { S: "小型", M: "中型", L: "大型", XL: "巨型" };
  const POSTURES = { up: "直立", spread: "斜展", pendant: "下垂" };
  // 特徵調查指引的受控詞彙
  const SHIELD_FORMS = { appressed: "貼伏", "erect-wedge": "直立楔形", "erect-lobed": "直立多裂",
    "erect-multilobed": "直立多上揚裂片", "spreading-wedge": "展開楔形" };
  const SHIELD_BROWNING = { withering: "成熟後枯褐", green: "保持綠色", darkening: "轉深綠" };
  const SHIELD_FRINGE = { none: "無", "above-stipe": "只在葉柄上方", encircling: "環繞葉柄" };
  const SPORES = { tips: "末端裂片", sinus: "分岔凹處", medial: "裂片中段", "shell-lobe": "獨立殼狀裂片" };
  const FEATURE_CONF = { "高": "high", "中": "mid", "低": "low" };
  // 0–5 分的欄位（空白 = 未知）
  const SCORE_FIELDS = ["difficulty", "shield_height", "shield_hair",
    "fertile_width", "fertile_hair", "light", "water", "humidity"];
  const toScore = (v) => (v === "" || v == null || isNaN(Number(v)) ? null : Math.min(5, Math.max(0, Math.round(Number(v)))));
  // 分岔次數記範圍：「2–3」「≤5」「0」→ { lo, hi, mid }
  function parseSplit(v) {
    const s = String(v || "").trim();
    if (!s) return null;
    const m = s.match(/^(≤)?(\d+)(?:[–-](\d+))?$/);
    if (!m) return null;
    const lo = m[1] ? 0 : Number(m[2]), hi = Number(m[3] ?? m[2]);
    return { lo, hi, mid: (lo + hi) / 2, text: s };
  }

  let ITEMS = [];          // 全部品種
  let BY_ID = new Map();
  let REGIONS = {};
  let EDIT = false;        // 以 tools/serve.py 啟動時可在網頁上新增／刪除照片
  let EDIT_DATA = false;   // 同上，可在網頁上編輯 data/*.csv
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

  const photoOf = (p) => ({ src: p.src, caption: p.caption, credit: p.credit, license: p.license, source: p.source, variant: p.variant || "" });
  // variant 欄有值（例如「斑葉」）的是變異株照片，另外收，不當封面也不混在主相簿
  function setPhotos(it, rows) {
    it.photos = rows.filter((p) => p.src && !p.variant).map(photoOf);
    it.variantPhotos = rows.filter((p) => p.src && p.variant).map(photoOf);
  }

  async function loadData() {
    const [plants, regions, photos, features] = await Promise.all([
      fetchCSV(DATA_FILES.plants), fetchCSV(DATA_FILES.regions), fetchCSV(DATA_FILES.photos), fetchCSV(DATA_FILES.features)
    ]);

    // 每個特徵的摘要值、可信度與各來源標記
    const featuresById = new Map();
    for (const f of features) {
      if (!featuresById.has(f.plant_id)) featuresById.set(f.plant_id, {});
      featuresById.get(f.plant_id)[f.field] = f;
    }

    REGIONS = Object.fromEntries(regions.map((r) => [r.key, { label: r.label, color: r.color || "#6b7d72" }]));

    const photosById = new Map(), variantsById = new Map();
    for (const p of photos) {
      if (!p.id || !p.src) continue;
      const map = p.variant ? variantsById : photosById;
      if (!map.has(p.id)) map.set(p.id, []);
      map.get(p.id).push(photoOf(p));
    }

    ITEMS = plants.filter((p) => p.id).map((p) => {
      const it = {
        ...p,
        type: TYPE_LABEL[p.type] ? p.type : "species",
        aka: splitList(p.aka),
        parents: splitList(p.parents),
        base: p.base || "",
        confidence: CONFIDENCE[p.confidence] ? p.confidence : "",
        refs: splitList(p.refs),
        posture: splitList(p.fertile_posture),
        size: SIZES[p.size] ? p.size : "",
        split: parseSplit(p.fertile_split),
        features: featuresById.get(p.id) || {},
        photos: photosById.get(p.id) || [],
        variantPhotos: variantsById.get(p.id) || []
      };
      for (const k of SCORE_FIELDS) it[k] = toScore(p[k]);
      for (const k of ["min_temp", "max_temp"]) it[k] = p[k] === "" || p[k] == null || isNaN(Number(p[k])) ? null : Number(p[k]);
      return it;
    });
    BY_ID = new Map(ITEMS.map((it) => [it.id, it]));

    // 品系：空白的栽培欄位往上沿用 base（base 也可能是品系，所以遞迴）
    const done = new Set();
    const inherit = (it, depth = 0) => {
      if (done.has(it.id)) return;
      done.add(it.id);
      it.inherited = new Set();
      const base = BY_ID.get(it.base);
      if (!base || depth > 10) return;
      inherit(base, depth + 1);
      for (const k of INHERIT_FIELDS) {
        const empty = it[k] == null || it[k] === "";
        if (empty && base[k] != null && base[k] !== "") { it[k] = base[k]; it.inherited.add(k); }
      }
    };
    ITEMS.forEach((it) => inherit(it));
  }

  const regionOf = (it) => REGIONS[it.region] || { label: it.region || "未分類", color: "#6b7d72" };
  const childrenOf = (id) => ITEMS.filter((it) => it.parents.includes(id));
  const cultivarsOf = (id) => ITEMS.filter((it) => it.base === id);
  const baseOf = (it) => BY_ID.get(it.base);

  // 短名：去掉「鹿角蕨」；只剩一個字時保留「鹿角」避免歧義（銀鹿角蕨 → 銀鹿角）
  function shortZh(it) {
    if (!it.zh) return it.name;
    const s = it.zh.replace(/鹿角蕨$/, "");
    if (!s) return it.zh;
    return s.length === 1 ? `${s}鹿角` : s;
  }
  // 交配式：原生種、品系用短名；親本若是雜交種，有俗名用俗名，否則加括號展開
  function crossOf(it, depth = 0) {
    return it.parents.map((pid) => {
      const p = BY_ID.get(pid);
      if (!p) return pid;
      if (p.type !== "hybrid") return shortZh(p);
      if (p.zh || depth > 4) return p.zh || p.name;
      return `(${crossOf(p, depth + 1)})`;
    }).join(" × ");
  }
  // 標題：原生種、品系 → 短名；雜交種 → 俗名（A × B × …），沒有俗名就只顯示交配式
  function titleOf(it) {
    if (it.type !== "hybrid" || !it.parents.length) return shortZh(it);
    const cross = crossOf(it);
    return it.zh ? `${it.zh}（${cross}）` : cross;
  }
  // 副標：英文名（與標題或學名重複時省略）
  const enOf = (it) => (it.en && it.en !== it.zh && !it.name.includes(it.en) ? it.en : "");

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

  // 尺寸階梯：S M L XL 由小到大，標出目前尺寸
  const sizeScale = (it) => it.size
    ? `<span class="size-scale" aria-label="尺寸 ${SIZES[it.size]}">${Object.keys(SIZES).map((k) =>
        `<span class="${k === it.size ? "on" : ""}">${icon("size")}<b>${k}</b></span>`).join("")}</span>`
    : "";

  // 孢子葉姿態：直立／斜展／下垂三個圖示，標出符合的
  const postureIcons = (it) => it.posture.length
    ? `<span class="posture">${Object.entries(POSTURES).map(([k, lbl]) =>
        `<span class="${it.posture.includes(k) ? "on" : ""}">${icon("p-" + k)}${lbl}</span>`).join("")}</span>`
    : "";

  const confBadge = (it) => it.confidence
    ? `<span class="conf ${it.confidence}" title="資料可信度">${esc(CONFIDENCE[it.confidence])}</span>` : "";

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

  const photoEditBtn = (it, cls) =>
    `<button type="button" class="${cls}" data-photo-edit="${esc(it.id)}" title="新增／刪除照片" aria-label="管理 ${esc(titleOf(it))} 的照片">${icon("camera")}${cls === "card-edit" ? "" : "<span>管理照片</span>"}</button>`;

  function cardHTML(it, hint = "") {
    const en = enOf(it);
    const href = `#/p/${encodeURIComponent(it.id)}`;
    return `
      <article class="card" data-id="${esc(it.id)}">
        <div class="thumb">
          <img src="${esc(coverOf(it))}" alt="" loading="lazy" decoding="async">
          <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>
          ${hint ? `<span class="sort-hint">${esc(hint)}</span>` : ""}
          ${it.photos.length > 1 ? `<span class="count">${it.photos.length} 張</span>` : ""}
          ${cmpToggleBtn(it, "card-cmp")}
          ${EDIT ? photoEditBtn(it, "card-edit") : ""}
        </div>
        <div class="card-body">
          <div class="card-title">
            <a class="card-link card-zh" href="${href}">${esc(titleOf(it))}</a>
            ${googleLink(it)}
          </div>
          <div class="card-latin">${esc(it.name)}</div>
          ${en ? `<div class="card-en">${esc(en)}</div>` : ""}
          ${baseOf(it) ? `<div class="card-en">選自 ${esc(titleOf(baseOf(it)))}</div>` : ""}
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
      opt("veined", "葉脈隆起", (it) => it.shield_vein === "yes"),
      opt("wide", "寬葉", (it) => it.fertile_width >= 4),
      opt("fewsplit", "少分岔", (it) => it.split != null && it.split.mid <= 1),
      opt("manysplit", "多回分岔", (it) => it.split != null && it.split.mid >= 4),
      opt("dormant", "有休眠期", (it) => it.dormancy === "yes")] },
    { key: "confidence", label: "資料可信度", icon: "info", mode: "any",
      options: Object.entries(CONFIDENCE).map(([k, lbl]) => opt(k, lbl, (it) => it.confidence === k)) }
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
    { ...score("shield_hair", "盾葉絨毛"), label: "盾葉絨毛" },
    { key: "fertile_split", label: "孢子葉分岔", get: (it) => it.split?.mid ?? null,
      hint: (it) => `分岔 ${it.split.text} 次`, dirLabels: ["少 → 多", "多 → 少"] },
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
  // 關鍵字搜尋的比對文字（列表搜尋與比較頁的「加入品種」共用）
  function searchText(it) {
    const base = baseOf(it);
    return [it.id, it.name, titleOf(it), it.en, ...it.aka, regionOf(it).label, it.origin, it.breeder,
      ...it.parents.map((p) => BY_ID.get(p)?.name || p), base?.name, base && titleOf(base)].join(" ").toLowerCase();
  }

  function filtered(skipKey) {
    const q = state.q.trim().toLowerCase();
    return ITEMS.filter((it) => {
      if (state.type !== "all" && it.type !== state.type) return false;
      if (state.region !== "all" && it.region !== state.region) return false;
      if (!matchesFeatures(it, skipKey)) return false;
      return !q || searchText(it).includes(q);
    });
  }

  function chip(group, value, label, dotColor) {
    const pressed = state[group] === value;
    const dot = dotColor ? `<span class="dot" style="background:${esc(dotColor)}"></span>` : "";
    return `<button class="chip" data-group="${group}" data-value="${esc(value)}" aria-pressed="${pressed}">${dot}${esc(label)}</button>`;
  }

  // 卡片大小拉桿：設定網格欄寬下限（px），未設定時沿用 CSS 的響應式預設
  const CARD_MIN = 140, CARD_MAX = 360, CARD_DEFAULT = 220;

  function initCardSize() {
    const grid = app.querySelector("#grid"), input = app.querySelector("#card-size");
    const apply = (px) => {
      grid.classList.toggle("sized", px != null);
      if (px != null) grid.style.setProperty("--card-min", `${px}px`);
      else grid.style.removeProperty("--card-min");
      input.value = px ?? CARD_DEFAULT;
    };
    let saved = null;
    try { saved = parseInt(localStorage.getItem("card-size"), 10); } catch (e) { /* 無痕模式等 */ }
    apply(saved >= CARD_MIN && saved <= CARD_MAX ? saved : null);

    input.addEventListener("input", () => apply(Number(input.value)));
    input.addEventListener("change", () => {
      try { localStorage.setItem("card-size", input.value); } catch (e) { /* 無痕模式等 */ }
    });
    input.addEventListener("dblclick", () => {
      apply(null);
      try { localStorage.removeItem("card-size"); } catch (e) { /* 無痕模式等 */ }
    });
  }

  function renderList() {
    document.title = "鹿角蕨圖鑑";
    const nOf = (type) => ITEMS.filter((i) => i.type === type).length;

    app.innerHTML = `
      <div class="toolbar" id="toolbar">
        <div class="search-row">
          <label class="search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <input id="q" type="search" placeholder="搜尋學名、中文名、別名、產地…" value="${esc(state.q)}" autocomplete="off" enterkeyhint="search">
          </label>
          <div class="chips${state.type === "all" ? " collapsed" : ""}" role="group" aria-label="類型" data-chips="type">
            ${chip("type", "all", `所有類型 ${ITEMS.length}`)}
            ${Object.entries(TYPE_LABEL).map(([k, lbl]) => chip("type", k, `${lbl} ${nOf(k)}`)).join("")}
          </div>
          <div class="chips${state.region === "all" ? " collapsed" : ""}" role="group" aria-label="地區" data-chips="region">
            ${chip("region", "all", "所有地區")}
            ${Object.entries(REGIONS).map(([k, r]) => chip("region", k, r.label, r.color)).join("")}
          </div>
          <button class="feat-toggle" id="feat-toggle" aria-expanded="${state.featOpen}" aria-controls="feat-panel">
            ${icon("filter")}<span class="lbl">特徵篩選</span><span class="n" id="feat-n"></span>
          </button>
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
        <button class="back-btn cmp-all" id="cmp-all" data-cmp-all hidden>${icon("compare")}<span></span></button>
        ${EDIT_DATA ? `<button class="back-btn data-edit" data-plant-new>＋ 新增品種</button>` : ""}
        <label class="card-size" title="調整卡片大小，雙擊還原">
          ${icon("book")}
          <input id="card-size" type="range" min="${CARD_MIN}" max="${CARD_MAX}" step="10" aria-label="卡片大小">
        </label>
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
    initCardSize();

    app.querySelector("#q").addEventListener("input", (e) => { state.q = e.target.value; updateGrid(); });
    // 類型／地區選項：選「全部」時收合成單一按鈕，點它展開；選了其他選項則保持展開
    const chipGroups = app.querySelectorAll(".chips[data-chips]");
    const collapseIdle = (except) => chipGroups.forEach((g) => {
      if (g !== except && state[g.dataset.chips] === "all") g.classList.add("collapsed");
    });
    app.querySelectorAll(".chip[data-group]").forEach((btn) => btn.addEventListener("click", () => {
      const groupEl = btn.closest(".chips"), group = btn.dataset.group;
      if (groupEl.classList.contains("collapsed")) {
        collapseIdle(groupEl);
        groupEl.classList.remove("collapsed");
        return;
      }
      const changed = state[group] !== btn.dataset.value;
      state[group] = btn.dataset.value;
      app.querySelectorAll(`.chip[data-group="${group}"]`).forEach((b) =>
        b.setAttribute("aria-pressed", String(b === btn)));
      if (state[group] === "all") groupEl.classList.add("collapsed");
      if (changed) updateGrid();
    }));
    document.addEventListener("click", function onOutside(e) {
      if (!app.contains(chipGroups[0])) { document.removeEventListener("click", onOutside); return; }
      if (!e.target.closest(".chips[data-chips]")) collapseIdle();
    });

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
    // 篩選結果夠少時，一鍵把整批放進比較
    const cmpAll = app.querySelector("#cmp-all");
    cmpAll.hidden = list.length < 2 || list.length > CMP_MAX;
    cmpAll.querySelector("span").textContent = `比較這 ${list.length} 個`;

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
    const variantsHTML = it.variantPhotos.length ? `
      <div class="variant-photos">
        <h3>變異株照片 <small>斑葉等非典型個體，不代表此種的一般外觀</small></h3>
        <div class="thumbs">${it.variantPhotos.map((p, i) =>
          `<button data-vidx="${i}" aria-label="變異株照片：${esc(p.variant)}"><img src="${esc(p.src)}" alt="" loading="lazy"><span>${esc(p.variant)}</span></button>`).join("")}</div>
      </div>` : "";

    const facts = [["原產地", esc(it.origin)], ["生長習性", esc(it.growth)], ["選育者", esc(it.breeder)],
      ["資料來源", refsHTML(it.refs)]].filter(([, v]) => v);

    const parentsHTML = it.type === "hybrid" && it.parents.length ? `
      <section class="section">
        <h2>親本 <small>點選可前往</small></h2>
        <div class="parents">
          ${it.parents.map((pid) => BY_ID.has(pid) ? cardHTML(BY_ID.get(pid)) : `<div class="empty">${esc(pid)}</div>`)
            .join(`<span class="x">×</span>`)}
        </div>
      </section>` : "";

    const base = baseOf(it);
    const baseHTML = base ? `
      <section class="section">
        <h2>選拔自 <small>此品系從這個${TYPE_LABEL[base.type]}選出</small></h2>
        <div class="parents">${cardHTML(base)}</div>
      </section>` : "";

    const cultivars = cultivarsOf(id);
    const cultivarsHTML = cultivars.length ? `
      <section class="section">
        <h2>品系 <small>${cultivars.length} 個從此選出的品系・產地型</small></h2>
        <div class="rail">${cultivars.map(cardHTML).join("")}</div>
      </section>` : "";

    const children = childrenOf(id);
    const childrenHTML = children.length ? `
      <section class="section">
        <h2>雜交後代 <small>${children.length} 個以此為親本</small></h2>
        <div class="rail">${children.map(cardHTML).join("")}</div>
      </section>` : "";

    // 同地區：品系太多會淹沒列表，只列原生種與雜交種
    const shown = new Set([id, it.base, ...it.parents, ...children.map((c) => c.id)]);
    const siblings = ITEMS.filter((x) => x.region === it.region && x.type !== "cultivar" && !shown.has(x.id));
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
        ${cmpToggleBtn(it, "back-btn cmp-btn")}
        ${EDIT_DATA ? `<button class="back-btn data-edit" data-data-edit="${esc(it.id)}">${icon("edit")}編輯資料</button>
          <button class="back-btn data-edit" data-table-open="citations" data-table-q="${esc(it.id)}" title="這個品種在 citations.csv 的引用">${icon("table")}引用</button>` : ""}
      </nav>

      <article class="detail">
        <div class="detail-head">
          <div class="title-block">
            <div class="tags">
              <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>
              ${regionTag(it)}
              ${confBadge(it)}
            </div>
            <h1>${esc(titleOf(it))}${googleLink(it, "lg")}</h1>
            <p class="latin">${esc(it.name)}</p>
            ${en ? `<p class="en">${esc(en)}</p>` : ""}
            ${it.aka.length ? `<div class="aka">別名：${it.aka.map(esc).join("、")}</div>` : ""}
          </div>
          ${it.desc ? `<p class="desc">${esc(it.desc)}</p>` : ""}
          ${it.note ? `<div class="note">${esc(it.note)}</div>` : ""}
        </div>

        <div class="gallery">
          <div class="gallery-main ${hasPhotos ? "" : "placeholder"}" id="gmain" role="${hasPhotos ? "button" : "img"}" tabindex="${hasPhotos ? 0 : -1}" aria-label="${hasPhotos ? "放大檢視照片" : "尚無照片"}">
            <img id="gimg" src="${esc(coverOf(it))}" alt="${esc(titleOf(it))}">
          </div>
          <div class="gallery-cap" id="gcap">${hasPhotos ? photoCaption(it.photos[0]) : EDIT ? "尚無照片" : "尚無照片，可在 data/photos.csv 新增"}</div>
          ${thumbs}
          ${variantsHTML}
          ${EDIT ? photoEditBtn(it, "back-btn gallery-edit") : ""}
        </div>

        <div class="detail-body">
          ${statsHTML(it)}
          ${traitsHTML(it)}
          ${facts.length ? `<dl class="facts">
            ${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}
          </dl>` : ""}
          ${sourcesHTML(it)}
        </div>
      </article>

      ${baseHTML}
      ${parentsHTML}
      ${cultivarsHTML}
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
      app.querySelectorAll(".thumbs button[data-idx]").forEach((b, j) => b.setAttribute("aria-current", String(i === j)));
    };
    app.querySelectorAll(".thumbs button[data-idx]").forEach((b) =>
      b.addEventListener("click", () => setPhoto(Number(b.dataset.idx))));
    // 變異株照片只在燈箱裡瀏覽，不切換主圖
    app.querySelectorAll(".thumbs button[data-vidx]").forEach((b) =>
      b.addEventListener("click", () => lightbox.open(it.variantPhotos, Number(b.dataset.vidx), null)));

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
      <span class="tbar" role="img" aria-label="建議 ${lo} 到 ${hi}°C">
        <i style="left:${pct(lo)}%;right:${100 - pct(hi)}%"></i>
      </span></div>`;
  }

  // 特徵調查指引 v1.3 的來源等級
  const TIERS = { T1: "學術文獻", T2: "機構與專家", T3: "業者與玩家" };
  const tierText = (tiers) => (tiers || "").split("|").filter(Boolean).map((t) => `${t} ${TIERS[t] || ""}`.trim()).join("、");

  // 一個欄位的提示文字：「可信度 低（依據 T3 業者與玩家）」＋各來源標記（每個來源附 Tx）
  function featureNote(it, field) {
    const f = it.features[field];
    if (!f) return "";
    const head = f.summary && f.confidence
      ? `可信度 ${f.confidence}${f.tiers ? `（依據 ${tierText(f.tiers)}）` : ""}` : "";
    return [head, f.by_source].filter(Boolean).join("\n");
  }

  function statsHTML(it) {
    // 注記平時隱藏，hover／focus（觸控點按）時以浮動提示顯示
    const tile = (iconName, label, value, sub) => `
      <div class="stat${sub ? " has-note" : ""}"${sub ? ` tabindex="0"` : ""}>
        <div class="stat-head">${icon(iconName)}<span>${label}</span></div>
        <div class="stat-val">${value}</div>
        ${sub ? `<div class="stat-sub" role="tooltip">${esc(sub)}</div>` : ""}
      </div>`;


    // 浮動提示：摘要可信度、依據的來源等級（Tx）與各來源標記
    const note = (...parts) => parts.filter(Boolean).join("\n");
    const tempNote = [["最低溫", "min_temp"], ["最高溫", "max_temp"]]
      .map(([n, k]) => featureNote(it, k) && `${n}｜${featureNote(it, k)}`).filter(Boolean).join("\n\n");

    const tiles = [
      tile("size", "尺寸", sizeScale(it) || `<span class="muted">未知</span>`, note(SIZES[it.size], featureNote(it, "size") || it.size_note)),
      tile("star", "栽培難度", stars(it.difficulty), note(DIFF_LABEL[it.difficulty || 0], featureNote(it, "difficulty"))),
      tile("sun", "光照需求", iconRating(it.light, "sun", "光照"), featureNote(it, "light") || it.light_note),
      tile("drop", "澆水量", iconRating(it.water, "drop", "澆水"), featureNote(it, "water") || it.water_note),
      tile("humid", "空氣濕度", iconRating(it.humidity, "humid", "濕度"), featureNote(it, "humidity")),
      tile("thermo", "建議溫度", tempRange(it), tempNote || it.temp_note),
      tile("pups", "繁殖方式",
        it.pups === "yes" ? "群生型" : it.pups === "no" ? "單株型" : `<span class="muted">未知</span>`,
        note(it.pups === "yes" ? "會長側芽，可分株" : it.pups === "no" ? "不長側芽，以孢子繁殖" : "", featureNote(it, "pups"))),
      tile("moon", "休眠期",
        it.dormancy === "yes" ? "有" : it.dormancy === "no" ? "無明顯休眠" : `<span class="muted">未知</span>`,
        note(it.dormancy === "yes" ? "休眠期需減少澆水" : "", featureNote(it, "dormancy")))
    ];
    const base = baseOf(it);
    const inherited = base && [...it.inherited].some((k) => k !== "region")
      ? `<p class="hint">栽培條件尚未個別調查，暫時沿用「${esc(titleOf(base))}」的資料。</p>` : "";
    return `<section class="block">
      <h2 class="block-h">快速指標</h2>
      <div class="stats">${tiles.join("")}</div>
      ${inherited}
    </section>`;
  }

  /* ---------- 詳細頁：盾葉（臉）／孢子葉（手） ---------- */
  function traitsHTML(it) {
    const row = (label, html) => html ? `<div><dt>${label}</dt><dd>${html}</dd></div>` : "";
    const text = (v) => (v ? esc(v) : "");

    const posture = postureIcons(it);

    const vocab = (map, v) => text(map[v] || v);
    const vein = { yes: "隆起", no: "埋入" }[it.shield_vein] || "";
    const split = it.split ? (it.split.text === "0" ? "不分岔" : `${esc(it.split.text)} 次`) : "";

    const shield = [
      row("冠形", vocab(SHIELD_FORMS, it.shield_form)),
      row("冠高", meter(it.shield_height, "貼伏", "高聳", "冠高")),
      row("老化", vocab(SHIELD_BROWNING, it.shield_browning)),
      row("領片", vocab(SHIELD_FRINGE, it.shield_fringe)),
      row("脈紋", vein),
      row("絨毛", meter(it.shield_hair, "光滑", "密毛", "絨毛")),
      row("概述", text(it.shield))
    ].join("");

    const fertile = [
      row("姿態", posture),
      row("長度", text(it.fertile_length)),
      row("分岔", split),
      row("葉寬", meter(it.fertile_width, "細", "寬", "葉寬")),
      row("絨毛", meter(it.fertile_hair, "光滑", "密毛", "絨毛")),
      row("孢子囊", vocab(SPORES, it.spore)),
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

  /* ---------- 詳細頁：特徵來源與可信度 ---------- */
  const FEATURE_LABELS = [
    ["size", "尺寸"], ["shield_form", "盾葉冠形"], ["shield_height", "盾葉冠高"], ["shield_browning", "盾葉老化"],
    ["shield_fringe", "盾葉領片"], ["shield_vein", "盾葉脈紋"], ["shield_hair", "盾葉絨毛"],
    ["fertile_posture", "孢子葉姿態"], ["fertile_length", "孢子葉長度"], ["fertile_split", "孢子葉分岔"],
    ["fertile_width", "孢子葉寬度"], ["fertile_hair", "孢子葉絨毛"], ["spore", "孢子囊位置"],
    ["pups", "側芽"], ["dormancy", "休眠期"], ["origin", "原產地"],
    ["light", "光照"], ["water", "澆水"], ["humidity", "濕度"], ["min_temp", "建議最低溫"], ["max_temp", "建議最高溫"],
    ["difficulty", "栽培難度"]
  ];
  const VALUE_LABELS = {
    shield_form: SHIELD_FORMS, shield_browning: SHIELD_BROWNING, shield_fringe: SHIELD_FRINGE, spore: SPORES,
    shield_vein: { yes: "隆起", no: "埋入" }, pups: { yes: "叢生", no: "單生" }, dormancy: { yes: "有", no: "無" },
    fertile_posture: { up: "直立", spread: "展開", pendant: "下垂", "spread|pendant": "展開、側裂片下垂" }
  };

  function featureValue(field, v) {
    if (!v) return `<span class="muted">未知</span>`;
    if (VALUE_LABELS[field]) return esc(VALUE_LABELS[field][v] || v);
    if (field === "min_temp" || field === "max_temp") return `${esc(v)}°C`;
    if (field === "size") return `${esc(SIZES[v] || "")} ${esc(v)}`;
    if (SCORE_FIELDS.includes(field)) return `${esc(v)}/5`;
    return esc(v);
  }

  function sourcesHTML(it) {
    const rows = FEATURE_LABELS.filter(([k]) => it.features[k]).map(([k, label]) => {
      const f = it.features[k];
      const conf = f.summary && FEATURE_CONF[f.confidence]
        ? `<span class="fconf ${FEATURE_CONF[f.confidence]}"${f.tiers ? ` title="依據 ${esc(tierText(f.tiers))}"` : ""}>可信度 ${esc(f.confidence)}${
            f.tiers ? ` · ${esc(f.tiers.split("|").join("/"))}` : ""}</span>` : "";
      return `<div><dt>${label}</dt><dd>
        <div class="fsum">${featureValue(k, f.summary)}${conf}</div>
        ${f.by_source ? `<div class="fsrc">${esc(f.by_source)}</div>` : ""}
      </dd></div>`;
    });
    if (!rows.length) return "";
    const version = it.survey_version ? `依特徵調查指引 ${esc(it.survey_version)} 整理。` : "";
    return `<section class="block">
      <details class="feature-src">
        <summary>特徵來源與可信度</summary>
        <dl class="facts">${rows.join("")}</dl>
        <p class="hint">${version}摘要值依各來源換算後平均；標「參考」的來源（原生地棲地、耐受紀錄、其他地區的難度評等）只顯示，不計入摘要。來源等級：T1 學術文獻、T2 機構與專家、T3 業者與玩家；型態欄位只有 T3 來源時，可信度一律為低。</p>
      </details>
    </section>`;
  }

  // 資料來源：顯示網域名稱，連到原始網址
  function refsHTML(refs) {
    const links = refs.filter((u) => /^https?:\/\//i.test(u)).map((u) => {
      let host = u;
      try { host = new URL(u).hostname.replace(/^www\./, ""); } catch (e) { /* 網址格式錯誤就顯示原文 */ }
      return `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(host)}</a>`;
    });
    return links.length ? `<span class="refs">${links.join("")}</span>` : "";
  }

  // 照片說明：說明文字 · 作者 · 授權，作者連到原始出處
  function photoCaption(p) {
    const parts = [];
    if (p.variant) parts.push(`<strong>變異株・${esc(p.variant)}</strong>`);
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

  /* ---------------- 本機伺服器 API（tools/serve.py） ---------------- */
  // 有 body 用 POST（JSON），沒有就 GET
  async function api(path, body) {
    const res = await fetch(path, body === undefined ? { cache: "no-store" }
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(j.error || `HTTP ${res.status}`);
    return j;
  }

  /* ---------------- 照片管理（tools/serve.py） ---------------- */
  // 照片在瀏覽器裡先縮到長邊 1600px、轉 JPEG，再交給本機伺服器存到 images/<id>/ 並寫入 photos.csv
  const photoEditor = (() => {
    const dlg = document.getElementById("photo-dlg");
    const $ = (s) => dlg.querySelector(s);
    const list = $("#pd-list"), pendingEl = $("#pd-pending"), msg = $("#pd-msg"), uploadBtn = $("#pd-upload");
    const field = (k) => $(`#pd-${k}`);
    let it = null, pending = [], changed = false, busy = false;
    const say = (text, err = false) => { msg.textContent = text; msg.classList.toggle("err", err); };
    const blobToDataURL = (b) => new Promise((ok, fail) => {
      const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = fail; r.readAsDataURL(b);
    });
    async function toJPEG(blob) {
      const bmp = await createImageBitmap(blob);
      const k = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
      const c = document.createElement("canvas");
      c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height); // 透明 PNG 轉 JPEG 時底色用白色
      ctx.drawImage(bmp, 0, 0, c.width, c.height);
      return blobToDataURL(await new Promise((ok) => c.toBlob(ok, "image/jpeg", 0.88)));
    }

    function renderList() {
      const all = [...it.photos, ...it.variantPhotos];
      list.innerHTML = all.length ? all.map((p, i) => `
        <figure class="pd-item">
          <img src="${esc(p.src)}" alt="" loading="lazy">
          ${i === 0 && !p.variant ? `<span class="pd-cover">封面</span>` : ""}
          ${p.variant ? `<span class="pd-cover">變異株・${esc(p.variant)}</span>` : ""}
          <figcaption>${esc(p.caption || p.src.split("/").pop())}${p.credit ? `<br><small>📷 ${esc(p.credit)}</small>` : ""}</figcaption>
          <div class="pd-btns">
            ${i > 0 && !p.variant ? `<button type="button" data-pd-cover="${esc(p.src)}">設為封面</button>` : ""}
            <button type="button" class="danger" data-pd-del="${esc(p.src)}">刪除</button>
          </div>
        </figure>`).join("") : `<p class="muted">還沒有照片</p>`;
    }
    function renderPending() {
      pendingEl.innerHTML = pending.map((p, i) => `
        <figure class="pd-item"><img src="${p.url}" alt="">
          <div class="pd-btns"><button type="button" data-pd-drop="${i}">移除</button></div></figure>`).join("");
      uploadBtn.disabled = busy || !pending.length;
      uploadBtn.textContent = pending.length ? `上傳 ${pending.length} 張` : "上傳";
    }
    function addBlobs(blobs) {
      const imgs = blobs.filter((b) => b.type.startsWith("image/"));
      if (!imgs.length) return say("沒有找到圖片", true);
      pending.push(...imgs.map((blob) => ({ blob, url: URL.createObjectURL(blob) })));
      renderPending();
      say(`已加入 ${imgs.length} 張，填好下方資料後按「上傳」`);
    }
    async function addURL(url) {
      url = url.trim();
      if (!/^https?:\/\//i.test(url)) return say("請貼上 http(s) 開頭的圖片網址", true);
      say("下載中…");
      try {
        const j = await api("api/fetch", { url });
        addBlobs([await (await fetch(`data:${j.type};base64,${j.data}`)).blob()]);
        $("#pd-url-input").value = "";
      } catch (e) { say(e.message, true); }
    }
    const done = (j) => { setPhotos(it, j.photos); changed = true; renderList(); };

    async function upload() {
      if (busy || !pending.length) return;
      busy = true; renderPending();
      const meta = Object.fromEntries(["caption", "credit", "source", "license", "variant"].map((k) => [k, field(k).value.trim()]));
      try {
        while (pending.length) {
          say(`上傳中…（剩 ${pending.length} 張）`);
          done(await api("api/photos/add", { id: it.id, data: await toJPEG(pending[0].blob), ...meta }));
          URL.revokeObjectURL(pending.shift().url);
          renderPending();
        }
        say("已上傳，並寫入 data/photos.csv");
      } catch (e) { say(`上傳失敗：${e.message}`, true); }
      busy = false; renderPending();
    }

    dlg.addEventListener("click", async (e) => {
      const b = e.target.closest("button");
      // 點對話框外的背景也關閉
      const r = dlg.getBoundingClientRect();
      if (e.target === dlg && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) return dlg.close();
      if (!b) return;
      try {
        if (b.dataset.pd === "close") dlg.close();
        else if (b.id === "pd-upload") upload();
        else if (b.dataset.pdDrop) { URL.revokeObjectURL(pending.splice(Number(b.dataset.pdDrop), 1)[0].url); renderPending(); }
        else if (b.dataset.pdCover) done(await api("api/photos/cover", { src: b.dataset.pdCover }));
        else if (b.dataset.pdDel && confirm("確定刪除這張照片？照片檔也會一併刪除。")) {
          done(await api("api/photos/delete", { src: b.dataset.pdDel }));
          say("已刪除");
        }
      } catch (err) { say(err.message, true); }
    });
    $("#pd-file").addEventListener("change", (e) => { addBlobs([...e.target.files]); e.target.value = ""; });
    $("#pd-url").addEventListener("submit", (e) => { e.preventDefault(); addURL($("#pd-url-input").value); });

    // 拖曳：檔案直接收；從其他分頁拖來的圖片只有網址，優先取 <img src>，交給伺服器下載
    const drop = $("#pd-drop");
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault(); drop.classList.remove("over");
      const dt = e.dataTransfer;
      if (dt.files.length) return addBlobs([...dt.files]);
      const img = dt.getData("text/html").match(/<img[^>]+src="([^"]+)"/i)?.[1];
      const url = (img || dt.getData("text/uri-list") || dt.getData("text/plain")).split("\n")[0].replace(/&amp;/g, "&");
      if (url) addURL(url);
    });
    // 貼上：圖片一律收；文字只在沒有聚焦輸入框時當作圖片網址
    document.addEventListener("paste", (e) => {
      if (!dlg.open) return;
      const files = [...e.clipboardData.files];
      if (files.length) { e.preventDefault(); return addBlobs(files); }
      const text = e.clipboardData.getData("text/plain");
      if (!e.target.matches("input, textarea") && /^https?:\/\//i.test(text.trim())) { e.preventDefault(); addURL(text); }
    });

    // 關閉時才重畫底下的頁面，並保留捲動位置
    dlg.addEventListener("close", () => {
      pending.forEach((p) => URL.revokeObjectURL(p.url));
      pending = [];
      if (!changed) return;
      const y = window.scrollY;
      route();
      window.scrollTo(0, y);
    });

    return {
      get isOpen() { return dlg.open; },
      open(id) {
        it = BY_ID.get(id);
        if (!it) return;
        changed = false;
        $("#pd-title").textContent = `照片管理・${titleOf(it)}`;
        // 作者、授權常常整批相同，保留上次填的
        for (const k of ["caption", "source", "variant"]) field(k).value = "";
        say("");
        renderList(); renderPending();
        dlg.showModal();
        drop.focus();
      }
    };
  })();

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-photo-edit]");
    if (!b) return;
    e.preventDefault();
    photoEditor.open(b.dataset.photoEdit);
  });

  /* ---------------- 資料編輯（tools/serve.py） ---------------- */
  // 直接改 data/*.csv 的一列；存檔後重新讀取資料、重畫畫面。features.csv 由調查腳本產生，不在這裡改
  // 表單欄位：[欄位, 標籤, 設定]；kind：area 多行、score 1–5、number、multi 複選（| 分隔）、color；opts 為下拉選項
  const USES = { summary: "計入摘要", reference: "只供參考", excluded: "排除" };
  const FORMS = {
    plants: [
      ["基本資料", [
        ["id", "代號", { hint: "英文小寫、數字與 -，也是網址；建立後不能改" }],
        ["type", "類型", { opts: TYPE_LABEL }],
        ["name", "學名", { hint: "雜交種寫交配式或栽培品種名，品系寫 P. willinckii 'Nano'" }],
        ["zh", "中文名／俗名"], ["en", "英文名"],
        ["aka", "別名", { hint: "多個用 | 分隔" }],
        ["region", "地區", { opts: () => Object.fromEntries(Object.entries(REGIONS).map(([k, r]) => [k, r.label])) }],
        ["origin", "原產地"],
        ["parents", "親本", { hint: "雜交種的親本 id，用 | 分隔", list: "dd-plant-ids" }],
        ["base", "選拔來源", { hint: "品系的來源 id（一個）", list: "dd-plant-ids" }],
        ["breeder", "選育者"],
        ["confidence", "資料可信度", { opts: CONFIDENCE }],
        ["refs", "參考網址", { kind: "area", hint: "多個用 | 分隔" }],
        ["desc", "簡介", { kind: "area" }],
        ["note", "補充說明", { kind: "area" }],
        ["survey_version", "調查指引版本", { hint: "空白 = 尚未依指引調查" }]]],
      ["尺寸與難度", [
        ["size", "尺寸", { opts: Object.fromEntries(Object.entries(SIZES).map(([k, v]) => [k, `${k} ${v}`])) }],
        ["size_note", "尺寸依據"],
        ["difficulty", "栽培難度", { kind: "score", hint: "1 入門 → 5 挑戰" }]]],
      ["盾葉（臉）", [
        ["shield", "概述", { kind: "area" }],
        ["shield_form", "冠形", { opts: SHIELD_FORMS }],
        ["shield_height", "冠高", { kind: "score", hint: "1 貼伏 → 5 高聳" }],
        ["shield_browning", "老化", { opts: SHIELD_BROWNING }],
        ["shield_fringe", "領片", { opts: SHIELD_FRINGE }],
        ["shield_vein", "脈紋", { opts: { yes: "隆起", no: "埋入" } }],
        ["shield_hair", "絨毛", { kind: "score", hint: "1 光滑 → 5 密毛" }]]],
      ["孢子葉（手）", [
        ["fertile", "概述", { kind: "area" }],
        ["fertile_posture", "姿態", { kind: "multi", opts: POSTURES }],
        ["fertile_length", "長度", { hint: "例如 30–60 cm" }],
        ["fertile_split", "分岔次數", { hint: "例如 2–3、≤5；不分裂記 0" }],
        ["fertile_width", "葉寬", { kind: "score", hint: "1 細 → 5 寬" }],
        ["fertile_hair", "絨毛", { kind: "score", hint: "1 光滑 → 5 密毛" }],
        ["spore", "孢子囊位置", { opts: SPORES }]]],
      ["栽培", [
        ["growth", "生長習性"],
        ["pups", "側芽", { opts: { yes: "會長（群生型）", no: "不長（單株型）" } }],
        ["dormancy", "休眠", { opts: { yes: "有", no: "無" } }],
        ["light", "光照需求", { kind: "score" }], ["light_note", "光照說明"],
        ["water", "澆水量", { kind: "score" }], ["water_note", "澆水說明"],
        ["humidity", "空氣濕度", { kind: "score" }],
        ["min_temp", "建議最低溫 °C", { kind: "number" }], ["max_temp", "建議最高溫 °C", { kind: "number" }],
        ["temp_note", "溫度說明", { kind: "area", hint: "「可耐 X 度」這類耐受紀錄寫在這裡" }]]]
    ],
    regions: [["", [
      ["key", "代號", { hint: "英文小寫、數字與 -；建立後不能改" }], ["label", "名稱"], ["color", "代表色", { kind: "color" }]]]],
    sources: [["", [
      ["id", "代號", { hint: "英文小寫、數字與 -；建立後不能改" }], ["title", "標題"], ["publisher", "網站／出版者"],
      ["url", "網址"], ["archive_url", "存檔網址"],
      ["type", "類型", { opts: { vendor: "商品頁", article: "文章・新聞", database: "彙整資料庫", reference: "學術文獻" } }],
      ["lang", "語言", { hint: "例如 zh-TW、en、ja" }], ["published", "發布日期"], ["accessed", "查閱日期"],
      ["reliability", "可靠度", { opts: { primary: "育種者・命名者自述", secondary: "業者・媒體", aggregator: "二手彙整" } }],
      ["tier", "來源等級", { opts: { T1: "T1 學術文獻", T2: "T2 機構與專家", T3: "T3 業者與玩家", T4: "T4" } }],
      ["region", "地區", { hint: "例如 台灣、美國；學術文獻填 學術" }], ["short", "顯示用簡稱"], ["note", "備註", { kind: "area" }]]]],
    citations: [["", [
      ["plant_id", "品種", { list: "dd-plant-ids" }], ["source_id", "來源", { list: "dd-source-ids" }],
      ["field", "欄位", { hint: "特徵欄位用 plants.csv 欄位名；其他用 exists、name、parents、base、breeder、origin、aka、note" }],
      ["value", "值", { hint: "換算後的值，特徵欄位必填" }], ["label", "原始標記"],
      ["use", "用途", { opts: USES }], ["claim", "說法", { kind: "area" }],
      ["quote", "原文摘錄", { kind: "area" }], ["page", "頁碼"]]]],
    photos: [["", [
      ["id", "品種", { list: "dd-plant-ids" }], ["src", "照片路徑", { readonly: true }], ["caption", "說明"],
      ["credit", "作者"], ["license", "授權", { list: "pd-licenses" }], ["source", "出處網址"],
      ["variant", "變異株", { hint: "斑葉等非典型個體才填" }]]]]
  };
  // 資料表清單每列顯示的摘要
  const TABLES = {
    plants: { label: "品種", file: "plants.csv", cols: (r) => [r.id, r.zh, r.name] },
    regions: { label: "地區", file: "regions.csv", cols: (r) => [r.key, r.label, r.color] },
    sources: { label: "來源", file: "sources.csv", cols: (r) => [r.id, r.short || r.publisher, r.title] },
    citations: { label: "引用", file: "citations.csv",
      cols: (r) => [`${r.plant_id} ← ${r.source_id}`, `${r.field}${r.value ? ` = ${r.value}` : ""}`, r.claim] },
    photos: { label: "照片", file: "photos.csv", cols: (r) => [r.id, r.src.split("/").pop(), r.caption || r.credit] }
  };
  const LIST_MAX = 200;

  // 資料改動後重新讀取 CSV，重畫圖鑑與關係圖；有指定網址就跳過去
  async function reloadData(hash) {
    const y = window.scrollY;
    await loadData();
    graph.refresh();
    if (hash && location.hash !== hash) { location.hash = hash; return; } // hashchange 會呼叫 route()
    route();
    window.scrollTo(0, y);
  }

  const dataEditor = (() => {
    const dlg = document.getElementById("data-dlg");
    const body = dlg.querySelector("#dd-body"), title = dlg.querySelector("#dd-title");
    const msg = dlg.querySelector("#dd-msg"), backBtn = dlg.querySelector('[data-dd="back"]');
    // view：目前畫面；cache：已讀取的資料表；goto：關閉後要前往的網址
    let view = null, cache = {}, changed = false, dirty = false, goto = null;

    // 表單畫面的訊息顯示在固定於底部的按鈕列，捲到哪都看得到
    const say = (text, err = false) => {
      const el = body.querySelector(".dd-actions .pd-msg") || msg;
      msg.textContent = ""; el.textContent = text; el.classList.toggle("err", err);
    };
    const load = async (name) => (cache[name] = await api(`api/data/${name}`));

    function datalists() {
      const opt = (v, l) => `<option value="${esc(v)}"${l ? ` label="${esc(l)}"` : ""}>`;
      return `<datalist id="dd-plant-ids">${ITEMS.map((it) => opt(it.id, titleOf(it))).join("")}</datalist>
        <datalist id="dd-source-ids">${(cache.sources?.rows || []).map((r) => opt(r.id, r.short || r.title)).join("")}</datalist>`;
    }

    /* ---- 資料表：分頁、搜尋、清單 ---- */
    async function showTable(name, q = "") {
      if (dirty && !confirm("表單還沒儲存，確定離開？")) return;
      dirty = false;
      say("讀取中…");
      const t = cache[name] || await load(name);
      say("");
      view = { kind: "table", name, q };
      title.textContent = "資料表";
      backBtn.hidden = true;
      body.innerHTML = `
        <div class="chips dd-tabs" role="group" aria-label="資料表">${Object.entries(TABLES).map(([k, x]) =>
          `<button type="button" class="chip" aria-pressed="${k === name}" data-dd-table="${k}">${x.label}</button>`).join("")}</div>
        <div class="dd-bar">
          <input type="search" id="dd-q" placeholder="搜尋 ${esc(TABLES[name].file)}…" value="${esc(q)}" autocomplete="off">
          ${t.add ? `<button type="button" class="pd-upload" data-dd-new>＋ 新增</button>` : ""}
        </div>
        <p class="hint" id="dd-count"></p>
        <div class="dd-rows" id="dd-rows"></div>
        ${name === "photos" ? `<p class="hint">新增、刪除照片請用品種頁的「管理照片」，照片檔才會一併處理。</p>` : ""}`;
      const input = body.querySelector("#dd-q");
      input.addEventListener("input", () => { view.q = input.value; renderRows(); });
      renderRows();
      input.focus();
    }

    function renderRows() {
      const t = cache[view.name], words = view.q.toLowerCase().split(/\s+/).filter(Boolean);
      const hits = t.rows.map((r, i) => [r, i]).filter(([r]) => {
        const text = Object.values(r).join(" ").toLowerCase();
        return words.every((w) => text.includes(w));
      });
      body.querySelector("#dd-count").textContent = hits.length > LIST_MAX
        ? `共 ${hits.length} 筆，只顯示前 ${LIST_MAX} 筆，請用搜尋縮小範圍` : `共 ${hits.length} 筆`;
      body.querySelector("#dd-rows").innerHTML = hits.slice(0, LIST_MAX).map(([r, i]) => {
        const [a, b, c] = TABLES[view.name].cols(r).map((x) => esc(x || ""));
        return `<button type="button" class="dd-row" data-dd-row="${i}"><b>${a}</b><span>${b}</span><small>${c}</small></button>`;
      }).join("") || `<p class="muted">沒有符合的資料</p>`;
    }

    /* ---- 表單：一列資料 ---- */
    // orig 為 null 時是新增；init 是新增時預填的值
    async function showForm(name, orig, { init = {}, back = view?.kind === "table" ? { ...view } : null } = {}) {
      const t = cache[name] || await load(name);
      if (name === "citations" && !cache.sources) await load("sources");
      dirty = false;
      view = { kind: "form", name, orig, back };
      const row = orig || init;
      const label = TABLES[name].label;
      title.textContent = orig ? `編輯${label}・${TABLES[name].cols(orig)[0]}` : `新增${label}`;
      backBtn.hidden = !back;

      // 依 FORMS 分組；CSV 裡有、表單沒列到的欄位放在「其他」，表單有、CSV 沒有的欄位略過
      const listed = new Set();
      const groups = FORMS[name].map(([g, fields]) => [g, fields.filter(([k]) => t.header.includes(k) && listed.add(k))]);
      const rest = t.header.filter((k) => !listed.has(k));
      if (rest.length) groups.push(["其他", rest.map((k) => [k, k])]);

      const surveyed = name === "plants" && orig?.survey_version;
      body.innerHTML = `
        <form class="dd-form" id="dd-form" novalidate>
          ${surveyed ? `<p class="note">此品種已依調查指引 ${esc(orig.survey_version)} 整理，特徵欄位由 project_plan/survey/survey_species.py 產生；重新執行腳本會覆蓋這裡對特徵欄位的修改，記得同步改腳本或 citations。</p>` : ""}
          ${groups.map(([g, fields]) => `
            <fieldset>${g ? `<legend>${esc(g)}</legend>` : ""}
              <div class="pd-fields">${fields.map(([k, lbl, o = {}]) => fieldHTML(name, k, lbl, o, row[k] ?? "")).join("")}</div>
            </fieldset>`).join("")}
          ${datalists()}
          <div class="pd-actions dd-actions">
            <p class="pd-msg" role="status"></p>
            ${orig && t.add ? `<button type="button" class="link-btn danger" data-dd-del>刪除</button>
              <button type="button" class="link-btn" data-dd-copy>複製成新的一列</button>` : ""}
            <button type="submit" class="pd-upload">${orig ? "儲存" : "新增"}</button>
          </div>
        </form>`;
      const form = body.querySelector("#dd-form");
      form.addEventListener("input", () => { dirty = true; });
      form.addEventListener("submit", (e) => { e.preventDefault(); save(); });
      // 色票與文字框同步
      form.querySelectorAll("[data-color-for]").forEach((c) => c.addEventListener("input", () => {
        form.elements[c.dataset.colorFor].value = c.value;
      }));
      say("");
      form.querySelector("input:not([readonly]), select, textarea")?.focus();
    }

    function fieldHTML(table, k, lbl, o, v) {
      const key = cache[table].key;
      const locked = o.readonly || (key === k && view.orig);
      const hint = o.hint ? `<small>${esc(o.hint)}</small>` : "";
      const wide = o.kind === "area" ? " wide" : "";
      let input;
      if (o.kind === "multi") {
        const on = splitList(v);
        const opts = { ...o.opts, ...Object.fromEntries(on.filter((x) => !(x in o.opts)).map((x) => [x, x])) };
        input = `<span class="dd-multi" data-multi="${k}">${Object.entries(opts).map(([x, l]) =>
          `<label><input type="checkbox" value="${esc(x)}" ${on.includes(x) ? "checked" : ""}>${esc(l)}</label>`).join("")}</span>`;
        return `<div class="dd-field"><span>${esc(lbl)}</span>${input}${hint}</div>`;
      }
      if (o.opts || o.kind === "score") {
        const opts = o.kind === "score" ? { 1: "1", 2: "2", 3: "3", 4: "4", 5: "5" } : typeof o.opts === "function" ? o.opts() : o.opts;
        // CSV 裡的舊值不在選項中時也保留，避免一打開就被清掉
        const all = v && !(v in opts) ? { ...opts, [v]: `${v}（不在選項中）` } : opts;
        input = `<select name="${k}" ${locked ? "disabled" : ""}><option value="">${o.kind === "score" ? "未知" : "（空白）"}</option>${
          Object.entries(all).map(([x, l]) => `<option value="${esc(x)}" ${x === v ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
      } else if (o.kind === "area") {
        input = `<textarea name="${k}" rows="3">${esc(v)}</textarea>`;
      } else if (o.kind === "color") {
        input = `<span class="dd-color"><input type="color" data-color-for="${k}" value="${/^#[0-9a-f]{6}$/i.test(v) ? esc(v) : "#6b7d72"}">
          <input name="${k}" value="${esc(v)}" placeholder="#3f8f6b"></span>`;
      } else {
        input = `<input name="${k}" value="${esc(v)}" ${o.kind === "number" ? `inputmode="decimal"` : ""}
          ${o.list ? `list="${o.list}"` : ""} ${locked ? "readonly" : ""} autocomplete="off">`;
      }
      return `<label class="dd-field${wide}"><span>${esc(lbl)}</span>${input}${hint}</label>`;
    }

    function formValues() {
      const form = body.querySelector("#dd-form");
      const row = {};
      for (const k of cache[view.name].header) {
        const multi = form.querySelector(`[data-multi="${k}"]`);
        if (multi) row[k] = [...multi.querySelectorAll("input:checked")].map((c) => c.value).join("|");
        else if (form.elements[k]) row[k] = form.elements[k].value.trim();
        else row[k] = view.orig?.[k] ?? "";
      }
      if (view.orig && cache[view.name].key) row[cache[view.name].key] = view.orig[cache[view.name].key];
      return row;
    }

    async function save() {
      const { name, orig } = view;
      const row = formValues();
      say("儲存中…");
      try {
        await api("api/data/save", { table: name, orig, row });
        changed = true; dirty = false;
        delete cache[name];
        if (name === "plants" && !orig) goto = `#/p/${encodeURIComponent(row.id)}`;
        say(`已寫入 data/${TABLES[name].file}`);
        // 從資料表進來的回到清單；從品種頁直接編輯的關閉對話框，馬上看到結果
        if (view.back) { await showTable(view.back.name, view.back.q); say(`已寫入 data/${TABLES[name].file}`); }
        else dlg.close();
      } catch (e) { say(`儲存失敗：${e.message}`, true); }
    }

    async function remove() {
      const { name, orig } = view;
      const what = TABLES[name].cols(orig)[0];
      if (!confirm(`確定從 ${TABLES[name].file} 刪除「${what}」？`)) return;
      try {
        await api("api/data/delete", { table: name, orig });
        changed = true; dirty = false;
        delete cache[name];
        if (name === "plants" && location.hash === `#/p/${encodeURIComponent(orig.id)}`) goto = "#/";
        if (view.back) { await showTable(view.back.name, view.back.q); say("已刪除"); }
        else dlg.close();
      } catch (e) { say(e.message, true); }
    }

    dlg.addEventListener("click", async (e) => {
      const r = dlg.getBoundingClientRect();
      if (e.target === dlg && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) return close();
      const b = e.target.closest("button");
      if (!b) return;
      try {
        if (b.dataset.dd === "close") close();
        else if (b.dataset.dd === "back" && view.back) showTable(view.back.name, view.back.q);
        else if (b.dataset.ddTable) showTable(b.dataset.ddTable);
        else if (b.dataset.ddRow) showForm(view.name, cache[view.name].rows[Number(b.dataset.ddRow)]);
        else if (b.hasAttribute("data-dd-new")) showForm(view.name, null, { init: newRowDefaults(view.name, view.q) });
        else if (b.hasAttribute("data-dd-del")) remove();
        else if (b.hasAttribute("data-dd-copy")) {
          const init = formValues();
          if (cache[view.name].key) init[cache[view.name].key] = "";
          showForm(view.name, null, { init, back: view.back });
          dirty = true;
          say("已複製，請填入新的代號後按「新增」");
        }
      } catch (err) { say(err.message, true); }
    });

    // 從資料表新增時預填；引用的搜尋字剛好是品種 id 就帶入（品種頁的「引用」按鈕會這樣打開）
    function newRowDefaults(name, q) {
      if (name === "plants") return { type: "species" };
      if (name === "citations") return { plant_id: BY_ID.has(q.trim()) ? q.trim() : "", use: "summary" };
      return {};
    }

    const close = () => {
      if (dirty && !confirm("表單還沒儲存，確定關閉？")) return;
      dirty = false;
      dlg.close();
    };
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); close(); }); // Esc
    dlg.addEventListener("close", () => {
      body.innerHTML = "";
      cache = {};
      if (!changed) return;
      changed = false;
      const hash = goto; goto = null;
      reloadData(hash).catch((err) => alert(`重新讀取資料失敗：${err.message}`));
    });

    async function open(fn) {
      say(""); changed = false; dirty = false; goto = null; view = null;
      body.innerHTML = "";
      dlg.showModal();
      try { await fn(); } catch (e) { say(e.message, true); }
    }

    return {
      get isOpen() { return dlg.open; },
      table: (name, q = "") => open(() => showTable(name, q)),
      // 直接開某品種的表單；從品種頁進來，存檔後留在表單
      editPlant: (id) => open(async () => {
        const t = await load("plants");
        const row = t.rows.find((r) => r.id === id);
        if (!row) throw new Error(`plants.csv 裡找不到 ${id}`);
        await showForm("plants", row, { back: null });
      }),
      newPlant: () => open(() => showForm("plants", null, { init: { type: "species" }, back: null }))
    };
  })();

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-data-edit], [data-table-open], [data-plant-new]");
    if (!b) return;
    e.preventDefault();
    if (b.dataset.dataEdit) dataEditor.editPlant(b.dataset.dataEdit);
    else if (b.dataset.tableOpen) dataEditor.table(b.dataset.tableOpen, b.dataset.tableQ || "");
    else dataEditor.newPlant();
  });

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

  /* 分隔線：拖拉調整左右比例（存百分比，視窗縮放時維持比例；上下限與 CSS 的 clamp 相同） */
  (() => {
    const divider = document.getElementById("pane-divider");
    const shell = document.querySelector(".shell");
    const DEFAULT = 45.45, GRAPH_MIN = 300, CONTENT_MIN = 380;
    const clampPct = (pct) => {
      const w = shell.clientWidth || 1;
      const lo = GRAPH_MIN / w * 100, hi = 100 - CONTENT_MIN / w * 100;
      return Math.round(Math.min(Math.max(pct, lo), Math.max(lo, hi)) * 100) / 100;
    };
    const apply = (pct, save) => {
      shell.style.setProperty("--split", pct + "%");
      divider.setAttribute("aria-valuenow", String(Math.round(pct)));
      if (save) try { localStorage.setItem("split", String(pct)); } catch (e) { /* 無痕模式等 */ }
    };
    let saved = NaN;
    try { saved = parseFloat(localStorage.getItem("split")); } catch (e) { /* 無痕模式等 */ }
    apply(saved > 0 && saved < 100 ? saved : DEFAULT, false);
    divider.setAttribute("aria-valuemin", "0");
    divider.setAttribute("aria-valuemax", "100");

    const pctAt = (x) => {
      const r = shell.getBoundingClientRect();
      return clampPct((x - r.left) / r.width * 100);
    };
    divider.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      divider.setPointerCapture(e.pointerId);
      document.body.classList.add("resizing");
      const move = (ev) => apply(pctAt(ev.clientX), false);
      const end = (ev) => {
        divider.removeEventListener("pointermove", move);
        divider.removeEventListener("pointerup", end);
        divider.removeEventListener("pointercancel", end);
        document.body.classList.remove("resizing");
        apply(pctAt(ev.clientX), true);
      };
      divider.addEventListener("pointermove", move);
      divider.addEventListener("pointerup", end);
      divider.addEventListener("pointercancel", end);
    });
    // 雙擊還原預設比例
    divider.addEventListener("dblclick", () => apply(DEFAULT, true));
    // 鍵盤：左右鍵微調，Shift 加大步距，Home／End 到上下限
    divider.addEventListener("keydown", (e) => {
      const cur = clampPct(parseFloat(shell.style.getPropertyValue("--split")) || DEFAULT);
      const step = e.shiftKey ? 10 : 2;
      const next = { ArrowLeft: cur - step, ArrowRight: cur + step, Home: 0, End: 100 }[e.key];
      if (next === undefined) return;
      e.preventDefault();
      apply(clampPct(next), true);
    });
  })();

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
    const focusBtn = graphPane.querySelector("[data-graph-focus]");
    let d3 = null, svg = null, root = null, zoom = null, sim = null, loading = null;
    let nodes = [], links = [], byId = new Map(), up = new Map(), down = new Map();
    let selected = null, hovering = null, warming = false;
    let userMoved = false; // 使用者自己縮放／拖曳過就不再自動全覽
    let showIsolated = true, pinFocus = true; // pinFocus：品種頁期間持續淡化無關的品種
    // 品種頁開著時節點固定不動（不漂浮、不重新模擬），離開品種頁才恢復
    const frozen = () => calm || !!selected;
    const resume = () => { if (sim && !frozen() && !graphPane.hidden && !document.hidden) sim.restart(); };
    try {
      showIsolated = localStorage.getItem("graph-isolated") !== "0";
      pinFocus = localStorage.getItem("graph-focus") !== "0";
    } catch (e) { /* 無痕模式等 */ }

    const loadScript = (src) => new Promise((ok, fail) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = ok;
      s.onerror = () => fail(new Error(`無法載入 ${src}`));
      document.head.append(s);
    });

    const showMsg = (html) => { msg.innerHTML = html; msg.hidden = !html; };

    // 節點標籤：原生種、品系用短名；雜交種用俗名，沒有俗名就用交配式
    const nodeLabel = (it) => (it.type === "hybrid" && it.parents.length ? it.zh || crossOf(it) : shortZh(it));
    // 往上的連結：雜交親本（實線）＋ 品系的選拔來源（虛線）
    const upIds = (it) => (it.base ? [...it.parents, it.base] : it.parents);

    const measure = (() => {
      const ctx = document.createElement("canvas").getContext("2d");
      return (text) => { ctx.font = `600 14px ${FONT}`; return ctx.measureText(text).width; };
    })();

    // 世代：原生種 0，雜交種、品系 = 最深的親本／來源 + 1（之後有多代雜交也能分層）
    const genCache = new Map();
    function gen(id, depth = 0) {
      if (genCache.has(id)) return genCache.get(id);
      const it = BY_ID.get(id);
      const ups = it ? upIds(it) : [];
      const g = !ups.length || depth > 10 ? 0 : 1 + Math.max(...ups.map((p) => gen(p, depth + 1)));
      genCache.set(id, g);
      return g;
    }

    function graphData() {
      const linked = new Set();
      for (const it of ITEMS) if (upIds(it).length) [it.id, ...upIds(it)].forEach((id) => linked.add(id));

      const list = [], edges = [], missing = new Set();
      const add = (id, label, type, color) =>
        list.push({ id, label, type, color, linked: linked.has(id), gen: gen(id),
          w: Math.ceil(measure(label)) + (type === "hybrid" ? 40 : type === "cultivar" ? 32 : 26) });

      for (const it of ITEMS) {
        if (!showIsolated && !linked.has(it.id) && it.id !== selected) continue;
        add(it.id, nodeLabel(it), it.type, regionOf(it).color);
      }
      for (const it of ITEMS) for (const pid of upIds(it)) {
        if (!BY_ID.has(pid) && !missing.has(pid)) {
          missing.add(pid);
          console.warn(`[關係圖] ${it.id} 的親本／來源「${pid}」不存在於 plants.csv`);
          add(pid, pid, "missing", "");
        }
        edges.push({ id: `${pid}→${it.id}`, source: pid, target: it.id, kind: pid === it.base ? "base" : "cross" });
      }
      return { list, edges };
    }

    // 外形：原生種圓角矩形、雜交種六角形、品系膠囊形
    function shapePath(d) {
      const hw = d.w / 2, hh = NODE_H / 2;
      if (d.type === "hybrid") {
        const c = 12;
        return `M${-hw},0L${-hw + c},${-hh}L${hw - c},${-hh}L${hw},0L${hw - c},${hh}L${-hw + c},${hh}Z`;
      }
      const r = d.type === "cultivar" ? hh : 9;
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
        .join("path").attr("class", (l) => `g-link ${l.kind}`);
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

      if (fresh || frozen()) {
        // 先在背景算到大致穩定，第一次顯示時不會亂飛；品種頁期間也直接算好，不播放移動過程
        warming = true;
        sim.alpha(fresh ? 1 : .6);
        for (let i = 0; i < (fresh ? 320 : 200); i++) sim.tick();
        warming = false;
        draw();
        if (fresh) fit();
      } else {
        sim.alpha(.6);
      }
      if (frozen()) sim.stop(); else sim.restart();
      mark();
    }

    function dragBehavior() {
      return d3.drag()
        .clickDistance(4)
        .on("start", (e, d) => {
          if (!e.active && !frozen()) sim.alphaTarget(.25).restart();
          d.fx = d.x; d.fy = d.y;
          dragging = true;
          hideTip();
        })
        // 固定時只移動被拖曳的節點，其他節點不受牽動
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; if (frozen()) { d.x = e.x; d.y = e.y; draw(); } })
        .on("end", (e, d) => {
          if (!e.active) sim.alphaTarget(calm ? 0 : .02);
          d.fx = null; d.fy = null; // 放開後由彈簧拉回
          dragging = false;
          if (calm && !selected) sim.alpha(.3).restart();
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
      focus(hovering);
    }

    // 只留下該品種的祖先與後代：滑過時看滑過的品種；沒滑過時，若開啟血緣高亮就看目前的品種，
    // 一直維持到回到圖鑑列表為止
    function focus(id) {
      hovering = id;
      if (!nodeSel) return;
      const key = id || (pinFocus && selected && byId.has(selected) ? selected : null);
      const set = key ? lineage(key) : null;
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
          if (!dragging) sim.stop(); // 滑過時暫停漂浮，節點才不會從游標下溜走
          focus(id);
          showTip(id, e);
        })
        .on("pointermove", (e) => { if (tipId) moveTip(e); })
        .on("pointerout", (e) => {
          if (e.pointerType !== "mouse" || e.relatedTarget?.closest?.(".g-node")) return;
          if (!dragging) resume();
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
        if (document.hidden || graphPane.hidden) sim.stop(); else resume();
      });

      graphPane.querySelector("#graph-legend").innerHTML = `
        <span><i class="lg-sp"></i>原生種</span><span><i class="lg-hy"></i>雜交種</span><span><i class="lg-cv"></i>品系</span>
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
      if (selected && byId.has(selected)) return fitLineage(selected, 500);
      userMoved = false;
      setTimeout(() => fit(500), 350); // 等新加入的節點稍微就位再全覽
    });
    focusBtn.setAttribute("aria-pressed", String(pinFocus));
    focusBtn.addEventListener("click", () => {
      pinFocus = !pinFocus;
      focusBtn.setAttribute("aria-pressed", String(pinFocus));
      try { localStorage.setItem("graph-focus", pinFocus ? "1" : "0"); } catch (e) { /* 無痕模式等 */ }
      focus(hovering);
    });
    // 品種頁：縮放到高亮的血緣範圍；列表頁：全覽
    const fitLineage = (id, dur) => fitTo([...lineage(id)].map((x) => byId.get(x)).filter(Boolean), { dur, pad: 60, maxK: 1.3 });
    graphPane.querySelector("[data-graph-fit]").addEventListener("click", () => {
      if (selected && byId.has(selected)) return fitLineage(selected, 500);
      userMoved = false;
      fit(500);
    });

    // 從圖鑑卡片預覽：效果等同滑過節點（暫停漂浮、只留血緣），並縮放到整個血緣，但不顯示懸浮框。
    // 稍微延遲再套用，滑鼠掃過一排卡片時畫面才不會來回晃
    let previewing = null, previewTimer = 0, beforePreview = null;
    function applyPreview(id) {
      if (!nodeSel || graphPane.hidden || !box.clientWidth) return;
      if (id && !byId.has(id)) id = null;
      if (id === previewing) return;
      if (id && !previewing) beforePreview = d3.zoomTransform(svg.node()); // 列表頁離開時回到原本的視角
      previewing = id;
      nodeSel.classed("hover", (d) => d.id === id);
      if (id) {
        sim.stop();
        nodeSel.filter((d) => d.id === id).raise();
        focus(id);
        // 縮放到能看到整個血緣（祖先＋後代）；沒有親緣的品種就只會置中它自己
        fitLineage(id, 450);
      } else {
        resume();
        focus(null);
        if (selected && byId.has(selected)) center(selected, 450);
        else if (beforePreview) go(beforePreview, 450);
        beforePreview = null;
      }
    }
    function clearPreview() {
      clearTimeout(previewTimer);
      if (!previewing) return;
      previewing = null;
      beforePreview = null;
      hovering = null;
      nodeSel?.classed("hover", false);
      resume();
    }

    return {
      // 面板打開時呼叫：第一次才載入 D3
      show() {
        if (!ITEMS.length) return;
        if (!loading) loading = init().catch((err) => {
          console.error(err);
          showMsg(`關係圖載入失敗：${esc(err.message)}<br>請確認網路連線後重新整理。`);
        });
        else resume();
      },
      hide() { clearPreview(); sim?.stop(); },
      // 資料編輯後重建節點與連線（保留既有節點的位置）
      refresh() {
        genCache.clear();
        if (sim) build();
      },
      preview(id) {
        clearTimeout(previewTimer);
        previewTimer = setTimeout(() => applyPreview(id), id ? 120 : 220);
      },
      // 路由切換時同步目前的品種，並把它移到畫面中央
      select(id) {
        const prev = selected;
        selected = id;
        clearPreview(); // 點卡片換頁時，卡片已被移除、不會再收到 pointerout
        if (!sim) return;
        const isolated = (x) => x && BY_ID.has(x) && !upIds(BY_ID.get(x)).length && !childrenOf(x).length && !cultivarsOf(x).length;
        if (!showIsolated && (isolated(prev) || isolated(id))) build(); else mark();
        if (id) sim.stop(); else resume();
        if (id && !graphPane.hidden) center(id);
      },
      // 「在關係圖中查看」：縮放到該品種的整個家族
      async reveal(id) {
        selected = id;
        this.show();
        await loading;
        if (!sim) return;
        if (!byId.has(id)) build(); else mark();
        sim.stop();
        userMoved = true;
        fitLineage(id, 600);
      }
    };
  })();

  // 圖鑑列表與品種頁的卡片：滑過時在關係圖中預覽該品種
  app.addEventListener("pointerover", (e) => {
    const card = e.target.closest(".card[data-id]");
    if (!card || e.pointerType !== "mouse" || !panes.graph) return;
    graph.preview(card.dataset.id);
  });
  app.addEventListener("pointerout", (e) => {
    const card = e.target.closest(".card[data-id]");
    if (!card || e.pointerType !== "mouse" || card.contains(e.relatedTarget)) return;
    if (!e.relatedTarget?.closest?.(".card[data-id]")) graph.preview(null);
  });

  /* ---------------- 比較 ---------------- */
  // 已選的品種（有順序）存在 localStorage；比較頁以網址 #/compare/a,b,c 為準，方便分享
  const CMP_MAX = 6;
  let onCompare = false;
  const loadJSON = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (e) { return fallback; }
  };
  const saveJSON = (key, v) => {
    try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) { /* 無痕模式等 */ }
  };
  state.compare = [];
  state.cmpBase = null;
  state.cmpQ = "";
  state.cmpOpts = { diff: false, conf: false, collapsed: [], ...loadJSON("cmp-opts", {}) };
  if (!Array.isArray(state.cmpOpts.collapsed)) state.cmpOpts.collapsed = [];
  const inCompare = (id) => state.compare.includes(id);
  const compareHash = () => `#/compare/${state.compare.map(encodeURIComponent).join(",")}`;

  // 卡片上只有圖示，詳細頁的按鈕另有文字
  const cmpToggleInner = (on, withLabel) =>
    icon(on ? "check" : "plus") + (withLabel ? `<span class="lbl">${on ? "已加入比較" : "加入比較"}</span>` : "");
  function cmpToggleBtn(it, cls) {
    const on = inCompare(it.id);
    return `<button type="button" class="${cls}" data-cmp-toggle="${esc(it.id)}" aria-pressed="${on}"
      aria-label="${on ? "從比較移除" : "加入比較"}：${esc(titleOf(it))}" title="${on ? "從比較移除" : "加入比較"}">${
      cmpToggleInner(on, !cls.includes("card-cmp"))}</button>`;
  }
  // 就地更新按鈕狀態（不重建元素，鍵盤焦點才不會跑掉）
  function syncCmpToggles() {
    document.querySelectorAll("[data-cmp-toggle]").forEach((b) => {
      const it = BY_ID.get(b.dataset.cmpToggle);
      if (!it) return;
      const on = inCompare(it.id);
      if (b.getAttribute("aria-pressed") === String(on)) return;
      b.setAttribute("aria-pressed", String(on));
      b.setAttribute("aria-label", `${on ? "從比較移除" : "加入比較"}：${titleOf(it)}`);
      b.title = on ? "從比較移除" : "加入比較";
      b.innerHTML = cmpToggleInner(on, !b.classList.contains("card-cmp"));
    });
  }

  // 暫時的提示訊息（例如已達上限），比較列與比較頁各有一個顯示位置
  let cmpMsgTimer = null;
  function cmpNotice(msg) {
    clearTimeout(cmpMsgTimer);
    document.querySelectorAll("[data-cmp-msg]").forEach((el) => { el.textContent = msg; });
    cmpMsgTimer = setTimeout(() => document.querySelectorAll("[data-cmp-msg]").forEach((el) => { el.textContent = ""; }), 3200);
  }

  function addCompare(ids) {
    const fresh = ids.filter((id) => BY_ID.has(id) && !inCompare(id));
    const room = CMP_MAX - state.compare.length;
    if (fresh.length > room) cmpNotice(`最多比較 ${CMP_MAX} 個品種，請先移除一些。`);
    if (!room) return;
    state.compare.push(...fresh.slice(0, room));
    compareChanged();
  }
  function removeCompare(id) {
    state.compare = state.compare.filter((x) => x !== id);
    if (state.cmpBase === id) state.cmpBase = null;
    compareChanged();
  }
  function moveCompare(id, d) {
    const i = state.compare.indexOf(id), j = i + d;
    if (i < 0 || j < 0 || j >= state.compare.length) return;
    [state.compare[i], state.compare[j]] = [state.compare[j], state.compare[i]];
    compareChanged();
  }
  function setCompare(ids) {
    state.compare = [...new Set(Array.isArray(ids) ? ids : [])].filter((id) => BY_ID.has(id)).slice(0, CMP_MAX);
    if (!inCompare(state.cmpBase)) state.cmpBase = null;
  }

  function compareChanged() {
    saveJSON("compare", state.compare);
    if (onCompare) {
      // 不觸發 hashchange，直接重繪比較頁並保留捲動位置
      history.replaceState(null, "", compareHash());
      renderCompare({ keepScroll: true });
    } else syncCmpToggles();
    renderTray();
  }

  // 回到頂端：往下捲超過一個視窗高度才出現
  const toTop = document.getElementById("to-top");
  const syncToTop = () => { toTop.hidden = window.scrollY < innerHeight * 0.8; };
  window.addEventListener("scroll", syncToTop, { passive: true });
  syncToTop();
  toTop.addEventListener("click", () => {
    const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: calm ? "auto" : "smooth" });
    app.focus({ preventScroll: true });
  });

  // 圖鑑底部的比較列：在比較頁或還沒選任何品種時隱藏
  const tray = document.getElementById("cmp-tray");
  function renderTray() {
    state.compare = state.compare.filter((id) => BY_ID.has(id)); // 資料編輯後可能刪掉了某個品種
    const n = state.compare.length;
    tray.hidden = onCompare || !n;
    if (tray.hidden) { tray.innerHTML = ""; return; }
    tray.innerHTML = `
      <div class="cmp-picks">${state.compare.map((id) => {
        const it = BY_ID.get(id);
        return `<span class="cmp-pick" title="${esc(titleOf(it))}">
          <a class="cmp-open" href="#/p/${encodeURIComponent(id)}" aria-label="開啟：${esc(titleOf(it))}">
            <img src="${esc(coverOf(it))}" alt="">
            <span class="nm">${esc(titleOf(it))}</span>
          </a>
          <button type="button" data-cmp-remove="${esc(id)}" aria-label="從比較移除：${esc(titleOf(it))}">${icon("close")}</button>
        </span>`;
      }).join("")}</div>
      <span class="cmp-n">${n}／${CMP_MAX}</span>
      <span class="cmp-msg" data-cmp-msg role="status"></span>
      <button type="button" class="link-btn" data-cmp-clear>清除</button>
      <button type="button" class="done-btn" data-cmp-go ${n < 2 ? "disabled" : ""}>${n < 2 ? "再選一個" : "比較 →"}</button>`;
  }

  /* ---------- 比較頁：列定義 ---------- */
  // value：判斷「是否有差異」；num：與基準比較高低；render：顯示；fields：對應 features.csv 的欄位（可信度、沿用）
  const vocabText = (map) => (it, k) => (it[k] ? esc(map[it[k]] || it[k]) : "");
  const scoreRow = (key, label, render, sub) => ({ key, label, sub, num: (it) => it[key], render });
  const meterRow = (key, label, lo, hi) => scoreRow(key, label, (it) => it[key] == null ? "" : meter(it[key], lo, hi, label), `${lo} → ${hi}`);
  const vocabRow = (key, label, map) => ({ key, label, render: (it) => vocabText(map)(it, key) });
  const CMP_GROUPS = [
    { key: "quick", label: "快速指標", rows: [
      { key: "size", label: "尺寸", num: (it) => SIZE_RANK[it.size], render: sizeScale, hint: (it) => SIZES[it.size], legacy: "size_note" },
      scoreRow("difficulty", "栽培難度", (it) => it.difficulty == null ? "" :
        `${stars(it.difficulty)}<small class="cmp-sub">${DIFF_LABEL[it.difficulty]}</small>`, "入門 → 挑戰"),
      { ...scoreRow("light", "光照需求", (it) => it.light == null ? "" : iconRating(it.light, "sun", "光照")), legacy: "light_note" },
      { ...scoreRow("water", "澆水量", (it) => it.water == null ? "" : iconRating(it.water, "drop", "澆水")), legacy: "water_note" },
      scoreRow("humidity", "空氣濕度", (it) => it.humidity == null ? "" : iconRating(it.humidity, "humid", "濕度")),
      { key: "temp", label: "建議溫度", sub: "0–40°C", fields: ["min_temp", "max_temp"], legacy: "temp_note",
        value: (it) => `${it.min_temp ?? ""}|${it.max_temp ?? ""}`,
        render: (it) => it.min_temp == null && it.max_temp == null ? "" : tempRange(it) },
      { ...vocabRow("pups", "繁殖方式", { yes: "群生型", no: "單株型" }),
        hint: (it) => ({ yes: "會長側芽，可分株", no: "不長側芽，以孢子繁殖" })[it.pups] },
      { ...vocabRow("dormancy", "休眠期", { yes: "有", no: "無明顯休眠" }), hint: (it) => it.dormancy === "yes" ? "休眠期需減少澆水" : "" }] },
    { key: "shield", label: "盾葉", icon: "shield", rows: [
      vocabRow("shield_form", "冠形", SHIELD_FORMS),
      meterRow("shield_height", "冠高", "貼伏", "高聳"),
      vocabRow("shield_browning", "老化", SHIELD_BROWNING),
      vocabRow("shield_fringe", "領片", SHIELD_FRINGE),
      vocabRow("shield_vein", "脈紋", { yes: "隆起", no: "埋入" }),
      meterRow("shield_hair", "絨毛", "光滑", "密毛")] },
    { key: "fertile", label: "孢子葉", icon: "hand", rows: [
      { key: "posture", label: "姿態", fields: ["fertile_posture"], value: (it) => it.posture.join("|"), render: postureIcons },
      { key: "fertile_length", label: "長度", render: (it) => esc(it.fertile_length) },
      { key: "split", label: "分岔", fields: ["fertile_split"], value: (it) => it.split?.text, num: (it) => it.split?.mid,
        render: (it) => it.split ? (it.split.text === "0" ? "不分岔" : `${esc(it.split.text)} 次`) : "" },
      meterRow("fertile_width", "葉寬", "細", "寬"),
      meterRow("fertile_hair", "絨毛", "光滑", "密毛"),
      vocabRow("spore", "孢子囊", SPORES)] },
    { key: "basic", label: "來源與親本", icon: "info", rows: [
      { key: "type", label: "類型", render: (it) => `<span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span>` },
      { key: "region", label: "地區", render: regionTag },
      { key: "origin", label: "原產地", render: (it) => esc(it.origin) },
      { key: "lineage", label: "親本／來源", fields: [],
        value: (it) => (it.base ? `base:${it.base}` : it.parents.join("|")),
        render: (it) => {
          const link = (id) => BY_ID.has(id)
            ? `<a class="cmp-link" href="#/p/${encodeURIComponent(id)}">${esc(titleOf(BY_ID.get(id)))}</a>` : esc(id);
          if (baseOf(it)) return `選自 ${link(it.base)}`;
          return it.parents.map(link).join(`<span class="muted"> × </span>`);
        } },
      { key: "breeder", label: "選育者", fields: [], render: (it) => esc(it.breeder) },
      { key: "confidence", label: "資料可信度", fields: [], render: confBadge },
      { key: "desc", label: "簡介", fields: [], hint: (it) => it.desc, // 格子裡只顯示前幾行，完整內容放提示
        render: (it) => it.desc ? `<p class="cmp-desc">${esc(it.desc)}</p>` : "" }] }
  ];
  const rowValue = (row, it) => String((row.value ? row.value(it) : it[row.key]) ?? "");

  function cmpCell(row, it, base) {
    const html = row.render(it) || `<span class="muted" title="未知">—</span>`;
    const fields = row.fields || [row.key];
    const meta = [];
    // 與基準比較：只標高低，不評好壞（例如光照高不代表比較好）
    let delta = "";
    if (base && it !== base && row.num) {
      const a = row.num(it), b = row.num(base);
      if (a != null && b != null && a !== b) {
        delta = `比基準「${titleOf(base)}」${a > b ? "高" : "低"}。`;
        meta.push(`<span class="cmp-delta ${a > b ? "up" : "down"}" aria-label="${esc(delta)}">${a > b ? "▲" : "▼"}</span>`);
      }
    }
    const inherited = fields.some((k) => it.inherited.has(k));
    if (inherited) meta.push(`<span class="cmp-inh">沿用</span>`);
    const f = fields.map((k) => it.features[k]).find((x) => x?.summary && FEATURE_CONF[x.confidence]);
    if (f) meta.push(`<span class="cmp-conf ${FEATURE_CONF[f.confidence]}">${esc(f.confidence)}</span>`);

    // 浮動提示：和詳細頁快速指標的卡片一樣，顯示可信度、來源等級與各來源的說法
    const note = cmpNote(row, it, inherited, delta);
    const cls = [it === base && "is-base", note && "has-note"].filter(Boolean).join(" ");
    return `<td${cls ? ` class="${cls}"` : ""}${note ? ` tabindex="0" data-note="${esc(note)}" data-note-h="${esc(`${titleOf(it)}・${row.label}`)}"` : ""}>
      <div class="cmp-v">${html}</div>${meta.length ? `<div class="cmp-meta">${meta.join("")}</div>` : ""}</td>`;
  }

  function cmpNote(row, it, inherited, delta) {
    const fields = row.fields || [row.key];
    // 多個欄位（例如最低溫／最高溫）時，每段前面加上欄位名
    const notes = fields.map((k) => {
      const n = featureNote(it, k);
      return n && fields.length > 1 ? `${FEATURE_LABELS.find(([fk]) => fk === k)?.[1] || k}｜${n}` : n;
    }).filter(Boolean);
    return [
      row.hint?.(it),
      notes.length ? notes.join("\n\n") : row.legacy && it[row.legacy],
      inherited && `尚未個別調查，沿用「${titleOf(baseOf(it))}」的資料。`,
      delta
    ].filter(Boolean).join("\n\n");
  }

  // 比較表的浮動提示只有一個，掛在 body 上（position: fixed），才不會被表格的捲動框裁掉
  const cmpTip = document.createElement("div");
  cmpTip.className = "cmp-tip";
  cmpTip.setAttribute("role", "tooltip");
  cmpTip.id = "cmp-tip";
  document.body.append(cmpTip);
  let tipCell = null;
  function showCmpTip(td) {
    if (tipCell === td) return;
    tipCell?.removeAttribute("aria-describedby"); // 直接從一格移到另一格時，上一格的高亮要清掉
    tipCell = td;
    cmpTip.innerHTML = `<b>${esc(td.dataset.noteH)}</b>${esc(td.dataset.note)}`;
    td.setAttribute("aria-describedby", "cmp-tip");
    cmpTip.classList.add("on");
    placeCmpTip();
  }
  function placeCmpTip() {
    const td = tipCell;
    // 預設在格子下方，空間不夠就放上方；左右不超出視窗
    const r = td.getBoundingClientRect(), gap = 6, pad = 8;
    const w = Math.min(320, innerWidth - pad * 2);
    cmpTip.style.width = `${w}px`;
    const h = cmpTip.offsetHeight;
    const below = r.bottom + gap + h <= innerHeight - pad || r.top - gap - h < pad;
    cmpTip.style.left = `${Math.max(pad, Math.min(r.left, innerWidth - w - pad))}px`;
    cmpTip.style.top = `${below ? r.bottom + gap : r.top - gap - h}px`;
  }
  function hideCmpTip() {
    if (!tipCell) return;
    tipCell.removeAttribute("aria-describedby");
    tipCell = null;
    cmpTip.classList.remove("on");
  }
  app.addEventListener("pointerover", (e) => {
    if (e.pointerType !== "mouse") return; // 觸控改用點按（focus）
    const td = e.target.closest?.(".cmp td.has-note");
    if (td) showCmpTip(td);
    else hideCmpTip();
  });
  app.addEventListener("pointerleave", hideCmpTip);
  app.addEventListener("focusin", (e) => { if (e.target.matches(".cmp td.has-note")) showCmpTip(e.target); });
  app.addEventListener("focusout", (e) => { if (e.target === tipCell) hideCmpTip(); });
  // 視窗或表格捲動時跟著格子移動；格子捲出表格可見範圍就收起
  document.addEventListener("scroll", () => {
    if (!tipCell) return;
    const r = tipCell.getBoundingClientRect(), box = tipCell.closest(".cmp-wrap")?.getBoundingClientRect();
    if (!box || r.bottom < box.top || r.top > box.bottom || r.right < box.left || r.left > box.right) hideCmpTip();
    else placeCmpTip();
  }, true);
  window.addEventListener("resize", hideCmpTip);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideCmpTip(); });

  function cmpHeadCell(it, i, n) {
    const href = `#/p/${encodeURIComponent(it.id)}`;
    const isBase = state.cmpBase === it.id;
    // 雜交種一鍵加入親本、品系一鍵加入選拔來源
    const kin = (it.base ? [it.base] : it.parents).filter((id) => BY_ID.has(id) && !inCompare(id));
    const kinBtn = kin.length && n < CMP_MAX
      ? `<button type="button" class="cmp-kin" data-cmp-add="${esc(kin.join(","))}">${icon("plus")}${it.base ? "加入選拔來源" : "加入親本"}</button>` : "";
    return `<th scope="col" class="cmp-col${isBase ? " is-base" : ""}">
      <a class="cmp-photo" href="${href}" tabindex="-1" aria-hidden="true"><img src="${esc(coverOf(it))}" alt="" loading="lazy"></a>
      <a class="cmp-name" href="${href}">${esc(titleOf(it))}</a>
      <div class="cmp-latin">${esc(it.name)}</div>
      <div class="cmp-acts">
        <button type="button" data-cmp-move="${esc(it.id)}" data-d="-1" ${i === 0 ? "disabled" : ""} aria-label="往左移" title="往左移">‹</button>
        <button type="button" class="cmp-base-btn" data-cmp-base="${esc(it.id)}" aria-pressed="${isBase}"
          title="${isBase ? "取消基準" : "設為基準：其他品種會標出比它高或低"}">基準</button>
        <button type="button" data-cmp-move="${esc(it.id)}" data-d="1" ${i === n - 1 ? "disabled" : ""} aria-label="往右移" title="往右移">›</button>
        <button type="button" data-cmp-remove="${esc(it.id)}" aria-label="移除 ${esc(titleOf(it))}" title="移除">${icon("close")}</button>
      </div>
      ${kinBtn}
    </th>`;
  }

  function renderCompare({ keepScroll = false } = {}) {
    hideCmpTip();
    const wrap = app.querySelector(".cmp-wrap");
    const pos = keepScroll && wrap ? [wrap.scrollLeft, wrap.scrollTop, window.scrollY] : null;
    const refocus = keepScroll && document.activeElement?.id === "cmp-q";

    const items = state.compare.map((id) => BY_ID.get(id));
    const n = items.length;
    const base = BY_ID.get(state.cmpBase);
    const { diff, conf, collapsed } = state.cmpOpts;
    document.title = n ? `比較 ${n} 個品種｜鹿角蕨圖鑑` : "比較｜鹿角蕨圖鑑";

    const groups = CMP_GROUPS.map((g) => {
      let diffN = 0;
      const rows = g.rows.map((row) => {
        const differs = n > 1 && new Set(items.map((it) => rowValue(row, it))).size > 1;
        if (differs) diffN++;
        return `<tr class="${differs ? "diff" : "same"}">
          <th scope="row">${esc(row.label)}${row.sub ? `<small>${esc(row.sub)}</small>` : ""}</th>
          ${items.map((it) => cmpCell(row, it, base)).join("")}
        </tr>`;
      }).join("");
      const open = !collapsed.includes(g.key);
      return `<tbody class="${open ? "" : "collapsed"}${diffN ? "" : " all-same"}" data-g="${g.key}">
        <tr class="cmp-gh"><th colspan="${n + 1}" scope="colgroup">
          <button type="button" data-cmp-group="${g.key}" aria-expanded="${open}">
            <span class="chev" aria-hidden="true">▾</span>${g.icon ? icon(g.icon) : ""}${esc(g.label)}
            <small>${n > 1 ? (diffN ? `${diffN} 項不同` : "全部相同") : ""}</small>
          </button>
        </th></tr>
        ${rows}
      </tbody>`;
    }).join("");

    const table = n ? `
      <div class="cmp-wrap">
        <table class="cmp${diff ? " only-diff" : ""}${conf ? " show-conf" : ""}" style="--n:${n}">
          <caption class="sr-only">${esc(items.map(titleOf).join("、"))} 的特徵比較</caption>
          <thead><tr><th class="cmp-corner" scope="col">特徵</th>${items.map((it, i) => cmpHeadCell(it, i, n)).join("")}</tr></thead>
          ${groups}
        </table>
      </div>` : "";

    app.innerHTML = `
      <nav class="crumbs">
        <a class="back-btn" href="#/">‹ 列表</a><span>/</span><span>比較</span>
      </nav>
      <div class="cmp-head">
        <h1>${icon("compare")}比較品種 <small>${n}／${CMP_MAX}</small></h1>
        <div class="cmp-tools">
          <div class="cmp-add" id="cmp-add">
            <label class="search">
              ${icon("plus")}
              <input id="cmp-q" type="search" autocomplete="off" value="${esc(state.cmpQ)}"
                placeholder="${n >= CMP_MAX ? `已達 ${CMP_MAX} 個上限` : "加入品種：搜尋名稱、別名…"}" ${n >= CMP_MAX ? "disabled" : ""}
                role="combobox" aria-expanded="false" aria-controls="cmp-sugg" aria-autocomplete="list">
            </label>
            <div class="cmp-sugg" id="cmp-sugg" role="listbox" hidden></div>
          </div>
          <label class="switch"><input type="checkbox" data-cmp-opt="diff" ${diff ? "checked" : ""}><span class="sw" aria-hidden="true"></span><span>只顯示差異</span></label>
          <label class="switch"><input type="checkbox" data-cmp-opt="conf" ${conf ? "checked" : ""}><span class="sw" aria-hidden="true"></span><span>可信度</span></label>
          ${n ? `<button type="button" class="link-btn" data-cmp-clear>全部清除</button>` : ""}
        </div>
        <p class="cmp-msg" data-cmp-msg role="status"></p>
      </div>
      ${n < 2 ? `<div class="empty cmp-empty">${n ? "再加入至少一個品種就能開始比較。" : "還沒有選擇品種。"}<br>
        在列表卡片右上角按 ${icon("plus")}，或在上方搜尋加入。</div>` : ""}
      ${table}
      ${n > 1 ? `<p class="hint">「沿用」表示該品系尚未個別調查，暫時沿用選拔來源的栽培資料。評分為品種間的相對比較（1–5）。▲▼ 只表示比基準高或低，不代表好壞。</p>` : ""}`;

    if (pos) {
      const w = app.querySelector(".cmp-wrap");
      if (w) { w.scrollLeft = pos[0]; w.scrollTop = pos[1]; }
      window.scrollTo(0, pos[2]);
    } else window.scrollTo(0, 0);
    if (refocus) app.querySelector("#cmp-q")?.focus(); // focusin 會重新顯示建議清單
  }

  // 加入品種：有輸入就搜尋，沒輸入就列出目前篩選結果
  function showSuggestions() {
    const box = app.querySelector("#cmp-sugg"), input = app.querySelector("#cmp-q");
    if (!box || input.disabled) return;
    const q = state.cmpQ.trim().toLowerCase();
    const pool = q ? ITEMS.filter((it) => searchText(it).includes(q)) : visibleList();
    const list = pool.filter((it) => !inCompare(it.id)).slice(0, 8);
    box.innerHTML = (q ? "" : `<div class="cmp-sugg-h">${activeFeatCount() || state.q || state.type !== "all" || state.region !== "all" ? "來自目前的篩選結果" : "所有品種"}</div>`) +
      (list.length ? list.map((it, i) => `<button type="button" role="option" data-cmp-add="${esc(it.id)}" ${i === 0 ? `aria-selected="true"` : ""}>
          <img src="${esc(coverOf(it))}" alt=""><span><b>${esc(titleOf(it))}</b><i>${esc(it.name)}</i></span>
          <span class="badge ${it.type}">${TYPE_LABEL[it.type]}</span></button>`).join("")
        : `<div class="cmp-sugg-h">找不到符合的品種</div>`);
    box.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }
  function hideSuggestions() {
    const box = app.querySelector("#cmp-sugg");
    if (!box) return;
    box.hidden = true;
    app.querySelector("#cmp-q")?.setAttribute("aria-expanded", "false");
  }

  app.addEventListener("input", (e) => {
    if (e.target.id !== "cmp-q") return;
    state.cmpQ = e.target.value;
    showSuggestions();
  });
  app.addEventListener("focusin", (e) => { if (e.target.id === "cmp-q") showSuggestions(); });
  // 點建議項目時焦點留在搜尋框，否則 focusout 會先把清單收起來，點擊就落空
  app.addEventListener("pointerdown", (e) => { if (e.target.closest("#cmp-sugg")) e.preventDefault(); });
  app.addEventListener("focusout", (e) => {
    const add = app.querySelector("#cmp-add");
    if (add?.contains(e.target) && !add.contains(e.relatedTarget)) hideSuggestions();
  });
  app.addEventListener("keydown", (e) => {
    if (e.target.id !== "cmp-q" && !e.target.closest?.("#cmp-sugg")) return;
    const opts = [...app.querySelectorAll("#cmp-sugg [data-cmp-add]")];
    const i = opts.indexOf(document.activeElement);
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const j = e.key === "ArrowDown" ? Math.min(i + 1, opts.length - 1) : i - 1;
      (j < 0 ? app.querySelector("#cmp-q") : opts[j])?.focus();
    } else if (e.key === "Enter" && e.target.id === "cmp-q" && opts[0]) {
      e.preventDefault();
      opts[0].click();
    } else if (e.key === "Escape") {
      state.cmpQ = "";
      app.querySelector("#cmp-q").value = "";
      hideSuggestions();
    }
  });
  app.addEventListener("change", (e) => {
    const opt = e.target.closest?.("[data-cmp-opt]");
    if (!opt) return;
    state.cmpOpts[opt.dataset.cmpOpt] = opt.checked;
    saveJSON("cmp-opts", state.cmpOpts);
    app.querySelector(".cmp")?.classList.toggle(opt.dataset.cmpOpt === "diff" ? "only-diff" : "show-conf", opt.checked);
  });

  // 比較列在 #app 外面，所以在 document 上委派
  document.addEventListener("click", (e) => {
    const t = (sel) => e.target.closest(sel);
    let el;
    if ((el = t("[data-cmp-toggle]"))) {
      const id = el.dataset.cmpToggle;
      inCompare(id) ? removeCompare(id) : addCompare([id]);
    } else if ((el = t("[data-cmp-add]"))) {
      const fromSearch = !!el.closest("#cmp-sugg");
      if (fromSearch) state.cmpQ = "";
      addCompare(el.dataset.cmpAdd.split(","));
      if (fromSearch) app.querySelector("#cmp-q")?.focus();
    } else if ((el = t("[data-cmp-remove]"))) removeCompare(el.dataset.cmpRemove);
    else if ((el = t("[data-cmp-move]"))) moveCompare(el.dataset.cmpMove, Number(el.dataset.d));
    else if ((el = t("[data-cmp-base]"))) {
      state.cmpBase = state.cmpBase === el.dataset.cmpBase ? null : el.dataset.cmpBase;
      renderCompare({ keepScroll: true });
    } else if ((el = t("[data-cmp-group]"))) {
      const key = el.dataset.cmpGroup, tbody = el.closest("tbody");
      const open = tbody.classList.toggle("collapsed") === false;
      el.setAttribute("aria-expanded", String(open));
      const set = new Set(state.cmpOpts.collapsed);
      open ? set.delete(key) : set.add(key);
      state.cmpOpts.collapsed = [...set];
      saveJSON("cmp-opts", state.cmpOpts);
    } else if (t("[data-cmp-clear]")) {
      state.compare = [];
      state.cmpBase = null;
      compareChanged();
    } else if (t("[data-cmp-go]")) location.hash = compareHash();
    else if (t("[data-cmp-all]")) {
      setCompare(visibleList().map((it) => it.id));
      saveJSON("compare", state.compare);
      location.hash = compareHash();
    }
  });

  /* ---------------- 鍵盤 ---------------- */
  let detailNav = null;
  document.addEventListener("keydown", (e) => {
    if (photoEditor.isOpen || dataEditor.isOpen) return; // Esc 交給對話框自己關閉
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
    hideCmpTip();
    const m = location.hash.match(/^#\/p\/(.+)$/);
    const cmp = location.hash.match(/^#\/compare(?:\/(.*))?$/);
    if (onList) state.scrollY = window.scrollY; // 離開列表時記住捲動位置
    onCompare = !!cmp;
    if (cmp) {
      // 網址是比較清單的依據（可分享），同步回 localStorage
      onList = false;
      detailNav = null;
      setCompare((cmp[1] || "").split(",").map((s) => decodeURIComponent(s)).filter(Boolean));
      saveJSON("compare", state.compare);
      if (location.hash !== compareHash()) history.replaceState(null, "", compareHash());
      renderCompare();
      graph.select(null);
    } else if (m) {
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
    renderTray();
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
  // 靜態主機上沒有這個 API（404），編輯按鈕就不會出現
  const probeEdit = fetch("api/edit", { cache: "no-store" })
    .then((r) => r.ok && r.json()).then((j) => {
      EDIT = !!j?.ok;
      // 舊版 serve.py 只有照片 API，沒有 tables 就不顯示資料編輯
      EDIT_DATA = EDIT && !!j.tables;
      document.getElementById("data-btn").hidden = !EDIT_DATA;
    }).catch(() => {});
  Promise.all([loadData(), probeEdit])
    .then(() => {
      if (panes.graph) graph.show();
      setCompare(loadJSON("compare", []));
      window.addEventListener("hashchange", route);
      route();
    })
    .catch((err) => {
      console.error(err);
      const isFile = location.protocol === "file:";
      app.innerHTML = `<div class="empty">
        <p>資料載入失敗：${esc(err.message)}</p>
        ${isFile ? `<p>瀏覽器不允許直接以檔案（file://）讀取 CSV。<br>請在專案資料夾執行 <code>python3 tools/serve.py</code>，<br>再開啟 <code>http://localhost:8000</code>。</p>` : ""}
      </div>`;
    });
})();
