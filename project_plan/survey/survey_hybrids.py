"""Feature survey of hybrids and cultivars, guideline v1.3 (v1.4 batches at the end) — one block per plant.

Rules shared with survey_species.py live in survey_common.py (summary values, confidence, text columns).
Guideline §1.6: hybrids and cultivars are never inferred from their parents; every statement below describes the plant itself.

Each round adds one block to BLOCKS (and its new sources to SOURCES). For every plant in BLOCKS this script replaces only:
  data/citations.csv                   the plant's feature rows, desc / note rows, and the block's own rows of other fields
                                       (`extra`, e.g. parents: matched by plant + source + field; other sources' rows are kept)
  data/features.csv                    the plant's rows
  project_plan/survey/search_log.csv   the plant's rows
  data/plants.csv                      the plant's feature columns, text columns, refs, survey_version
                                       (name, parents, base, breeder, aka, region, confidence … are left as they are)
and adds or updates its sources in data/sources.csv. Rows of every other plant are left untouched, and rows are
replaced in place, so the order of running survey_species.py and this script does not matter.
usage: python3 project_plan/survey/survey_hybrids.py . [--adopt | --force]  (manual edits: see survey_common.flush)
"""
import os, sys
from collections import defaultdict

from survey_common import flush, FIELDS, VERSION, CH, SH, FH, LH, rw, write, replace_rows, source_meta, feature_rows, plant_text

ROOT = sys.argv[1]
HB = "https://halling.com/Platyceriums/"
HALLING = "Halling — Hobbyist's Guide to Identifying Platyceriums"

# id, title, publisher, url, archive_url, type, lang, published, accessed, reliability, tier, region, short, note
SOURCES = [
    # ---- elemaria (2026-10-15)
    ("hoshizaki-price1990", "Platycerium update", "Hoshizaki, B.J. & Price, M.G.；American Fern Journal 80(2): 53–69",
     "https://archive.org/details/mobot31753002743844", "", "reference", "en", "1990", "2026-10-15", "primary",
     "T1", "學術", "Hoshizaki & Price 1990", "pp. 61–64 發表 P. × elemaria 與 cv. Sanchez；全文取自 archive.org 的 BHL 掃描（v.79–80 合訂本）OCR"),
    ("powo-elemaria", "Platycerium × elemaria Hoshiz. & M.G.Price", "Plants of the World Online（Royal Botanic Gardens, Kew）",
     "https://powo.science.kew.org/taxon/17531060-1", "", "database", "en", "", "2026-10-15", "secondary",
     "T2", "英國", "POWO", "Wayback 存檔失敗（HTTP 520）"),
    ("halling-elemaria", "Platycerium elemaria", HALLING, HB + "Elemaria.htm",
     "https://web.archive.org/web/20261014165151/https://halling.com/Platyceriums/Elemaria.htm", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", "轉述栽培者回報；照片取自 LAIFS Journal"),
    ("halling-hybrid-index", "Platycerium Hybrids（交種表）", HALLING, HB + "hybrid_index.htm",
     "https://web.archive.org/web/20261014155851/https://halling.com/Platyceriums/hybrid_index.htm", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", "交種的親本對照表"),
    ("palmtalk-platyceriums", "Platyceriums — another black hole（討論串）", "PalmTalk 論壇（International Palm Society）；使用者 epiphyte",
     "https://palmtalk.org/topic/91853-platyceriums-another-black-hole/", "", "forum", "en", "2025-11-13", "2026-10-15", "secondary",
     "T3", "美國", "PalmTalk 論壇", "2025-11-13 的貼文轉述 2011 年展覽標籤與 Fernando Orellana 2018 年的電子郵件；Wayback 存檔失敗（HTTP 520）"),
    # ---- batch 1 (2026-10-15)
    ("hoshizaki1975", "A Staghorn Fern (Platycerium) Hybrid", "Hoshizaki, B.J.；American Fern Journal 65(4): 99–101",
     "https://archive.org/details/mobot31753002153499", "", "reference", "en", "1975", "2026-10-15", "primary",
     "T1", "學術", "Hoshizaki 1975", "P. × mentelosii 與 cv. Fantastic Gardens 的原始發表；全文取自 archive.org 的 BHL 掃描（v.64–65 合訂本）OCR"),
    ("ploy-ratana2014", "Platycerium × kitshakoodiense, a hybrid of sister Thai fern species", "Ploy-ratana, P.；Acta Horticulturae 1025（ISHS）",
     "https://doi.org/10.17660/ActaHortic.2014.1025.11", "", "reference", "en", "2014", "2026-10-15", "primary",
     "T1", "學術", "Ploy-ratana 2014", "原始發表；只取得 ISHS 網站上的摘要（https://ishs.org/ishs-article/1025_11/）"),
    ("hoshizaki-yansura2021", "The Platycerium Variant from Mount Lewis, Australia", "Hoshizaki, B.J. & Yansura, D.G.；American Fern Journal 111(1): 24–34",
     "https://doi.org/10.1640/0002-8444-111.1.24", "", "reference", "en", "2021", "2026-10-15", "primary",
     "T1", "學術", "Hoshizaki & Yansura 2021", "只取得 BioOne 上的摘要，全文需訂閱"),
    ("halling-home", "Platyceriums: Staghorn Ferns and/or Elkhorn Ferns（首頁，逐種與交種摘要）", HALLING, HB + "Default.htm",
     "", "article", "en", "", "2026-10-15", "secondary", "T2", "美國", "Halling", "首頁逐段介紹各原生種與交種"),
    ("halling-charles-alford", "Platycerium Charles Alford", HALLING, HB + "Charles_Alford.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-callard", "Platycerium Callard Hybrid", HALLING, HB + "Callard.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-dawboy", "Platycerium Dawboy", HALLING, HB + "Dawboy.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-yanid", "Platycerium Yanid", HALLING, HB + "Yanid.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-mtkitshakood", "Platycerium Mt. Kitshakood", HALLING, HB + "MtKitshakood.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-mtlewis", "Platycerium Mt. Lewis", HALLING, HB + "MtLewis.htm", "", "article", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "Halling", ""),
    ("halling-alc-mad", "Platycerium Alcicorne x Madagascariense（Horn's Surprise、Larry Weed、Dawboy）", HALLING, HB + "Alcicorne-Madagascariense.htm",
     "", "article", "en", "", "2026-10-15", "secondary", "T2", "美國", "Halling", ""),
    ("mo-pegasus", "飛馬鹿角蕨怎麼照顧？特徵介紹、上板方向、價格 3 重點一篇搞懂！", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/pegasus-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-elephant", "象耳鹿角蕨有哪些？猛瑪象＆三角象鹿角蕨 8 品種照顧圖鑑", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/elephant-ear-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-ridley", "亞猴鹿角蕨 6 品種：細葉、圓葉、侏儒亞猴鹿角蕨照顧全指南", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/ridley-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-lemoinei", "檸檬鹿角蕨是什麼品種？高冠細葉＆侏儒檸檬鹿角蕨照顧圖鑑", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/lemoinei-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-crown", "皇冠鹿角蕨 2 大種類差異？菲律賓皇冠 vs 泰國皇冠鹿角蕨", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/crown-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-alcicorne", "圓盾鹿角蕨只有非圓與馬圓？非洲圓盾＆馬島圓盾10大品種圖鑑", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/alcicorne-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("mo-java", "爪哇鹿角蕨有什麼品種？短手＆侏儒爪哇鹿角蕨照顧分辨指南", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/java-staghorn-fern/",
     "", "article", "zh-TW", "", "2026-10-15", "secondary", "T3", "台灣", "微體溫室", ""),
    ("jl-rydeen", "Platycerium 'Rydeen'", "Jungle Leaves", "https://www.jungle-leaves.de/en/products/platycerium-rydeen", "", "vendor", "en", "",
     "2026-10-15", "secondary", "T3", "德國", "Jungle Leaves", "商品頁末段的照護句（不要太濕、需要大量光線）在該店各商品頁重複出現，視為通用文字不採用"),
    ("jl-alcicorne-dwarf", "Platycerium alcicorne 'Dwarf' (Madagascar)", "Jungle Leaves", "https://www.jungle-leaves.de/en/products/platycerium-alcicorne-dwarf-madagaskar",
     "", "vendor", "en", "", "2026-10-15", "secondary", "T3", "德國", "Jungle Leaves", "同上，通用照護句不採用"),
    ("jl-foong-siqi-qq", "Platycerium bifurcatum ssp. willinckii 'Foong SiQi QQ'", "Jungle Leaves",
     "https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-foong-siqi-qq", "", "vendor", "en", "", "2026-10-15", "secondary",
     "T3", "德國", "Jungle Leaves", "QQ 為 Foong Siqi 的組培版本；通用照護句不採用"),
    ("jl-jade-girl", "Platycerium bifurcatum ssp. willinckii 'Jade Girl'", "Jungle Leaves",
     "https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-jade-girl", "", "vendor", "en", "", "2026-10-15", "secondary",
     "T3", "德國", "Jungle Leaves", "通用照護句不採用"),
    ("jl-bacteria", "Platycerium bifurcatum ssp. willinckii 'Bacteria'", "Jungle Leaves",
     "https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-bacteria", "", "vendor", "en", "", "2026-10-15", "secondary",
     "T3", "德國", "Jungle Leaves", "通用照護句不採用"),
    # ---- batch 2 (2026-10-15)
    ("zyx-guide", "竹意軒的鹿角蕨小百科 | Platycerium Interactive Guide", "竹意軒", "https://zhu-yi-xuan.com/platycerium/", "", "article", "zh-TW", "",
     "2026-10-15", "secondary", "T3", "台灣", "竹意軒", "業者介紹自家蒐藏的逐品種短評；末段「栽培與繁殖指南」是屬層級通用說明，不採用"),
    ("kapei-notes", "【蕨得很好】鹿角蕨品種 31交種ｘ18原生種｜蕨類EP005．筆記", "卡呸醬的腦神經（痞客邦部落格）", "https://scent1983.pixnet.net/blog/post/230632765",
     "", "blog", "zh-TW", "2021-06-04", "2026-10-15", "secondary", "T3", "台灣", "卡呸醬", "玩家個人筆記（2022-08-04 更新）"),
    ("siam-holttumii-elephantotis", "Siam Exotica Plants of Platycerium holttumii x elephantotis", "Siam Exotica Plants（泰國）",
     "http://siamexotica.com/holttumii-elephantotis.html", "https://web.archive.org/web/20160816180607/http://siamexotica.com/holttumii-elephantotis.html",
     "vendor", "th", "", "2026-10-15", "secondary", "T3", "泰國", "Siam Exotica", "原站已失效，內容取自 Wayback 存檔；泰文"),
    ("siam-pup", "Pup_Platycerium（分株繁殖）", "Siam Exotica Plants（泰國）", "http://siamexotica.com/Pup_Platycerium.html",
     "https://web.archive.org/web/20080502155403/http://siamexotica.com:80/Pup_Platycerium.html", "vendor", "th", "", "2026-10-15", "secondary",
     "T3", "泰國", "Siam Exotica", "原站已失效，內容取自 Wayback 存檔；泰文"),
    ("siam-ridleyi-hybrid", "สายพันธุ์ย่อยและลูกผสมของ P.ridleyi（亞猴的品系與交種）", "Siam Exotica Plants（泰國）", "http://siamexotica.com/ridleyi-Hybrid.html",
     "https://web.archive.org/web/20160817085803/http://siamexotica.com/ridleyi-Hybrid.html", "vendor", "th", "", "2026-10-15", "secondary",
     "T3", "泰國", "Siam Exotica", "原站已失效，內容取自 Wayback 存檔；泰文"),
    ("siam-silver-velvet", "Platycerium elephantotis X Platycerium willinckii", "Siam Exotica Plants（泰國）",
     "http://siamexotica.com/Platycerium_elephantotis_X_willinckii.html",
     "https://web.archive.org/web/20131021203521/http://siamexotica.com/Platycerium_elephantotis_X_willinckii.html", "vendor", "en", "", "2026-10-15",
     "secondary", "T3", "泰國", "Siam Exotica", "原站已失效，內容取自 Wayback 存檔"),
    *[(sid, title, "阿金的便秘花園", "https://www.ajinsgarden.com/products/" + slug, "", "vendor", "zh-TW", "", "2026-10-15", "secondary",
       "T3", "台灣", "阿金的便秘花園", "")
      for sid, title, slug in [
          ("ajins-akki", "AKKI鹿角蕨 孢子苗 2吋盆", "p-akki（veitchii-silver-x-veitchii-wild）"),
          ("ajins-hillii-dwarf", "侏儒深綠鹿角蕨 Platycerium Hillii Dwarf", "platycerium-hillii-dwarf"),
          ("ajins-elephantotis-x-willinckii", "象耳交爪哇 象爪鹿角蕨 P. elephantotis x willinchii 組培苗", "p-elephantotis-x-willinchii"),
          ("ajins-smurf", "藍色小精靈鹿角蕨 Smurf 組培苗", "platy-willinckii-smurf"),
          ("ajins-unicorn", "獨角獸鹿角蕨 P. Unicorn 組培苗", "p-unicorn"),
          ("ajins-jenny", "珍妮鹿角蕨 Platycerium willinckii 'Jenny' 組培苗", "platycerium-willinckii-dwarf-jenny"),
          ("ajins-bacteria", "細菌爪哇鹿角蕨 Bacteria 2吋盆", "platycerium-willinckii-bacteria"),
          ("ajins-omg", "OMG鹿角蕨孢子苗", "p-willinckii-dwarf-cv-omg"),
          ("ajins-hakuna-matata", "馬塔塔 Hakuna matata鹿角蕨", "hakuna-matata"),
          ("ajins-alcicorne-africa-x-elephantotis", "非洲圓盾交象耳 非圓象 3吋", "palcicorne-africa-x-pelephantotis"),
          ("ajins-veitchii-x-wandae", "銀女 銀鹿交女王 鹿角蕨 3.5吋盆苗", "pveitchii-×-pwandae"),
          ("ajins-auburn-river", "奧本河銀葉鹿角蕨孢子苗 2.5吋盆",
           "奧本河銀葉鹿角蕨孢子苗-25吋盆-奧銀-澳銀-蕨類-鹿角蕨上板-觀葉植物-園藝-植栽-陽台植物【阿金的便秘花園】"),
          ("ajins-lemon", "檸檬鹿角蕨2吋盆", "檸檬鹿角蕨2吋盆-蕨類-鹿角蕨上板-觀葉植物-上板植物-園藝-療癒-植栽-陽台"),
          ("ajins-wallichii-x-willinckii", "蝴蝶交爪哇鹿角蕨 2.5吋盆", "蝴蝶交爪哇鹿角蕨-25吋盆-蕨類植物-鹿角蕨上板-上板植物-觀葉植物-園藝-植栽"),
          ("ajins-veitchii-x-willinckii", "銀哇鹿角蕨(銀鹿交爪哇) P. veitchii x P. willinchii 4吋盆", "銀哇鹿角蕨銀鹿交爪哇-p-veitchii-x-p-willinchii-4吋盆"),
          ("ajins-moose", "駝鹿鹿角蕨 Platycerium 'Moose'", "駝鹿鹿角蕨-深綠交非洲圓盾"),
          ("ajins-celso", "賽爾索鹿角蕨 P. willinckii 'Celso Tatsuta' TC 2吋盆苗", "賽爾索鹿角蕨-p-willinckii-celso-tatsuta-tc-2吋盆苗"),
          ("ajins-moonlight", "月光鹿角蕨 P. Willinckii Moonlight", "p-willinckii-moonlight"),
          ("ajins-robin", "羅賓鹿角蕨 Platycerium willinckii 'Robin' (TC) 布丁杯苗 2吋盆", "p-robin"),
          ("ajins-popcorn", "爆米花鹿角蕨 2吋盆 孢子苗", "ppopcorn"),
          ("ajins-flamenco", "佛朗明哥鹿角蕨 Platycerium (hillii x coronarium) 'Flamenco' 組培苗(TC) 2吋盆", "philliicoronariumflamenco"),
      ]],
    *[(sid, title, "晴花鹿苑 Haruhana Plants", "https://www.haruhanaplants.com/products/" + slug, "", "vendor", "zh-TW", "", "2026-10-15", "secondary",
       "T3", "台灣", "晴花鹿苑", "")
      for sid, title, slug in [
          ("haruhana-akki", "P. Akki 鹿角蕨", "p-akki"),
          ("haruhana-flamenco", "佛朗明哥", "phillii-x-coronarium-flamenco"),
          ("haruhana-monkey-north", "北猴鹿角蕨", "pmonkey-north"),
          ("haruhana-lemoinei", "檸檬鹿角蕨 入盆販售", "pveitchii-lemoinei-1"),
          ("haruhana-bif-white", "P. bif sp white 正側芽", "pbif-sp-white-00-1"),
          ("haruhana-willinckii-x-bif", "P. willinckii × P. bifurcatum 正側芽", "pwillinckii-x-bif-96"),
      ]],
    ("haruhana-fb-flamenco", "P.hillii × coronarium 'Flamenco' 佛朗明哥由深綠 Mio 與千手皇冠交種出來的絕美個體（影片）", "晴花鹿苑 Facebook",
     "https://www.facebook.com/100083026125755/videos/1758039951590851/", "", "vendor", "zh-TW", "", "2026-10-16", "secondary", "T3", "台灣", "晴花鹿苑", "只讀到網址裡的影片標題，影片內容未看"),
    ("ajins-wandae-dwarf", "侏儒捲葉女王 P. wandae var. dwarf & curling 2.5吋盆", "阿金的便秘花園",
     "https://www.ajinsgarden.com/products/侏儒捲葉女王-p-wandae-var-dwarf-curling-25吋盆", "", "vendor", "zh-TW", "", "2026-10-15", "secondary",
     "T3", "台灣", "阿金的便秘花園", ""),
    # ---- batch 4 (2026-10-16): the other vendor pages of this batch were entered in sources.csv when the plants were added
    ("haruhana-yellow-moon-dwarf", "琥珀 正側芽（P.willinckii Kohaku）", "晴花鹿苑 Haruhana Plants",
     "https://www.haruhanaplants.com/products/pwillinckii-yellow-moon-dwarf-1-1-1-1-1", "", "vendor", "zh-TW", "", "2026-10-16", "secondary",
     "T3", "台灣", "晴花鹿苑", "網址是 yellow-moon-dwarf，但頁面販售的是命名個體「琥珀 Kohaku」，型態描述不套用到侏儒黃月"),
    ("ncsu-bifurcatum", "Platycerium bifurcatum (Staghorn Fern)", "NC State Extension Gardener Plant Toolbox",
     "https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/common-name/staghorn-fern/", "", "database", "en", "", "2026-10-15", "secondary",
     "T2", "美國", "NC State Extension", "大學推廣單位；頁面的照護欄位寫的是二叉鹿角蕨這個種，不套用到栽培品種"),
    ("cistus-netherlands", "*RETAIL - Platycerium bifurcatum 'Netherlands'", "Cistus Nursery", "https://cistus.com/products/retail-platycerium-bifurcatum-netherlands",
     "", "vendor", "en", "", "2026-10-15", "secondary", "T3", "美國", "Cistus Nursery", "奧勒岡州苗圃"),
    # ---- FSQ line (2026-10-18): Wanna's monthly catalogs (I Love Ferns Nursery, bloggang) are the breeder's own listings
    *[(f"wanna-cat-{ym}", title, "I Love Ferns Nursery（Wanna Pinjipaitoon，泰國尖竹汶）",
       f"https://www.bloggang.com/m/viewdiary.php?id=ladyslipper&month={ym[5:]}-{ym[:4]}&date=01&group=25&gblog={g}", "", "vendor", "en",
       f"{ym}-01", "2026-10-18", "primary", "T3", "泰國", "I Love Ferns（Wanna）", "育種者自家的月型錄；品名後的 (FSQ) 標示出自 Foongsiqi 孢子苗系")
      for ym, g, title in [
          ("2020-03", 176, "จำหน่ายเฟินชายผ้าสีดาและเฟินอื่นๆประจำเดือนมีนาคม/March 2020"),
          ("2020-09", 179, "จำหน่ายเฟินชายผ้าสีดาและเฟินอื่นๆประจำเดือนกันยายน/September /2020"),
          ("2020-11", 181, "จำหน่ายเฟินชายผ้าสีดาและเฟินอื่นๆประจำเดือนพฤศจิกายน/November /2020"),
          ("2021-02", 184, "จำหน่ายเฟินชายผ้าสีดาและเฟินอื่นๆประจำเดือนกุมภาพันธ์/February 2021"),
          ("2021-03", 185, "จำหน่ายเฟินชายผ้าสีดาและเฟินอื่นๆประจำเดือนมีนาคม / March 2021"),
          ("2021-10", 191, "จำหน่ายเฟินชายผ้าสีดา เดือนตุลาคม2564/October Catalog 2021"),
          ("2022-11", 204, "November Catalog Platycerium ferns for sale"),
          ("2022-12", 205, "December Catalog Platycerium ferns for sale"),
          ("2023-02", 207, "จำหน่ายเฟินชายผ้าสีดา Platycerium Catalog for February 2023"),
          ("2023-03", 208, "March Catalog iloveferns Nursery by Wanna"),
          ("2023-11", 216, "Platycerium ferns November Catalog 2023"),
          ("2023-12", 217, "December Catalog 2023 by iloveferns Nursery"),
          ("2025-02", 228, "จำหน่ายเฟินชายผ้าสีดา Platycerium ferns for sale February 2025"),
          ("2025-03", 229, "Platycerium Ferns for Sale for March 2025"),
          ("2026-04", 237, "จำหน่ายเฟินชายผ้าสีดาเดือนเมษายน2569 / Platycerium ferns for sale April 2026"),
          ("2026-07", 239, "จำหน่ายเฟินชายผ้าสีดาเดือนกรกฏาคม2569(Platycerium ferns for sale July 2026)"),
          ("2026-08", 240, "จำหน่ายเฟินชายผ้าสีดาเดือนสิงหาคม 2569 / Platycerium ferns Catalog for August 2026"),
      ]],
    ("wanna-yt-kusuma", "Platycerium FSQ No. 16 (Kusuma)", "YouTube；Thaigardenstore & iloveferns By Wanna",
     "https://www.youtube.com/watch?v=q2Gp1Hc0Hrg", "", "vendor", "en", "", "2026-10-18", "primary", "T3", "泰國", "I Love Ferns（Wanna）",
     "YouTube 影片；與 Wanna 型錄同一單位"),
    ("wps-foong-si-qi", "Platycerium 'Foong Si Qi'（WPS-P-000048）", "World Platycerium Society Registry",
     "https://www.worldplatycerium.org/registry/WPS-P-000048", "", "database", "en", "", "2026-10-18", "aggregator", "T4", "國際",
     "World Platycerium Society", "登錄狀態 Research in progress；引用黃仕傑《鹿角蕨日記簿：栽培與觀賞》（2025）與晴花鹿苑；把 FSQ 列為別名"),
    ("wps-sazanami", "Platycerium 'Sazanami'（WPS-P-000040）", "World Platycerium Society Registry",
     "https://www.worldplatycerium.org/registry/WPS-P-000040", "", "database", "en", "", "2026-10-18", "aggregator", "T4", "國際",
     "World Platycerium Society", "登錄狀態 Accepted record；選育資料由晴花鹿苑第一手提供"),
    ("haruhana-usa-sazanami", "P. Sazanami", "Haruhana USA（晴花鹿苑美國站）", "https://haruhana-usa.com/products/p-sazanami", "", "vendor", "en",
     "", "2026-10-18", "secondary", "T3", "台灣", "晴花鹿苑", "與晴花鹿苑台灣站同一單位"),
    # ---- PlatyWiki 品種清單的獨立查證 (2026-10-18)：PlatyWiki 本身不引用，只當線索
    ("siam-sale-newhybrids", "Sale Platycerium New Hybrids 1", "Siam Exotica Plants（泰國）",
     "http://www.siamexotica.com/Sale-Platycerium-NewHybrids-1.html",
     "https://web.archive.org/web/20090605080222/http://www.siamexotica.com:80/Sale-Platycerium-NewHybrids-1.html", "vendor", "en", "",
     "2026-10-18", "secondary", "T3", "泰國", "Siam Exotica", "交種價目表；Halling 說 Durval Nunes 是 Siam Exotica 列出的"),
    ("platyceriumferns-durval", "Introducing A Extreamy Rare New Cultivar", "Platycerium ferns（platyceriumferns.com）",
     "http://www.platyceriumferns.com/2007/10/introducing-extreamy-rare-new-cultivar.html", "", "blog", "en", "2007-10", "2026-10-18",
     "primary", "T3", "美國", "platyceriumferns.com", "販售鹿角蕨的玩家部落格；Siam Exotica 的價目表把它列為 Durval Nunes 的來源"),
    ("basements-totoro", "Platycerium Willinckii Dwarf 'Totoro' Sporelings", "The Basements",
     "https://www.thebasements.com/products/platycerium-willinckii-dwarf-totoro-sporelings", "", "vendor", "en", "2025-12-17", "2026-10-18",
     "secondary", "T3", "美國", "The Basements", "照護欄的溫度 65–85 °F 是生長適溫，不當建議最低／最高溫"),
    ("naturefix-totoro", "P.willinckii Totoro sporeling", "naturefix", "https://naturefix.official.ec/items/110401384", "", "vendor", "ja",
     "", "2026-10-18", "secondary", "T3", "日本", "naturefix", "已售完"),
    ("yahoo-frontier-totoro", "【Frontier Plants】【現品】ビカクシダ・ウィリンキー・トトロ 胞子苗 豆豆龍 P.willinckii Totoro sporeling Yellow Moon Dwarf",
     "Yahoo!オークション（出品者 Frontier Plants）", "https://page.auctions.yahoo.co.jp/jp/auction/b1246371030", "", "vendor", "ja", "2026-09-29",
     "2026-10-18", "secondary", "T3", "日本", "Frontier Plants", "已結標的拍賣頁"),
    ("yahoo-hhr-totoro", "HHR Garden由来 P. willinckii 'Totoro' sporeling", "Yahoo!オークション（出品者在愛知縣）",
     "https://page.auctions.yahoo.co.jp/jp/auction/u1244834332", "", "vendor", "ja", "2026-09-16", "2026-10-18", "secondary", "T3", "日本",
     "日本拍賣（HHR Garden 苗）", "已結標的拍賣頁；個人轉售"),
    ("yahoo-vandaka-grace", "P. willinckii 'Grace' spore grown (select)", "Yahoo!オークション（出品者 vandaka plants）",
     "https://page.auctions.yahoo.co.jp/jp/auction/w1245886822", "", "vendor", "ja", "2026-09-25", "2026-10-18", "secondary", "T3", "日本",
     "vandaka plants", "已結標的拍賣頁；落札價 1,901,000 日圓"),
    ("yahoo-grace-2024", "特A1，P.Willinckii Grace sporeling HHR 黄さんの直筆サイン入り", "Yahoo!オークション（出品者在千葉縣）",
     "https://page.auctions.yahoo.co.jp/jp/auction/t1158136168", "", "vendor", "ja", "2024-10-23", "2026-10-18", "secondary", "T3", "日本",
     "日本拍賣（HHR 苗）", "已結標的拍賣頁；個人轉售"),
    # ---- v1.4 B1 (2026-10-19): vendor pages found by name searches
    ("joshsfrogs-lemoinei", "Platycerium veitchii 'Lemoinei' - French Staghorn Fern", "Josh's Frogs",
     "https://joshsfrogs.com/sp/platycerium-veitchii-lemoinei-french-staghorn-fern-plant588", "", "vendor", "en", "", "2026-10-19",
     "secondary", "T3", "美國", "Josh's Frogs", "ReptiFiles 商店頁的文字與此頁相同，視為同一來源"),
    ("foliage-factory-netherlands", "Platycerium bifurcatum 'Netherlands'", "Foliage Factory",
     "https://www.foliage-factory.com/platycerium-bifurcatum-netherlands", "", "vendor", "en", "", "2026-10-19",
     "secondary", "T3", "德國", "Foliage Factory", "從德國與荷蘭出貨的歐洲網店"),
    ("theplantco-netherlands", "Platycerium bifurcatum 'Netherlands' (Elkhorn Fern, Staghorn Fern)", "The Plant Company",
     "https://theplantcompany.co.nz/shop/product/ferns/platycerium-bifurcatum-netherlands", "", "vendor", "en", "", "2026-10-19",
     "secondary", "T3", "紐西蘭", "The Plant Company", ""),
    ("vegetal-high-finger", "Platycerium High Finger", "Vegetal Design",
     "https://vegetaldesignqc.com/en/products/platycerium-high-finger", "", "vendor", "en", "", "2026-10-19",
     "secondary", "T3", "加拿大", "Vegetal Design", "照護欄（低至中光、15–30 °C）像該店通用的照護表，不採用"),
    ("vegetal-pegasus", "Platycerium Pegasus", "Vegetal Design", "https://vegetaldesignqc.com/en/products/platycerium-pegasus", "", "vendor", "en", "",
     "2026-10-19", "secondary", "T3", "加拿大", "Vegetal Design", "照護欄是該店通用的照護表，不採用"),
    ("paraiso-polar-bear", "Mounted Platycerium Omo 'Polar Bear'", "Paraíso Plant Studio",
     "https://paraisoplant.studio/collections/all/products/mounted-platycerium-omo-polar-bear", "", "vendor", "en", "", "2026-10-19",
     "secondary", "T3", "美國", "Paraíso Plant Studio", "加州舊金山灣區的植物店；照護欄是蕨類通用文字，不採用"),
    # ---- Banna series (2026-10-20): Thai nursery "Banna" numbered hybrids, Taiwan / Japan vendor and grower pages
    ("lwhp-banna-a", "P. Banna #A 鹿角蕨", "風和日麗 Live with House Plants",
     "https://live-with-house-plants.tw/p-banna-a-%E9%B9%BF%E8%A7%92%E8%95%A8/", "", "vendor", "zh-TW", "", "2026-10-20",
     "secondary", "T3", "台灣", "風和日麗", "花蓮的植物店；「照顧祕訣」各條是該店通用文字，只採用逐種的「特別留意」段"),
    ("leo-banna-a", "《LEO雨林植物》 P. Banna #A 鹿角蕨", "LEO雨林植物（iOPEN Mall）",
     "https://mall.iopenmall.tw/029209/index.php?action=product_detail&prod_no=P2920904303577", "", "vendor", "zh-TW", "", "2026-10-20",
     "secondary", "T3", "台灣", "LEO雨林植物", "「照顧方式」與 #B 頁逐字相同，視為店家通用文字，不採用"),
    ("leo-banna-b", "P. Banna #B 鹿角蕨", "LEO雨林植物（iOPEN Mall）",
     "https://mall.iopenmall.tw/029209/index.php?action=product_detail&prod_no=P2920904303568", "", "vendor", "zh-TW", "", "2026-10-20",
     "secondary", "T3", "台灣", "LEO雨林植物", "與 leo-banna-a 同一店家，不算獨立來源；「照顧方式」是店家通用文字，不採用"),
    ("calmplants-banna-a", "ビカクシダ バンナA (P. Banna#A)", "calmplants のビカクシダブログ（Ameblo）",
     "https://ameblo.jp/calmplants/entry-12813647913.html", "", "blog", "ja", "", "2026-10-20",
     "secondary", "T3", "日本", "calmplants 部落格", "日本的栽培者兼賣家；親本寫「だそう」（聽說）"),
    ("calmplants-banna-a-2", "その後のビカクシダ バンナA (P. Banna#A) ①", "calmplants のビカクシダブログ（Ameblo）",
     "https://ameblo.jp/calmplants/entry-12822950216.html", "", "blog", "ja", "", "2026-10-20",
     "secondary", "T3", "日本", "calmplants 部落格", "與 calmplants-banna-a 同一作者"),
    ("greensnap-banna-b", "P. Banna #B 成長記録 2024.12.18", "GreenSnap（kame_plants）",
     "https://greensnap.jp/greenBlog/13440627", "", "blog", "ja", "2021-03-28", "2026-10-20",
     "secondary", "T3", "日本", "GreenSnap（kame_plants）", "玩家的栽培紀錄（2021–2024）；和 #A 的比較是看親株照片的推測，只寫進 note"),
    ("orchids-shop-banna-a", "Platycerium Banna # A P. andinum", "Orchids-shop（Orchideeën Shop）",
     "https://orchids-shop.com/products/platycerium-banna-a-p-andinum", "", "vendor", "en", "", "2026-10-20",
     "secondary", "T3", "荷蘭", "Orchids-shop", "把 Banna #A 寫成安地斯鹿角蕨的選拔，與其他來源都不同，疑似誤植，不採用"),
]

# Wayback snapshots taken after the sources were cited (guideline §6 工具); id -> archive_url
ARCHIVE = {
    "ajins-akki": "https://web.archive.org/web/20261014184152/https://www.ajinsgarden.com/products/p-akki%EF%BC%88veitchii-silver-x-veitchii-wild%EF%BC%89",
    "ajins-alcicorne-africa-x-elephantotis": "https://web.archive.org/web/20261014185253/https://www.ajinsgarden.com/products/palcicorne-africa-x-pelephantotis",
    "ajins-auburn-river": "https://web.archive.org/web/20261014185444/https://www.ajinsgarden.com/products/%E5%A5%A7%E6%9C%AC%E6%B2%B3%E9%8A%80%E8%91%89%E9%B9%BF%E8%A7%92%E8%95%A8%E5%AD%A2%E5%AD%90%E8%8B%97-25%E5%90%8B%E7%9B%86-%E5%A5%A7%E9%8A%80-%E6%BE%B3%E9%8A%80-%E8%95%A8%E9%A1%9E-%E9%B9%BF%E8%A7%92%E8%95%A8%E4%B8%8A%E6%9D%BF-%E8%A7%80%E8%91%89%E6%A4%8D%E7%89%A9-%E5%9C%92%E8%97%9D-%E6%A4%8D%E6%A0%BD-%E9%99%BD%E5%8F%B0%E6%A4%8D%E7%89%A9%E3%80%90%E9%98%BF%E9%87%91%E7%9A%84%E4%BE%BF%E7%A7%98%E8%8A%B1%E5%9C%92%E3%80%91",
    "ajins-bacteria": "https://web.archive.org/web/20261014184957/https://www.ajinsgarden.com/products/platycerium-willinckii-bacteria",
    "ajins-celso": "https://web.archive.org/web/20261014185838/https://www.ajinsgarden.com/products/%E8%B3%BD%E7%88%BE%E7%B4%A2%E9%B9%BF%E8%A7%92%E8%95%A8-p-willinckii-celso-tatsuta-tc-2%E5%90%8B%E7%9B%86%E8%8B%97",
    "ajins-elephantotis-x-willinckii": "https://web.archive.org/web/20261015001729/https://www.ajinsgarden.com/products/p-elephantotis-x-willinchii",
    "ajins-hakuna-matata": "https://web.archive.org/web/20261014185134/https://www.ajinsgarden.com/products/hakuna-matata",
    "ajins-hillii-dwarf": "https://web.archive.org/web/20261014184325/https://www.ajinsgarden.com/products/platycerium-hillii-dwarf",
    "ajins-jenny": "https://web.archive.org/web/20261014184848/https://www.ajinsgarden.com/products/platycerium-willinckii-dwarf-jenny",
    "ajins-lemon": "https://web.archive.org/web/20261014185614/https://www.ajinsgarden.com/products/%E6%AA%B8%E6%AA%AC%E9%B9%BF%E8%A7%92%E8%95%A82%E5%90%8B%E7%9B%86-%E8%95%A8%E9%A1%9E-%E9%B9%BF%E8%A7%92%E8%95%A8%E4%B8%8A%E6%9D%BF-%E8%A7%80%E8%91%89%E6%A4%8D%E7%89%A9-%E4%B8%8A%E6%9D%BF%E6%A4%8D%E7%89%A9-%E5%9C%92%E8%97%9D-%E7%99%82%E7%99%92-%E6%A4%8D%E6%A0%BD-%E9%99%BD%E5%8F%B0",
    "ajins-moonlight": "https://web.archive.org/web/20261014185936/https://www.ajinsgarden.com/products/p-willinckii-moonlight",
    "ajins-moose": "https://web.archive.org/web/20261014185806/https://www.ajinsgarden.com/products/%E9%A7%9D%E9%B9%BF%E9%B9%BF%E8%A7%92%E8%95%A8-%E6%B7%B1%E7%B6%A0%E4%BA%A4%E9%9D%9E%E6%B4%B2%E5%9C%93%E7%9B%BE",
    "ajins-omg": "https://web.archive.org/web/20261014185052/https://www.ajinsgarden.com/products/p-willinckii-dwarf-cv-omg",
    "ajins-smurf": "https://web.archive.org/web/20261014184626/https://www.ajinsgarden.com/products/platy-willinckii-smurf",
    "ajins-unicorn": "https://web.archive.org/web/20261014184752/https://www.ajinsgarden.com/products/p-unicorn",
    "ajins-veitchii-x-wandae": "https://web.archive.org/web/20261014185416/https://www.ajinsgarden.com/products/pveitchii-%C3%97-pwandae",
    "ajins-veitchii-x-willinckii": "https://web.archive.org/web/20261014185735/https://www.ajinsgarden.com/products/%E9%8A%80%E5%93%87%E9%B9%BF%E8%A7%92%E8%95%A8%E9%8A%80%E9%B9%BF%E4%BA%A4%E7%88%AA%E5%93%87-p-veitchii-x-p-willinchii-4%E5%90%8B%E7%9B%86",
    "ajins-wallichii-x-willinckii": "https://web.archive.org/web/20261014185646/https://www.ajinsgarden.com/products/%E8%9D%B4%E8%9D%B6%E4%BA%A4%E7%88%AA%E5%93%87%E9%B9%BF%E8%A7%92%E8%95%A8-25%E5%90%8B%E7%9B%86-%E8%95%A8%E9%A1%9E%E6%A4%8D%E7%89%A9-%E9%B9%BF%E8%A7%92%E8%95%A8%E4%B8%8A%E6%9D%BF-%E4%B8%8A%E6%9D%BF%E6%A4%8D%E7%89%A9-%E8%A7%80%E8%91%89%E6%A4%8D%E7%89%A9-%E5%9C%92%E8%97%9D-%E6%A4%8D%E6%A0%BD",
    "ajins-wandae-dwarf": "https://web.archive.org/web/20261014190657/https://www.ajinsgarden.com/products/%E4%BE%8F%E5%84%92%E6%8D%B2%E8%91%89%E5%A5%B3%E7%8E%8B-p-wandae-var-dwarf-curling-25%E5%90%8B%E7%9B%86",
    "cistus-netherlands": "https://web.archive.org/web/20261015001955/https://cistus.com/products/retail-platycerium-bifurcatum-netherlands",
    "halling-alc-mad": "https://web.archive.org/web/20261014181911/https://halling.com/Platyceriums/Alcicorne-Madagascariense.htm",
    "halling-callard": "https://web.archive.org/web/20261014181325/https://halling.com/Platyceriums/Callard.htm",
    "halling-charles-alford": "https://web.archive.org/web/20261014181110/https://halling.com/Platyceriums/Charles_Alford.htm",
    "halling-dawboy": "https://web.archive.org/web/20261014181349/https://halling.com/Platyceriums/Dawboy.htm",
    "halling-home": "https://web.archive.org/web/20261014181057/https://halling.com/Platyceriums/Default.htm",
    "halling-mtkitshakood": "https://web.archive.org/web/20261014181634/https://halling.com/Platyceriums/MtKitshakood.htm",
    "halling-mtlewis": "https://web.archive.org/web/20261014181751/https://halling.com/Platyceriums/MtLewis.htm",
    "halling-yanid": "https://web.archive.org/web/20261014181514/https://halling.com/Platyceriums/Yanid.htm",
    "haruhana-akki": "https://web.archive.org/web/20261014190008/https://www.haruhanaplants.com/products/p-akki",
    "haruhana-bif-white": "https://web.archive.org/web/20261014190326/https://www.haruhanaplants.com/products/pbif-sp-white-00-1",
    "haruhana-lemoinei": "https://web.archive.org/web/20261014190210/https://www.haruhanaplants.com/products/pveitchii-lemoinei-1",
    "haruhana-monkey-north": "https://web.archive.org/web/20261014190135/https://www.haruhanaplants.com/products/pmonkey-north",
    "haruhana-willinckii-x-bif": "https://web.archive.org/web/20261015001909/https://www.haruhanaplants.com/products/pwillinckii-x-bif-96",
    "jl-alcicorne-dwarf": "https://web.archive.org/web/20261014183300/https://www.jungle-leaves.de/en/products/platycerium-alcicorne-dwarf-madagaskar",
    "jl-bacteria": "https://web.archive.org/web/20261014183741/https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-bacteria",
    "jl-foong-siqi-qq": "https://web.archive.org/web/20261014183447/https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-foong-siqi-qq",
    "jl-jade-girl": "https://web.archive.org/web/20261014183619/https://www.jungle-leaves.de/en/products/platycerium-bifurcatum-ssp-willinckii-jade-girl",
    "jl-rydeen": "https://web.archive.org/web/20261014183133/https://www.jungle-leaves.de/en/products/platycerium-rydeen",
    "kapei-notes": "https://web.archive.org/web/20261014184015/https://scent1983.pixnet.net/blog/posts/8230632765",
    "mo-alcicorne": "https://web.archive.org/web/20261014182828/https://micro-oasis.com/posts/alcicorne-staghorn-fern/",
    "mo-crown": "https://web.archive.org/web/20261014182656/https://micro-oasis.com/posts/crown-staghorn-fern/",
    "mo-elephant": "https://web.archive.org/web/20261014182210/https://micro-oasis.com/posts/elephant-ear-staghorn-fern/",
    "mo-java": "https://web.archive.org/web/20261014183027/https://micro-oasis.com/posts/java-staghorn-fern/",
    "mo-lemoinei": "https://web.archive.org/web/20261014182522/https://micro-oasis.com/posts/lemoinei-staghorn-fern/",
    "mo-pegasus": "https://web.archive.org/web/20261014182030/https://micro-oasis.com/posts/pegasus-staghorn-fern/",
    "mo-ridley": "https://web.archive.org/web/20261014182349/https://micro-oasis.com/posts/ridley-staghorn-fern/",
    "ncsu-bifurcatum": "https://web.archive.org/web/20261014190804/https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/common-name/staghorn-fern/",
    "zyx-guide": "https://web.archive.org/web/20261014183855/https://zhu-yi-xuan.com/platycerium/",
}

# ---------------------------------------------------------------- blocks
# cites: (source, field, value, label, claim, quote, page, use)
# desc / note: (sentence, source, quote, page) — every sentence carries one citation
# text: overrides of generated text columns (shield, fertile, growth, ...); the facts must already be cited above
# extra: non-feature fields the block cites (rows matched by plant + source + field)
# searched: what was searched for fields left without a summary (guideline §6); "*" is the default
# version / date: guideline version and survey date of the block (default v1.3 / 2026-10-15); v1.4 batches set both
#   (batches_v1.4.md); relaxed statements (guideline v1.4) carry a "~" value prefix, e.g. c(src, "size", "~S", "小型", ...)
HP = "hoshizaki-price1990"
BLOCKS = {}

BLOCKS["elemaria"] = dict(
    cites=[
        # morphology — T1: the protologue (Hoshizaki & Price 1990)
        (HP, "size", "~70", "盾葉可達 70 × 30 cm、孢子葉可達 63 × 53 cm",
         "只給上限（to …），無範圍可算嚴格 D；v1.4 記為寬鬆 D = 70", "Base fronds to 70 x 30 cm ... Foliage fronds ... to 63 x 53 cm", "pp. 63–64", "summary"),
        (HP, "fertile_length", "~≤63 cm", "可達 63 cm", "只給上限 → v1.4 寬鬆說法", "the fronds slightly asymmetrical, ± deltoid, to 63 x 53 cm", "p. 64", "summary"),
        (HP, "shield_vein", "yes", "主脈略隆起", "somewhat prominent → yes（隆起）",
         "Base fronds to 70 x 30 cm, upper part extended and foliaceous, with somewhat prominent main veins", "p. 63", "summary"),
        (HP, "shield_fringe", "above-stipe", "芽點上方有盾葉組織的皺褶",
         "ruffle of base frond tissue 覆蓋芽點上方，對應專著「只在孢子葉柄上方」的領片", "Bud covered above by a ruffle of base frond tissue.", "pp. 63–64", "summary"),
        (HP, "fertile_split", "0", "不分岔（先端不規則鈍裂）", "沒有明確的分岔，先端只有不規則鈍裂片 → 0",
         "apical margin subentire to with 9 irregular blunt lobes to 12 x 7 cm ... the absence of any defined forking of the foliage fronds", "p. 64", "summary"),
        (HP, "fertile_width", 5, "不分裂", "孢子葉不分岔 → 5", "the absence of any defined forking of the foliage fronds", "p. 64", "summary"),
        (HP, "spore", "tips", "葉片上部三分之一", "散生於葉片遠端三分之一 → 葉片上部",
         "Soral patches irregular in shape and distribution, several, scattered on the distal third of the frond and extending to the base of the apical lobes.", "p. 64", "summary"),
        (HP, "pups", "yes", "可由根芽（側芽）繁殖", "會長根芽並可繁殖 → yes",
         "P. x elemaria has been successfully reproduced from root bud \"pups\" by Mr. Ernie Sanchez", "p. 64", "summary"),
        (HP, "origin", "美國加州帕薩迪納的苗圃中發現；不確定源於栽培或野外", "發現於加州苗圃",
         "", "we have been unable to determine if the hybrid originated in cultivation or was collected from the wild", "p. 62", "summary"),
        # morphology — T2 (no T1 statement on hairs)
        ("halling-elemaria", "fertile_hair", 1, "深綠色、上表面蠟質（下表面未知）", "waxy → 1；來源說不確定下表面是否多毛",
         "The fertile fronds are dark green with a waxy top. It is not known if the underside is harry like P. stemaria.", "", "summary"),
        # care
        ("halling-elemaria", "water", 1, "最常見的問題是澆水過多而腐爛", "相當於 easily over-watered → 1（同頁另寫尚無澆水的報告）",
         "most common problem reported is rot from too much watering.", "", "summary"),
        # parents (not a feature column; plants.csv `parents` is left as it is)
        (HP, "parents", "elephantotis|stemaria", "象耳 × 三角（依外形推斷）", "原發表依形態推斷", "we encountered a hybrid plant whose parents we confidently believe are P. elephantotis and P. stemaria", "p. 62", "summary"),
        ("powo-elemaria", "parents", "elephantotis|stemaria", "象耳 × 三角", "", "The hybrid formula of this artificial cross is P. elephantotis × P. stemaria.", "", "summary"),
        ("halling-hybrid-index", "parents", "andinum|elephantotis", "安地斯 × 象耳（DNA 確認）", "交種表第 6 列；註腳說親本經 DNA 檢測確認，但未給出處",
         "'Elemaria'** | Andinum | Elephantotis ... ** Elemaria parantage is confirmed via DNA testing", "", "summary"),
        ("palmtalk-platyceriums", "parents", "andinum", "其中一個親本的遺傳標記與安地斯一致（未發表）", "論壇轉述的私人電子郵件，只供參考",
         "the genetic markers of one of the parents was consistent with P. andinum, I don't think this has been published yet", "", "reference"),
    ],
    extra={"parents"},
    desc=[
        ("Hoshizaki 與 Price 在美國加州帕薩迪納 Ernie Sanchez 的 Tropical Gardens Nursery 發現這個雜交種，1990 年發表。", HP,
         "In examining the Platycerium collection of Mr. Ernie Sanchez of Tropical Gardens Nursery, Pasadena, CA, we encountered a hybrid plant", "p. 61"),
        ("外形與象耳鹿角蕨相近，但孢子葉先端不規則淺裂、上表面葉脈只略隆起，也沒有排水孔。", HP,
         "from P. elephantotis by the irregularly lobed distal margin, the veins only slightly prominent on adaxial surface, and absence of hydathodes", "p. 64"),
        ("孢子葉灰綠色，近三角形、略不對稱，大致成對長出。", HP,
         "Foliage fronds gray-green, produced essentially in pairs, the fronds slightly asymmetrical, + deltoid", "p. 64"),
        ("在加州相同的栽培條件下，成熟植株每年長出兩對孢子葉。", HP,
         "the number of pairs of fronds produced annually in cultivation in California under the same cultural conditions ... and P. x elemaria two pairs", "p. 64"),
        ("孢子囊多半皺縮、空的，孢子多為畸形，是雜交種的特徵。", HP,
         "Sporangia mostly shriveled and empty ... The irregularity of the lobing and the soral areas, and the abortive sporangia and spores are indicative of hybridity", "p. 64"),
        ("比雙親耐寒，在南加州可以戶外栽培。", "halling-elemaria", "P. elemaria appears more tolerant to cold than its parents. It grows out doors in So. California.", ""),
    ],
    note=[
        ("Hoshizaki & Price 1990 依外形認為親本是 P. elephantotis 與 P. stemaria，但無法確定它源於栽培還是野外。", HP,
         "a hybrid plant whose parents we confidently believe are P. elephantotis and P. stemaria. ... unable to determine if the hybrid originated in cultivation or was collected from the wild", "p. 62"),
        ("POWO 依此列為人工雜交種，雜交式為 P. elephantotis × P. stemaria。", "powo-elemaria",
         "This is an artificial hybrid. The hybrid formula of this artificial cross is P. elephantotis × P. stemaria.", ""),
        ("Halling 的交種表則把親本列為 P. andinum × P. elephantotis，並註明親本經 DNA 檢測確認。", "halling-hybrid-index",
         "'Elemaria'** | Andinum | Elephantotis ... ** Elemaria parantage is confirmed via DNA testing", ""),
        ("PalmTalk 論壇轉述 Fernando Orellana 2018 年的電子郵件：Dan Yansura 的基因檢測顯示其中一個親本的遺傳標記與 P. andinum 一致，但尚未發表。", "palmtalk-platyceriums",
         "Our friend Dan Yansura conducted a genetic test about two years ago and discovered that the genetic markers of one of the parents was consistent with P. andinum, I don't think this has been published yet", ""),
        ("以根芽繁殖的植株特徵穩定，同一篇發表另命名為栽培品種 'Sanchez'。", HP,
         "Since P. x elemaria has been successfully reproduced from root bud \"pups\" by Mr. Ernie Sanchez, and its features are constant ... we are pleased to name this after Mr. Sanchez", "p. 64"),
    ],
    text=dict(
        shield="上半部延伸成葉狀，主脈略隆起，先端近全緣至波狀；芽點上方覆有盾葉組織形成的皺褶。",
        fertile="孢子葉灰綠色，近三角形、略不對稱，沒有明確分岔，先端近全緣或有最多 9 個不規則鈍裂片；孢子囊群形狀不規則，散生於葉片上部三分之一。",
        growth="會長根芽（側芽），可分株繁殖。",
    ),
    searched={
        "*": "Hoshizaki & Price 1990（Amer. Fern J. 80: 61–64，原始發表）|POWO|Halling Elemaria.htm 與交種表"
             "|搜尋：\"elemaria\" Platycerium fronds shield pendulous description Hoshizaki|PalmTalk 討論串",
        "care": "Halling Elemaria.htm|搜尋：Elemaria 鹿角蕨|搜尋：\"Platycerium elemaria\" care light water"
                "|搜尋：Platycerium 'Elemaria' staghorn fern grow outdoors nursery|搜尋：ビカクシダ エレマリア elemaria 育て方",
    },
)
BLOCKS["elemaria"]["searched"]["min_temp"] = BLOCKS["elemaria"]["searched"]["care"] + "|（Halling 只寫比雙親耐寒、南加州可戶外栽培，沒有溫度數值，寫入 desc）"


# ---------------------------------------------------------------- batch 1 helpers
def c(src, field, value, label, claim="", quote="", page="", use="summary"):
    return (src, field, value, label, claim, quote, page, use)


# 微體溫室〈40 種鹿角蕨一次推薦〉: rows = light, columns = difficulty (same mapping as survey_species.py)
MO_DIFF = {1: "新手", 3: "中階", 5: "進階"}
MO_LIGHT = {5: "中強光（夏季遮陰 30%）", 3: "中光（夏季遮陰 50%）", 1: "低弱光（夏季遮陰 70%）"}


def mo_guide(zh, diff, light):
    q = f"{MO_LIGHT[light].replace(' ', '')}｜{MO_DIFF[diff]}鹿角蕨品種：{zh}鹿角蕨"
    return [c("mo-guide", "difficulty", diff, MO_DIFF[diff], f"「{zh}鹿角蕨」列在表格的「{MO_DIFF[diff]}鹿角蕨品種」欄", q),
            c("mo-guide", "light", light, MO_LIGHT[light], f"「{zh}鹿角蕨」列在表格的「{MO_LIGHT[light]}」列", q)]


# 微體溫室 per-article difficulty tables: five grades onto the guideline's 1 / 3 / 5
MO_RATE = {"容易": 1, "中偏易": "1–3", "中等": 3, "中偏難": "3–5", "難": 5}


def mo_rate(src, zh, rate, table):
    return c(src, "difficulty", MO_RATE[rate], rate, f"〈{table}〉表格中「{zh}」的照顧難度為「{rate}」→ {MO_RATE[rate]}", f"{zh}｜{rate}")


H1 = "hoshizaki1975"
PR = "ploy-ratana2014"
HY = "hoshizaki-yansura2021"
HH = "halling-home"
GENERIC = "（共用的屬層級通用照護文字不採用：阿金商品頁末段的鹿角蕨通用說明、We Love Tropical Plants 各商品頁相同的照護表、Jungle Leaves 各商品頁相同的照護句）"


def searched(star, care):
    return {"*": star, "care": care}


# ---------------------------------------------------------------- batch 1: hybrids with literature (T1 / Halling)
BLOCKS["mentelosii"] = dict(
    cites=[
        c(H1, "size", 80, "盾葉約 80 × 45–70 cm、孢子葉約 60 × 75 cm",
          "盾葉長 80、盾葉寬 45–70（中點 57.5）、孢子葉長 60 → D = 80；作者只檢視了一株",
          "The base fronds are oblong, ca. 80 cm long, 45 cm wide at the base, and 70 cm wide at the apex ... The fertile fronds are several times forked, ca. 60 cm long and 75 cm wide.", "p. 99"),
        c(H1, "shield_form", "erect-lobed", "長橢圓、上部葉狀而離開附著物，上緣不規則分裂成短裂片",
          "上部離開附著物（非貼伏），長橢圓、上緣不規則分裂 → 對應「上半部直立，橢圓形，有多個不等長裂片」；原文沒有寫 erect，是依「free of the substrate」判斷",
          "The base fronds are oblong ... and are apically foliaceous and free of the substrate. Their upper margin is irregularly forked", "p. 99"),
        c(H1, "shield_height", 5, "上部離開附著物，盾葉長約 80 cm", "非貼伏、長度約 80 cm（≥ 80）→ 5",
          "The base fronds are oblong, ca. 80 cm long ... apically foliaceous and free of the substrate.", "p. 99"),
        c(H1, "shield_fringe", "encircling", "芽點周圍的邊緣呈皺褶", "皺褶環繞芽點 → 環繞孢子葉柄",
          "but the margin around the bud is ruffled.", "p. 99"),
        c(H1, "fertile_length", "60 cm", "約 60 cm", "「約 X」視為 X", "The fertile fronds are several times forked, ca. 60 cm long and 75 cm wide.", "p. 99"),
        c(H1, "fertile_split", "≤5", "數回分岔，至約 5 回", "「to ca. 5 times forked」記為 ≤5",
          "The fertile frond to ca. 5 times forked", "p. 100"),
        c(H1, "fertile_width", 5, "孢子囊群寬約 20 cm", "裂片形狀不規則、無法依形狀判定；孢子囊群寬度上限 ≥ 20 cm → 5",
          "There are two broad sporangial patches, each ca. 20cm long and 20 cm wide.", "p. 99"),
        c(H1, "spore", "sinus", "兩個新月形孢子囊群，位於第二回分岔凹處周圍", "around the secondary sinuses → 分岔凹處",
          "The patches are roughly crescent-shaped, irregularly margined, and submarginal, and are situated around the secondary sinuses and extend up into the next fork", "p. 99"),
        c(H1, "origin", "人工雜交：美國佛州邁阿密 Fantastic Gardens 的 Tom Mentelos 育成", "佛州苗圃人工雜交",
          "", "A hybrid of Platycerium has been developed by Mr. Tom Mentelos of Fantastic Gardens, Miami, Florida.", "p. 99"),
        c(HH, "pups", "no", "不像三角鹿角蕨會長側芽", "does not offer volunteers → no",
          "Like its P. superbum parent, the P. x mentelosii does not offer volunteers like the P. stemaria."),
        c(H1, "parents", "stemaria|superbum", "三角 × 巨大", "原始發表", "The parents of this hybrid are P. stemaria (Pal. Beauv.) Desv. and P. superbum Jonch. & Hennipm.", "p. 99"),
    ],
    extra={"parents"},
    desc=[
        ("Tom Mentelos 在美國佛州邁阿密的 Fantastic Gardens 把兩個親本的原葉體交錯種成一排排而得到這個雜交種，Hoshizaki 1975 年發表。", H1,
         "A hybrid of Platycerium has been developed by Mr. Tom Mentelos of Fantastic Gardens, Miami, Florida. ... Mr. Mentelos obtained the hybrid by planting prothalli of the parents in alternate rows.", "p. 99"),
        ("外觀介於雙親之間：和三角鹿角蕨的差別是盾葉上緣分裂，和巨大鹿角蕨的差別是有兩個孢子囊群。", H1,
         "Platycerium X mentelosii can be distinguished from P. stemaria by its lobed rather than entire base fronds and from P. superbum by having two rather than usually one sporangial patch.", "p. 99"),
        ("孢子葉第一回分岔以下的部分寬而呈楔形，各裂片形狀不規則，越往先端越短越窄。", H1,
         "The area of the lamina below the primary fork is wide and wedge-shaped; the lamina divisions are very irregular and mostly become successively shorter and narrower towards the blade apex", "p. 99"),
        ("孢子大多畸形，少數形狀正常，可能是傳聞可以播種的原因；據說孢子苗外觀不一，小時候帶銀色、像巨大鹿角蕨。", H1,
         "Spores produced by this hybrid are greatly distorted, although a few of normal shape may be found; these probably account for the reports of viability of this hybrid. Plants grown from these spores are said to vary in appearance, but when small they are silvery and like P. superbum.", "p. 99"),
    ],
    note=[
        ("依國際栽培植物命名法規，同一篇發表另命名栽培品種 'Fantastic Gardens'。", H1,
         "Therefore, it is necessary to provide a cultivar name as follows: Platycerium mentelosii cv. Fantastic Gardens, Hoshizaki, cv. nov.", "p. 100"),
        ("Halling 認為現在的栽培者可能用別的名稱稱呼它。", HH,
         "Not a lot is known about this cross and today's growers may be calling it something different.", ""),
    ],
    text=dict(growth="單生，不像三角鹿角蕨會長側芽；孢子大多畸形。"),
    searched=searched("Hoshizaki 1975（Amer. Fern J. 65: 99–101，原始發表，archive.org BHL 掃描）|Hoshizaki 1977（Gard. Bull. Singapore 30: 13–15）|Halling 首頁與交種表"
                      "|搜尋：Platycerium × mentelosii Hoshizaki 1975 hybrid stemaria superbum description",
                      "Halling 首頁|搜尋：Platycerium mentelosii care light water growing（只有屬層級通用照護）"),
)

BLOCKS["ridleyi-x-coronarium"] = dict(
    cites=[
        c(PR, "origin", "泰國人工雜交（Ploy-ratana 以混合孢子法育成）", "泰國人工雜交", "",
          "Hybridization between these species was conducted using mix-spore technique.", "摘要"),
        c("halling-mtkitshakood", "fertile_posture", "pendant", "孢子葉下垂", "hanging down → pendant",
          "The fertile fronds hanging down are more a P. coronarium trait."),
        *mo_guide("亞皇", 1, 3),
        c(PR, "parents", "coronarium|ridleyi", "皇冠 × 亞猴", "原始發表（摘要）",
          "Among the four Thai native species, P. coronarium and P. ridleyi are phylogenically sister species according to DNA analysis. Hybridization between these species was conducted", "摘要"),
    ],
    extra={"parents"},
    desc=[
        ("泰國的 Ploy-ratana 以混合孢子法雜交皇冠與亞洲猴腦鹿角蕨，1,000 株移植的孢子苗中有 8 株確認為種間雜交種，命名為 P. × kitshakoodiense。", PR,
         "Hybridization between these species was conducted using mix-spore technique. Among 1,000 transplanted sporelings, 8 plants were identified as interspecific hybrids. ... The hybrid, which was named Platycerium × kitshakoodiense", "摘要"),
        ("F1 的特徵介於雙親之間；幼株產生的孢子沒有活性，產孢兩年後才得到約 50% 有活性的孢子。", PR,
         "The F1 hybrid population showed intermediate characteristics of the parents. ... However, the spores from young plants were non-viable. After producing spore patches for two years, spores with 50% viability were finally attained.", "摘要"),
        ("F2 的盾葉與孢子葉型態出現分離。", PR, "The F2 population showed segregation of shield and fertile fronds.", "摘要"),
        ("Halling 2016 年底從泰國引進，在南加州的溫室長得很好。", "halling-mtkitshakood",
         "I obtained this hybrid from Thailand in late 2016 and it has done very well in my greenhouse in Southern California.", ""),
    ],
    note=[
        ("Halling 認為名稱來自泰國佛教徒朝聖的 Kitchakut 山。", "halling-mtkitshakood",
         "Mt Kitshakood is thought to have derived its name from Mt Kitchakut in Thailand where Thai Buddhists would go to pray.", ""),
    ],
    searched=searched("Ploy-ratana 2014（Acta Hortic. 1025，原始發表，只取得摘要）|Halling MtKitshakood.htm 與交種表"
                      "|搜尋：Platycerium kitshakoodiense ridleyi coronarium hybrid Acta Horticulturae",
                      "微體溫室〈40 種鹿角蕨〉|Halling MtKitshakood.htm|搜尋：Platycerium Mt Kitshakood care light water difficulty（只有屬層級通用照護）"),
)

BLOCKS["charles-alford"] = dict(
    cites=[
        c("halling-charles-alford", "shield_fringe", "encircling", "芽點周圍有皺褶", "frills around the bud → 環繞",
          "The P. charles alford grows a single, raised, flat, triangular lobe with frills around the bud."),
        c("halling-charles-alford", "shield_form", "appressed", "幼株盾葉貼附板子", "描述的是幼株，依「以成熟植株為準」排除",
          "The photo on the right is younger and is reminiscent of P. ridleyi with the shield hugging the mount", "", "excluded"),
        c("halling-charles-alford", "fertile_posture", "up", "幼株孢子葉直立（作者推測之後會下垂）", "描述的是幼株，排除",
          "fertile fronds growing vertical like a P. ridleyi. I assume the spore lobes will develop soon and the fronds will droop down.", "", "excluded"),
    ],
    desc=[
        ("Charles Alford 在 1980 年代中期播種女王鹿角蕨孢子時意外得到，起初被當成女王的芽變。", HH,
         "Mr Charles Alford reports it appeared while sowing P. wandae spore in the mid 1980's. It was thought to be a sport of P. wandae", ""),
        ("栽培數十年後，他認為這是女王與亞洲猴腦鹿角蕨的雜交種。", "halling-charles-alford",
         "But after several decades of establishing the P. charles alford , he has concluded it is a hybrid cross of P. wandae and P. ridleyi.", ""),
        ("較老的植株盾葉像女王，但孢子囊群只有一個，女王則有兩個。", "halling-charles-alford",
         "The photo on the left is aparently an older established P. charles alford with shield fronds like a P. wandae . The spore lobes are singular whereas the P. wandae has two spore patches.", ""),
        ("以它的孢子播種，也長出相同特徵的後代。", "halling-charles-alford",
         "New plants have been grown from P. charles alford spore and the cultivar encompasses the original, and the progeny.", ""),
    ],
    searched=searched("Halling Charles_Alford.htm、首頁與交種表|搜尋：Platycerium 'Charles Alford' wandae ridleyi hybrid care",
                      "Halling Charles_Alford.htm|搜尋：Platycerium 'Charles Alford' wandae ridleyi hybrid care（只有親本種的照護）"),
)

BLOCKS["horne-surprise"] = dict(
    cites=[
        c("halling-alc-mad", "shield_vein", "yes", "盾葉有肋紋（較淺），具非猴的盾葉特徵", "ribs → 葉脈隆起",
          "The shield frond has shallower ribs and the color is lighter green. ... shows the P. madagascarinese shield frond characteristic"),
        c("halling-alc-mad", "fertile_posture", "spread|pendant", "從芽點向外長出，再折向下彎", "grow outward ... curve downward → 展開後下垂",
          "the nature of the fertile fronds to grow outward from the bud and fold over and curve downward while maintaining the initial angle of growth from the bud"),
        c("halling-alc-mad", "fertile_split", "2–3", "一次主要分岔，先端再分岔一兩次", "主分岔 1 次＋近先端 1–2 次 → 2–3",
          "The fertile fronds seem to have a major fork, then one or two smaller forks again near the tip."),
        *mo_guide("非非", 1, 3),
    ],
    desc=[
        ("以佛州的苗圃業者、早期的鹿角蕨專家 Jerry Horn 命名。", HH,
         "Named for Jerry Horn, a nursery man in Florida and was one of the first experts on platyceriums.", ""),
        ("盾葉淺綠色、溝紋較淺；Halling 依顏色認為親本是非洲型圓盾。", "halling-alc-mad",
         "The shield fronds are light green and appear not as deeply grooved. ... When observing the shade of green, it is apparent the P. Horn's Surprise is a cross with the African variety", ""),
        ("Halling 觀察到螞蟻喜歡在它的盾葉中築巢，旁邊的其他種則沒有。", "halling-alc-mad",
         "I have also observed that ants tend to nest in the shield fronds where as other adjacent species are not bothered by the ants.", ""),
    ],
    note=[
        ("Charles Alford 另有一個非猴與圓盾的雜交，他說是反向雜交。", HH,
         "Charles Alford has a hybrid cross of P. madagascariense and P. alcicorne which he says is a reverse cross of the two.", ""),
    ],
    searched=searched("Halling Alcicorne-Madagascariense.htm、首頁與交種表|微體溫室〈圓盾鹿角蕨 10 大品種〉",
                      "微體溫室〈40 種鹿角蕨〉、〈圓盾鹿角蕨 10 大品種〉|Halling Alcicorne-Madagascariense.htm"),
)

BLOCKS["dawboy"] = dict(
    cites=[
        c("halling-dawboy", "shield_vein", "yes", "盾葉有非猴的鬆餅狀網紋", "waffling → yes",
          "The shield fronds defiantly show the P. madagascariense waffling."),
        c("halling-dawboy", "fertile_posture", "up", "孢子葉較長、較直立", "erect → up",
          "The fertile fronds are more P. alcicorne and stand longer and more erect."),
        c("halling-dawboy", "spore", "tips", "孢子囊群在葉先端", "spore patched on the tips → tips",
          "The P. dawboy is characterized by having the dark green, wide fertile fronds with spore patched on the tips."),
        c("halling-dawboy", "humidity", 1, "南加州戶外、濕度約 30% 仍可栽培（觀察）", "栽培者的耐受觀察，不是建議條件 → reference",
          "However Tom Gauci is growing it outside in Southern California, about 5 miles from the beach. The average humidity is probably about 30%.", "", "reference"),
    ],
    desc=[
        ("來自泰國的雜交種，孢子葉深綠、寬。", "halling-dawboy",
         "The Platycerium Dawboy is a new hybrid out of Thailand. ... The P. dawboy is characterized by having the dark green, wide fertile fronds", ""),
        ("植株小，像非猴。", "halling-dawboy", "The plant is small like P. madagascariense .", ""),
        ("孢子囊群的範圍因株而異：有的從裂片上方蓋滿整個葉寬直到離先端約一英寸，有的大多在裂片上方、略超過裂片就停止。", "halling-dawboy",
         "the spore patch covers the full width of the frond from above the lobe to about 1 inch from the tip. Other P. dawboy photos show the spore patch mostly above the lobe and stopping just beyond the lobe.", ""),
    ],
    note=[
        ("泰國的 Siam Exotica 說親本是非猴與非洲型圓盾 'Vassei'；Halling 依深綠色認為是馬達加斯加型圓盾。", HH,
         "Siam Exotica states the P. dawboy is a cross of P. madagascariense and the African form P. alcicorne 'Vassei' but my observations suggest it is crossed with the Madagascar P. alcicorne.", ""),
    ],
    searched=searched("Halling Dawboy.htm、Alcicorne-Madagascariense.htm、首頁與交種表|阿金商品頁",
                      "Halling Dawboy.htm|阿金商品頁（只有屬層級通用照護）"),
)

BLOCKS["larry-weed"] = dict(
    cites=[
        c(HH, "shield_vein", "yes", "盾葉有非猴典型的深溝紋", "deep folds → yes",
          "The shield fronds appear to be the typical P. madagascariense form with the deep folds."),
        c(HH, "fertile_hair", 1, "孢子葉較寬、蠟質、葉脈明顯", "waxy → 1", "The fertile frond is wider, waxy like with pronounced veins."),
    ],
    desc=[
        ("Charles Alford 育成的圓盾與非猴雜交。", HH, "is also a cross of the P. alcicorne and P. madagascariense created by Charles Alford.", ""),
        ("顏色深綠，Halling 認為親本是馬達加斯加型圓盾。", HH,
         "It appears to be the Madagascar form of the P. alcicorne. ... The color is also dark green, typical of the P. alcicorne from Madagascar.", ""),
    ],
    note=[
        ("Halling 指出它和 Dawboy 很像，若是同一植物，需依命名先後決定名稱。", "halling-alc-mad",
         "Charles Alford also has a cross of P. alcicorne and P. madagascariense that's been named P. Larry Weed and it is similar to the P. Dawboy photo above. If they are the same, it needs to be resolved which name should be used, based upon who came first.", ""),
    ],
    searched=searched("Halling 首頁、Alcicorne-Madagascariense.htm 與交種表", "Halling 首頁與 Alcicorne-Madagascariense.htm（沒有照護資料）"),
)

BLOCKS["callard"] = dict(
    cites=[],
    desc=[
        ("佛州栽培家 Charles Alford 育成，以聖地牙哥蕨類協會前會長 Don Callard 命名。", "halling-callard",
         "Charles Alfred, a prominent grower in Florida created this cross and named it after Don Callard, former president of the San Diego Fern Society.", ""),
        ("孢子葉寬、會分岔；盾葉高而窄。", "halling-callard",
         "the quadridichotomum trait is obvious in the fertile fronds with the wide frond and the forking. ... The andinum is also apparent in the fertile fronds plus the tall narrow shield frond", ""),
    ],
    note=[
        ("Halling 把親本寫成安地斯與「可能是」四叉。", "halling-callard", "(P. andinum and probably P. quadridichotomum)", ""),
    ],
    searched=searched("Halling Callard.htm、首頁與交種表", "Halling Callard.htm（沒有照護資料）"),
)

BLOCKS["roy-vail"] = dict(
    cites=[
        c(HH, "shield_vein", "yes", "盾葉有非猴的鬆餅狀網紋", "waffled → yes", "The shield fronds are waffled like the P. madagascariense , but tall and narrow like the P. andinum ."),
    ],
    desc=[
        ("出自 Charles Alford 的園子，以第一本鹿角蕨專書《Hobbyist's Handbook》的作者 Roy Vail 命名。", HH,
         "From the gardens of Charles Alford. Obviously named after Roy Vail, author of the first bible on platyceriums, \" Hobbyist's Handbook \"", ""),
        ("盾葉高而窄；孢子葉寬、會分岔且較長；Halling 撰文時尚未長出孢子囊群。", HH,
         "The shield fronds are waffled like the P. madagascariense , but tall and narrow like the P. andinum . The fertile fronds are wide and forked like the P. madagascariense yet longer like the P. andinum. This plant has not grown spore patches yet.", ""),
    ],
    searched=searched("Halling 首頁與交種表", "Halling 首頁（沒有照護資料）"),
)

BLOCKS["hillii-x-willinckii"] = dict(
    cites=[
        c("halling-yanid", "fertile_posture", "pendant", "孢子葉從芽點側向長出後下垂", "hangs down → pendant",
          "the fertile fronds are growing out from the bud in an edgewise manor. Then hangs down in a ratty manor."),
        c("halling-yanid", "min_temp", 0, "Woodside 冬季常短暫低於冰點，大型植株仍存活", "耐受紀錄，不是建議值 → reference",
          "In Woodside the temperature frequently frequently drops below freezing for short periods during the winter ... One reason they have survived is the large root ball", "", "reference"),
    ],
    desc=[
        ("Halling 記錄加州 Filoli Garden 的一批大型植株，至少 50 年、可能上百年。", "halling-yanid",
         "The plant above is at least 50 years old, and possibly 100 years old. It is hanging along with a dozen more large examples at the Filoli Garden in Woodside CA.", ""),
        ("盾葉圓、不高也不深裂，向內長成球狀。", "halling-yanid",
         "the shield fronds are rounded and not tall and deeply lobed. ... the plant shield fronds form a ball like Platycerium hillii", ""),
        ("園丁把盾葉上緣剪開讓雨水流入，多餘的水似乎沒有傷害植株。", "halling-yanid",
         "The gardeners have opened up the ball to allow rain water to freely enter the plant. The fact excess water does not appear to harm the plant", ""),
    ],
    note=[
        ("Halling 依外形推斷這批植株是爪哇與深綠的雜交，稱為 'Yanid'；它們早於交種流行的年代，可能是自然雜交。", HH,
         "today is called a hybrid whereas the pictured individual dates back before hybrids were popular and may have occurred naturally", ""),
    ],
    searched=searched("Halling Yanid.htm、首頁與交種表", "Halling Yanid.htm（只有耐寒觀察）"),
)

BLOCKS["siamense"] = dict(
    cites=[
        c(HH, "pups", "yes", "推測會長側芽", "作者寫「we can assume」，屬推測 → excluded",
          "Little is known about this cultivar, but we can assume it likes a warm climate between 60°F and 90°F and it grows pups.", "", "excluded"),
    ],
    desc=[
        ("盾葉巨大如象耳，孢子葉寬而深裂。", HH,
         "Grows massive shield fronds like the P. elephantotis and wide fertile fronds, only deeply branched like the P. willinckii.", ""),
    ],
    note=[
        ("Halling 指出寬的孢子葉與盾葉形狀也有深綠的特徵。", HH,
         "One could argue that there are traits of P. hillii with the wide fronds and shape of the shield fronds.", ""),
    ],
    searched=searched("Halling 首頁與交種表（Silver_Velvet.htm 已失效）|搜尋：Platycerium × siamense elephantotis willinckii hybrid new nothospecies",
                      "Halling 首頁（只有推測）|搜尋：Platycerium 'Silver Velvet' siamense elephantotis willinckii care（只有親本種的照護）"),
)

BLOCKS["majus"] = dict(
    cites=[
        c(HH, "fertile_posture", "up", "孢子葉強烈直立", "strongly erect → up",
          "It is a fairly large growing staghorn with a growth habit similar to P. veitchii with strongly erect fertile fronds."),
    ],
    desc=[
        ("相當大型，生長習性像銀鹿。", HH, "It is a fairly large growing staghorn with a growth habit similar to P. veitchii", ""),
        ("盾葉分裂，但沒有銀鹿那樣的長裂片。", HH, "The shields are lobed, but do not exhibit the long divisions of true P. veitchii .", ""),
    ],
    note=[
        ("過去稱為 P. alcicorne 'Majus'，Halling 認為這個名稱有誤導，它源自澳洲而不屬於圓盾。", HH,
         "is clearly of Australian origin and not within the P. alcicorne species. The improper name P. alcicorne Majus formerly used is very misleading", ""),
        ("Charles Alford 認為可能是二叉複合群內的雜交，或許是銀鹿 × 深綠。", HH,
         "Charles Alford believes it is probably a hybrid within the bifurcatum compex, possibly P. vietchii x P. hillii", ""),
    ],
    searched=searched("Halling 首頁與交種表", "Halling 首頁（作者寫不確定 Majus 喜歡的光照）"),
)

BLOCKS["hillii-x-bifurcatum"] = dict(
    cites=[],
    desc=[
        ("孢子葉寬、盾葉圓，Halling 認為可能比一般鹿角蕨大。", HH,
         "The fertile fronds are wide like P. hillii, and the shield fronds are round like P. hillii. ... The P. diversifolium may be a larger than average platycerium.", ""),
    ],
    note=[
        ("Halling 把園藝上的 'Diversifolium' 記為二叉與深綠的雜交。", HH, "P. diversifolium hybrid is a cross of P. bifurcatum and P. hillii .", ""),
        ("專著中的 P. diversifolium Bonap. 是愛麗絲鹿角蕨的異名，和這個交種不同。", "hennipman1982",
         "Platycerium diversifolium Bonap., Notes Pterid. 4 (1917) 84. - P. ellisii Baker var. diversifolium C. Chr.", "p. 98"),
    ],
    searched=searched("Halling 首頁與交種表|Hennipman & Roos 1982（P. diversifolium Bonap. 為 P. ellisii 的異名，非此交種）", "Halling 首頁（沒有照護資料）"),
)

BLOCKS["electrofilia"] = dict(
    cites=[],
    desc=[
        ("二叉與銀鹿的雜交，由泰國 Siam Exotica 繁殖。", HH, "hybrid is a cross between P. bifurcatum and P. veitchii and propagated by Siam Exotica in Thailand", ""),
        ("阿金說孢子葉分岔的邊緣有滾邊，並改善了銀鹿生長慢的問題。", "ajins-veitchii-x-bifurcatum",
         "除了改善銀鹿生長速度慢的情況，白毛也是必須的！板植盆種都非常美的二叉銀，孢子葉分岔的邊緣有滾邊是一大特色", ""),
    ],
    searched=searched("Halling 首頁與交種表|阿金〈二叉銀〉商品頁", "Halling 首頁|阿金〈二叉銀〉商品頁（只有屬層級通用照護）"),
)

BLOCKS["veitchii-x-willinckii"] = dict(
    cites=[
        c("halling-hybrid-index", "parents", "veitchii|willinckii", "爪哇 × 銀鹿（'Silver Fond'）", "交種表第 15 列", "15 | 'Silver Fond' | Willlinckii | Veitchii"),
    ],
    extra={"parents"},
    searched=searched("Halling 交種表（只有親本）", "Halling 交種表（沒有照護資料）"),
)

BLOCKS["bifurcatum-mt-lewis"] = dict(
    cites=[
        c(HY, "origin", "澳洲 Mount Lewis", "澳洲 Mount Lewis", "取自論文標題；摘要未寫分布", "The Platycerium Variant from Mount Lewis, Australia", "標題"),
        c("halling-mtlewis", "light", 5, "原生地與銀鹿並排生長在全日照下（影片）", "原生地觀察 → reference",
          "show a Veitchii and Mt Lewis growing side by side in full sun. P. Mt Lewis should take a lot of sun, similar to P. veitchii and P. superbums .", "", "reference"),
    ],
    desc=[
        ("Hoshizaki & Yansura 2021 指出，栽培界的 'Mount Lewis' 就是早期的栽培品種 'Venose Frond'，後來又被稱為 P. willinckii var. venosum。", HY,
         "The Platycerium plants circulating amongst hobbyists and growers under the common name Platycerium ‘Mount Lewis' is the same plant as the cultivar known as Platycerium ‘Venose Frond’, or, as it was later called, Platycerium willinckii var. venosum.", "摘要"),
        ("它的主脈隆起，這點和 1915 年發表的 P. bifurcatum var. lanciferum 相同。", HY,
         "This plant also shares the trait of raised major veins with P. bifurcatum var. lanciferum , described in 1915.", "摘要"),
        ("盾葉向外長，像傘一樣替孢子葉遮陰；孢子葉有寬葉與窄葉兩型。", "halling-mtlewis",
         "the shield fronds grow outward forming a shade umbrella for fertile fronds. ... The P. Mt Lewis on the left is described as a broad frond P. Mt Lewis . The photo on the right is a narrow frond M. Mt Lewis.", ""),
    ],
    note=[
        ("Hoshizaki & Yansura 2021 依形態與分子比較，認定它是二叉鹿角蕨的變異。", HY,
         "Morphological and molecular comparisons of this plant were made with members of the P. bifurcatum complex ... We conclude that Platycerium ‘Mount Lewis’ is a variant of P. bifurcatum.", "摘要"),
        ("Halling 則寫「目前看法」是爪哇的栽培品種。", "halling-mtlewis",
         "The P. Mt Lewis was listed as a unique species, but current thought is the P. Mt Lewis is a cultivar of the P. willinckii species.", ""),
    ],
    searched=searched("Hoshizaki & Yansura 2021（只取得摘要）|Halling MtLewis.htm",
                      "Halling MtLewis.htm（只有原生地觀察）"),
)

# ---------------------------------------------------------------- batch 1: hybrids with Taiwan sources only (微體溫室)
EL = "象耳鹿角蕨 8 品種照顧圖鑑"
BLOCKS["erawan"] = dict(
    cites=[
        mo_rate("mo-elephant", "非猴象耳鹿角蕨（非象）", "中等", EL),
        c("mo-elephant", "shield_vein", "yes", "營養葉有凹紋", "", "非猴象耳鹿角蕨（非象）｜葉脈浮凸明顯　營養葉有凹紋"),
        c("halling-hybrid-index", "parents", "elephantotis|madagascariense", "象耳 × 非猴", "交種表第 7 列", "7 | 'Erawan' | Elephantotis | Madagascariense"),
    ],
    extra={"parents"},
    desc=[("孢子葉葉脈浮凸明顯，營養葉有凹紋。", "mo-elephant", "非猴象耳鹿角蕨（非象）｜葉脈浮凸明顯　營養葉有凹紋", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉|Halling 交種表", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["neptune"] = dict(
    cites=[
        mo_rate("mo-elephant", "三角象鹿角蕨（白象）", "中偏易", EL),
        c("mo-elephant", "fertile_hair", 3, "表面白毛明顯", "白毛明顯 → 3", "三角象鹿角蕨（白象）｜表面白毛明顯　葉型呈長三角"),
    ],
    desc=[("孢子葉長三角形，表面白毛明顯。", "mo-elephant", "三角象鹿角蕨（白象）｜表面白毛明顯　葉型呈長三角", "")],
    note=[("Halling 交種表把象耳 × 三角列為 'Luaentii'，交叉表則寫 'Neptune'。", "halling-hybrid-index",
           "10 | 'Luaentii' | Elephantotis | Stamaria ... Elephantotis | ... | 'Neptune'", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉|Halling 交種表", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["antis"] = dict(
    cites=[
        mo_rate("mo-elephant", "安地斯象耳鹿角蕨（安象）", "中偏易", EL),
        c("mo-elephant", "fertile_hair", 3, "表面白毛明顯", "白毛明顯 → 3", "安地斯象耳鹿角蕨（安象）｜表面白毛明顯　葉脈也呈白色"),
    ],
    desc=[("孢子葉表面白毛明顯，葉脈也呈白色。", "mo-elephant", "安地斯象耳鹿角蕨（安象）｜表面白毛明顯　葉脈也呈白色", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["burirom"] = dict(
    cites=[mo_rate("mo-elephant", "愛麗絲象耳鹿角蕨（愛象）", "中偏易", EL)],
    desc=[("孢子葉多層次生長，末端呈波浪緣。", "mo-elephant", "愛麗絲象耳鹿角蕨（愛象）｜多層次葉生長　末端呈波浪緣", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉|Halling 交種表（象耳 × 愛麗絲列為 No name yet）", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["alcicorne-x-elephantotis"] = dict(
    cites=[mo_rate("mo-elephant", "馬圓象耳鹿角蕨（馬圓象）", "容易", EL)],
    desc=[("孢子葉寬大，末端呈波浪狀。", "mo-alcicorne", "馬圓象鹿角蕨｜馬圓X象耳｜孢子葉寬大　末端波浪狀", "")],
    note=[("微體溫室另列有非洲型圓盾 × 象耳的「非圓象」，孢子葉寬大、營養葉冠明顯。", "mo-alcicorne", "非圓象鹿角蕨｜非圓X象耳｜孢子葉寬大　營養葉冠明顯", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉、〈圓盾鹿角蕨 10 大品種〉", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["grande-x-elephantotis"] = dict(
    cites=[mo_rate("mo-elephant", "巨獸象耳鹿角蕨（巨象）", "中偏易", EL)],
    desc=[("是這系列中整體最巨大者，孢子葉呈長橢圓。", "mo-elephant", "巨獸象耳鹿角蕨（巨象）｜整體最為巨大　葉型呈長橢圓", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["moose"] = dict(
    cites=[*mo_guide("駝鹿", 1, 1)],
    desc=[("孢子葉分岔多，像駝鹿角般展開。", "mo-alcicorne", "駝鹿鹿角蕨｜非圓X深綠｜孢子葉分叉多　如駝鹿角展開", "")],
    searched=searched("微體溫室〈圓盾鹿角蕨 10 大品種〉", "微體溫室〈40 種鹿角蕨〉"),
)

# ---------------------------------------------------------------- batch 1: named hybrids and selections with Taiwan / vendor care sources
MOS = "微體溫室〈40 種鹿角蕨〉"
BLOCKS["pegasus"] = dict(
    cites=[
        *mo_guide("飛馬", 3, 5),
        c("mo-pegasus", "difficulty", 1, "相當推薦新手", "", "飛馬鹿角蕨是相當推薦新手的鹿角蕨品種"),
        c("mo-pegasus", "light", "3–5", "半日照至全日照", "半日照 3、全日照 5 → 3–5",
          "從半日照至全日照的環境皆能養護"),
        c("mo-pegasus", "water", 1, "較耐旱，水苔接近全乾再澆透", "耐旱 → 1",
          "可等到水苔接近全乾再一次澆透 ... 與檸檬鹿角蕨同屬較耐旱的園藝種"),
    ],
    desc=[
        ("同時有爪哇的高冠、二叉的翠綠折手與深綠的明顯脈紋，整體對稱如飛馬展翅。", "mo-pegasus",
         "外觀上分別擁有：爪哇鹿角蕨的典型高冠、二叉鹿角蕨的翠綠折手、以及深綠鹿角蕨的顯眼脈紋，整體對稱的造型宛如飛馬展翅一般", ""),
        ("成株的孢子葉先向上長再折下。", "mo-pegasus", "上板成株｜孢子葉向上長後折下", ""),
    ],
    searched=searched("微體溫室〈飛馬鹿角蕨〉", f"{MOS}|微體溫室〈飛馬鹿角蕨〉"),
)
for pid, zh, d, l in [("pewchan", "皮陳", 3, 5), ("white-hawk", "白霍克", 3, 5), ("white-shine", "白帥帥", 3, 5),
                      ("monkey-north", "北猴", 5, 5), ("ss-foong", "千手觀音", 3, 3)]:
    BLOCKS[pid] = dict(cites=[*mo_guide(zh, d, l)], searched=searched(MOS, MOS))
BLOCKS["polar-bear"] = dict(
    cites=[
        *mo_guide("北極熊", 3, 5),
        c("ajins-polar-bear", "fertile_hair", 5, "雪白絨毛非常濃密", "濃密白毛 → 5",
          "最大的特色，在於那層乾淨柔和的雪白絨毛，非常濃密，猶如糖霜一般。"),
    ],
    desc=[("北極熊是從 OMO 精選出來的緊湊型個體。", "ajins-polar-bear", "北極熊更是精選出來緊湊型的個體", "")],
    searched=searched(f"{MOS}|阿金〈白色戀人／北極熊〉商品頁", f"{MOS}|阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["white-lover"] = dict(
    cites=[c("ajins-polar-bear", "fertile_hair", 5, "孢子葉面厚厚一層白色絨毛，極致銀白", "濃密白毛 → 5",
             "OMO孢子葉面厚厚一層白色絨毛，呈現極致的銀白色")],
    desc=[("孢子葉面覆一層厚白絨毛，呈銀白色；隨植株成熟葉片會變得寬白狂野。", "ajins-polar-bear",
           "OMO孢子葉面厚厚一層白色絨毛，呈現極致的銀白色 ... 隨著植株成熟，葉片會逐漸展現寬白狂野的型態", "")],
    searched=searched("阿金〈白色戀人／北極熊〉商品頁", "阿金商品頁（只有屬層級通用照護）"),
)

FSQ = "mo-foongsiqi"
BLOCKS["foong-si-qi"] = dict(
    cites=[
        *mo_guide("捲捲鹿", 3, 3),
        c(FSQ, "difficulty", 1, "相對好照顧", "", "是相對好照顧的鹿角蕨品種之一"),
        c(FSQ, "light", "3–5", "成株中光至中強光", "中光 3、中強光 5 → 3–5", "上板成株 ... 1. 中光至中強光"),
        c(FSQ, "water", 1, "本身耐旱，乾濕容忍力強", "耐旱 → 1", "捲捲鹿角蕨和深綠鹿角蕨一樣對於環境乾溼度容忍力強 ... 雖然捲捲鹿角蕨本身耐旱"),
        c(FSQ, "min_temp", 5, "低於 5 度可能寒害", "受害溫度，不是建議值 → reference", "若低於 5 度則有可能發生寒害", "", "reference"),
        c(FSQ, "size", "~80", "成熟植株直徑 60–100 cm", "株徑中點 80；不是盾葉或孢子葉尺寸 → 寬鬆說法（v1.4）", "成熟植株直徑可達 60~100 公分"),
        c(FSQ, "fertile_length", "50–80 cm", "3 年以上成株手長 50–80 cm", "", "3 年以上完全成熟體的捲捲鹿角蕨孢子葉手長可達 50~80 公分"),
        c(FSQ, "pups", "yes", "多芽型", "", "捲捲鹿屬於多芽型鹿角蕨"),
        c("rff-foongsiqi", "light", 3, "需要明亮濾光，避免直曬", "bright filtered → 3", "Bright filtered light essential; avoid direct sun which causes scorching"),
        c("rff-foongsiqi", "water", 1, "澆透後讓介質乾約 80%", "drying between waterings → 1", "Water thoroughly then allow to dry significantly between waterings (about 80%)"),
        c("rff-foongsiqi", "min_temp", 12.8, "保持 55 °F 以上", "55 °F = 12.8 °C；建議值", "Keep above 55°F minimum; protect from frost at all costs"),
        c("rff-foongsiqi", "difficulty", 3, "適合中階栽培者", "美國來源，只供參考", "making it a rewarding project for the intermediate grower", "", "reference"),
        c("rff-foongsiqi", "spore", "tips", "孢子長在孢子葉先端", "", "As the plant matures and produces spores at the tips of these fronds, they begin to curl"),
        c("jl-foong-siqi-qq", "difficulty", 1, "不難照顧（組培 QQ）", "德國來源，只供參考", "'Foong SiQi QQ' grows relatively quickly and is not difficult to care for.", "", "reference"),
    ],
    desc=[
        ("最大特色是孢子葉末端 360 度捲曲，葉面覆白毛、葉脈清晰。", FSQ, "最大特色是 360 度捲曲的孢子葉末端，葉面如檸檬鹿角蕨覆白毛且葉脈清晰", ""),
        ("孢子葉要到性成熟、長出孢子囊時才會捲，通常需 1~2 年；幼苗期像二叉鹿角蕨，直分岔、翠綠。", FSQ,
         "此時捲捲鹿角蕨的孢子葉尚未成熟，其型態類似二叉鹿角蕨，具有直分叉且葉色呈翠綠。當達到性成熟階段時，孢子囊的快速生長才會造成孢子葉末端向內反捲", ""),
        ("孢子苗可能失去捲葉性狀，側芽則能保留母株特徵。", FSQ, "相對側芽是從母株上無性繁殖出的個體，基因上幾乎 100% 完美遺傳捲捲鹿角蕨的特徵", ""),
    ],
    note=[
        ("Jungle Leaves 寫它以馬來西亞育種家 SS Foong 的女兒 Si Qi 命名。", "jl-foong-siqi-qq",
         "This staghorn fern is named after Si Qi, the daughter of the Malaysian Platycerium breeder SS Foong.", ""),
        ("Rainforest Flora 則寫馬來西亞的 Mr. Foong 2014-04-20 在 Facebook 發表，以孫女命名。", "rff-foongsiqi",
         "first introduced this cultivar on Facebook on April 20, 2014 ... named this beautiful plant after his granddaughter", ""),
        ("微體溫室寫它由泰國的培育家馮詩琪選育，與其他來源不同。", FSQ, "一般大家所熟知的是由泰國知名鹿角蕨培育家-馮詩琪所精心選育出來", ""),
        ("「FSQ」在育種者 Wanna 的型錄裡指本品種的孢子苗系，和無性繁殖的「Foongsiqi Original」分開列（見 FSQ 條目）。", "wanna-cat-2022-11",
         "No.13 P. Foongsiqi Original ... No.20 P. Ivory (FSQ)", ""),
        ("晴花鹿苑則把 FSQ 當成本品種的別名，市面上標 FSQ 的植株可能是原品種也可能是孢子苗。", "haruhana-usa-sazanami",
         "derived from hand-selected Platycerium 'Foong Siqi' (FSQ) sporelings", ""),
    ],
    searched=searched("微體溫室〈捲捲鹿〉|Rainforest Flora 商品頁|Jungle Leaves 商品頁",
                      f"{MOS}|微體溫室〈捲捲鹿〉|Rainforest Flora 商品頁|Jungle Leaves 商品頁"),
)
BLOCKS["geisha"] = dict(
    cites=[
        c("rff-geisha", "light", 3, "需要明亮濾光，避免直曬", "bright filtered → 3", "Bright filtered light essential; avoid direct sun which causes scorching"),
        c("rff-geisha", "water", 1, "澆透後讓介質乾約 60–80%", "drying between waterings → 1", "Water thoroughly then allow to dry significantly between waterings (about 60-80%)"),
        c("rff-geisha", "min_temp", 12.8, "保持 55 °F 以上", "55 °F = 12.8 °C；建議值", "Keep above 55°F minimum; protect from frost at all costs"),
        c("rff-geisha", "difficulty", 1, "容易栽培", "美國來源，只供參考", "Easy to Grow", "", "reference"),
        c("rff-geisha", "pups", "yes", "多芽（叢生）", "", "As a \"multi-eyed\" (clumping) staghorn, it will produce multiple growing points over time"),
        c("ajins-geisha", "fertile_hair", 5, "厚實的白毛", "厚白毛 → 5", "厚實的白毛，明顯的脈紋"),
    ],
    desc=[("孢子葉寬、不會長得太長。", "rff-geisha", "Its fertile fronds are broad and do not grow excessively long", "")],
    note=[
        ("Rainforest Flora 寫它是深綠鹿角蕨的栽培品種。", "rff-geisha", "This rare and captivating staghorn fern is a cultivar of Platycerium hillii", ""),
        ("阿金則寫它是從捲捲鹿孢子苗層層篩選出來的個體。", "ajins-geisha", "從捲捲鹿孢子苗層層篩選，精心雕琢出這麼一個個體", ""),
    ],
    searched=searched("Rainforest Flora 商品頁|阿金商品頁", "Rainforest Flora 商品頁|阿金商品頁"),
)

MOON = "月亮系列鹿角蕨雖品系眾多，然而因同屬爪哇鹿角蕨的交種或園藝變種，因此照顧上卻有許多相似之處：充足日照、耐旱喜透氣、澆透不積水"
MOONT = "月光、藍月、黃月鹿角蕨有何不同？5 種月亮系列"


def moon_water(name):
    return c("mo-moon", "water", 1, "月亮系列：耐旱喜透氣", f"文章說月亮系列（含{name}）照顧相似、耐旱 → 1", MOON)


BLOCKS["willinckii-moonlight"] = dict(
    cites=[*mo_guide("月光", 5, 3), mo_rate("mo-moon", "月光鹿角蕨", "中偏易", MOONT), moon_water("月光")],
    desc=[("帶狀孢子葉柔美下垂，日照充足時葉面更白、營養葉高冠更聳立。", "mo-moon",
           "帶狀柔美的孢子葉如月光傾瀉而下，在日照充足下葉面會更顯皎白，營養葉高冠也會更加聳立", "")],
    searched=searched("微體溫室〈月亮系列〉|晴花鹿苑商品頁", f"{MOS}|微體溫室〈月亮系列〉"),
)
BLOCKS["new-moon"] = dict(
    cites=[mo_rate("mo-moon", "新月鹿角蕨", "中偏易", MOONT), moon_water("新月")],
    desc=[("和月光相比，孢子葉白色脈紋更突出、分岔數多。", "mo-moon", "新月鹿角蕨手手的白色脈紋更突出、且分叉數多", "")],
    note=[("微體溫室把它寫成爪哇鹿角蕨的栽培品種 P. willinckii cv. 'New Moon'。", "mo-moon", "4. 新月鹿角蕨 (P. willinckii cv. ‘New Moon’)", "")],
    searched=searched("微體溫室〈月亮系列〉", "微體溫室〈月亮系列〉"),
)
BLOCKS["willinckii-yellow-moon"] = dict(
    cites=[
        mo_rate("mo-moon", "黃月鹿角蕨", "中等", MOONT), moon_water("黃月"),
        c("mo-moon", "light", 3, "不直曬，4~8 小時半日照、明亮散射光", "半日照 → 3",
          "黃月鹿角蕨建議不要直曬太陽，適合 4~8 小時半日照環境，明亮散射光為佳"),
    ],
    desc=[
        ("孢子葉微黃白皙，指尖微翹。", "mo-moon", "微黃白皙的鹿手搭上誘人微翹的指尖", ""),
        ("孢子苗個體之間變異大，衍生出侏儒黃月等交種與變異種。", "mo-moon",
         "黃月鹿角蕨還有一個極大的魅力是孢子苗個體間的變異性大 ... 由此衍生出的交種與變異種（如：侏儒黃月）", ""),
    ],
    searched=searched("微體溫室〈月亮系列〉", "微體溫室〈月亮系列〉"),
)
BLOCKS["blue-moon"] = dict(
    cites=[mo_rate("mo-moon", "藍月鹿角蕨", "中等", MOONT), moon_water("藍月")],
    desc=[("孢子葉銀白帶藍，比黃月寬，末端細小分岔多；部分個體有白色葉脈紋。", "mo-moon",
           "藍月鹿角蕨最大的特色是銀白帶藍的孢子葉，相較黃月鹿角蕨的手更寬，而且葉尾末端的細小分叉多 ... 藍月鹿角蕨部分個體擁有葉脈白紋", "")],
    note=[("微體溫室把它寫成爪哇鹿角蕨的栽培品種 P. willinckii cv. 'Blue Moon'。", "mo-moon", "2. 藍月鹿角蕨 (P. willinckii cv. ‘Blue Moon’)", "")],
    searched=searched("微體溫室〈月亮系列〉", "微體溫室〈月亮系列〉"),
)
BLOCKS["snow-moon"] = dict(
    cites=[
        mo_rate("mo-moon", "雪月鹿角蕨", "中等", MOONT), moon_water("雪月"),
        c("mo-moon", "fertile_posture", "spread|pendant", "孢子葉向外延伸再下垂", "", "如同飛馬鹿角蕨的孢子葉向外延伸再下垂"),
    ],
    desc=[("白毛厚實。", "mo-moon", "雪月鹿角蕨第一眼看到感覺神似知名的雪后鹿角蕨，兩者同樣擁有厚實白毛", "")],
    note=[("微體溫室指出雪月有不同的培育品系，例如泰國 Wanna 與台灣培育的版本。", "mo-moon",
           "雪月鹿角蕨其實有不同的培育品系，像是有泰國 Wanna 或是台灣培育的版本", "")],
    searched=searched("微體溫室〈月亮系列〉", "微體溫室〈月亮系列〉"),
)

DW = "侏儒鹿角蕨品種有幾種？11 種侏儒鹿角蕨照顧難度圖鑑"
BLOCKS["willinckii-jade-girl"] = dict(
    cites=[
        *mo_guide("玉女", 5, 3), mo_rate("mo-dwarf", "玉女鹿角蕨", "中等", DW),
        c("mo-dwarf", "light", 3, "半遮陰陽台（明亮散射光）", "明亮散射光 → 3", "半遮陰陽台｜9,000~12,000 lux（明亮散射光）｜玉女鹿角蕨"),
        c("jl-jade-girl", "fertile_length", "15 cm", "約 15 cm（很老的植株 20 cm）", "", "The fronds only reach about 15 cm in length, or 20 cm in very old plants"),
        c("jl-jade-girl", "fertile_hair", 5, "密覆白色分枝毛，呈粉狀", "densely covered with white hairs → 5；T3", "They are densely covered with white, branched hairs, giving them a powdery appearance."),
        c("jl-jade-girl", "pups", "yes", "數年後長成密叢", "", "it forms a dense clump after a few years"),
        c("jl-jade-girl", "difficulty", 1, "生長慢但不難照顧", "德國來源，只供參考", "'Jade Girl' grows slowly but is not difficult to care for.", "", "reference"),
    ],
    desc=[
        ("孢子葉厚、呈銀白，分岔不規則。", "mo-dwarf", "玉女鹿角蕨｜中等｜1. 孢子葉厚呈銀白 2. 孢子葉分叉不規則", ""),
        ("微體溫室說它本身栽培難度不算特別高，但價格較高，適合有經驗的人。", "mo-guide", "玉女鹿角蕨：珍稀侏儒鹿角蕨品種，本身栽培難度不算特別高，但價格較高昂適合有栽培經驗的老手。", ""),
    ],
    searched=searched("微體溫室〈侏儒鹿角蕨〉|Jungle Leaves 商品頁", f"{MOS}|微體溫室〈侏儒鹿角蕨〉|Jungle Leaves 商品頁"),
)
BLOCKS["omg"] = dict(
    cites=[
        *mo_guide("OMG ", 5, 3), mo_rate("mo-dwarf", "OMG 鹿角蕨", "中等", DW),
        c("mo-dwarf", "light", 3, "半遮陰陽台（明亮散射光）", "明亮散射光 → 3", "半遮陰陽台｜9,000~12,000 lux（明亮散射光）｜OMG 鹿角蕨"),
    ],
    desc=[("孢子葉短分岔、整體呈扇形，成熟後葉背呈橘紅。", "mo-dwarf", "OMG 鹿角蕨｜中等｜1. 孢子葉呈短分叉 2. 整體孢子葉呈扇形 3. 成熟孢子葉背呈橘紅", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉", f"{MOS}|微體溫室〈侏儒鹿角蕨〉"),
)
BLOCKS["willinckii-bacteria"] = dict(
    cites=[
        *mo_guide("細菌", 5, 1), mo_rate("mo-dwarf", "細菌鹿角蕨", "中偏難", DW),
        c("jl-bacteria", "fertile_length", "10 cm", "約 10 cm（很老的植株 15 cm）", "", "The fronds only reach about 10 cm in length, or 15 cm in very old plants"),
        c("jl-bacteria", "fertile_hair", 5, "密覆白色分枝毛，呈粉狀", "densely covered with white hairs → 5；T3", "They are densely covered with white, branched hairs, giving them a powdery appearance."),
        c("jl-bacteria", "pups", "yes", "數年後長成密叢", "", "it forms a dense clump after a few years"),
        c("jl-bacteria", "difficulty", 1, "生長慢但不難照顧", "德國來源，只供參考", "'Bacteria' grows slowly but is not difficult to care for.", "", "reference"),
    ],
    desc=[
        ("孢子葉暗綠覆白毛，整體嬌小。", "mo-dwarf", "細菌鹿角蕨｜中偏難｜1. 孢子葉呈暗綠覆白毛 2. 整體型態嬌小", ""),
        ("微體溫室說它適合弱光環境或燈養，較適合有育苗經驗的人。", "mo-guide", "細菌鹿角蕨：同為侏儒鹿角蕨品種，適合生長於弱光環境（或燈養），相對適合有育苗經驗的栽培玩家。", ""),
    ],
    searched=searched("微體溫室〈侏儒鹿角蕨〉|Jungle Leaves 商品頁", f"{MOS}|微體溫室〈侏儒鹿角蕨〉|Jungle Leaves 商品頁"),
)
BLOCKS["willinckii-golden-boy"] = dict(
    cites=[*mo_guide("金童", 5, 1), mo_rate("mo-dwarf", "金童鹿角蕨", "難", DW)],
    desc=[("孢子葉銀黃、排列緊密叢生，分岔細長。", "mo-dwarf", "金童鹿角蕨｜難｜1. 孢子葉呈銀黃 2. 孢子葉序緊密叢生 3. 孢子葉分叉細長", "")],
    note=[("與珍妮、鉑金並列交易金額上百萬元的鹿角蕨。", "mo-expensive", "除了珍妮鹿角蕨、金童鹿角蕨、鉑金鹿角蕨等創下上百萬元交易金額的最貴鹿角蕨品種", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉、〈鹿角蕨為什麼那麼貴〉|商業周刊報導", f"{MOS}|微體溫室〈侏儒鹿角蕨〉"),
)
BLOCKS["willinckii-jenny"] = dict(
    cites=[*mo_guide("珍妮", 5, 1), mo_rate("mo-dwarf", "珍妮鹿角蕨", "難", DW)],
    desc=[("孢子葉上翹微捲，整體呈扇形，成熟後葉背銀黃。", "mo-dwarf", "珍妮鹿角蕨｜難｜1. 孢子葉呈上翹微捲 2. 整體孢子葉呈扇形 3. 成熟孢子葉背呈銀黃", "")],
    note=[
        ("與金童、鉑金並列交易金額上百萬元的鹿角蕨。", "mo-expensive", "除了珍妮鹿角蕨、金童鹿角蕨、鉑金鹿角蕨等創下上百萬元交易金額的最貴鹿角蕨品種", ""),
        ("2023 年 2 月底，一株爪哇珍妮在觀葉植物展以 600 萬元售出。", "bw-golden-boy", "有鹿角蕨業者在2023年2月底的觀葉植物展覽中，以600萬元天價售出特殊的「爪哇珍妮」鹿角蕨", ""),
    ],
    searched=searched("微體溫室〈侏儒鹿角蕨〉、〈鹿角蕨為什麼那麼貴〉|商業周刊報導", f"{MOS}|微體溫室〈侏儒鹿角蕨〉"),
)
BLOCKS["willinckii-nano"] = dict(
    cites=[mo_rate("mo-dwarf", "Nano 鹿角蕨", "中等", DW)],
    desc=[("孢子葉暗銀、分岔細長，成熟後葉背呈銀黃。", "mo-dwarf", "Nano 鹿角蕨｜中等｜1. 孢子葉呈暗銀 2. 孢子葉分叉細長 3. 成熟孢子葉背呈銀黃", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉", "微體溫室〈侏儒鹿角蕨〉"),
)
BLOCKS["willinckii-spur"] = dict(
    cites=[mo_rate("mo-dwarf", "骨刺鹿角蕨", "難", DW)],
    desc=[("孢子葉尖端分岔如刺，葉脈白紋明顯。", "mo-dwarf", "骨刺鹿角蕨｜難｜1. 孢子葉尖端分叉如刺 2. 孢子葉脈白紋明顯", "")],
    note=[("微體溫室把它列為侏儒 Nook 系列的名貴品種之一。", "mo-expensive", "Nook 系列的侏儒鹿角蕨出了許多名貴品種，如：骨刺、Kao Hom、加百列等", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉、〈鹿角蕨為什麼那麼貴〉", "微體溫室〈侏儒鹿角蕨〉"),
)
BLOCKS["fishbone"] = dict(
    cites=[mo_rate("mo-dwarf", "魚骨／寶石甲蟲鹿角蕨", "難", DW)],
    desc=[("孢子葉暗綠覆白毛，葉脈有一般鹿角蕨少見的白色菱格紋。", "mo-expensive",
           "魚骨（寶石甲蟲）等，更是飆破數十萬元，葉脈具有一般鹿角蕨很少見的白色菱格紋", "")],
    note=[("屬於侏儒 Watchara 系列。", "mo-expensive", "3. 侏儒 Watchara 鹿角蕨系列（魚骨／寶石甲蟲）", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉、〈鹿角蕨為什麼那麼貴〉|The Basements 商品頁（照護文字疑似 AI 生成，不採用）",
                      "微體溫室〈侏儒鹿角蕨〉|The Basements 商品頁（不採用）"),
)
BLOCKS["gabriel"] = dict(
    cites=[
        mo_rate("mo-dwarf", "加百列鹿角蕨", "中偏難", DW),
        c("haruhana-gabriel", "fertile_posture", "spread", "如天使之翼向兩邊展開", "", "最終極型態出來整體猶如天使之翼的向兩邊展開"),
        c("haruhana-gabriel", "origin", "Dwarf Nook 選拔的孢子苗", "Dwarf Nook 孢子苗", "T3，origin 只採 T1", "來自dwarf nook selection 的孢子苗"),
    ],
    desc=[("孢子葉厚、銀白、葉幅寬大，整體向外展開。", "mo-dwarf", "加百列鹿角蕨｜中偏難｜1. 孢子葉厚呈銀白 2. 孢子葉幅寬大 3. 整體孢子葉向外展開", "")],
    note=[("晴花鹿苑以聖經中的天使長加百列命名。", "haruhana-gabriel", "我們以聖經裡希伯來傳統的天使長「Gabriel」這個名字命名", "")],
    searched=searched("微體溫室〈侏儒鹿角蕨〉|晴花鹿苑商品頁", "微體溫室〈侏儒鹿角蕨〉|晴花鹿苑商品頁"),
)
BLOCKS["willinckii-celso-tatsuta"] = dict(
    cites=[*mo_guide("賽索爾", 5, 5)],
    note=[("台灣培育技術成熟後，賽索爾從一株側芽數十萬元降到 200~500 元。", "mo-expensive",
           "像「賽索爾」從原本一株側芽動輒數十萬元的天價降至 200~500 元即可入手的平民價格", "")],
    searched=searched(MOS + "|微體溫室〈鹿角蕨為什麼那麼貴〉", MOS),
)

BLOCKS["ginka"] = dict(
    cites=[
        *mo_guide("銀華", 5, 5),
        c("haruhana-ginka", "difficulty", 1, "整體養護簡易", "", "整體養護簡易，耐溫將近可達35度，非常適合台灣多數的環境。"),
        c("haruhana-ginka", "max_temp", 35, "耐溫將近可達 35 度", "耐受紀錄 → reference", "耐溫將近可達35度", "", "reference"),
        c("haruhana-ginka", "fertile_posture", "spread", "孢子葉向兩側展開", "", "向兩側展開的孢子葉型態，不僅葉片厚實，且具有顯眼白皙的星狀毛。"),
        c("haruhana-ginka", "fertile_hair", 5, "顯眼白皙的星狀毛", "", "具有顯眼白皙的星狀毛"),
        c("haruhana-ginka", "origin", "泰國 Wanna 園區，由 FSQ 播孢苗特選", "泰國 Wanna", "T3，origin 只採 T1", "源於泰國Wanna園區，由FSQ播孢苗特選而來。"),
    ],
    desc=[("以白銀般的質感、波浪起伏的孢子葉與層層堆疊的極短分岔聞名。", "ajins-ginka",
           "以白銀般的質感、波浪起伏的孢子葉，以及層層堆疊的極緻短分岔聞名", "")],
    searched=searched("晴花鹿苑、阿金商品頁", f"{MOS}|晴花鹿苑商品頁|阿金商品頁（只有屬層級通用照護）|We Love Tropical Plants（通用照護表，不採用）"),
)
BLOCKS["white-gizmo"] = dict(
    cites=[
        c("haruhana-white-gizmo", "fertile_posture", "spread", "孢子葉如緞帶向兩側對稱展開", "", "此品有著如緞帶般向兩側對稱的展開的孢子葉"),
        c("haruhana-white-gizmo", "origin", "由 FSQ 孢子苗特選", "FSQ 孢子苗", "T3，origin 只採 T1", "P. White Gizmo 由FSQ sporeling 特選命名。"),
    ],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
for pid, src, lab, q in [
    ("kiyohime", "haruhana-kiyohime", "種植門檻低，適合入門者", "對環境的適應力佳，耐溫性強，種植門檻低，十分適合栽培入門者與資深玩家收藏。"),
    ("elsa", "haruhana-elsa", "簡單容易，新手也能養", "簡單搭配頂光的環境，簡單容易就可以養得非常漂亮，無論是新手或是資深玩家，都值得收藏。"),
    ("hakuna-matata", "haruhana-hakuna-matata", "養殖難度低", "養殖難度低就能養的很漂亮"),
    ("willinckii-pearl-queen", "haruhana-pearl-queen", "養護與種植容易", "珍珠皇后的養護與種植容易，是耐高溫的一品鹿角蕨。"),
]:
    BLOCKS[pid] = dict(cites=[c(src, "difficulty", 1, lab, "", q)],
                       searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁|We Love Tropical Plants（通用照護表，不採用）"))
BLOCKS["kiyohime"]["cites"].append(c("haruhana-kiyohime", "fertile_posture", "up", "孢子葉筆直挺立", "", "成株後展現出如皇冠般的美麗冠型，以及筆直挺立的孢子葉。"))
BLOCKS["elsa"]["cites"].append(c("haruhana-elsa", "fertile_posture", "up", "孢子葉短而挺立", "", "緊湊且短而挺立的孢子葉，末端帶有優雅細緻的分岔，同時有著白皙迷人的絨毛。"))
BLOCKS["willinckii-white-swan"] = dict(
    cites=[c("haruhana-white-swan", "fertile_posture", "pendant", "孢子葉向下垂擺", "", "其孢子葉向下垂擺，帶有剛翼般的分岔，白皙對稱的弧度")],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["willinckii-anapat-9"] = dict(
    cites=[c("haruhana-anapat-9", "fertile_posture", "pendant", "下墜型的孢子葉", "", "知名系列Anapat #9 有著鹿角蕨經典的冠型與下墜型的孢子葉")],
    desc=[("孢子葉末端有許多分岔，帶明顯白皙感。", "haruhana-anapat-9", "在末端有著無數的岔型與此同時帶著明顯白皙感", "")],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["et"] = dict(
    cites=[
        c("haruhana-et", "fertile_posture", "pendant", "整體集中向前並自然下垂", "", "整體姿態集中向前並自然下垂"),
        c("haruhana-et", "fertile_hair", 5, "覆蓋如白雪般的細緻絨毛", "", "表面覆蓋著如白雪般的細緻絨毛"),
    ],
    desc=[("孢子葉寬大飽滿，葉端分岔密集而圓潤短小。", "haruhana-et", "搭配寬大飽滿的孢子葉 ... 葉端分叉密集且圓潤短小", "")],
    searched=searched("晴花鹿苑商品頁（播孢母本）", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["tornado"] = dict(
    cites=[],
    desc=[("孢子葉寬大、分岔較長、葉脈清晰，成熟後會從側邊捲起。", "haruhana-tornado",
           "同時有著寬大的孢子葉，其形態帶有較長的分岔與清晰的葉脈紋理。其孢子葉在成熟後會開始從側邊捲起", "")],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["willinckii-leonids"] = dict(
    cites=[], desc=[("母本有高冠與細長的孢子葉。", "haruhana-leonids", "母本有著霸氣的高冠與細緻秀長的孢子葉", "")],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["willinckii-pedro"] = dict(
    cites=[], desc=[("以對稱的高冠與層次分明、白皙的孢子葉聞名。", "haruhana-pedro", "以對稱優雅的高冠與層次分明、白皙迷人的孢子葉聞名", "")],
    searched=searched("晴花鹿苑商品頁", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["trident"] = dict(
    cites=[], desc=[("孢子葉末端的分岔像三叉戟。", "ajins-trident", "末端的分叉有如海神手中的三叉戟", "")],
    searched=searched("阿金商品頁", "阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["hillii-raijin"] = dict(
    cites=[],
    desc=[("孢子葉深色、寬厚，分岔圓潤，葉脈紋理明顯並帶絨毛感。", "haruhana-raijin",
           "繼承深綠寬厚大葉的特色外，葉形帶有的圓潤的分岔，深色的孢子葉刻有明顯的葉脈紋理並帶著絨毛感。", "")],
    note=[("阿金說它是出自泰國的園藝種。", "ajins-raijin", "深綠中夢幻逸品，出自泰國的經典園藝種", "")],
    searched=searched("晴花鹿苑、阿金商品頁", "晴花鹿苑商品頁|阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["rydeen"] = dict(
    cites=[c("jl-rydeen", "fertile_posture", "pendant", "孢子葉下垂、近乎彎折，分岔細", "",
             "'Rydeen' has the drooping, almost bent, finely branched fronds of 'Mt. Lewis' combined with the upright tips of the bracts of 'High Finger'.")],
    desc=[("盾葉先端直立尖細，生長很快。", "jl-rydeen", "combined with the upright tips of the bracts of 'High Finger'. A truly fantastic cross, and very fast-growing to boot!", "")],
    note=[("Jungle Leaves 寫親本是 'Mount Lewis' 與銀鹿 'High Finger'。", "jl-rydeen",
           "Platycerium 'Rydeen' is a hybrid of Platycerium sp. 'Mount Lewis' and Platycerium veitchii 'High Finger'.", "")],
    searched=searched("Jungle Leaves 商品頁|搜尋：Platycerium Mt Kitshakood care（意外找到此頁）", "Jungle Leaves 商品頁（通用照護句，不採用）"),
)

# ---------------------------------------------------------------- batch 1: selections of native species (no inference from the species, guideline §1.6)
SILVER = "銀鹿鹿角蕨雖品系眾多，然而在照顧上卻有許多相似之處：充足日照、耐旱喜透氣、澆透不積水"
for pid, zh, lv, lab in [("veitchii-auburn-river", "澳銀", "3–5", "中至中強光"), ("veitchii-wild", "野銀", "3–5", "中至中強光"),
                         ("veitchii-nyx", "夜銀", "1–3", "中弱至中光")]:
    BLOCKS[pid] = dict(
        cites=[c("mo-silver", "light", lv, lab, f"文章表格「{zh}鹿角蕨」的日照欄", f"銀鹿鹿角蕨日照｜{zh}鹿角蕨：{lab}"),
               c("mo-silver", "water", 1, "銀鹿各品系：耐旱喜透氣", f"文章說銀鹿各品系（含{zh}）照顧相似、耐旱 → 1", SILVER)],
        searched=searched("微體溫室〈銀鹿 3 品種〉", "微體溫室〈銀鹿 3 品種〉"))
BLOCKS["veitchii-auburn-river"]["cites"] += mo_guide("澳銀", 5, 5)
BLOCKS["veitchii-auburn-river"]["desc"] = [
    ("在澳洲奧本河國家公園發現，營養葉尖冠明顯、如珊瑚向外展開，孢子葉末端分岔通常比一般銀鹿多。", "mo-silver",
     "澳銀鹿角蕨屬於營養葉尖冠明顯的銀鹿鹿角蕨品系，如珊瑚般向外展開，於澳洲的奧本河國家公園所發現，其孢子葉（手）的尾端分叉通常也會較一般銀鹿鹿角蕨品種來的多", "")]
BLOCKS["veitchii-wild"]["cites"].append(c("mo-silver", "fertile_posture", "up", "孢子葉與營養葉皆聳立直上", "", "不論孢子葉或營養葉皆聳立直上"))
BLOCKS["veitchii-wild"]["desc"] = [("在澳洲野外發現，營養葉尖冠比澳銀更細長、集中向上。", "mo-silver",
                                    "野銀鹿角蕨與澳銀鹿角蕨同為澳洲野外所發現的個體，然而營養葉尖冠更細長且集中向上", "")]
BLOCKS["veitchii-nyx"]["cites"] += [
    c("mo-silver", "fertile_hair", 5, "孢子葉覆滿細小銀白絨毛", "", "孢子葉短厚且覆滿細小銀白絨毛"),
    c("ajins-nyx", "fertile_posture", "up", "孢子葉非常立葉", "", "其次他的孢子葉會呈現非常立葉的型態"),
]
BLOCKS["veitchii-nyx"]["desc"] = [("由銀鹿選育而出，孢子葉短厚，營養葉渾圓、冠呈束狀。", "mo-silver",
                                   "夜銀鹿角蕨為銀鹿鹿角蕨選育而出的個體，孢子葉短厚且覆滿細小銀白絨毛，營養葉型態渾圓且冠成束", "")]

LEMO = "檸檬鹿角蕨是什麼品種？高冠細葉＆侏儒檸檬鹿角蕨"
BLOCKS["veitchii-lemoinei"] = dict(
    cites=[
        *mo_guide("檸檬", 1, 5),
        c("mo-lemoinei", "difficulty", 1, "適合新手入門", "", "高冠檸檬鹿角蕨 ... 是適合新手入門的鹿角蕨品種之一"),
        c("mo-lemoinei", "light", "3–5", "中至中強光；夏季遮陰 30~50%", "遮陰 30% → 5、50% → 3", "檸檬鹿角蕨日照｜中至中強光 ... 夏季可使用黑紗網遮陰 30~50%"),
        c("mo-lemoinei", "water", 1, "相對耐旱", "耐旱 → 1", "檸檬鹿角蕨是屬於相對耐旱的品種之一"),
        c("mo-lemoinei", "fertile_hair", 5, "孢子葉覆滿白絨毛", "", "覆滿白絨毛的孢子葉手長可超過 60 公分"),
    ],
    desc=[("營養葉有尖細聳立的冠，高可達 30~45 公分；日照充足時孢子葉聳立，陽光柔和時會向前垂墜、呈萊姆綠。", "mo-lemoinei",
           "營養葉的特化尖冠高度可達 30~45 公分 ... 經常為孢子葉聳立的姿態 ... 若栽培在陽光柔和的居家陽台，手會向前生長垂墜，葉色呈萊姆綠", "")],
    note=[("微體溫室稱它為「檸檬鹿角蕨」，學名寫作 P. veitchii 'Lemoinei'。", "mo-lemoinei", "學名為 Platycerium veitchii ‘Lemoinei’", "")],
    searched=searched("微體溫室〈檸檬鹿角蕨〉", f"{MOS}|微體溫室〈檸檬鹿角蕨〉"),
)

HIL = "深綠鹿角蕨雖品系多樣，然而在照顧上卻有許多相似之處：中弱光照度、好微溼喜透氣、澆透不積水"
HILW = c("mo-hillii", "water", 3, "成株乾濕週期澆水", "乾濕交替 → 3", "上板成株｜1. 明亮散射光 2. 乾溼週期澆水")
BLOCKS["hillii-dragon"] = dict(
    cites=[
        c("mo-hillii", "light", "3–5", "可遮陰 30%~50%", "遮陰 30% → 5、50% → 3（表格另寫中至中弱光）", "一般深綠或深綠龍鹿角蕨可以黑紗網遮陰 30%~50%"),
        HILW, c("mo-hillii", "difficulty", 1, "對環境不挑，適合新手", "", "加上對環境不太挑的特性，也是適合新手入手的特殊鹿角蕨品種之一"),
    ],
    desc=[("孢子葉有龍鱗般的格狀脈紋，末端如龍爪。", "mo-hillii", "並從中衍生出龍麟格狀的帥氣脈紋，加上龍爪狀的手手末端", "")],
    searched=searched("微體溫室〈深綠鹿角蕨〉", "微體溫室〈深綠鹿角蕨〉"),
)
BLOCKS["hillii-mio"] = dict(
    cites=[
        c("mo-hillii", "light", 1, "可提高遮光到 70%，日照需求低", "遮陰 70% → 1", "而綴化深綠或侏儒深綠鹿角蕨可再提高遮光率到 70% ... 而密歐所需的日照需求較低"),
        HILW,
    ],
    desc=[("孢子葉末端有多重綴化的小分岔，隨植株成熟越明顯、葉色也越深。", "mo-hillii",
           "孢子葉末端具有多重的綴化小手手，且隨著植株成熟綴化現象也會日益明顯、葉色也會更深邃", "")],
    searched=searched("微體溫室〈深綠鹿角蕨〉", "微體溫室〈深綠鹿角蕨〉"),
)
BLOCKS["hillii-dwarf"] = dict(
    cites=[
        c("mo-hillii", "light", 1, "可提高遮光到 70%", "遮陰 70% → 1", "而綴化深綠或侏儒深綠鹿角蕨可再提高遮光率到 70%"),
        HILW,
        c("mo-hillii", "max_temp", 33, "小苗：避免超過 33 度", "建議值（小苗）", "而像是侏儒深綠幼苗要避免環境溫度超過 33 度，否則易發生熱障礙而生長停滯"),
    ],
    desc=[("體型是一般深綠的 ⅓ 到 ¼，孢子葉分岔成小巧的指狀，成熟後有絨毛感。", "mo-hillii",
           "體型為一般深綠的 ⅓ 到 ¼ 大小，孢子葉呈分叉為小巧可愛的指狀，成熟後具絨毛感", "")],
    searched=searched("微體溫室〈深綠鹿角蕨〉", "微體溫室〈深綠鹿角蕨〉"),
)

RID = "亞猴鹿角蕨 6 品種"
RIDL = c("mo-ridley", "light", 3, "亞猴各品系：明亮散射光", "bright filtered → 3",
         "亞猴鹿角蕨雖品系眾多，然而在照顧上卻有許多相似之處：明亮散射光、高透氣性介質、澆透不積水")
for pid, zh, rate, d in [
    ("ridleyi-thin", "細葉亞猴鹿角蕨（一般亞猴）", "中等", "孢子葉柄細長，營養葉脈紋呈放射狀向外。|1. 孢子葉柄細長 2. 營養葉脈紋呈幅射向外"),
    ("ridleyi-wide", "寬葉亞猴鹿角蕨（摩天輪）", "中等", "孢子葉幅寬大，營養葉脈紋呈放射狀向外。|1. 孢子葉幅寬大 2. 營養葉脈紋呈幅射向外"),
    ("ridleyi-round", "圓葉亞猴鹿角蕨（漩渦）", "中等", "孢子葉緣呈波浪狀，營養葉脈紋呈漩渦狀向外。|1. 孢子葉波浪葉緣 2. 營養葉脈紋呈渦旋向外"),
    ("ridleyi-dwarf-silver", "侏儒銀葉鹿角蕨", "中偏易", "孢子葉末端銀白，幼苗期營養葉脈紋就很明顯。|1. 孢子葉末端銀白 2. 幼苗期營養葉脈紋明顯"),
    ("ridleyi-monkey-king", "美猴王鹿角蕨", "中等", "孢子葉特化出蕾絲狀葉緣。|1. 孢子葉特化蕾絲葉緣"),
]:
    s, q = d.split("|")
    BLOCKS[pid] = dict(cites=[mo_rate("mo-ridley", zh, rate, RID), RIDL], desc=[(s, "mo-ridley", f"{zh}｜{rate}｜{q}", "")],
                       searched=searched("微體溫室〈亞猴鹿角蕨 6 品種〉", "微體溫室〈亞猴鹿角蕨 6 品種〉"))
BLOCKS["ridleyi-thin"]["cites"] += [
    c("ajins-ridleyi-thin", "water", 3, "給水乾濕循環，不要常保過濕", "乾濕交替 → 3", "照顧方式也與亞猴一樣照顧需注意給水乾溼循環不要常保過濕"),
    c("ajins-ridleyi-thin", "light", 3, "置於明亮散光處，避開高溫", "bright filtered → 3", "且注意避開高溫環境置於明亮散光處"),
    c("ajins-ridleyi-thin", "pups", "no", "單芽型", "", "細葉亞洲猴腦是單芽型的鹿角蕨"),
]
BLOCKS["ridleyi-thin"]["note"] = [("微體溫室把細葉亞猴當成「一般亞猴」。", "mo-ridley", "細葉亞猴鹿角蕨（一般亞猴）", "")]
BLOCKS["ridleyi-round"]["note"] = [("微體溫室的「摩天輪」指寬葉亞猴，圓葉亞猴另稱「漩渦」。", "mo-ridley", "寬葉亞猴鹿角蕨（摩天輪） ... 圓葉亞猴鹿角蕨（漩渦）", "")]

ALC = "圓盾鹿角蕨雖品種眾多，然而在照顧上卻有許多相似之處：充足日照、耐旱喜透氣、澆透不積水"
ALCW = c("mo-alcicorne", "water", 1, "圓盾各品種：耐旱，可等介質全乾再澆", "耐旱 → 1；文章明說適用各品種", ALC + " ... 可以等到介質全乾再澆水")
ALCT = c("mo-alcicorne", "min_temp", 15, "保持 15 度以上", "建議值", "圓盾鹿角蕨照顧上可以把握 3 個原則：4~8 小時散射日照、3~7 天澆透一次，以及保持 15 度以上的環境溫度。")
BLOCKS["alcicorne-africa"] = dict(
    cites=[
        c("halling-dawboy", "fertile_hair", 1, "東非型孢子葉黃綠、蠟質、無毛、較窄", "waxy, hairless → 1",
          "Whereas the P. alcicorne from East Africa is yellow green, waxy, hairless and narrow compared to the Madagascar variety."),
        c("jl-alcicorne-dwarf", "fertile_hair", 1, "非洲型孢子葉毛稀疏", "sparse → 1", "The African form is known for its green, smooth mantle leaves with sparse hairs on the fronds."),
        c("mo-alcicorne", "shield_hair", 1, "營養葉翠綠、光滑帶蠟質", "waxy → 1", "非圓鹿角蕨相較馬圓鹿角蕨的營養葉型態更翠綠、且表面光滑帶蠟質感"),
        ALCW, ALCT,
    ],
    note=[("Halling 推測非洲型的盾葉可能較平滑、波紋較不明顯，但說需要更多樣本確認。", "halling-alc-mad",
           "the shield fronds of the African P. alcicorne may be smoother and the rippling effect of the P. madagascariense may be less pronounced. More examples of the African P. alcicorne need to be studied to confirm this observation.", "")],
    searched=searched("Halling Dawboy.htm、Alcicorne-Madagascariense.htm|微體溫室〈圓盾鹿角蕨 10 大品種〉|Jungle Leaves 商品頁"
                      "|Hennipman & Roos 1982（P. vassei 列為 P. alcicorne 異名，未分型描述，依指引不套用種的描述）",
                      "微體溫室〈圓盾鹿角蕨 10 大品種〉"),
)
BLOCKS["alcicorne-madagascar"] = dict(
    cites=[
        c("jl-alcicorne-dwarf", "fertile_hair", 5, "馬達加斯加型孢子葉通常覆白毛", "covered in white hairs → 5；T3", "its fronds are usually covered in white hairs"),
        c("mo-alcicorne", "fertile_hair", 1, "孢子葉較深色，仔細看才見星狀白毛", "仔細看才看得到 → 稀疏 1；T3", "馬圓鹿角蕨的孢子葉顏色也更深，仔細觀察的話還會發現葉面有星狀白毛"),
        ALCW, ALCT,
    ],
    desc=[("孢子葉寬、深綠色。", "halling-dawboy", "The fertile fronds of the P. alcicorne from Madagascar is characteristically; wide, and dark green.", ""),
          ("盾葉先端有皺褶。", "jl-alcicorne-dwarf", "the Madagascan form has folds at the tips of its mantle leaves", "")],
    searched=searched("Halling Dawboy.htm|微體溫室〈圓盾鹿角蕨 10 大品種〉|Jungle Leaves 商品頁|Hennipman & Roos 1982（未分型描述）",
                      "微體溫室〈圓盾鹿角蕨 10 大品種〉"),
)
BLOCKS["alcicorne-madagascar-dwarf"] = dict(
    cites=[
        c("ajins-alcicorne-dwarf", "light", 3, "明亮散射光與適當通風", "bright filtered → 3",
          "只要給予明亮散射光與適當通風，就能穩定生長，是相當容易入門的侏儒鹿角蕨。"),
        c("ajins-alcicorne-dwarf", "difficulty", 1, "相當容易入門", "", "是相當容易入門的侏儒鹿角蕨"),
        c("jl-alcicorne-dwarf", "fertile_posture", "up", "孢子葉直立、很窄", "", "have upright, very narrow fronds"),
        c("jl-alcicorne-dwarf", "difficulty", 1, "生長慢，不難照顧", "德國來源，只供參考", "Platycerium alcicorne 'Dwarf' grows relatively slowly and is not difficult to care for.", "", "reference"),
        ALCW, ALCT,
    ],
    desc=[
        ("只長到約 40 公分高、30 公分寬，孢子葉先端捲曲。", "jl-alcicorne-dwarf",
         "a particularly small selection, in which the fronds curl at the tips. They only grow to about 40 cm tall and 30 cm wide", ""),
        ("孢子葉向上昂起、末端捲翹，像噴泉湧出後順勢落下。", "haruhana-alcicorne-dwarf", "此外孢子葉向上昂起，並在末端帶有捲翹，就如噴泉般向上湧出，隨後順勢而降。", ""),
    ],
    searched=searched("阿金、晴花鹿苑、Jungle Leaves 商品頁|微體溫室〈圓盾鹿角蕨 10 大品種〉",
                      "阿金商品頁|Jungle Leaves 商品頁|微體溫室〈圓盾鹿角蕨 10 大品種〉"),
)
BLOCKS["horne-surprise-darwin"] = dict(
    cites=[c("mo-alcicorne", "shield_vein", "yes", "成熟營養葉有猴腦般的浮凸紋", "", "非非達爾文鹿角蕨（非非）｜非圓X非猴｜成熟營養葉如猴腦浮凸紋")],
    searched=searched("微體溫室〈圓盾鹿角蕨 10 大品種〉|阿金、Orchideeën Shop 商品頁", "阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["elephantotis-mammoth"] = dict(
    cites=[
        mo_rate("mo-elephant", "猛瑪象鹿角蕨", "容易", EL),
        c("mo-elephant", "min_temp", 15, "保持 15 度以上", "建議值；文章的照顧原則寫給象耳各品種", "以及保持 15 度以上的環境溫度"),
        c("mo-elephant", "water", 5, "需水量大，水苔不沾手即可再澆", "keep evenly moist → 5", "象耳鹿角蕨是需水量大的鹿角蕨品種，只要水苔摸起來不沾水即可再澆水，不用等到介質全乾。"),
    ],
    desc=[("孢子葉長橢圓，葉脈浮凸明顯，像浮起的青筋。", "mo-elephant", "猛瑪象擁有如青筋浮起的明顯脈紋 ... 猛瑪象鹿角蕨｜容易｜葉脈浮凸明顯　葉型呈長橢圓", "")],
    searched=searched("微體溫室〈象耳鹿角蕨 8 品種〉", "微體溫室〈象耳鹿角蕨 8 品種〉"),
)
BLOCKS["coronarium-thin"] = dict(
    cites=[],
    desc=[("大型，孢子葉細長、末端微捲。", "mo-crown", "細葉皇冠鹿角蕨｜大型種｜細葉　末端微捲", "")],
    searched=searched("微體溫室〈皇冠鹿角蕨〉|阿金商品頁", "阿金商品頁（只寫皇冠種的耐旱，不套用）"),
)


# ---------------------------------------------------------------- batch 2: additions to batch-1 plants (more Taiwan / Thai vendor pages)
def add(pid, cites=(), desc=(), note=(), star="", care=""):
    b = BLOCKS[pid]
    b.setdefault("cites", []).extend(cites)
    b.setdefault("desc", []).extend(desc)
    b.setdefault("note", []).extend(note)
    for k, v in (("*", star), ("care", care)):
        if v:
            b["searched"][k] += "|" + v


ZYX = "zyx-guide"
KP = "kapei-notes"
add("veitchii-lemoinei",
    cites=[c("haruhana-lemoinei", "difficulty", 1, "新手入門熱門首選，適應度極高", "", "在新手剛入門時是熱門首選! ... 同時對於環境的適應度極高。"),
           c("ajins-lemon", "difficulty", 1, "好照顧", "", "是非常漂亮而且好照顧的一款"),
           c("ajins-lemon", "light", 5, "喜愛日照強", "requires a lot of light → 5", "原生於澳洲，故喜愛日照強且乾旱的環境，日照越強表面的白毛就會越厚。"),
           c("ajins-lemon", "water", 1, "喜愛乾旱", "keep on the dry side → 1", "原生於澳洲，故喜愛日照強且乾旱的環境")],
    note=[("阿金商品頁只寫「檸檬鹿角蕨」，依微體溫室與晴花鹿苑（網址 pveitchii-lemoinei）把「檸檬」對應到 'Lemoinei'。", "haruhana-lemoinei",
           "可愛的小冠與厚實白皙的挺立孢子葉", "")],
    star="晴花鹿苑、阿金商品頁", care="晴花鹿苑、阿金商品頁")
add("veitchii-auburn-river",
    cites=[c("ajins-auburn-river", "light", 5, "原生地能適應高日曬", "原生地描述 → reference", "在原生地能適應高日曬的環境。", "", "reference")],
    desc=[("營養葉有極細長的高冠。", "ajins-auburn-river", "特色就是擁有極細長的高冠", "")],
    star="阿金商品頁", care="阿金商品頁")
add("hillii-dwarf",
    cites=[c("ajins-hillii-dwarf", "difficulty", 1, "好種好養，新手也能上手", "", "也相當好種好養，新手入門也能輕鬆上手。"),
           c("ajins-hillii-dwarf", "fertile_posture", "up", "整體型態自然上翹", "", "整體型態自然上翹")],
    star="阿金商品頁", care="阿金商品頁")
add("willinckii-bacteria",
    cites=[c("ajins-bacteria", "difficulty", 1, "好照顧，侏儒系中適合入門", "", "非常適合小空間栽培與上板展示，不占位置且好照顧，是侏儒系中相當適合入門的品種")],
    star="阿金商品頁", care="阿金商品頁|晴花鹿苑商品頁（只寫對環境敏感度高，沒有明確難度）")
add("omg",
    cites=[c("ajins-omg", "difficulty", 5, "比較進階的侏儒鹿角蕨", "進階 → 5", "是比較進階的侏儒鹿角蕨")],
    star="阿金商品頁", care="阿金商品頁")
add("willinckii-jenny", desc=[("孢子葉白皙，有細緻多層的分岔，末端有「勾爪」般的抱拳狀特徵。", "ajins-jenny",
                               "以其精緻白皙、有細緻且多層次分岔的孢子葉（營養葉）末端有可愛的「勾爪」抱拳狀特徵", "")], star="阿金商品頁")
add("hakuna-matata",
    cites=[c("ajins-hakuna-matata", "fertile_hair", 5, "成株有厚實的白毛", "", "Hakuna matata 成株表現具有厚實的白毛且孢子葉型態非常精緻捲翹")],
    desc=[("中小型，孢子葉短、分岔多，葉脈明顯。", "ajins-hakuna-matata", "於中小型鹿有著厚實白毛表現，手短且多岔，葉脈表現明顯且堅挺", "")], star="阿金商品頁")
add("alcicorne-x-elephantotis",
    cites=[c("ajins-alcicorne-africa-x-elephantotis", "difficulty", 1, "適合新手", "", "對濕度/氣候/環境要求都不高， 適合新手培育。"),
           c("ajins-alcicorne-africa-x-elephantotis", "light", 3, "訓養後可接受半日照", "半日照 → 3", "經訓養後也可以接受半日照，")],
    note=[("阿金的商品頁是非洲型圓盾 × 象耳（非圓象）。", "ajins-alcicorne-africa-x-elephantotis", "非洲圓盾交象耳 非圓象", "")],
    star="阿金〈非圓象〉商品頁", care="阿金〈非圓象〉商品頁")
add("willinckii-moonlight", desc=[("日照充足時葉面更白。", "ajins-moonlight", "日照充足的話，葉面會更顯皎白", "")], star="阿金商品頁")
add("willinckii-celso-tatsuta", desc=[("分岔與白毛表現亮眼。", "ajins-celso", "爪哇中夢幻逸品，擁有亮眼的分岔與白毛", "")], star="阿金商品頁")
add("moose", desc=[("葉面油亮厚實，新葉分岔密集、呈扇形層次。", "ajins-moose", "葉面油亮厚實，整體質感沉穩且富有光澤。新葉成長時分岔密集，展開呈現扇形層次", "")], star="阿金商品頁")
add("siamense",
    desc=[("Siam Exotica 介紹為象耳與爪哇的新交種。", "siam-silver-velvet", "Platycerium \"Silver Velvet\" It is new hybrid between Platycerium elephantotis X Platycerium willinckii", ""),
          ("孢子葉有象耳的寬大，也有爪哇的分岔，成為大波浪狀的分岔手。", "ajins-elephantotis-x-willinckii", "有象耳的大寬手，也有爪哇的分岔 ... 融合了兩種的特性變成大波浪的分岔手", "")],
    star="Siam Exotica 存檔頁|阿金〈象爪〉商品頁")
add("hillii-x-bifurcatum",
    cites=[c("siam-pup", "pups", "yes", "以二叉 × 深綠示範分株", "", "ในที่นี้จะเลือกหน่อที่แตกออกมามีใบชายแตกออกมา 4 ใบแล้ว ถือว่าแข็งแรง สามารถแยกได้อย่างปลอดภัยครับ ต้นที่แยกเป็นลูกผสมระหว่าง P.bifurcatum X P.hillii")],
    star="Siam Exotica 分株頁（存檔）")
add("veitchii-x-willinckii",
    cites=[c("ajins-veitchii-x-willinckii", "difficulty", 1, "生長快又好養", "", "且混合後的小銀哇，生長速度驚人又好養")],
    desc=[("成熟時盾葉冠如花朵綻放。", "ajins-veitchii-x-willinckii", "當植株成熟時，冠有如花朵般綻放", ""),
          ("孢子葉長、深裂。", KP, "銀哇 銀鹿ｘ爪哇010 | Willinckii x veitchii Silver 大長手超深裂", "")],
    star="阿金〈銀哇〉商品頁|卡呸醬筆記", care="阿金〈銀哇〉商品頁")
add("ridleyi-wide",
    cites=[c(KP, "humidity", 5, "喜空氣濕度", "high humidity → 5", "寬葉亞猴 ... 特性：怕冷、喜空氣濕度、水苔盡量乾燥且不碰到營養葉"),
           c(KP, "water", 1, "水苔盡量乾燥", "keep on the dry side → 1", "水苔盡量乾燥且不碰到營養葉")],
    desc=[("孢子葉圓、葉緣捲邊。", KP, "寬葉亞猴 寬葉亞洲猴腦019 | Platycerium ridleyi 圓葉捲邊", "")],
    star="卡呸醬筆記", care="卡呸醬筆記")
add("monkey-north",
    desc=[("兼具高冠、白絨毛與下垂的孢子葉。", ZYX, "奧銀與爪哇交種的經典個體。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉。", ""),
          ("晴花鹿苑說在適合的環境下生長速度會快很多。", "haruhana-monkey-north", "是一隻給予適合的環境 生長速度就會加快好幾倍的鹿角蕨", "")],
    star="竹意軒|晴花鹿苑商品頁", care="晴花鹿苑商品頁（沒有具體條件）")
add("ss-foong", desc=[("隨植株成熟，孢子葉分岔越來越多、越密集，組培苗又稱千手觀音。", ZYX,
                       "栽培過程中隨著植株的成熟，孢子葉的分岔數越來越多且密集，亦有千手觀音之稱的組培苗。", "")], star="竹意軒")
add("blue-moon", desc=[("竹意軒寫它是 DW 交種的月亮系列，葉胖寬，成熟時帶藍綠色。", ZYX, "DW交種中的月亮系列，葉胖寬，成熟時葉片具藍綠色之質感。", "")], star="竹意軒")
add("elsa", desc=[("絨毛表現佳；光照適當時孢子葉短而密集。", ZYX, "葉片絨毛表現極佳，成熟時分岔性好，給予適當光照時，葉片短且密集", "")], star="竹意軒")
add("bifurcatum-mt-lewis", desc=[("竹意軒的孢子苗為寬葉型。", ZYX, "貓路易士鹿角蕨孢子苗，具寬葉片。", "")], star="竹意軒")
add("callard",
    cites=[c(KP, "dormancy", "yes", "冬季休眠", "栽培者記錄固定在冬季休眠", "安地斯ｘ四叉006 | andinumｘquadridichotomum 高冠、長手深岔 休眠期：冬季")],
    desc=[("卡呸醬記為高冠、孢子葉長而深裂。", KP, "安地斯ｘ四叉006 | andinumｘquadridichotomum 高冠、長手深岔", "")],
    star="卡呸醬筆記", care="卡呸醬筆記")

# ---------------------------------------------------------------- batch 2: plants with only short vendor / grower notes
BLOCKS["holttumii-x-elephantotis"] = dict(
    cites=[
        c("siam-holttumii-elephantotis", "pups", "yes", "能從根端長出新芽", "",
          "จุดเด่นที่เชื่อว่าต้นมีเป็นลูกผสมระหว่าง Platycerium holttumii x elephantotis คือ มันสามารถให้หน่อ(pup) ใหม่ที่ปลายรากได้ครับ"),
        c(KP, "water", 1, "怕水", "easily over-watered → 1", "何象 何其美ｘ象耳 003 | P.holttumiiｘelephantotis 大臉大手 特性：怕水難顧，比亞猴非猴好顧。但是要美要技術"),
        c(KP, "difficulty", "3–5", "難顧，但比亞猴、非猴好顧", "難（5）但比亞猴（中階 3）、非猴好顧 → 3–5", "特性：怕水難顧，比亞猴非猴好顧。但是要美要技術"),
    ],
    desc=[
        ("泰國尖竹汶府的栽培者 Supakorn 育成。", "siam-holttumii-elephantotis",
         "ลูกผสมระหว่างเชื้อสายเอเชีย Platycerium holttumii กับเชื้อสายแอฟริกา Platycerium elephantotis ซึ่งเป็นฝีมือการผสมของคุณศุภกร แห่งจันทบุรี", ""),
        ("Siam Exotica 說有 2~3 種型態，成熟株能產孢也會長新芽；能從根端長芽是他們認為它是雜交種的依據。", "siam-holttumii-elephantotis",
         "Platycerium holttumii X elephantotis ที่ผสมได้นั้นมีอยู่ 2-3 ฟอร์ม ครับ ขนาดต้นโตเต็มที่สามารถสร้างสปอร์ และแตกหน่อใหม่ได้แล้ว", ""),
        ("盾葉與孢子葉都大。", KP, "大臉大手", ""),
    ],
    searched=searched("Siam Exotica 存檔頁|卡呸醬筆記|搜尋：何象鹿角蕨", "卡呸醬筆記"),
)
BLOCKS["holttumii-x-wandae"] = dict(
    cites=[],
    desc=[("孢子葉會長出像象耳、並有深裂的型態。", KP, "何女 何其美ｘ女王002 | P.holttumiiｘP.wandae 手會有象耳長出深岔手的型態", "")],
    searched=searched("卡呸醬筆記|搜尋：何女鹿角蕨", "卡呸醬筆記（沒有照護資料）"),
)
BLOCKS["wallichii-x-willinckii"] = dict(
    cites=[],
    desc=[("孢子葉像蝴蝶鹿角蕨般寬大、分岔，葉紋深，整體呈扇形展開，又有爪哇的飄逸感。", "ajins-wallichii-x-willinckii",
           "擁有蝴蝶般寬大分岔的孢子葉，葉紋深邃，整體有如扇形開展一般，也擁有爪哇的飄逸姿態", ""),
          ("卡呸醬記為高冠、孢子葉寬而淺裂，流通的是組培苗。", KP, "蝴蝶ｘ爪哇013 | P. Wallickii x Willinckii TC 高冠、寬葉淺裂", "")],
    searched=searched("阿金商品頁|卡呸醬筆記", "阿金商品頁（只有屬層級通用照護）|卡呸醬筆記"),
)
BLOCKS["coronarium-x-bifurcatum"] = dict(
    cites=[],
    desc=[("有皇冠高聳的盾葉與二叉的分岔。", "ajins-bifurcatum-x-coronarium", "同時擁有皇冠高聳雄偉的營養葉，以及二叉迷人的分岔。", ""),
          ("卡呸醬記為葉色深、孢子葉長而分岔小。", KP, "皇冠Ｘ二叉008 | Platycerium coronariumｘbifurcatum 深色、長手小岔", "")],
    searched=searched("阿金商品頁|卡呸醬筆記", "阿金商品頁（只有屬層級通用照護）|卡呸醬筆記"),
)
BLOCKS["andinum-x-stemaria"] = dict(
    cites=[], desc=[("孢子葉大。", KP, "安地斯ｘ三角 007 | P.andinumｘstemaria 大手", "")],
    searched=searched("卡呸醬筆記|Halling 首頁（只提到 Hoshizaki 曾寄給 Charles Alford 一株）", "卡呸醬筆記"),
)
BLOCKS["wandae-x-veitchii"] = dict(
    cites=[c("ajins-veitchii-x-wandae", "light", 5, "可強曬，適合屋頂", "full sun → 5", "再加上銀鹿可以強曬的特性，絕對是屋頂族必收品項之一。")],
    desc=[("盾葉張狂，孢子葉與分岔都大。", "ajins-veitchii-x-wandae", "搭上女王鹿角蕨碩大的基因之後直接張狂起來．孢子葉的型態跟分岔也是沒在客氣的大", "")],
    searched=searched("阿金〈銀女〉商品頁|卡呸醬筆記（只有名稱）", "阿金〈銀女〉商品頁"),
)
BLOCKS["salmon"] = dict(
    cites=[], desc=[("孢子葉寬、深裂，末端漸細。", KP, "鮭魚 爪哇ｘ深綠012 | P. Willinckii X Hillii \"Salmon\" 寬葉深裂，孢子葉末端趨細（頗特別）", "")],
    searched=searched("卡呸醬筆記", "卡呸醬筆記（沒有照護資料）"),
)
BLOCKS["willinckii-hp100"] = dict(
    cites=[], desc=[("孢子葉寬，有深有淺的分裂。", KP, "短手爪哇 011 | HP100 寬葉深淺裂", "")],
    searched=searched("卡呸醬筆記|微體溫室〈爪哇鹿角蕨〉（短手爪哇代表品種未列 HP100）", "卡呸醬筆記"),
)
BLOCKS["bifurcatum-little-kitty"] = dict(
    cites=[], desc=[("小型、孢子葉長。", KP, "小貓咪 細葉侏儒路易士018 | Platy. sp. Mt. Lewis thin & dwarf 'Little kitty' 小型品種、長手", "")],
    searched=searched("卡呸醬筆記|阿金商品頁（沒有描述）", "卡呸醬筆記|阿金商品頁"),
)
BLOCKS["veitchii-akki"] = dict(
    cites=[c("haruhana-akki", "difficulty", 1, "易於養護，新手喜愛", "", "同時易於養護的優勢，更是深受新手鹿友的喜愛。"),
           c(ZYX, "difficulty", 1, "栽培性佳", "栽培性佳 → easy → 1", "成熟表現冠高，型態狂暴粗曠，光線充足時也會向上生長，栽培性佳，是喜歡高冠品種的必收款。")],
    desc=[("成熟時盾葉冠高、型態粗獷，光線充足時孢子葉也會向上長。", ZYX, "成熟表現冠高，型態狂暴粗曠，光線充足時也會向上生長", "")],
    note=[("阿金寫它是銀鹿與野生澳銀的交種，承襲澳銀細尖的高冠。", "ajins-akki", "為銀鹿與野澳銀的交種。承襲了澳銀細尖高冠，且遺傳兩者的白毛與細緻。", "")],
    searched=searched("竹意軒|晴花鹿苑、阿金商品頁", "竹意軒|晴花鹿苑、阿金商品頁"),
)
for pid, label, q, d in [
    ("veitchii-ar-1", "", "自選個體，奧銀鹿角蕨之孢子苗，具有細尖的高冠，相當迷人。", "竹意軒從澳銀孢子苗自選的個體，盾葉冠細尖。"),
    ("hela", "", "成熟時冠部極度高聳，孢子葉呈下垂貌，爪哇與銀鹿檸檬交種個體。", "成熟時盾葉冠極高聳，孢子葉下垂。"),
    ("white-monkey", "", "奧銀與爪哇的交種。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉，是該系列較後續發表的個體。", "北猴系列較晚發表的個體，兼具高冠、白絨毛與下垂的孢子葉。"),
    ("wild-monkey", "", "奧銀與爪哇的交種。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉，此個體的冠部較為高聳。", "北猴系列中冠部較高聳的個體，有白絨毛與下垂的孢子葉。"),
    ("willinckii-wild-cat", "", "爪哇鹿角蕨的個體，孢子葉白且形態張揚，具有一定的辨識度。", "孢子葉白、形態張揚。"),
    ("full-moon", "", "DW交種，月亮系列的鹿角蕨，孢子葉有獨特的蠟質感，相當有辨識度。", "孢子葉有獨特的蠟質感。"),
    ("jynx", "", "葉片胖寬，整體體型適中，可愛的品種。", "葉片胖寬，體型中等。"),
    ("hillii-rimklong", "", "Rimklong為深綠鹿角蕨的個體，特色是孢子葉具綴化感，另外白毛也濃密。此株為孢子苗", "孢子葉有綴化感，白毛濃密。"),
    ("honey-moon", "", "DW交種中的月亮系列，葉基部較寬而逐漸縮窄，葉片葉色為蘋果綠色。", "孢子葉基部寬、漸窄，蘋果綠色。"),
    ("blue-monkey", "", "DW系列的交種，特色為孢子葉成熟時具有藍綠色質感，並且有明顯的葉脈紋路。", "孢子葉成熟時帶藍綠色，葉脈紋路明顯。"),
    ("white-hill", "", "孢子葉呈瀑布狀的下墜，排列密集，並且具有濃密的白色絨毛。", "孢子葉密集、如瀑布般下垂，白色絨毛濃密。"),
    ("willinckii-albo-anubis", "", "爪哇鹿角蕨的個體，葉片極其細緻。", "葉片極細緻。"),
    ("willinckii-cold-moon", "", "爪哇鹿角蕨的個體，孢子葉細緻而營養葉寬胖。", "孢子葉細緻，盾葉寬胖。"),
    ("alcicorne-gorgon", "", "圓盾鹿角蕨的個體，孢子葉成熟時葉緣會有波浪狀的質感。", "孢子葉成熟時葉緣呈波浪狀。"),
    ("willinckii-a-plus", "", "爪哇鹿角蕨的個體，白皙且排列密集，體型中型。", "中型，孢子葉白皙、排列密集。"),
    ("doi-tung", "", "光線足夠時，葉片會往上生長，短且具氣勢。", "光線足夠時孢子葉向上長，短而有氣勢。"),
    ("bifurcatum-mt-lewis-thin", "", "貓路易士鹿角蕨個體，具細緻孢子葉片。", "孢子葉細。"),
    ("white-wing", "", "孢子葉白皙，葉脈紋路明顯，成熟時葉尾具密集分岔。", "孢子葉白皙、葉脈明顯，成熟時末端分岔密集。"),
    ("willinckii-mr-tin", "", "爪哇鹿角蕨個體，具白皙且細緻的流線孢子葉。", "孢子葉白皙、細緻呈流線形。"),
]:
    BLOCKS[pid] = dict(cites=[], desc=[(d, ZYX, q, "")], searched=searched("竹意軒|搜尋：中文俗名＋鹿角蕨", "竹意軒（只有型態短評）"))
BLOCKS["paul-vespa"] = dict(
    cites=[c(ZYX, "difficulty", 1, "栽培性很好", "栽培性好 → easy → 1", "DW交種系列下的品種，葉片白皙且對稱性佳，栽培性也很好。")],
    desc=[("孢子葉白皙、對稱。", ZYX, "葉片白皙且對稱性佳", "")],
    searched=searched("竹意軒", "竹意軒"),
)
BLOCKS["mountain-rabbit"] = dict(
    cites=[c(ZYX, "pups", "no", "大型單芽種", "", "大型單芽種，營養葉高聳，孢子葉僅有一對孢子囊群斑塊，氣勢雄偉。")],
    desc=[("大型，盾葉高聳，孢子葉只有一對孢子囊群。", ZYX, "大型單芽種，營養葉高聳，孢子葉僅有一對孢子囊群斑塊，氣勢雄偉。", "")],
    searched=searched("竹意軒", "竹意軒（沒有照護資料）"),
)
BLOCKS["willinckii-little-will"] = dict(
    cites=[],
    desc=[("侏儒尺寸，是可以露天栽培的侏儒鹿角蕨。", ZYX, "爪哇鹿角蕨的個體，體型為侏儒尺寸，相當小，是可以露養的侏儒鹿角蕨。", "")],
    searched=searched("竹意軒", "竹意軒（只寫可露養，沒有光照等級）"),
)
BLOCKS["willinckii-smurf"] = dict(
    cites=[c("ajins-smurf", "fertile_hair", 5, "藍底白厚毛", "白厚毛 → 5", "藍底白厚毛，高冠表現，分岔微捲手型")],
    desc=[("孢子葉藍底覆厚白毛，分岔微捲；盾葉有高冠。", "ajins-smurf", "藍底白厚毛，高冠表現，分岔微捲手型", "")],
    searched=searched("阿金商品頁", "阿金商品頁"),
)
BLOCKS["willinckii-robin"] = dict(
    cites=[
        c("ajins-robin", "size", "S", "侏儒，成株約手掌大", "侏儒、成株約手掌大 → S", "這個個體不僅具有侏儒的型態……成株大約只有手掌大"),
        c("ajins-robin", "origin", "Dwarf Nook 孢子苗選拔", "Dwarf Nook 孢子苗", "T3，origin 只採 T1", "羅賓鹿角蕨是由 Dwarf Nook Sporling 選拔而來"),
        c("ajins-robin", "base", "willinckii-nook-dwarf", "", "由 Dwarf Nook 孢子苗選拔 → 侏儒 Nook", "羅賓鹿角蕨是由 Dwarf Nook Sporling 選拔而來"),
    ],
    extra={"base"},
    desc=[("侏儒型，葉面脈紋明顯、葉尾呈鋸齒，成株約手掌大。", "ajins-robin", "葉面上的脈紋表現明顯，葉尾鋸齒，成株大約只有手掌大", "")],
    searched=searched("阿金商品頁", "阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["bifurcatum-popcorn"] = dict(
    cites=[
        c("ajins-popcorn", "fertile_posture", "up", "超挺拔的孢子葉", "", "超挺拔的孢子葉和如同爆米花爆開的末端分岔"),
        c("ajins-popcorn", "origin", "Alan's fern 從二叉孢子苗特選", "Alan's fern 孢子苗特選", "T3，origin 只採 T1",
          "由台灣知名花圃Alan's fern從二歧鹿角蕨特選出的孢子苗，並由園主Alan命名"),
        c("ajins-popcorn", "base", "bifurcatum", "", "二歧鹿角蕨中的特選體 → 二叉", "為鹿角蕨科鹿角蕨屬下二歧鹿角蕨中的特選體"),
        c("ajins-popcorn", "breeder", "Alan's fern", "", "Alan's fern 選出、園主 Alan 命名", "由台灣知名花圃Alan's fern從二歧鹿角蕨特選出的孢子苗，並由園主Alan命名"),
    ],
    extra={"base", "breeder"},
    desc=[("孢子葉非常挺拔，末端分岔像爆米花爆開。", "ajins-popcorn", "型態很明顯特別，超挺拔的孢子葉和如同爆米花爆開的末端分岔", "")],
    note=[("台灣花圃 Alan's fern 從二叉孢子苗特選，由園主 Alan 命名。", "ajins-popcorn",
           "由台灣知名花圃Alan's fern從二歧鹿角蕨特選出的孢子苗，並由園主Alan命名", "")],
    searched=searched("阿金商品頁", "阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["flamenco"] = dict(
    cites=[
        c("haruhana-flamenco", "fertile_posture", "pendant", "孢子葉層層展開後自然垂墜", "", "層層展開後自然垂墜，彷彿身穿蓬鬆舞裙"),
        c("haruhana-flamenco", "pups", "no", "單芽型，無法萌生側芽", "", "作為單芽型鹿角蕨，無法萌生側芽"),
        c("haruhana-flamenco", "difficulty", 1, "簡單栽培也能展現美麗姿態", "", "對環境的適應性也非常良好，是一款即使簡單栽培也能輕鬆展現美麗姿態的理想品種"),
        c("ajins-flamenco", "parents", "hillii|coronarium", "深綠 × 皇冠", "", "佛朗明哥鹿角蕨為深綠鹿角蕨與皇冠鹿角蕨的交種個體"),
        c("haruhana-flamenco", "parents", "hillii|coronarium", "hillii（深綠）× 皇冠", "同頁兩段描述一段寫 hillii、一段寫深綠", "繼承了「hillii 」與「皇冠」兩者的獨特特徵"),
        c("haruhana-fb-flamenco", "parents", "hillii-mio|coronarium", "深綠 Mio × 千手皇冠", "影片標題；千手皇冠沒有條目，親本欄只寫到種", "P.hillii × coronarium 'Flamenco' 佛朗明哥由深綠mio與千手皇冠交種出來的絕美個體", "", "reference"),
    ],
    extra={"parents"},
    desc=[
        ("孢子葉深綠、分岔豐富，層層展開後自然垂墜。", "haruhana-flamenco", "此品種擁有深綠色、分岔豐富的孢子葉，層層展開後自然垂墜", ""),
        ("孢子葉邊緣波浪起伏，展開時像舞者的裙襬，因此得名「佛朗明哥」。", "ajins-flamenco", "孢子葉邊緣波浪起伏，層次柔和，展開時如同舞者裙襬般柔順延伸，因此得名「佛朗明哥」", ""),
    ],
    note=[("晴花鹿苑的影片標題寫親本是深綠 Mio 與千手皇冠。", "haruhana-fb-flamenco", "P.hillii × coronarium 'Flamenco' 佛朗明哥由深綠mio與千手皇冠交種出來的絕美個體", "")],
    searched=searched("阿金、晴花鹿苑商品頁|晴花鹿苑 Facebook 影片標題", "阿金商品頁（只有屬層級通用照護）|晴花鹿苑商品頁"),
)
BLOCKS["unicorn"] = dict(
    cites=[c("ajins-unicorn", "fertile_hair", 5, "絨毛層次多、非常潔白", "", "葉面覆蓋著帶有層次的絨毛，顏色非常潔白，甚至帶有一絲淡淡的藍色。")],
    searched=searched("阿金、晴花鹿苑商品頁", "阿金、晴花鹿苑商品頁|We Love Tropical Plants（通用照護表，不採用）"),
)


# ---------------------------------------------------------------- batch 3: the rest (mostly nothing found within the 5-lookup limit)
BLOCKS["bifurcatum-white"] = dict(
    cites=[
        c("haruhana-bif-white", "difficulty", 1, "養護簡單", "", "養護簡單，能耐高溫達到接近38度，側芽發展迅速，非常適合大多數環境。"),
        c("haruhana-bif-white", "max_temp", 38, "耐高溫接近 38 度", "耐受紀錄 → reference", "能耐高溫達到接近38度", "", "reference"),
        c("haruhana-bif-white", "pups", "yes", "側芽發展迅速", "", "側芽發展迅速"),
    ],
    desc=[("孢子葉細緻、分岔短，白皙的葉面上葉脈清晰。", "haruhana-bif-white", "P.bif sp white 擁有細緻的孢子葉和迷人的短分岔，在白皙的葉片上有清晰的葉脈紋理。", ""),
          ("流通的是組培苗。", KP, "白鹿014 | Platycerium bifurcatum sp. white TC", "")],
    searched=searched("晴花鹿苑商品頁|卡呸醬筆記", "晴花鹿苑商品頁"),
)
BLOCKS["bifurcatum-x-willinckii"] = dict(
    cites=[c("haruhana-willinckii-x-bif", "fertile_posture", "up", "孢子葉向上昂揚", "", "它具有優美的冠型與多岔白皙質感的孢子葉，隨著向上昂揚的姿態")],
    searched=searched("晴花鹿苑商品頁|卡呸醬筆記（只有名稱）", "晴花鹿苑商品頁（沒有照護資料）"),
)
BLOCKS["wandae-dwarf"] = dict(
    cites=[], desc=[("小而捲的外型，葉脈深。", "ajins-wandae-dwarf", "同時兼具「侏儒」還有「捲葉」的可愛小女王，不同於女王的外表，擁有小而捲的外型與深遂的葉脈", "")],
    searched=searched("阿金商品頁|卡呸醬筆記（只有名稱）", "阿金商品頁（只有屬層級通用照護）"),
)
BLOCKS["bifurcatum-netherlands"] = dict(
    cites=[
        c("cistus-netherlands", "light", 3, "明亮但避開直射", "bright, out of direct sun → 3", "Bright light is best but out of direct sun."),
        c("cistus-netherlands", "water", "1–3", "澆透後待乾；比其他型更耐頻繁澆水", "drying between waterings 1，但較耐頻繁澆水 → 1–3",
          "Best watered well and allowed to dry out before watering again, however, the 'Netherlands' form is more tolerant of more frequent watering."),
        c("cistus-netherlands", "fertile_length", "~≤91 cm", "孢子葉可達 3 呎", "只給上限 → 寬鬆說法（v1.4）", "fertile fronds to up to 3 ft long"),
    ],
    desc=[("NC State Extension 說它是常見的栽培品種，葉灰綠、分裂。", "ncsu-bifurcatum", "'Netherlands' popular cultivar with grayish-green and lobed fronds", ""),
          ("孢子葉淡灰綠，生長旺盛。", "cistus-netherlands", "Epiphytic fern with pale, gray-green, fertile fronds ... A vigorous grower", "")],
    searched=searched("NC State Extension Plant Toolbox|Cistus Nursery|Rainforest Flora（文字疑似 AI 生成，不採用）|搜尋：Platycerium bifurcatum 'Netherlands' cultivar description fronds care",
                      "Cistus Nursery|NC State Extension（照護欄位寫的是種，不套用）|Rainforest Flora（不採用）"),
)
for pid, star in [
    ("joe-young", "搜尋：Platycerium 'Joe Young' grande superbum hybrid|搜尋：巨猴鹿角蕨 Joe Young 照顧 日照|青青小樹（只有插畫）"),
    ("budsaba", "搜尋：Platycerium Budsaba madagascariense quadridichotomum hybrid|搜尋：非Q鹿角蕨 Budsaba|青青小樹（只有插畫）|Halling 交種表（非猴 × 四叉列為 No name yet）"),
    ("saikeaw", "搜尋：Platycerium Saikeaw andinum willinckii hybrid|搜尋：安爪鹿角蕨 Saikeaw 照顧|青青小樹（只有插畫）"),
    ("superbum-x-wandae", "搜尋：Platycerium superbum x wandae hybrid staghorn|Halling 交種表|Siam Exotica 存檔"),
    ("alcicorne-x-ellisii", "搜尋：Platycerium ellisii x alcicorne vassei hybrid Siam Exotica|Siam Exotica 存檔頁（只有名稱與照片）|Halling 交種表（非洲型圓盾 × 愛麗絲列為 No name yet）"),
    ("dw", "搜尋：Platycerium 'DW' diversifolium x willinckii hybrid|竹意軒（只提到 DW 系列的後代）|阿金、晴花鹿苑商品目錄"),
    ("mew", "阿金、晴花鹿苑商品目錄|竹意軒|微體溫室文章總覽"),
    ("willinckii-masayu", "阿金、晴花鹿苑商品目錄|竹意軒|微體溫室〈侏儒鹿角蕨〉"),
    ("ridleyi-jade-peony", "卡呸醬筆記（只有名稱）|微體溫室〈亞猴鹿角蕨 6 品種〉（未列）|阿金、晴花鹿苑商品目錄"),
    ("ridleyi-pakarang", "微體溫室〈亞猴鹿角蕨 6 品種〉（未列）|阿金、晴花鹿苑商品目錄|竹意軒"),
    ("hillii-wide", "卡呸醬筆記（只有名稱）|微體溫室〈深綠鹿角蕨〉（未列）|阿金、晴花鹿苑商品目錄"),
    ("veitchii-high-finger", "晴花鹿苑商品頁（與另一頁文字相同，無法確認描述的是哪個品種，不採用）|阿金商品目錄|微體溫室〈銀鹿 3 品種〉（未列）"),
    ("kitshakood-thin-dwarf", "阿金商品頁（學名標示 thin leaf and dwarf；照護只有屬層級通用說明）|微體溫室〈侏儒鹿角蕨〉（「侏儒亞皇」不確定是否同一植物，不採用）"),
    ("willinckii-kaguya", "微體溫室〈鹿角蕨為什麼那麼貴〉（只有價格）|阿金、晴花鹿苑商品目錄"),
    ("willinckii-blue-queen", "微體溫室〈侏儒鹿角蕨〉（侏儒藍皇后，依本站別名視為同一植物，只取侏儒說法）|阿金、晴花鹿苑商品目錄"),
    ("willinckii-sri-pueak", "晴花鹿苑商品頁（只有照片）|阿金商品目錄"),
    ("willinckii-nook-dwarf", "微體溫室〈鹿角蕨為什麼那麼貴〉（只有價格與衍生品種）|阿金、晴花鹿苑商品目錄"),
    ("willinckii-kaohom", "微體溫室〈鹿角蕨為什麼那麼貴〉（只有價格）|阿金、晴花鹿苑商品目錄"),
    ("willinckii-watchara", "微體溫室〈鹿角蕨為什麼那麼貴〉（只有價格）|阿金、晴花鹿苑商品目錄"),
    ("wolverine", "阿金商品頁（沒有描述）|SapphireChild Orchids（只有推測）|We Love Tropical Plants（通用照護表，不採用）"),
    ("south-pole-star", "阿金商品頁（沒有描述）|竹意軒"),
]:
    BLOCKS[pid] = dict(cites=[], searched=searched(star, star))
BLOCKS["willinckii-nook-dwarf"]["note"] = [("微體溫室說侏儒 Nook 系列出了骨刺、Kao Hom、加百列等名貴品種。", "mo-expensive",
                                            "Nook 系列的侏儒鹿角蕨出了許多名貴品種，如：骨刺、Kao Hom、加百列等", "")]
BLOCKS["willinckii-kaohom"]["note"] = [("微體溫室把它列為侏儒 Nook 系列的名貴品種之一。", "mo-expensive", "Nook 系列的侏儒鹿角蕨出了許多名貴品種，如：骨刺、Kao Hom、加百列等", "")]
BLOCKS["willinckii-kaguya"]["note"] = [("微體溫室把它列為侏儒黃月的收藏家命名個體之一。", "mo-expensive", "由於侏儒黃月孢子苗變化大，更有不少收藏家的命名個體，如：迦具夜、迦納、亞森等", "")]
BLOCKS["willinckii-watchara"]["note"] = [("微體溫室說 Watchara 是近期的侏儒爪哇系列，魚骨（寶石甲蟲）是其中更稀有的侏儒個體。", "mo-expensive",
                                          "Watchara 系列的侏儒爪哇鹿角蕨品種是近期的新興之作 ... 而更稀有的侏儒鹿角蕨個體，如：魚骨（寶石甲蟲）等", "")]


# ---------------------------------------------------------------- v1.3: dwarf statements → size S (guideline §4 尺寸)
# a source that calls the plant 侏儒 / dwarf without measurements gives size = S; one row per plant and publisher
DWT = "11 款熱門的侏儒爪哇鹿角蕨"
DWC = f"〈11 種侏儒鹿角蕨〉的「{DWT}」表格列出此品種 → 侏儒，視為 S"
for pid, zh, rate in [("willinckii-jade-girl", "玉女鹿角蕨", "中等"), ("willinckii-bacteria", "細菌鹿角蕨", "中偏難"),
                      ("willinckii-blue-queen", "侏儒藍皇后鹿角蕨", "中偏難"), ("willinckii-nano", "Nano 鹿角蕨", "中等"),
                      ("omg", "OMG 鹿角蕨", "中等"), ("willinckii-jenny", "珍妮鹿角蕨", "難"), ("willinckii-golden-boy", "金童鹿角蕨", "難"),
                      ("willinckii-spur", "骨刺鹿角蕨", "難"), ("fishbone", "魚骨／寶石甲蟲鹿角蕨", "難"), ("gabriel", "加百列鹿角蕨", "中偏難")]:
    add(pid, [c("mo-dwarf", "size", "S", "侏儒爪哇", DWC, f"{DWT} ... {zh}｜{rate}")])
for pid, src, lab, claim, quote in [
    ("willinckii-little-will", ZYX, "侏儒尺寸", "", "體型為侏儒尺寸，相當小"),
    ("ridleyi-dwarf-silver", "mo-ridley", "侏儒銀葉亞猴", "〈亞猴鹿角蕨 6 品種〉表格列出「侏儒銀葉鹿角蕨」", "侏儒銀葉鹿角蕨｜中偏易"),
    ("bifurcatum-little-kitty", KP, "thin & dwarf，小型品種", "", "Platy. sp. Mt. Lewis thin & dwarf 'Little kitty' 小型品種"),
    ("wandae-dwarf", "ajins-wandae-dwarf", "侏儒、捲葉的小女王", "", "同時兼具「侏儒」還有「捲葉」的可愛小女王"),
    ("hillii-dwarf", "mo-hillii", "侏儒，一般深綠的 ⅓ 到 ¼", "", "侏儒深綠鹿角蕨除了體型更小 ... 體型為一般深綠的 ⅓ 到 ¼ 大小"),
    ("alcicorne-madagascar-dwarf", "ajins-alcicorne-dwarf", "侏儒鹿角蕨", "", "是相當容易入門的侏儒鹿角蕨"),
    ("kitshakood-thin-dwarf", "ajins-kitshakood-thin", "thin leaf and dwarf", "阿金商品頁的學名標示", "P. Mt kitshakood var.thin leaf and dwarf"),
    ("willinckii-nook-dwarf", "mo-expensive", "侏儒 Nook 系列", "", "Nook 系列的侏儒鹿角蕨出了許多名貴品種"),
    ("willinckii-kaohom", "mo-expensive", "侏儒 Nook 系列", "", "Nook 系列的侏儒鹿角蕨出了許多名貴品種，如：骨刺、Kao Hom、加百列等"),
    ("willinckii-kaguya", "mo-expensive", "侏儒黃月的命名個體", "", "由於侏儒黃月孢子苗變化大，更有不少收藏家的命名個體，如：迦具夜、迦納、亞森等"),
    ("willinckii-watchara", "mo-expensive", "侏儒爪哇 Watchara 系列", "", "Watchara 系列的侏儒爪哇鹿角蕨品種是近期的新興之作"),
]:
    add(pid, [c(src, "size", "S", lab, (claim + "；" if claim else "") + "來源稱侏儒、沒有尺寸 → S", quote)])
add("alcicorne-madagascar-dwarf", [c("jl-alcicorne-dwarf", "size", "~40", "高約 40 cm、寬約 30 cm", "整株高寬 → v1.4 寬鬆 D（已有侏儒說法，不計入摘要）",
                                     "They only grow to about 40 cm tall and 30 cm wide")])


# ---------------------------------------------------------------- batch 4 (2026-10-16): plants added from Ajin's Garden / Haruhana pages
# Each plant has one or two vendor pages (T3). Searches by name (English and Chinese) found no other source for any of them;
# the 微體溫室 articles only cover 侏儒檸檬 and 侏儒黃月. Title keyword tags (e.g. 「半日照」「新手入門」) are not used, only the prose.
AJ = "阿金商品頁"
HR = "晴花鹿苑商品頁"
WEB = "搜尋：英文品名＋Platycerium|搜尋：中文俗名＋鹿角蕨"
B4 = "竹意軒|卡呸醬筆記|微體溫室文章總覽（未列）"
B4C = f"{B4}|阿金商品頁末段（屬層級通用說明，不採用）"
SMALL = "只寫小型、沒有說侏儒，也沒有尺寸 → 不算侏儒說法"

BLOCKS["nemo"] = dict(
    cites=[
        c("ajins-nemo", "light", 3, "半日照陽台即可培養出極致型態", "半日照 → 3", "在半日照的陽台環境中也能逐步培養出極致型態"),
        c("ajins-nemo", "difficulty", 1, "適合陽台栽培，成功率高", "成功率高 → easy → 1", "適合陽台栽培，成功率高"),
    ],
    desc=[("白毛質感與分岔表現佳，業者稱常被視為佩德羅的平價替代。", "ajins-nemo",
           "在白毛質感與分岔表現上都有相當亮眼的發展潛力 ... 常被玩家視為平替版佩德羅的選擇", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}|{B4C}"),
)
BLOCKS["cardinals"] = dict(
    cites=[],
    desc=[("承襲奧銀的高尖冠與貓路易士的肌肉紋理。", "ajins-cardinals", "紅雀鹿角蕨承襲了奧銀狂野的高冠，還有貓路易士的肌肉紋理", "")],
    note=[("阿金的便秘花園另售斑葉組培杯苗 Cardinals 'Variegata'（斑葉紅雀）。", "ajins-cardinals-variegata",
           "以斑葉個體進行組織培養，可能包含全綠、全黃及斑葉個體。", "")],
    searched=searched(f"阿金〈紅雀〉〈斑葉紅雀〉商品頁|{WEB}|{B4}", f"阿金〈紅雀〉〈斑葉紅雀〉商品頁（沒有照護資料）|{B4C}"),
)
BLOCKS["kitshakood-x-ridleyi"] = dict(
    cites=[
        c("ajins-kitshakood-x-ridleyi", "fertile_posture", "up", "孢子葉向上延展、上翹", "", "孢子葉向上延展，線條更為挺拔，上翹姿態帶有明顯張力"),
        c("ajins-kitshakood-x-ridleyi", "shield_vein", "yes", "營養葉紋路清晰立體", "紋路立體 → 葉脈隆起", "營養葉紋路清晰立體"),
    ],
    desc=[("亞皇與亞猴回交的個體，孢子葉上翹、分岔細緻緊湊，營養葉紋路立體。", "ajins-kitshakood-x-ridleyi",
           "皇猴鹿角蕨為經典亞皇鹿角蕨與亞洲猴腦鹿角蕨回交後的個體 ... 分岔細緻且排列緊湊 ... 營養葉紋路清晰立體", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}（沒有照護資料）|{B4C}"),
)
BLOCKS["snow-white-x-suddan"] = dict(
    cites=[
        c("ajins-snow-white-x-suddan", "fertile_hair", 5, "白毛覆蓋濃密，有白銀般的反光", "covered with white hair → 5",
          "白毛覆蓋濃密，帶有金屬反光質感"),
        c("ajins-snow-white-x-suddan", "light", 5, "高光環境下白毛更明顯", "建議高光 → 5", "在高光環境下栽培，白毛表現會更加明顯，型態也更顯立體與極致"),
    ],
    desc=[("寬手延展的葉型，白毛濃密，在光線下有白銀般的反光。", "ajins-snow-white-x-suddan",
           "呈現出寬手延展的葉型與濃密細緻的白毛質感。葉面白毛在光線下帶有如白銀般的金屬反光", "")],
    note=[("阿金的便秘花園寫親本是 Snow White 與 Bogor Mr. Suddan，兩者尚未建檔，parents 暫時留空。", "ajins-snow-white-x-suddan",
           "白雪蘇丹鹿角蕨為 Snow White 與 Bogor Mr.Suddan 的交種特選個體", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}|{B4C}"),
)
BLOCKS["bambi"] = dict(
    cites=[
        c("ajins-bambi", "size", "S", "侏儒型體態", "來源稱侏儒、沒有尺寸 → S", "以侏儒型體態與緊湊株型深受玩家喜愛"),
        c("ajins-bambi", "difficulty", 1, "新手也能輕鬆上手", "", "新手也能輕鬆上手"),
    ],
    desc=[("侏儒型、株型緊湊，白毛細緻，業者稱為 Tonkla 系列的熱門品種。", "ajins-bambi",
           "Tonkla 系列中相當受歡迎的熱門品種 ... 以侏儒型體態與緊湊株型深受玩家喜愛。葉面白毛細緻柔和", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}|{B4C}"),
)
BLOCKS["stella-aeterni"] = dict(
    cites=[
        c("ajins-stella-aeterni", "fertile_posture", "spread", "孢子葉放射狀展開", "spreading → spread", "孢子葉呈放射狀展開，線條穩定而均衡，宛如星芒般向外延伸"),
        c("ajins-stella-aeterni", "fertile_hair", 3, "葉面白毛細密", "densely set with hairs → 3", "葉面白毛細密，質感柔和"),
    ],
    desc=[("孢子葉放射狀展開、結構對稱，白毛細密。", "ajins-stella-aeterni", "以對稱結構與細緻白毛聞名 ... 孢子葉呈放射狀展開 ... 葉面白毛細密", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}（只有標題標籤「好養」「半日照」，不採用）|{B4C}"),
)
BLOCKS["aydan"] = dict(
    cites=[
        c("ajins-aydan", "size", "~S", "小型爪哇系", SMALL + "；v1.4 記為寬鬆 S", "是一款精緻迷人的小型爪哇系鹿角蕨 ... 整體尺寸維持在相對小巧的範圍"),
        c("ajins-aydan", "fertile_posture", "spread", "葉片自然向外舒展", "spreading → spread", "葉片自然向外舒展，分岔細緻而流暢"),
    ],
    desc=[("小型的爪哇系，孢子葉纖細、分岔細緻，覆細白毛。", "ajins-aydan",
           "小型爪哇系鹿角蕨 ... 孢子葉所呈現出的纖細線條與優雅分岔 ... 葉面覆蓋著細緻白毛", "")],
    note=[("阿金的便秘花園寫「小型爪哇系」，未寫是否為交種，暫以爪哇為 base。", "ajins-aydan", "是一款精緻迷人的小型爪哇系鹿角蕨", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}（沒有照護資料）|{B4C}"),
)
BLOCKS["willinckii-omega"] = dict(
    cites=[],
    desc=[("白毛細緻，分岔清晰、層次立體。", "ajins-omega", "葉面白毛細緻 隨著生長逐漸展現出分岔清晰且極具層次的立體結構", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}（沒有照護資料）|{B4C}"),
)
BLOCKS["willinckii-half-moon"] = dict(
    cites=[
        c("ajins-half-moon", "light", 3, "孢子苗：室內明亮散射光即可穩定生長", "bright filtered light → 3；小苗", "在室內明亮散射光環境下即可穩定生長"),
        c("ajins-half-moon", "difficulty", 1, "孢子苗：入門款，適合新手", "小苗", "入門款定位，適合新手開始養成"),
    ],
    desc=[("白毛與分岔表現優異。", "ajins-half-moon", "半月鹿角蕨孢子苗為實生培養的小型植株，白毛跟分叉表現優異", "")],
    note=[("台灣目前看到的是孢子苗，個體間的葉型與分岔可能有差異。", "ajins-half-moon", "不同個體在葉型、分岔與未來表現上皆可能產生變化", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}|{B4C}"),
)
BLOCKS["willinckii-silver-phoenix"] = dict(
    cites=[c("ajins-silver-phoenix", "fertile_hair", 5, "大量細緻的銀白色絨毛", "大量銀白絨毛 → 5", "銀鳳凰特徵是擁有大量細緻的銀白色絨毛")],
    desc=[("銀白色絨毛細密、植株對稱，孢子葉略寬厚，生長較快。", "ajins-silver-phoenix",
           "擁有大量細緻的銀白色絨毛 植株對稱優美，孢子葉也稍微比較寬厚一些 相較於其他鹿角蕨品種，銀鳳凰生長速度較快", "")],
    note=[("台灣目前看到的是孢子苗。", "ajins-silver-phoenix", "新品 | 銀鳳凰鹿角蕨P.Silver phoenix 孢子苗", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}", f"{AJ}（只有標題標籤「中光」，不採用）|{B4C}"),
)
BLOCKS["veitchii-no-shield"] = dict(
    cites=[
        c("ajins-veitchii-no-shield", "light", 3, "散光通風環境", "bright filtered light → 3", "適合在陽台等處以散光通風環境栽種"),
        c("ajins-veitchii-no-shield", "difficulty", 1, "相對好照顧", "好照顧 → easy → 1", "它屬於相對好照顧的觀葉植物"),
        c("ajins-veitchii-no-shield", "size", "~S", "外觀呈類侏儒形態", "只說外觀像侏儒，不是稱它為侏儒 → 不算侏儒說法；當小型描述記為寬鬆 S（v1.4）",
          "外觀呈類侏儒形態"),
    ],
    desc=[("沒有營養葉，只長孢子葉，外觀類似侏儒型；孢子葉白皙、微波浪分岔。", "ajins-veitchii-no-shield",
           "其主要特色是沒有營養葉，只有孢子葉生長 外觀呈類侏儒形態，葉片白皙且帶有微波浪分岔的質感", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}|微體溫室〈銀鹿〉（未列）", f"{AJ}|{B4C}"),
)
BLOCKS["bifurcatum-dwarf"] = dict(
    cites=[
        c("ajins-bifurcatum-dwarf", "size", "S", "侏儒", "來源稱侏儒、沒有尺寸 → S", "侏儒二叉鹿角蕨是一款小巧、好養，又有漂亮株型的侏儒鹿角蕨"),
        c("ajins-bifurcatum-dwarf", "fertile_posture", "up", "孢子葉集中向上生長", "", "孢子葉會集中向上生長"),
        c("ajins-bifurcatum-dwarf", "light", 3, "光線需求中等，明亮通風即可", "中光、明亮 → 3", "光線需求中等，不需要特別追求高光或特殊環境，在明亮、通風的空間就能穩定培養"),
        c("ajins-bifurcatum-dwarf", "difficulty", 1, "相當容易入門", "", "對第一次接觸鹿角蕨的新手來說也相當容易入門"),
    ],
    desc=[("孢子葉集中向上生長，整株像一束捧花。", "ajins-bifurcatum-dwarf", "孢子葉會集中向上生長 ... 整株就像捧在手中的一束綠色捧花", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}|微體溫室〈侏儒鹿角蕨〉（未列）", f"{AJ}|{B4C}"),
)
BLOCKS["veitchii-lemoinei-dwarf"] = dict(
    cites=[
        c("ajins-lemoinei-dwarf", "size", "S", "侏儒", "來源稱侏儒、沒有尺寸 → S", "侏儒檸檬鹿角蕨將檸檬鹿角蕨原本細緻的葉型進一步濃縮在更加迷你的株型中"),
        c("mo-lemoinei", "size", "S", "侏儒檸檬，體型不到一般檸檬的 ½", "來源稱侏儒、沒有尺寸 → S", "體型是一般檸檬鹿角蕨的 ½ 大小不到"),
        c("ajins-lemoinei-dwarf", "fertile_posture", "spread", "葉片集中向外展開", "spreading → spread", "葉片集中向外展開"),
        c("mo-lemoinei", "fertile_hair", 3, "孢子葉白毛感明顯", "明顯有毛 → 3", "孢子葉的白毛感明顯"),
        c("ajins-lemoinei-dwarf", "light", 5, "可適應較高光，光線充足下株型更好", "高光、光線充足 → 5",
          "栽培上也能適應較高光的環境，在光線充足、通風良好的條件下培養，更容易展現緊湊漂亮的株型"),
        c("mo-lemoinei", "light", "2–3", "中弱至中光", "中弱光介於低弱光（1）與中光（3）→ 2；至中光 → 2–3", "檸檬鹿角蕨日照｜中至中強光｜中至中強光｜中弱至中光（第三欄為侏儒檸檬）"),
        c("mo-lemoinei", "water", 1, "各品系：耐旱喜透氣、澆透不積水", "文章說各品系照顧相似、耐旱 → 1",
          "檸檬鹿角蕨雖有不同品系之分，然而在照顧上卻有許多相似之處：充足日照、耐旱喜透氣、澆透不積水"),
    ],
    desc=[("比檸檬的分岔更細、更密，株型緊湊。", "ajins-lemoinei-dwarf", "相較一般檸檬，它的孢子葉分岔更細、更小也更加密集", ""),
          ("營養葉淺綠，孢子葉短、覆白毛；可馴化到 6~8 小時日照，是少數能露養的侏儒品種。", "mo-lemoinei",
           "1. 營養葉呈淺綠 2. 孢子葉手短覆白毛 ... 侏儒檸檬鹿角蕨是少數能挑戰露養的侏儒品種，可馴化逐漸增加日照至 6~8 小時", "")],
    searched=searched(f"{AJ}|微體溫室〈檸檬鹿角蕨〉|{WEB}", f"{AJ}|微體溫室〈檸檬鹿角蕨〉（沒有侏儒檸檬的難度）"),
)
BLOCKS["willinckii-yellow-moon-dwarf"] = dict(
    cites=[
        c("ajins-yellow-moon-dwarf", "size", "S", "侏儒型個體", "來源稱侏儒、沒有尺寸 → S", "為經典黃月鹿角蕨孢子苗中篩選出的侏儒型個體"),
        c("mo-dwarf", "size", "S", "侏儒爪哇", DWC, f"{DWT} ... 侏儒黃月鹿角蕨｜中偏難"),
        c("ajins-yellow-moon-dwarf", "origin", "從黃月孢子苗篩選", "黃月孢子苗篩選", "沒有 T1、T2，採 T3", "為經典黃月鹿角蕨孢子苗中篩選出的侏儒型個體"),
        *mo_guide("侏儒黃月", 5, 3),
        mo_rate("mo-dwarf", "侏儒黃月鹿角蕨", "中偏難", DW),
        mo_rate("mo-moon", "侏儒黃月鹿角蕨", "中偏難", MOONT),
        c("mo-moon", "water", 1, "室內或弱光：介質偏乾再澆", "drying between waterings → 1",
          "栽培於室內或弱光環境的侏儒黃月鹿角蕨，就可以等到介質偏乾時再澆水"),
    ],
    desc=[("孢子葉細長，覆白皙絨毛。", "ajins-yellow-moon-dwarf", "孢子葉細長延展 ... 搭配白皙細緻的絨毛", ""),
          ("孢子葉纖細，葉背帶淡金色；孢子苗變化大，衍生出迦具夜、亞森等收藏家命名個體。", "mo-expensive",
           "整體孢子葉纖細精緻如藝術品、葉背更帶有特殊的淡金色 ... 由於侏儒黃月孢子苗變化大，更有不少收藏家的命名個體，如：迦具夜、迦納、亞森等", ""),
          ("微體溫室建議夏季移到室內控溫環境，並避免午後淋雨。", "mo-moon", "尤其侏儒黃月鹿角蕨建議移至室內控溫環境渡夏，也盡量避免午後淋雨", "")],
    note=[("晴花鹿苑網址為 yellow-moon-dwarf 的頁面販售的是命名個體「琥珀 Kohaku」，不確定是否同一植物，型態描述不採用。", "haruhana-yellow-moon-dwarf",
           "晴花鹿苑典藏鹿角蕨 P.willinckii Kohaku 琥珀 ... 一直是鹿友間爭相收藏的侏儒奢華逸品", "")],
    searched=searched(f"{AJ}|微體溫室〈侏儒鹿角蕨〉〈月亮系列〉〈鹿角蕨為什麼那麼貴〉|晴花鹿苑〈琥珀〉（不採用）",
                      f"{MOS}|微體溫室〈侏儒鹿角蕨〉〈月亮系列〉（幼苗控溫 22~28 度是適溫，不是建議最低／最高溫）"),
)
BLOCKS["hillii-wave"] = dict(
    cites=[
        c("ajins-hillii-wave", "origin", "從 P. hillii 'Pumila' 播孢特選", "Pumila 播孢特選", "沒有 T1、T2，採 T3",
          "是由歷史悠久的經典深綠園藝品種(Platycerium hillii 'Pumila')播孢特選而來"),
        c("ajins-hillii-wave", "light", 3, "半日照、光線不過強", "半日照 → 3", "在半日照且不過強的光線環境下，葉型表現最為優雅柔順"),
        c("ajins-hillii-wave", "difficulty", 1, "非常好種", "", "生長穩定、適應力佳，非常好種且觀賞性高"),
    ],
    desc=[("葉緣明顯波浪起伏，葉尾尖。", "ajins-hillii-wave", "葉緣呈現明顯波浪起伏，搭配尖葉尾線條", "")],
    note=[("阿金的便秘花園寫由深綠園藝品種 P. hillii 'Pumila' 播孢特選而來。", "ajins-hillii-wave",
           "是由歷史悠久的經典深綠園藝品種(Platycerium hillii 'Pumila')播孢特選而來", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}|微體溫室〈深綠鹿角蕨〉（未列）", f"{AJ}|{B4C}"),
)
BLOCKS["kitshakood-round-frond"] = dict(
    cites=[
        c("ajins-kitshakood-round", "origin", "從亞皇中篩選的圓葉個體", "亞皇篩選", "沒有 T1、T2，採 T3", "為經典亞皇鹿角蕨中所篩選出的圓葉型個體"),
        c("ajins-kitshakood-round", "light", 3, "半日照即可穩定培養", "半日照 → 3", "半日照環境即可穩定培養"),
    ],
    desc=[("營養葉比一般亞皇更圓潤飽滿。", "ajins-kitshakood-round", "相較一般亞皇，其營養葉更加圓潤飽滿", "")],
    searched=searched(f"{AJ}|{WEB}|{B4}|微體溫室〈亞猴鹿角蕨〉（未列）", f"{AJ}|{B4C}"),
)
BLOCKS["uncia"] = dict(
    cites=[
        c("haruhana-uncia", "size", "~M", "中小型", SMALL + "；v1.4 記為寬鬆 M", "成株尺寸為中小型"),
        c("haruhana-uncia", "fertile_posture", "spread", "葉型向外展開", "spreading → spread", "美麗霸氣的葉型向外展開"),
    ],
    desc=[("成株中小型，冠型小巧，孢子葉白皙、末端多岔如小爪；生長慢、芽量少。", "haruhana-uncia",
           "成株尺寸為中小型，帶著迷人的小巧精緻的冠型。其孢子葉帶著白皙絨毛的質感 ... 末端多岔型態猶如小爪子般 ... 其生長速度緩慢，芽量低少", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["tide"] = dict(
    cites=[
        c("haruhana-tide", "fertile_posture", "spread", "葉片放射狀姿態", "spreading → spread", "葉片展現出迷人的放射狀姿態"),
        c("haruhana-tide", "fertile_hair", 3, "墨綠基調上覆滿細緻白色絨毛", "看得出底色 → 3", "於墨綠基調上覆滿細緻的白色絨毛"),
    ],
    desc=[("孢子葉放射狀展開、脈絡寬厚清晰，墨綠底上覆細緻白毛，冠型小巧。", "haruhana-tide",
           "葉片展現出迷人的放射狀姿態，白皙的色澤映襯出寬厚而清晰的脈絡紋理。於墨綠基調上覆滿細緻的白色絨毛 ... 小巧精緻的冠型", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-ccs"] = dict(
    cites=[
        c("haruhana-ccs", "fertile_hair", 5, "臉與手有濃密白皙絨毛", "very densely → 5", "臉與手有著濃密的白皙絨毛質感"),
        c("haruhana-ccs", "shield_hair", 5, "臉與手有濃密白皙絨毛", "very densely → 5", "臉與手有著濃密的白皙絨毛質感 ... 營養葉的部分也完美的繼承了這樣的特點"),
    ],
    desc=[("高冠厚葉，盾葉與孢子葉都有濃密白毛；晴花鹿苑的商品名為「棉花雲」。", "haruhana-ccs",
           "棉花雲 ... 高冠厚葉的P. willinckii CCS最大的特點就是臉與手有著濃密的白皙絨毛質感", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-makigumo"] = dict(
    cites=[c("haruhana-makigumo", "spore", "tips", "孢子集中於葉端", "", "孢子成熟時，特徵明顯地集中於葉端")],
    desc=[("孢子葉亞成株時末端外捲、成株後內捲，分岔極短微捲，帶厚實星狀白毛。", "haruhana-makigumo",
           "在亞成階段時，孢子葉末端優雅地向外捲曲；進入成株階段後，葉端則奇妙地內捲 ... 岔型極短微捲，並覆蓋厚實的星狀白毛", "")],
    note=[("晴花鹿苑首度自行命名的品種。", "haruhana-makigumo", "「卷雲」是晴花鹿苑首度自行命名的鹿角蕨品種。", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-makigumo"]["cites"].append(
    c("haruhana-makigumo", "fertile_hair", 5, "覆蓋厚實的星狀白毛", "厚實白毛 → 5", "並覆蓋厚實的星狀白毛"))
BLOCKS["willinckii-white-heaven"] = dict(
    cites=[c("haruhana-white-heaven", "fertile_posture", "spread", "孢子葉如羽翼向兩側展開", "spreading → spread", "孢子葉如羽翼般向外兩側展翅")],
    desc=[("高冠翠綠，孢子葉如羽翼向兩側展開，白毛明顯。", "haruhana-white-heaven",
           "有著高聳翠綠的美麗冠型，同時孢子葉如羽翼般向外兩側展翅，優雅白皙的絨毛感", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-white-rose"] = dict(
    cites=[],
    desc=[("孢子葉寬厚白皙。", "haruhana-white-rose", "基因穩定表現出迷人寬厚的孢子葉特色 ... 喜歡寬、厚、白的鹿友", "")],
    note=[("晴花鹿苑販售的是孢子苗，稱基因穩定。", "haruhana-white-rose", "白玫瑰孢子苗，基因穩定表現出迷人寬厚的孢子葉特色", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-yami"] = dict(
    cites=[c("haruhana-yami", "difficulty", 1, "新手友善、易於養護", "", "也是一款新手友善易於養護的品項")],
    desc=[("細緻款的白爪哇，高冠，孢子葉細長飄逸。", "haruhana-yami", "P.willinckii Yami是一款細緻款的白哇 整體的高冠層次豐富，特別是孢子葉的型態細長而優雅", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}|{B4}"),
)
BLOCKS["sunny-cutie"] = dict(
    cites=[
        c("haruhana-sunny-cutie", "size", "S", "迷你爪哇", "來源稱迷你（mini）、沒有尺寸 → S", "罕見細緻型的迷你爪哇，整體成株體型嬌小"),
        c("haruhana-sunny-cutie", "fertile_posture", "pendant", "孢子葉如流水般下墜", "pendulous → pendant", "孢子葉修長優雅，宛如流水悠長的下墜姿態"),
    ],
    desc=[("迷你冠型，孢子葉修長下垂，末端捲翹。", "haruhana-sunny-cutie", "擁有縮小版的迷你冠型。此外孢子葉修長優雅，宛如流水悠長的下墜姿態，末端帶有捲翹的型態", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)
BLOCKS["willinckii-anne"] = dict(cites=[], searched=searched(f"{HR}（只有照片與出貨說明）|{WEB}|{B4}", f"{HR}（只有照片）|{B4}"))
BLOCKS["willinckii-bogie"] = dict(cites=[], searched=searched(f"{HR}（只有照片與出貨說明）|{WEB}|{B4}", f"{HR}（只有照片）|{B4}"))
BLOCKS["wfsq"] = dict(
    cites=[
        c("haruhana-wfsq", "fertile_posture", "spread", "孢子葉向兩側伸展", "spreading → spread", "其孢子葉優雅地向兩側伸展"),
        c("haruhana-wfsq", "fertile_hair", 3, "明顯而細緻的白色星狀絨毛", "明顯有毛 → 3", "表面覆有明顯而細緻的白色星狀絨毛"),
        c("haruhana-wfsq", "difficulty", 1, "養護容易，適合台灣多數環境", "", "整體養護容易，非常適合台灣多數的栽培環境"),
    ],
    desc=[("孢子葉厚實、向兩側伸展，呈不規則大波浪，末端多重短叉，覆星狀白毛。", "haruhana-wfsq",
           "其孢子葉優雅地向兩側伸展，葉片質地厚實，表面覆有明顯而細緻的白色星狀絨毛。孢子葉呈現不規則的大波浪狀曲線，末端分岔出多重短叉", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}|{B4}"),
)
BLOCKS["willinckii-anapat-1"] = dict(
    cites=[c("haruhana-anapat-1", "size", "~S", "母本成熟時體型偏小", SMALL + "；v1.4 記為寬鬆 S", "母本成熟時體型偏小")],
    desc=[("母本成熟時體型偏小，孢子葉秀氣精緻。", "haruhana-anapat-1", "母本成熟時體型偏小，擁有秀氣且精緻的孢子葉", "")],
    note=[("台灣目前看到的是孢子苗。", "haruhana-anapat-1", "經典款 P. willinckii Anapat 1 孢子苗。", "")],
    searched=searched(f"{HR}|{WEB}|{B4}", f"{HR}（沒有照護資料）|{B4}"),
)


# ---------------------------------------------------------------- FSQ line (2026-10-18): Wanna's Foongsiqi sporelings and their named selections
# Plants are listed when Wanna's own catalog sells them under the name and the staghornfern.org database (Wayback) lists them as
# Foongsiqi F2 by Wanna. Names found in only one of the two are left out (see species_list.md). Searches by name found no other page.
def wc(ym):
    return f"wanna-cat-{ym}"

WS = "I Love Ferns（Wanna）2020–2026 月型錄|staghornfern.org 交種資料庫（Wayback）|搜尋：英文品名＋Platycerium|晴花鹿苑、阿金、Haruhana USA 站內搜尋|World Platycerium Society 登錄"
WSC = f"{WS}（型錄只有品名與價格，沒有照護資料）"
BLOCKS["fsq"] = dict(
    cites=[c(wc("2020-11"), "origin", "Wanna 以 Foongsiqi 播孢的孢子苗", "FSQ Sporelings (Foongsiqi spore plant)", "T3，origin 只採 T1",
             "No.20 P. FSQ Sporelings (Foongsiqi spore plant)")],
    desc=[
        ("Foongsiqi（捲捲鹿）的孢子苗系，由泰國 I Love Ferns 的 Wanna 播孢培育，型錄寫作「FSQ (Foongsiqi Sporelings)」。", wc("2023-02"),
         "No.16 P. FSQ (Foongsiqi Sporelings) lot#3", ""),
        ("第一批 Foongsiqi 孢子苗約在 2008 年播出（2023 年底的型錄稱 15 年前）。", wc("2023-12"),
         "(from the first batch of Foongsiqi sporeling 15 years ago)", ""),
        ("孢子苗是有性繁殖的後代，可能和親本長得不同；", FSQ, "孢子苗則是由孢子囊播孢培育的有性繁殖個體，雖然捲捲鹿的遺傳穩定性高，但還是有機率孢子苗（小孩）與親本（父母）長的不同", ""),
        ("Wanna 從中選出多個個體另外命名，型錄在品名後標 (FSQ)。", wc("2023-02"), "Kin-Norn is Cultivar from spore propagation of Foongsiqi", ""),
    ],
    note=[
        ("Wanna 的型錄把無性繁殖的「Foongsiqi Original（No TC）」和 FSQ 孢子苗分開販售。", wc("2020-09"), "No.16 P. Foongsiqi Original (No TC)", ""),
        ("微體溫室把 FSQ 和銀華都稱為捲捲鹿的孢子苗特選個體。", FSQ, "如 FSQ、銀華鹿角蕨等皆是捲捲鹿的孢子苗特選個體", ""),
        ("晴花鹿苑則把 FSQ 當成 Foong Si Qi 本身的別名。", "haruhana-usa-sazanami", "hand-selected Platycerium 'Foong Siqi' (FSQ) sporelings", ""),
    ],
    searched=searched(WS, WSC),
)
BLOCKS["little-sis"] = dict(
    cites=[],
    desc=[("型態像母本 Foongsiqi，但葉面有毛而呈淺灰綠色；孢子囊斑厚，使葉尖略捲。", wc("2020-03"),
           "This specimen has form looks alike its mother (Foongsiqi) but color leaves are light green-grey because have hairs and spore patches are thick make their tips are a bit curly.", "")],
    searched=searched(WS, WSC),
)
BLOCKS["wannasiqi"] = dict(
    cites=[],
    note=[("Wanna 稱它出自約 15 年前第一批 Foongsiqi 孢子苗。", wc("2023-12"), "No.47 P. Wannasiqi (FSQ) Sporeling (from the first batch of Foongsiqi sporeling 15 years ago)", "")],
    searched=searched(WS, WSC),
)
BLOCKS["kusuma"] = dict(
    cites=[],
    note=[("Wanna 的影片標題寫作「FSQ No. 16 (Kusuma)」。", "wanna-yt-kusuma", "Platycerium FSQ No. 16 (Kusuma)", "")],
    searched=searched(WS, WSC),
)
BLOCKS["ivory"] = dict(
    cites=[],
    note=[("Wanna 的型錄寫作 Ivory (FSQ#19)。", wc("2023-11"), "No.17 P. Ivory(FSQ#19) Sporelings", "")],
    searched=searched(WS, WSC),
)
BLOCKS["kin-naree"] = dict(
    cites=[],
    note=[("Wanna 以它和爪哇 Schofield Tatsuta 雜交出 Tinkerbell。", wc("2026-08"), "No.17 P. Tinkerbell # 08 Original (Kinnaree(FSQ) x willinckii Schofield)", "")],
    searched=searched(WS, WSC),
)
BLOCKS["kin-norn"] = dict(
    cites=[],
    note=[("Wanna 的型錄註明它是從 Foongsiqi 孢子苗選出的品種。", wc("2023-02"), "Kin-Norn is Cultivar from spore propagation of Foongsiqi", "")],
    searched=searched(WS, WSC),
)
for pid in ("green-moon", "cotton-moon", "fsq-dwarf", "oliver-siqi", "thipsiqi"):
    BLOCKS[pid] = dict(cites=[], searched=searched(WS, WSC))
HUS = "haruhana-usa-sazanami"
BLOCKS["sazanami"] = dict(
    cites=[
        c(HUS, "size", "S", "dwarf selection", "來源稱侏儒、沒有尺寸 → S", "is a dwarf selection derived from hand-selected Platycerium 'Foong Siqi' (FSQ) sporelings"),
        c(HUS, "origin", "晴花鹿苑（台灣）由 Foong Si Qi 孢子苗選出", "Haruhana garden in Taiwan", "T3，origin 只採 T1",
          "derived from hand-selected Platycerium 'Foong Siqi' (FSQ) sporelings at Haruhana garden in Taiwan"),
    ],
    desc=[("株型緊湊，孢子葉深裂、呈波浪狀，像水面的漣漪。", HUS, "prized for its compact habit and wavy, deeply notched fertile fronds that mimic gentle water crests", "")],
    note=[("名字由日本收藏家所取，意思是漣漪。", HUS, "Named Sazanami (\"Ripples\") by a Japanese collector", ""),
          ("母本是晴花鹿苑園區自家的 Foong Si Qi（晴花鹿苑稱 FSQ）。", HUS, "hand-selected Platycerium 'Foong Siqi' (FSQ) sporelings at Haruhana garden in Taiwan", "")],
    searched=searched(f"Haruhana USA 商品頁|World Platycerium Society 登錄|{WEB}", "Haruhana USA 商品頁（沒有照護資料）"),
)
# ---------------------------------------------------------------- PlatyWiki 品種清單的獨立查證 (2026-10-18)
# PlatyWiki 是公開編輯的二手彙整，不引用；它列的品種另找原始來源。'Tiara'、'天堂鳥'、'霧氷'、'異變銀' 找不到兩個單位，暫不收錄（見 species_list.md §六）。
PWS = "搜尋：英文品名＋Platycerium|ビカク図鑑（T4，只看出典）|staghornfern.org 交種資料庫（Wayback）|Halling|Siam Exotica（Wayback）|aucfan／Yahoo!オークション 拍賣紀錄|晴花鹿苑、阿金、微體溫室全站|World Platycerium Society 登錄"
BLOCKS["durval-nunes"] = dict(
    cites=[
        c("platyceriumferns-durval", "shield_vein", "yes", "像非猴一樣有鬆餅狀質感", "waffle → yes",
          "Like P.madagascariense it has the waffle like texture and grasping shields."),
        c("platyceriumferns-durval", "pups", "yes", "可用孢子和側芽繁殖", "propagated by pups → yes",
          "I know that this cultivar can be propagated by spore and pups."),
        c("siam-sale-newhybrids", "parents", "madagascariense", "非猴 × ?", "第二個親本不明", "P.\"Durval Nunes\" (P.madagascariense x ?)"),
        c("platyceriumferns-durval", "parents", "madagascariense", "非猴 × 另一種", "第二個親本不明",
          "P.'Durval Nunes' is a cross with P.madagascariense and another platycerium fern."),
        c("exotica-madagascariense", "parents", "madagascariense", "非猴 × 不明（傳說是四叉）", "第二個親本不明；四叉一說作者自己標為傳聞",
          "spontaneous hybrids involving an unknown second parent, such as Durval Nunes (although allegedly another cross x P. quadridichotum)"),
        c(HH, "parents", "madagascariense|quadridichotomum", "非猴 × 四叉（依照片推測）", "Halling 看 Siam Exotica 的照片推測，只供參考",
          "From the photo they give, this author believes it is a cross of P. madagascariense and P quadridichotomum", "", "reference"),
        c("sf-hybrid-db", "parents", "madagascariense|stemaria", "非猴 × 三角", "T4 只當線索；沒有找到這個說法的原始來源",
          "P. Durval Nunes | Madagascariense | Stemaria | —", "", "reference"),
    ],
    extra={"parents"},
    desc=[
        ("非猴與另一種鹿角蕨的交種，第二個親本不明。", "siam-sale-newhybrids", "P.\"Durval Nunes\" (P.madagascariense x ?)", ""),
        ("和非猴一樣有鬆餅狀的凹凸質感，盾葉會抱住附著物；可用孢子或側芽繁殖。", "platyceriumferns-durval",
         "Like P.madagascariense it has the waffle like texture and grasping shields. ... this cultivar can be propagated by spore and pups.", ""),
    ],
    note=[
        ("Exotica Esoterica 稱它是第二親本不明的自然雜交，另有一說是與四叉的雜交。", "exotica-madagascariense",
         "spontaneous hybrids involving an unknown second parent, such as Durval Nunes (although allegedly another cross x P. quadridichotum)", ""),
        ("Halling 依 Siam Exotica 的照片推測是非猴 × 四叉，也就是和 Charles Alford 的非猴 × 四叉相同。", HH,
         "From the photo they give, this author believes it is a cross of P. madagascariense and P quadridichotomum which would be the same as Charles Alords hybrid.", ""),
    ],
    searched=searched(PWS, f"{PWS}（只有 platyceriumferns.com 提到繁殖方式，沒有照護資料）"),
)
BLOCKS["willinckii-totoro"] = dict(
    cites=[
        c("basements-totoro", "size", "S", "dwarf form", "來源稱侏儒、沒有尺寸 → S",
          "'Totoro' is a dwarf form selected from Platycerium Willinckii sporelings"),
        c("naturefix-totoro", "size", "S", "ウィリンキードワーフ", "來源稱侏儒、沒有尺寸 → S", "人気のウィリンキードワーフ Totoroの胞子培養株となります。"),
        c("yahoo-frontier-totoro", "size", "S", "矮性、ドワーフの性質", "來源稱侏儒、沒有尺寸 → S",
          "イエロームーンの胞子苗の中から矮性、ドワーフの性質がある個体の中から選ばれました。"),
        c("yahoo-frontier-totoro", "origin", "從黃月孢子苗選出的侏儒個體", "黃月孢子苗選拔", "沒有 T1、T2，採 T3",
          "ビカクシダ・ウィリンキー・トトロはビカクシダ・ウィリンキー・イエロームーンの選抜品種。"),
        c("basements-totoro", "light", 3, "明亮散射光或輕微遮光的日照", "bright indirect → 3",
          "Light : Bright indirect light or lightly filtered sunlight; avoid harsh direct light"),
        c("basements-totoro", "humidity", 5, "濕度 70–90%", "high humidity → 5", "Humidity : 70–90%"),
        c("basements-totoro", "difficulty", 3, "Difficulty Level 3", "美國來源，只供參考", "Difficulty Level : 3", "", "reference"),
        c("yahoo-frontier-totoro", "base", "willinckii-yellow-moon-dwarf", "", "黃月孢子苗中的矮性個體，屬黃月侏儒系 → 侏儒黃月",
          "数あるイエロームーンドワーフの品種の中でも有名で人気のある品種。"),
        c("yahoo-frontier-totoro", "aka", "", "トトロ、豆豆龍", "拍賣標題的日文名與中文名", "ビカクシダ・ウィリンキー・トトロ 胞子苗 豆豆龍"),
    ],
    extra={"base", "aka"},
    desc=[
        ("從黃月孢子苗中挑出有矮性的個體選拔而成，是黃月侏儒系中有名的品種。", "yahoo-frontier-totoro",
         "イエロームーンの胞子苗の中から矮性、ドワーフの性質がある個体の中から選ばれました。数あるイエロームーンドワーフの品種の中でも有名で人気のある品種。", ""),
        ("株型緊湊圓胖，盾葉圓；孢子葉短而柔軟，葉尖略捲。", "basements-totoro",
         "identified by its compact size, round shield fronds, and soft, plush fertile fronds that curl slightly at the tips", ""),
        ("孢子葉分岔多，葉尖纖細。", "yahoo-frontier-totoro", "分岐数も多く繊細な葉先でとても魅力的な品種です。", ""),
    ],
    note=[
        ("日本拍賣有標示從台灣 HHR Garden 正規輸入的孢子苗。", "yahoo-hhr-totoro", "台湾のHHR Gardenより正規輸入した、Totoroの胞子苗です。", ""),
        ("The Basements 提醒孢子苗要長大後才會顯出 Totoro 的型態。", "basements-totoro",
         "Sporelings at this stage may not yet fully express the mature form", ""),
    ],
    searched=searched(PWS, f"{PWS}（只有 The Basements 有照護資料）"),
)
BLOCKS["willinckii-grace"] = dict(
    cites=[
        c("yahoo-vandaka-grace", "size", "S", "強度の高い矮性、スーパードワーフ種", "來源稱侏儒、沒有尺寸 → S",
          "強度の高い矮性と白さに加え、葉先が内巻きにカールする次世代のスーパードワーフ種です。"),
        c("yahoo-vandaka-grace", "origin", "侏儒 Nook 的選拔", "willinckii dwarf Nook 選拔", "沒有 T1、T2，採 T3",
          "willinckii dwarf Nookからの選抜品種です。"),
        c("yahoo-vandaka-grace", "base", "willinckii-nook-dwarf", "", "dwarf Nook 的選拔 → 侏儒 Nook", "willinckii dwarf Nookからの選抜品種です。"),
    ],
    extra={"base"},
    desc=[
        ("侏儒 Nook 的選拔，矮性強、株色白，葉尖向內捲，明顯捲超過一圈。", "yahoo-vandaka-grace",
         "willinckii dwarf Nookからの選抜品種です。強度の高い矮性と白さに加え、葉先が内巻きにカールする ... こちらは1回転以上明確に巻きます", ""),
        ("在 LED 燈下也能正常展開，不容易走樣。", "yahoo-vandaka-grace", "LED光でも素直に展開し形崩れしにくいのも特徴かと。", ""),
    ],
    note=[
        ("2024 年日本拍賣的孢子苗標示是 HHR 所有的 Grace 母株播的孢子。", "yahoo-grace-2024",
         "HHRが所有するP.willinckii Graceの胞子培養株になります。", ""),
        ("2026 年 vandaka plants 在日本拍賣的選拔孢子苗以 190 萬日圓結標。", "yahoo-vandaka-grace", "現在 1,901,000 円 （税0円） ... 102 件 ... 終了", ""),
    ],
    searched=searched(PWS, f"{PWS}（拍賣頁沒有照護資料）"),
)


# ---------------------------------------------------------------- v1.4 B1 (2026-10-19): 銀鹿、二叉、深綠的品系 (batches_v1.4.md)
# Cited pages re-read for relaxed statements ("~" values, guideline v1.4), then up to 5 new lookups per plant.
# English searches by name found nothing for the Asian selections; Japanese searches returned no cultivar pages.
B1 = "2026-10-19"
B1S = "v1.4 重讀已引用頁面"


def v14(pid, cites=(), desc=(), note=(), star="", care="", date=B1):
    add(pid, cites, desc, note, star, care)
    BLOCKS[pid].update(version="v1.4", date=date)


HAR, HAKKI = "haruhana-raijin", "haruhana-akki"
MONKEY = "奧銀與爪哇的交種。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉"
NETH = "搜尋：Platycerium bifurcatum 'Netherlands' staghorn compact fronds upright|Foliage Factory、The Plant Company、Cornell Farms 商品頁（Cornell 只有種的通用描述，不採用）"
NOEN = "搜尋：英文品名＋Platycerium staghorn（沒有該品系的頁面）"
NOJA = "搜尋：ビカクシダ＋品名（沒有該品系的頁面）"
v14("veitchii-auburn-river",
    [c("mo-silver", "size", "~150", "整株高度超過 150 公分", "整株高度、只給下限 → 寬鬆 D = 150", "整體植株高度超過 150 公分以上，是相當壯麗的銀白品系之一"),
     c("mo-silver", "shield_height", "~3", "營養葉尖冠明顯，如珊瑚向外展開", "高冠 → 寬鬆 3", "澳銀鹿角蕨屬於營養葉尖冠明顯的銀鹿鹿角蕨品系，如珊瑚般向外展開"),
     c("ajins-auburn-river", "shield_height", "~3", "極細長的高冠", "高冠 → 寬鬆 3", "特色就是擁有極細長的高冠"),
     c(KP, "shield_hair", "~5", "臉手全銀", "整片銀白 → 寬鬆 5", "澳銀 奧本河銀葉009 | P. veitchii\"Auburn River\" 臉手全銀！很美"),
     c(KP, "fertile_hair", "~5", "臉手全銀", "整片銀白 → 寬鬆 5", "澳銀 奧本河銀葉009 | P. veitchii\"Auburn River\" 臉手全銀！很美")],
    desc=[("整株高度可超過 150 公分。", "mo-silver", "整體植株高度超過 150 公分以上", "")],
    star=f"{B1S}（微體溫室〈銀鹿〉、阿金、卡呸醬）|{NOEN}")
v14("veitchii-ar-1",
    [c(ZYX, "shield_height", "~3", "細尖的高冠", "高冠 → 寬鬆 3", "自選個體，奧銀鹿角蕨之孢子苗，具有細尖的高冠，相當迷人。")],
    star=f"{B1S}（竹意軒）")
v14("veitchii-akki",
    [c(HAKKI, "shield_height", "~3", "高而強烈的尖冠", "高冠 → 寬鬆 3", "因此讓Akki有著高而強烈的尖冠"),
     c(HAKKI, "fertile_hair", "~3", "孢子葉白而細緻", "白 → 有白毛，寬鬆 3", "孢子葉白而細緻，且挺拔的向上昂揚"),
     c(HAKKI, "fertile_posture", "~up", "孢子葉挺拔向上昂揚", "挺拔向上 → 寬鬆 up", "孢子葉白而細緻，且挺拔的向上昂揚"),
     c(ZYX, "shield_height", "~3", "成熟時冠高", "冠高 → 寬鬆 3", "成熟表現冠高，型態狂暴粗曠"),
     c(ZYX, "fertile_posture", "~up", "光線充足時也會向上生長", "光線充足時向上 → 寬鬆 up", "光線充足時也會向上生長"),
     c("ajins-akki", "shield_height", "~3", "承襲澳銀細尖高冠", "高冠 → 寬鬆 3", "承襲了澳銀細尖高冠，且遺傳兩者的白毛與細緻。"),
     c("ajins-akki", "fertile_hair", "~3", "有白毛", "有白毛 → 寬鬆 3", "承襲了澳銀細尖高冠，且遺傳兩者的白毛與細緻。")],
    desc=[("晴花鹿苑寫它的尖冠高而強烈，孢子葉白、細緻，挺拔向上。", HAKKI, "因此讓Akki有著高而強烈的尖冠，孢子葉白而細緻，且挺拔的向上昂揚。", "")],
    star=f"{B1S}（竹意軒、晴花鹿苑、阿金）|{NOEN}")
v14("veitchii-lemoinei",
    [c("mo-lemoinei", "size", "~60", "孢子葉長可超過 60 公分", "孢子葉長只給下限 → 寬鬆 D = 60", "覆滿白絨毛的孢子葉手長可超過 60 公分"),
     c("joshsfrogs-lemoinei", "size", "~61", "成株高可達 24 吋", "整株高度上限 24 in ≈ 61 cm → 寬鬆 D", "Height at Maturity: Up to 24 inches"),
     c("mo-lemoinei", "fertile_length", "~≥60 cm", "孢子葉長可超過 60 公分", "只給下限 → 寬鬆說法", "覆滿白絨毛的孢子葉手長可超過 60 公分"),
     c("mo-lemoinei", "shield_height", "~3", "尖冠高可達 30~45 公分", "高冠、上限 45 cm（< 80）→ 寬鬆 3", "營養葉的特化尖冠高度可達 30~45 公分"),
     c("ajins-lemon", "shield_height", "~3", "成熟營養葉有尖高冠", "高冠 → 寬鬆 3", "成熟的營養葉具尖高冠表現"),
     c("haruhana-lemoinei", "shield_height", "~3", "可愛的小冠", "有冠（直立）→ 寬鬆 3", "可愛的小冠與厚實白皙的挺立孢子葉"),
     c("mo-lemoinei", "fertile_posture", "~up", "日照充足時孢子葉聳立向上", "聳立向上 → 寬鬆 up；陽光柔和時會垂墜（寫入 desc）", "在日照充足下孢子葉會聳立向上生長"),
     c("haruhana-lemoinei", "fertile_posture", "~up", "挺立的孢子葉", "挺立 → 寬鬆 up", "可愛的小冠與厚實白皙的挺立孢子葉"),
     c("joshsfrogs-lemoinei", "light", 3, "Partial Shade", "partial shade → 3", "Lighting: Partial Shade"),
     c("joshsfrogs-lemoinei", "water", 1, "澆水後待乾；耐旱、怕積水", "drying between waterings、drought tolerant → 1",
       "Water regularly but allow the soil to dry out between watering ... Drought tolerant but sensitive to overly saturated soil"),
     c("joshsfrogs-lemoinei", "humidity", "3–5", "Moderate – Humid", "moderate 3、humid 5 → 3–5", "Humidity: Moderate (30-70%) - Humid (70-100%)"),
     c("joshsfrogs-lemoinei", "min_temp", 18.3, "65 °F 以上", "建議值；65 °F = 18.3 °C", "Temperature Requirement (°F): Above 65°"),
     c("joshsfrogs-lemoinei", "difficulty", 1, "照顧容易", "美國來源 → reference", "is easy to maintain with minimal care", "", "reference")],
    desc=[("Josh's Frogs 說孢子葉呈暗淡的藍綠色，成熟後呈鹿角狀。", "joshsfrogs-lemoinei",
           "One of the most unique looking ferns that take on an 'antler' shape as it matures ... Fronds form a dull blue-green color", "")],
    star=f"{B1S}（微體溫室〈檸檬〉、阿金、晴花鹿苑）|搜尋：Platycerium veitchii Lemoinei staghorn fern description fronds|Josh's Frogs、ReptiFiles（同文）商品頁|Rainforest Flora（不採用）",
    care="Josh's Frogs 商品頁")
v14("bifurcatum-mt-lewis",
    [c("halling-mtlewis", "shield_height", "~3", "盾葉向外長，像傘一樣替孢子葉遮陰", "向外展開 → 寬鬆 3",
       "the shield fronds grow outward forming a shade umbrella for fertile fronds."),
     c(ZYX, "fertile_width", "~3", "孢子苗具寬葉片", "孢子苗，不是成熟植株 → excluded", "貓路易士鹿角蕨孢子苗，具寬葉片。", "", "excluded")],
    star=f"{B1S}（Halling、竹意軒）|搜尋：Platycerium bifurcatum 'Mt Lewis' staghorn fern fronds size|搜尋：\"Mt Lewis\" platycerium venosum fronds veins grower"
         "|搜尋：Mount Lewis staghorn care|{NOJA}（皆只有種的描述或 Hoshizaki & Yansura 2021 摘要）")
v14("bifurcatum-mt-lewis-thin", star=f"{B1S}（竹意軒只寫「細緻孢子葉片」；品名的 Thin 不當描述）")
v14("bifurcatum-little-kitty", star=f"{B1S}（卡呸醬只有「小型品種、長手」）|搜尋：Platycerium 'Little Kitty' staghorn（沒有該品系的頁面）")
v14("bifurcatum-netherlands",
    [c("cistus-netherlands", "size", "~91", "孢子葉可達 3 呎", "孢子葉長上限 3 ft ≈ 91 cm → 寬鬆 D", "fertile fronds to up to 3 ft long"),
     c("theplantco-netherlands", "size", "~75", "株高與寬約 60–90 公分", "整株高寬，中點 75 → 寬鬆 D",
       "typically grows to around 60 to 90 centimetres tall and wide depending on growing conditions and mounting style."),
     c("foliage-factory-netherlands", "size", "~100", "栽培尺寸約高 100、寬 90 公分", "整株高寬，取較大者 100 → 寬鬆 D", "Cultivated size guide Height: 100 cm • Spread: 90 cm"),
     c("foliage-factory-netherlands", "shield_form", "~appressed", "圓形盾葉重疊包覆根部", "圓形、包覆根部 → 貼伏",
       "Rounded fronds overlap around the roots and build the fern's protective nest."),
     c("foliage-factory-netherlands", "shield_height", "~1", "圓形盾葉重疊包覆根部", "包覆附著物 → 寬鬆 1",
       "Rounded fronds overlap around the roots and build the fern's protective nest."),
     c("foliage-factory-netherlands", "fertile_posture", "~spread", "分岔的孢子葉從基部向外拱出", "向外展開 → 寬鬆 spread",
       "Longer grey-green fronds divide into forked lobes and arch away from the base."),
     c("foliage-factory-netherlands", "fertile_hair", "~3", "細毛讓孢子葉呈柔和的灰色", "有毛、灰色 → 寬鬆 3",
       "Fine natural hairs give the longer fronds their soft grey cast."),
     c("foliage-factory-netherlands", "pups", "~yes", "成株會長側芽、擴成一叢", "會長側芽、成叢 → 寬鬆 yes",
       "Mature plants can produce rooted pups and expand into a broader clump."),
     c("foliage-factory-netherlands", "light", 3, "明亮的散射光", "bright filtered light → 3", "Give the fern bright, filtered light."),
     c("foliage-factory-netherlands", "water", 1, "介質乾到五到七成再澆透", "drying between waterings → 1",
       "Water when ~50–70% dry ... When it is nearly dry, water thoroughly and let the excess drain away."),
     c("foliage-factory-netherlands", "humidity", 3, "濕度 50–60%", "moderate humidity → 3", "Aim for 50–60% humidity."),
     c("foliage-factory-netherlands", "min_temp", 10, "避免長時間低於 10 °C", "建議值", "Avoid prolonged temperatures below 10 °C."),
     c("theplantco-netherlands", "light", 3, "明亮的散射光", "bright indirect light → 3", "grows best in bright indirect light with good airflow and moderate humidity."),
     c("theplantco-netherlands", "water", 3, "介質稍乾就澆透，不要一直濕", "乾濕交替 → 3",
       "Water thoroughly when the growing medium begins to dry slightly, but avoid keeping roots constantly wet."),
     c("theplantco-netherlands", "humidity", 3, "中等濕度，乾燥時偶爾噴霧", "moderate humidity、occasional misting → 3",
       "grows best in bright indirect light with good airflow and moderate humidity ... Mist the foliage occasionally during dry weather")],
    desc=[("Foliage Factory 說它通常被當成比一般型更緊湊、室內較整齊的選拔，成熟後盤基變厚、孢子葉伸得更遠。", "foliage-factory-netherlands",
           "It is generally sold as a more compact selection that stays tidier indoors than many standard forms. ... As 'Netherlands' matures, the base becomes thicker and the antler-like fronds reach farther from the centre.", "")],
    star=f"{B1S}（Cistus、NC State）|{NETH}", care=NETH)
v14("bifurcatum-white",
    [c("haruhana-bif-white", "fertile_hair", "~3", "白皙的葉片", "白皙 → 有白毛，寬鬆 3", "在白皙的葉片上有清晰的葉脈紋理")],
    star=f"{B1S}（晴花鹿苑、卡呸醬）|搜尋：Platycerium bifurcatum white Japan cultivar（沒有該品系的頁面）")
v14("bifurcatum-popcorn", star=f"{B1S}（阿金只有「超挺拔的孢子葉」，已記）")
v14("hillii-mio", star=f"{B1S}（微體溫室〈深綠〉、卡呸醬「碎手」：沒有能換算的說法）|搜尋：Platycerium hillii 'Mio' staghorn（沒有該品系的頁面）")
v14("hillii-wide", star=f"{B1S}（卡呸醬只有名稱）")
v14("hillii-rimklong",
    [c(ZYX, "fertile_hair", "~5", "白毛濃密", "白毛濃密 → 寬鬆 5", "Rimklong為深綠鹿角蕨的個體，特色是孢子葉具綴化感，另外白毛也濃密。")],
    star=f"{B1S}（竹意軒）|搜尋：Platycerium hillii Rimklong（沒有該品系的頁面）")
v14("pewchan", star=f"{B1S}（微體溫室〈40 種〉只有表格分類）|搜尋：Platycerium 'Pewchan' staghorn（沒有該品系的頁面）")
v14("white-shine", star=f"{B1S}（微體溫室〈40 種〉、卡呸醬只有名稱）|搜尋：Platycerium 'White Shine' staghorn（沒有該品系的頁面）")
for pid, extra in [("white-monkey", "是該系列較後續發表的個體"), ("wild-monkey", "此個體的冠部較為高聳")]:
    v14(pid,
        [c(ZYX, "shield_height", "~3", "高冠", "高冠 → 寬鬆 3", f"{MONKEY}，{extra}。"),
         c(ZYX, "fertile_hair", "~3", "白絨毛", "有白絨毛 → 寬鬆 3", f"{MONKEY}，{extra}。"),
         c(ZYX, "fertile_posture", "~pendant", "下墜的孢子葉", "下垂 → 寬鬆 pendant", f"{MONKEY}，{extra}。")],
        star=f"{B1S}（竹意軒）|搜尋：Platycerium \"Wild Monkey\" OR \"White Monkey\" staghorn（沒有該品系的頁面）")
v14("salmon", star=f"{B1S}（卡呸醬「寬葉深裂，孢子葉末端趨細」：寬葉與末端細互相矛盾，不換算裂片寬度）")
v14("veitchii-wild",
    [c("mo-silver", "shield_height", "~3", "營養葉尖冠細長、集中向上", "高冠 → 寬鬆 3", "然而營養葉尖冠更細長且集中向上"),
     c("haruhana-veitchii-wild", "shield_height", "~3", "細尖高冠", "高冠 → 寬鬆 3", "其特殊的細尖高冠一直以來辨識度極強，以及挺立昂揚的孢子手"),
     c("haruhana-veitchii-wild", "fertile_posture", "~up", "挺立昂揚的孢子葉", "挺立 → 寬鬆 up", "以及挺立昂揚的孢子手")],
    desc=[("晴花鹿苑說它生長緩慢，但耐受性強、不怕日曬。", "haruhana-veitchii-wild", "雖然成長緩慢，但對於環境的耐受性極強，也是少數能無懼太陽的強悍品種。", "")],
    star=f"{B1S}（微體溫室〈銀鹿〉、晴花鹿苑）")
v14("veitchii-high-finger",
    [c("vegetal-high-finger", "fertile_width", "~1", "孢子葉很長、細而直，像手指或矛", "細長 → 寬鬆 1",
       "fertile fronds that very long, thin and straight, resembling \"fingers\" or vertical spears, hence the name High Finger"),
     c("vegetal-high-finger", "fertile_posture", "~up", "孢子葉直立如矛", "直立 → 寬鬆 up",
       "fertile fronds that very long, thin and straight, resembling \"fingers\" or vertical spears"),
     c("jl-rydeen", "shield_height", "~3", "High Finger 的盾葉先端直立", "Rydeen 商品頁描述 High Finger 本身的盾葉先端直立 → 寬鬆 3",
       "combined with the upright tips of the bracts of 'High Finger'.")],
    desc=[("孢子葉很長、細而直，像直立的手指，品名由此而來；生長慢。", "vegetal-high-finger",
           "fertile fronds that very long, thin and straight, resembling \"fingers\" or vertical spears, hence the name High Finger ... Growth: Slow.", "")],
    star=f"{B1S}（晴花鹿苑頁仍不採用）|搜尋：Platycerium veitchii 'High Finger' staghorn description|Vegetal Design 商品頁|Jungle Leaves〈Rydeen〉|{NOJA}",
    care="Vegetal Design 商品頁（通用照護表，不採用）")
v14("veitchii-nyx",
    [c("mo-silver", "shield_height", "~3", "營養葉渾圓、冠成束", "有冠 → 寬鬆 3", "營養葉型態渾圓且冠成束"),
     c("ajins-nyx", "shield_hair", "~5", "特別銀白的銀鹿", "整株特別銀白（含盾葉）→ 寬鬆 5", "夜銀顧名思義是一顆特別銀白的銀鹿")],
    star=f"{B1S}（微體溫室〈銀鹿〉、阿金）")
v14("hillii-dragon",
    [c("mo-hillii", "fertile_width", "~3", "保有深綠寬大孢子葉的特徵", "寬大 → 寬鬆 3", "保有深綠鹿角蕨寬大孢子葉的特徵")],
    star=f"{B1S}（微體溫室〈深綠〉）|搜尋：Platycerium hillii 'Dragon' staghorn fern fronds description（沒有該品系的頁面）")
v14("hillii-dwarf",
    [c("mo-hillii", "fertile_width", "~1", "孢子葉分岔成小巧的指狀", "指狀 → 狹長，寬鬆 1", "孢子葉呈分叉為小巧可愛的指狀，成熟後具絨毛感"),
     c("mo-hillii", "fertile_hair", "~3", "成熟後有絨毛感", "有毛 → 寬鬆 3", "孢子葉呈分叉為小巧可愛的指狀，成熟後具絨毛感"),
     c("ajins-hillii-dwarf", "fertile_width", "~1", "分岔細緻，像一根根小手指", "細長 → 寬鬆 1", "隨著成熟分岔會逐漸變得細緻，宛如一根根小手指般立體生長"),
     c("ajins-hillii-dwarf", "fertile_hair", "~3", "細緻白毛", "有白毛 → 寬鬆 3", "搭配深綠葉色與細緻白毛")],
    star=f"{B1S}（微體溫室〈深綠〉、阿金）")
v14("hillii-raijin",
    [c(HAR, "fertile_width", "~3", "寬厚大葉", "寬葉 → 寬鬆 3", "繼承深綠寬厚大葉的特色外，葉形帶有的圓潤的分岔"),
     c(HAR, "fertile_hair", "~3", "帶絨毛感", "有毛 → 寬鬆 3", "深色的孢子葉刻有明顯的葉脈紋理並帶著絨毛感"),
     c(HAR, "fertile_posture", "~spread", "向上放射展開", "放射展開 → 寬鬆 spread", "向上放射展開溫潤的葉形"),
     c("ajins-raijin", "fertile_width", "~3", "寬大的孢子葉", "寬葉 → 寬鬆 3", "寬大的孢子葉帶圓潤分岔")],
    star=f"{B1S}（晴花鹿苑、阿金）|搜尋：Platycerium hillii 'Raijin' staghorn|{NOJA}")
v14("veitchii-no-shield",
    [c("ajins-veitchii-no-shield", "fertile_hair", "~3", "葉片白皙", "白皙 → 有白毛，寬鬆 3", "葉片白皙且帶有微波浪分岔的質感")],
    star=f"{B1S}（阿金）")
v14("bifurcatum-dwarf", star=f"{B1S}（阿金：沒有新說法）")
v14("veitchii-lemoinei-dwarf",
    [c("ajins-lemoinei-dwarf", "fertile_width", "~1", "孢子葉分岔更細、更小", "細 → 寬鬆 1", "相較一般檸檬，它的孢子葉分岔更細、更小也更加密集")],
    star=f"{B1S}（阿金、微體溫室〈檸檬〉）")
v14("hillii-wave", star=f"{B1S}（阿金只寫波浪葉緣、尖葉尾，沒有能換算的說法）")

# ---------------------------------------------------------------- v1.4 B2 (2026-10-19): 澳洲群內的交種
# New lookups (English names) found nothing beyond the pages already cited. We Love Tropical Plants' prose reads as generated copy
# and is not used (guideline §2 T4), as before for its care table.
B2S = "v1.4 重讀已引用頁面"
WLTP = "We Love Tropical Plants（描述疑似生成文字，不採用）"
v14("veitchii-x-willinckii",
    [c("ajins-veitchii-x-willinckii", "shield_height", "~3", "成熟時冠如花朵綻放", "有冠、展開 → 寬鬆 3", "當植株成熟時，冠有如花朵般綻放"),
     c("ajins-veitchii-x-willinckii", "fertile_posture", "~pendant", "拉長的手如彩帶般飄逸", "彩帶般飄垂 → 寬鬆 pendant", "遠眺時看拉長的手有如彩帶般的飄逸")],
    star=f"{B2S}（阿金、卡呸醬、Halling 交種表）")
v14("hillii-x-bifurcatum",
    [c(HH, "fertile_width", "~3", "孢子葉寬，像深綠", "寬葉 → 寬鬆 3", "The fertile fronds are wide like P. hillii"),
     c(HH, "size", "~L", "可能比一般鹿角蕨大", "作者寫 may be → 推測 → excluded", "The P. diversifolium may be a larger than average platycerium.", "", "excluded")],
    star=f"{B2S}（Halling）|搜尋：Platycerium 'Diversifolium' staghorn fern hillii bifurcatum hybrid description（沒有該交種的頁面）")
v14("dw", star="搜尋：Platycerium 'DW' diversifolium x willinckii（v1.4 再查仍沒有描述）")
v14("monkey-north",
    [c("haruhana-monkey-north", "shield_height", "~3", "有奧銀的高冠", "高冠 → 寬鬆 3", "爪哇交奧銀 有著奧銀的高冠基因"),
     c(ZYX, "shield_height", "~3", "高冠", "高冠 → 寬鬆 3", "奧銀與爪哇交種的經典個體。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉。"),
     c(ZYX, "fertile_hair", "~3", "白絨毛", "有白絨毛 → 寬鬆 3", "奧銀與爪哇交種的經典個體。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉。"),
     c(ZYX, "fertile_posture", "~pendant", "下墜的孢子葉", "下垂 → 寬鬆 pendant", "奧銀與爪哇交種的經典個體。兼具親本兩者特色：高冠、白絨毛以及下墜的孢子葉。")],
    star=f"{B2S}（晴花鹿苑、竹意軒）")
v14("hela",
    [c(ZYX, "shield_height", "~5", "成熟時冠部極度高聳", "冠很高 → 寬鬆 5", "成熟時冠部極度高聳，孢子葉呈下垂貌，爪哇與銀鹿檸檬交種個體。"),
     c(ZYX, "fertile_posture", "~pendant", "孢子葉下垂", "下垂 → 寬鬆 pendant", "成熟時冠部極度高聳，孢子葉呈下垂貌")],
    star=f"{B2S}（竹意軒）")
v14("snow-moon",
    [c("mo-moon", "fertile_hair", 5, "厚實白毛，葉色銀白", "厚白毛、銀白 → 5（同 v1.3 對「厚實白毛」的換算）",
       "兩者同樣擁有厚實白毛 ... 雪月鹿角蕨｜中等｜$400~$1,200｜葉色呈銀白 絨毛感厚實")],
    star=f"{B2S}（微體溫室〈月亮系列〉）")
v14("rydeen",
    [c("jl-rydeen", "shield_height", "~3", "盾葉先端直立", "直立 → 寬鬆 3", "combined with the upright tips of the bracts of 'High Finger'."),
     c("jl-rydeen", "fertile_width", "~1", "孢子葉分岔細", "細 → 寬鬆 1", "'Rydeen' has the drooping, almost bent, finely branched fronds of 'Mt. Lewis'")],
    star=f"{B2S}（Jungle Leaves）|搜尋：Platycerium 'Rydeen' OR 'Tornado' OR 'Kiyohime' staghorn fern hybrid")
v14("electrofilia",
    [c("ajins-veitchii-x-bifurcatum", "fertile_hair", "~3", "白毛也是必須的", "有白毛 → 寬鬆 3", "除了改善銀鹿生長速度慢的情況，白毛也是必須的！")],
    star=f"{B2S}（阿金、Halling）|搜尋：Platycerium 'Electrofilia' OR electrifolia staghorn（沒有該交種的頁面）")
v14("majus",
    [c(HH, "size", "~L", "相當大型", "大型 → 寬鬆 L", "It is a fairly large growing staghorn with a growth habit similar to P. veitchii")],
    star=f"{B2S}（Halling）|搜尋：Platycerium 'Majus' staghorn fern（沒有該交種的頁面）")
v14("hillii-x-willinckii",
    [c("halling-yanid", "shield_form", "~appressed", "盾葉圓、不高，向內長成球狀", "圓形、不高、包覆 → 貼伏",
       "the shield fronds are rounded and not tall and deeply lobed. ... the plant shield fronds form a ball like Platycerium hillii"),
     c("halling-yanid", "shield_height", "~1", "盾葉不高，長成球狀", "不長高 → 寬鬆 1",
       "the shield fronds are rounded and not tall and deeply lobed. ... the plant shield fronds form a ball like Platycerium hillii")],
    star=f"{B2S}（Halling Yanid.htm）")
v14("bifurcatum-x-willinckii",
    [c("haruhana-willinckii-x-bif", "shield_height", "~3", "優美的冠型", "有冠 → 寬鬆 3", "它具有優美的冠型與多岔白皙質感的孢子葉"),
     c("haruhana-willinckii-x-bif", "fertile_hair", "~3", "多岔、白皙質感的孢子葉", "白皙 → 寬鬆 3", "它具有優美的冠型與多岔白皙質感的孢子葉")],
    star=f"{B2S}（晴花鹿苑）")
v14("elsa",
    [c("haruhana-elsa", "size", "~S", "孢子葉緊湊、短", "緊湊 → 寬鬆 S", "緊湊且短而挺立的孢子葉"),
     c("haruhana-elsa", "fertile_hair", "~3", "白皙迷人的絨毛", "有白絨毛 → 寬鬆 3", "同時有著白皙迷人的絨毛"),
     c(ZYX, "fertile_hair", "~5", "絨毛表現極佳", "絨毛極佳 → 濃密，寬鬆 5", "葉片絨毛表現極佳，成熟時分岔性好")],
    star=f"{B2S}（晴花鹿苑、竹意軒）|搜尋：Platycerium 'Elsa' OR 'Hakuna Matata' staghorn fern fronds（沒有該品種的頁面）")
v14("doi-tung",
    [c(ZYX, "fertile_posture", "~up", "光線足夠時葉片往上長", "向上 → 寬鬆 up", "光線足夠時，葉片會往上生長，短且具氣勢。")],
    star=f"{B2S}（竹意軒）")
v14("hakuna-matata",
    [c("ajins-hakuna-matata", "size", "~M", "中小型", "中小型 → 寬鬆 M", "於中小型鹿有著厚實白毛表現，手短且多岔")],
    star=f"{B2S}（阿金、晴花鹿苑）|{WLTP}")
v14("kiyohime",
    [c("haruhana-kiyohime", "shield_height", "~3", "成株有如皇冠般的冠型", "有冠 → 寬鬆 3", "成株後展現出如皇冠般的美麗冠型")],
    star=f"{B2S}（晴花鹿苑）")
v14("tornado",
    [c("haruhana-tornado", "fertile_width", "~3", "寬大的孢子葉", "寬葉 → 寬鬆 3", "同時有著寬大的孢子葉"),
     c("haruhana-tornado", "shield_height", "~1", "營養葉上板後快速包覆水苔", "包覆附著物 → 寬鬆 1", "從小側芽就容易有著美麗的營養葉，上板後能快速包覆水苔。")],
    star=f"{B2S}（晴花鹿苑）")
v14("et",
    [c("haruhana-et", "shield_height", "~3", "優雅秀氣的冠型", "有冠 → 寬鬆 3", "展現優雅秀氣的冠型"),
     c("haruhana-et", "fertile_width", "~3", "寬大飽滿的孢子葉，分岔圓潤短小", "寬、圓 → 寬鬆 3", "搭配寬大飽滿的孢子葉 ... 葉端分叉密集且圓潤短小")],
    star=f"{B2S}（晴花鹿苑，播孢母本的描述）")
v14("trident", star=f"{B2S}（阿金只寫末端分岔像三叉戟）")
v14("wolverine",
    [c("sapphirechild-wolverine", "shield_height", "~3", "預期盾葉會長出高的指狀裂片", "依親本預期，不是觀察 → excluded",
       "As these grow up, we can expect awesome tall 'fingers' on the shield fronds from the veitchii parent", "", "excluded")],
    star=f"{B2S}（阿金、SapphireChild）|{WLTP}")
v14("south-pole-star", star=f"{B2S}（阿金只有品名）")
v14("unicorn",
    [c("ajins-unicorn", "fertile_width", "~3", "孢子葉短而圓胖", "圓 → 寬鬆 3", "孢子葉的型態短而圓胖，呈「手」狀")],
    star=f"{B2S}（阿金；晴花鹿苑頁是孢子苗，不採用）|{WLTP}")
v14("nemo", star=f"{B2S}（阿金只寫白毛與分岔「有發展潛力」）")
v14("cardinals",
    [c("ajins-cardinals", "shield_height", "~3", "承襲奧銀狂野的高冠", "高冠 → 寬鬆 3", "紅雀鹿角蕨 承襲了奧銀狂野的高冠")],
    star=f"{B2S}（阿金）")
v14("uncia",
    [c("haruhana-uncia", "shield_height", "~3", "小巧精緻的冠型", "有冠 → 寬鬆 3", "帶著迷人的小巧精緻的冠型"),
     c("haruhana-uncia", "fertile_hair", "~3", "孢子葉帶白皙絨毛", "有白絨毛 → 寬鬆 3", "其孢子葉帶著白皙絨毛的質感")],
    star=f"{B2S}（晴花鹿苑）")

# ---------------------------------------------------------------- v1.4 B3 (2026-10-19): 爪哇品系（一）
# New lookups (English names) only returned Orchideeën Shop's generic dwarf-willinckii copy; nothing new is cited from them.
B3S = "v1.4 重讀已引用頁面"
B3W = "搜尋：英文品名＋Platycerium willinckii staghorn（只有 Orchideeën Shop 的泛用文字，不採用）"
DWQ = lambda zh, rate, d: f"{DWT} ... {zh}鹿角蕨｜{rate}｜{d}"
v14("willinckii-nano",
    [c("mo-dwarf", "fertile_hair", "~3", "孢子葉呈暗銀", "暗銀 → 有毛，寬鬆 3", DWQ("Nano", "中等", "1. 孢子葉呈暗銀 2. 孢子葉分叉細長")),
     c("mo-dwarf", "fertile_width", "~1", "孢子葉分岔細長", "細長 → 寬鬆 1", DWQ("Nano", "中等", "1. 孢子葉呈暗銀 2. 孢子葉分叉細長"))],
    star=f"{B3S}（微體溫室〈侏儒鹿角蕨〉）|{B3W}")
v14("willinckii-jade-girl", star=f"{B3S}（Jungle Leaves、微體溫室：盾葉「open basket」是種的通用句，不採用）")
v14("willinckii-little-will", star=f"{B3S}（竹意軒只有侏儒、可露養）")
v14("willinckii-jenny",
    [c("mo-dwarf", "fertile_posture", "~up", "孢子葉上翹微捲", "上翹 → 寬鬆 up", DWQ("珍妮", "難", "1. 孢子葉呈上翹微捲 2. 整體孢子葉呈扇形")),
     c("ajins-jenny", "fertile_hair", "~3", "孢子葉精緻白皙", "白皙 → 寬鬆 3", "以其精緻白皙、有細緻且多層次分岔的孢子葉"),
     c("bw-golden-boy", "pups", "~yes", "植株有很多側芽", "側芽多 → 寬鬆 yes", "該株鹿角蕨是現在消費者喜愛的「侏儒爪哇」品種之一，植株有很多側芽而抬升價值。")],
    star=f"{B3S}（微體溫室、阿金、商業周刊）|{B3W}")
v14("willinckii-bacteria", star=f"{B3S}（阿金、Jungle Leaves：盾葉句是種的通用句）")
v14("willinckii-smurf",
    [c("ajins-smurf", "shield_height", "~3", "高冠表現", "高冠 → 寬鬆 3", "藍底白厚毛，高冠表現，分岔微捲手型")],
    star=f"{B3S}（阿金）")
v14("willinckii-spur",
    [c("mo-dwarf", "fertile_width", "~1", "孢子葉尖端分岔如刺", "如刺 → 狹長，寬鬆 1", DWQ("骨刺", "難", "1. 孢子葉尖端分叉如刺 2. 孢子葉脈白紋明顯"))],
    star=f"{B3S}（微體溫室〈侏儒鹿角蕨〉〈為什麼那麼貴〉）")
v14("willinckii-masayu", star=f"{B3W}")
v14("willinckii-celso-tatsuta",
    [c("ajins-celso", "fertile_hair", "~3", "亮眼的白毛", "有白毛 → 寬鬆 3", "爪哇中夢幻逸品，擁有亮眼的分岔與白毛")],
    star=f"{B3S}（阿金、微體溫室）|{B3W}（Dwarf Tatsuta 不確定是同一植物）")
v14("willinckii-hp100",
    [c(KP, "fertile_width", "~3", "寬葉深淺裂", "寬葉 → 寬鬆 3", "短手爪哇 011 | HP100 寬葉深淺裂")],
    star=f"{B3S}（卡呸醬）")
for pid, q, rows in [
    ("willinckii-wild-cat", "爪哇鹿角蕨的個體，孢子葉白且形態張揚，具有一定的辨識度。", [("fertile_hair", "~3", "孢子葉白", "白 → 寬鬆 3")]),
    ("willinckii-mr-tin", "爪哇鹿角蕨個體，具白皙且細緻的流線孢子葉。", [("fertile_hair", "~3", "孢子葉白皙", "白皙 → 寬鬆 3")]),
    ("willinckii-a-plus", "爪哇鹿角蕨的個體，白皙且排列密集，體型中型。",
     [("size", "~M", "體型中型", "中型 → 寬鬆 M"), ("fertile_hair", "~3", "白皙", "白皙 → 寬鬆 3")]),
]:
    v14(pid, [c(ZYX, f, v, lab, cl, q) for f, v, lab, cl in rows], star=f"{B3S}（竹意軒）")
v14("willinckii-cold-moon", star=f"{B3S}（竹意軒「孢子葉細緻、營養葉寬胖」，沒有能換算的說法）")
v14("willinckii-albo-anubis", star=f"{B3S}（竹意軒只寫「葉片極其細緻」）")
v14("willinckii-yellow-moon",
    [c("mo-moon", "fertile_hair", "~3", "孢子葉微黃白皙", "白皙 → 寬鬆 3", "微黃白皙的鹿手搭上誘人微翹的指尖")],
    star=f"{B3S}（微體溫室〈月亮系列〉；Orchideeën Shop 頁是侏儒黃月，不採用）|{B3W}")
v14("willinckii-kaguya", star=f"{B3S}（微體溫室只描述侏儒黃月系列整體，不套用）")
v14("willinckii-moonlight",
    [c("ajins-moonlight", "shield_height", "~3", "高冠在日照充足時更挺立", "高冠 → 寬鬆 3", "日照充足的話，葉面會更顯皎白 高冠也會更加挺立"),
     c("ajins-moonlight", "fertile_posture", "~pendant", "流線型飄曳的手", "飄曳 → 寬鬆 pendant", "柔美的孢子葉如月光灑下來 ... 流線型飄曳的手手"),
     c("haruhana-moonlight", "shield_height", "~3", "營養葉有美麗高冠", "高冠 → 寬鬆 3", "而營養葉則展現眾人追求的美麗高冠"),
     c("mo-moon", "fertile_posture", "~pendant", "帶狀孢子葉如月光傾瀉而下", "傾瀉而下 → 寬鬆 pendant", "帶狀柔美的孢子葉如月光傾瀉而下"),
     c("mo-moon", "fertile_hair", "~5", "葉色呈銀白", "銀白 → 寬鬆 5", f"{MOONT} ... 月光鹿角蕨｜中偏易｜$250~$600｜葉色呈銀白 層次感明顯")],
    star=f"{B3S}（阿金、晴花鹿苑、微體溫室〈月亮系列〉）|{B3W}")
v14("willinckii-blue-queen",
    [c("mo-dwarf", "fertile_hair", "~5", "孢子葉呈銀白", "銀白 → 寬鬆 5", DWQ("侏儒藍皇后", "中偏難", "1. 孢子葉呈銀白 2. 孢子葉末端內捲"))],
    star=f"{B3S}（微體溫室〈侏儒鹿角蕨〉）|{B3W}")
v14("willinckii-golden-boy",
    [c("mo-dwarf", "fertile_width", "~1", "孢子葉分岔細長", "細長 → 寬鬆 1", DWQ("金童", "難", "1. 孢子葉呈銀黃 2. 孢子葉序緊密叢生 3. 孢子葉分叉細長"))],
    star=f"{B3S}（微體溫室、商業周刊）|{B3W}")
v14("willinckii-pearl-queen",
    [c("haruhana-pearl-queen", "shield_height", "~3", "多層次的迷人高冠", "高冠 → 寬鬆 3", "美麗多層次的迷人高冠"),
     c("haruhana-pearl-queen", "fertile_hair", "~3", "白皙厚實的葉面", "白皙 → 寬鬆 3", "白皙厚實的葉面如珍珠般閃爍迷人")],
    star=f"{B3S}（晴花鹿苑）|{B3W}|We Love Tropical Plants（描述疑似生成文字，不採用）")
v14("willinckii-leonids",
    [c("haruhana-leonids", "shield_height", "~3", "母本有霸氣的高冠", "高冠 → 寬鬆 3", "母本有著霸氣的高冠與細緻秀長的孢子葉"),
     c("haruhana-leonids", "fertile_width", "~1", "母本孢子葉細緻秀長", "細長 → 寬鬆 1", "母本有著霸氣的高冠與細緻秀長的孢子葉")],
    star=f"{B3S}（晴花鹿苑，母本的描述）|{B3W}")
v14("willinckii-white-swan",
    [c("haruhana-white-swan", "shield_height", "~3", "長岔高冠", "高冠 → 寬鬆 3", "整品植株有著霸氣且左右相襯的長岔高冠"),
     c("haruhana-white-swan", "fertile_hair", "~5", "白厚", "白而厚 → 寬鬆 5", "白皙對稱的弧度，如同白天鵝優雅的展翅之姿。 白厚與優雅的姿態令人摒息。")],
    star=f"{B3S}（晴花鹿苑）")
v14("willinckii-pedro",
    [c("haruhana-pedro", "shield_height", "~3", "對稱優雅的高冠", "高冠 → 寬鬆 3", "以對稱優雅的高冠與層次分明、白皙迷人的孢子葉聞名"),
     c("haruhana-pedro", "fertile_hair", "~3", "白皙的孢子葉", "白皙 → 寬鬆 3", "這株又白又美的神獸級鹿角蕨，以對稱優雅的高冠與層次分明、白皙迷人的孢子葉聞名")],
    star=f"{B3S}（晴花鹿苑）|{B3W}")

# ---------------------------------------------------------------- v1.4 B4 (2026-10-19): 爪哇品系（二）
B4S = "v1.4 重讀已引用頁面"
B4W = "搜尋：英文品名＋Platycerium willinckii staghorn（沒有該品系的頁面）"
v14("willinckii-anapat-9",
    [c("haruhana-anapat-9", "shield_height", "~3", "經典的冠型", "有冠 → 寬鬆 3", "知名系列Anapat #9 有著鹿角蕨經典的冠型與下墜型的孢子葉"),
     c("haruhana-anapat-9", "fertile_hair", "~3", "明顯白皙感", "白皙 → 寬鬆 3", "在末端有著無數的岔型與此同時帶著明顯白皙感")],
    star=f"{B4S}（晴花鹿苑）|{B4W}")
v14("willinckii-sri-pueak",
    [c("haruhana-sri-pueak", "fertile_hair", "~3", "成株葉色白皙柔亮", "白皙 → 寬鬆 3", "成株後葉面厚實飽滿、葉色白皙柔亮")],
    star=f"{B4S}（晴花鹿苑）|{B4W}")
for pid in ("willinckii-nook-dwarf", "willinckii-kaohom", "willinckii-watchara"):
    v14(pid, star=f"{B4S}（微體溫室只描述系列與價格）|{B4W}")
v14("gabriel",
    [c("haruhana-gabriel", "fertile_hair", "~3", "葉面肥厚且白皙", "白皙 → 寬鬆 3", "最終極型態出來整體猶如天使之翼的向兩邊展開，葉面非常肥厚且白皙"),
     c("mo-dwarf", "fertile_hair", "~5", "孢子葉厚呈銀白", "銀白 → 寬鬆 5", DWQ("加百列", "中偏難", "1. 孢子葉厚呈銀白 2. 孢子葉幅寬大 3. 整體孢子葉向外展開")),
     c("mo-dwarf", "fertile_width", "~3", "孢子葉幅寬大", "寬葉 → 寬鬆 3", DWQ("加百列", "中偏難", "1. 孢子葉厚呈銀白 2. 孢子葉幅寬大 3. 整體孢子葉向外展開"))],
    star=f"{B4S}（晴花鹿苑、微體溫室）|{B4W}")
v14("willinckii-robin", star=f"{B4S}（阿金：葉面脈紋是孢子葉的，不換算盾葉葉脈）")
v14("fishbone",
    [c("mo-dwarf", "fertile_hair", "~3", "孢子葉暗綠覆白毛", "看得出底色、有白毛 → 寬鬆 3", DWQ("魚骨／寶石甲蟲", "難", "1. 孢子葉呈暗綠覆白毛 2. 孢子葉脈菱格紋明顯"))],
    star=f"{B4S}（微體溫室；The Basements 的描述疑似生成文字，不採用）")
v14("aydan",
    [c("ajins-aydan", "fertile_width", "~1", "孢子葉纖細、分岔細緻", "細 → 寬鬆 1", "孢子葉所呈現出的纖細線條與優雅分岔 ... 分岔細緻而流暢"),
     c("ajins-aydan", "fertile_hair", "~3", "葉面覆細緻白毛，柔和的銀白質感", "有白毛 → 寬鬆 3", "葉面覆蓋著細緻白毛，在光線下呈現柔和的銀白質感")],
    star=f"{B4S}（阿金）")
v14("willinckii-omega",
    [c("ajins-omega", "fertile_hair", "~3", "葉面白毛細緻", "有白毛 → 寬鬆 3", "整體型態成熟穩定，葉面白毛細緻")],
    star=f"{B4S}（阿金）")
v14("willinckii-half-moon", star=f"{B4S}（阿金頁描述的是孢子苗，不採用型態）")
v14("willinckii-silver-phoenix",
    [c("ajins-silver-phoenix", "fertile_width", "~3", "孢子葉稍寬厚", "寬 → 寬鬆 3", "植株對稱優美，孢子葉也稍微比較寬厚一些")],
    star=f"{B4S}（阿金）")
v14("willinckii-yellow-moon-dwarf",
    [c("ajins-yellow-moon-dwarf", "fertile_width", "~1", "孢子葉細長", "細長 → 寬鬆 1", "孢子葉細長延展"),
     c("ajins-yellow-moon-dwarf", "fertile_hair", "~3", "白皙細緻的絨毛", "有白絨毛 → 寬鬆 3", "搭配白皙細緻的絨毛"),
     c("mo-dwarf", "fertile_width", "~1", "孢子葉分岔細長", "細長 → 寬鬆 1", DWQ("侏儒黃月", "中偏難", "1. 孢子葉呈黃暈向外 2. 孢子葉分叉細長")),
     c("mo-dwarf", "fertile_posture", "~spread", "孢子葉黃暈向外", "向外 → 寬鬆 spread", DWQ("侏儒黃月", "中偏難", "1. 孢子葉呈黃暈向外 2. 孢子葉分叉細長"))],
    star=f"{B4S}（阿金、微體溫室）")
v14("willinckii-ccs",
    [c("haruhana-ccs", "shield_height", "~3", "高冠厚葉", "高冠 → 寬鬆 3", "高冠厚葉的P. willinckii CCS最大的特點就是臉與手有著濃密的白皙絨毛質感")],
    star=f"{B4S}（晴花鹿苑）|{B4W}")
v14("willinckii-makigumo", star=f"{B4S}（晴花鹿苑：葉端捲曲、岔型極短，沒有能換算的新說法）|{B4W}")
v14("willinckii-white-heaven",
    [c("haruhana-white-heaven", "shield_height", "~3", "高聳翠綠的冠型", "高冠 → 寬鬆 3", "有著高聳翠綠的美麗冠型"),
     c("haruhana-white-heaven", "fertile_hair", "~3", "白皙的絨毛感", "有白絨毛 → 寬鬆 3", "優雅白皙的絨毛感讓整體葉色更富質感")],
    star=f"{B4S}（晴花鹿苑）|{B4W}")
v14("willinckii-white-rose", star=f"{B4S}（晴花鹿苑頁描述的是孢子苗，不採用型態）")
v14("willinckii-yami",
    [c("haruhana-yami", "shield_height", "~3", "高冠層次豐富", "高冠 → 寬鬆 3", "整體的高冠層次豐富，特別是孢子葉的型態細長而優雅"),
     c("haruhana-yami", "fertile_width", "~1", "孢子葉細長", "細長 → 寬鬆 1", "特別是孢子葉的型態細長而優雅"),
     c("haruhana-yami", "fertile_posture", "~pendant", "孢子葉如秀髮般柔美悠長、飄逸", "飄垂 → 寬鬆 pendant", "有如少女的秀髮般柔美悠長，自然高雅的弧度，亂中有序的飄逸綻放"),
     c("haruhana-yami", "fertile_hair", "~3", "細緻款的白哇", "白 → 寬鬆 3", "P.willinckii Yami是一款細緻款的白哇")],
    star=f"{B4S}（晴花鹿苑）|{B4W}")
v14("sunny-cutie",
    [c("haruhana-sunny-cutie", "shield_height", "~3", "縮小版的迷你冠型", "有冠 → 寬鬆 3", "擁有縮小版的迷你冠型"),
     c("haruhana-sunny-cutie", "fertile_width", "~1", "孢子葉修長", "細長 → 寬鬆 1", "此外孢子葉修長優雅，宛如流水悠長的下墜姿態")],
    star=f"{B4S}（晴花鹿苑）")
v14("willinckii-anne", star=f"{B4S}（晴花鹿苑頁沒有描述）")
v14("willinckii-bogie", star=f"{B4S}（晴花鹿苑頁沒有描述）")
v14("willinckii-anapat-1",
    [c("haruhana-anapat-1", "shield_height", "~3", "母本有經典的冠型", "有冠 → 寬鬆 3", "同時具備經典的冠型與獨特風格")],
    star=f"{B4S}（晴花鹿苑，母本的描述）|{B4W}")
v14("willinckii-totoro",
    [c("yahoo-frontier-totoro", "fertile_width", "~1", "分岔多、葉先纖細", "纖細 → 寬鬆 1", "分岐数も多く繊細な葉先でとても魅力的な品種です。")],
    star=f"{B4S}（Frontier Plants、naturefix、The Basements、HHR 拍賣頁）")
v14("willinckii-grace",
    [c("yahoo-vandaka-grace", "fertile_hair", "~3", "株色白", "白 → 寬鬆 3", "強度の高い矮性と白さに加え、葉先が内巻きにカールする次世代のスーパードワーフ種です。")],
    star=f"{B4S}（vandaka plants、日本拍賣）")

# ---------------------------------------------------------------- v1.4 B5 (2026-10-19): DW 系與親本不明的命名個體
B5S = "v1.4 重讀已引用頁面"
B5W = "搜尋：英文品名＋Platycerium staghorn（沒有該品種的頁面）"
v14("white-hawk", star=f"{B5S}（微體溫室〈40 種〉只有表格分類）|{B5W}")
v14("omg",
    [c("ajins-omg", "fertile_width", "~3", "孢子葉短而闊", "闊 → 寬鬆 3", "孢子葉短而闊，成多叉形態")],
    star=f"{B5S}（阿金、微體溫室）")
v14("pegasus",
    [c("mo-pegasus", "shield_height", "~3", "有爪哇的典型高冠", "高冠 → 寬鬆 3", "外觀上分別擁有： 爪哇鹿角蕨 的典型高冠"),
     c("mo-pegasus", "fertile_posture", "~spread|pendant", "成株孢子葉向上長後折下", "向外再折下 → 寬鬆 spread|pendant", "上板成株 孢子葉向上長後折下 營養葉尖冠開始明顯"),
     c("mo-pegasus", "shield_browning", "~withering", "高溫下營養葉會乾枯", "盾葉乾枯 → 寬鬆 withering", "此外高溫下營養葉有像 圓盾鹿角蕨 乾枯的狀況，是屬於正常現象喔！"),
     c("vegetal-pegasus", "fertile_posture", "~spread", "孢子葉大、深裂有齒，像展開的翅膀", "展開 → 寬鬆 spread",
       "fertile fronds large, deeply lobed and toothed, resembling outstretched wings, hence the name Pegasus")],
    desc=[("Vegetal Design 說孢子葉大、深裂而有齒，像展開的翅膀。", "vegetal-pegasus",
           "fertile fronds large, deeply lobed and toothed, resembling outstretched wings, hence the name Pegasus", "")],
    star=f"{B5S}（微體溫室〈飛馬〉）|搜尋：Platycerium 'Pegasus' staghorn fern hybrid fronds|Vegetal Design 商品頁",
    care="Vegetal Design 商品頁（通用照護表，不採用）")
v14("white-lover",
    [c("ajins-polar-bear", "fertile_width", "~3", "成熟後葉片寬白", "寬 → 寬鬆 3", "隨著植株成熟，葉片會逐漸展現寬白狂野的型態")],
    star=f"{B5S}（阿金）|搜尋：Platycerium 'OMO' OR 'White Lover' OR 'Polar Bear' staghorn fern description")
v14("full-moon",
    [c(ZYX, "fertile_hair", "~1", "孢子葉有獨特的蠟質感", "蠟質 → 寬鬆 1", "DW交種，月亮系列的鹿角蕨，孢子葉有獨特的蠟質感，相當有辨識度。")],
    star=f"{B5S}（竹意軒）")
v14("blue-moon",
    [c(ZYX, "fertile_width", "~3", "葉胖寬", "寬 → 寬鬆 3", "DW交種中的月亮系列，葉胖寬，成熟時葉片具藍綠色之質感。"),
     c("mo-moon", "fertile_width", "~3", "孢子葉比黃月寬", "寬 → 寬鬆 3", "相較黃月鹿角蕨的手更寬，而且葉尾末端的細小分叉多"),
     c("mo-moon", "fertile_hair", "~5", "銀白帶藍的孢子葉", "銀白 → 寬鬆 5", "藍月鹿角蕨最大的特色是銀白帶藍的孢子葉")],
    star=f"{B5S}（竹意軒、微體溫室〈月亮系列〉）|{B5W}")
v14("honey-moon", star=f"{B5S}（竹意軒「基部寬、漸窄、蘋果綠」，沒有能換算的說法）")
v14("blue-monkey", star=f"{B5S}（竹意軒「藍綠色、葉脈明顯」指孢子葉，沒有能換算的說法）")
v14("paul-vespa",
    [c(ZYX, "fertile_hair", "~3", "葉片白皙", "白皙 → 寬鬆 3", "DW交種系列下的品種，葉片白皙且對稱性佳，栽培性也很好。")],
    star=f"{B5S}（竹意軒）")
v14("new-moon",
    [c("mo-moon", "fertile_hair", "~5", "葉色呈銀白", "銀白 → 寬鬆 5", f"{MOONT} ... 新月鹿角蕨｜中偏易｜$250~$600｜葉色呈銀白 末端分叉修長"),
     c("mo-moon", "fertile_width", "~1", "末端分岔修長", "細長 → 寬鬆 1", f"{MOONT} ... 新月鹿角蕨｜中偏易｜$250~$600｜葉色呈銀白 末端分叉修長")],
    star=f"{B5S}（微體溫室〈月亮系列〉）")
v14("polar-bear",
    [c("ajins-polar-bear", "size", "~S", "精選出來的緊湊型個體", "緊湊 → 寬鬆 S", "北極熊更是精選出來緊湊型的個體"),
     c("paraiso-polar-bear", "fertile_hair", "~5", "孢子葉明顯偏白", "很白 → 寬鬆 5", "Each staghorn looks a little different but the Omo 'Polar Bear' has distinctively white fronds.")],
    star=f"{B5S}（阿金、微體溫室）|搜尋：Platycerium 'OMO' OR 'Polar Bear' staghorn fern description|Paraíso Plant Studio 商品頁|We Love Tropical Plants（不採用）",
    care="Paraíso Plant Studio 商品頁（蕨類通用照護文字，不採用）")
v14("jynx",
    [c(ZYX, "size", "~M", "整體體型適中", "中等體型 → 寬鬆 M", "葉片胖寬，整體體型適中，可愛的品種。"),
     c(ZYX, "fertile_width", "~3", "葉片胖寬", "寬 → 寬鬆 3", "葉片胖寬，整體體型適中，可愛的品種。")],
    star=f"{B5S}（竹意軒）")
v14("mountain-rabbit",
    [c(ZYX, "size", "~L", "大型", "大型 → 寬鬆 L", "大型單芽種，營養葉高聳，孢子葉僅有一對孢子囊群斑塊，氣勢雄偉。"),
     c(ZYX, "shield_height", "~3", "營養葉高聳", "高冠 → 寬鬆 3", "大型單芽種，營養葉高聳")],
    star=f"{B5S}（竹意軒）")
v14("white-hill",
    [c(ZYX, "fertile_posture", "~pendant", "孢子葉如瀑布般下墜", "下垂 → 寬鬆 pendant", "孢子葉呈瀑布狀的下墜，排列密集，並且具有濃密的白色絨毛。"),
     c(ZYX, "fertile_hair", "~5", "濃密的白色絨毛", "白毛濃密 → 寬鬆 5", "孢子葉呈瀑布狀的下墜，排列密集，並且具有濃密的白色絨毛。")],
    star=f"{B5S}（竹意軒）")
v14("white-wing",
    [c(ZYX, "fertile_hair", "~3", "孢子葉白皙", "白皙 → 寬鬆 3", "孢子葉白皙，葉脈紋路明顯，成熟時葉尾具密集分岔。")],
    star=f"{B5S}（竹意軒）")
v14("mew", star=f"{B5W}（v1.4 再查）")
v14("geisha",
    [c("rff-geisha", "fertile_width", "~3", "孢子葉寬", "寬 → 寬鬆 3", "Its fertile fronds are broad and do not grow excessively long")],
    star=f"{B5S}（Rainforest Flora、阿金）")
v14("snow-white-x-suddan",
    [c("ajins-snow-white-x-suddan", "fertile_width", "~3", "寬手延展的葉型", "寬 → 寬鬆 3", "呈現出寬手延展的葉型與濃密細緻的白毛質感")],
    star=f"{B5S}（阿金）")
v14("bambi",
    [c("ajins-bambi", "fertile_hair", "~3", "葉面白毛細緻柔和", "有白毛 → 寬鬆 3", "葉面白毛細緻柔和，孢子葉分岔自然")],
    star=f"{B5S}（阿金）")
v14("stella-aeterni", star=f"{B5S}（阿金：沒有新說法）")
v14("tide",
    [c("haruhana-tide", "shield_height", "~3", "小巧精緻的冠型", "有冠 → 寬鬆 3", "卻在其中蘊藏著小巧精緻的冠型")],
    star=f"{B5S}（晴花鹿苑）")

# ---------------------------------------------------------------- v1.4 B6 (2026-10-19): FSQ（捲捲鹿）系
# Wanna's catalogs give names and prices only; no named FSQ selection has a description beyond what v1.3 cited.
B6S = "v1.4 重讀已引用頁面"
v14("foong-si-qi",
    [c(FSQ, "size", "~M", "與亞猴同屬中等體型", "中型 → 寬鬆 M", "成熟植株直徑可達 60~100 公分，與 亞猴鹿角蕨 同屬中等體型的 鹿角蕨品種 之一"),
     c(FSQ, "fertile_hair", "~3", "葉面如檸檬鹿角蕨覆白毛", "有白毛 → 寬鬆 3", "最大特色是 360 度捲曲的孢子葉末端，葉面如 檸檬鹿角蕨 覆白毛且葉脈清晰"),
     c(FSQ, "shield_height", "~1", "成株營養葉包覆介質生長", "包覆附著物 → 寬鬆 1", "上板成株 營養葉包覆介質生長 1~2 年後手開始捲曲")],
    star=f"{B6S}（微體溫室〈捲捲鹿〉、Rainforest Flora、Jungle Leaves、Wanna 型錄）")
v14("ss-foong", star=f"{B6S}（阿金、竹意軒只寫分岔多）")
v14("fsq", star=f"{B6S}（Wanna 型錄、微體溫室：孢子苗系，沒有型態描述）")
v14("ginka", star=f"{B6S}（晴花鹿苑、阿金：沒有新說法）|We Love Tropical Plants（不採用）")
v14("white-gizmo",
    [c("haruhana-white-gizmo", "fertile_width", "~3", "喜歡寬葉者必備", "寬葉 → 寬鬆 3", "其色澤白皙迷人，帶著明顯的葉脈紋理。 喜歡寬葉、白皙的收藏家必備的經典品種。"),
     c("haruhana-white-gizmo", "fertile_hair", "~3", "色澤白皙", "白皙 → 寬鬆 3", "其色澤白皙迷人，帶著明顯的葉脈紋理。")],
    star=f"{B6S}（晴花鹿苑）")
v14("little-sis",
    [c(wc("2020-03"), "fertile_hair", "~3", "葉面有毛而呈淺灰綠", "有毛、看得出底色 → 寬鬆 3",
       "color leaves are light green-grey because have hairs and spore patches are thick make their tips are a bit curly")],
    star=f"{B6S}（Wanna 型錄）")
for pid in ("wannasiqi", "kin-norn", "kin-naree", "ivory", "green-moon", "cotton-moon", "kusuma", "fsq-dwarf", "oliver-siqi", "thipsiqi"):
    v14(pid, star=f"{B6S}（Wanna 2020–2026 型錄只有品名與價格）")
v14("sazanami", star=f"{B6S}（Haruhana USA：沒有新說法）")
v14("wfsq", star=f"{B6S}（晴花鹿苑：沒有新說法）")

# ---------------------------------------------------------------- v1.4 B7 (2026-10-19): 非洲、馬達加斯加、象耳、安地斯群的交種與品系
B7S = "v1.4 重讀已引用頁面"
B7W = "搜尋：英文品名＋Platycerium staghorn（只有 Orchideeën Shop、RHS 的泛用文字）"
ALCT10 = "圓盾鹿角蕨品種｜圓盾鹿角蕨來源｜圓盾鹿角蕨型態"
v14("elemaria", star=f"{B7S}（Hoshizaki & Price 1990 的「可達」尺寸改記寬鬆說法）")
v14("alcicorne-x-ellisii", star="v1.4 再查：搜尋英文品名（沒有描述）")
v14("horne-surprise", star=f"{B7S}（Halling、微體溫室：沒有新說法）")
v14("erawan", star=f"{B7S}（微體溫室〈象耳〉、Halling 交種表）|{B7W}")
v14("budsaba", star="v1.4 再查：搜尋英文品名（沒有描述）")
v14("neptune", star=f"{B7S}（微體溫室〈象耳〉）|{B7W}")
v14("antis", star=f"{B7S}（微體溫室〈象耳〉）|{B7W}")
v14("saikeaw", star="v1.4 再查：搜尋英文品名（沒有描述）")
v14("siamense",
    [c(HH, "fertile_width", "~3", "孢子葉寬", "寬 → 寬鬆 3", "Grows massive shield fronds like the P. elephantotis and wide fertile fronds, only deeply branched like the P. willinckii."),
     c(HH, "shield_height", "~5", "盾葉巨大，像象耳", "巨大冠型 → 寬鬆 5", "Grows massive shield fronds like the P. elephantotis"),
     c("ajins-elephantotis-x-willinckii", "fertile_width", "~3", "有象耳的大寬手", "寬 → 寬鬆 3", "有象耳的大寬手，也有爪哇的分岔")],
    star=f"{B7S}（Halling、阿金、Siam Exotica 存檔）")
v14("moose",
    [c("ajins-moose", "fertile_hair", "~1", "葉面油亮厚實", "油亮 → 寬鬆 1", "葉面油亮厚實，整體質感沉穩且富有光澤"),
     c("ajins-moose", "fertile_posture", "~spread", "新葉分岔密集，展開呈扇形", "展開 → 寬鬆 spread", "新葉成長時分岔密集，展開呈現扇形層次"),
     c("mo-alcicorne", "fertile_posture", "~spread", "孢子葉分岔多，如駝鹿角展開", "展開 → 寬鬆 spread", f"{ALCT10} ... 駝鹿鹿角蕨｜非圓X深綠｜孢子葉分叉多 如駝鹿角展開")],
    star=f"{B7S}（阿金、微體溫室〈圓盾〉）|{B7W}")
v14("burirom", star=f"{B7S}（微體溫室〈象耳〉只寫末端大波浪）|{B7W}")
v14("alcicorne-x-elephantotis",
    [c("ajins-alcicorne-africa-x-elephantotis", "shield_height", "~3", "營養葉呈冠型", "有冠 → 寬鬆 3", "非洲圓盾交象耳鹿角蕨營養葉呈冠型"),
     c("ajins-alcicorne-africa-x-elephantotis", "fertile_width", "~3", "孢子葉像象耳一樣寬大", "寬 → 寬鬆 3", "孢子葉和象耳一樣是較寬大的型態，在末端會分岔"),
     c("mo-alcicorne", "shield_height", "~3", "非圓象：營養葉冠明顯", "有冠 → 寬鬆 3", f"{ALCT10} ... 非圓象鹿角蕨｜非圓X象耳｜孢子葉寬大 營養葉冠明顯"),
     c("mo-alcicorne", "fertile_width", "~3", "非圓象、馬圓象：孢子葉寬大", "寬 → 寬鬆 3",
       f"{ALCT10} ... 非圓象鹿角蕨｜非圓X象耳｜孢子葉寬大 營養葉冠明顯 ... 馬圓象鹿角蕨｜馬圓X象耳｜孢子葉寬大 末端波浪狀")],
    star=f"{B7S}（阿金、微體溫室〈圓盾〉〈象耳〉）")
v14("andinum-x-stemaria", star=f"{B7S}（卡呸醬只寫「大手」）")
v14("callard",
    [c("halling-callard", "fertile_width", "~3", "孢子葉寬、分岔", "寬 → 寬鬆 3", "the quadridichotomum trait is obvious in the fertile fronds with the wide frond and the forking"),
     c("halling-callard", "shield_height", "~3", "盾葉高而窄", "直立、高 → 寬鬆 3", "The andinum is also apparent in the fertile fronds plus the tall narrow shield frond"),
     c(KP, "shield_height", "~3", "高冠", "高冠 → 寬鬆 3", "安地斯ｘ四叉006 | andinumｘquadridichotomum 高冠、長手深岔")],
    star=f"{B7S}（Halling Callard.htm、卡呸醬）")
v14("roy-vail",
    [c(HH, "shield_height", "~3", "盾葉高而窄", "直立、高 → 寬鬆 3", "The shield fronds are waffled like the P. madagascariense , but tall and narrow like the P. andinum ."),
     c(HH, "fertile_width", "~3", "孢子葉寬、會分岔", "寬 → 寬鬆 3", "The fertile fronds are wide and forked like the P. madagascariense yet longer like the P. andinum.")],
    star=f"{B7S}（Halling）")
v14("dawboy",
    [c("halling-dawboy", "size", "~S", "植株小，像非猴", "小型 → 寬鬆 S", "The plant is small like P. madagascariense ."),
     c("halling-dawboy", "fertile_width", "~3", "孢子葉深綠、寬", "寬 → 寬鬆 3", "The P. dawboy is characterized by having the dark green, wide fertile fronds with spore patched on the tips.")],
    star=f"{B7S}（Halling、阿金）|{B7W}")
v14("larry-weed",
    [c(HH, "fertile_width", "~3", "孢子葉較寬", "寬 → 寬鬆 3", "The fertile frond is wider, waxy like with pronounced veins.")],
    star=f"{B7S}（Halling）")
v14("alcicorne-africa",
    [c("halling-dawboy", "fertile_width", "~1", "孢子葉比馬達加斯加型窄", "窄 → 寬鬆 1",
       "Whereas the P. alcicorne from East Africa is yellow green, waxy, hairless and narrow compared to the Madagascar variety.")],
    star=f"{B7S}（Halling、微體溫室〈圓盾〉、Jungle Leaves）")
v14("alcicorne-madagascar",
    [c("halling-dawboy", "fertile_width", "~3", "孢子葉寬、深綠", "寬 → 寬鬆 3", "The fertile fronds of the P. alcicorne from Madagascar is characteristically; wide, and dark green.")],
    star=f"{B7S}（Halling、微體溫室〈圓盾〉、Jungle Leaves）")
v14("alcicorne-gorgon", star=f"{B7S}（竹意軒只寫葉緣波浪狀）")
v14("elephantotis-mammoth", star=f"{B7S}（微體溫室〈象耳〉只寫葉脈浮凸、長橢圓）")
v14("alcicorne-madagascar-dwarf",
    [c("haruhana-alcicorne-dwarf", "shield_form", "~appressed", "盾狀營養葉包覆水苔，溫和圓潤", "圓形、包覆附著物 → 貼伏", "繼承馬圓可愛的盾狀營養葉，包覆水苔後有著溫和圓潤的造型。"),
     c("haruhana-alcicorne-dwarf", "shield_height", "~1", "營養葉包覆水苔", "包覆附著物 → 寬鬆 1", "繼承馬圓可愛的盾狀營養葉，包覆水苔後有著溫和圓潤的造型。"),
     c("haruhana-alcicorne-dwarf", "fertile_hair", "~3", "層次豐富的 Q 毛孢子葉", "有毛 → 寬鬆 3", "成株低調的營養葉搭配著層次豐富的Q毛孢子葉")],
    star=f"{B7S}（晴花鹿苑、阿金、Jungle Leaves、微體溫室）")
v14("horne-surprise-darwin", star=f"{B7S}（阿金只有品名；Orchideeën Shop 是泛用文字）")
v14("durval-nunes",
    [c("platyceriumferns-durval", "shield_height", "~1", "盾葉抱住附著物", "包覆附著物 → 寬鬆 1", "Like P.madagascariense it has the waffle like texture and grasping shields.")],
    star=f"{B7S}（platyceriumferns.com、Exotica Esoterica、Halling）")

# ---------------------------------------------------------------- v1.4 B8 (2026-10-19): 亞猴、皇冠群與巨型群
B8S = "v1.4 重讀已引用頁面"
B8W = "搜尋：英文品名＋Platycerium staghorn（只有種的描述）"
SAMEAJ = "阿金〈美猴王〉與〈圓葉亞猴〉兩頁文字相同，無法確認描述的是哪個品種，不採用"
CRT = "皇冠鹿角蕨品種｜皇冠鹿角蕨體型｜皇冠鹿角蕨孢子葉型態"
v14("ridleyi-x-coronarium", star=f"{B8S}（Halling；Ploy-ratana 2014 只取得書目）|{B8W}")
v14("coronarium-x-bifurcatum",
    [c("ajins-bifurcatum-x-coronarium", "shield_height", "~3", "有皇冠高聳雄偉的營養葉", "高冠 → 寬鬆 3", "同時擁有皇冠高聳雄偉的營養葉，以及二叉迷人的分岔。")],
    star=f"{B8S}（阿金、卡呸醬）")
v14("flamenco",
    [c("ajins-flamenco", "shield_height", "~3", "有高冠的結構感", "高冠 → 寬鬆 3", "成熟後株型立體，葉片線條流暢，兼具高冠的結構感與深綠系統的穩定表現")],
    star=f"{B8S}（阿金、晴花鹿苑）")
v14("ridleyi-wide",
    [c("mo-ridley", "fertile_width", "~3", "孢子葉幅寬大", "寬 → 寬鬆 3", f"{RID} ... 寬葉亞猴鹿角蕨（摩天輪）｜中等｜1. 孢子葉幅寬大 2. 營養葉脈紋呈幅射向外"),
     c(KP, "fertile_width", "~3", "圓葉捲邊", "圓葉 → 寬鬆 3", "寬葉亞猴 寬葉亞洲猴腦019 | Platycerium ridleyi 圓葉捲邊")],
    star=f"{B8S}（微體溫室〈亞猴〉、卡呸醬）")
v14("ridleyi-jade-peony", star=B8W)
v14("ridleyi-dwarf-silver",
    [c("mo-ridley", "fertile_hair", "~3", "孢子葉末端銀白", "末端銀白 → 有白毛，寬鬆 3", f"{RID} ... 侏儒銀葉鹿角蕨｜中偏易｜1. 孢子葉末端銀白 2. 幼苗期營養葉脈紋明顯 3. 整體型態嬌小")],
    star=f"{B8S}（微體溫室〈亞猴〉）")
v14("ridleyi-pakarang", star=B8W)
v14("ridleyi-monkey-king", star=f"{B8S}（{SAMEAJ}）|{B8W}|We Love Tropical Plants（不採用）")
v14("ridleyi-round", star=f"{B8S}（{SAMEAJ}；阿金頁是孢子苗）|We Love Tropical Plants（不採用）")
v14("ridleyi-thin", star=f"{B8S}（阿金、微體溫室：「葉柄細長」不是裂片寬度）")
v14("coronarium-thin",
    [c("mo-crown", "size", "~L", "大型種", "大型 → 寬鬆 L", f"{CRT} ... 細葉皇冠鹿角蕨｜大型種｜細葉 末端微捲"),
     c("mo-crown", "fertile_width", "~1", "細葉", "細葉（內文描述）→ 寬鬆 1", f"{CRT} ... 細葉皇冠鹿角蕨｜大型種｜細葉 末端微捲"),
     c("ajins-coronarium-thin", "fertile_width", "~1", "孢子葉較為細長", "細長 → 寬鬆 1", "細葉皇冠的孢子葉較為細長優雅，相當具有特色")],
    star=f"{B8S}（微體溫室〈皇冠〉、阿金：皇冠種的描述不套用）")
v14("kitshakood-thin-dwarf", star=f"{B8S}（阿金只有學名標示）")
v14("kitshakood-x-ridleyi", star=f"{B8S}（阿金：沒有新說法）")
v14("kitshakood-round-frond", star=f"{B8S}（阿金只寫營養葉較圓）")
v14("superbum-x-wandae", star=B8W)
v14("charles-alford", star=f"{B8S}（Halling：幼株盾葉貼伏是幼葉，不採用）|{B8W}")
v14("joe-young", star=B8W)
v14("grande-x-elephantotis",
    [c("mo-elephant", "size", "~XL", "整體最為巨大", "巨大 → 寬鬆 XL", f"{EL} ... 巨獸象耳鹿角蕨（巨象）｜中偏易｜整體最為巨大 葉型呈長橢圓")],
    star=f"{B8S}（微體溫室〈象耳〉）")
v14("holttumii-x-wandae", star=f"{B8S}（卡呸醬只寫孢子葉型態）")
v14("holttumii-x-elephantotis", star=f"{B8S}（卡呸醬「大臉大手」、Siam Exotica 存檔）")
v14("wandae-x-veitchii", star=f"{B8S}（阿金：沒有能換算的說法）")
v14("wallichii-x-willinckii",
    [c("ajins-wallichii-x-willinckii", "fertile_width", "~3", "蝴蝶般寬大分岔的孢子葉", "寬 → 寬鬆 3", "擁有蝴蝶般寬大分岔的孢子葉，葉紋深邃，整體有如扇形開展一般"),
     c("ajins-wallichii-x-willinckii", "fertile_posture", "~spread", "整體如扇形開展", "展開 → 寬鬆 spread", "整體有如扇形開展一般，也擁有爪哇的飄逸姿態"),
     c(KP, "shield_height", "~3", "高冠", "高冠 → 寬鬆 3", "蝴蝶ｘ爪哇013 | P. Wallickii x Willinckii TC 高冠、寬葉淺裂"),
     c(KP, "fertile_width", "~3", "寬葉淺裂", "寬葉 → 寬鬆 3", "蝴蝶ｘ爪哇013 | P. Wallickii x Willinckii TC 高冠、寬葉淺裂")],
    star=f"{B8S}（阿金、卡呸醬）")
v14("mentelosii", star=f"{B8S}（Hoshizaki 1975、Halling：沒有缺欄可補的新說法）")
v14("wandae-dwarf", star=f"{B8S}（阿金只寫「小而捲」）")
# ---------------------------------------------------------------- Banna series (2026-10-20): 泰國 Banna 園子的編號交種
# 只收 #A、#B：兩者都有直接描述的來源與親本說法。#G（只有一家美國賣家寫 veitchii × bifurcatum）、#J（只知道收錄在《ビカクシダ2》）
# 資料不足，記在 species_list.md。We Love Tropical Plants 的 #A 頁照護段是通用文字（"Like most staghorn ferns"），且該店沒有地區資料，不引用。
BNS = ("搜尋：Platycerium Banna hybrid|搜尋：鹿角蕨 Banna 品種|搜尋：ビカクシダ バンナ 交配 親|搜尋：\"Banna #B\"～\"#E\" platycerium"
       "|風和日麗、LEO雨林植物、calmplants、GreenSnap、We Love Tropical Plants、Orchids-shop、Seed Studio 商品頁|ビカク図鑑、egcworks 品種一覽（都沒有收錄）")
BLOCKS["banna-a"] = dict(
    cites=[
        c("lwhp-banna-a", "pups", "yes", "多芽型", "", "屬多芽型鹿角蕨"),
        c("lwhp-banna-a", "fertile_hair", "~3", "表面有薄薄的一層白毛", "有白毛 → 寬鬆 3", "表面有薄薄的一層白毛"),
        c("lwhp-banna-a", "size", "~S", "成株比二叉明顯小", "偏小、沒有說侏儒 → 寬鬆 S", "成株相較二叉也明顯較小"),
        c("lwhp-banna-a", "difficulty", 1, "適應力極強，適合新手入門", "新手、入門 → 1", "P. Banna #A 適應力極強，好照顧，適合新手入門"),
        c("lwhp-banna-a", "humidity", 5, "營養葉薄，需要高濕度", "high humidity → 5", "營養葉薄，需要高濕度，但太濕狀況下，容易葉傷。"),
        c("lwhp-banna-a", "light", 3, "不適合太強的日照，適合半日照遮陰處", "半日照 → 3", "孢子葉薄，不適合太強的日照，適合半日照遮陰處。"),
        c("lwhp-banna-a", "parents", "bifurcatum|willinckii", "日本普鹿交種 × 爪哇", "二叉這一方是園藝品系 'Japanese hybrid'",
          "P. Banna #A 鹿角蕨（P. Bifurcatum Japanese hybrid x P. Willinckii 日本普鹿交種爪哇）"),
        c("leo-banna-a", "parents", "bifurcatum|willinckii", "爪哇 × 二叉 'Japanese hybrid'", "與風和日麗的寫法正反相反", "P. willinckii x bif. cv. Japanese hybrid"),
        c("leo-banna-a", "origin", "泰國 Banna 園子", "泰國 Banna 的園子", "交種沒有 T1、T2，採 T3", "泰國Banna的園子代標性作品之一，葉白分岔極美。"),
        c("leo-banna-a", "fertile_hair", "~3", "葉白", "有白毛 → 寬鬆 3", "葉白分岔極美"),
        c("leo-banna-a", "light", 3, "陽光不直曬，散光", "店家通用照護文字，與 #B 頁逐字相同 → 不採用", "陽光不直曬，散光及通風良好的環境", "", "excluded"),
        c("calmplants-banna-a", "parents", "bifurcatum|willinckii", "爪哇與二叉的交配種（聽說）", "原文為傳聞語氣", "バンナ＃Aは、ウィリンキーとビフルカツムの交配種だそう。"),
        c("calmplants-banna-a", "size", "~S", "比較緊湊（聽說）", "compact → 寬鬆 S", "バンナ＃Aは環境にもよりますが、比較的コンパクトに育つらしいです。"),
        c("calmplants-banna-a", "fertile_width", "~1", "孢子葉比 #B 細", "細 → 寬鬆 1", "＃Bよりも＃Aの方が胞子葉が細くて多分岐で、色も白いので人気でがあるそう。"),
        c("calmplants-banna-a", "fertile_hair", "~3", "星狀毛細緻", "有白毛 → 寬鬆 3", "バンナ＃Aの星状毛は細かくて上品に見えます。"),
        c("orchids-shop-banna-a", "parents", "andinum", "安地斯鹿角蕨的選拔", "與其他來源都不同，疑似誤植 → 不採用",
          "De Platycerium Banna #A is a special variation of Platycerium andinum", "", "excluded"),
        c("orchids-shop-banna-a", "fertile_length", "~100 cm", "孢子葉可超過 1 m、下垂", "描述的是安地斯鹿角蕨，疑似誤植 → 不採用",
          "De Banna #A is known for its elongated, gracefully drooping fertile leaves that can reach over a meter.", "", "excluded"),
    ],
    extra={"parents"},
    desc=[
        ("泰國 Banna 園子的代表作之一，葉色偏白、分岔多。", "leo-banna-a", "泰國Banna的園子代標性作品之一，葉白分岔極美。", ""),
        ("多芽型，孢子葉比二叉明顯短、分岔多，表面有薄薄一層白毛；成株比二叉明顯小，生長快。", "lwhp-banna-a",
         "屬多芽型鹿角蕨，表面有薄薄的一層白毛，手相較二叉明顯較短且分岔多，成株相較二叉也明顯較小，同樣生長快速", ""),
        ("星狀毛細緻，孢子葉壽命長，植株看起來茂密。", "calmplants-banna-a",
         "バンナ＃Aの星状毛は細かくて上品に見えます。... 胞子葉が長持ちするので、葉が沢山茂って見た目がとっても華やか。", ""),
    ],
    note=[
        ("親本一般寫作二叉的園藝品系 'Japanese hybrid' × 爪哇，各來源的正反交方向不一致。", "lwhp-banna-a",
         "P. Bifurcatum Japanese hybrid x P. Willinckii 日本普鹿交種爪哇", ""),
        ("同系列還有 #B、#G、#J；日本玩家說 #A 以外的編號較少流通，#A 因孢子葉較細、分岔多、顏色白而比 #B 受歡迎。", "calmplants-banna-a",
         "そう、バンナ＃Bもあります。なんならバンナ＃Jもあります。ハチ的には＃A以外はあまり出回っていない印象でしたが、最近は＃Gも見かけるようになりました。", ""),
        ("#J 收錄在日本的《ビカクシダ2》一書。", "calmplants-banna-a-2", "今話題の「ビカクシダ2」には、バンナ＃Jが掲載されています。", ""),
        ("荷蘭 Orchids-shop 把它寫成安地斯鹿角蕨的選拔，與其他來源都不同，疑似誤植。", "orchids-shop-banna-a",
         "De Platycerium Banna #A is a special variation of Platycerium andinum", ""),
    ],
    searched=searched(BNS, f"{BNS}（LEO雨林植物的照顧方式是店家通用文字）"),
    version="v1.4", date="2026-10-20",
)
BLOCKS["banna-b"] = dict(
    cites=[
        c("leo-banna-b", "origin", "泰國 Banna 園子", "泰國 Banna 園子的交種", "交種沒有 T1、T2，採 T3", "泰國Banna園子的交種，白皙細手"),
        c("leo-banna-b", "fertile_width", "~1", "細手", "細 → 寬鬆 1", "泰國Banna園子的交種，白皙細手"),
        c("leo-banna-b", "fertile_hair", "~3", "白皙", "有白毛 → 寬鬆 3", "泰國Banna園子的交種，白皙細手"),
        c("leo-banna-b", "light", 3, "陽光不直曬，散光", "店家通用照護文字，與 #A 頁逐字相同 → 不採用", "陽光不直曬，散光及通風良好的環境", "", "excluded"),
        c("greensnap-banna-b", "parents", "bifurcatum|willinckii", "二叉 'japanese hybrid' × 爪哇", "", "P. Banna #B ( P. bifurcatum 'japanese hybrid'x P. willinckii )"),
        c("greensnap-banna-b", "fertile_posture", "~pendant", "孢子葉應該會下垂", "栽培者自己植株的觀察；下垂 → 寬鬆 pendant",
          "下2本の胞子葉のように垂れるはずが、ライトが近すぎたせいか上の3本は短くなってしまいました"),
    ],
    extra={"parents"},
    desc=[("泰國 Banna 園子的交種，孢子葉細、偏白。", "leo-banna-b", "泰國Banna園子的交種，白皙細手", "")],
    note=[
        ("日本玩家比對親株照片，推測 #B 比 #A 整株大、孢子葉較粗、分岔較少，但沒有確定。", "greensnap-banna-b",
         "#Aと親株の写真を比較すると、#Bの方が全体的に大きい・胞子葉太め・分岐少なめ？？", ""),
        ("同一位玩家說只找得到 #A 與 #B 的親株照片。", "greensnap-banna-b", "親株の写真探しましたがAとBしか見つけられませんでした", ""),
    ],
    searched=searched(BNS, f"{BNS}（LEO雨林植物的照顧方式是店家通用文字；GreenSnap 只有栽培紀錄）"),
    version="v1.4", date="2026-10-20",
)
# ---------------------------------------------------------------- build
CARE ={"light", "water", "humidity", "min_temp", "max_temp", "difficulty", "dormancy"}
C = []  # (plant, source, field, value, label, use, claim, quote, page)
for pid, b in BLOCKS.items():
    for src, field, value, label, claim, quote, page, use in b["cites"]:
        assert field in FIELDS or field in b.get("extra", ()), (pid, field)
        C.append((pid, src, field, str(value), label, use, claim, quote, page))
    for kind in ("desc", "note"):
        for s, src, quote, page in b.get(kind, []):
            C.append((pid, src, kind, "", s, "summary", s, quote, page))


def owned(r):
    b = BLOCKS.get(r["plant_id"])
    if not b:
        return False
    if r["field"] in FIELDS or r["field"] in ("desc", "note"):
        return True
    return r["field"] in b.get("extra", ()) and any(x[0] == r["plant_id"] and x[1] == r["source_id"] and x[2] == r["field"] for x in C)


# sources
sh, srows = rw(os.path.join(ROOT, "data/sources.csv"))
srows = [dict(zip(sh, r)) for r in srows]
byid = {r["id"]: r for r in srows}
for s in SOURCES:
    rec = dict(zip(SH, s))
    rec["archive_url"] = rec["archive_url"] or ARCHIVE.get(rec["id"], "")
    assert rec["tier"] and rec["region"] and rec["short"], s
    if s[0] in byid:
        byid[s[0]].update(rec)
    else:
        srows.append(rec)
        byid[s[0]] = rec
write(os.path.join(ROOT, "data/sources.csv"), SH, [[r.get(k, "") for k in SH] for r in srows])
meta = source_meta(srows)
for x in C:
    assert x[1] in meta, x[1]
    assert meta[x[1]]["tier"] != "T4" or x[5] != "summary", x  # T4 is only a lead

# citations
ch, crows = rw(os.path.join(ROOT, "data/citations.csv"))
crows = [dict(zip(ch, r)) for r in crows]
crows = replace_rows(crows, [dict(zip(CH, x)) for x in C], owned)
write(os.path.join(ROOT, "data/citations.csv"), CH, [[r.get(k, "") for k in CH] for r in crows])

# features
by = defaultdict(list)
for x in C:
    by[(x[0], x[2])].append(x)
PLANTS = list(BLOCKS)
summary, detail = feature_rows(PLANTS, by, meta)
FP = os.path.join(ROOT, "data/features.csv")
_, frows = rw(FP) if os.path.exists(FP) else (FH, [])
write(FP, FH, replace_rows(frows, [[str(x) for x in d] for d in detail], lambda r: r[0] in BLOCKS))

# search log (guideline §6)
ACCESSED = "2026-10-15"
log = []
for pid in PLANTS:
    sd = BLOCKS[pid]["searched"]
    for f in FIELDS:
        if f == "size_note" or summary[pid].get(f):
            continue
        partial = any(r[5] != "summary" for r in by.get((pid, f), []))
        log.append([pid, f, BLOCKS[pid].get("version", VERSION), BLOCKS[pid].get("date", ACCESSED), sd.get(f) or sd["care" if f in CARE else "*"],
                    "partial" if partial else "not_found"])
LP = os.path.join(ROOT, "project_plan/survey/search_log.csv")
_, lrows = rw(LP) if os.path.exists(LP) else (LH, [])
write(LP, LH, replace_rows(lrows, log, lambda r: r[0] in BLOCKS))

# plants.csv
ph, prows = rw(os.path.join(ROOT, "data/plants.csv"))
prows = [dict(zip(ph, r)) for r in prows]
urls = {s["id"]: s["url"] for s in srows}
for r in prows:
    pid = r["id"]
    if pid not in BLOCKS:
        continue
    b = BLOCKS[pid]
    for f in FIELDS:
        r[f] = summary[pid].get(f, "")
    r.update(plant_text(summary[pid], lambda f: "／".join(d[5] for d in detail if d[0] == pid and d[1] == f)))
    r.update(b.get("text", {}))
    used = []
    for x in crows:  # every citation of the plant that is not excluded, including rows from other surveys (name, parents …)
        u = urls.get(x["source_id"])
        if x["plant_id"] == pid and x["use"] != "excluded" and u and u not in used:
            used.append(u)
    r["refs"] = "|".join(used)
    r["desc"] = "".join(s for s, *_ in b.get("desc", []))
    r["note"] = "".join(s for s, *_ in b.get("note", []))
    r["survey_version"] = b.get("version", VERSION)
write(os.path.join(ROOT, "data/plants.csv"), ph, [[r.get(k, "") for k in ph] for r in prows])

for pid in PLANTS:
    print(pid, {f: v for f, v in summary[pid].items() if v})
print("citations", len(C), {u: sum(1 for x in C if x[5] == u) for u in ("summary", "reference", "excluded")}, "search_log", len(log))
flush(sys.argv[2:])
