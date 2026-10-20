"""Shared rules for the feature-survey scripts (guideline v1.3).

Used by survey_species.py (18 native species) and survey_hybrids.py (hybrids and cultivars, one block per plant).
Summary values and confidence follow guideline §5; text columns follow §4 文字欄.

Files are written by flush() at the end of each script, after the manual-edit check (see "manual edits" below).
Each script owns only its own rows. `replace_rows` swaps a script's rows in place (at the position of the first row
it previously wrote, or at the end the first time), so running the scripts in any order gives the same files.
"""
import csv, io, math, os, sys

FIELDS = ["size", "size_note", "shield_form", "shield_height", "shield_vein", "shield_hair", "shield_browning", "shield_fringe",
          "fertile_posture", "fertile_length", "fertile_split", "fertile_width", "fertile_hair", "spore", "pups", "dormancy", "origin",
          "light", "water", "humidity", "min_temp", "max_temp", "difficulty"]
SCALE = {"shield_height", "shield_hair", "fertile_hair", "fertile_width", "light", "water", "humidity", "difficulty"}
TEMP = {"min_temp", "max_temp"}
T1_TEXT = {"fertile_length", "fertile_split", "origin"}
CULT = {"light", "water", "humidity", "min_temp", "max_temp", "difficulty", "dormancy"}
# difficulty: only Taiwan / Southeast Asia sources count toward the summary (guideline v1.2)
DIFF_REGIONS = {"台灣", "新加坡", "馬來西亞", "泰國", "印尼", "菲律賓", "越南"}
VERSION = "v1.3"

CH = ["plant_id", "source_id", "field", "value", "label", "use", "claim", "quote", "page"]
SH = ["id", "title", "publisher", "url", "archive_url", "type", "lang", "published", "accessed", "reliability", "tier", "region", "short", "note"]
FH = ["plant_id", "field", "summary", "confidence", "independent_sources", "by_source", "tiers"]
LH = ["plant_id", "field", "guideline_version", "date", "searched", "status"]

LBL_FORM = {"appressed": "貼伏", "erect-wedge": "直立楔形", "erect-lobed": "直立多裂", "erect-multilobed": "直立多上揚裂片", "spreading-wedge": "展開楔形"}
LBL_BROWN = {"withering": "成熟後枯褐", "green": "保持綠色", "darkening": "轉深綠"}
LBL_FRINGE = {"none": "無", "above-stipe": "葉柄上方", "encircling": "環繞葉柄"}
LBL_POST = {"up": "直立", "spread": "展開", "pendant": "下垂", "spread|pendant": "展開、側裂片下垂"}
LBL_SPORE = {"tips": "末端裂片", "sinus": "分岔凹處", "medial": "裂片中段", "shell-lobe": "獨立殼狀裂片"}


# ---------------------------------------------------------------- summary rules (guideline §5)
def num(v):
    v = v.replace("≤", "")
    if "–" in v and not v.startswith("-"):
        a, b = v.split("–")
        return (float(a) + float(b)) / 2
    return float(v)


def round_scale(x):
    f = math.floor(x)
    if abs(x - f - 0.5) < 1e-9:  # exactly .5 -> toward 3
        return f + 1 if f + 1 <= 3 else f
    return int(round(x))


def round_temp(x, field):
    f = math.floor(x)
    if abs(x - f - 0.5) < 1e-9:  # exactly .5 -> conservative
        return f + 1 if field == "min_temp" else f
    return int(round(x))


def size_class(d):
    return "S" if d <= 30 else "M" if d <= 80 else "L" if d <= 110 else "XL"


DWARF = "S"  # size value of a statement that calls the plant a dwarf (侏儒、dwarf、mini) without measurements (v1.3)


def basis(rows, meta):
    """Morphology (v1.3): summary statements of the highest tier group present (T1 + T2, else T3); True if T3 only."""
    top = [r for r in rows if meta[r[1]]["tier"] in ("T1", "T2")]
    if top:
        return top, False
    return [r for r in rows if meta[r[1]]["tier"] == "T3"], True


def summarize(field, rows, meta):
    """rows: (plant, source, field, value, label, use, claim, quote, page); meta: source id -> tier/region/short/org."""
    use = [r for r in rows if r[5] == "summary" and r[3] != ""]
    if not use:
        return "", ""
    tiers = [meta[r[1]]["tier"] for r in use]
    orgs = {meta[r[1]]["org"] for r in use}
    if field in CULT:
        # v1.2: one care source (T1–T3) is enough for a summary, but its confidence is always 低
        if not set(tiers) <= {"T1", "T2", "T3"}:
            return "", ""
        if field == "difficulty":
            assert all(meta[r[1]]["region"] in DIFF_REGIONS for r in use), rows
        single = len(orgs) < 2
        if field == "dormancy":
            vals = [r[3] for r in use]
            top = max(vals, key=vals.count)  # a tie goes to the first statement (set order would vary between runs)
            if len(set(vals)) > 1 and vals.count(top) * 2 == len(vals):
                return "", ""
            return top, "低" if single or len(set(vals)) > 1 else "高"
        xs = [num(r[3]) for r in use]
        mean, spread = sum(xs) / len(xs), max(xs) - min(xs)
        if field in TEMP:
            val, conf = str(round_temp(mean, field)), "高" if spread <= 3 else "中" if spread <= 8 else "低"
        else:
            val, conf = str(round_scale(mean)), "高" if spread == 0 else "中" if spread <= 2 else "低"
        return val, "低" if single else conf
    # v1.3: morphology takes the highest tier group present; T3 counts only when there is no T1 / T2, and then
    # the confidence is always 低 (T4 is never a summary source)
    use, t3_only = basis(use, meta)
    if not use:
        return "", ""
    # v1.4: relaxed statements (value prefixed "~") count only when the tier group has no strict statement; confidence 低
    use, relaxed = relaxed_or_strict(use)
    val, conf = morph(field, use, meta, "T1" in {meta[r[1]]["tier"] for r in use}, relaxed)
    return val, ("低" if (t3_only or relaxed) and val else conf)


RELAXED = "~"  # value prefix of a relaxed morphology statement (v1.4)
SIZE_CLASSES = ["S", "M", "L", "XL"]


def relaxed_or_strict(rows):
    """Strict rows if there are any, else the relaxed rows with the "~" stripped from their values; and whether relaxed."""
    strict = [r for r in rows if not r[3].startswith(RELAXED)]
    if strict:
        return strict, False
    return [r[:3] + (r[3][len(RELAXED):],) + tuple(r[4:]) for r in rows], True


def morph(field, use, meta, has_t1, relaxed=False):
    if field == "size" and relaxed:
        # whole-plant size or "up to" values give D; size words (小型, 大型 …) give a class only when no number is given
        ds = [num(r[3]) for r in use if r[3] not in SIZE_CLASSES]
        if ds:
            return size_class(sum(ds) / len(ds)), "低"
        ks = [SIZE_CLASSES.index(r[3]) for r in use]
        return SIZE_CLASSES[min(set(ks), key=lambda k: (-ks.count(k), k))], "低"  # majority; a tie goes to the smaller class
    if field == "size":
        ds = [num(r[3]) for r in use if r[3] != DWARF]
        classes = {size_class(d) for d in ds}
        if any(r[3] == DWARF for r in use):
            # a dwarf statement makes the plant S; measured D values outside S lower the confidence
            return "S", "低" if classes - {"S"} else "高" if has_t1 else "中"
        return size_class(sum(ds) / len(ds)), "高" if has_t1 and len(classes) == 1 else "中"
    if field in SCALE:
        xs = [num(r[3]) for r in use]
        spread = max(xs) - min(xs)
        conf = "低" if spread > 2 else "高" if has_t1 and spread == 0 else "中"
        return str(round_scale(sum(xs) / len(xs))), conf
    vals = [r[3] for r in use]
    t1v = [r[3] for r in use if meta[r[1]]["tier"] == "T1"]
    if field in T1_TEXT:
        # measured / place text: the first statement of the best tier, no mixing
        first = t1v[0] if t1v else vals[0]
        return first, "高" if t1v else "中" if all(x == first for x in vals) else "低"
    if t1v:
        # first T1 statement (the monograph) decides; any disagreeing statement lowers confidence
        return t1v[0], "高" if all(x == t1v[0] for x in vals) else "低"
    top = max(vals, key=vals.count)  # a tie goes to the first statement (set order would vary between runs)
    return top, "中" if len(set(vals)) == 1 else "低"


def feature_rows(plants, by, meta):
    """Per-plant summary dict and features.csv rows (detail) from citations grouped by (plant, field)."""
    summary, detail = {}, []
    for sp in plants:
        summary[sp] = {}
        for f in FIELDS:
            if f == "size_note":
                continue
            rows = by.get((sp, f), [])
            if not rows:
                continue
            val, conf = summarize(f, rows, meta)
            summary[sp][f] = val
            shown = [r for r in rows if r[5] != "excluded"]
            disp = "／".join(src_label(r, meta) for r in shown)
            n = len({meta[r[1]]["org"] for r in rows if r[5] == "summary"})
            tiers = "|".join(sorted({meta[r[1]]["tier"] for r in rows if r[5] == "summary" and r[3] != ""}))
            detail.append([sp, f, val, conf, n, disp, tiers])
        sizes, relaxed = relaxed_or_strict([r for r in by.get((sp, "size"), []) if r[5] == "summary"])
        summary[sp]["size_note"] = "；".join(
            f"{meta[r[1]]['short']}（{meta[r[1]]['tier']}）" + (f"：{r[4]}" if relaxed or r[3] == DWARF else f" D = {num(r[3]):g} cm") for r in sizes)
    return summary, detail


def src_label(r, meta):
    """「台灣 微體溫室（T3）：中光」— the tier is shown with every source statement (v1.3)."""
    m = meta[r[1]]
    return f"{m['region']} {m['short']}（{m['tier']}）：{r[4]}".strip() + ("（參考）" if r[5] == "reference" else "（寬鬆）" if r[3].startswith(RELAXED) else "")


# ---------------------------------------------------------------- csv io
def rw(path):
    raw = open(path, encoding="utf-8-sig", newline="").read()
    rows = list(csv.reader(io.StringIO(raw)))
    return rows[0], rows[1:]


def write(path, header, rows):
    """Stage a CSV. Nothing reaches disk until flush(), which checks for manual edits first (see flush)."""
    _PENDING[os.path.abspath(path)] = (list(header), [list(r) for r in rows])


def _write_now(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows([header] + rows)


# ---------------------------------------------------------------- manual edits (overrides and the overwrite guard)
# data/plants.csv and data/citations.csv can also be edited by hand or in the web editor (tools/serve.py). The scripts
# regenerate their own cells and rows, so such edits would be lost. Two safeguards:
#   manual_overrides.csv  cells of plants.csv kept on purpose (plant_id, field, value, reason, date). flush() applies them
#                         after every run; for a feature field, features.csv shows the override and its reason.
#   generated/            what the scripts last wrote. A cell or citation that differs from it was edited by hand; if the
#                         run would overwrite it, flush() writes nothing and lists it. Rerun with --adopt to record the
#                         plants.csv cells in manual_overrides.csv, or --force to overwrite them.
HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDES = os.path.join(HERE, "manual_overrides.csv")
OH = ["plant_id", "field", "value", "reason", "date"]
SNAP = os.path.join(HERE, "generated")
GUARDED = {"plants.csv": "id", "citations.csv": None}  # file -> key column (None: compare whole rows)
_PENDING = {}


def _pending(name):
    return next(((p, v) for p, v in _PENDING.items() if p.endswith(os.sep + "data" + os.sep + name)), (None, None))


def _overrides():
    return [dict(zip(OH, r)) for r in rw(OVERRIDES)[1]] if os.path.exists(OVERRIDES) else []


def _apply_overrides():
    ovs = _overrides()
    _, plants = _pending("plants.csv")
    if plants:
        ph, rows = plants
        byid = {r[0]: r for r in rows}
        for o in ovs:
            assert o["field"] in ph and o["plant_id"] in byid, ("manual_overrides.csv", o)
            byid[o["plant_id"]][ph.index(o["field"])] = o["value"]
    _, feats = _pending("features.csv")
    if feats:
        rows = feats[1]
        for o in ovs:
            if o["field"] not in FIELDS or o["field"] == "size_note":
                continue
            i = next((i for i, r in enumerate(rows) if r[0] == o["plant_id"] and r[1] == o["field"]), None)
            if i is not None and rows[i][3] == "人工調整":  # applied before and not regenerated by this run
                continue
            old = rows[i] if i is not None else [o["plant_id"], o["field"], "", "", "0", "", ""]
            note = f"人工調整（調查摘要 {old[2] or '無'}）：{o['reason']}" + (f"／{old[5]}" if old[5] else "")
            row = [o["plant_id"], o["field"], o["value"], "人工調整", old[4], note, ""]
            if i is not None:
                rows[i] = row
            else:
                last = max((j for j, r in enumerate(rows) if r[0] == o["plant_id"]), default=len(rows) - 1)
                rows.insert(last + 1, row)


def _conflicts():
    """Manual edits (disk differs from the last generated snapshot) that this run would overwrite."""
    out = []
    for name, key in GUARDED.items():
        path, staged = _pending(name)
        snap = os.path.join(SNAP, name)
        if not staged or not os.path.exists(path):
            continue
        if not os.path.exists(snap):
            print(f"注意：沒有 {snap}，這次不檢查 {name} 的手動修改")
            continue
        (dh, disk), (sh_, prev), (nh, new) = rw(path), rw(snap), staged
        if key:
            d = {r[0]: dict(zip(dh, r)) for r in disk}
            s = {r[0]: dict(zip(sh_, r)) for r in prev}
            n = {r[0]: dict(zip(nh, r)) for r in new}
            for pid, dr in d.items():
                for col, v in dr.items():
                    before = s.get(pid, {}).get(col)
                    after = n.get(pid, {}).get(col, "")
                    if v != (before if before is not None else "") and v != after:
                        out.append((name, f"{pid}.{col}", v, after))
        else:
            d, s, n = [tuple(r) for r in disk], [tuple(r) for r in prev], {tuple(r) for r in new}
            ss, ds = set(s), set(d)
            out += [(name, "手動新增或修改的引用", "|".join(r[:4]), "（會被刪除）") for r in d if r not in ss and r not in n]
            out += [(name, "手動刪除的引用", "|".join(r[:4]), "（會被加回）") for r in s if r not in ds and r in n]
    return out


def _adopt(conflicts):
    rows = rw(OVERRIDES)[1] if os.path.exists(OVERRIDES) else []
    today = __import__("datetime").date.today().isoformat()
    for name, cell, value, _ in conflicts:
        if name == "plants.csv":
            pid, col = cell.split(".", 1)
            rows = [r for r in rows if (r[0], r[1]) != (pid, col)] + [[pid, col, value, "手動修改（--adopt 收錄，請補上理由）", today]]
    _write_now(OVERRIDES, OH, rows)


def flush(argv=()):
    """Apply manual_overrides.csv, refuse to overwrite unrecorded manual edits, then write every staged file at once."""
    _apply_overrides()
    conflicts = _conflicts()
    if conflicts and "--adopt" in argv:
        _adopt(conflicts)
        _apply_overrides()
        conflicts = _conflicts()
    if conflicts and "--force" not in argv:
        print("\n停止：下列手動修改會被這次執行覆蓋，所有檔案都沒有寫入。")
        for name, cell, value, after in conflicts:
            print(f"  {name}  {cell}: {value!r} → {after!r}")
        print("處理方式：plants.csv 的修改要保留 → 加進 project_plan/survey/manual_overrides.csv（或加 --adopt 自動收錄）；"
              "引用的修改要保留 → 寫進調查腳本的 block；確定要覆蓋 → 加 --force。")
        sys.exit(1)
    for path, (header, rows) in _PENDING.items():
        _write_now(path, header, rows)
        name = os.path.basename(path)
        if path.endswith(os.sep + "data" + os.sep + name) and name in GUARDED:
            _write_now(os.path.join(SNAP, name), header, rows)
    _PENDING.clear()


def replace_rows(rows, new, owned):
    """Drop rows for which owned(row) is true and put `new` where the first of them was (or at the end)."""
    pos = next((i for i, r in enumerate(rows) if owned(r)), None)
    kept = [r for r in rows if not owned(r)]
    if pos is None:
        return kept + list(new)
    pos -= sum(1 for r in rows[:pos] if owned(r))
    return kept[:pos] + list(new) + kept[pos:]


def source_meta(srows):
    return {r["id"]: dict(tier=r.get("tier", ""), region=r.get("region", ""), short=r.get("short", ""), org=r.get("short") or r["publisher"])
            for r in srows}


# ---------------------------------------------------------------- text columns generated from summaries and labels
FORM_TXT = {"appressed": "上半部貼伏，圓形至腎形", "erect-wedge": "上半部直立，楔形", "erect-lobed": "上半部直立，橢圓形，有多個不等長裂片",
            "erect-multilobed": "上半部直立，楔形，有多個上揚的裂片", "spreading-wedge": "上半部向外展開，楔形，有多個等長裂片"}
BROWN_TXT = {"withering": "成熟後不久即枯褐", "green": "保持綠色直到新盾葉長出", "darkening": "成熟後轉為深綠"}
FRINGE_TXT = {"none": "基部沒有明顯領片", "above-stipe": "基部在孢子葉柄上方有領片", "encircling": "基部有環繞孢子葉柄的領片"}
POST_TXT = {"up": "直立", "spread": "展開", "pendant": "下垂", "spread|pendant": "主葉展開、側生裂片下垂"}
SPORE_TXT = {"tips": "孢子囊群生於末端裂片或葉片上部", "sinus": "孢子囊群生於分岔凹處", "medial": "孢子囊群沿裂片中段生長、面向植株",
             "shell-lobe": "孢子囊群生於獨立、有柄的殼狀孢子葉片"}


def split_txt(v):
    if v == "0":
        return "不分裂"
    if v.startswith("≤"):
        return f"最多分岔 {v[1:]} 次"
    if v.startswith("0–"):
        return f"不分裂至分岔 {v[2:]} 次"
    return f"分岔 {v} 次"


def sentence(parts):
    parts = [p for p in parts if p]
    return "，".join(parts) + "。" if parts else ""


def plant_text(s, labels):
    """s: summary dict of one plant; labels(field) -> joined source labels of that field."""
    vein = {"yes": "葉脈隆起", "no": "葉脈埋入"}.get(s.get("shield_vein"), "")
    shield = sentence([FORM_TXT.get(s.get("shield_form"), ""), BROWN_TXT.get(s.get("shield_browning"), ""),
                       FRINGE_TXT.get(s.get("shield_fringe"), ""), vein])
    length = s.get("fertile_length")
    fertile = sentence([("孢子葉" + POST_TXT[s["fertile_posture"]]) if s.get("fertile_posture") else "",
                        f"長 {length}" if length else "", split_txt(s["fertile_split"]) if s.get("fertile_split") else "",
                        SPORE_TXT.get(s.get("spore"), "")])
    growth = {"yes": "叢生，會長側芽，可分株。", "no": "單生，不長側芽，以孢子繁殖。"}.get(s.get("pups"), "")
    if s.get("dormancy") == "yes":
        growth += f"有固定休眠期（{labels('dormancy')}）。"
    temp = "。".join(f"{n}：{labels(f)}" for n, f in [("最低溫", "min_temp"), ("最高溫", "max_temp")] if labels(f))
    return dict(shield=shield, fertile=fertile, growth=growth, light_note=labels("light"), water_note=labels("water"), temp_note=temp)
