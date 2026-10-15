# 鹿角蕨特徵調查指引 v1.3

> 適用：`data/plants.csv` 的型態與栽培欄位，以及所有蒐集、整理這些欄位的人（包括 AI 助手）。
> 版本：v1.3（2026-10-15）。修訂時更新版本號並記在文末「修訂紀錄」。

本指引規定四件事：每個特徵欄位的**定義與值域**、可接受的**來源**、**如何記錄每個來源的標記**，以及**如何從多個來源算出摘要值與可信度**。依本指引調查的結果先寫入 `project_plan/survey/`，驗證後再遷移到 `data/plants.csv`（網站目前仍使用舊欄位，見第四節末的遷移對照）。

## 一、原則

1. **每個值都要有出處。** 沒有出處的值不得寫入。找不到來源就留空，網站顯示「未知」。
2. **保留每個來源的標記。** 同一個欄位有多個來源時，每個來源的說法都記錄下來，並標明來源與地區，例如「難度：台灣 微體溫室：入門／美國 Halling：中高」。網站另外顯示一個依規則算出的**摘要值**與**可信度**。
3. **「否」也是一個值。** `pups = no`、`dormancy = no` 和其他值一樣需要來源；沒找到證據時應留空，不能填 `no`。
4. **依規則換算，不憑印象。** 分數與受控詞彙依第四節的規則，從來源原文換算；換算過程寫進引用。
5. **型態以學術文獻為準，沒有學術或機構來源時才用業者、玩家的資料；栽培以「建議照護條件」為準。** 栽培欄位不限國別，以植物園、研究機構、政府與大學的園藝推廣單位、專業栽培者為主，並涵蓋原產地（東南亞、澳洲、非洲、馬達加斯加、南美）的資料。原生地的棲地描述只當參考，不計入摘要值。
6. **交種與品系不從親本推論。** 只記錄直接描述該交種或品系的來源。
7. **限制查找深度。** 每個品種的每個欄位最多查找 5 次，找不到就記錄查過的範圍、標記「尚未找到資料」，先跳過（見第六節）。

## 二、來源

### 分級

| 等級 | 類型 | 例子 |
| --- | --- | --- |
| T1 | 學術：專著、植物誌、期刊論文、學位論文的實驗結果、標本館的鑑定資料 | Hennipman & Roos 1982；Ciarle et al. 2025（PLoS ONE）；劉純安 2019（台大碩論）；Australian Tropical Ferns and Lycophytes |
| T2 | 機構與專家：植物園、政府園藝單位、大學推廣出版品、專家網站與專業雜誌 | NParks Flora & Fauna Web；RHS；UF/IFAS（EDIS）；牛津植物園；Halling；Exotica Esoterica |
| T3 | 業者、玩家、科普媒體 | 微體溫室、晴花鹿苑、Rainforest Flora、國外苗圃商品頁 |
| T4 | 二手彙整、AI 生成內容、內容農場 | ビカク図鑑、staghornfern.org、各式懶人包 |

`sources.csv` 記錄每個來源的 `tier`（T1–T4）、`region`（經驗或資料所在地區，例如 台灣、美國、新加坡；學術文獻填「學術」）與 `short`（顯示用的簡稱）。

**T4 只能當線索。** 看到 T4 的說法時，追到它引用的原始來源，引用原始來源；追不到就不採用。

**判定為內容農場、一律不用的特徵：**學名與中文名錯配（例如把「女王」寫成 *P. superbum*）、作者自稱權威卻沒有可查證的經歷、全文只有通用建議而沒有逐種資訊、同一網站大量發布各種主題的「全攻略」。

**只講整個屬的通用建議**（例如「鹿角蕨適溫 20–30 °C」）不能當成任何一個種的來源。

### 獨立性

不同作者或單位才算獨立來源。同一單位的多個頁面（例如 UF/IFAS 的 EDIS 出版品與 Gardening Solutions 網頁、Halling 的不同頁面）算一個來源。

## 三、每個來源怎麼記

每個來源對某欄位的說法，在 `citations.csv` 記一筆：

| 欄位 | 填法 |
| --- | --- |
| `plant_id` | 品種 id |
| `source_id` | 來源 id（先在 `sources.csv` 建立） |
| `field` | `plants.csv` 的欄位名（本指引的名稱），例如 `light`、`fertile_split` |
| `value` | 換算成本指引值域的值。來源給範圍時記範圍，例如 `3–5`、`10–15` |
| `label` | 來源的原始標記，簡短中文，例如「入門」「中高」「半日照、全日照」「H1B」。網站顯示各來源標記時用這個欄位 |
| `use` | `summary`：計入摘要值；`reference`：只供參考（如原生地棲地）；`excluded`：依規則排除（如套用上階分類的數值、來源標示未確認、疑似誤植） |
| `claim` | 中文摘述與換算過程 |
| `quote` | 原文摘錄，短句即可 |
| `page` | 書籍、論文的頁碼或圖號 |

## 四、欄位定義

### 共通判定規則

- **範圍取值。** 來源寫「25–85 cm」記為範圍；括號內的極端值（如「(20-)25–85(-100)」的 20 與 100）不採計。「約 X」視為 X。尺寸、溫度等測量值寫「可達 X」「up to X」時屬極端值，記錄但 `use = excluded`；分岔次數寫「up to X」時記為 `≤X`。
- **以成熟植株為準。** 型態欄位描述成熟植株；來源描述幼株、小苗的型態記為 `excluded`。栽培欄位可採用小苗的實驗結果，但要在 `label` 註明「小苗」。
- **分類階層。** 專著把 willinckii、veitchii、hillii 處理為 *P. bifurcatum* 的亞種或變種。下階分類優先引用下階分類本身的描述。上階描述中的**定性特徵**，若描述為全體共通（如「growing in clusters」），可套用到下階分類；上階的**數值範圍**或寫明有變異者（如「erect or appressed」「2–5 times forked」）不可套用，記錄為 `excluded`。
- **來源自己標示「未確認」的數據**記為 `excluded`。

### 尺寸

**`size`**：植株尺寸等級。每個來源取「盾葉長、盾葉寬、孢子葉長」各範圍的**中點**，三者中最大者為該來源的 *D*；摘要取各來源 *D* 的平均。

| 值 | *D* 平均 |
| --- | --- |
| `S` | ≤ 30 cm |
| `M` | 31–80 cm |
| `L` | 81–110 cm |
| `XL` | > 110 cm |

**侏儒品系。** 來源明確稱某品系為侏儒（侏儒、dwarf、mini、迷你）時，該來源的 `size` 記為 `S`，`label` 寫原文說法，不必有尺寸數字。只要有一個 `use = summary` 的侏儒說法，摘要值就是 `S`；同一品種另有來源算出的 *D* 不在 S 範圍時，可信度為「低」。只寫「小型」「嬌小」而沒有說侏儒的，不算侏儒說法。整株的高度、寬度或株徑不是 *D* 的組成，記為 `excluded`。

不另設 `XS`。理由：侏儒品系少有尺寸數字，微體溫室寫侏儒成熟植株「大多只有 15~30 公分」，已落在 S 的範圍內；原生小型種（如 madagascariense，*D* = 22.5 cm）也在 S，再細分沒有足夠的來源支撐。

**`size_note`**：列出各來源的 *D* 與依據數值；侏儒說法列出原文標記。

### 盾葉（臉）

**`shield_form`**：盾葉上半部的型式，依專著特徵 12、13 的五型，單選。來源只描述形狀、沒寫上半部是貼伏或直立時，需另一個來源補上位置。

| 值 | 定義 | 專著列舉的種 |
| --- | --- | --- |
| `appressed` | 上半部貼伏，圓形至腎形，全緣或淺裂 | alcicorne、ellisii、madagascariense、ridleyi、bifurcatum（部分） |
| `erect-wedge` | 上半部直立，楔形，全緣或分成兩個主裂片 | elephantotis、quadridichotomum、stemaria、andinum |
| `erect-lobed` | 上半部直立，橢圓形，有多個不等長裂片 | coronarium、bifurcatum（部分） |
| `erect-multilobed` | 上半部直立，楔形，有多個上揚、形狀不一的裂片 | wallichii |
| `spreading-wedge` | 上半部向外展開，楔形，有多個等長裂片 | grande、holttumii、superbum、wandae |

**`shield_height`**：盾葉冠高。1 = 上半部貼伏；3 = 直立或展開、盾葉長度上限 < 80 cm；5 = 直立或展開、盾葉長度上限 ≥ 80 cm。

**`shield_vein`**：盾葉葉脈是否隆起（專著特徵 8）。`yes` = veins prominent（含 waffle 網紋）；`no` = veins immersed。

**`shield_hair`**：盾葉星狀毛，判定方式同 `fertile_hair`。

**`shield_browning`**：成熟盾葉的顏色變化（專著特徵 9）。`withering` = 成熟後不久即枯褐；`green` = 保持綠色直到新盾葉長出；`darkening` = 轉為深綠（madagascariense）。

**`shield_fringe`**：盾葉基部的皺褶狀領片（專著特徵 15）。`none` = 無或不明顯；`above-stipe` = 只在孢子葉柄上方；`encircling` = 環繞孢子葉柄。

### 孢子葉（手）

**`fertile_posture`**：孢子葉姿態，可多選。erect → `up`；spreading → `spread`；pendulous → `pendant`。主葉展開、側生裂片下垂時記 `spread|pendant`。幼葉才有的姿態不採計。

**`fertile_length`**：孢子葉長度範圍，單位 cm，例如 `25–85 cm`。

**`fertile_split`**：孢子葉分岔次數，**記範圍**，例如 `2–3`；不分裂記 `0`；「entire or once lobed」記 `0–1`。巨型種以側生裂片（lateral appendages）的分岔次數計。

**`fertile_width`**：孢子葉裂片寬度。判定順序：(1) 來源描述了末端裂片形狀 → 線形、狹三角形、狹長形記 1，橢圓形、倒卵形、匙形記 3；(2) 孢子葉不分裂 → 5；(3) 孢子囊群寬度上限 ≥ 20 cm（孢子囊群長在裂片上，裂片至少同寬）→ 5。以上都不適用時留空；孢子囊群的形狀不能代替裂片形狀。

**`fertile_hair`**／**`shield_hair`**：星狀毛覆蓋程度。1 = 稀疏，以綠色為主或有蠟質（sparsely、nearly no hairs、waxy）；3 = 明顯有毛但看得出底色（densely set with hairs）；5 = 毛被濃密，呈銀白（very densely、covered with white hair）。

**`spore`**：孢子囊群位置（專著特徵 19、20）。`tips` = 末端裂片或葉片上部；`sinus` = 分岔凹處或其周圍；`medial` = 沿裂片中段、面向植株；`shell-lobe` = 獨立、有柄的殼狀或腎形孢子葉片。

### 生長習性

**`pups`**：是否叢生。growing in clusters、colonial、pups well → `yes`；growing solitary、not in clusters、does not pup → `no`。

**`dormancy`**：是否有固定休眠期。`yes`：來源記錄原生地有固定乾季休眠（落葉、捲葉、停止生長），或栽培來源指出會固定進入休眠。只在溫帶冬季停滯（例如南加州溫室紀錄）不算。

**`origin`**：原產地，依 T1 的分布記錄。交種與品系記錄育成或選拔的來源（例如某園區的孢子苗），沒有 T1、T2 時可用 T3。

### 栽培

栽培欄位只採計**建議照護條件**。原生地的棲地描述記為 `reference`。

**`light`**：光照需求，1–5。

| 來源用語 | 值 |
| --- | --- |
| full sun、requires a lot of light、very bright；中強光（夏季遮陰 30%）、全日照 | 5 |
| semi-shade、partial shade、bright filtered／indirect light；中光（夏季遮陰 50%）、半日照 | 3 |
| low light、shade；低弱光（夏季遮陰 70%）、耐陰 | 1 |

同時列兩種（如「Semi-Shade, Full Sun」）記範圍 `3–5`。

**`water`**：澆水需求，1–5。

| 來源用語 | 值 |
| --- | --- |
| drying between waterings、easily over-watered、keep on the dry side、drought tolerant；耐旱 | 1 |
| moderate water、乾濕交替 | 3 |
| frequent watering、lots of water、keep evenly moist | 5 |

**`humidity`**：空氣濕度需求，1–5。

| 來源用語 | 值 |
| --- | --- |
| tolerates dry air | 1 |
| moderate humidity、occasional misting | 3 |
| high humidity、mist daily、needs a humid environment | 5 |

**`min_temp`**／**`max_temp`**：**建議最低／最高溫**，°C，指來源建議栽培時不要低於（高於）的溫度。華氏換算到小數一位。

| 來源說法 | 處理 |
| --- | --- |
| 建議值：「keep above X」「not below X」「low of X」「tender below X」「最低 X」；RHS 耐寒等級（H1A → 15、H1B → `10–15`、H1C → `5–10`、H2 → `1–5`、H3 → `-5–1`）；研究中植株正常、再低一級就受害的溫度 | `use = summary` |
| 耐受紀錄：「hardy to X for short periods」「semi-hardy to X」「tolerates light frost」「can withstand X」 | `use = reference`，顯示但不計入摘要 |
| 「最適溫度」「生長適溫」 | 不是建議最低／最高溫，不填入 |

只有耐受紀錄、沒有建議值時，摘要留空；耐受紀錄寫進 `temp_note`。

**`difficulty`**：栽培難度，1–5。摘要值只採計**台灣與東南亞**（`region` 為台灣、新加坡、馬來西亞、泰國、印尼、菲律賓、越南等）的來源；其他地區的評等記為 `use = reference`，照樣顯示。來源的評等換算：

| 來源評等 | 值 |
| --- | --- |
| easy、easiest；新手、入門；Halling 第 1、2 級 | 1 |
| moderately difficult、maintenance moderate；中階；Halling 第 3 級 | 3 |
| difficult、more difficult；進階；Halling 第 4、5 級 | 5 |

### 文字欄

`shield`、`fertile`、`growth`、`light_note`、`water_note`、`temp_note`、`desc`、`note` 為中文說明，每一句事實陳述都要能對到一筆引用。

## 五、摘要值與可信度

### 摘要值

| 欄位類型 | 欄位 | 摘要值 |
| --- | --- | --- |
| 數值、分數 | `size`（*D*）、`shield_height`、`shield_hair`、`fertile_hair`、`fertile_width`、`light`、`water`、`humidity`、`difficulty`、`min_temp`、`max_temp` | 所有 `use = summary` 來源的**平均**（範圍取中點）。分數四捨五入到整數，剛好 .5 時往 3 靠攏；溫度四捨五入到整數，剛好 .5 時取較保守者（最低溫往上、最高溫往下） |
| 型態類別 | `shield_form`、`shield_vein`、`shield_browning`、`shield_fringe`、`fertile_posture`、`spore`、`pups` | T1 的值；沒有 T1 時取多數 |
| 範圍、文字 | `fertile_length`、`fertile_split`、`origin` | 最高等級來源的第一個值（T1 優先），不混合不同來源 |
| 尺寸 | `size` | 有侏儒說法時為 `S`；否則依 *D* 平均（見第四節） |

**型態欄位依來源等級取值（v1.3）。** 有 T1 或 T2 時，只用 T1、T2 的說法計算摘要；T3 的說法照常記錄、顯示，但不計入。只有 T3 時，用 T3 的說法計算摘要，可信度一律為「低」。T4 永遠不計入。
| 栽培類別 | `dormancy` | 多數；平手時留空 |

**產生摘要值的最低要求：**
- 型態欄位：1 個 T1、T2 或 T3（依上述等級取值）；只有 T3 時可信度一律為「低」。
- 栽培欄位：1 個照護來源（T1–T3）即可；只有一個來源時可信度一律為「低」。

### 可信度

| 可信度 | 條件 |
| --- | --- |
| 高 | 型態：有 T1 且沒有衝突。栽培：2 個以上獨立來源，值都相同；溫度相差 ≤ 3 °C |
| 中 | 型態：只有 T2（沒有 T1），或來源分數相差 2 以內。栽培：2 個以上獨立來源，分數相差 2（一級）以內；溫度相差 ≤ 8 °C |
| 低 | 型態欄位只有 T3 來源；栽培欄位只有一個來源；來源分數相差超過 2；類別值不一致；溫度相差 > 8 °C；侏儒說法與實測 *D* 不一致 |

### 網站呈現

- 每個來源的標記都附上來源等級，格式為「地區 簡稱（Tx）：標記」，例如「台灣 微體溫室（T3）：中光」。
- `features.csv` 的 `tiers` 欄列出計入摘要的來源等級（例如 `T1|T3`）。
- 品種頁的特徵卡片在 hover（觸控時點按）顯示：摘要可信度、依據的來源等級，以及各來源的標記。「特徵來源與可信度」區塊的可信度標籤也標出來源等級。

### 與現行 `plants.csv` 的遷移對照

| 現行欄位 | 本指引 | 變更 |
| --- | --- | --- |
| `shield_height`、`shield_hair`、`fertile_hair`、`fertile_width`、`light`、`water`、`humidity`、`difficulty` | 同名 | 定義改為本指引；仍為 1–5 |
| `shield_vein` | 同名 | 改為 `yes`／`no` |
| `fertile_split` | 同名 | 改為範圍 |
| `shield_form`、`spore` | 同名 | 文字改為受控詞彙，原文字描述移到 `shield`／`fertile` |
| `size` | 同名 | 改以 *D* 平均判定 |
| `shield_color` | `shield_browning` | 改名並改定義 |
| `fertile_color` | 刪除 | 有特殊顏色時寫進 `fertile` |
| — | `shield_fringe` | 新增 |
| — | 每個特徵的可信度 | 新增（儲存方式於遷移時決定） |
| — | `survey_version` | 新增，見下節 |

### 標記指引版本：`survey_version`

`plants.csv` 的 `survey_version` 欄記錄該品種的特徵是依哪一版指引調查的，例如 `v1.2`。空白表示尚未依指引調查（目前的草稿值）。一個品種只要有任何特徵依新版指引重新調查，就更新此欄；指引改版後，舊版本的品種不必立刻重做，可依此欄找出需要更新的品種。

## 六、調查流程

1. **確認分類地位。** 到 POWO 查學名、異名與分布。T1 採用不同分類處理時，在 `note` 註明，並依「分類階層」規則取值。
2. **型態：查 T1。** 依序查 Hennipman & Roos 1982 的種描述（pp. 79–117）與檢索表（pp. 77–78）、地區植物誌與標本館資料（如 Australian Tropical Ferns and Lycophytes）、期刊論文。逐欄換算並記錄頁碼。交種與品系通常沒有 T1、T2，就記錄業者、玩家的型態說法（T3），包括「侏儒」的說法。
3. **栽培：查 T2 機構來源。** 植物園與政府、大學的園藝單位（NParks、RHS、UF/IFAS、各國植物園）、研究論文的實驗結果，以及專家網站與雜誌。優先找原產地的機構。
4. **栽培：補 T3。** 業者、玩家的逐種經驗，包括台灣來源。
5. **記錄每個來源的標記**，再依第五節算摘要值與可信度。
6. **自我檢查**（第七節）後，才遷移到 `data/plants.csv`，並填寫 `survey_version`。

### 查找次數上限

每個品種的每個欄位，**最多查找 5 次**。一次「查找」指一次搜尋查詢，或打開一個候選來源頁面確認內容。5 次內找不到合格來源時：

1. 停止查找，該欄摘要留空；
2. 在 `project_plan/survey/search_log.csv` 記一筆，標記為「尚未找到資料」；
3. 之後有餘力時，從紀錄的範圍之外繼續找。

`search_log.csv` 欄位：

| 欄位 | 填法 |
| --- | --- |
| `plant_id` | 品種 id |
| `field` | 欄位名 |
| `guideline_version` | 查找時依據的指引版本 |
| `date` | 查找日期 |
| `searched` | 查過的範圍：搜尋關鍵字與看過的網站、文獻，用 `\|` 分隔 |
| `status` | `not_found` 尚未找到資料；`partial` 只找到被排除或參考用的資料 |

屬層級的通用資料（例如整個屬的適溫）在多個品種間共用，只需查找一次，不重複計入每個品種的次數。

工具：
- 用 `crawl4ai`（`crwl` 指令或 Python API）抓網頁存成 markdown。
- 擋爬蟲的頁面可改用搜尋摘要取得原文，但要在 `claim` 註明。
- 專著與論文 PDF 用 `pypdf` 抽文字；PubMed Central 論文可用 Europe PMC 的 full text XML。
- 引用網頁後到 Wayback Machine 存檔，網址填進 `sources.csv` 的 `archive_url`。

## 七、完成檢查清單

- [ ] 每個非空摘要值都有對應 `field`、`use = summary` 的引用
- [ ] 每個來源的說法都有 `value` 與 `label`，包括被排除與只供參考者
- [ ] 只有一個栽培來源的摘要值，可信度標為「低」
- [ ] 只靠 T3 的型態摘要值，可信度標為「低」；有 T1、T2 時，T3 沒有計入型態摘要
- [ ] 來源稱為侏儒的品系，`size` 有一筆 `S` 的引用
- [ ] 最低溫、最高溫的摘要只用建議值；耐受紀錄標為 `reference`
- [ ] 難度摘要只用台灣與東南亞來源
- [ ] 查找 5 次仍找不到的欄位，已記入 `search_log.csv`
- [ ] 已遷移的品種填了 `survey_version`
- [ ] 沒有任何值只靠 T4，也沒有用屬層級的通用建議
- [ ] 棲地描述都標為 `reference`
- [ ] 下階分類沒有套用上階的數值範圍
- [ ] 可信度依第五節判定

## 附錄 A：專著術語對照

| 英文 | 中文 | 說明 |
| --- | --- | --- |
| base frond | 盾葉（臉） | 不與根莖關節相連、宿存、不育的葉 |
| foliage frond | 孢子葉（手） | 與根莖關節相連、會脫落、通常可育的葉 |
| upper part／lower part | 盾葉上半部／下半部 | 上半部決定冠形；下半部貼附在附著物上 |
| appressed／erect／spreading | 貼伏／直立／展開 | |
| pendulous | 下垂 | |
| withering | 枯褐 | 盾葉成熟後不久變褐 |
| fringe（frill、collar） | 領片 | 盾葉基部的膜質皺褶 |
| veins immersed／prominent | 葉脈埋入／隆起 | |
| waffle-pattern | 鬆餅狀網紋 | madagascariense 盾葉的格狀隆起 |
| dichotomously forked | 二叉分岔 | 「3 times forked」= 分岔 3 次 |
| sinus | 分岔凹處 | 兩個裂片之間的凹口 |
| lateral appendages | 側生裂片 | 巨型種孢子囊群兩側二次延長的裂片 |
| soral patch | 孢子囊群（斑塊） | |
| stellate hair | 星狀毛 | |
| growing in clusters／solitary | 叢生／單生 | 對應 `pups` |

## 參考文獻

| 文獻 | 等級 | 狀態 |
| --- | --- | --- |
| Hennipman, E. & Roos, M.C. (1982). *A monograph of the fern genus Platycerium (Polypodiaceae)*. Verh. Kon. Ned. Akad. Wetensch., Afd. Natuurk., Tweede Reeks 80: 1–126. [KNAW PDF](https://dwc.knaw.nl/DL/publications/PU00011522.pdf) | T1 | 已取得 |
| Ciarle, de Bock, Burns & Dececchi (2025). Evolutionary origins and life-history correlates of coloniality in the epiphytic fern genus *Platycerium*. *PLoS ONE* 20: e0329099. [PMC12316288](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12316288/) | T1 | 已取得；補充表有 18 種的叢生／單生 |
| 劉純安 (2019)。環境因子與室內維管對女王鹿角蕨光合作用及生長之影響。國立臺灣大學園藝暨景觀學系碩士論文。[TDR](https://tdr.lib.ntu.edu.tw/handle/123456789/74704) | T1 | 已取得摘要 |
| Australian Tropical Ferns and Lycophytes（[Lucidcentral](https://apps.lucidcentral.org/ferns/)） | T1 | 已取得 bifurcatum、hillii、veitchii、superbum |
| Hoshizaki, B.J. (1972). Morphology and phylogeny of *Platycerium* species. *Biotropica* 4(2): 93–117. | T1 | 未取得全文 |
| Kreier, H.-P. & Schneider, H. (2006). *Am. J. Bot.* 93(2): 217–225. | T1 | 親緣關係用 |
| Flora of Australia（ALA Profiles）；Flora Malesiana | T1 | 尚未抓到內容 |
| Brown, S.P. (2007). *Staghorn Ferns at a Glance*（ENH36）. UF/IFAS Extension. | T2 | 已取得；11 種的難度、溫度、光照、濕度、澆水 |
| NParks Flora & Fauna Web（新加坡國家公園局） | T2 | 已取得 coronarium、ridleyi、bifurcatum、grande |
| RHS Plants（英國皇家園藝學會） | T2 | 已取得 bifurcatum、veitchii、superbum 的耐寒等級與光照 |
| Oxford Botanic Garden, *Plants 400*：Platycerium | T2 | 已取得 |
| Halling, *Hobbyist's Guide to Identifying Platyceriums* | T2 | 已取得 |
| Exotica Esoterica：*Platycerium madagascariense* | T2 | 已取得 |
| Hoshizaki, B.J. & Moran, R.C. (2001). *Fern Grower's Manual*. Timber Press. | T2 | 未取得 |
| 微體溫室〈40 種鹿角蕨一次推薦〉 | T3 | 已取得 |

## 修訂紀錄

| 版本 | 日期 | 內容 |
| --- | --- | --- |
| v1.0 | 2026-10-14 | 初版：欄位定義、來源分級、引用格式 |
| v1.1 | 2026-10-14 | 栽培來源不限台灣，以機構與研究為主；保留每個來源的標記（`label`、`use`）並新增摘要值與可信度規則；光照只採計照護建議，棲地改為參考；`fertile_split` 改記範圍；`shield_vein` 改為是否隆起；`size` 改以各來源中點平均；取消「台灣來源優先」 |
| v1.3 | 2026-10-15 | 型態欄位沒有 T1、T2 時可用 T3 產生摘要，可信度一律為低；侏儒說法視為 `size = S`，不另設 `XS`；每個來源標記附上來源等級（Tx），`features.csv` 新增 `tiers` 欄，網站 hover 顯示可信度與來源等級 |
| v1.2 | 2026-10-14 | 最低／最高溫改為建議值，耐受紀錄只供參考；難度摘要只用台灣與東南亞來源；栽培欄位單一來源也產生摘要，可信度標為低；每欄最多查找 5 次，找不到記入 `search_log.csv`；`plants.csv` 新增 `survey_version` |
