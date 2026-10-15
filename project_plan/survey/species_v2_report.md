# 18 原生種特徵調查：guideline v1.1 測試報告

> 2026-10-14。依 [feature_survey_guideline.md](../feature_survey_guideline.md) v1.1 重做 18 個原生種的調查，取代 [v1 報告](species_v1_report.md)。
>
> - 摘要值：[species_v2.csv](species_v2.csv)
> - 每個欄位的摘要值、可信度與各來源標記：[species_v2_detail.csv](species_v2_detail.csv)
> - 原始引用：`data/citations.csv` 中 18 原生種的特徵列，共 433 筆（計入摘要 399、參考 19、排除 15）
> - 產生方式：`python3 project_plan/survey/survey_species.py .`，重跑結果相同

## 一、這一版改了什麼

1. **來源不限台灣，以機構與研究為主。** 新增 12 個來源：
   - **研究**：Ciarle et al. 2025（PLoS ONE）、台大劉純安 2019 碩論
   - **標本館**：Australian Tropical Ferns and Lycophytes（澳洲熱帶標本館）
   - **植物園與政府、大學園藝單位**：NParks（新加坡）、RHS（英國）、UF/IFAS（美國佛州大學）、牛津植物園
   - **專業雜誌**：Exotica Esoterica
   - **科普**：《博物一分鐘》
2. **每個來源的標記都保留**，並標明地區與來源。例如 `species_v2_detail.csv` 的皇冠難度：「美國 Halling：第 4 級（有點難）／台灣 微體溫室：新手」。
3. **光照只採計照護建議。** 原生地棲地改為「參考」，在來源列表中標「（參考）」，不計入摘要。
4. **`fertile_split` 記範圍**，`shield_vein` 改為是否隆起，`size` 改以各來源中點平均。
5. **摘要值取平均，並標可信度**（高／中／低）。栽培欄位仍需 2 個獨立照護來源才產生摘要值；只有一個來源時，該來源的標記照樣顯示，但不產生摘要值。

## 二、覆蓋率與可信度

| 欄位 | v1 | v1.1 | 高 | 中 | 低 |
| --- | --- | --- | --- | --- | --- |
| `size`、`shield_vein`、`fertile_posture`、`fertile_length`、`spore`、`pups`、`origin` | 18 | 18 | 幾乎全高 | | |
| `shield_browning` | 18 | 18 | 17 | | 1 |
| `shield_fringe` | 18 | 18 | 15 | | 3 |
| `shield_form`、`shield_height`、`fertile_split` | 16 | 16 | 16 | | |
| `fertile_width` | 11 | 11 | 11 | | |
| `fertile_hair` | 6 | 6 | 4 | 2 | |
| `difficulty` | 18 | 18 | 8 | 6 | 4 |
| `light` | 8 | 9 | 3 | 5 | 1 |
| `min_temp` | 0 | 5 | 1 | | 4 |
| `water` | 1 | 4 | 1 | 2 | 1 |
| `dormancy` | 1 | 2 | 2 | | |
| `humidity` | 2 | 1 | | 1 | |
| `max_temp`、`shield_hair` | 0 | 0 | | | |

**可信度「低」的 14 項：**

| 品種 | 欄位 | 摘要 | 原因 |
| --- | --- | --- | --- |
| 二叉、銀鹿、巨大 | `min_temp` | 4、6、4 °C | RHS 耐寒等級（英國，10–15 °C 或 > 15 °C）與 UF/IFAS（佛州，約 −1 °C）相差 11 °C 以上 |
| 巨獸 | `min_temp` | 10 °C | UF/IFAS 15.6 °C、Halling 4.4 °C |
| 皇冠 | `difficulty` | 3 | Halling 第 4 級、微體溫室「新手」 |
| 巨獸、巨大 | `difficulty` | 3 | Halling 第 2 級、UF/IFAS「難」 |
| 女王 | `difficulty` | 2 | Halling 第 2 級、微體溫室「新手」、UF/IFAS「難」 |
| 巨獸 | `water` | 3 | NParks「多水、中等」、UF/IFAS「容易澆太多」 |
| 非猴 | `light` | 3 | 微體溫室「低弱光」、Exotica Esoterica「非常明亮」 |
| 象耳 | `shield_browning` | 保持綠色 | 專著寫保持綠色；UF/IFAS 寫佛州冬季會轉褐 |
| 巨獸、何其美、蝴蝶 | `shield_fringe` | 有領片 | 專著有描述；Halling 的比較表寫沒有 |

## 三、觀察

1. **型態欄位已經穩定。** 16 個型態欄位中，多數 18 種都是高可信度，`pups` 也有專著與 Ciarle et al. 2025 兩個研究來源互相印證。
2. **難度在不同地區差異大。** 18 種只有 8 種三個來源一致。巨型種在美國（UF/IFAS）列為「難」，在台灣列為「新手／中階」，反映氣候差異。這正是保留各來源標記的價值：網站可以同時顯示「台灣：新手／美國：難」。
3. **RHS 的耐寒等級偏保守。** RHS 等級是英國溫室栽培的建議（H1B = 需 10–15 °C），UF/IFAS 則是佛州戶外的實際耐受（約 −1 °C）。兩者的平均值（約 4–6 °C）在兩邊都不成立。
4. **栽培來源仍然稀少。** 機構來源主要集中在常見種（二叉、銀鹿、巨大、皇冠、亞猴、巨獸）；冷門種（何其美、蝴蝶、愛麗絲、四叉、安地斯）幾乎只有 Halling 與微體溫室。
5. **NParks 的巨獸頁面疑似誤植。** 它列的盾葉與孢子囊群尺寸和專著裡何其美的數字完全相同，已排除，沒有計入尺寸。

## 四、需要你決定的事

1. **最低溫的來源要不要分「建議」與「耐受」兩種？** 是否把 `min_temp` 拆成「建議最低溫」（RHS 這類溫室建議）與「可耐受最低溫」（UF/IFAS、牛津植物園這類耐寒紀錄）兩欄，或只保留其中一種。不拆的話，平均值會像現在這樣兩邊都不準。
2. **難度要不要依地區分開？** 保留各來源標記之外，網站是否還需要一個總摘要。如果網站主要給台灣讀者，可以考慮只用台灣與東南亞來源算摘要，其他地區的標記只顯示。
3. **單一來源的栽培資料要不要在篩選中使用？** 目前光照有 9 種只有一個來源，因此沒有摘要值，篩選「喜強光」時不會出現這些種。

## 五、下一步

1. 依你對第四節的決定，修訂 guideline 為 v1.2。
2. 繼續補冷門種的栽培來源，優先找原產地機構：
   - 泰國：詩麗吉王后植物園、泰國國家公園局標本館
   - 馬達加斯加：Kew Madagascar Conservation Centre
   - 非洲：Kew、各國植物園
   - 中國：西雙版納熱帶植物園
3. 補 Hoshizaki 1972（JSTOR）與《Fern Grower's Manual》，可以補毛被與栽培資料。
4. 確認後遷移到 `plants.csv`，並在網站詳細頁顯示各來源標記與可信度。
