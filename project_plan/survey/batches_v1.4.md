# 特徵調查 v1.4 分批進度

> 依《鹿角蕨特徵調查指引》v1.4 重新調查交種與品系（187 個）。建立：2026-10-19。計畫說明見 `project_plan/plan.md` §4.4。

## 每批的做法

1. **重讀已引用的頁面**：這批品種在 `citations.csv` 已引用的頁面，用 v1.4 的規則重讀一次，把所有欄位（型態與栽培）的說法一次記完，包括 v1.3 記為 `excluded` 的「小型」「中小型」「整株尺寸」「可達 X」（改記為寬鬆說法）。不計入查找次數。
2. **新查找**：每個品種最多 5 次新查找（所有欄位共用），優先找業者商品頁、拍賣頁、玩家部落格、論壇與社團貼文。T4（ビカク図鑑、PlatyWiki、懶人包）只當線索。
3. **寫入**：在 `survey_hybrids.py` 補上該批品種的 block，每個 block 設 `version="v1.4"`、`date=調查日`；寬鬆說法的 `value` 加 `~`。查不到的欄位寫進 `searched`。
4. **執行與檢查**：執行 `survey_species.py` 與 `survey_hybrids.py`，確認不在這批的品種資料沒有變動（`git diff` 只動到這批），再依指引第七節自我檢查。
5. **收尾**：更新本檔的狀態與成果，一批一個 commit。

每批以一次工作階段完成為原則（約 20–30 個品種）；做不完時在「備註」記下停在哪個品種，下次從那裡接續。

## 總覽

| 批次 | 範圍 | 品種數 | 缺尺寸 | 缺型態欄位（格） | 狀態 | 完成日 | 成果 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 銀鹿、二叉、深綠的品系 | 28 | 24 | 378 | 完成 | 2026-10-19 | 尺寸 +4、型態 +39、栽培 +4 |
| B2 | 澳洲群內的交種（銀哇、北猴、雷電…） | 24 | 24 | 323 | 完成 | 2026-10-19 | 尺寸 +4、型態 +27 |
| B3 | 爪哇品系（一） | 24 | 15 | 319 | 完成 | 2026-10-19 | 尺寸 +1、型態 +26 |
| B4 | 爪哇品系（二） | 24 | 14 | 316 | 完成 | 2026-10-19 | 尺寸 +2、型態 +25 |
| B5 | DW 系（月亮、飛馬…）與親本不明的命名個體 | 21 | 19 | 282 | 完成 | 2026-10-19 | 尺寸 +3、型態 +20 |
| B6 | FSQ（捲捲鹿）系 | 18 | 17 | 243 | 完成 | 2026-10-19 | 尺寸 +1、型態 +5 |
| B7 | 非洲、馬達加斯加、象耳、安地斯群的交種與品系 | 24 | 23 | 309 | 完成 | 2026-10-19 | 尺寸 +2、型態 +19 |
| B8 | 亞猴、皇冠群與巨型群 | 24 | 20 | 316 | 完成 | 2026-10-19 | 尺寸 +2、型態 +8 |
| 合計 | | 187 | 156 | 2486 | 完成 | 2026-10-19 | 尺寸 +19、型態 +169、栽培 +4 |

狀態：待辦／進行中／完成。「缺型態欄位」是開始前 14 個型態欄位中空白的格數；「成果」填補上的格數，例如「尺寸 +12、型態 +40、栽培 +8」。

## B1：銀鹿、二叉、深綠的品系（28）

**結果（2026-10-19）：** 重讀已引用頁面得到大部分寬鬆說法；新查找只在英文業者頁找到荷蘭鹿角、檸檬、High Finger 的描述，其餘亞洲品系以英文、日文品名搜尋都沒有專頁。11 個品種沒有新增任何欄位（多半只有名稱或無法換算的形容）。

可能的來源：微體溫室〈銀鹿〉〈深綠〉〈檸檬〉、晴花鹿苑、阿金；日本業者（ビカクシダ＋品名）

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `veitchii-auburn-river` | 奧銀 | 品系 | 14/14 | 4/7 | 尺寸 XL（整株 >150 cm） |
| [x] | `veitchii-ar-1` | 奧銀 AR-1 | 品系 | 14/14 | 7/7 | |
| [x] | `veitchii-akki` | Akki | 品系 | 14/14 | 6/7 | |
| [x] | `veitchii-lemoinei` | 檸檬 | 品系 | 13/14 | 4/7 | 尺寸 M；光照 5 → 4（加入 Josh's Frogs） |
| [x] | `bifurcatum-mt-lewis` | 貓路易士 | 品系 | 14/14 | 7/7 | |
| [x] | `bifurcatum-mt-lewis-thin` | 細葉貓路易士 | 品系 | 14/14 | 7/7 | |
| [x] | `bifurcatum-little-kitty` | 小貓咪 | 品系 | 13/14 | 7/7 | |
| [x] | `bifurcatum-netherlands` | 荷蘭鹿角 | 品系 | 14/14 | 5/7 | 尺寸 L；業者也稱它「較緊湊」，數字優先 |
| [x] | `bifurcatum-white` | 白鹿 | 品系 | 13/14 | 6/7 | |
| [x] | `bifurcatum-popcorn` | 爆米花 | 品系 | 13/14 | 7/7 | |
| [x] | `hillii-mio` | 綴化深綠 | 品系 | 14/14 | 5/7 | |
| [x] | `hillii-wide` | 寬葉深綠 | 品系 | 14/14 | 7/7 | |
| [x] | `hillii-rimklong` | 深綠 Rimklong | 品系 | 14/14 | 7/7 | |
| [x] | `pewchan` | 皮陳 | 品系 | 14/14 | 5/7 | |
| [x] | `white-monkey` | 白猴 | 品系 | 14/14 | 7/7 | |
| [x] | `wild-monkey` | 野猴 | 品系 | 14/14 | 7/7 | |
| [x] | `white-shine` | 白帥帥 | 品系 | 14/14 | 5/7 | |
| [x] | `salmon` | 鮭魚 | 品系 | 14/14 | 7/7 | 「寬葉」與「末端趨細」矛盾，不記裂片寬度 |
| [x] | `veitchii-wild` | 野銀 | 品系 | 13/14 | 5/7 | |
| [x] | `veitchii-high-finger` | 銀鹿 High Finger | 品系 | 14/14 | 7/7 | 晴花鹿苑頁仍不採用 |
| [x] | `veitchii-nyx` | 夜銀 | 品系 | 12/14 | 5/7 | |
| [x] | `hillii-dragon` | 深綠龍 | 品系 | 14/14 | 4/7 | |
| [x] | `hillii-dwarf` | 侏儒深綠 | 品系 | 12/14 | 3/7 | |
| [x] | `hillii-raijin` | 雷神 | 品系 | 14/14 | 7/7 | 「向上放射展開」記 ~spread |
| [x] | `veitchii-no-shield` | 無臉銀 | 品系 | 14/14 | 5/7 | 「類侏儒」改記 ~S |
| [x] | `bifurcatum-dwarf` | 侏儒二叉 | 品系 | 12/14 | 5/7 | |
| [x] | `veitchii-lemoinei-dwarf` | 侏儒檸檬 | 品系 | 11/14 | 5/7 | |
| [x] | `hillii-wave` | 深綠浪 | 品系 | 14/14 | 5/7 | |

## B2：澳洲群內的交種（銀哇、北猴、雷電…）（24）

**結果（2026-10-19）：** 新查找（英文品名）沒有找到已引用頁面以外的描述；成果都來自重讀阿金、晴花鹿苑、竹意軒、Halling 的頁面。We Love Tropical Plants 的商品描述疑似生成文字，不採用。7 個品種沒有新增欄位。

可能的來源：晴花鹿苑、阿金、Jungle Leaves；泰國育種者（Facebook、拍賣）；Halling（Majus、Diversifolium）

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `veitchii-x-willinckii` | 銀哇 | 交種 | 14/14 | 6/7 | |
| [x] | `hillii-x-bifurcatum` | Diversifolium | 交種 | 13/14 | 7/7 | 「可能較大」屬推測，排除 |
| [x] | `dw` | DW | 交種 | 14/14 | 7/7 | |
| [x] | `monkey-north` | 北猴 | 交種 | 14/14 | 5/7 | |
| [x] | `hela` | 海拉 | 交種 | 14/14 | 7/7 | |
| [x] | `snow-moon` | 雪月 | 交種 | 13/14 | 5/7 | 「厚實白毛」照 v1.3 換算記嚴格 5 |
| [x] | `rydeen` | 雷電 | 交種 | 13/14 | 7/7 | |
| [x] | `electrofilia` | P. 'Electrofilia' | 交種 | 14/14 | 7/7 | |
| [x] | `majus` | P. 'Majus' | 交種 | 13/14 | 7/7 | Halling「相當大型」→ ~L |
| [x] | `hillii-x-willinckii` | P. hillii × P. willinckii | 交種 | 13/14 | 7/7 | |
| [x] | `bifurcatum-x-willinckii` | 普哇 | 交種 | 13/14 | 7/7 | |
| [x] | `elsa` | 艾莎 | 交種 | 13/14 | 6/7 | 「孢子葉緊湊」→ ~S |
| [x] | `doi-tung` | 杜藤 | 交種 | 14/14 | 7/7 | |
| [x] | `hakuna-matata` | P. 'Hakuna Matata' | 交種 | 13/14 | 6/7 | |
| [x] | `kiyohime` | 清姬 | 交種 | 13/14 | 6/7 | |
| [x] | `tornado` | 龍捲風 | 交種 | 14/14 | 7/7 | |
| [x] | `et` | P. 'E.T.' | 交種 | 12/14 | 7/7 | |
| [x] | `trident` | 三叉戟 | 交種 | 14/14 | 7/7 | |
| [x] | `wolverine` | 金剛狼 | 交種 | 14/14 | 7/7 | SapphireChild 依親本預期的高冠，排除 |
| [x] | `south-pole-star` | 南極星 | 交種 | 14/14 | 7/7 | |
| [x] | `unicorn` | 獨角獸 | 交種 | 13/14 | 7/7 | |
| [x] | `nemo` | 尼莫 | 交種 | 14/14 | 5/7 | |
| [x] | `cardinals` | 紅雀 | 交種 | 14/14 | 7/7 | |
| [x] | `uncia` | 雪豹 | 交種 | 13/14 | 7/7 | 「中小型」改記 ~M |

## B3：爪哇品系（一）（24）

**結果（2026-10-19）：** 成果來自重讀微體溫室〈侏儒鹿角蕨〉〈月亮系列〉、晴花鹿苑、阿金、竹意軒、商業周刊；英文品名搜尋只有 Orchideeën Shop 的泛用文字。7 個品種沒有新增欄位。

可能的來源：微體溫室〈爪哇〉〈侏儒〉〈月亮系列〉、晴花鹿苑、阿金；日本拍賣與業者

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `willinckii-nano` | Nano | 品系 | 13/14 | 6/7 | |
| [x] | `willinckii-jade-girl` | 玉女 | 品系 | 10/14 | 5/7 | |
| [x] | `willinckii-little-will` | 無臉哇 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-jenny` | 珍妮 | 品系 | 13/14 | 5/7 | 商業周刊「植株有很多側芽」→ ~yes |
| [x] | `willinckii-bacteria` | 細菌 | 品系 | 10/14 | 5/7 | |
| [x] | `willinckii-smurf` | 藍精靈 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-spur` | 爪哇 Spur | 品系 | 13/14 | 6/7 | |
| [x] | `willinckii-masayu` | 爪哇 Masayu | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-celso-tatsuta` | 賽索爾 | 品系 | 14/14 | 5/7 | |
| [x] | `willinckii-hp100` | 短手爪哇 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-wild-cat` | 野貓 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-mr-tin` | 爪哇 Mr. Tin | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-a-plus` | 爪哇 A+ | 品系 | 14/14 | 7/7 | 竹意軒「體型中型」→ ~M |
| [x] | `willinckii-cold-moon` | 冷月 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-albo-anubis` | 白胡狼 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-yellow-moon` | 黃月 | 品系 | 14/14 | 4/7 | |
| [x] | `willinckii-kaguya` | 迦具夜 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-moonlight` | 月光 | 品系 | 14/14 | 4/7 | |
| [x] | `willinckii-blue-queen` | 藍皇后 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-golden-boy` | 金童 | 品系 | 13/14 | 5/7 | |
| [x] | `willinckii-pearl-queen` | 珍珠皇后 | 品系 | 14/14 | 6/7 | |
| [x] | `willinckii-leonids` | 獅子座 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-white-swan` | 白天鵝 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-pedro` | 佩德羅 | 品系 | 14/14 | 7/7 | |

## B4：爪哇品系（二）（24）

**結果（2026-10-19）：** 成果來自重讀晴花鹿苑、阿金、微體溫室〈侏儒鹿角蕨〉與日本拍賣頁；英文品名搜尋沒有結果。The Basements 的描述疑似生成文字，不採用。9 個品種沒有新增欄位（晴花鹿苑 Anne、Bogie 頁沒有文字，半月、白玫瑰頁描述的是孢子苗）。

可能的來源：同 B3；晴花鹿苑命名個體頁

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `willinckii-anapat-9` | Anapat #9 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-sri-pueak` | 水氣 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-nook-dwarf` | 侏儒 Nook | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-kaohom` | Kao Hom | 品系 | 13/14 | 7/7 | |
| [x] | `gabriel` | 加百列 | 品系 | 12/14 | 6/7 | |
| [x] | `willinckii-robin` | 羅賓 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-watchara` | Watchara | 品系 | 13/14 | 7/7 | |
| [x] | `fishbone` | 魚骨 | 品系 | 13/14 | 6/7 | |
| [x] | `aydan` | 艾登 | 品系 | 13/14 | 7/7 | 「小型爪哇系」改記 ~S |
| [x] | `willinckii-omega` | 爪哇 Omega | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-half-moon` | 半月 | 品系 | 14/14 | 5/7 | |
| [x] | `willinckii-silver-phoenix` | 銀鳳凰 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-yellow-moon-dwarf` | 侏儒黃月 | 品系 | 13/14 | 4/7 | |
| [x] | `willinckii-ccs` | 爪哇 CCS | 品系 | 12/14 | 7/7 | |
| [x] | `willinckii-makigumo` | 卷雲 | 品系 | 12/14 | 7/7 | |
| [x] | `willinckii-white-heaven` | 白色天堂 | 品系 | 13/14 | 7/7 | |
| [x] | `willinckii-white-rose` | 白玫瑰 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-yami` | 爪哇 Yami | 品系 | 14/14 | 6/7 | |
| [x] | `sunny-cutie` | 晴天小可愛 | 品系 | 12/14 | 7/7 | |
| [x] | `willinckii-anne` | 爪哇 Anne | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-bogie` | 波奇 | 品系 | 14/14 | 7/7 | |
| [x] | `willinckii-anapat-1` | Anapat 1 | 品系 | 14/14 | 7/7 | 「母本體型偏小」改記 ~S |
| [x] | `willinckii-totoro` | 豆豆龍 | 品系 | 13/14 | 5/7 | |
| [x] | `willinckii-grace` | P. willinckii 'Grace' | 品系 | 13/14 | 7/7 | |

## B5：DW 系（月亮、飛馬…）與親本不明的命名個體（21）

**結果（2026-10-19）：** 成果多來自重讀竹意軒、微體溫室〈月亮系列〉〈飛馬〉、阿金；新查找找到 Vegetal Design〈Pegasus〉與 Paraíso Plant Studio〈Polar Bear〉兩頁（照護欄都是通用文字，不採用）。6 個品種沒有新增欄位。

可能的來源：微體溫室〈月亮系列〉〈飛馬〉、竹意軒；泰國、日本業者

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `white-hawk` | 白霍克 | 品系 | 14/14 | 5/7 | |
| [x] | `omg` | OMG | 品系 | 13/14 | 5/7 | |
| [x] | `pegasus` | 飛馬 | 品系 | 14/14 | 4/7 | |
| [x] | `white-lover` | 白色戀人 | 品系 | 13/14 | 7/7 | |
| [x] | `full-moon` | 滿月 | 品系 | 14/14 | 7/7 | |
| [x] | `blue-moon` | 藍月 | 品系 | 14/14 | 5/7 | |
| [x] | `honey-moon` | 蜜月 | 品系 | 14/14 | 7/7 | |
| [x] | `blue-monkey` | 藍猴 | 品系 | 14/14 | 7/7 | |
| [x] | `paul-vespa` | 保羅偉士牌 | 品系 | 14/14 | 6/7 | |
| [x] | `new-moon` | 新月 | 品系 | 14/14 | 5/7 | |
| [x] | `polar-bear` | 北極熊 | 品系 | 13/14 | 5/7 | 「緊湊型個體」→ ~S |
| [x] | `jynx` | 迷唇姐 | 交種 | 14/14 | 7/7 | 「體型適中」→ ~M |
| [x] | `mountain-rabbit` | 山兔 | 交種 | 13/14 | 7/7 | 「大型」→ ~L |
| [x] | `white-hill` | 白色山丘 | 交種 | 14/14 | 7/7 | |
| [x] | `white-wing` | 白翼 | 交種 | 14/14 | 7/7 | |
| [x] | `mew` | P. 'Mew' | 交種 | 14/14 | 7/7 | |
| [x] | `geisha` | 藝伎 | 交種 | 12/14 | 4/7 | |
| [x] | `snow-white-x-suddan` | 白雪蘇丹 | 交種 | 13/14 | 6/7 | |
| [x] | `bambi` | 斑比 | 交種 | 13/14 | 6/7 | |
| [x] | `stella-aeterni` | 永恆之星 | 交種 | 12/14 | 7/7 | |
| [x] | `tide` | 潮汐 | 交種 | 12/14 | 7/7 | |

## B6：FSQ（捲捲鹿）系（18）

**結果（2026-10-19）：** Wanna 2020–2026 型錄對 FSQ 選拔個體只有品名與價格，10 個命名個體仍沒有型態描述；成果只來自微體溫室〈捲捲鹿〉、晴花鹿苑〈White Gizmo〉與型錄裡 Little Sis 的一句描述。15 個品種沒有新增欄位。

可能的來源：Wanna 型錄與影片、晴花鹿苑、Haruhana USA、微體溫室〈捲捲鹿〉

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `foong-si-qi` | 捲捲鹿 | 交種 | 11/14 | 3/7 | 株徑 60–100 cm 改記 ~80，加「中等體型」→ M |
| [x] | `ss-foong` | 千手觀音 | 交種 | 14/14 | 5/7 | |
| [x] | `fsq` | P. 'FSQ' | 品系 | 14/14 | 7/7 | |
| [x] | `ginka` | 銀華 | 品系 | 12/14 | 5/7 | |
| [x] | `white-gizmo` | P. 'White Gizmo' | 品系 | 13/14 | 7/7 | |
| [x] | `wannasiqi` | P. 'Wannasiqi' | 品系 | 14/14 | 7/7 | |
| [x] | `little-sis` | P. 'Little Sis' | 品系 | 14/14 | 7/7 | |
| [x] | `kin-norn` | P. 'Kin-Norn' | 品系 | 14/14 | 7/7 | |
| [x] | `kin-naree` | P. 'Kin-Naree' | 品系 | 14/14 | 7/7 | |
| [x] | `ivory` | P. 'Ivory' | 品系 | 14/14 | 7/7 | |
| [x] | `green-moon` | P. 'Green Moon' | 品系 | 14/14 | 7/7 | |
| [x] | `cotton-moon` | P. 'Cotton Moon' | 品系 | 14/14 | 7/7 | |
| [x] | `kusuma` | P. 'Kusuma' | 品系 | 14/14 | 7/7 | |
| [x] | `fsq-dwarf` | P. 'FSQ Dwarf' | 品系 | 14/14 | 7/7 | |
| [x] | `oliver-siqi` | P. 'Oliver Siqi' | 品系 | 14/14 | 7/7 | |
| [x] | `thipsiqi` | P. 'Thipsiqi' | 品系 | 14/14 | 7/7 | |
| [x] | `sazanami` | 漣 | 品系 | 13/14 | 7/7 | |
| [x] | `wfsq` | P. 'WFSQ' | 交種 | 12/14 | 6/7 | |

## B7：非洲、馬達加斯加、象耳、安地斯群的交種與品系（24）

**結果（2026-10-19）：** 成果來自重讀 Halling（Callard、Dawboy、Alcicorne × Madagascariense、首頁）、微體溫室〈圓盾〉〈象耳〉、阿金、晴花鹿苑；英文品名搜尋只有 Orchideeën Shop、RHS 的泛用文字。12 個品種沒有新增欄位。另修正 survey_common.py 型態類別平手時結果隨執行變動的問題（改為取先出現的說法）。

可能的來源：Halling 各交種頁、微體溫室〈圓盾〉〈象耳〉、Siam Exotica（Wayback）、阿金

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `elemaria` | Elemaria | 交種 | 7/14 | 6/7 | Hoshizaki & Price 的「可達」尺寸改記 ~70、~≤63 cm |
| [x] | `alcicorne-x-ellisii` | P. alcicorne × P. ellisii | 交種 | 14/14 | 7/7 | |
| [x] | `horne-surprise` | 非非 | 交種 | 11/14 | 5/7 | |
| [x] | `erawan` | 非象 | 交種 | 13/14 | 6/7 | |
| [x] | `budsaba` | 非Q | 交種 | 14/14 | 7/7 | |
| [x] | `neptune` | 三角象 | 交種 | 13/14 | 6/7 | |
| [x] | `antis` | 安象 | 交種 | 13/14 | 6/7 | |
| [x] | `saikeaw` | 安爪 | 交種 | 14/14 | 7/7 | |
| [x] | `siamense` | 象爪 | 交種 | 14/14 | 7/7 | Halling「盾葉巨大」→ 冠高 ~5 |
| [x] | `moose` | 駝鹿 | 交種 | 14/14 | 5/7 | |
| [x] | `burirom` | 愛象 | 交種 | 14/14 | 6/7 | |
| [x] | `alcicorne-x-elephantotis` | 馬圓象 | 交種 | 14/14 | 5/7 | |
| [x] | `andinum-x-stemaria` | P. andinum × P. stemaria | 交種 | 14/14 | 7/7 | |
| [x] | `callard` | P. 'Callard' | 交種 | 14/14 | 6/7 | |
| [x] | `roy-vail` | P. 'Roy Vail' | 交種 | 13/14 | 7/7 | |
| [x] | `dawboy` | P. 'Dawboy' | 交種 | 11/14 | 7/7 | Halling「植株小」→ ~S |
| [x] | `larry-weed` | P. 'Larry Weed' | 交種 | 12/14 | 7/7 | |
| [x] | `alcicorne-africa` | 非圓 | 品系 | 12/14 | 5/7 | |
| [x] | `alcicorne-madagascar` | 馬圓 | 品系 | 13/14 | 5/7 | |
| [x] | `alcicorne-gorgon` | 圓盾 Gorgon | 品系 | 14/14 | 7/7 | |
| [x] | `elephantotis-mammoth` | 猛瑪象 | 品系 | 14/14 | 4/7 | |
| [x] | `alcicorne-madagascar-dwarf` | 侏儒馬圓 | 品系 | 12/14 | 3/7 | |
| [x] | `horne-surprise-darwin` | 達爾文 | 品系 | 13/14 | 7/7 | |
| [x] | `durval-nunes` | P. 'Durval Nunes' | 交種 | 12/14 | 7/7 | |

## B8：亞猴、皇冠群與巨型群（24）

**結果（2026-10-19）：** 成果來自重讀微體溫室〈亞猴〉〈皇冠〉〈象耳〉、阿金、卡呸醬；英文品名搜尋只有種的描述。阿金〈美猴王〉與〈圓葉亞猴〉兩頁文字相同，不採用。17 個品種沒有新增欄位。

可能的來源：微體溫室〈亞猴〉〈皇冠〉、Siam Exotica（Wayback）、Halling（Charles Alford、Joe Young）、阿金

| | id | 名稱 | 類型 | 缺型態 | 缺栽培 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `ridleyi-x-coronarium` | 亞皇 | 交種 | 13/14 | 5/7 | |
| [x] | `coronarium-x-bifurcatum` | P. coronarium × P. bifurcatum | 交種 | 14/14 | 7/7 | |
| [x] | `flamenco` | 佛朗明哥 | 交種 | 12/14 | 6/7 | |
| [x] | `ridleyi-wide` | 寬葉亞猴 | 品系 | 14/14 | 3/7 | |
| [x] | `ridleyi-jade-peony` | 翠玉牡丹 | 品系 | 14/14 | 7/7 | |
| [x] | `ridleyi-dwarf-silver` | 侏儒銀亞猴 | 品系 | 13/14 | 5/7 | |
| [x] | `ridleyi-pakarang` | 珊瑚亞猴 | 品系 | 14/14 | 7/7 | |
| [x] | `ridleyi-monkey-king` | 猴王 | 品系 | 14/14 | 5/7 | |
| [x] | `ridleyi-round` | 圓葉亞猴 | 品系 | 14/14 | 5/7 | |
| [x] | `ridleyi-thin` | 細葉亞猴 | 品系 | 13/14 | 4/7 | |
| [x] | `coronarium-thin` | 細葉皇冠 | 品系 | 14/14 | 7/7 | 微體溫室「大型種」→ ~L |
| [x] | `kitshakood-thin-dwarf` | 侏儒細葉亞皇 | 品系 | 13/14 | 7/7 | |
| [x] | `kitshakood-x-ridleyi` | 皇猴 | 交種 | 12/14 | 7/7 | |
| [x] | `kitshakood-round-frond` | 圓葉亞皇 | 品系 | 14/14 | 6/7 | |
| [x] | `superbum-x-wandae` | P. superbum × P. wandae | 交種 | 14/14 | 7/7 | |
| [x] | `charles-alford` | 阿福 | 交種 | 13/14 | 7/7 | |
| [x] | `joe-young` | 巨猴 | 交種 | 14/14 | 7/7 | |
| [x] | `grande-x-elephantotis` | 巨象 | 交種 | 14/14 | 6/7 | 微體溫室「整體最為巨大」→ ~XL |
| [x] | `holttumii-x-wandae` | 何女 | 交種 | 14/14 | 7/7 | |
| [x] | `holttumii-x-elephantotis` | 何象 | 交種 | 13/14 | 5/7 | |
| [x] | `wandae-x-veitchii` | P. wandae × P. veitchii | 交種 | 14/14 | 6/7 | |
| [x] | `wallichii-x-willinckii` | P. wallichii × P. willinckii | 交種 | 14/14 | 7/7 | |
| [x] | `mentelosii` | P. × mentelosii | 交種 | 5/14 | 7/7 | |
| [x] | `wandae-dwarf` | 侏儒捲葉女王 | 品系 | 13/14 | 7/7 | |
