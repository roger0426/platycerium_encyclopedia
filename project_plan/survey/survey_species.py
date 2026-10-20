"""Feature survey of the 18 native species, guideline v1.3.

Every source's statement is kept (citations.csv: value, label, use); summary values and
confidence are computed from the `use = summary` statements.

Writes:
  data/sources.csv                           adds tier/region/short columns and the sources used here
  data/citations.csv                         adds label/use columns; replaces this survey's rows
  data/features.csv                          per-field summary, confidence and every source's label (read by the site); only the 18 species' rows
  data/plants.csv                            migrates to the guideline's columns; fills the 18 species, survey_version = VERSION
  project_plan/survey/species_v3.csv         summary values (wide)
  project_plan/survey/search_log.csv         fields with no summary after the search limit; only the 18 species' rows
Rows are replaced in place (survey_common.replace_rows), so hybrid / cultivar rows written by survey_hybrids.py are kept.
Summary rules shared with survey_hybrids.py live in survey_common.py.
usage: python3 project_plan/survey/survey_species.py . [--adopt | --force]  (manual edits: see survey_common.flush)
"""
import os, sys
from collections import defaultdict

from survey_common import (flush, FIELDS, SCALE, TEMP, T1_TEXT, CULT, DIFF_REGIONS, VERSION, CH, SH, FH, LH, LBL_FORM, LBL_BROWN, LBL_FRINGE,
                           LBL_POST, LBL_SPORE, num, rw, write, replace_rows, source_meta, feature_rows, plant_text as _plant_text)

ROOT = sys.argv[1]
ACCESSED = "2026-10-14"
HB = "https://halling.com/Platyceriums/"
HALLING = "Halling — Hobbyist's Guide to Identifying Platyceriums"
LUCID = "https://apps.lucidcentral.org/ferns/text/entities/"
ATF = "Australian Tropical Ferns and Lycophytes（Australian Tropical Herbarium）"
NPARKS = "NParks Flora & Fauna Web（新加坡國家公園局）"
RHS = "RHS（英國皇家園藝學會）"

# id, title, publisher, url, type, lang, published, reliability, note, tier, region, short
NEW_SOURCES = [
    ("hennipman1982", "A monograph of the fern genus Platycerium (Polypodiaceae)", "Hennipman, E. & Roos, M.C.；Verh. Kon. Ned. Akad. Wetensch., Afd. Natuurk., Tweede Reeks 80: 1–126",
     "https://dwc.knaw.nl/DL/publications/PU00011522.pdf", "reference", "en", "1982-12", "primary", "把 willinckii、veitchii、hillii 處理為 P. bifurcatum 的亞種或變種", "T1", "學術", "Hennipman & Roos 1982"),
    ("ciarle2025", "Evolutionary origins and life-history correlates of coloniality in the epiphytic fern genus Platycerium (Polypodiaceae)",
     "Ciarle, de Bock, Burns & Dececchi；PLoS ONE 20: e0329099", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12316288/", "reference", "en", "2025", "primary",
     "補充資料 S1 有 18 種的叢生／單生判定", "T1", "學術", "Ciarle et al. 2025"),
    ("liu2019", "環境因子與室內維管對女王鹿角蕨光合作用及生長之影響", "劉純安；國立臺灣大學園藝暨景觀學系碩士論文（指導：葉德銘）",
     "https://tdr.lib.ntu.edu.tw/handle/123456789/74704", "reference", "zh-TW", "2019", "primary", "以 2–3 片營養葉的小苗進行生長箱試驗", "T1", "台灣", "劉純安 2019（台大）"),
    ("atf-bifurcatum", "Platycerium bifurcatum", ATF, LUCID + "platycerium_bifurcatum.htm", "database", "en", "", "primary", "含 bifurcatum／veitchii 檢索", "T1", "澳洲", "Australian Tropical Ferns"),
    ("atf-veitchii", "Platycerium veitchii", ATF, LUCID + "platycerium_veitchii.htm", "database", "en", "", "primary", "", "T1", "澳洲", "Australian Tropical Ferns"),
    ("atf-superbum", "Platycerium superbum", ATF, LUCID + "platycerium_superbum.htm", "database", "en", "", "primary", "", "T1", "澳洲", "Australian Tropical Ferns"),
    ("nparks-coronarium", "Platycerium coronarium", NPARKS, "https://www.nparks.gov.sg/florafaunaweb/flora/1/5/1562", "database", "en", "", "secondary", "", "T2", "新加坡", "NParks"),
    ("nparks-ridleyi", "Platycerium ridleyi", NPARKS, "https://www.nparks.gov.sg/florafaunaweb/flora/1/5/1563", "database", "en", "", "secondary", "", "T2", "新加坡", "NParks"),
    ("nparks-bifurcatum", "Platycerium bifurcatum", NPARKS, "https://www.nparks.gov.sg/florafaunaweb/flora/4/5/4576", "database", "en", "", "secondary", "", "T2", "新加坡", "NParks"),
    ("nparks-grande", "Platycerium grande", NPARKS, "https://www.nparks.gov.sg/florafaunaweb/flora/4/5/4577", "database", "en", "", "secondary",
     "盾葉與孢子囊群尺寸與專著的 holttumii 完全相同，疑似誤植", "T2", "新加坡", "NParks"),
    ("rhs-bifurcatum", "Platycerium bifurcatum", RHS, "https://www.rhs.org.uk/plants/13234/platycerium-bifurcatum/details", "database", "en", "", "secondary", "耐寒等級以英國栽培為準", "T2", "英國", "RHS"),
    ("rhs-veitchii", "Platycerium veitchii", RHS, "https://www.rhs.org.uk/plants/13238/platycerium-veitchii/details", "database", "en", "", "secondary", "耐寒等級以英國栽培為準", "T2", "英國", "RHS"),
    ("rhs-superbum", "Platycerium superbum", RHS, "https://www.rhs.org.uk/plants/19712/platycerium-superbum/details", "database", "en", "", "secondary", "耐寒等級以英國栽培為準", "T2", "英國", "RHS"),
    ("ufifas-enh36", "Staghorn Ferns at a Glance（ENH36）", "UF/IFAS Extension（佛羅里達大學）；Sydney Park Brown", "https://journals.flvc.org/edis/article/download/116899/115058/169218",
     "reference", "en", "2007-07", "secondary", "2007 年修訂版；文中 25–30 °F 誤換算為 1.1 °C，應約 −1 °C", "T2", "美國", "UF/IFAS"),
    ("ufifas-gs", "Staghorn Ferns", "UF/IFAS Extension（佛羅里達大學）Gardening Solutions", "https://gardeningsolutions.ifas.ufl.edu/plants/ornamentals/staghorn-fern/",
     "article", "en", "", "secondary", "與 ENH36 同單位，不算獨立來源", "T2", "美國", "UF/IFAS"),
    ("oxford-bg", "Plants 400: Platycerium", "University of Oxford Botanic Garden", "https://herbaria.plants.ox.ac.uk/bol/plants400/Profiles/OP/Platycerium",
     "article", "en", "", "secondary", "", "T2", "英國", "牛津植物園"),
    ("exotica-madagascariense", "Platycerium madagascariense – Waffles and Dream", "Exotica Esoterica", "https://www.exoticaesoterica.com/magazine/platycerium-madagascariense-waffles-and-dream",
     "article", "en", "", "primary", "作者在瓜地馬拉與美國加州溫室的栽培經驗", "T2", "美國", "Exotica Esoterica"),
    ("bowu-wallichii", "【博物一分钟】鹿角蕨 Platycerium wallichii", "博物一分鐘（bilibili 專欄）", "https://www.bilibili.com/read/cv46510290",
     "article", "zh-CN", "", "secondary", "頁面擋爬蟲，原文取自搜尋摘要", "T3", "中國", "博物一分鐘"),
    ("halling-difficulty", "Platyceriums Degree of Difficulty in Growing", HALLING, HB + "Difficulty.htm", "article", "en", "", "primary", "五級難度表", "T2", "美國", "Halling"),
    ("halling-giants", "Platycerium wallichii（含 grande、superbum、holttumii、wandae、wallichii 比較表）", HALLING, HB + "Wallichii.htm", "article", "en", "", "primary",
     "比較表的 holttumii、wallichii、wandae 溫度標示 * 未確認", "T2", "美國", "Halling"),
    ("halling-alcicorne", "Platycerium alcicorne", HALLING, HB + "Alcicorne.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-coronarium", "Platycerium coronarium", HALLING, HB + "Coronarium.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-ellisii", "Platycerium ellisii", HALLING, HB + "Ellisii.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-hillii", "Platycerium hillii", HALLING, HB + "Hillii.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-quadridichotomum", "Platycerium quadridichotomum", HALLING, HB + "Quadridichotomum.htm", "article", "en", "", "secondary", "轉述 Charles Alford（RareFerns.com）", "T2", "美國", "Halling"),
    ("halling-ridleyi", "Platycerium ridleyi", HALLING, HB + "Ridleyi.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-stemaria", "Platycerium stemaria", HALLING, HB + "Stemaria.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-veitchii", "Platycerium veitchii", HALLING, HB + "Veitchii.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-willinckii", "Platycerium willinckii", HALLING, HB + "Willinckii.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("mo-guide", "40 種鹿角蕨一次推薦！新手＆進階鹿角蕨品種栽培懶人包", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/staghorn-fern/", "article", "zh-TW", "", "secondary",
     "逐種的難度（新手／中階／進階）與日照（中強光／中光／低弱光）對照表", "T3", "台灣", "微體溫室"),
    # v1.2
    ("atf-hillii", "Platycerium hillii", ATF, LUCID + "platycerium_hillii.htm", "database", "en", "", "primary", "", "T1", "澳洲", "Australian Tropical Ferns"),
    ("halling-andinum", "Platycerium andinum", HALLING, HB + "Andinum.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-elephantotis", "Platycerium elephantotis", HALLING, HB + "Elephantotis.htm", "article", "en", "", "secondary", "轉述 Roy Vail 的栽培建議", "T2", "美國", "Halling"),
    ("halling-grande", "Platycerium grande", HALLING, HB + "Grande.htm", "article", "en", "", "primary", "比較表的溫度範圍與 Wallichii.htm 不同（grande 40–90 °F、superbum 30–95 °F）", "T2", "美國", "Halling"),
    ("halling-holttumii", "Platycerium holttumii", HALLING, HB + "Holttumii.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-madagascariense", "Platycerium madagascariense", HALLING, HB + "Madagascariense.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-superbum", "Platycerium superbum", HALLING, HB + "superbum.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    ("halling-wandae", "Platycerium wandae", HALLING, HB + "Wandae.htm", "article", "en", "", "primary", "", "T2", "美國", "Halling"),
    # fyi.csv follow-up (2026-10-15)
    ("mo-giant", "巨獸鹿角蕨與巨大鹿角蕨的差異？2 大型鹿角蕨照顧大不同！", "微體溫室 Micro Oasis", "https://micro-oasis.com/posts/giant-staghorn-fern/", "article", "zh-TW", "", "secondary",
     "巨獸（grande）與巨大（superbum）的溫度、日照、澆水對照表", "T3", "台灣", "微體溫室"),
]
ARCHIVE = {"mo-giant": "https://web.archive.org/web/20261015032459/https://micro-oasis.com/posts/giant-staghorn-fern/"}

# tier / region / short for sources added in earlier rounds (by id prefix)
BACKFILL = [
    ("haruhana-", "T3", "台灣", "晴花鹿苑"), ("ajins-", "T3", "台灣", "阿金的便秘花園"), ("mo-", "T3", "台灣", "微體溫室"),
    ("bw-", "T3", "台灣", "商業周刊"), ("sf-", "T4", "國際", "staghornfern.org"), ("bikaku-", "T4", "日本", "ビカク図鑑"),
    ("wltp-", "T3", "", "We Love Tropical Plants"), ("sapphirechild-", "T3", "美國", "SapphireChild Orchids"),
    ("rff-", "T3", "美國", "Rainforest Flora"), ("orchideeen-", "T3", "荷蘭", "Orchideeën Shop"), ("basements-", "T3", "", "The Basements"),
]

SPECIES = ["alcicorne", "andinum", "bifurcatum", "hillii", "veitchii", "willinckii", "coronarium", "elephantotis", "ellisii",
           "grande", "holttumii", "madagascariense", "quadridichotomum", "ridleyi", "stemaria", "superbum", "wallichii", "wandae"]
C = []  # (sp, source, field, value, label, use, claim, quote, page)
def c(sp, src, field, value, label, claim="", quote="", page="", use="summary"):
    C.append((sp, src, field, str(value), label, use, claim, quote, page))
M = "hennipman1982"

# ---------------------------------------------------------------- T1: Hennipman & Roos 1982
# dims: base length, base width, fertile length (lo, hi) in cm; None = not given as a range
T1 = {
 "alcicorne": dict(p="pp. 79–82", dims=((20, 35), (15, 25), (25, 85)), form=("appressed", "upper part appressed, rounded, margin entire"),
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("none", "without fringe"),
    posture=("up", "erect, symmetrical, wedge-shaped"), length=("25–85 cm", "25-85 cm long"), split=("2–3", "2-3 times dichotomously forked"),
    spore=("tips", "situated away from the plant on the ultimate segments and often also around the ultimate sinusses"),
    pups=("yes", "Epiphytic, growing in clusters."),
    origin=("肯亞、坦尚尼亞、羅德西亞（今辛巴威一帶）、莫三比克、葛摩、馬達加斯加、馬斯克林群島（留尼旺、模里西斯）", "Kenya, Tanzania, Rhodesia, Moçambique, Comores, Madagascar, Mascarenes")),
 "andinum": dict(p="pp. 82–84", dims=((40, 60), (15, 30), (100, 200)), form=("erect-wedge", "upper part erect, wedge-shaped, 1, 2(3) times dichotomously forked"),
    vein="veins immersed", brown=("withering", "Basefronds sessile, withering"), fringe=("above-stipe", "fringe ± conspicuous, situated above the stipe only"),
    posture=("pendant", "pendulous, asymmetrical, linear-wedge-shaped"), length=("100–200 cm 以上", "100 to more than 200 cm long"), split=("3–5", "3-5 times ± dichotomously forked"),
    spore=("medial", "facing the plant ... or spread medially"), pups=("yes", "Epiphytic, growing in clusters."), origin=("秘魯、玻利維亞", "Distribution. Peru, Bolivia.")),
 "bifurcatum": dict(p="pp. 88–90", dims=((20, 50), (15, 45), (35, 90)), form=None,
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("none", "without conspicuous fringe"),
    posture=("spread", "Foliage fronds variously spreading, asymmetrical"), length=("35–90 cm", "35-90 cm long"), split=None,
    width=(1, "ultimate segments ± linear or narrowly triangular", "線形、狹三角形 → 1"), hair=(3, "densely set with hairs", "密生 → 3"),
    spore=("tips", "inserted in the apical part"), pups=("yes", "Epiphytic and epilithic, growing in clusters."), origin=("澳洲東部（特別是內陸高原）", "E. Australia, especially the interior tablelands.")),
 "hillii": dict(p="p. 91", dims=((20, 40), (12, 24), (25, 70)), form=("appressed", "upper part rounded, margin entire"), pos_from_t2=True,
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("none", "without conspicuous fringe"),
    posture=("up", "Foliage fronds erect, usually symmetrical"), length=("25–70 cm", "25-70 cm long"), split=None,
    width=(3, "ultimate segments angustate, elliptical to obovate", "橢圓至倒卵形 → 3"), hair=(1, "sparsely set with hairs", "稀疏 → 1"),
    spore=("tips", "inserted in the apical part"), pups=("yes", "Epiphytic and epilithic, growing in clusters."), origin=("新幾內亞、澳洲東部（特別是沿海地區）", "New Guinea, E. Australia, especially in coastal areas.")),
 "veitchii": dict(p="pp. 91–92", dims=((20, 45), (8, 15), (25, 70)), form=("erect-lobed", "upper part elliptical, consisting of unequally long-sized, up to 2 times forked linear lobes"), pos_from_t2=True,
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("none", "without conspicuous fringe"),
    posture=("up", "Foliage fronds erect (to spreading)"), length=("25–70 cm", "25-70 cm (or more) long"), split=("2–3", "2-3 times forked"),
    width=(1, "ultimate segments linear to narrowly triangular", "線形、狹三角形 → 1"), hair=(5, "very densely set with hairs", "極密 → 5"),
    spore=("tips", "inserted in the apical part"), pups=("yes", "Epiphytic and epilithic, growing in clusters."), origin=("澳洲東部", "Distribution. E. Australia.")),
 "willinckii": dict(p="p. 92", dims=(None, None, (25, 90)), form=("erect-lobed", "upper part elliptical, consisting of up to 4 times forked, unequally long-sized, angustate lobes"), pos_from_t2=True,
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("none", "without conspicuous fringe"),
    posture=("pendant", "Foliage fronds ± pendulous, asymmetrical"), length=("25–90 cm", "25-90 cm long"), split=("≤5", "up to 5 times forked"),
    width=(1, "ultimate segments ± angustate triangular", "狹三角形 → 1"), hair=(3, "densely set with hairs", "密生 → 3"),
    spore=("tips", "inserted in the apical part"), pups=("yes", "Epiphytic and epilithic, growing in clusters."), origin=("爪哇、小巽他群島", "Distribution. Java, Lesser Sunda Is."),
    base_len=70, size_excl="盾葉寫「長達 70 cm、寬達 50 cm」（up to），不採計"),
 "coronarium": dict(p="pp. 92–95", dims=((50, 110), (25, 55), (50, 125)), form=("erect-lobed", "upper part erect, elliptical, 2-5 times dichotomously lobed, lobes unequally-long"),
    vein="veins immersed", brown=("green", "Basefronds sessile, green, old fronds recurving"), fringe=("above-stipe", "fringe conspicuous, situated above the stipe only"),
    posture=("pendant", "basal part of frond spreading, otherwise pendulous"), length=("50–125 cm", "50-125 (or more) cm long"), split=("3–7", "3-7 times forked"),
    spore=("shell-lobe", "central lobe, fertile, horizontally exposed, either shell-shaped, or kidney-shaped ... stalk 2-7 cm long"), pups=("yes", "Epiphytic, growing in clusters."),
    origin=("緬甸、泰國、越南、蘇門答臘、馬來半島、新加坡、廖內群島、邦加島、爪哇、阿南巴斯群島、婆羅洲（北部、東部）、菲律賓", "Birma, Thailand, Vietnam, Sumatra, Malay Peninsula, ... Philippines")),
 "elephantotis": dict(p="pp. 95–98", dims=((30, 75), (10, 30), (40, 75)), form=("erect-wedge", "upper part erect, wedge-shaped, apex truncate, margin ± entire"),
    vein="veins immersed", brown=("green", "Base fronds sessile, green, old fronds erect"), fringe=("above-stipe", "fringe conspicuous, situated above the stipe only"),
    posture=("pendant", "pendulous, asymmetrical, obovate, entire"), length=("40–75 cm", "40-75 cm (by 20-55 cm)"), split=("0", "obovate, entire"),
    width=(5, "obovate, entire, 40-75 cm (by 20-55 cm)", "不分裂 → 5"),
    spore=("tips", "soral patch one, horizontally exposed, situated in the apical part"), pups=("yes", "epilithic, growing in clusters."),
    origin=("熱帶非洲大陸，西起塞內加爾、東至肯亞與莫三比克", "Senegal, Guinea, ... Kenya, Angola, Tanzania, Malawi, Zambia, Moçambique")),
 "ellisii": dict(p="pp. 98–99", dims=((20, 30), (15, 20), (30, 60)), form=("appressed", "upper part appressed, rounded, margin entire"),
    vein="veins immersed", brown=("withering", "Basefronds sessile, withering"), fringe=("none", "without fringe"),
    posture=("up", "erect, often symmetrical"), length=("30–60 cm", "30-60 cm long"), split=("0–1", "entire or one time lobed"),
    width=(5, "wedge-shaped to obovate, 30-60 cm long, entire or one time lobed", "多為不分裂 → 5"),
    spore=("tips", "situated away from the plant, in the apical part"), pups=("yes", "Epiphytic, growing in clusters."), origin=("馬達加斯加（東部）", "Distribution. Madagascar. ... 'Domaine de l'Est'")),
 "grande": dict(p="pp. 99–101", dims=((80, 110), (90, 180), (50, 120)), form=("spreading-wedge", "upper part spreading, wedge shaped, apex truncate, 3-5 times dichotomously lobed, lobes equally-long"),
    vein="veins immersed", brown=("green", "Base fronds sessile, green, old fronds recurring"), fringe=("encircling", "fringe conspicuous, encircling the stipes"),
    posture=("spread|pendant", "spreading, lateral appendages pendulous"), length=("50–120 cm", "50-120 cm long"), split=("3–7", "flanked on both sides by 3-7 times forked lateral appendages"),
    width=(5, "soral patch ... 7-35 by 2-22 cm", "孢子囊群寬度上限 22 cm ≥ 20 → 5"),
    spore=("sinus", "one ± semi-circular, horizontally exposed soral patch, situated in the sinus"), pups=("no", "Epiphytic, growing solitary."),
    origin=("菲律賓（呂宋？、提勞、宿霧、民答那峨）", "Philippines (Luzon (?), Ticao, Cebu, Mindanao)"),
    origin_excl="Hoshizaki & Price 1990 pp. 65–66 更正：呂宋的模式產地與宿霧的紀錄都是誤記，以較新的 T1 為準"),
 "holttumii": dict(p="pp. 101–103", dims=((90, 115), (90, 135), (95, 125)), form=("spreading-wedge", "upper part spreading, wedge-shaped, the apex truncate, 3-6 times dichotomously lobed, lobes equally-long"),
    vein="veins immersed", brown=("green", "Basefronds sessile, green, old fronds recurving"), fringe=("encircling", "fringe conspicuous, encircling the stipes"),
    posture=("spread|pendant", "spreading, lateral appendages pendulous"), length=("95–125 cm", "95-125 cm long"), split=("2–5", "3-5 (central lobe) or 2-3 (lateral lobe) times forked lateral appendages"),
    width=(5, "soral patch ... 10-45 by 8-35 cm", "孢子囊群寬度上限 35 cm ≥ 20 → 5"),
    spore=("sinus", "each bearing one ± semi-circular, horizontally exposed soral patch, situated in the sinus"), pups=("no", "Epiphytic, growing solitary."),
    origin=("泰國、柬埔寨、寮國、越南、馬來半島", "Thailand, Cambodia, Laos, Vietnam, Malay Peninsula.")),
 "madagascariense": dict(p="pp. 104–106", dims=((10, 35), (8, 22), (10, 30)), form=("appressed", "upper part appressed, round, margin minutely dentate"),
    vein="veins prominent, forming a waffle-pattern", brown=("darkening", "Base fronds inconspicuously stalked, green, darkening"), fringe=("encircling", "fringe conspicuous, encircling the stipes"),
    posture=("up", "erect, symmetrical, wedge-shaped"), length=("10–30 cm", "10-30 cm long"), split=("1–3", "1-3 times forked"),
    spore=("tips", "situated away from the plant on the (pen-)ultimate segments"), pups=("yes", "Epiphytic, growing in clusters."), origin=("馬達加斯加", "Distribution. Madagascar.")),
 "quadridichotomum": dict(p="pp. 106–107", dims=((18, 40), (7, 17), (15, 40)), form=("erect-wedge", "upper part erect, wedge-shaped, apex truncate, margin entire or irregularly dentate"),
    vein="veins immersed", brown=("withering", "Basefronds sessile, withering"), fringe=("none", "without a fringe"),
    posture=("pendant", "pendulous (spreading when young)"), length=("15–40 cm", "15-40 cm long"), split=("2–4", "2-4 times dichotomously forked"),
    hair=(3, "exposing the densely hairy lower surface", "下表面密毛 → 3"),
    spore=("medial", "facing the plant ... or spread medially"), pups=("yes", "epilithic, often epiphytic, growing in clusters."), origin=("馬達加斯加（西部與北部）", "confined to the western and northern part of Madagascar")),
 "ridleyi": dict(p="pp. 107–108", dims=((20, 50), (20, 40), (25, 50)), form=("appressed", "upper part appressed, ± rounded, margin entire"),
    vein="veins prominent, not forming a waffle-pattern", brown=("green", "Base fronds conspicuously stalked, green"), fringe=("none", "without a fringe"),
    posture=("up", "erect, asymmetrical, ± kidney-shaped"), length=("25–50 cm", "25-50 cm (or more) long"), split=("5–8", "5-8 times dichotomously forked"),
    spore=("shell-lobe", "a central sorallobe, shell-shaped ... stalk 2-10 cm long"), pups=("no", "growing with several specimens in one hosttree, but not in clusters."),
    origin=("泰國（存疑）、蘇門答臘、馬來半島、新加坡、林加群島、婆羅洲（東北部）", "(Thailand), Sumatra, Malay Peninsula, Singapore, Lingga Arch., Borneo (N.E.)")),
 "stemaria": dict(p="pp. 108–110", dims=((30, 60), (15, 30), (30, 90)), form=("erect-wedge", "upper part erect, wedge-shaped, apex truncate, margin entire"),
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("above-stipe", "fringe conspicuous, situated above the stipe only"),
    posture=("spread", "spreading ('laurentii' ± pendulous)"), length=("30–90 cm", "30-90 cm long"), split=("1–2", "1, 2 times dichotomously forked"),
    width=(5, "soral patches ... 7-30 by 5-22 cm", "孢子囊群寬度上限 22 cm ≥ 20 → 5"),
    spore=("sinus", "situated around the ultimate sinusses (var. stemaria)"), pups=("yes", "epilithic, growing in clusters."), origin=("西非至中非（含幾內亞灣島嶼）、烏干達", "Senegal, Guinea, ... Zaire, Angola, Uganda")),
 "superbum": dict(p="pp. 111–113", dims=((90, 160), (75, 150), (75, 160)), form=("spreading-wedge", "upper part spreading, wedge-shaped, the apex truncate, 3-4 times dichotomously forked, lobes equally-long"),
    vein="veins immersed", brown=("green", "Basefronds sessile, green, old fronds recurving"), fringe=("encircling", "fringe conspicuous, encircling the stipes"),
    posture=("spread|pendant", "spreading, lateral appendages pendulous"), length=("75–160 cm", "75-160 cm long"), split=("3–5", "flanked on both sides by 3-5 times forked lateral appendages"),
    width=(5, "soral patch 1 ... 10-42 by 9-68 cm", "孢子囊群寬度上限 68 cm ≥ 20 → 5"),
    spore=("sinus", "soral patch 1, ± semi-circular, horizontally exposed, situated in the sinus"), pups=("no", "Epiphytic, rarely epilithic, growing solitary."),
    origin=("澳洲東部（熱帶與亞熱帶）", "Distribution. E. Australia (tropical and subtropical).")),
 "wallichii": dict(p="pp. 113–115", dims=((20, 65), (20, 50), (25, 75)), form=("erect-multilobed", "upper part erect, wedge-shaped, apex ± truncate, 3-5-times irregularly forked"),
    vein="veins immersed", brown=("withering", "Base fronds sessile, withering"), fringe=("above-stipe", "fringe conspicuous, above the stipe only"),
    posture=("pendant", "pendulous, asymmetrical, wedge-shaped"), length=("25–75 cm", "25-75 cm long"), split=("0–3", "2-3 times forked appendages ... unforked or 1 time forked ... unforked to up to 2 times forked"),
    spore=("sinus", "soral patch ± semi-circular, situated in the ultimate sinus, horizontally exposed"), pups=("no", "growing with several specimens in one hosttree, but not in clusters."),
    origin=("印度東部、緬甸、泰國、中國雲南", "E. India, Birma, Thailand, China (... Yunnan)")),
 "wandae": dict(p="pp. 115–117", dims=((100, 125), (100, 135), (50, 135)), form=("spreading-wedge", "upper part spreading, wedge-shaped, apex truncate, 4-6 times dichotomously forked, lobes equally-long"),
    vein="veins immersed", brown=("green", "Basefronds sessile, green, old fronds recurving"), fringe=("encircling", "fringe conspicuous, encircling the stipes"),
    posture=("spread|pendant", "spreading, lateral appendages pendulous"), length=("50–135 cm", "50-135 cm long"), split=("0–4", "3-4 times forked (medial lobe) or not forked (lateral lobe) lateral appendages"),
    width=(5, "soral patch ... 7-33 by 20-60 cm", "孢子囊群寬度上限 60 cm ≥ 20 → 5"),
    spore=("sinus", "horizontally exposed soral patch, situated in the ultimate sinus"), pups=("no", "Epiphytic, growing solitary."), origin=("新幾內亞", "Distribution. New Guinea.")),
}


def mid(r):
    return (r[0] + r[1]) / 2


for sp, t in T1.items():
    p = t["p"]
    d = max(mid(r) for r in t["dims"] if r)
    parts = [f"{n} {r[0]}–{r[1]}" for n, r in zip(["盾葉長", "盾葉寬", "孢子葉長"], t["dims"]) if r]
    c(sp, M, "size", d, f"D = {d:g} cm", "各範圍中點最大者；" + "；".join(parts), "", p)
    if t.get("size_excl"):
        c(sp, M, "size", "", "up to", t["size_excl"], "base fronds up to 70 by up to 50 cm", p, use="excluded")
    if t["form"]:
        val = t["form"][0]
        if t.get("pos_missing"):
            c(sp, M, "shield_form", val, LBL_FORM[val], "形狀與裂刻符合此型，但未寫上半部位置，也沒有其他來源補充", t["form"][1], p, use="excluded")
        else:
            claim = "形狀與裂刻符合此型；上半部位置依 Halling" if t.get("pos_from_t2") else "依特徵 12、13 的五型判定"
            c(sp, M, "shield_form", val, LBL_FORM[val], claim, t["form"][1], p)
            bl = t.get("base_len") or t["dims"][0][1]
            h = 1 if val == "appressed" else (5 if bl >= 80 else 3)
            c(sp, M, "shield_height", h, LBL_FORM[val] + ("" if h == 1 else f"，盾葉長上限 {bl} cm"),
              "貼伏 → 1" if h == 1 else f"直立／展開，盾葉長度上限 {bl} cm → {h}", t["form"][1], p)
    prom = "prominent" in t["vein"]
    c(sp, M, "shield_vein", "yes" if prom else "no", "隆起" if prom else "埋入", "", t["vein"], p)
    c(sp, M, "shield_browning", t["brown"][0], LBL_BROWN[t["brown"][0]], "", t["brown"][1], p)
    c(sp, M, "shield_fringe", t["fringe"][0], LBL_FRINGE[t["fringe"][0]], "", t["fringe"][1], p)
    c(sp, M, "fertile_posture", t["posture"][0], LBL_POST[t["posture"][0]], "", t["posture"][1], p)
    c(sp, M, "fertile_length", t["length"][0], t["length"][0], "", t["length"][1], p)
    if t["split"]:
        c(sp, M, "fertile_split", t["split"][0], f"{t['split'][0]} 回", "", t["split"][1], p)
    if t.get("width"):
        w = t["width"]
        c(sp, M, "fertile_width", w[0], w[2].split(" → ")[0], w[2], w[1], p)
    if t.get("hair"):
        h = t["hair"]
        c(sp, M, "fertile_hair", h[0], h[2].split(" → ")[0], h[2], h[1], p)
    c(sp, M, "spore", t["spore"][0], LBL_SPORE[t["spore"][0]], "", t["spore"][1], p)
    c(sp, M, "pups", t["pups"][0], "叢生" if t["pups"][0] == "yes" else "單生", "", t["pups"][1], p)
    if t.get("origin_excl"):
        c(sp, M, "origin", t["origin"][0], "原產地", t["origin_excl"], t["origin"][1], p, use="excluded")
    else:
        c(sp, M, "origin", t["origin"][0], "原產地", "", t["origin"][1], p)

c("bifurcatum", M, "shield_form", "appressed", "貼伏或直立", "種描述寫 erect or appressed（有變異），var. bifurcatum 未寫位置 → 依分類階層規則不套用",
  "upper part erect or appressed, rounded to elliptical", "p. 88", use="excluded")
for sp, other in [("bifurcatum", "var. hillii"), ("hillii", "var. bifurcatum")]:
    c(sp, M, "fertile_split", "2–5", "2–5 回（ssp. bifurcatum）", f"這是 ssp. bifurcatum 整體的範圍，含 {other} → 依分類階層規則不套用", "2-5 times forked", "p. 89", use="excluded")

# ---------------------------------------------------------------- other morphology sources
c("hillii", "halling-hillii", "shield_form", "appressed", "緊貼附著物", "", "The shields grow close together, tightly pressed, into layers of old fronds.")
c("willinckii", "halling-willinckii", "shield_form", "erect-lobed", "高、深裂", "", "the shield fronds are different by being very tall and may be deeply lobed")
c("willinckii", "halling-willinckii", "shield_browning", "withering", "很快轉褐", "", "They quickly turn brown")
c("veitchii", "halling-veitchii", "fertile_hair", 5, "大量白毛", "→ 5", "It is covered with a great amount of white hair.")
c("veitchii", "atf-veitchii", "fertile_hair", 5, "濃密星狀毛", "孢子葉下表面被白毛遮住葉脈 → 5", "Plants with a dense covering of stellate hairs, foliage fronds white below obscuring venation")
c("veitchii", "atf-veitchii", "shield_browning", "withering", "乾枯成粉灰色", "", "nest fronds drying to a mushroom pink or grey")
c("bifurcatum", "atf-bifurcatum", "fertile_hair", "1–3", "上表面稀疏、下表面密生", "種描述：上表面 sparsely → 1，下表面 densely → 3，記範圍（檢索表另寫 sparse covering）",
  "upper surface green, ±sparsely stellately hairy; lower surface greyish green, ±densely covered with stellate hairs")
c("bifurcatum", "atf-bifurcatum", "shield_browning", "withering", "檢索表：乾枯成古銅褐色；描述：長期保持綠色",
  "同一頁的檢索表與種描述互相矛盾，不採計", "nest fronds drying to a coppery brown ... remaining green for a long time", use="excluded")
c("alcicorne", "ufifas-enh36", "shield_browning", "withering", "盾葉自然轉褐", "", "Basal fronds turn brown naturally.", "p. 2")
c("elephantotis", "ufifas-enh36", "shield_browning", "withering", "佛州栽培冬季盾葉轉褐",
  "栽培地冬季的季節現象，不是成熟後的老化型態；比照 dormancy「溫帶冬季停滯不算」只供參考", "Basal fronds brown in the winter.", "p. 3", use="reference")
c("coronarium", "halling-coronarium", "shield_vein", "yes", "葉脈突出（幼株）", "照片為幼株，依「以成熟植株為準」排除", "The shield fronds are light green and show protruding veins. This platy appears young", use="excluded")
# Halling's "frill around bud" = the little frills on the shields at the bud that tell wandae from holttumii, not the
# monograph's fringe (character 15); Holttumii.htm also shows "the P. grande photo ... with the little frills",
# contradicting the table's "No" for grande → excluded
FRILL = "Halling 的 frill 指芽點旁盾葉上的小皺褶（用來區分女王與何其美），與專著特徵 15 的領片定義不同；且其何其美頁說 grande 照片有 little frills，與比較表矛盾"
for sp, v, t1 in [("grande", "No", "encircling"), ("superbum", "Yes", "encircling"), ("holttumii", "No", "encircling"), ("wallichii", "No", "above-stipe"), ("wandae", "Yes", "encircling")]:
    c(sp, "halling-giants", "shield_fringe", t1 if v == "Yes" else "none", "芽點有小皺褶" if v == "Yes" else "芽點無小皺褶", FRILL, f"Frill around bud | {v}", use="excluded")
c("alcicorne", "halling-alcicorne", "fertile_hair", 1, "非洲型：幾乎無毛、有蠟質", "兩型不同，種層級不計入", "The African platy is yellow-green in color, waxy with nearly no hairs.", use="reference")
c("alcicorne", "halling-alcicorne", "fertile_hair", 3, "馬達加斯加型：多毛", "兩型不同，種層級不計入", "The Madagascar plants tend to be dark green, with many hair.", use="reference")
c("ellisii", "halling-ellisii", "fertile_hair", 1, "黃綠色、有蠟質", "T1 未描述毛被", "They have the same yellow-green color, waxy coating")
c("bifurcatum", "nparks-bifurcatum", "size", 90, "D = 90 cm", "盾葉 12–45 cm（中點 28.5）、孢子葉約 90 cm → D = 90", "sterile fronds ... about 12 - 45 cm long, fertile fronds ... about 90 cm long")
c("ridleyi", "nparks-ridleyi", "size", 37.5, "D = 37.5 cm", "數字與專著相同，視為轉引專著", "nest-fronds are corrugated, 20–50 by 20–40cm ... fertile fronds are 25–50 cm long", use="reference")
c("grande", "nparks-grande", "size", 112.5, "D = 112.5 cm", "盾葉 90–115 × 90–135 cm 與專著的 holttumii 完全相同，疑似誤植", "measuring about 90 - 115 cm long and 90 - 135 cm wide", use="excluded")
c("coronarium", "nparks-coronarium", "size", 300, "可達 3 m", "「up to」屬極端值", "up to 3m long by 1.5m across when fully grown", use="excluded")
c("coronarium", "halling-coronarium", "size", 366, "台灣植株孢子葉約 12 呎", "單一植株的極端值", "They measure about 12 ft from the bud to the bottom.", use="excluded")
# v1.2 additions
c("veitchii", "halling-veitchii", "shield_form", "erect-lobed", "盾葉上緣高聳指狀", "補上半部位置（直立）；形狀依專著", "You can see in the photo above the tall fingers on the shield fronds")
c("hillii", "atf-hillii", "shield_form", "appressed", "上緣全緣、緊貼附著物", "", "upper margin entire to slightly wavy, firmly appressed to substrate")
c("hillii", "atf-hillii", "shield_browning", "withering", "很快轉褐", "", "soon becoming brown")
c("hillii", "atf-hillii", "fertile_split", "1–5", "1–5 回", "", "distal one-third forked 1–5 times")
c("hillii", "atf-hillii", "fertile_hair", 1, "無毛或近無毛", "glabrous → 1", "ultimate segments oblong, 1–6 cm wide, dark green, glabrous or almost so")
c("hillii", "halling-hillii", "fertile_hair", "1–3", "上表面蠟質、下表面有絨毛", "上表面蠟質 → 1；下表面絨毛 → 3；記範圍", "The tops are waxy with fuzzy hair on the underside.")
c("bifurcatum", "atf-bifurcatum", "fertile_split", "0–5", "0–5 回", "澳洲標本館把 bifurcatum 與 hillii、veitchii 分開處理，直接描述本種", "0–5 times forked")
c("superbum", "atf-superbum", "shield_hair", 3, "密被淡褐色星狀毛", "densely clothed → 3", "appressed to substrate and densely clothed with fawn stellate hairs")
c("superbum", "atf-superbum", "fertile_split", "≤5", "≤5 回", "", "up to 5 times forked")
c("andinum", "ufifas-enh36", "fertile_hair", 5, "密被銀白毛", "dense silvery hairs → 5", "Fronds covered with dense silvery hairs.", "p. 3")
c("andinum", "ufifas-enh36", "shield_hair", 5, "密被銀白毛", "原文 Fronds 未區分盾葉與孢子葉；同文寫明 basal and foliar fronds 都有星狀毛 → 5", "Fronds covered with dense silvery hairs.", "p. 3")
c("stemaria", "halling-stemaria", "fertile_hair", 3, "下表面多毛", "quite hairy → 3", "The wide fertile fronds are often shiny on the upper surface, and quite hairy on the underneath.")
c("stemaria", "ufifas-enh36", "fertile_hair", 5, "幼葉帶銀白", "只描述幼葉，依「以成熟植株為準」排除", "Semi-erect, large foliar fronds with a silvery case when young.", "p. 2", use="excluded")
c("quadridichotomum", "halling-quadridichotomum", "fertile_hair", 3, "下表面密被褐毛", "densely covered with tan hairs → 3", "The lower surface is densely covered with tan hairs.")

# ---------------------------------------------------------------- pups: Ciarle 2025 + extension / Halling
COLONIAL = {"andinum": "叢生、單型", "stemaria": "叢生、多型", "elephantotis": "叢生、多型（P. angolense）", "ellisii": "叢生、單型", "alcicorne": "叢生、多型",
            "madagascariense": "叢生、單型", "quadridichotomum": "叢生、多型", "coronarium": "叢生、單型", "veitchii": "叢生、多型", "willinckii": "叢生、多型",
            "bifurcatum": "叢生、多型", "hillii": "叢生、多型"}
for sp in SPECIES:
    lab = COLONIAL.get(sp, "單生")
    c(sp, "ciarle2025", "pups", "yes" if sp in COLONIAL else "no", lab, "補充資料 S1 File 的 coloniality 判定",
      "Solitary" if sp not in COLONIAL else ("Colonial, polymorphic" if "多型" in lab else "Colonial, monomorphic"), "S1 File, Table S2")
for sp, v, q in [("bifurcatum", "yes", "Produces large numbers of \"pups\""), ("veitchii", "yes", "Produces pups."), ("alcicorne", "yes", "Pups well."),
                 ("hillii", "yes", "Produces pups."), ("stemaria", "yes", "Pups well."), ("andinum", "yes", "Pups well."),
                 ("grande", "no", "Does not pup."), ("superbum", "no", "Does not pup.")]:
    c(sp, "ufifas-enh36", "pups", v, "會長側芽" if v == "yes" else "不長側芽", "", q, "pp. 2–3")
for sp, v in [("grande", "No"), ("superbum", "No"), ("holttumii", "No"), ("wallichii", "Very rare"), ("wandae", "No")]:
    c(sp, "halling-giants", "pups", "no", "不長側芽" if v == "No" else "極少長側芽", "比較表 Volunteer Pups", f"Volunteer Pups | {v}")
c("veitchii", "halling-veitchii", "pups", "yes", "容易長側芽", "", "a ... rugged species which forms pups freely")
c("coronarium", "halling-coronarium", "pups", "yes", "根莖分枝長出新株", "", "branches to the side and peaks out through the shield frond to grow a new pup")

# ---------------------------------------------------------------- dormancy
c("quadridichotomum", M, "dormancy", "yes", "原生地乾季孢子葉內捲", "約 6 個月乾季", "During the long dry season the plants have longitudinally recurved (involuted) foliage fronds", "p. 107")
c("quadridichotomum", "halling-quadridichotomum", "dormancy", "yes", "乾季休眠、轉褐", "", "During the dry season, they go dormant and turn brown, appear dead.")
c("wallichii", "halling-giants", "dormancy", "yes", "栽培下常進入休眠", "", "more often it goes into dormancy and never comes out.")
c("wallichii", "bowu-wallichii", "dormancy", "yes", "旱季枯黃、雨季再萌發", "原文取自搜尋摘要",
  "鹿角蕨的枯黄其实是对旱季干旱气候的适应……待气候重新变得湿润，再萌发出新芽")
c("alcicorne", "halling-alcicorne", "dormancy", "yes", "南加州冬季休眠", "只是溫帶冬季停滯，依定義不算",
  "The shield fronds die in late summer and fall and the plant goes dormant through the winter.", use="excluded")

# ---------------------------------------------------------------- difficulty
HALL = {1: ["alcicorne", "bifurcatum", "hillii", "veitchii", "willinckii"], 2: ["superbum", "grande", "wandae"],
        3: ["andinum", "elephantotis", "ellisii", "holttumii", "stemaria"], 4: ["coronarium", "madagascariense"], 5: ["quadridichotomum", "ridleyi", "wallichii"]}
HALL_LBL = {1: "第 1 級（最容易）", 2: "第 2 級（相當容易）", 3: "第 3 級（需些經驗）", 4: "第 4 級（有點難）", 5: "第 5 級（困難）"}
MOD = {1: ["bifurcatum", "wandae", "veitchii", "elephantotis", "alcicorne", "coronarium", "willinckii", "holttumii", "hillii"],
       3: ["ridleyi", "grande", "wallichii", "ellisii", "superbum", "stemaria"], 5: ["madagascariense", "andinum", "quadridichotomum"]}
MOD_LBL = {1: "新手", 3: "中階", 5: "進階"}
ZH = dict(alcicorne="圓盾", andinum="安地斯", bifurcatum="二叉", hillii="深綠", veitchii="銀鹿", willinckii="爪哇", coronarium="皇冠",
          elephantotis="象耳", ellisii="愛麗絲", grande="巨獸", holttumii="何其美", madagascariense="非猴", quadridichotomum="四叉",
          ridleyi="亞猴", stemaria="三角", superbum="巨大", wallichii="蝴蝶", wandae="女王")
for lv, sps in HALL.items():
    for sp in sps:
        c(sp, "halling-difficulty", "difficulty", 1 if lv <= 2 else 3 if lv == 3 else 5, HALL_LBL[lv], f"Level {lv}；美國來源，只供參考", f"Level {lv}", use="reference")
for v, sps in MOD.items():
    for sp in sps:
        c(sp, "mo-guide", "difficulty", v, MOD_LBL[v], f"「{ZH[sp]}鹿角蕨」列在表格的「{MOD_LBL[v]}鹿角蕨品種」欄")
ENH_DIFF = {"bifurcatum": (1, "最容易", "the easiest to grow"), "veitchii": (1, "容易", "A common and easy-to-grow species"),
            "alcicorne": (1, "容易", "Easy-to-grow species"), "hillii": (1, "容易", "Easy to grow"),
            "stemaria": (5, "較難", "More difficult to grow"), "andinum": (3, "中等難度", "Moderately difficult."),
            "elephantotis": (3, "中等難度", "Moderately difficult."), "grande": (5, "難", "Difficult to grow."),
            "superbum": (5, "難", "Difficult to grow."), "wandae": (5, "難", "Difficult to grow species.")}
for sp, (v, lab, q) in ENH_DIFF.items():
    c(sp, "ufifas-enh36", "difficulty", v, lab, "美國來源，只供參考", q, "pp. 2–3", use="reference")
c("ridleyi", "nparks-ridleyi", "difficulty", 3, "維護需求：中等", "", "Maintenance Requirements | Moderate")

# ---------------------------------------------------------------- light (care recommendations; habitat = reference)
LIGHT = {5: ["bifurcatum", "wandae", "veitchii", "elephantotis", "alcicorne"],
         3: ["coronarium", "willinckii", "holttumii", "ridleyi", "grande", "wallichii", "ellisii"],
         1: ["hillii", "superbum", "stemaria", "madagascariense", "andinum", "quadridichotomum"]}
LLBL = {5: "中強光（夏季遮陰 30%）", 3: "中光（夏季遮陰 50%）", 1: "低弱光（夏季遮陰 70%）"}
for v, sps in LIGHT.items():
    for sp in sps:
        c(sp, "mo-guide", "light", v, LLBL[v], f"「{ZH[sp]}鹿角蕨」列在表格的「{LLBL[v]}」列")
for sp, src, v, lab, q in [
    ("coronarium", "nparks-coronarium", "3–5", "半日照、全日照", "Light Preference | Semi-Shade, Full Sun"),
    ("ridleyi", "nparks-ridleyi", "3–5", "半日照、全日照", "Light Preference | Semi-Shade, Full Sun"),
    ("bifurcatum", "nparks-bifurcatum", 3, "半日照", "Light Preference | Semi-Shade"),
    ("grande", "nparks-grande", 3, "半日照", "Light Preference | Semi-Shade"),
    ("bifurcatum", "rhs-bifurcatum", 3, "半遮蔭", "Partial shade"),
    ("veitchii", "rhs-veitchii", 3, "半遮蔭", "Partial shade"),
    ("superbum", "rhs-superbum", 3, "半遮蔭", "Partial shade"),
    ("veitchii", "ufifas-enh36", 5, "需要大量光線", "requires a lot of light"),
    ("andinum", "ufifas-enh36", 1, "需要低光", "Requires low light."),
    ("stemaria", "halling-stemaria", 1, "一般栽培於低光", "however the plant is normally grown in low light."),
    ("madagascariense", "exotica-madagascariense", 5, "非常明亮", "thrives under very bright, humid, \"cool tropical\" and intermediate conditions"),
    # v1.2: "bright light" without "filtered" or "very" is between 3 and 5 → recorded as 3–5
    ("alcicorne", "halling-alcicorne", "3–5", "明亮光線", "an easy Platycerium that can be grown out doors in bright light"),
    ("elephantotis", "halling-elephantotis", "3–5", "明亮、溫暖", "He cautions about keeping it wet, and under low light ... He recommends bright warm temperatures"),
    ("holttumii", "halling-holttumii", "3–5", "明亮處", "Hobbyists should grow P. holttumii in bright locations with high humidity for best results."),
    ("ellisii", "halling-ellisii", 1, "全遮蔭", "ellissii must require a high humidity with solid shade."),
    ("veitchii", "halling-veitchii", 5, "很高的光量", "It likes very high light levels for these traits to be fully shown."),
    ("willinckii", "halling-willinckii", 3, "中等光線", "It does well in medium light, moist moss, and is not prone to rot."),
    ("grande", "halling-grande", 3, "50% 遮光網", "After one year in under a 50% shade cloth facing south, it has its first fertile frond."),
    ("superbum", "halling-superbum", "3–5", "喜光強於一般鹿角蕨", "Likes brighter light than the average staghorn."),
    ("wandae", "halling-wandae", 3, "明亮散射光", "it likes bright filtered shade, mort than most other platyceriums"),
]:
    c(sp, src, "light", v, lab, "", q, "pp. 2–3" if src == "ufifas-enh36" else "")
HABITAT_LIGHT = {
    "bifurcatum": ("p. 89", 5, "疏林草原", "in more open vegetations (savannah-forest, or brusheries)"),
    "hillii": ("p. 89", 5, "疏林草原", "in more open vegetations (savannah-forest, or brusheries)"),
    "veitchii": ("p. 91", 5, "曝曬的岩石與灌叢", "Exposed on basalt and sandstone in open shrub vegetations"),
    "coronarium": ("p. 95", 3, "遮蔭低枝與曝曬高枝", "growing on shaded low branches as well as on high branches exposed to the sun"),
    "elephantotis": ("p. 98", 5, "含疏林草原", "in several types of primary and secondary forests, and in savannahs"),
    "ridleyi": ("p. 108", 5, "曝曬的高枝", "growing on high branches (more than 25 m above the ground) exposed to the sun"),
    "stemaria": ("p. 110", 3, "曝曬或遮蔭處", "growing either exposed to the sun or in more shady situations"),
    "superbum": ("p. 113", 5, "有時曝露於峽谷岩石", "or exposed on rocks in gorges"),
}
for sp, (page, v, lab, q) in HABITAT_LIGHT.items():
    c(sp, M, "light", v, "原生地：" + lab, "原生地棲地，只供參考", q, page, use="reference")

# ---------------------------------------------------------------- water
for sp, src, v, lab, q, use in [
    ("coronarium", "nparks-coronarium", 3, "中等，偶爾噴霧", "Water Preference | Moderate Water, Occasional Misting", "summary"),
    ("ridleyi", "nparks-ridleyi", 3, "中等，偶爾噴霧", "Water Preference | Moderate Water, Occasional Misting", "summary"),
    ("bifurcatum", "nparks-bifurcatum", 3, "中等", "Water Preference | Moderate Water", "summary"),
    ("grande", "nparks-grande", "3–5", "多水、中等", "Water Preference | Lots of Water, Moderate Water", "summary"),
    ("bifurcatum", "rhs-bifurcatum", "3–5", "生長期充分澆水，冬季少澆", "When in growth water freely ... Water sparingly in winter.", "summary"),
    ("stemaria", "ufifas-enh36", 5, "需經常澆水", "Needs high humidity and frequent watering.", "summary"),
    ("andinum", "ufifas-enh36", 1, "兩次澆水間需乾燥", "needs good ventilation, and drying between waterings", "summary"),
    ("grande", "ufifas-enh36", 1, "容易澆太多", "Likes high humidity but is easily over-watered.", "summary"),
    ("superbum", "ufifas-enh36", 1, "容易澆太多", "Easily over-watered.", "summary"),
    ("wandae", "ufifas-enh36", 1, "容易澆太多", "High humidity, easily over-watered.", "summary"),
    ("veitchii", "halling-veitchii", 1, "澆太多容易出問題", "Over watering can give P. veitchii difficulties", "summary"),
    ("veitchii", "mo-silver", 1, "耐旱、澆透不積水", "充足日照、耐旱喜透氣、澆透不積水", "summary"),
    ("veitchii", "atf-veitchii", 1, "冷涼季節偏乾；具耐旱機制", "Plants should be kept on the dry side in cool weather.", "summary"),
    ("superbum", "atf-superbum", 1, "冷涼季節偏乾", "Plants should be kept on the dry side in cool weather.", "reference"),
    ("wandae", "liu2019", 3, "乾濕交替生長最佳（小苗）", "以20%/70% VWC處理之植株乾重、葉面積、淨光合作用速率與氣孔導度最高", "summary"),
    # v1.2
    ("coronarium", "halling-coronarium", 1, "容易澆太多", "making it light weight and easy to over water.", "summary"),
    ("elephantotis", "halling-elephantotis", 1, "忌長期潮濕，乾旱萎凋可恢復", "if this platy wilts during a dry period, it will recover completely. He cautions about keeping it wet", "summary"),
    ("holttumii", "halling-holttumii", 5, "生長期多澆、保持濕潤", "During growing seasons, water more frequently and keep it extra moist.", "summary"),
    ("willinckii", "halling-willinckii", 5, "水苔保持濕潤", "It does well in medium light, moist moss, and is not prone to rot.", "summary"),
    ("andinum", "halling-andinum", 1, "不喜大量澆水", "Platycerium andinum does not like full sun, or great amounts of water.", "summary"),
    ("ridleyi", "halling-ridleyi", 1, "高濕環境中少澆水", "growing mine in a closed humidity chamber with little air circulation and infrequent watering.", "summary"),
    ("quadridichotomum", "halling-quadridichotomum", 5, "全年充分澆水、不給乾季休眠", "He feels his nicest plants were well watered all year and not given a dry dormancy period.", "summary"),
    ("madagascariense", "exotica-madagascariense", 5, "根團不可長時間乾燥", "the root mass of P. madagascariense should not be allowed to dry out for any prolonged period of time.", "summary"),
    # 微體溫室 species notes (veitchii already cited from the same publisher's 銀鹿 page)
    ("elephantotis", "mo-guide", 5, "性喜暖溼，介質不沾水即可再澆", "象耳鹿角蕨、三角鹿角蕨性喜暖溼，介質摸起來不沾水時就可以再次澆水", "summary"),
    ("stemaria", "mo-guide", 5, "性喜暖溼，介質不沾水即可再澆", "象耳鹿角蕨、三角鹿角蕨性喜暖溼，介質摸起來不沾水時就可以再次澆水", "summary"),
    ("wandae", "mo-guide", 1, "水苔接近全乾再澆透", "女王鹿角蕨、銀鹿鹿角蕨可等到水苔接近全乾再一次澆透", "summary"),
    ("ridleyi", "mo-guide", 1, "夏季待介質偏乾再澆", "亞猴鹿角蕨或非猴鹿角蕨這類怕悶熱的品種，就建議等到介質偏乾時再澆水", "summary"),
    ("madagascariense", "mo-guide", "1–5", "喜介質潮溼，但夏季待偏乾再澆", "同時喜歡介質潮溼、但又怕夏季悶熱 ... 等到介質偏乾時再澆水", "summary"),
    ("ellisii", "mo-guide", 1, "介質不宜長期潮溼", "種植介質不建議長期潮溼，否則易臉黑", "summary"),
]:
    c(sp, src, "water", v, lab, "只講冷涼季節，不計入" if use == "reference" else "", q, "pp. 2–3" if src == "ufifas-enh36" else "", use=use)

# ---------------------------------------------------------------- humidity
HAB_PAGE = {"ridleyi": "p. 108", "coronarium": "p. 95", "veitchii": "p. 91", "quadridichotomum": "p. 106"}
for sp, src, v, lab, q, use, claim in [
    ("ridleyi", "halling-ridleyi", 5, "低濕度地區難栽培", "difficult to grow in low humidity regions", "summary", ""),
    ("coronarium", "halling-coronarium", 5, "原產地多雨高濕", "frequent rain showers with high humidity so the plants never dry out.", "reference", "描述原產地環境，只供參考"),
    ("coronarium", "nparks-coronarium", 3, "偶爾噴霧", "Water Preference | Moderate Water, Occasional Misting", "summary", ""),
    ("ridleyi", "nparks-ridleyi", 3, "偶爾噴霧", "Water Preference | Moderate Water, Occasional Misting", "summary", ""),
    ("stemaria", "ufifas-enh36", 5, "需要高濕度", "Needs high humidity", "summary", ""),
    ("grande", "ufifas-enh36", 5, "喜高濕度", "Likes high humidity", "summary", ""),
    ("wandae", "ufifas-enh36", 5, "高濕度", "High humidity", "summary", ""),
    ("bifurcatum", "rhs-bifurcatum", 5, "高濕度、每日噴霧", "with bright filtered light and high humidity ... mist daily", "summary", ""),
    ("madagascariense", "exotica-madagascariense", 5, "濕潤", "thrives under very bright, humid ... conditions", "summary", ""),
    ("ridleyi", M, 5, "原生地：極濕的森林、沼澤", "Epiphytic in very humid forest types (e.g. swamps)", "reference", "原生地棲地，只供參考"),
    ("coronarium", M, 5, "原生地：終年潮濕的森林", "In everwet primary and secondary forests", "reference", "原生地棲地，只供參考"),
    ("veitchii", M, 1, "原生地：明顯乾季", "in areas with a pronounced dry season", "reference", "原生地棲地，只供參考"),
    ("quadridichotomum", M, 1, "原生地：約 6 個月嚴重乾季", "in areas enduring a severe dry period of ± 6 months of the year", "reference", "原生地棲地，只供參考"),
    # v1.2
    ("ellisii", "halling-ellisii", 5, "需要高濕度", "ellissii must require a high humidity with solid shade.", "summary", ""),
    ("holttumii", "halling-holttumii", 5, "高濕度", "grow P. holttumii in bright locations with high humidity for best results.", "summary", ""),
    ("wandae", "halling-wandae", 5, "溫室栽培以維持高濕", "should be grown in a greenhouse to keep the humidity high", "summary", ""),
    ("madagascariense", "halling-madagascariense", 5, "溫室、高濕度", "best grown in a greenhouse environment with lots of humidity.", "summary", ""),
    ("wallichii", "halling-giants", 5, "潮濕溫室", "Growing environment | Humid Greenhouse", "summary", "比較表的栽培環境"),
]:
    page = HAB_PAGE.get(sp, "") if src == M else ("pp. 2–3" if src == "ufifas-enh36" else "")
    c(sp, src, "humidity", v, lab, claim, q, page, use=use)

# ---------------------------------------------------------------- temperature
def F(f):
    return round((f - 32) * 5 / 9, 1)

# v1.2: only recommended values count; tolerance records ("hardy to", "semi-hardy", "can withstand",
# Halling's comparison-table "Temp Range", whose footnote calls it cold tolerance) are reference
TOL = "耐受紀錄，只供參考"
for sp, src, v, lab, q, use, claim in [
    ("bifurcatum", "rhs-bifurcatum", "10–15", "H1B（10–15 °C）", "H1B", "summary", "RHS 耐寒等級"),
    ("veitchii", "rhs-veitchii", "10–15", "H1B（10–15 °C）", "H1B", "summary", "RHS 耐寒等級"),
    ("superbum", "rhs-superbum", 15, "H1A（> 15 °C）", "H1A", "summary", "RHS 耐寒等級"),
    ("bifurcatum", "ufifas-enh36", F(30), "短時間可耐 25–30 °F", "Hardy to temperatures of 25-30°F (1.1°C) for short periods.", "reference", TOL + "；取 30 °F；原文誤換算為 1.1 °C"),
    ("veitchii", "ufifas-enh36", F(30), "半耐寒至 25–30 °F，可耐輕霜", "Semi-hardy to temperatures of 25-30°F (1.1°C) and tolerant of light frost.", "reference", TOL + "；取 30 °F；原文誤換算為 1.1 °C"),
    ("superbum", "ufifas-enh36", F(30), "短時間可耐 30 °F", "Hardy to 30°F (1.1°C) for short periods", "reference", TOL + "；原文誤換算為 1.1 °C"),
    ("alcicorne", "ufifas-enh36", F(40), "半耐寒至 40 °F", "Semi-hardy to 40°F (4.4°C).", "reference", TOL),
    ("hillii", "ufifas-enh36", F(40), "半耐寒至 40 °F", "Semi-hardy to 40°F (4.4°C).", "reference", TOL),
    ("stemaria", "ufifas-enh36", F(50), "不低於 50 °F", "not below 50°F (10°C)", "summary", ""),
    ("andinum", "ufifas-enh36", F(60), "最低 60 °F", "low of 60°F (15.5°C)", "summary", ""),
    ("elephantotis", "ufifas-enh36", F(60), "最低 60 °F", "low of 60°F (15.5°C)", "summary", ""),
    ("grande", "ufifas-enh36", F(60), "60 °F 以下會受害", "Tender below 60°F (15.5°C).", "summary", ""),
    ("wandae", "ufifas-enh36", F(60), "最低 60 °F", "lows of 60°F (15.5°C)", "summary", ""),
    ("bifurcatum", "ufifas-gs", F(30), "可耐 30 °F", "Platycerium bifurcatum and Platycerium veitchii can withstand temperatures as low as 30°F", "reference", TOL + "；與 ENH36 同單位"),
    ("veitchii", "ufifas-gs", F(30), "可耐 30 °F", "Platycerium bifurcatum and Platycerium veitchii can withstand temperatures as low as 30°F", "reference", TOL + "；與 ENH36 同單位"),
    ("bifurcatum", "oxford-bg", 0, "可耐輕霜", "Some such as Platycerium bifurcatum are very cold hardy, even tolerating light frosts", "reference", TOL + "；輕霜 → 0 °C"),
    ("grande", "halling-giants", F(40), "40–100 °F", "Temp Range | 40 to 100 F", "reference", TOL + "；比較表註「not quite as cold tolerant」，屬耐受範圍"),
    ("superbum", "halling-giants", F(30), "30–100 °F", "Temp Range | 30 to 100 F", "reference", TOL + "；比較表的耐受範圍"),
    ("holttumii", "halling-giants", F(60), "60–100 °F（未確認）", "Temp Range | 60 to 100 F *", "excluded", "來源標示未確認"),
    ("wallichii", "halling-giants", F(60), "60–100 °F（未確認）", "Temp Range | 60 to 100 F *", "excluded", "來源標示未確認"),
    ("wandae", "halling-giants", F(60), "60–100 °F（未確認）", "Temp Range | 60 to 100 F *", "excluded", "來源標示未確認"),
    ("wandae", "halling-wandae", F(60), "喜 60–100 °F", "P. wandae likes temperatures between 60 F and 100 F.", "summary", "物種頁的建議溫度（比較表同值標未確認）"),
    ("wandae", "halling-wandae", F(40), "短時間可耐低溫，40 °F 以下受害", "It will tolerate cold temperatures for a short period, but damage will occur below 40 F.", "reference", TOL),
    ("wandae", "liu2019", 15, "20/15 °C 正常、15/13 °C 寒害（小苗）", "栽培於15/13°C者則遭受寒害，生長受阻", "summary", "研究中夜溫 15 °C 正常、13 °C 寒害 → 15"),
    ("madagascariense", "exotica-madagascariense", 8, "短暫降到 40 多 °F／8 °C 無妨", "these ferns are unfazed by brief dips into the 40s F/8 C", "reference", TOL),
    ("madagascariense", "halling-madagascariense", 0, "曾在 32–110 °F 栽培成功，應避免極端", "it has been successfully grown in temps 32°F to 110°F but the extremes should be avoided", "reference", TOL),
]:
    c(sp, src, "min_temp", v, lab, claim, q, "pp. 2–3" if src == "ufifas-enh36" else "", use=use)
for sp, src, v, lab, q, use, claim in [
    ("grande", "halling-giants", F(100), "40–100 °F", "Temp Range | 40 to 100 F", "reference", TOL),
    ("superbum", "halling-giants", F(100), "30–100 °F", "Temp Range | 30 to 100 F", "reference", TOL),
    ("holttumii", "halling-giants", F(100), "60–100 °F（未確認）", "Temp Range | 60 to 100 F *", "excluded", "來源標示未確認"),
    ("wallichii", "halling-giants", F(100), "60–100 °F（未確認）", "Temp Range | 60 to 100 F *", "excluded", "來源標示未確認"),
    ("wandae", "halling-wandae", F(100), "喜 60–100 °F", "P. wandae likes temperatures between 60 F and 100 F.", "summary", "物種頁的建議溫度"),
    ("wandae", "liu2019", 30, "30/25 °C 正常、35/30 °C 傷害光系統（小苗）", "35/30°C處理之植株不僅受到非氣孔因素限制，還伴隨著光系統II的損傷", "summary", "研究中日溫 30 °C 正常、35 °C 受損 → 30"),
    ("madagascariense", "exotica-madagascariense", 35, "短暫升到 90 多 °F／35 °C 無妨", "pops to highs into the 90s F/35 F", "reference", TOL + "；原文「35 F」應為 35 °C"),
    ("madagascariense", "halling-madagascariense", F(110), "曾在 32–110 °F 栽培成功，應避免極端", "it has been successfully grown in temps 32°F to 110°F but the extremes should be avoided", "reference", TOL),
]:
    c(sp, src, "max_temp", v, lab, claim, q, use=use)

# ---------------------------------------------------------------- fyi.csv follow-up (2026-10-15): findings logged while surveying hybrids
HP = "hoshizaki-price1990"
GT = "巨大鹿角蕨照顧 | 15~27 度 | 中弱光為主（ 夏季降低照度 ） | 4~7 天 一次澆透"
GG = "巨獸鹿角蕨照顧 | 18~35 度 | 中光為主（恆為散射光） | 3~6 天 一次澆透"
for sp, src, f, v, lab, q, use, claim in [
    ("superbum", "mo-giant", "min_temp", 15, "15~27 度", GT, "summary", "照顧對照表的溫度欄"),
    ("superbum", "mo-giant", "max_temp", 27, "夏季不超過 27 度", "與 非猴鹿角蕨 類似 不建議夏季溫度超過 27 度", "summary", ""),
    ("superbum", "mo-giant", "max_temp", 33, "部分馴化個體可耐 33 度", "部分馴化過的個體可耐受到 33 度", "reference", TOL),
    ("superbum", "mo-giant", "light", "1–3", "中弱光為主，夏季降低照度", GT, "summary", "中弱光介於低弱光（1）與中光（3）之間 → 1–3"),
    ("superbum", "mo-giant", "water", 1, "水苔接近全乾才給水", "嚴格控管澆水頻率， 只有在水苔接近全乾才給水", "summary", ""),
    ("superbum", "mo-giant", "dormancy", "yes", "台灣夏季生長遲滯、甚至夏眠", "不像巨大鹿角蕨在夏季會有生長遲滯、甚至夏眠的狀況", "excluded",
     "台灣平地夏季高溫造成的停滯，屬栽培環境反應；比照溫帶冬季停滯不算"),
    ("grande", "mo-giant", "min_temp", 18, "18~35 度，保持 18 度以上", GG, "summary", "照顧對照表的溫度欄；內文另寫「保持 18 度以上的環境溫度」"),
    ("grande", "mo-giant", "max_temp", 35, "18~35 度", GG, "summary", "照顧對照表的溫度欄"),
    ("grande", "mo-giant", "max_temp", 35, "原生地：與台灣相仿的 20~35 度", "原生於菲律賓的原始雨林中，因此氣溫上與台灣相仿在 20~35 度", "reference", "原生地氣候，只供參考"),
    ("grande", "mo-giant", "light", 3, "中光為主（恆為散射光）", GG, "summary", ""),
    ("grande", "mo-giant", "water", 1, "長大後耐旱，介質全乾再澆透", "偏好介質全乾再一次澆透", "summary", ""),
    ("elephantotis", "mo-elephant", "min_temp", 15, "保持 15 度以上", "保持 15 度以上的環境溫度", "summary", ""),
    ("elephantotis", "mo-elephant", "water", 5, "需水量大，不用等介質全乾", "象耳鹿角蕨是需水量大的鹿角蕨品種，只要水苔摸起來不沾水即可再澆水，不用等到介質全乾。", "summary", ""),
    ("elephantotis", "mo-elephant", "difficulty", 1, "容易", "象耳鹿角蕨（原生象） | 容易", "summary", "〈象耳鹿角蕨 8 品種照顧圖鑑〉表格中「象耳鹿角蕨（原生象）」的照顧難度為「容易」→ 1"),
    ("alcicorne", "mo-alcicorne", "min_temp", 15, "保持 15 度以上", "保持 15 度以上的環境溫度", "summary", ""),
    ("alcicorne", "mo-alcicorne", "water", 1, "耐旱，介質全乾再澆透", "圓盾鹿角蕨是耐旱的鹿角蕨品種，可以等到介質全乾再一次澆透。", "summary", ""),
    ("bifurcatum", "ncsu-bifurcatum", "light", 3, "散射光至半遮蔭", "It takes dappled sunlight to partial shade.", "summary", ""),
    ("bifurcatum", "ncsu-bifurcatum", "water", 3, "根部略乾再澆，不可全乾",
     "Water its crown regularly, allowing the roots to dry slightly between waterings but never letting them dry out completely.", "summary", ""),
    ("bifurcatum", "ncsu-bifurcatum", "min_temp", F(30), "可在 USDA Zone 10 戶外栽培", "can be grown outside in Zone 10", "reference", TOL + "；Zone 10 最低溫 30–40 °F，取 30 °F"),
    ("grande", HP, "origin", "菲律賓民答那峨（1908 年另有一份標本記為提勞島）", "原產地（更正）",
     "We believe that P. grande never occurred in Luzon. ... it is evident that any surviving wild plants are now confined to Mindanao.", "summary",
     "更正專著：呂宋與宿霧為誤記；其餘標本除 1908 年一份記為提勞島外都來自民答那峨"),
]:
    c(sp, src, f, v, lab, claim, q, "pp. 65–66" if src == HP else "", use=use)
# the summary averages rows, so one publisher counts once: where 微體溫室's per-species article covers a field,
# its 40-species table row for that field is excluded (as with veitchii's 銀鹿 page above)
MO_ARTICLE = {(x[0], x[2]) for x in C if x[1] in ("mo-giant", "mo-elephant", "mo-alcicorne") and x[5] == "summary"}
C[:] = [x[:5] + ("excluded", "微體溫室的專文已有此欄說法，同一出版者只計一次", x[7], x[8]) if x[1] == "mo-guide" and (x[0], x[2]) in MO_ARTICLE else x
        for x in C]


# ---------------------------------------------------------------- desc / note: every sentence carries a citation (guideline §4 文字欄)
E = "ufifas-enh36"
DESC = {
 "bifurcatum": [("栽培最普遍、也最容易種的鹿角蕨。", E, "The most common species in cultivation and also the easiest to grow.", "p. 2"),
                ("會大量長出側芽，最後長成很大的群體。", E, "Produces large numbers of \"pups,\" eventually forming a very large plant.", "p. 2"),
                ("與同種的其他亞種很容易互相雜交，產生可孕的後代。", M, "all taxa easily hybridize with each other producing fertile offspring", "p. 89")],
 "veitchii": [("孢子葉直立，呈銀白色。", E, "A common and easy-to-grow species with erect, silvery foliar fronds.", "p. 2"),
              ("光線不足時，孢子葉較不直立、白毛也較少。", "halling-veitchii", "If the light is less, the fertile fronds are less erect, have fewer hairs", ""),
              ("具有捲葉、厚白毛、CAM 光合作用等一系列耐旱機制。", "atf-veitchii", "This taxon expresses a suite of drought tolerating mechanisms including leaf rolling, sunken stomata, a thick indument of reflective insulating hairs and CAM photosynthesis.", "")],
 "hillii": [("孢子葉直立、深綠色，末端裂片寬 1–6 cm。", "atf-hillii", "ultimate segments oblong, 1–6 cm wide, dark green", ""),
            ("盾葉上緣不分裂，緊貼附著物，把巢的上方封住。", "atf-hillii", "The upper margin of the nest-fronds are not lobed and seal the upper surface of the nest.", ""),
            ("園藝上有多個品系。", E, "Several varieties are available.", "p. 2")],
 "superbum": [("盾葉形成大型籃狀，承接雨水與落葉並導向根部。", "atf-superbum", "The nest fronds of this species form a large basket that catches rain and falling debris and funnels it into the root system.", ""),
              ("每片孢子葉只有一個孢子囊群，可藉此與有兩個孢子囊群的 P. grande 區分。", M, "Foliage fronds with 1 soral patch", "p. 77")],
 "wandae": [("可能是體型最大的鹿角蕨。", E, "Possibly largest Platycerium.", "p. 3"),
            ("芽點旁的盾葉有小皺褶，是與外形相近的 P. holttumii 區分的特徵。", "halling-holttumii", "The lack of little frills on the shields at the bud differentiate the P. holttumii from P. wandae", "")],
 "willinckii": [("孢子葉下垂，密被星狀毛。", M, "Foliage fronds ± pendulous ... densely set with hairs", "p. 92"),
                ("容易栽培，沒有特別的問題。", "halling-willinckii", "This platy is easy to grow and offers no specific problems.", "")],
 "coronarium": [("孢子囊群長在獨立、有柄的殼狀或腎形裂片上，其餘孢子葉長而下垂。", M, "central lobe, fertile, horizontally exposed, either shell-shaped, or kidney-shaped", "p. 94"),
                ("在原產地相當常見，也常栽培作觀賞。", M, "It is locally very common, also as an ornamental plant.", "p. 95")],
 "ridleyi": [("孢子葉直立，與孢子葉下垂的 P. coronarium 很容易區分。", M, "position of the foliage fronds (pendulous in P. coronarium, erect in P. ridleyi)", "p. 95"),
             ("在低濕度地區不易栽培。", "halling-ridleyi", "difficult to grow in low humidity regions", "")],
 "holttumii": [("每片孢子葉有一小一大兩個孢子囊群，小的位置較高。", "halling-holttumii", "One is smaller and elevated while the second is larger", ""),
               ("外形與 P. wandae 相近，芽點旁沒有小皺褶。", "halling-holttumii", "The plant looks a lot like a P. wandae only there are no frills around the bud.", "")],
 "wallichii": [("原生於乾濕季分明的季風林。", "halling-giants", "monsoon forests with definite wet and dry seasons", ""),
               ("栽培中常進入休眠後就不再恢復。", "halling-giants", "more often it goes into dormancy and never comes out.", "")],
 "grande": [("只分布於菲律賓。", M, "Philippines (Luzon (?), Ticao, Cebu, Mindanao)", "p. 101"),
            ("孢子葉左右對稱，由兩個相等的半邊組成，各有一個孢子囊群。", M, "Foliage fronds with 2 soral patches ... Foliage fronds symmetrical, consisting of 2 equal halves", "p. 77")],
 "stemaria": [("孢子葉寬，上表面常有光澤，下表面多毛。", "halling-stemaria", "The wide fertile fronds are often shiny on the upper surface, and quite hairy on the underneath.", ""),
              ("在加州的栽培紀錄中，成熟植株每年長出 3–5 對孢子葉。", HP, "Mature plants of P. elephantotis usually produce one pair per year, P. stemaria 3—5 pairs", "p. 64")],
 "elephantotis": [("孢子葉不分裂、先端寬圓。", M, "Foliage fronds entire with a broadly rounded apex", "p. 77"),
                  ("生長有明顯季節性：春季舊盾葉枯死，夏季長出新盾葉。", "halling-elephantotis", "During the spring, last years shield fronds die and new ones form during the summer.", ""),
                  ("在加州的栽培紀錄中，成熟植株通常每年只長出一對孢子葉。", HP, "Mature plants of P. elephantotis usually produce one pair per year", "p. 64")],
 "alcicorne": [("外形與 P. bifurcatum 相近，早期常被混淆。", M, "shows much resemblance to P. bifurcatum with which it has been confused especially by the early authors", "p. 82"),
               ("非洲型黃綠色、有蠟質、幾乎無毛；馬達加斯加型深綠、多毛。", "halling-alcicorne", "The African platy is yellow-green in color, waxy with nearly no hairs.", "")],
 "madagascariense": [("盾葉葉脈隆起成鬆餅狀格紋，成熟後轉為深綠。", M, "Mature base fronds dark green ... veins raised forming a waffle pattern", "p. 77"),
                     ("需要雨水、蒸餾水或 RO 水等低溶解物的水。", "exotica-madagascariense", "High quality water, with low TDS (i.e. rain, distilled, RO/RODI, etc.) is required to succeed with this species.", "")],
 "quadridichotomum": [("原生地有長達半年的乾季，乾季時孢子葉縱向內捲。", M, "During the long dry season the plants have longitudinally recurved (involuted) foliage fronds", "p. 107")],
 "ellisii": [("孢子葉楔形至倒卵形，不分裂或只裂一次。", M, "wedge-shaped to obovate, 30-60 cm long, entire or one time lobed", "p. 98"),
             ("盾葉與 P. alcicorne 基本相似。", M, "The base fronds of the present species are basically similar to those found in P. ellisii", "p. 82")],
 "andinum": [("美洲唯一的鹿角蕨。", E, "Only Platycerium native to South America", "p. 3"),
             ("葉片密被銀白毛。", E, "Fronds covered with dense silvery hairs.", "p. 3"),
             ("群落可大到壓斷附生的大樹枝。", M, "Clusters of plants of P. andinum may become so voluminous and heavy that they cause the break-down of the big branches", "p. 84")],
}
NOTE = {"hillii": ("Hennipman & Roos 1982 將本種處理為 P. bifurcatum ssp. bifurcatum var. hillii。", "3.a.2. var. hillii. (T. Moore) Domin.", "p. 91"),
        "veitchii": ("Hennipman & Roos 1982 將本種處理為 P. bifurcatum ssp. veitchii。", "3.b. ssp. veitchii. (Underwood) Hennipman & Roos, stat.nov.", "p. 91"),
        "willinckii": ("Hennipman & Roos 1982 將本種處理為 P. bifurcatum ssp. willinckii。", "3.c. ssp. willinckii. (T. Moore) Hennipman & Roos, stat. nov.", "p. 92"),
        "grande": ("Hoshizaki & Price 1990 指出低地龍腦香林持續砍伐，野生族群已少到若非已有栽培族群將瀕臨滅絕。",
                   "the natural populations of P. grande have diminished to the point where extinction would be imminent if not for the fact that the species has been established in cultivation.", "p. 66"),
        "coronarium": ("Hoshizaki & Price 1990 將 P. platylobum 併入本種，認為那只是孢子葉片變異的個體。",
                       "We therefore synonymize P. platylobum under P. coronarium.", "p. 68")}
NOTE_SRC = {"grande": HP, "coronarium": HP}
for sp, sents in DESC.items():
    for s, src, q, p in sents:
        c(sp, src, "desc", "", s, s, q, p)
for sp, (s, q, p) in NOTE.items():
    c(sp, NOTE_SRC.get(sp, M), "note", "", s, s, q, p)


meta = {}


# ---------------------------------------------------------------- write
sh, srows = rw(os.path.join(ROOT, "data/sources.csv"))
srows = [dict(zip(sh, r)) for r in srows]
byid = {r["id"]: r for r in srows}
for s in NEW_SOURCES:
    rec = dict(id=s[0], title=s[1], publisher=s[2], url=s[3], type=s[4], lang=s[5], published=s[6], accessed="2026-10-15" if s[0] in ARCHIVE else ACCESSED,
               reliability=s[7], note=s[8], tier=s[9], region=s[10], short=s[11])
    if s[0] in byid:
        byid[s[0]].update(rec)
    else:
        srows.append(rec)
        byid[s[0]] = rec
    byid[s[0]]["archive_url"] = byid[s[0]].get("archive_url") or ARCHIVE.get(s[0], "")
for r in srows:
    if not r.get("tier"):
        for pre, tier, region, short in BACKFILL:
            if r["id"].startswith(pre):
                r.update(tier=tier, region=region, short=short)
                break
write(os.path.join(ROOT, "data/sources.csv"), SH, [[r.get(k, "") for k in SH] for r in srows])
meta.update(source_meta(srows))
for x in C:
    assert x[1] in meta, x[1]

ch, crows = rw(os.path.join(ROOT, "data/citations.csv"))
crows = [dict(zip(ch, r)) for r in crows]
for r in crows:
    r.setdefault("label", "")
    r["use"] = r.get("use") or "summary"
# replace this survey's rows in place; other plants' rows are left untouched
crows = replace_rows(crows, [dict(zip(CH, x)) for x in C], lambda r: r["plant_id"] in SPECIES and r["field"] in FIELDS + ["desc", "note"])
write(os.path.join(ROOT, "data/citations.csv"), CH, [[r.get(k, "") for k in CH] for r in crows])

by = defaultdict(list)
for x in C:
    by[(x[0], x[2])].append(x)
summary, detail = feature_rows(SPECIES, by, meta)

write(os.path.join(ROOT, "project_plan/survey/species_v3.csv"), ["id"] + FIELDS, [[sp] + [summary[sp].get(f, "") for f in FIELDS] for sp in SPECIES])
# features.csv / search_log.csv: replace only the 18 species' rows (hybrid and cultivar rows come from survey_hybrids.py)
FP = os.path.join(ROOT, "data/features.csv")
_, frows = rw(FP) if os.path.exists(FP) else (FH, [])
write(FP, FH, replace_rows(frows, [[str(x) for x in d] for d in detail], lambda r: r[0] in SPECIES))

# ---------------------------------------------------------------- search log (guideline §6)
S_MORPH = ("Hennipman & Roos 1982 pp. 77–117（種描述與檢索表）|Australian Tropical Ferns（bifurcatum、hillii、veitchii、superbum）|PlantNET NSW Flora"
           "|Halling 各種頁面|UF/IFAS ENH36|Hoshizaki & Price 1990")
S_CARE = ("UF/IFAS ENH36|Halling 各種頁面與巨型種比較表|NParks Flora & Fauna Web（搜尋其他種無結果）|RHS Plants（bifurcatum、veitchii、superbum、ridleyi、wandae、ellisii、elephantotis）"
          "|微體溫室〈40 種鹿角蕨〉|晴花鹿苑〈照養注意事項〉|Exotica Esoterica（madagascariense）"
          "|微體溫室〈巨獸與巨大〉〈象耳 8 品種〉〈圓盾 10 品種〉|NC State Extension（bifurcatum）")
S_TEMP = S_CARE + "|搜尋：鹿角蕨 原生種 耐寒 最低溫度|搜尋：Platycerium species care temperature minimum|搜尋：鹿角蕨 碩士論文 溫度 光度"
SEARCHED = {f: S_MORPH for f in FIELDS}
SEARCHED.update({f: S_CARE for f in CULT}, min_temp=S_TEMP, max_temp=S_TEMP)
SEARCHED["dormancy"] = S_CARE + "|Hennipman & Roos 1982 棲地與附註"
SEARCHED["pups"] = S_MORPH + "|Ciarle et al. 2025 補充資料 S1"
log = []
for sp in SPECIES:
    for f in FIELDS:
        if f == "size_note" or summary[sp].get(f):
            continue
        partial = any(r[5] != "summary" for r in by.get((sp, f), []))
        log.append([sp, f, VERSION, ACCESSED, SEARCHED[f], "partial" if partial else "not_found"])
LP = os.path.join(ROOT, "project_plan/survey/search_log.csv")
_, lrows = rw(LP) if os.path.exists(LP) else (LH, [])
write(LP, LH, replace_rows(lrows, log, lambda r: r[0] in SPECIES))

# ---------------------------------------------------------------- migrate data/plants.csv (guideline §4 table)
def labels(sp, f):
    return "／".join(d[5] for d in detail if d[0] == sp and d[1] == f)


def plant_text(sp):
    return _plant_text(summary[sp], lambda f: labels(sp, f))


ph, prows = rw(os.path.join(ROOT, "data/plants.csv"))
prows = [dict(zip(ph, r)) for r in prows]
if "shield_color" in ph:  # one-time column migration
    ph = [c for c in ph if c != "fertile_color"]
    i = ph.index("shield_color")
    ph[i:i + 1] = ["shield_browning", "shield_fringe"]
    for r in prows:
        # draft free text in columns whose vocabulary changed moves to the shield / fertile descriptions
        for col, txt, pre in [("shield_form", "shield", "冠形："), ("shield_color", "shield", "顏色："), ("spore", "fertile", "孢子囊群："), ("fertile_color", "fertile", "顏色：")]:
            v = r.pop(col, "") if col in ("shield_color", "fertile_color") else r.get(col, "")
            if v and v not in r.get(txt, ""):
                r[txt] = (r.get(txt, "") + pre + v + "。").strip()
        r["shield_form"] = r["spore"] = ""
        r["shield_vein"] = ""  # old 1–5 draft scores cannot be read as yes/no without a source
        r["shield_browning"] = r["shield_fringe"] = ""
urls = {s["id"]: s["url"] for s in srows}
for r in prows:
    sp = r["id"]
    if sp not in SPECIES:
        continue
    for f in FIELDS:
        r[f] = summary[sp].get(f, "")
    r.update(plant_text(sp))
    used = []
    for x in C:
        if x[0] == sp and x[5] != "excluded" and urls.get(x[1]) and urls[x[1]] not in used:
            used.append(urls[x[1]])
    r["refs"] = "|".join(used)
    # desc / note keep only cited sentences
    r["desc"] = "".join(s for s, *_ in DESC.get(sp, []))
    r["note"] = NOTE[sp][0] if sp in NOTE else ""
    r["survey_version"] = VERSION
write(os.path.join(ROOT, "data/plants.csv"), ph, [[r.get(k, "") for k in ph] for r in prows])

print({f: sum(1 for sp in SPECIES if summary[sp].get(f)) for f in FIELDS})
print("citations", len(C), {u: sum(1 for x in C if x[5] == u) for u in ("summary", "reference", "excluded")})
flush(sys.argv[2:])
