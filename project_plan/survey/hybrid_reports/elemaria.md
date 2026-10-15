# elemaria（P. × elemaria）特徵調查：guideline v1.2

> 2026-10-15。產生方式：`python3 project_plan/survey/survey_hybrids.py .`（`BLOCKS["elemaria"]`）。

## 1. 分類與親本查證

- **原始發表（T1）**：Hoshizaki & Price 1990, *Amer. Fern J.* 80(2): 61–64，nothosp. nov.。模式標本採自加州帕薩迪納 Tropical Gardens Nursery 的栽培植株（Hoshizaki 88-6, LA），同時命名栽培品種 cv. Sanchez。作者「依外形」認為親本是 **elephantotis × stemaria**，並寫明無法確定它源於栽培還是野外。
- **POWO（T2）**：人工雜交種，elephantotis × stemaria（沿用原始發表）。
- **Halling（T2）**：交種表與 Elemaria 頁都寫 **andinum × elephantotis**，並註明「經 DNA 檢測確認」，但沒有給出處。
- **PalmTalk 論壇（T3）**：轉述 Fernando Orellana 2018 年的電子郵件：Dan Yansura 的基因檢測顯示其中一個親本與 P. andinum 一致，**尚未發表**。我找不到任何已發表的 DNA 研究。
- **處理方式**：`parents` 維持現值 `andinum|elephantotis`，四個說法都記進 citations（`field = parents`），`note` 用有出處的句子說明兩種說法。舊 note 中「安象（Antis）、三角象（Neptune）分別對應這兩種說法」沒有出處，已刪除。

## 2. 來源

| 來源 | 等級 | 地區 | 用途 |
| --- | --- | --- | --- |
| Hoshizaki & Price 1990（archive.org 上的 BHL 掃描 OCR，pp. 61–64） | T1 | 學術 | 型態、origin、desc、note、parents |
| POWO | T2 | 英國 | note、parents |
| Halling：Elemaria.htm | T2 | 美國 | fertile_hair、water、desc |
| Halling：hybrid_index.htm | T2 | 美國 | note、parents |
| PalmTalk 論壇討論串（2025-11-13） | T3 | 美國 | note；parents（reference） |

5 個都是新來源（`data/sources.csv`）。Halling 兩頁已存到 Wayback；POWO 與 PalmTalk 存檔失敗（HTTP 520），`archive_url` 留空。AFJ 的 `url` 指向 archive.org 上的掃描本。

## 3. 摘要值與可信度

| 欄位 | 摘要 | 可信度 | 依據 |
| --- | --- | --- | --- |
| shield_vein | yes | 高 | T1「somewhat prominent main veins」 |
| shield_fringe | above-stipe | 高 | T1「Bud covered above by a ruffle of base frond tissue」 |
| fertile_split | 0 | 高 | T1「absence of any defined forking」，先端最多 9 個不規則鈍裂片 |
| fertile_width | 5 | 高 | 孢子葉不分裂 → 5 |
| fertile_hair | 1 | 中 | Halling：上表面有蠟質（下表面未知） |
| spore | tips | 高 | T1：散生於葉片上部三分之一 |
| pups | yes | 高 | T1：可由根芽（pups）繁殖 |
| origin | 美國加州帕薩迪納的苗圃中發現；不確定源於栽培或野外 | 高 | T1 |
| water | 1 | 低 | Halling：最常見的問題是澆水過多而腐爛（單一來源） |

**和舊草稿相比被清空的欄位**：size（L）、difficulty（2）、shield_height（3）、shield_hair（1）、fertile_posture（spread\|pendant）、fertile_length（50–80 cm）、dormancy（no）、light（4）、humidity（3）、min_temp（15）、max_temp（35），以及 light_note、temp_note。T1 的尺寸只寫「to 70 × 30 cm」「to 63 × 53 cm」，屬於上限，依規則排除。
**改變的欄位**：fertile_split 1 → 0；water 3 → 1；origin「人工雜交」→ T1 的說法；新增 shield_vein、shield_fringe、spore；shield、fertile、growth、water_note、desc、note 全部改寫為有引用的句子，`survey_version = v1.2`。值相同的有：fertile_width 5、fertile_hair 1、pups yes。

## 4. 記入 search_log

size（partial）、fertile_length（partial）、shield_form、shield_height、shield_hair、shield_browning、fertile_posture、dormancy、light、humidity、min_temp、max_temp、difficulty（not_found），共 13 筆。

## 5. FYI（`project_plan/survey/fyi.csv`，8 筆）

- mentelosii：Hoshizaki & Price 1990 說它由 Hoshizaki 1975 發表，親本是 stemaria × superbum。
- elephantotis／stemaria：同文 p. 64 記錄了加州栽培下每年長出的孢子葉對數（1／3–5 對）和側絲直徑。
- grande：同文 p. 65 起有〈Notes on Platycerium grande〉，可用來補查 T1。
- coronarium：同文討論它的分類位置與孢子葉片。
- horne-surprise：PalmTalk 說它在南加州可以戶外栽培（只是耐受紀錄）。
- burirom：Halling 交種表把 ellisii × elephantotis 列為「No name yet」。
- neptune：Halling 交種表把 'Luaentii' 列為 elephantotis × stemaria。

## 6. 腳本修改與驗證

- 新增 `survey_common.py`：從 survey_species.py 抽出摘要與可信度規則（`summarize`、`feature_rows`）、文字欄產生（`plant_text`）、CSV 讀寫，以及 `replace_rows`（把自己負責的列在原位置替換；第一次執行時接在檔尾）。
- `survey_species.py`：改為 import 共用模組。citations、features.csv、search_log.csv 都只在原位置替換 18 個原生種的列，不再覆寫整個檔案。
- 新增 `survey_hybrids.py`：每個品種一個 `BLOCKS[...]` 區塊，包含 cites、desc、note、text 覆寫、extra（例如 parents，依「品種＋來源＋欄位」比對，別的來源的列會保留）、searched。新來源加在 `SOURCES`。
- 驗證：
  - 重構後只跑 species，輸出與備份逐位元相同。
  - species → hybrids 與 hybrids → species 兩種順序的結果相同；從備份重新開始、用反向順序跑，結果也相同。
  - 和備份相比，除了 elemaria 與 5 個新來源，citations、features、plants、photos、regions、search_log、sources 其他列全部相同。

## 7. 需要使用者決定

1. **parents**：已發表的 T1 與 POWO 是 elephantotis × stemaria；andinum 的說法只有 Halling（未給出處）和論壇轉述的未發表檢測。目前維持 `andinum|elephantotis`。要不要改回 `elephantotis|stemaria`？
2. **water = 1**：Halling 同一頁也寫「Nothing has been reported on the watering」。目前把「最常見的問題是澆太多而腐爛」視為 easily over-watered，記為 summary。如果認為兩句矛盾，可以改為 excluded，water 就會留空。
3. **shield_fringe = above-stipe**：T1 只寫芽點上方有盾葉組織的皺褶，對應到專著的「葉柄上方的領片」是我的判斷。
4. **fertile_hair = 1**：只依 Halling 說上表面有蠟質；T1 寫孢子葉是灰綠色，沒有描述毛被。
