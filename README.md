# 鹿角蕨圖鑑

快速瀏覽鹿角蕨原生種、雜交種、照片與親本關係的靜態網頁。純 HTML/CSS/JS，不需要建置。

## 本機預覽

瀏覽器不允許以 `file://` 讀取 CSV，需要開一個本機伺服器：

```bash
python3 tools/serve.py
# 開啟 http://localhost:8000
```

`tools/serve.py` 除了提供網頁，也讓你直接在網頁上新增／刪除照片（見下方「照片」），以及編輯 CSV 資料（見下方「在網頁上編輯資料」）。只想看不想改，用 `python3 -m http.server 8000` 也可以。

## 修改資料（CSV）

所有資料都在 `data/`，可用 Excel、Numbers、Google 試算表或任何文字編輯器修改。

| 檔案 | 內容 |
| --- | --- |
| `data/plants.csv` | 品種資料，一列一個品種 |
| `data/photos.csv` | 照片，一列一張，同一品種可有多列 |
| `data/regions.csv` | 地區代號、名稱與代表色 |
| `data/sources.csv` | 參考資料，一列一個網頁／文獻（網站目前還沒讀，供之後的引用機制使用） |
| `data/citations.csv` | 引用：哪個品種的哪個說法出自哪個來源 |

### plants.csv 欄位

| 欄位 | 說明 |
| --- | --- |
| `id` | 唯一代號（英文小寫、可用 `-`），也是網址 `#/p/<id>` |
| `type` | `species`（原生種）、`hybrid`（雜交種）或 `cultivar`（品系，見下方說明） |
| `name` | 學名（雜交種寫交配式或栽培品種名，如 `Platycerium 'Elemaria'`；品系寫 `P. willinckii 'Nano'`） |
| `zh` | 原生種：中文名；雜交種、品系：台灣市場俗名（沒有就留空） |
| `en` | 英文名，顯示在副標 |
| `aka` | 別名，多個用 `\|` 分隔 |
| `region` | 對應 `regions.csv` 的 `key` |
| `parents` | 雜交種的親本 `id`，用 `\|` 分隔，例如 `elephantotis\|stemaria`（親本也可以是品系，例如 `veitchii-auburn-river`） |
| `base` | 品系的選拔來源 `id`（一個），可以是原生種、雜交種或另一個品系 |
| `breeder` | 選育者／來源（選填） |
| `confidence` | 資料可信度：`documented` 有文獻、`vendor` 業者・玩家說法、`unknown` 來源待查（原生種留空） |
| `refs` | 參考資料網址，多個用 `\|` 分隔，詳細頁會列在「資料來源」 |
| `origin` / `growth` | 原產地 / 生長習性 |
| `size` | 尺寸：`S` 小型、`M` 中型、`L` 大型、`XL` 巨型 |
| `size_note` | 尺寸依據，例如「Hennipman & Roos 1982 D = 55 cm」 |
| `difficulty` | 栽培難度 1–5（★）；摘要只採計台灣與東南亞來源 |
| `desc` / `note` | 簡介 / 補充說明（選填） |
| `survey_version` | 特徵依哪一版[調查指引](project_plan/feature_survey_guideline.md)調查，例如 `v1.2`；空白表示尚未依指引調查的草稿 |

**盾葉（臉）**

| 欄位 | 說明 |
| --- | --- |
| `shield` | 概述 |
| `shield_form` | 冠形：`appressed`、`erect-wedge`、`erect-lobed`、`erect-multilobed`、`spreading-wedge` |
| `shield_height` | 冠高 1–5（貼伏 → 高聳） |
| `shield_browning` | 成熟盾葉的顏色變化：`withering` 枯褐、`green` 保持綠色、`darkening` 轉深綠 |
| `shield_fringe` | 基部領片：`none` 無、`above-stipe` 只在葉柄上方、`encircling` 環繞葉柄 |
| `shield_vein` | 葉脈是否隆起：`yes` / `no` |
| `shield_hair` | 絨毛 1–5（光滑 → 密毛） |

**孢子葉（手）**

| 欄位 | 說明 |
| --- | --- |
| `fertile` | 概述 |
| `fertile_posture` | 姿態：`up` 直立、`spread` 斜展、`pendant` 下垂，可多選，用 `\|` 分隔 |
| `fertile_length` | 長度（文字），例如「30–60 cm」 |
| `fertile_split` | 分岔次數範圍，例如 `2–3`、`≤5`；不分裂記 `0` |
| `fertile_width` | 葉寬 1–5（細 → 寬） |
| `fertile_hair` | 絨毛 1–5（光滑 → 密毛） |
| `spore` | 孢子囊位置：`tips` 末端裂片、`sinus` 分岔凹處、`medial` 裂片中段、`shell-lobe` 獨立殼狀裂片 |

**栽培**

| 欄位 | 說明 |
| --- | --- |
| `pups` | 會不會長側芽：`yes` 群生型、`no` 單株型 |
| `dormancy` | 是否休眠：`yes` / `no` |
| `light` / `light_note` | 光照需求 1–5（☀）/ 說明 |
| `water` / `water_note` | 澆水量 1–5（💧）/ 說明 |
| `humidity` | 空氣濕度需求 1–5 |
| `min_temp` / `max_temp` | 建議栽培的最低／最高溫度（°C）；「可耐 X 度」這類耐受紀錄只寫進 `temp_note` |
| `temp_note` | 溫度說明 |

分數欄位留空會顯示「未知」。分數是品種之間的相對比較，不是絕對量測值。

依指引調查過的品種（`survey_version` 有值），每個特徵的摘要值、可信度（高／中／低）與各來源的標記記在 `data/features.csv`，由 `project_plan/survey/survey_species.py` 產生，詳細頁的「特徵來源與可信度」會顯示這些內容。原始引用在 `data/citations.csv`，來源在 `data/sources.csv`。

### 首頁的特徵篩選與排序

- **環境溫度**（特徵篩選面板最上方）：用雙頭拉桿設定你種植環境的冬季最低溫與夏季最高溫，只顯示 `min_temp ≤ 最低溫` 且 `max_temp ≥ 最高溫` 的品種；也可點「台灣平地」等預設值。預設值定義在 `js/app.js` 的 `ENV_PRESETS`。
- **特徵篩選**（搜尋列旁的按鈕）：尺寸、栽培難度、孢子葉姿態、繁殖方式、光照需求、外觀特徵。同一組可複選（符合任一即可），「外觀特徵」則須全部符合。篩選條件與門檻定義在 `js/app.js` 的 `FEATURE_GROUPS`。
- **排序**：可依名稱、尺寸、難度、光照、澆水、濕度、最低溫度、盾葉／孢子葉各項分數、照片數量排序，並切換方向。值未知的品種一律排在最後。排序選項定義在 `js/app.js` 的 `SORTS`。
- 詳細頁的「上一個／下一個」會沿用目前的篩選與排序。
- **比較**：卡片右上角的 ＋ 或詳細頁的「加入比較」可選最多 6 個品種，圖鑑底部會出現比較列；篩選結果只剩 2–6 個時，結果列會出現「比較這 n 個」。比較頁網址是 `#/compare/id1,id2,…`，可直接分享。比較頁可「只顯示差異」、顯示各欄位可信度、設定基準（其他品種標出 ▲▼ 高低）、一鍵加入雜交種的親本或品系的選拔來源。比較的列定義在 `js/app.js` 的 `CMP_GROUPS`。

卡片標題會去掉「鹿角蕨」只留名字（例如「女王」）；只剩一個字時保留「鹿角」避免歧義（「銀鹿角」、「大鹿角」）。
雜交種的標題會自動組成「俗名（A × B）」，A、B 是親本的短名；沒有俗名時只顯示「A × B」。
每張卡片和詳細頁標題旁都有 Google 按鈕，會用小視窗開啟該品種學名的搜尋結果（瀏覽器擋彈出視窗時改開新分頁）。
親本本身也可以是雜交種，例如 `parents` 填 `elemaria|alcicorne`，會顯示成「Elemaria × 麋角」；沒有俗名的雜交親本會加括號展開成「(希爾 × 二叉) × 銀鹿」。

「雜交後代」區塊會根據 `parents` 自動產生，不需另外填寫。

### 品系（cultivar）

品系是「從某個原生種或雜交種選出來的個體或產地型」，例如爪哇的 Nano、DW 交種選出的白霍克、奧銀。「侏儒」是性狀不是分類，用 `size = S` 表示，再用特徵篩選的「小型」找出來。

- `base` 指向選拔來源；來源頁會自動出現「品系」區塊，關係圖以虛線連接、節點為膠囊形。
- 品系沒填的**栽培欄位**（地區、難度、光照、澆水、濕度、溫度、側芽、休眠）會沿用 `base` 的資料，詳細頁會標示「暫時沿用」。形態欄位（盾葉、孢子葉）不沿用。
- **孢子苗不另外建檔。** 只有組培（TC）或分株的苗跟原株基因相同；孢子苗是後代，性狀可能跑掉，請在 `photos.csv` 的 `caption` 註明（例如「Nano 孢子苗，約 2 年」）。
- 同一個交配組合若有多個命名選拔，建一筆雜交種，再把各選拔建成 `base` 指向它的品系（例如 `dw` 底下的白霍克、OMG、滿月）。

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

**在網頁上管理照片**：以 `python3 tools/serve.py` 啟動時，每張卡片右上角和品種頁照片下方會出現相機按鈕，可以：

- 新增：把照片拖曳進去、在 FB／Google 圖片上按右鍵「複製圖片」後按 ⌘V／Ctrl+V 貼上、選擇檔案，或貼上圖片網址（由本機伺服器代為下載）
- 刪除（照片檔會一併刪除）、設為封面

照片會自動縮到長邊 1600px、轉成 JPEG，存成 `images/<id>/NN.jpg` 並寫入 `photos.csv`。改完記得 commit。部署到 GitHub Pages 等靜態主機時沒有這個伺服器，按鈕不會出現。

目前的照片都下載自 Wikimedia Commons（皆為 CC 授權或公眾領域）。使用 CC BY / BY-SA 照片時必須保留作者、授權與出處，請勿刪除這三個欄位。

### 參考資料（sources.csv / citations.csv）

網站目前只讀 `plants.csv` 的 `refs` 欄。這兩個檔案記錄更細的出處，供之後做引用（cite）用。新增品種時，請把每個說法（親本、選育者、別名…）各記一列 citation，`refs` 則列出該品種用到的來源網址。特徵欄位的調查方式與判定規則見 [project_plan/feature_survey_guideline.md](project_plan/feature_survey_guideline.md)。

**sources.csv**：一列一個來源

| 欄位 | 說明 |
| --- | --- |
| `id` | 來源代號，例如 `haruhana-ginka`、`sf-hybrid-db` |
| `title` / `publisher` | 頁面標題 / 網站或出版者 |
| `url` | 原始網址 |
| `archive_url` | 存檔網址（原網址失效時使用，例如 Wayback Machine） |
| `type` | `vendor` 商品頁、`article` 文章・新聞、`database` 彙整資料庫、`reference` 學術文獻 |
| `lang` | 語言，例如 `zh-TW`、`en`、`ja` |
| `published` / `accessed` | 發布日期（不知道就留空）/ 查閱日期 |
| `reliability` | `primary` 育種者・命名者自述、`secondary` 業者・媒體、`aggregator` 二手彙整 |
| `tier` | 來源等級 `T1`–`T4`（定義見調查指引） |
| `region` | 資料或經驗所在地區，例如 `台灣`、`美國`、`新加坡`；學術文獻填 `學術` |
| `short` | 顯示用簡稱，例如 `NParks`、`微體溫室` |
| `note` | 備註，例如「頁面未寫親本」 |

**citations.csv**：一列一個說法

| 欄位 | 說明 |
| --- | --- |
| `plant_id` | 對應 `plants.csv` 的 `id` |
| `source_id` | 對應 `sources.csv` 的 `id` |
| `field` | 這個來源佐證什麼：特徵欄位直接用 `plants.csv` 的欄位名；其他用 `exists` 名稱存在、`name` 名稱對應、`parents` 親本、`base` 選拔來源、`breeder` 選育者、`origin` 由來、`aka` 別名、`note` 其他 |
| `value` | 換算後的值，例如 `5`、`pendant`、`3–5`（特徵欄位必填） |
| `label` | 來源的原始標記（簡短中文），網站顯示「地區 來源：標記」時使用 |
| `use` | `summary` 計入摘要值、`reference` 只供參考（如原生地棲地）、`excluded` 依規則排除 |
| `claim` | 用中文摘述來源的說法與換算過程 |
| `quote` | 原文摘錄（選填，簡短即可） |
| `page` | 書籍、論文的頁碼或圖號，例如 `p. 94` |

### 在網頁上編輯資料

以 `python3 tools/serve.py` 啟動時會多出這些按鈕（部署到靜態主機時不會出現）：

- **頂欄「資料表」**：瀏覽、搜尋 `plants`、`regions`、`sources`、`citations`、`photos` 五個 CSV，點一列就能編輯，也可以新增、刪除或「複製成新的一列」。
- **品種頁「編輯資料」**：直接開這個品種的表單，欄位依上方說明分組，受控詞彙用下拉選單。**「引用」**會打開這個品種在 `citations.csv` 的引用，新增時自動帶入品種。
- **列表「＋ 新增品種」**：建立新品種，存檔後會直接跳到它的頁面。

存檔時伺服器會檢查：

- 代號（`id`／`key`）不能重複、只能用英文小寫、數字與 `-`，**建立後不能在網頁上改**（照片資料夾、親本、引用都會用到它，請直接改 CSV）。
- `region`、`parents`、`base`、`plant_id`、`source_id` 指到的資料必須存在。
- 刪除前若還有其他資料用到它（親本、選拔來源、照片、引用、地區…），會列出來並拒絕刪除。
- 表單打開後，如果同一列被 Excel 或其他程式改過，會拒絕覆蓋，請重新整理後再改。

寫入時保留原本的欄位順序與 BOM，只改動那一列。`features.csv` 由 `project_plan/survey/survey_species.py` 產生，不開放在網頁上改；已依指引調查的品種（`survey_version` 有值），重新執行調查腳本會覆蓋 `plants.csv` 的特徵欄位，表單上會提醒。照片的新增、刪除請用「管理照片」，資料表裡的 `photos` 只能改說明、作者、授權等文字欄位。改完記得 commit。

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
