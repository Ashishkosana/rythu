"""My-Field crop calendar: from the one date a farmer knows — sowing or transplanting — to dated tasks.

Content rule: every task restates a line of ``docs/agronomy-data.md`` (official PJTSAU / TNAU / ICAR /
NIPHM sources), carries that source, and keeps its ``needs_verification`` flag, so the app shows the
"confirm with your AEO / Soil Health Card" fallback exactly where the research says it must. Where the
sources give a crop STAGE but no day count (red gram "at flowering"), the task stays stage-based —
a made-up date would be worse than none. Fertilizer tasks name the share of the dose, never a brand;
pest tasks are scouting reminders (thresholds first, sprays only with the AEO), never sprays.

Pure: no clock, no I/O. ``plan`` takes the reference date and returns dated tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from rythu_weather.domain.models import Crop


class Reference(StrEnum):
    SOWING = "sowing"
    TRANSPLANTING = "transplanting"


class TaskKind(StrEnum):
    PREPARE = "prepare"
    FERTILIZER = "fertilizer"
    WEEDS = "weeds"
    SCOUT = "scout"


@dataclass(frozen=True, slots=True)
class TaskSpec:
    id: str
    kind: TaskKind
    start_day: int | None  # days after the reference date; None = stage-based (no reliable day count)
    end_day: int | None  # inclusive; None with a start = "from then on"
    title_te: str
    title_en: str
    detail_te: str
    detail_en: str
    source: str
    needs_verification: bool
    stage_te: str = ""  # for stage-based tasks: when to do it
    stage_en: str = ""


@dataclass(frozen=True, slots=True)
class CropCalendar:
    reference: Reference
    tasks: tuple[TaskSpec, ...]


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    spec: TaskSpec
    start: date | None
    end: date | None


_PADDY = "https://www.pjtau.edu.in/files/publications/2023/Journal-of-Research-PJTSAU-50-4.pdf"
_PADDY_BPH = "https://agritech.tnau.ac.in/crop_protection/rice/crop_prot_crop_insectpest%20_cereals_paddy_12.html"
_COTTON = "https://tnaucottondatabase.wordpress.com/wp-content/uploads/2012/03/ap.pdf"
_COTTON_PBW = "https://niphm.gov.in/IPMPackages/Cotton.pdf"
_MAIZE = "https://tnagriculture.in/dashboard/CPG/02_%20Maize.pdf"
_MAIZE_FAW = (
    "https://agriculture.vikaspedia.in/viewcontent/agriculture/crop-production/integrated-pest-managment/"
    "ipm-for-cerels/identification-and-management-of-fall-armyworm"
)
_RED_GRAM = "https://icar.org.in/sites/default/files/Circulars/ICAR-En-Kharif-Agro-Advisories-for-Farmers-2025.pdf"
_RED_GRAM_PB = "https://niphm.gov.in/IPMPackages/Redgram.pdf"
_CHILLI = "https://agritech.tnau.ac.in/horticulture/horti_vegetables_chilli_Manuring.html"
_CHILLI_PESTS = "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect-veg_chillies_pest&disease.html"


def _split(crop: str, n: int, day: int, te: str, en: str, detail_te: str, detail_en: str,
           source: str, verify: bool) -> TaskSpec:
    return TaskSpec(f"{crop}.split{n}", TaskKind.FERTILIZER, day, day, te, en, detail_te, detail_en, source, verify)


CALENDARS: dict[Crop, CropCalendar] = {
    Crop.PADDY: CropCalendar(Reference.TRANSPLANTING, (
        TaskSpec(
            "paddy.basal", TaskKind.FERTILIZER, 0, 0,
            "దుక్కిలో ఎరువు (basal)", "Basal fertilizer",
            "చివరి దమ్ములో P, K మొత్తం + N లో మూడో వంతు మట్టిలో కలపండి. 15 రోజుల తర్వాత P/కాంప్లెక్స్ పైపాటు వద్దు.",
            "At final puddling: all the P and K plus one third of the N, mixed into the soil. No P/complex "
            "top-dressing after about 15 days.",
            _PADDY, False,
        ),
        TaskSpec(
            "paddy.weeds", TaskKind.WEEDS, 0, 40,
            "కలుపు నివారణ", "Keep weeds out",
            "నాట్లు వేసిన మొదటి 40 రోజులు కలుపు నివారణకు చాలా ముఖ్యం.",
            "The first 40 days after transplanting matter most for weed control.",
            "https://pjtsau.edu.in", False,
        ),
        _split("paddy", 2, 25, "రెండో N మోతాదు — పిలకల దశ", "Second N dose — tillering",
               "N లో మూడో వంతు, నాట్లు వేసిన 25–30 రోజులకు.", "One third of the N, 25–30 days after transplanting.",
               _PADDY, False),
        TaskSpec(
            "paddy.bph", TaskKind.SCOUT, 25, None,
            "సుడి దోమ కోసం చూడండి", "Check for brown planthopper",
            "పిలకల దశ నుండి, నీటి పైన మొక్క మొదళ్లలో చూడండి. సాలీడు లేకపోతే పిలకకు 1 దోమ, ఉంటే 2 — అప్పుడే చర్య.",
            "From tillering on, look at the plant base just above the water. Act only at 1 hopper per tiller "
            "(2 if spiders are present). Neem first; avoid early pyrethroids.",
            _PADDY_BPH, False,
        ),
        _split("paddy", 3, 55, "మూడో N మోతాదు — కంకి దశ", "Third N dose — panicle initiation",
               "N లో మూడో వంతు, 55–60 రోజులకు. తేలిక నేలల్లో సగం K కూడా ఇప్పుడే.",
               "The last third of the N, 55–60 days after transplanting. On light soils, half the K now too.",
               _PADDY, False),
    )),
    Crop.COTTON: CropCalendar(Reference.SOWING, (
        TaskSpec(
            "cotton.basal", TaskKind.FERTILIZER, 0, 0,
            "దుక్కిలో ఎరువు (basal)", "Basal fertilizer",
            "విత్తేటప్పుడు P మొత్తం దుక్కిలో.", "All the P at sowing.",
            _COTTON, True,
        ),
        _split("cotton", 1, 30, "N, K మొదటి భాగం", "N + K, first third",
               "విత్తిన 30 రోజులకు N, K లో మూడో వంతు — మొక్కకు 7–10 సెం.మీ. దూరంలో.",
               "30 days after sowing: one third of the N and K, placed 7–10 cm from the plant.", _COTTON, True),
        TaskSpec(
            "cotton.pbw.traps", TaskKind.SCOUT, 45, 45,
            "గులాబీ కాయతొలుచు పురుగు — ఎర బుట్టలు", "Pink bollworm — pheromone traps",
            "విత్తిన 45 రోజులకు ఎకరానికి 5 లింగాకర్షక బుట్టలు పెట్టండి.",
            "45 days after sowing, set up 5 pheromone traps per acre.",
            _COTTON_PBW, True,
        ),
        _split("cotton", 2, 60, "N, K రెండో భాగం", "N + K, second third",
               "విత్తిన 60 రోజులకు N, K లో మూడో వంతు.", "60 days after sowing: one third of the N and K.",
               _COTTON, True),
        _split("cotton", 3, 90, "N, K మూడో భాగం", "N + K, last third",
               "విత్తిన 90 రోజులకు మిగతా N, K.", "90 days after sowing: the last third of the N and K.",
               _COTTON, True),
        *(
            TaskSpec(
                f"cotton.pbw.check{d}", TaskKind.SCOUT, d, d,
                "గులాబీ కాయతొలుచు పురుగు — తనిఖీ", "Pink bollworm — check",
                "బుట్టలు, పూలు, పచ్చి కాయలు చూడండి. 3 రాత్రులు వరుసగా బుట్టకు 8 పురుగులు లేదా 10% నష్టం ఉంటేనే చర్య.",
                "Check traps, flowers and green bolls. Act only at 8 moths per trap per night for 3 nights, "
                "or 10% damaged rosette flowers or bolls.",
                _COTTON_PBW, True,
            )
            for d in (90, 105, 120, 135, 150)
        ),
    )),
    Crop.MAIZE: CropCalendar(Reference.SOWING, (
        TaskSpec(
            "maize.basal", TaskKind.FERTILIZER, 0, 0,
            "దుక్కిలో ఎరువు (basal)", "Basal fertilizer",
            "విత్తే ముందు P, K మొత్తం + N లో పావు వంతు.", "Before sowing: all the P and K plus a quarter of the N.",
            _MAIZE, True,
        ),
        TaskSpec(
            "maize.faw", TaskKind.SCOUT, 0, None,
            "కత్తెర పురుగు కోసం చూడండి", "Check for fall armyworm",
            "ప్రతి వారం W ఆకారంలో 20 మొక్కలు చూడండి. 5–10% సుడుల్లో నష్టం ఉంటేనే చర్య. సుడి మధ్య దశ తర్వాత మందులు వద్దు.",
            "Every week, check 20 plants walking a W. Act only at 5–10% whorl damage. No chemicals after the "
            "mid-whorl stage.",
            _MAIZE_FAW, True,
        ),
        _split("maize", 2, 25, "N రెండో మోతాదు — మోకాలి ఎత్తు", "N — knee-high",
               "మోకాలి ఎత్తులో (~25 రోజులు) N లో సగం.", "At knee height (about 25 days): half of the N.",
               _MAIZE, True),
        _split("maize", 3, 45, "N చివరి మోతాదు", "N — last quarter",
               "సుమారు 45 రోజులకు మిగతా పావు వంతు N.", "About 45 days after sowing: the last quarter of the N.",
               _MAIZE, True),
    )),
    Crop.RED_GRAM: CropCalendar(Reference.SOWING, (
        TaskSpec(
            "red_gram.seed", TaskKind.PREPARE, 0, 0,
            "విత్తన శుద్ధి", "Seed treatment",
            "విత్తే ముందు విత్తనానికి రైజోబియం + PSB పట్టించండి.", "Before sowing, treat the seed with Rhizobium + PSB.",
            _RED_GRAM, True,
        ),
        TaskSpec(
            "red_gram.basal", TaskKind.FERTILIZER, 0, 0,
            "దుక్కిలో ఎరువు (basal)", "Basal fertilizer",
            "మొత్తం మోతాదు విత్తేటప్పుడే. ఖరీఫ్‌లో పైపాటు అవసరం లేదు.",
            "The whole dose at sowing, placed. No top-dressing in kharif.",
            _RED_GRAM, True,
        ),
        TaskSpec(
            "red_gram.pod_borer", TaskKind.SCOUT, None, None,
            "కాయతొలుచు పురుగు — పూత దశ", "Pod borer — at flowering",
            "ఎకరానికి 4–5 లింగాకర్షక బుట్టలు, 8 పక్షి స్థావరాలు. మొక్కకు 2 గుడ్లు/పురుగులు ఉంటేనే చర్య.",
            "4–5 pheromone traps and about 8 bird perches per acre. Act only at 2 eggs or larvae per plant.",
            _RED_GRAM_PB, True,
            stage_te="పూత మొదలైనప్పుడు", stage_en="When flowering starts",
        ),
    )),
    Crop.CHILLI: CropCalendar(Reference.TRANSPLANTING, (
        TaskSpec(
            "chilli.basal", TaskKind.FERTILIZER, 0, 0,
            "దుక్కిలో ఎరువు (basal)", "Basal fertilizer",
            "నాట్ల సమయంలో పశువుల ఎరువు + P, K మొత్తం + సగం N. K ను పొటాషియం సల్ఫేట్‌గా వేయండి.",
            "At transplanting: farmyard manure, all the P and K and half the N. Give the K as potassium sulphate.",
            _CHILLI, True,
        ),
        TaskSpec(
            "chilli.sucking_pests", TaskKind.SCOUT, 0, None,
            "తామర పురుగు, నల్లి కోసం చూడండి", "Check for thrips and mites",
            "ప్రతి వారం ఆకులు చూడండి — ఇవి ఆకుముడత వైరస్ వ్యాపింపజేస్తాయి. మందు ముందు AEO ని అడగండి.",
            "Check the leaves every week — thrips and mites spread leaf-curl virus. Ask your AEO before any spray.",
            _CHILLI_PESTS, True,
        ),
        *(
            _split("chilli", n, d, f"N పైపాటు — {d} రోజులు", f"N top-dressing — day {d}",
                   "మిగతా N లో మూడో వంతు.", "One third of the remaining N.", _CHILLI, True)
            for n, d in ((1, 30), (2, 60), (3, 90))
        ),
    )),
}


def plan(crop: Crop, reference_date: date) -> list[ScheduledTask]:
    """The crop's tasks dated from ``reference_date``: by start day, stage-based tasks last."""
    tasks = [
        ScheduledTask(
            t,
            None if t.start_day is None else reference_date + timedelta(days=t.start_day),
            None if t.end_day is None else reference_date + timedelta(days=t.end_day),
        )
        for t in CALENDARS[crop].tasks
    ]
    return sorted(tasks, key=lambda s: (s.start is None, s.start or reference_date, s.spec.id))
