# 18 原生種特徵調查：guideline v1.0 測試報告

> **已由 [v2 報告](species_v2_report.md) 取代。** 本報告的工作表 species_v1.csv 已移除，引用也已由 v1.1 調查重寫。以下保留作為 v1.0 的測試紀錄。

> 2026-10-14。依 [feature_survey_guideline.md](../feature_survey_guideline.md) v1.0 調查 18 個原生種，目的是檢驗 guideline 能不能用，以及現有草稿值是否可靠。
>
> - 調查結果（已採用的值）：[species_v1.csv](species_v1.csv)。尚未寫入 `data/plants.csv`。
> - 每個值的出處（含未採用的說法）：`data/citations.csv` 中 `plant_id` 為 18 原生種的列，共 352 筆，其中 44 筆標註「未採用」。

## 一、使用的來源

| 來源 | 等級 | 用在 |
| --- | --- | --- |
| Hennipman & Roos 1982 專著（種描述 pp. 77–117） | T1 | 所有型態欄位、`pups`、`origin`，以及光照、濕度的第二來源 |
| Halling 網站：難度表、大型種比較表、各種頁面 | T2 | `difficulty`、溫度（未採用）、佐證型態與習性 |
| 微體溫室〈40 種鹿角蕨一次推薦〉的難度 × 日照表 | T3 | `difficulty`、`light` |
| 微體溫室〈銀鹿鹿角蕨 3 品種〉 | T3 | veitchii 的 `water` |

查過但排除的來源：
- **內容農場兩篇**（benjamintrips.tw、ffovk.com）：把「女王」寫成 *P. superbum*、「猴腦」寫成 *P. holttumii*，依 guideline 判定為 T4 並排除。
- **竹意軒、農業知識入口網、環境資訊中心**：只有全屬通用的建議（例如「最適 20–30 °C」），沒有逐種資訊。
- **Flora of Australia**（ALA Profiles）：動態網頁，抓不到內容。

## 二、覆蓋率

| 欄位 | 有值 | 說明 |
| --- | --- | --- |
| `size`、`size_note`、`shield_vein`、`shield_browning`、`shield_fringe`、`fertile_posture`、`fertile_length`、`spore`、`pups`、`origin`、`difficulty` | 18／18 | |
| `shield_form`、`shield_height` | 16／18 | bifurcatum、veitchii 缺：專著在亞種、變種層級沒寫盾葉上半部是貼伏還是直立 |
| `fertile_split` | 16／18 | bifurcatum、hillii 缺：「2–5 回」是 ssp. bifurcatum 整體的範圍，依規則不套用到兩個變種 |
| `fertile_width` | 11／18 | 專著多半沒描述末端裂片形狀 |
| `light` | 8／18 | 只有微體溫室一家給逐種資料；其餘 10 種缺第二來源 |
| `fertile_hair` | 6／18 | 專著只在 bifurcatum 各亞種描述毛被 |
| `humidity` | 2／18 | ridleyi、coronarium |
| `dormancy` | 1／18 | quadridichotomum |
| `water` | 1／18 | veitchii |
| `shield_hair`、`min_temp`、`max_temp` | 0／18 | 沒有逐種來源；Halling 的溫度只有單一來源，部分還標示未確認 |

**型態欄位可以用專著補齊大半；栽培欄位的來源嚴重不足。**

## 三、現有草稿值的問題

`plants.csv` 現有的 18 種特徵值和調查結果有大量差異（數值欄位已先換算成三級再比較）：

| 欄位 | 可比對 | 不同 |
| --- | --- | --- |
| `shield_vein` | 18 | 11 |
| `fertile_posture` | 18 | 10 |
| `fertile_split` | 16 | 9 |
| `difficulty` | 18 | 8 |
| `size` | 18 | 7 |
| `light` | 8 | 4 |
| `shield_height` | 16 | 4 |
| `fertile_hair` | 6 | 3 |
| `fertile_width` | 11 | 2 |
| `pups` | 18 | 1 |

**明確的錯誤**（T1 原文直接矛盾）：

- **coronarium `pups`**：草稿 `no`。專著寫「growing in clusters」，Halling 也描述根莖分枝長出新株。
- **quadridichotomum `fertile_posture`**：草稿 `up`。專著寫「pendulous (spreading when young)」。
- **madagascariense `fertile_posture`**：草稿 `spread`。專著寫「erect」。
- **andinum、quadridichotomum `spore`**：草稿「末端裂片背面」。兩種的孢子囊群都是沿裂片中段分布、面向植株，專著指出這是辨識這兩種的特徵。
- **elephantotis `spore`**：草稿「葉片下半部背面」。專著寫「situated in the apical part」。
- **elephantotis、ellisii 等 11 種 `shield_vein`**：草稿給 3–4 分。專著寫「veins immersed」，只有 ridleyi、madagascariense 葉脈隆起。

**找不到任何來源支持的草稿值：**

- `dormancy = yes`：andinum、elephantotis、holttumii、wallichii。只有 quadridichotomum 有來源。
- 18 種的 `min_temp`、`max_temp` 全部沒有來源。其中 grande 草稿最低溫 15 °C，但唯一的來源（Halling）寫 40 °F（約 4 °C）。

結論：**現有草稿值不宜直接沿用**，遷移時應以調查結果為準，查不到的欄位留空。

## 四、guideline 運作檢討

### 運作良好

- **`spore`、`shield_browning`、`shield_fringe`、`fertile_posture`、`pups`** 的受控詞彙都能從專著原文直接對應，18 種沒有判定困難。
- **分類階層規則** 有效擋下錯誤套用（例如沒有把 ssp. bifurcatum 的「2–5 回分岔」套用到 hillii）。
- **衝突記錄** 讓被捨棄的說法都留在 `citations.csv`。例如 Halling 比較表寫 grande、holttumii、wallichii 沒有領片，與專著衝突，已依 T1 優先處理並記錄。

### 測試中補充的規則（已寫入 v1.0）

1. **`fertile_width`**：專著很少描述裂片形狀，補上「孢子囊群寬度上限 ≥ 20 cm 推定主裂片 ≥ 20 cm」，6 種因此有值。
2. **栽培欄位的雙來源要求**：改為「2 個來源對該欄位有說法，衝突時依規則取值」。否則來源互相衝突的 8 種難度會全部留空。

### 需要你決定的問題

1. **栽培欄位的雙來源要求太嚴，還是來源太少？** 目前 `light` 只有 8 種有值，`water`、`humidity`、溫度幾乎全空。可選：
   - (a) 維持雙來源，繼續找台灣業者、玩家的逐種資料；
   - (b) 放寬為單一 T2／T3 來源即可，但在網站上標示「單一來源」。
2. **T1 棲地換算光照不可靠。** 8 個有光照第二來源的種中，4 個與台灣來源衝突：hillii、superbum 的棲地含開闊環境，台灣來源卻列為「低弱光」；ridleyi 長在曝曬高枝，台灣列「中光」；stemaria 則反過來。原生地的光照與栽培建議似乎是兩回事。建議**取消「棲地換算光照」這條規則**，濕度換算則保留觀察。
3. **`fertile_split` 取上限會飽和。** 16 種裡有 7 種是 5，而且巨型種用側生裂片計算，看起來比 bifurcatum 還「多分岔」，與直覺不符。可選：
   - (a) 改記範圍（如 `3–7`）；
   - (b) 分成「主分岔次數」與「最多分岔次數」兩欄。
4. **`shield_vein` 三級用不到中間值。** 專著只分埋入／隆起，18 種裡 16 種是 1。建議改成是否隆起的二元欄位（`no`／`yes`），網站「葉脈隆起」篩選照用。
5. **`size` 依標本尺寸偏小。** 專著數據來自標本，例如 coronarium 孢子葉記 50–125 cm，但 Halling 記錄台灣辜嚴倬雲植物保種中心的植株約 12 呎（3.6 m）。可選：
   - (a) 維持只用 T1；
   - (b) 允許 T2 的栽培實測，取較大值。
6. **難度以台灣來源為準。** 8 種與 Halling（美國南加州）不同，差最多的是 coronarium：台灣列「新手」，Halling 列第 4 級。目前依 guideline 採台灣來源。

## 五、下一步建議

1. 你決定上述 6 點後，修訂 guideline 為 v1.1，修改並重跑 [survey_species.py](survey_species.py)（`python3 project_plan/survey/survey_species.py .`，重跑會取代它先前寫入的引用）。
2. 補來源：
   - Flora of Australia：可以補 bifurcatum、hillii、veitchii 的盾葉位置與分岔數，需要換方式抓或手動查。
   - Hoshizaki 1972、《Fern Grower's Manual》：可以補毛被與栽培資料，需取得全文。
   - 台灣業者、玩家的逐種栽培文章：補光照、澆水、濕度、溫度的第二來源。
3. 確認後把 `species_v1.csv` 遷移進 `plants.csv`，同時調整 `js/app.js` 的欄位（`shield_color` → `shield_browning`、刪除 `fertile_color`、新增 `shield_fringe`），以及受控詞彙的中文顯示。
4. 型態文字欄（`shield`、`fertile`、`growth`、`desc`）依新的引用改寫。
