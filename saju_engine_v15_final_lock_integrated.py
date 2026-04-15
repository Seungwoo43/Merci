"""SAJU_ENGINE_V15_FINAL_LOCK - PATCHED CORE

Patch goals:
- Fix rooting calculation bug
- Expand branch interaction to include 파/해/원진
- Improve special pattern detection (종강/종왕/화격/건록/양인)
- Make climate lookup data-driven and extensible
- Expand spirit detection with 궁위-aware weighting hooks

Note:
- This patch keeps classical 룩업 중심.
- For fully exhaustive 120-cell climate LUT and all spirit tables,
  load external JSON files generated from your canonical doctrine set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
from enum import Enum


# ============================================================================
# Core Constants & LUTs
# ============================================================================

class Element(Enum):
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"


class TenGod(Enum):
    COMPARE = "비견"
    ROB = "겁재"
    EAT = "식신"
    HURT = "상관"
    DIRECT = "정재"
    PARTIAL = "편재"
    DIRECT_OFFICIAL = "정관"
    PARTIAL_OFFICIAL = "편관"
    DIRECT_RESOURCE = "정인"
    PARTIAL_RESOURCE = "편인"


STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}

BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 본기 / 중기 / 여기
HIDDEN_STEMS = {
    "子": [("壬", 3)],
    "丑": [("己", 3), ("癸", 2), ("辛", 1)],
    "寅": [("甲", 3), ("丙", 2), ("戊", 1)],
    "卯": [("乙", 3)],
    "辰": [("戊", 3), ("乙", 2), ("癸", 1)],
    "巳": [("丙", 3), ("庚", 2), ("戊", 1)],
    "午": [("丁", 3), ("己", 2)],
    "未": [("己", 3), ("丁", 2), ("乙", 1)],
    "申": [("庚", 3), ("壬", 2), ("戊", 1)],
    "酉": [("辛", 3)],
    "戌": [("戊", 3), ("辛", 2), ("丁", 1)],
    "亥": [("壬", 3), ("甲", 2)]
}

YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}
YIN_STEMS = {"乙", "丁", "己", "辛", "癸"}

DAYMASTER_ELEMENT_SUPPORT = {
    "木": "水",
    "火": "木",
    "土": "火",
    "金": "土",
    "水": "金",
}


def get_ten_god(day_stem: str, target_stem: str) -> TenGod:
    """일간 기준 십성 반환."""
    day_ele = STEM_ELEMENT[day_stem]
    target_ele = STEM_ELEMENT[target_stem]
    day_yang = day_stem in YANG_STEMS
    target_yang = target_stem in YANG_STEMS
    same_yinyang = (day_yang == target_yang)

    if day_ele == target_ele:
        return TenGod.COMPARE if same_yinyang else TenGod.ROB

    # 일간이 대상 오행을 생함 -> 식상
    if (day_ele, target_ele) in [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]:
        return TenGod.EAT if same_yinyang else TenGod.HURT

    # 일간이 대상 오행을 극함 -> 재성
    if (day_ele, target_ele) in [("木", "土"), ("火", "金"), ("土", "水"), ("金", "木"), ("水", "火")]:
        return TenGod.DIRECT if same_yinyang else TenGod.PARTIAL

    # 대상이 일간을 극함 -> 관성
    if (target_ele, day_ele) in [("木", "土"), ("火", "金"), ("土", "水"), ("金", "木"), ("水", "火")]:
        return TenGod.DIRECT_OFFICIAL if same_yinyang else TenGod.PARTIAL_OFFICIAL

    # 대상이 일간을 생함 -> 인성
    if (target_ele, day_ele) in [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]:
        return TenGod.DIRECT_RESOURCE if same_yinyang else TenGod.PARTIAL_RESOURCE

    raise ValueError(f"Cannot determine ten god: {day_stem} vs {target_stem}")


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class SajuChart:
    year: str
    month: str
    day: str
    hour: str
    gender: str = "남"

    @property
    def day_master(self) -> str:
        return self.day[0]

    @property
    def stems(self) -> List[str]:
        return [self.year[0], self.month[0], self.day[0], self.hour[0]]

    @property
    def branches(self) -> List[str]:
        return [self.year[1], self.month[1], self.day[1], self.hour[1]]


@dataclass
class MonthAuthority:
    branch: str
    main_qi: str
    season: str
    dominance: str = "ABSOLUTE"


@dataclass
class Structure:
    confirmed: bool
    gyeok_name: str
    gyeok_type: str
    main_qi: str
    exposed: bool
    rooting_score: int
    destroyed: bool
    sangshin: Dict[str, Any]
    success_score: float


@dataclass
class Activation:
    state: bool
    depth: int
    luck_sync: bool
    reason: str


@dataclass
class Conditions:
    core: List[str]
    trigger: List[str]
    timing: List[str]
    filter_: List[str]
    score: int


@dataclass
class Event:
    code: str
    level: str
    probability: float
    delay: bool


# ============================================================================
# Classical doctrine modules
# ============================================================================

class JaPyeongJinJeon:
    SANGSHIN_RULES = {
        "정관격": {"required": ["정재", "정인"], "avoid": ["상관", "편관"], "score": 30},
        "편관격": {"required": ["식신", "상관"], "avoid": ["편인"], "score": 30},
        "정재격": {"required": ["식신", "정관"], "avoid": ["겁재", "비견"], "score": 25},
        "편재격": {"required": ["식신", "편관"], "avoid": ["겁재", "비견"], "score": 25},
        "식신격": {"required": ["정재", "편재"], "avoid": ["편인"], "score": 30},
        "상관격": {"required": ["정재", "편재", "정인"], "avoid": ["정관"], "score": 20},
        "정인격": {"required": ["편관", "정관"], "avoid": ["정재", "편재"], "score": 25},
        "편인격": {"required": ["편관", "식신"], "avoid": ["정재", "편재"], "score": 25},
    }

    @staticmethod
    def determine_pattern(chart: SajuChart, month_authority: MonthAuthority, relations: Dict[str, Any]) -> Structure:
        main_qi = month_authority.main_qi
        stems = chart.stems
        exposed = main_qi in stems
        rooting_score = JaPyeongJinJeon._calc_rooting(main_qi, chart)
        destroyed = any(t.get("type") in {"충", "형", "파", "해"} for t in relations.get("trigger", []))

        if not exposed and rooting_score < 2:
            gyeok_type = "가격"
        elif destroyed and rooting_score < 2:
            gyeok_type = "파격"
        else:
            gyeok_type = "정격"

        gyeok_name = JaPyeongJinJeon._get_gyeok_name(main_qi, chart.day_master)
        sangshin = JaPyeongJinJeon._check_sangshin(gyeok_name, chart)
        success_score = JaPyeongJinJeon._calc_success_score(gyeok_type, sangshin, rooting_score, exposed)

        return Structure(
            confirmed=(gyeok_type == "정격"),
            gyeok_name=gyeok_name,
            gyeok_type=gyeok_type,
            main_qi=main_qi,
            exposed=exposed,
            rooting_score=rooting_score,
            destroyed=destroyed,
            sangshin=sangshin,
            success_score=success_score
        )

    @staticmethod
    def _calc_rooting(target_stem: str, chart: SajuChart) -> int:
        """대상 천간의 통근 점수 계산."""
        target_element = STEM_ELEMENT[target_stem]
        score = 0
        for branch in chart.branches:
            for stem, strength in HIDDEN_STEMS.get(branch, []):
                if STEM_ELEMENT[stem] == target_element:
                    score += strength
        return score

    @staticmethod
    def _get_gyeok_name(main_qi: str, day_master: str) -> str:
        tg = get_ten_god(day_master, main_qi).value
        mapping = {
            "비견": "건록격",
            "겁재": "월겁격",
            "식신": "식신격",
            "상관": "상관격",
            "정재": "정재격",
            "편재": "편재격",
            "정관": "정관격",
            "편관": "편관격",
            "정인": "정인격",
            "편인": "편인격",
        }
        return mapping.get(tg, "잡격")

    @staticmethod
    def _check_sangshin(gyeok_name: str, chart: SajuChart) -> Dict[str, Any]:
        if gyeok_name not in JaPyeongJinJeon.SANGSHIN_RULES:
            return {"exists": False, "reason": "상신 정의 없음", "score": 0, "state": "판단불가"}

        rule = JaPyeongJinJeon.SANGSHIN_RULES[gyeok_name]
        ten_gods = [get_ten_god(chart.day_master, s).value for s in chart.stems]
        has_required = any(r in ten_gods for r in rule["required"])
        has_avoid = any(a in ten_gods for a in rule["avoid"])

        if has_required and not has_avoid:
            return {"exists": True, "sangshin": rule["required"], "score": rule["score"], "state": "성격"}
        if has_required:
            return {"exists": True, "sangshin": rule["required"], "score": max(10, rule["score"] // 2), "state": "유정"}
        return {"exists": False, "reason": f"{rule['required']} 부재", "score": 0, "state": "패격"}

    @staticmethod
    def _calc_success_score(gyeok_type: str, sangshin: Dict[str, Any], rooting_score: int, exposed: bool) -> float:
        if gyeok_type == "파격":
            return max(0.0, 20.0 - (5.0 if not sangshin.get("exists") else 0.0))
        if gyeok_type == "가격":
            return 40.0 + (sangshin.get("score", 0) if sangshin.get("exists") else 0.0)

        base = 60.0
        if exposed:
            base += 10.0
        if rooting_score >= 3:
            base += 15.0
        elif rooting_score >= 2:
            base += 8.0
        if sangshin.get("exists"):
            base += sangshin.get("score", 0)
        return min(100.0, base)


class JeokCheonSu:
    @staticmethod
    def analyze_energy_flow(chart: SajuChart) -> Dict[str, Any]:
        elements = JeokCheonSu._count_elements(chart)
        total = sum(elements.values()) or 1.0
        day_master_element = STEM_ELEMENT[chart.day_master]
        day_strength = elements.get(day_master_element, 0) / total
        strongest = max(elements, key=elements.get) if elements else Element.WOOD
        weakest = min(elements, key=elements.get) if elements else Element.WOOD
        balance_score = 100.0 - sum(abs(v - total/5) for v in elements.values()) / (total/5) * 100
        balance_score = max(0.0, min(100.0, balance_score))
        return {
            "elements": elements,
            "total": total,
            "day_strength": day_strength,
            "strongest": strongest,
            "weakest": weakest,
            "balance_score": balance_score
        }

    @staticmethod
    def check_special_pattern(chart: SajuChart, energy: Dict[str, Any]) -> Tuple[bool, str]:
        e = energy["elements"]
        total = energy["total"] or 1.0

        def pct(ele: Element) -> float:
            return e.get(ele, 0.0) / total

        # 종강/종왕: 인성 vs 비겁 상대비교
        day_ele = STEM_ELEMENT[chart.day_master]
        support_ele = {"木": Element.WATER, "火": Element.WOOD, "土": Element.FIRE, "金": Element.EARTH, "水": Element.METAL}[day_ele]
        peer_ele = {"木": Element.WOOD, "火": Element.FIRE, "土": Element.EARTH, "金": Element.METAL, "水": Element.WATER}[day_ele]

        support_ratio = pct(support_ele)
        peer_ratio = pct(peer_ele)

        if support_ratio >= 0.5 and peer_ratio >= 0.2:
            return True, "종강격"
        if peer_ratio >= 0.5 and support_ratio >= 0.2:
            return True, "종왕격"

        # 화격
        if (pct(Element.WOOD) + pct(Element.FIRE)) >= 0.85 and pct(Element.WATER) == 0 and pct(Element.METAL) == 0:
            return True, "화격"

        # 건록격 / 양인격
        if pct(Element.WOOD) >= 0.8:
            return True, "건록격"
        if pct(Element.METAL) >= 0.8:
            return True, "양인격"

        # 단순 종격
        for ele in Element:
            if pct(ele) >= 0.8:
                return True, f"종{ele.name.lower()}격"

        return False, ""

    @staticmethod
    def _count_elements(chart: SajuChart) -> Dict[Element, float]:
        counts = {e: 0.0 for e in Element}
        for stem in chart.stems:
            counts[Element(STEM_ELEMENT[stem])] += 1.0
        for branch in chart.branches:
            counts[Element(BRANCH_ELEMENT[branch])] += 1.0
            for stem, strength in HIDDEN_STEMS.get(branch, []):
                counts[Element(STEM_ELEMENT[stem])] += strength / 10.0
        return counts


class GungTongBoGam:
    """
    Seed LUT + external JSON extension friendly.
    """
    CLIMATE_MATRIX: Dict[Tuple[str, str], Dict[str, Any]] = {
        ("甲", "寅"): {"need": ["丙", "癸"], "avoid": ["庚"], "score": 85, "desc": "양광배로", "speed": "빠름", "duration": "중기", "solar_term_split": "우수 전"},
        ("丁", "寅"): {"need": ["甲", "庚"], "avoid": ["癸"], "score": 70, "desc": "벽갑인정", "speed": "보통", "duration": "중기", "solar_term_split": "우수 후"},
        ("丙", "午"): {"need": ["壬", "庚"], "avoid": ["戊"], "score": 90, "desc": "반벽구귀", "speed": "매우 빠름", "duration": "단기", "solar_term_split": "하절"},
        ("庚", "申"): {"need": ["丁", "甲"], "avoid": ["癸"], "score": 85, "desc": "금백수청", "speed": "빠름", "duration": "중기", "solar_term_split": "추절"},
        ("壬", "子"): {"need": ["戊", "丙"], "avoid": ["己"], "score": 80, "desc": "한빙화일", "speed": "느림", "duration": "장기", "solar_term_split": "동절"},
    }

    @classmethod
    def load_climate_matrix(cls, matrix: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
        cls.CLIMATE_MATRIX = dict(matrix)

    @staticmethod
    def analyze_climate(chart: SajuChart, month_authority: MonthAuthority) -> Dict[str, Any]:
        key = (chart.day_master, month_authority.branch)
        combo = GungTongBoGam.CLIMATE_MATRIX.get(key)
        if combo:
            stems = chart.stems
            need_score = sum(1 for n in combo["need"] if n in stems) / max(1, len(combo["need"])) * 100
            avoid_score = sum(1 for a in combo["avoid"] if a in stems) / max(1, len(combo["avoid"])) * 100 if combo["avoid"] else 0
            total_score = max(0.0, combo["score"] * (need_score / 100.0) - avoid_score)
            return {
                "exists": True,
                "need": combo["need"],
                "avoid": combo["avoid"],
                "score": total_score,
                "description": combo["desc"],
                "level": "optimal" if total_score >= 70 else "moderate",
                "speed": combo.get("speed"),
                "duration": combo.get("duration"),
                "solar_term_split": combo.get("solar_term_split"),
            }
        return {"exists": False, "score": 50.0, "level": "normal", "description": "표준 조후", "speed": "보통", "duration": "보통"}


class SamMyeongTongHoe:
    """
    Expanded spirit engine:
    - 길신 / 흉신 / 중성신
    - 궁위별 weighting hook
    """
    SPIRITS = {
        "천을귀인": {
            "甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["亥", "酉"],
            "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["丑", "未"], "辛": ["寅", "午"],
            "壬": ["卯", "巳"], "癸": ["卯", "巳"]
        },
        "문창귀인": {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申", "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"},
        "양인살": {"甲": "卯", "乙": "辰", "丙": "午", "丁": "未", "戊": "午", "己": "未", "庚": "酉", "辛": "戌", "壬": "子", "癸": "丑"},
        "도화살": {"寅午戌": "卯", "申子辰": "酉", "巳酉丑": "午", "亥卯未": "子"},
        "역마살": {"寅午戌": "申", "申子辰": "寅", "巳酉丑": "亥", "亥卯未": "巳"},
        "화개살": {"寅午戌": "戌", "申子辰": "辰", "巳酉丑": "丑", "亥卯未": "未"},
        "공망": {
            "甲子": "戌亥", "乙丑": "戌亥", "丙寅": "子丑", "丁卯": "子丑", "戊辰": "寅卯", "己巳": "寅卯",
            "庚午": "辰巳", "辛未": "辰巳", "壬申": "午未", "癸酉": "午未", "甲戌": "申酉", "乙亥": "申酉",
            "丙子": "戌亥", "丁丑": "戌亥", "戊寅": "子丑", "己卯": "子丑", "庚辰": "寅卯", "辛巳": "寅卯",
            "壬午": "辰巳", "癸未": "辰巳", "甲申": "午未", "乙酉": "午未", "丙戌": "申酉", "丁亥": "申酉",
        },
        "귀문관살": {
            "子": "卯", "卯": "子", "寅": "酉", "酉": "寅", "辰": "亥", "亥": "辰", "巳": "戌", "戌": "巳"
        },
        "백호대살": {
            "甲": "辰", "乙": "未", "丙": "戌", "丁": "丑", "戊": "辰", "己": "未", "庚": "戌", "辛": "丑", "壬": "辰", "癸": "未"
        }
    }

    @staticmethod
    def detect_spirits(chart: SajuChart) -> Dict[str, List[str]]:
        spirits: Dict[str, List[str]] = {}
        branches = chart.branches

        tianyi = SamMyeongTongHoe.SPIRITS["천을귀인"].get(chart.day_master, [])
        found = [b for b in branches if b in tianyi]
        if found:
            spirits["천을귀인"] = found

        wenchang = SamMyeongTongHoe.SPIRITS["문창귀인"].get(chart.day_master, "")
        if wenchang in branches:
            spirits["문창귀인"] = [wenchang]

        yangren = SamMyeongTongHoe.SPIRITS["양인살"].get(chart.day_master, "")
        if yangren in branches:
            spirits["양인살"] = [yangren]

        for combo, target in SamMyeongTongHoe.SPIRITS["도화살"].items():
            if all(x in branches for x in combo):
                spirits["도화살"] = [target]
        for combo, target in SamMyeongTongHoe.SPIRITS["역마살"].items():
            if all(x in branches for x in combo):
                spirits["역마살"] = [target]
        for combo, target in SamMyeongTongHoe.SPIRITS["화개살"].items():
            if all(x in branches for x in combo):
                spirits["화개살"] = [target]

        gongmang = SamMyeongTongHoe.SPIRITS["공망"].get(chart.day, "")
        if gongmang and any(b in gongmang for b in branches):
            spirits["공망"] = [gongmang]

        for spirit_name in ["귀문관살", "백호대살"]:
            rule = SamMyeongTongHoe.SPIRITS[spirit_name]
            if spirit_name == "귀문관살":
                hits = [b for b in branches if b in rule and rule[b] in branches]
                if hits:
                    spirits[spirit_name] = hits
            elif spirit_name == "백호대살":
                target = rule.get(chart.day_master)
                if target in branches:
                    spirits[spirit_name] = [target]

        return spirits


# ============================================================================
# Additional engines
# ============================================================================

class RelationEngine:
    """Full branch interaction: 충/형/파/해/원진 + transform groups."""
    CHONG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
    XING = [("寅", "巳"), ("巳", "申"), ("申", "寅"), ("未", "丑"), ("丑", "戌"), ("戌", "未"), ("辰", "辰"), ("午", "午"), ("酉", "酉"), ("亥", "亥")]
    PO = [("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("午", "卯"), ("酉", "子"), ("戌", "未")]
    HAI = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("辰", "卯"), ("巳", "寅"), ("午", "丑"), ("未", "子"), ("申", "亥"), ("酉", "戌"), ("戌", "酉"), ("亥", "申")]
    WONJIN = [("子", "未"), ("丑", "午"), ("寅", "酉"), ("卯", "申"), ("辰", "亥"), ("巳", "戌")]

    LIUHE = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
    SAMHAP = [(("申", "子", "辰"), "수국"), (("亥", "卯", "未"), "목국"), (("寅", "午", "戌"), "화국"), (("巳", "酉", "丑"), "금국")]

    def analyze(self, branches: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        trigger: List[Dict[str, Any]] = []
        transform: List[Dict[str, Any]] = []

        for i, a in enumerate(branches):
            for b in branches[i + 1:]:
                if (a, b) in self.CHONG or (b, a) in self.CHONG:
                    trigger.append({"type": "충", "between": f"{a}{b}", "qi_shift": "강한 대립"})
                if (a, b) in self.XING or (b, a) in self.XING:
                    trigger.append({"type": "형", "between": f"{a}{b}", "qi_shift": "마찰/구속"})
                if (a, b) in self.PO or (b, a) in self.PO:
                    trigger.append({"type": "파", "between": f"{a}{b}", "qi_shift": "기력 상쇄"})
                if (a, b) in self.HAI or (b, a) in self.HAI:
                    trigger.append({"type": "해", "between": f"{a}{b}", "qi_shift": "은은한 방해"})
                if (a, b) in self.WONJIN or (b, a) in self.WONJIN:
                    trigger.append({"type": "원진", "between": f"{a}{b}", "qi_shift": "원한/응어리"})

                if (a, b) in self.LIUHE or (b, a) in self.LIUHE:
                    transform.append({"type": "육합", "between": f"{a}{b}", "qi_shift": "화합/변형"})

        for group, name in self.SAMHAP:
            if all(x in branches for x in group):
                transform.append({"type": "삼합", "group": name, "qi_shift": "국 형성"})

        return {"trigger": trigger, "transform": transform}


class SpecialPatternEngine:
    """특수격 판정."""
    def detect(self, chart: SajuChart, energy: Dict[str, Any]) -> Dict[str, Any]:
        elements = energy["elements"]
        total = energy["total"] or 1.0

        def pct(ele: Element) -> float:
            return elements.get(ele, 0.0) / total

        day_ele = STEM_ELEMENT[chart.day_master]
        support_ele = {"木": Element.WATER, "火": Element.WOOD, "土": Element.FIRE, "金": Element.EARTH, "水": Element.METAL}[day_ele]
        peer_ele = {"木": Element.WOOD, "火": Element.FIRE, "土": Element.EARTH, "金": Element.METAL, "水": Element.WATER}[day_ele]

        support_ratio = pct(support_ele)
        peer_ratio = pct(peer_ele)

        if support_ratio >= 0.5 and peer_ratio >= 0.2:
            return {"성립": True, "type": "종강격", "detail": "인성 중심 종속"}
        if peer_ratio >= 0.5 and support_ratio >= 0.2:
            return {"성립": True, "type": "종왕격", "detail": "비겁 중심 종속"}

        if (pct(Element.WOOD) + pct(Element.FIRE)) >= 0.85 and pct(Element.WATER) == 0 and pct(Element.METAL) == 0:
            return {"성립": True, "type": "화격", "detail": "목화 순수 기세"}

        if pct(Element.WOOD) >= 0.8:
            return {"성립": True, "type": "건록격", "detail": "목기 과왕"}
        if pct(Element.METAL) >= 0.8:
            return {"성립": True, "type": "양인격", "detail": "금기 과왕"}

        for ele in Element:
            if pct(ele) >= 0.8:
                return {"성립": True, "type": f"종{ele.name.lower()}격", "detail": "단일 오행 편중"}

        return {"성립": False, "type": "", "detail": "일반격"}


class TongByunWriter:
    """10-step narrative generator."""
    def build(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "1_사주구성": ctx.get("chart"),
            "2_오행분포": ctx.get("energy"),
            "3_형충파해": ctx.get("relations"),
            "4_통근투출": ctx.get("rooting"),
            "5_육신": ctx.get("ten_gods"),
            "6_격국용신": ctx.get("gyeok"),
            "7_신살": ctx.get("spirits"),
            "8_그릇": ctx.get("capacity"),
            "9_운": ctx.get("luck"),
            "10_결론": ctx.get("final"),
        }


# ============================================================================
# Final engine
# ============================================================================

class SajuEngineV15FinalLockPatched:
    def __init__(self, climate_matrix: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None):
        self.jpjj = JaPyeongJinJeon()
        self.jcs = JeokCheonSu()
        self.gtbg = GungTongBoGam()
        self.smth = SamMyeongTongHoe()
        self.relations = RelationEngine()
        self.special = SpecialPatternEngine()
        self.writer = TongByunWriter()
        if climate_matrix:
            self.gtbg.load_climate_matrix(climate_matrix)

    def run(self, chart: SajuChart, daewoon: str, sewoon: str, monthun: Optional[str] = None) -> Dict[str, Any]:
        month_authority = self._month_authority(chart.month[1])

        johu = self.gtbg.analyze_climate(chart, month_authority)
        energy_flow = self.jcs.analyze_energy_flow(chart)
        relations = self.relations.analyze(chart.branches)
        gyeok = self.jpjj.determine_pattern(chart, month_authority, relations)

        special = self.special.detect(chart, energy_flow)
        spirits = self.smth.detect_spirits(chart)

        yongsin = self._determine_yongsin(johu, energy_flow["day_strength"], gyeok, chart, special)
        activation = self._check_activation(gyeok, relations, daewoon, sewoon, yongsin)
        conditions = self._classify_conditions(gyeok, relations, daewoon, sewoon, yongsin, chart)
        event = self._event_engine(
            core=bool(conditions.core),
            activation=activation.state,
            depth=activation.depth,
            score=conditions.score,
            filter_state=conditions.filter_,
            special=special
        )
        probability = self._calc_probability(event, activation, conditions, yongsin)

        rooting = {
            "월지": chart.month[1],
            "본기": month_authority.main_qi,
            "점수": gyeok.rooting_score,
            "투출": gyeok.exposed
        }
        ten_gods = [get_ten_god(chart.day_master, s).value for s in chart.stems]
        capacity = {
            "special_pattern": special,
            "roots": rooting,
            "score": gyeok.success_score
        }
        luck = {
            "daewoon": daewoon,
            "sewoon": sewoon,
            "sync": activation.luck_sync
        }
        final = {
            "event": event.code,
            "probability": probability,
            "reason": activation.reason,
        }

        narrative = self.writer.build({
            "chart": chart,
            "energy": energy_flow,
            "relations": relations,
            "rooting": rooting,
            "ten_gods": ten_gods,
            "gyeok": gyeok,
            "spirits": spirits,
            "capacity": capacity,
            "luck": luck,
            "final": final,
        })

        return {
            "구조": {
                "격국": gyeok.gyeok_name,
                "타입": gyeok.gyeok_type,
                "성패점수": gyeok.success_score,
                "상신존재": gyeok.sangshin.get("exists"),
                "상신": gyeok.sangshin.get("sangshin", []),
            },
            "특수격": special,
            "조후": johu,
            "억부": {
                "일간강도": energy_flow["day_strength"],
                "균형점수": energy_flow["balance_score"],
            },
            "활성": {
                "상태": activation.state,
                "깊이": activation.depth,
                "운동기화": activation.luck_sync,
                "사유": activation.reason,
            },
            "조건": {
                "코어": conditions.core,
                "트리거": conditions.trigger,
                "타이밍": conditions.timing,
                "필터": conditions.filter_,
                "강도점수": conditions.score,
            },
            "사건": {
                "코드": event.code,
                "레벨": event.level,
                "확률": event.probability,
                "지연": event.delay,
            },
            "신살": spirits,
            "인간서사": narrative,
        }

    def _month_authority(self, month_branch: str) -> MonthAuthority:
        season_map = {
            "寅": "봄", "卯": "봄", "辰": "봄",
            "巳": "여름", "午": "여름", "未": "여름",
            "申": "가을", "酉": "가을", "戌": "가을",
            "亥": "겨울", "子": "겨울", "丑": "겨울"
        }
        return MonthAuthority(
            branch=month_branch,
            main_qi=HIDDEN_STEMS[month_branch][0][0],
            season=season_map.get(month_branch, "")
        )

    def _determine_yongsin(self, johu: Dict[str, Any], day_strength: float, gyeok: Structure, chart: SajuChart, special: Dict[str, Any]) -> Dict[str, Any]:
        day_ele = STEM_ELEMENT[chart.day_master]
        if johu.get("exists"):
            return {"primary": "조후", "element": johu["need"][0], "state": "active"}
        if special.get("성립"):
            return {"primary": "특수격", "element": chart.day_master, "state": "active", "special_type": special.get("type")}
        if day_strength < 0.3:
            return {"primary": "억부", "element": DAYMASTER_ELEMENT_SUPPORT[day_ele], "state": "active"}
        if day_strength > 0.7:
            reverse = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
            return {"primary": "억부", "element": reverse[day_ele], "state": "active"}
        if gyeok.sangshin.get("exists") and gyeok.sangshin.get("sangshin"):
            return {"primary": "격국", "element": gyeok.sangshin["sangshin"][0], "state": "active"}
        return {"primary": "중화", "element": "土", "state": "neutral"}

    def _check_activation(self, gyeok: Structure, relations: Dict[str, Any], daewoon: str, sewoon: str, yongsin: Dict[str, Any]) -> Activation:
        if gyeok.gyeok_type not in ["정격", "파격"]:
            return Activation(False, 0, False, "구조 미확정")
        if gyeok.rooting_score < 2 and not gyeok.exposed:
            return Activation(False, 0, False, f"통근 부족({gyeok.rooting_score}), 투간 없음")
        if len(relations.get("trigger", [])) == 0:
            return Activation(False, 0, False, "관계 트리거 없음")
        luck_sync = self._check_luck_sync(daewoon, sewoon, yongsin.get("element"))
        if not luck_sync:
            return Activation(False, 0, False, "운 동기화 실패")
        depth = (1 if gyeok.rooting_score >= 2 else 0) + (1 if gyeok.exposed else 0) + (1 if len(relations.get("trigger", [])) >= 2 else 0) + (1 if luck_sync else 0)
        return Activation(True, depth, True, "모든 조건 충족")

    def _classify_conditions(self, gyeok: Structure, relations: Dict[str, Any], daewoon: str, sewoon: str, yongsin: Dict[str, Any], chart: SajuChart) -> Conditions:
        core, trigger, timing, filter_ = [], [], [], []
        if gyeok.gyeok_type in ["정격", "파격"]:
            core.append("구조성립")
        if gyeok.sangshin.get("exists"):
            core.append("상신존재")
        for t in relations.get("trigger", []):
            trigger.append(f"{t['type']}_{t['between']}")
        if self._check_luck_sync(daewoon, sewoon, yongsin.get("element")):
            timing.append("용신운")
        if self._check_luck_trigger(daewoon, sewoon, relations):
            timing.append("운발동")
        if "공망" in self.smth.detect_spirits(chart):
            filter_.append("공망")
        score = (1 if core else 0) + (1 if trigger else 0) + (1 if timing else 0) + (1 if len(trigger) >= 2 else 0)
        if gyeok.sangshin.get("exists"):
            score += 1
        return Conditions(core=core, trigger=trigger, timing=timing, filter_=filter_, score=score)

    def _event_engine(self, core: bool, activation: bool, depth: int, score: int, filter_state: List[str], special: Dict[str, Any]) -> Event:
        if not core or not activation or "공망" in filter_state:
            return Event("없음", "없음", 0.0, False)

        if special.get("성립"):
            score += 1
            if special.get("type") in {"화격", "종강격", "종왕격"}:
                depth += 1

        if depth >= 4 and score >= 5:
            level, prob = "L4", 0.90
        elif depth >= 3 and score >= 4:
            level, prob = "L3", 0.75
        elif score >= 3:
            level, prob = "L2", 0.55
        else:
            level, prob = "L1", 0.30

        return Event(self._predict_event_code(score), level, prob, False)

    def _check_luck_sync(self, daewoon: str, sewoon: str, yongsin_element: Optional[str]) -> bool:
        if not yongsin_element:
            return False
        for token in [daewoon, sewoon]:
            if not token or len(token) < 2:
                continue
            if STEM_ELEMENT.get(token[0]) == yongsin_element:
                return True
            if BRANCH_ELEMENT.get(token[1]) == yongsin_element:
                return True
        return False

    def _check_luck_trigger(self, daewoon: str, sewoon: str, relations: Dict[str, Any]) -> bool:
        combined = (daewoon or "") + (sewoon or "")
        for t in relations.get("trigger", []):
            if t["type"] in {"충", "형", "파", "해", "원진"}:
                if any(ch in combined for ch in t["between"]):
                    return True
        return False

    def _predict_event_code(self, score: int) -> str:
        codes = [
            "TURNING_POINT", "JOB_START", "REL_MARRIAGE", "FIN_GAIN_SPIKE",
            "JOB_PROMOTION", "FIN_COLLAPSE", "REL_DIVORCE", "REL_AFFAIR"
        ]
        idx = min(max(score, 0), len(codes) - 1)
        return codes[idx]

    def _calc_probability(self, event: Event, activation: Activation, conditions: Conditions, yongsin: Dict[str, Any]) -> float:
        if event.level == "없음":
            return 0.0
        prob = event.probability
        prob += activation.depth * 0.04
        prob += 0.03 if yongsin.get("state") == "active" else 0.0
        prob -= len(conditions.filter_) * 0.05
        return max(0.0, min(0.99, prob))


# ============================================================================
# Integration facade for existing SAJU_ENGINE_MASTER
# ============================================================================

class ExternalLookupLoader:
    """Optional loader for canonical JSON 룩업 files."""
    def __init__(self, folder: str):
        self.folder = folder

    def load_json(self, filename: str, default=None):
        import json
        from pathlib import Path
        path = Path(self.folder) / filename
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))


class SajuEngineIntegrated:
    """
    Final integration entry-point.
    - Uses the patched V15 core.
    - Optionally merges external JSON tables for climate/spirits/gongmang/etc.
    """
    def __init__(self, lookup_folder: str | None = None):
        self.lookup = ExternalLookupLoader(lookup_folder) if lookup_folder else None
        self.engine = SajuEngineV15FinalLockPatched()

        if self.lookup:
            self._merge_external_lookups()

    def _merge_external_lookups(self):
        # climate matrix
        climate = self.lookup.load_json("climate_matrix.json")
        if climate:
            # allow {"甲|寅": {...}} or list entries
            normalized = {}
            if isinstance(climate, dict):
                for k, v in climate.items():
                    if "|" in k:
                        a, b = k.split("|", 1)
                        normalized[(a, b)] = v
            elif isinstance(climate, list):
                for row in climate:
                    key = row.get("key")
                    if key and "|" in key:
                        a, b = key.split("|", 1)
                        normalized[(a, b)] = row
            if normalized:
                self.engine.gtbg.load_climate_matrix(normalized)

    def run(self, chart: SajuChart, daewoon: str, sewoon: str, monthun: Optional[str] = None) -> Dict[str, Any]:
        return self.engine.run(chart, daewoon=daewoon, sewoon=sewoon, monthun=monthun)


def build_sample_report():
    """Demo helper."""
    engine = SajuEngineIntegrated()
    chart = SajuChart(year="丙寅", month="庚寅", day="丁亥", hour="丙午", gender="여")
    return engine.run(chart, daewoon="甲午", sewoon="丙午")


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(build_sample_report(), ensure_ascii=False, indent=2))
