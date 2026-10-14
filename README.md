# 鹿角蕨圖鑑

快速瀏覽鹿角蕨原生種、雜交種、照片與親本關係的靜態網頁。純 HTML/CSS/JS，不需要建置。

## 本機預覽

瀏覽器不允許以 `file://` 讀取 CSV，需要開一個本機伺服器：

```bash
python3 -m http.server 8000
# 開啟 http://localhost:8000
```

## 修改資料（CSV）

所有資料都在 `data/`，可用 Excel、Numbers、Google 試算表或任何文字編輯器修改。

| 檔案 | 內容 |
| --- | --- |
| `data/plants.csv` | 品種資料，一列一個品種 |
| `data/photos.csv` | 照片，一列一張，同一品種可有多列 |
| `data/regions.csv` | 地區代號、名稱與代表色 |

### plants.csv 欄位

| 欄位 | 說明 |
| --- | --- |
| `id` | 唯一代號（英文小寫、可用 `-`），也是網址 `#/p/<id>` |
| `type` | `species`（原生種）或 `hybrid`（雜交種） |
| `name` | 學名（雜交種寫交配式或栽培品種名，如 `Platycerium 'Elemaria'`） |
| `zh` | 原生種：中文名；雜交種：俗名（沒有就留空） |
| `en` | 英文名，顯示在副標 |
| `aka` | 別名，多個用 `\|` 分隔 |
| `region` | 對應 `regions.csv` 的 `key` |
| `parents` | 雜交種的親本 `id`，用 `\|` 分隔，例如 `elephantotis\|stemaria` |
| `origin` / `growth` | 原產地 / 生長習性 |
| `size` | 尺寸：`S` 小型、`M` 中型、`L` 大型、`XL` 巨型 |
| `size_note` | 尺寸說明，例如「成株寬約 40–90 cm」 |
| `difficulty` | 栽培難度 1–5（★） |
| `desc` / `note` | 簡介 / 補充說明（選填） |

**盾葉（臉）**

| 欄位 | 說明 |
| --- | --- |
| `shield` | 概述 |
| `shield_form` | 冠形（文字） |
| `shield_height` | 冠高 1–5（貼伏 → 高聳） |
| `shield_color` | 顏色（文字） |
| `shield_vein` | 脈紋 1–5（平滑 → 隆起） |
| `shield_hair` | 絨毛 1–5（光滑 → 密毛） |

**孢子葉（手）**

| 欄位 | 說明 |
| --- | --- |
| `fertile` | 概述 |
| `fertile_posture` | 姿態：`up` 直立、`spread` 斜展、`pendant` 下垂，可多選，用 `\|` 分隔 |
| `fertile_length` | 長度（文字），例如「30–60 cm」 |
| `fertile_split` | 分岔 0–5（0 = 不分岔，5 = 多回分岔） |
| `fertile_width` | 葉寬 1–5（細 → 寬） |
| `fertile_color` | 顏色（文字） |
| `fertile_hair` | 絨毛 1–5（光滑 → 密毛） |
| `spore` | 孢子囊位置（文字） |

**栽培**

| 欄位 | 說明 |
| --- | --- |
| `pups` | 會不會長側芽：`yes` 群生型、`no` 單株型 |
| `dormancy` | 是否休眠：`yes` / `no` |
| `light` / `light_note` | 光照需求 1–5（☀）/ 說明 |
| `water` / `water_note` | 澆水量 1–5（💧）/ 說明 |
| `humidity` | 空氣濕度需求 1–5 |
| `min_temp` / `max_temp` | 可耐受的最低／最高溫度（°C，數字，估計值） |
| `temp_note` | 溫度說明 |

分數欄位留空會顯示「未知」。分數是品種之間的相對比較，不是絕對量測值。

### 首頁的特徵篩選與排序

- **環境溫度**（特徵篩選面板最上方）：用雙頭拉桿設定你種植環境的冬季最低溫與夏季最高溫，只顯示 `min_temp ≤ 最低溫` 且 `max_temp ≥ 最高溫` 的品種；也可點「台灣平地」等預設值。預設值定義在 `js/app.js` 的 `ENV_PRESETS`。
- **特徵篩選**（搜尋列旁的按鈕）：尺寸、栽培難度、孢子葉姿態、繁殖方式、光照需求、外觀特徵。同一組可複選（符合任一即可），「外觀特徵」則須全部符合。篩選條件與門檻定義在 `js/app.js` 的 `FEATURE_GROUPS`。
- **排序**：可依名稱、尺寸、難度、光照、澆水、濕度、最低溫度、盾葉／孢子葉各項分數、照片數量排序，並切換方向。值未知的品種一律排在最後。排序選項定義在 `js/app.js` 的 `SORTS`。
- 詳細頁的「上一個／下一個」會沿用目前的篩選與排序。

卡片標題會去掉「鹿角蕨」只留名字（例如「女王」）；只剩一個字時保留「鹿角」避免歧義（「銀鹿角」、「大鹿角」）。
雜交種的標題會自動組成「俗名（A × B）」，A、B 是親本的短名；沒有俗名時只顯示「A × B」。
每張卡片和詳細頁標題旁都有 Google 按鈕，會用小視窗開啟該品種學名的搜尋結果（瀏覽器擋彈出視窗時改開新分頁）。
親本本身也可以是雜交種，例如 `parents` 填 `elemaria|alcicorne`，會顯示成「Elemaria × 麋角」；沒有俗名的雜交親本會加括號展開成「(希爾 × 二叉) × 銀鹿」。

「雜交後代」區塊會根據 `parents` 自動產生，不需另外填寫。

### 照片（photos.csv）

| 欄位 | 說明 |
| --- | --- |
| `id` | 對應 plants.csv 的 `id` |
| `src` | 照片路徑，例如 `images/grande/01.jpg` |
| `caption` | 說明文字 |
| `credit` | 作者 |
| `license` | 授權，例如 `CC BY-SA 4.0` |
| `source` | 原始出處網址，作者名稱會連到這裡 |

第一張會當作卡片封面；沒有照片的品種會自動顯示佔位圖。建議照片長邊縮到 1600px 以內。

目前的照片都下載自 Wikimedia Commons（皆為 CC 授權或公眾領域）。使用 CC BY / BY-SA 照片時必須保留作者、授權與出處，請勿刪除這三個欄位。

### 用 Excel 編輯的注意事項

存檔時請選 **「CSV UTF-8（逗號分隔）」**，否則中文會變成亂碼。

## 部署

整個資料夾都是靜態檔案，可直接放到 GitHub Pages、Netlify、Cloudflare Pages 等服務。

## 檔案結構

```
index.html
css/style.css
js/app.js        # CSV 解析、路由、畫面
data/*.csv       # 資料
images/<id>/     # 照片
```
