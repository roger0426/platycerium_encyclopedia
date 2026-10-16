#!/usr/bin/env python3
"""本機預覽＋照片／資料編輯伺服器。

取代 `python3 -m http.server`，另外提供照片上傳／刪除 API 與 CSV 資料編輯 API，
網頁偵測到後會顯示照片管理、編輯資料與「資料表」按鈕。
只監聽 127.0.0.1，部署到 GitHub Pages 等靜態主機時沒有這些 API，按鈕自動隱藏。

    python3 tools/serve.py          # http://localhost:8000
    python3 tools/serve.py 8080
"""
import base64
import csv
import io
import json
import re
import sys
import threading
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS_CSV = ROOT / "data" / "photos.csv"
PLANTS_CSV = ROOT / "data" / "plants.csv"
IMAGES = ROOT / "images"
FIELDS = ["id", "src", "caption", "credit", "license", "source", "variant"]
MAX_BYTES = 25 * 1024 * 1024
LOCK = threading.Lock()  # 同時有兩個請求時，避免 CSV 被交錯寫壞
EXTS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
DATA = ROOT / "data"
# 可在網頁上編輯的資料表：檔名、主鍵欄位（None = 沒有唯一鍵，以整列內容比對）、可否新增／刪除。
# features.csv 由 project_plan/survey/survey_species.py 產生，手改會被覆蓋，所以不開放。
# photos.csv 的新增／刪除要連同照片檔一起處理，交給照片管理。
TABLES = {
    "plants": {"file": "plants.csv", "key": "id", "add": True},
    "regions": {"file": "regions.csv", "key": "key", "add": True},
    "sources": {"file": "sources.csv", "key": "id", "add": True},
    "citations": {"file": "citations.csv", "key": None, "add": True},
    "photos": {"file": "photos.csv", "key": "src", "add": False},
}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path, header, rows):
    # 保留原本的欄位順序與 BOM（Excel 開啟才不會亂碼）；先寫暫存檔再取代，寫到一半中斷也不會壞檔
    tmp = path.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def write_photos(header, rows):
    # 有變異株照片時才補 variant 欄
    if any(r.get("variant") for r in rows) and "variant" not in header:
        header = header + ["variant"]
    write_csv(PHOTOS_CSV, header, rows)


def plant_ids():
    return {r["id"] for r in read_csv(PLANTS_CSV)[1] if r.get("id")}


def photos_of(rows, pid):
    return [{k: r.get(k, "") for k in FIELDS} for r in rows if r.get("id") == pid]


def image_path(src):
    """只允許 images/ 底下的檔案，避免刪到其他地方。"""
    p = (ROOT / src).resolve()
    if IMAGES.resolve() not in p.parents:
        raise ValueError("照片路徑必須在 images/ 底下")
    return p


class Conflict(Exception):
    """CSV 在網頁開啟表單後被其他程式改過。"""


def table_of(name):
    if name not in TABLES:
        raise ValueError(f"不能編輯 {name}")
    return TABLES[name]


def same_row(a, b, header):
    return all((a.get(k) or "").strip() == (b.get(k) or "").strip() for k in header)


def find_row(rows, header, key, orig):
    """找出網頁開啟表單時的那一列。有主鍵用主鍵找；內容跟當時不同代表 CSV 在這期間被改過（例如 Excel），拒絕覆蓋。"""
    if key:
        i = next((i for i, r in enumerate(rows) if r.get(key) == orig.get(key)), None)
    else:
        i = next((i for i, r in enumerate(rows) if same_row(r, orig, header)), None)
    if i is None:
        raise Conflict("找不到這一列，可能已被刪除或修改")
    if not same_row(rows[i], orig, header):
        raise Conflict("這一列在你開啟表單後被其他程式改過")
    return i


def split_ids(v):
    return [x.strip() for x in (v or "").split("|") if x.strip()]


def validate(name, row, rows, header, index):
    """檢查必填、唯一鍵與參照；index 是被編輯那一列的位置（新增時為 None）。"""
    t = TABLES[name]
    key = t["key"]
    if key and not row.get(key):
        raise ValueError(f"{key} 不能空白")
    if key and any(r.get(key) == row[key] for i, r in enumerate(rows) if i != index):
        raise ValueError(f"{key}「{row[key]}」已經存在")
    if index is not None and key and rows[index].get(key) != row[key]:
        # 改主鍵要連帶修改照片資料夾、親本、引用等，容易漏改，請直接改 CSV
        raise ValueError(f"{key} 建立後不能在網頁上修改")

    if name == "plants":
        if not ID_RE.match(row["id"]):
            raise ValueError("id 只能用英文小寫、數字與 -")
        if row.get("type") not in ("species", "hybrid", "cultivar"):
            raise ValueError("type 必須是 species、hybrid 或 cultivar")
        ids = {r["id"] for r in rows if r.get("id")} | {row["id"]}
        regions = {r["key"] for r in read_csv(DATA / "regions.csv")[1]}
        if row.get("region") and row["region"] not in regions:
            raise ValueError(f"找不到地區 {row['region']}")
        for k in ("parents", "base"):
            for x in split_ids(row.get(k)):
                if x == row["id"]:
                    raise ValueError(f"{k} 不能指向自己")
                if x not in ids:
                    raise ValueError(f"{k} 裡的 {x} 不在 plants.csv")
        if len(split_ids(row.get("base"))) > 1:
            raise ValueError("base 只能有一個")
    elif name == "regions":
        if not ID_RE.match(row["key"]):
            raise ValueError("key 只能用英文小寫、數字與 -")
    elif name == "sources":
        if not ID_RE.match(row["id"]):
            raise ValueError("id 只能用英文小寫、數字與 -")
    elif name == "citations":
        if row.get("plant_id") not in plant_ids():
            raise ValueError(f"找不到品種 {row.get('plant_id')}")
        if row.get("source_id") not in {r["id"] for r in read_csv(DATA / "sources.csv")[1]}:
            raise ValueError(f"找不到來源 {row.get('source_id')}")
    elif name == "photos":
        if row.get("id") not in plant_ids():
            raise ValueError(f"找不到品種 {row.get('id')}")


def references(name, value):
    """刪除前檢查還有誰用到這個鍵，回傳說明文字的清單。"""
    refs = []
    if name == "plants":
        for r in read_csv(PLANTS_CSV)[1]:
            if value in split_ids(r.get("parents")):
                refs.append(f"{r['id']} 的親本")
            if r.get("base") == value:
                refs.append(f"{r['id']} 的選拔來源")
        n = sum(r.get("id") == value for r in read_csv(PHOTOS_CSV)[1])
        if n:
            refs.append(f"{n} 張照片")
        for f, col in (("citations.csv", "plant_id"), ("features.csv", "plant_id")):
            n = sum(r.get(col) == value for r in read_csv(DATA / f)[1])
            if n:
                refs.append(f"{f} 的 {n} 列")
    elif name == "regions":
        n = sum(r.get("region") == value for r in read_csv(PLANTS_CSV)[1])
        if n:
            refs.append(f"{n} 個品種")
    elif name == "sources":
        n = sum(r.get("source_id") == value for r in read_csv(DATA / "citations.csv")[1])
        if n:
            refs.append(f"citations.csv 的 {n} 列")
    return refs


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/edit":
            return self.send_json({"ok": True, "tables": {k: {"key": t["key"], "add": t["add"]} for k, t in TABLES.items()}})
        m = re.match(r"^/api/data/(\w+)$", self.path)
        if m:
            try:
                t = table_of(m.group(1))
                header, rows = read_csv(DATA / t["file"])
                return self.send_json({"header": header, "rows": rows, "key": t["key"], "add": t["add"]})
            except ValueError as e:
                return self.send_json({"error": str(e)}, 404)
        return super().do_GET()

    def do_POST(self):
        # 只接受 JSON：跨站表單無法送出這種請求，其他網站也就無法偷偷改資料
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.send_json({"error": "需要 JSON"}, 415)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BYTES * 2:
                raise ValueError("檔案太大")
            body = json.loads(self.rfile.read(length) or b"{}")
            actions = {"/api/photos/add": self.add, "/api/photos/delete": self.delete,
                       "/api/photos/cover": self.cover, "/api/fetch": self.fetch,
                       "/api/data/save": self.save_row, "/api/data/delete": self.delete_row}
            if self.path not in actions:
                return self.send_json({"error": "not found"}, 404)
            if self.path == "/api/fetch":
                return self.fetch(body)
            with LOCK:
                actions[self.path](body)
        except ValueError as e:
            self.send_json({"error": str(e)}, 400)
        except Conflict as e:
            self.send_json({"error": f"{e}，請重新整理頁面後再改"}, 409)
        except Exception as e:  # noqa: BLE001
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def fetch(self, body):
        """代為下載網址上的圖片（瀏覽器直接抓會被跨站限制擋下），原樣回傳給網頁縮圖。"""
        url = str(body.get("url", "")).strip()
        if not re.match(r"^https?://", url, re.I):
            raise ValueError("網址需以 http:// 或 https:// 開頭")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as res:
            ctype = res.headers.get_content_type()
            data = res.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("圖片超過 25 MB")
        if not ctype.startswith("image/"):
            raise ValueError(f"這個網址不是圖片（{ctype}）。請在圖片上按右鍵「複製圖片網址」")
        self.send_json({"type": ctype, "data": base64.b64encode(data).decode()})

    def add(self, body):
        pid = str(body.get("id", ""))
        if pid not in plant_ids():
            raise ValueError(f"找不到品種 {pid}")
        m = re.match(r"^data:(image/[\w+.-]+);base64,(.+)$", str(body.get("data", "")), re.S)
        if not m or m.group(1) not in EXTS:
            raise ValueError("照片格式不支援")
        data = base64.b64decode(m.group(2))
        if len(data) > MAX_BYTES:
            raise ValueError("圖片超過 25 MB")

        folder = IMAGES / pid
        folder.mkdir(parents=True, exist_ok=True)
        nums = [int(p.stem) for p in folder.iterdir() if p.stem.isdigit()]
        name = f"{max(nums, default=0) + 1:02d}{EXTS[m.group(1)]}"
        (folder / name).write_bytes(data)

        header, rows = read_csv(PHOTOS_CSV)
        row = {k: str(body.get(k, "")).strip() for k in FIELDS}
        row.update(id=pid, src=f"images/{pid}/{name}")
        # 插在同品種最後一張之後，CSV 依品種分組比較好讀
        idx = max((i for i, r in enumerate(rows) if r.get("id") == pid), default=len(rows) - 1) + 1
        rows.insert(idx, row)
        write_photos(header, rows)
        self.send_json({"photos": photos_of(rows, pid), "src": row["src"]})

    def delete(self, body):
        src = str(body.get("src", ""))
        path = image_path(src)
        header, rows = read_csv(PHOTOS_CSV)
        hit = [r for r in rows if r.get("src") == src]
        if not hit:
            raise ValueError("photos.csv 裡沒有這張照片")
        rows = [r for r in rows if r.get("src") != src]
        write_photos(header, rows)
        if path.is_file():
            path.unlink()
        self.send_json({"photos": photos_of(rows, hit[0]["id"])})

    def cover(self, body):
        """把照片移到同品種的第一列（第一張 = 卡片封面）。"""
        src = str(body.get("src", ""))
        header, rows = read_csv(PHOTOS_CSV)
        i = next((i for i, r in enumerate(rows) if r.get("src") == src), None)
        if i is None:
            raise ValueError("photos.csv 裡沒有這張照片")
        row = rows.pop(i)
        first = next((j for j, r in enumerate(rows) if r.get("id") == row["id"]), i)
        rows.insert(first, row)
        write_photos(header, rows)
        self.send_json({"photos": photos_of(rows, row["id"])})


    def save_row(self, body):
        """新增（orig 為 null）或修改一列。只寫入 CSV 既有的欄位，欄位順序不變。"""
        name = str(body.get("table", ""))
        t = table_of(name)
        path = DATA / t["file"]
        header, rows = read_csv(path)
        orig = body.get("orig")
        row = {k: str((body.get("row") or {}).get(k) or "").strip() for k in header}
        if orig is None:
            if not t["add"]:
                raise ValueError(f"{t['file']} 不能在這裡新增")
            index = None
        else:
            index = find_row(rows, header, t["key"], orig)
            if name == "photos" and row.get("src") != rows[index].get("src"):
                raise ValueError("照片路徑不能修改")
        validate(name, row, rows, header, index)
        if index is None:
            rows.append(row)
        else:
            rows[index] = row
        write_csv(path, header, rows)
        self.send_json({"row": row})

    def delete_row(self, body):
        name = str(body.get("table", ""))
        t = table_of(name)
        if not t["add"]:
            raise ValueError(f"{t['file']} 不能在這裡刪除")
        path = DATA / t["file"]
        header, rows = read_csv(path)
        index = find_row(rows, header, t["key"], body.get("orig") or {})
        if t["key"]:
            refs = references(name, rows[index][t["key"]])
            if refs:
                raise ValueError("還有資料用到它，請先處理：" + "、".join(refs))
        rows.pop(index)
        write_csv(path, header, rows)
        self.send_json({"ok": True})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"鹿角蕨圖鑑（可編輯照片與資料）：http://localhost:{port}　Ctrl+C 結束")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
