# 18 原生種特徵調查：guideline v1.2 報告

> 2026-10-14。依 [feature_survey_guideline.md](../feature_survey_guideline.md) v1.2 重算並補查 18 個原生種，結果已遷移到 `data/plants.csv`（`survey_version = v1.2`）。
>
> - 摘要值：[species_v3.csv](species_v3.csv)
> - 每個欄位的摘要值、可信度與各來源標記：`data/features.csv`（網站詳細頁「特徵來源與可信度」讀取這個檔）
> - 原始引用：`data/citations.csv` 中 18 原生種的特徵列，共 477 筆（計入摘要 400、參考 62、排除 15）
> - 查找 5 次仍無摘要的欄位：[search_log.csv](search_log.csv)（90 筆：`not_found` 75、`partial` 15）
> - 產生方式：`python3 project_plan/survey/survey_species.py .`，重跑結果相同

## 一、依 v1.2 規則改變的地方

1. **最低／最高溫只採計建議值。** UF/IFAS 的「Hardy to」「Semi-hardy to」、牛津植物園的「可耐輕霜」、Halling 比較表的「Temp Range」（註腳寫明是耐寒程度）都改為 `reference`，寫進 `temp_note`。因此二叉、銀鹿、巨大的最低溫改由 RHS 決定（13、13、15 °C），圓盾、深綠只剩耐受紀錄，最低溫留空。
2. **難度摘要只用台灣與東南亞來源。** Halling 與 UF/IFAS 的難度改為 `reference`，摘要來自微體溫室（與亞猴的 NParks）。17 種只有一個來源，可信度為「低」。
3. **單一栽培來源也產生摘要**，可信度一律「低」。
4. **欄位遷移**：`shield_color` → `shield_browning`，新增 `shield_fringe`，刪除 `fertile_color`；`shield_vein` 改 `yes`／`no`，`fertile_split` 改範圍，`shield_form`、`spore` 改受控詞彙。6 個有草稿的雜交種，原本的冠形、顏色、孢子囊文字移到 `shield`／`fertile`，`shield_vein` 草稿分數清空。

## 二、這次補查的來源

| 來源 | 等級 | 補到的欄位 |
| --- | --- | --- |
| Australian Tropical Ferns（hillii，新增；bifurcatum、superbum 重讀） | T1 | 深綠的冠形、孢子葉分岔、毛被；二叉的分岔；巨大的盾葉毛被 |
| Halling 各種頁面（andinum、elephantotis、grande、holttumii、madagascariense、superbum、wandae，新增） | T2 | 光照、澆水、濕度；女王的建議溫度 60–100 °F；銀鹿冠形的上半部位置 |
| UF/IFAS ENH36（重讀） | T2 | 安地斯的毛被 |
| Exotica Esoterica（重讀） | T2 | 非猴的澆水；溫度耐受紀錄 |

## 三、覆蓋率與可信度（摘要值非空的品種數）

| 欄位 | v1.1 | v1.2 | 高 | 中 | 低 |
| --- | --- | --- | --- | --- | --- |
| `size`、`shield_vein`、`fertile_posture`、`fertile_length`、`spore`、`pups`、`origin`、`shield_browning`、`shield_fringe` | 18 | 18 | 幾乎全高 | | 4 |
| `fertile_split` | 16 | 18 | 18 | | |
| `shield_form`、`shield_height` | 16 | 17 | 17 | | |
| `fertile_width` | 11 | 11 | 11 | | |
| `fertile_hair` | 6 | 8 | 3 | 5 | |
| `shield_hair` | 0 | 2 | 1 | 1 | |
| `light` | 9 | 18 | 4 | 9 | 5 |
| `water` | 4 | 14 | 2 | 4 | 8 |
| `humidity` | 1 | 10 | 2 | 1 | 7 |
| `min_temp` | 5 | 8 | 1 | | 7 |
| `max_temp` | 0 | 1 | | 1 | |
| `difficulty` | 18 | 18 | 1 | | 17 |
| `dormancy` | 2 | 2 | 2 | | |

## 四、橫向驗證與修正

**引用原文核對。** 重新抓取 39 個來源，逐筆比對 18 種所有引用的 `quote`。專著以外的引用全部對得上原文。專著有 12 筆因 OCR 錯字（如「saral pateh」「symmetrieal」「pronouneed」）無法自動比對，已逐筆人工確認存在。另外核對：
- 微體溫室的難度與日照表：18 種全部與表格位置一致。
- Halling 的五級難度：全部一致。
- Ciarle et al. 2025 的叢生／單生：18 種全部一致。頁碼由「S1 Table」更正為「S1 File, Table S2」。

**修正的衝突**

| 品種 | 欄位 | 處理 | 理由 |
| --- | --- | --- | --- |
| 巨獸、巨大、何其美、蝴蝶、女王 | `shield_fringe` | Halling 的標記改為排除；巨獸、何其美、蝴蝶的可信度由「低」變「高」 | Halling 的 frill 指芽點旁的小皺褶（用來區分女王與何其美），與專著的領片定義不同；Halling 的何其美頁也說 grande 照片有 little frills，與其比較表矛盾 |
| 二叉 | `shield_browning` | Australian Tropical Ferns 改為排除 | 同一頁的檢索表（乾枯成古銅色）與種描述（長期保持綠色）互相矛盾 |
| 二叉 | `fertile_hair` | Australian Tropical Ferns 由 1 改為 `1–3` | 原本只取檢索表的「sparse」；種描述寫上表面稀疏、下表面密生 |
| 象耳 | `shield_browning` | UF/IFAS「冬季盾葉轉褐」改為參考；可信度由「低」變「高」 | 栽培地冬季的季節現象，不是成熟後的老化型態，比照 dormancy「溫帶冬季停滯不算」 |
| 皇冠 | `shield_vein` | 刪除重複的專著引用 | 同一來源同一欄位記了兩筆 |

**補上的來源。** 微體溫室文中逐種的澆水說明（象耳、三角、女王、亞猴、非猴、愛麗絲）原本沒有記錄，已補上。

**沒有出處的文字。** 18 種的 `desc`、`note` 全部重寫，每一句都對到一筆引用（`citations.csv` 的 `field = desc` 38 筆、`note` 3 筆）。刪除的說法包括：
- 與來源矛盾：象耳「唯一孢子葉不分岔」（愛麗絲也可不分裂）、圓盾「葉面光滑亮綠」（Halling 記載兩型）、三角與象耳「熱帶雨林種」（UF/IFAS 寫象耳原生於乾燥森林）。
- 沒有出處：「適合陽台」「收藏者的夢幻種」「公認最難養」「常被拿來做精緻上板」「數量稀少」等。

**仍保留的衝突**（可信度「低」，各來源標記照樣顯示）：

| 品種 | 欄位 | 摘要 | 各來源 |
| --- | --- | --- | --- |
| 象耳 | `water` | 3 | Halling：忌長期潮濕（1）／微體溫室：性喜暖溼（5） |
| 巨獸 | `water` | 3 | NParks：多水、中等（3–5）／UF/IFAS：容易澆太多（1） |
| 非猴 | `light` | 3 | 微體溫室：低弱光（1）／Exotica Esoterica：非常明亮（5） |
| 巨大 | `light` | 3 | 微體溫室：低弱光（1）／RHS：半遮蔭（3）／Halling：喜光強於一般（3–5） |

這幾項是不同地區的栽培建議真的不同，不是換算錯誤，依指引取平均並標「低」。

**品系。** 網站對未調查品系「暫時沿用」base 栽培值的做法維持不變，未來有直接描述該品系的來源時再修正。

## 五、需要注意

1. **網站的溫度篩選幾乎沒有資料。** `max_temp` 只有女王有值，「環境溫度」篩選目前只會留下女王。耐受紀錄都在 `temp_note`，網站仍會顯示。
2. **難度改用台灣來源後變化很大。** 例如女王、何其美由草稿的 3、皇冠由 4 變為 1（微體溫室列為新手）。Halling 與 UF/IFAS 的評等仍顯示在來源列表中。
3. **文字欄都由引用產生。** `shield`、`fertile`、`growth`、`light_note`、`water_note`、`temp_note` 由摘要與來源標記自動產生，`desc`、`note` 由逐句引用組成（見第四節）。
4. **二叉的冠形留空。** 專著寫「erect or appressed」（有變異），澳洲標本館寫「spreading」，都無法單選五型之一。
5. **`dormancy = no` 一律留空。** 沒有任何來源明確寫「不休眠」；圓盾在南加州的冬季休眠依定義排除。
6. **品系的栽培欄位仍沿用 base。** 依決定保留，見第四節。

## 六、依 fyi.csv 補查（2026-10-15）

交種調查時記在 `fyi.csv` 的原生種線索，這次補進 `survey_species.py`（「fyi.csv follow-up」段）。新增來源 `mo-giant`（微體溫室〈巨獸鹿角蕨與巨大鹿角蕨的差異？〉，已存 Wayback）；其他來源（`mo-elephant`、`mo-alcicorne`、`ncsu-bifurcatum`、`hoshizaki-price1990`）是交種調查時加入的。

| 品種 | 欄位 | 原本 | 現在 | 依據 |
| --- | --- | --- | --- | --- |
| superbum | max_temp | 空 | 27（低） | 微體溫室：不建議夏季超過 27 度；「馴化個體可耐 33 度」記為參考 |
| superbum | min_temp | 15（低） | 15（高） | 微體溫室對照表 15~27 度，與 RHS H1A 一致 |
| superbum | water | 1（低） | 1（高） | 微體溫室：水苔接近全乾才給水 |
| superbum | light | 3（低） | 3（中） | 改用微體溫室專文的「中弱光」（1–3） |
| grande | min_temp／max_temp | 16（低）／空 | 17（高）／35（低） | 微體溫室對照表 18~35 度；「原生地 20~35 度」記為參考 |
| grande | water | 3（低） | 2（低） | 微體溫室：長大後耐旱，介質全乾再澆透 |
| grande | origin | 菲律賓（呂宋？、提勞、宿霧、民答那峨） | 菲律賓民答那峨（1908 年另有一份標本記為提勞島） | Hoshizaki & Price 1990 pp. 65–66 更正專著 |
| elephantotis | min_temp | 16（低） | 15（高） | 微體溫室：保持 15 度以上，與 UF/IFAS 60 °F 一致 |
| alcicorne | min_temp／water | 空／空 | 15（低）／1（低） | 微體溫室：保持 15 度以上；耐旱，介質全乾再澆透 |
| bifurcatum | light | 4（中） | 3（中） | NC State Extension：散射光至半遮蔭 |
| bifurcatum | water | 3（中，2 源） | 3（中，3 源） | NC State Extension：根部略乾再澆，不可全乾；「Zone 10 可戶外栽培」記為參考 |

文字欄：
- `note` 新增 grande（野生族群因低地森林砍伐而瀕危）、coronarium（P. platylobum 併入本種）兩句，出自 Hoshizaki & Price 1990。
- `desc` 新增 elephantotis（每年約一對孢子葉）、stemaria（每年 3–5 對）兩句，出自同一篇論文 p. 64。

判定方式：
1. **同一出版者只計一次。** 摘要是逐列平均，所以微體溫室的專文（巨獸／巨大、象耳、圓盾）已涵蓋某欄時，〈40 種鹿角蕨〉表格中同欄的那一列改為 excluded，做法與先前 veitchii 的〈銀鹿〉頁相同。受影響的是 superbum light、grande light、elephantotis water／difficulty。這四欄的摘要值都沒變，只有 superbum light 的可信度由低變中。
2. **grande 的專著原產地改為 excluded。** 較新的 T1（Hoshizaki & Price 1990）明確指出呂宋與宿霧是誤記，所以改用新的說法。如果你希望保留專著的寫法，這一點需要你決定。
3. **superbum 的「台灣夏季生長遲滯、甚至夏眠」記為 excluded。** 這是栽培環境造成的停滯，比照溫帶冬季停滯不算休眠。
4. **沒有採用的 FYI 項目：**
   - willinckii（Halling 首頁）：與已引用的 Halling willinckii 頁同一出版者、同一句話。
   - bifurcatum「濕度太高可能出現黑斑」：沒有建議濕度值。
   - grande「推薦給初學者的大型鹿角蕨之一」：只和其他大型種比較，而且與同一出版者的〈40 種〉表格（中階）不同。
   - elephantotis 老葉皮層的深色細胞層：屬解剖特徵，沒有對應欄位。
   - 交種與名稱類的 FYI 項目（burirom、neptune、horne-surprise、horne-surprise-darwin、ridleyi-x-coronarium）不在這次範圍內。
