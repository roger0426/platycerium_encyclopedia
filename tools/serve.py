#!/usr/bin/env python3
"""本機預覽＋照片編輯伺服器。

取代 `python3 -m http.server`，另外提供照片上傳／刪除 API，網頁偵測到後會在卡片與品種頁顯示照片管理按鈕。
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
LOCK = threading.Lock()  # 同時有兩個請求時，避免 photos.csv 被交錯寫壞
EXTS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_photos(header, rows):
    # 保留原本的欄位順序與 BOM（Excel 開啟才不會亂碼）；有變異株照片時才補 variant 欄
    if any(r.get("variant") for r in rows) and "variant" not in header:
        header = header + ["variant"]
    tmp = PHOTOS_CSV.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(PHOTOS_CSV)


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
            return self.send_json({"ok": True})
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
                       "/api/photos/cover": self.cover, "/api/fetch": self.fetch}
            if self.path not in actions:
                return self.send_json({"error": "not found"}, 404)
            if self.path == "/api/fetch":
                return self.fetch(body)
            with LOCK:
                actions[self.path](body)
        except ValueError as e:
            self.send_json({"error": str(e)}, 400)
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


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"鹿角蕨圖鑑（可編輯照片）：http://localhost:{port}　Ctrl+C 結束")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
