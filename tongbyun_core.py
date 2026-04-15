"""SAJU_ENGINE_MASTER vFINAL MASTER - TongByun Core

This module provides:
- TongLayer: fixed (통)
- ByunLayer: contextual (변)
- TongByunEngine: combined report
- Optional pipeline integration helpers

The engine is designed to be 룩업 기반 and to keep
calculation out of the interpretive layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Iterable
import json
from pathlib import Path


# =========================
# Domain models
# =========================

@dataclass
class AnalysisContext:
    chart: Any = None
    climate: Any = None
    strength: Any = None
    gyeok: Any = None
    hidden: Any = None
    tongguan: Any = None
    cheyong: Any = None
    events: Any = None
    causal_chain: Any = None
    medicine: Any = None
    cases: Any = None
    timeline: Any = None
    prob: Any = None
    final_report: Dict[str, Any] = field(default_factory=dict)

    # Optional raw / runtime hints
    raw: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    hidden_triggers: List[str] = field(default_factory=list)
    event_triggers: List[str] = field(default_factory=list)
    target_event_type: str = "미분류"
    has_structure: bool = False
    luck_flow_match: bool = False
    has_conflict_or_combo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =========================
# Tong / Byun layers
# =========================

class TongLayer:
    """통(通): relatively stable, rule-fixed layer."""

    def apply(self, ctx: AnalysisContext) -> Dict[str, Any]:
        return {
            "조후": ctx.climate,
            "억부": ctx.strength,
            "격국": ctx.gyeok,
        }


class ByunLayer:
    """변(變): contextual, event-driven layer."""

    def apply(self, ctx: AnalysisContext) -> Dict[str, Any]:
        return {
            "지장간": ctx.hidden,
            "통관": ctx.tongguan,
            "체용": ctx.cheyong,
            "사건": ctx.events,
            "인과": ctx.causal_chain,
            "타임라인": ctx.timeline,
            "사례": ctx.cases,
            "처방": ctx.medicine,
        }


class TongByunEngine:
    """Combine fixed and contextual layers into a final interpretive report."""

    def run(self, ctx: AnalysisContext) -> Dict[str, Any]:
        tong = TongLayer().apply(ctx)
        byun = ByunLayer().apply(ctx)

        merged = {
            "통": tong,
            "변": byun,
            "통변결론": self._merge(tong, byun),
        }
        return merged

    def _merge(self, tong: Dict[str, Any], byun: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "핵심구조": tong.get("격국"),
            "실제작동": byun.get("체용"),
            "사건흐름": byun.get("인과"),
            "환경": tong.get("조후"),
            "기세": tong.get("억부"),
            "사건": byun.get("사건"),
        }


# =========================
# Supporting modules
# =========================

class EventTriggerValidator:
    """Hard condition gate for event recognition."""

    def validate(self, ctx: AnalysisContext) -> bool:
        return bool(
            ctx.has_structure
            and ctx.luck_flow_match
            and ctx.has_conflict_or_combo
        )


class CausalChainEngine:
    """Build a human-readable causal chain from analysis state."""

    def build(self, ctx: AnalysisContext) -> List[str]:
        chain: List[str] = []

        if ctx.gyeok:
            chain.append("구조 형성")

        if ctx.strength:
            chain.append("기세 확보")

        if ctx.tongguan:
            chain.append("충돌 중재")

        if ctx.cheyong:
            chain.append("체용 연결")

        if ctx.events:
            chain.append("사건 발동")

        if ctx.timeline:
            chain.append("시간층 확장")

        return chain


class FinalReportBuilder:
    """Single place to assemble the final engine output."""

    def build(self, ctx: AnalysisContext, tongbyun: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "조후": ctx.climate,
            "억부": ctx.strength,
            "격국": ctx.gyeok,
            "지장간": ctx.hidden,
            "체용": ctx.cheyong,
            "통관": ctx.tongguan,
            "사건": ctx.events,
            "인과": ctx.causal_chain,
            "타임라인": ctx.timeline,
            "사례": ctx.cases,
            "처방": ctx.medicine,
            "통변": tongbyun,
        }
        ctx.final_report = report
        return report


# =========================
# Pipeline integration helper
# =========================

class TongByunIntegration:
    """Use this after your core pipeline has already filled ctx."""

    def __init__(self):
        self.validator = EventTriggerValidator()
        self.causal = CausalChainEngine()
        self.builder = FinalReportBuilder()
        self.tongbyun = TongByunEngine()

    def finalize(self, ctx: AnalysisContext) -> Dict[str, Any]:
        # Make sure event state is validated before finalization.
        ctx.events = ctx.events or []
        if not ctx.causal_chain:
            ctx.causal_chain = self.causal.build(ctx)

        # Optional: enrich context only if conditions are met
        ctx.event_valid = self.validator.validate(ctx)

        tongbyun_report = self.tongbyun.run(ctx)
        return self.builder.build(ctx, tongbyun_report)


# =========================
# Simple JSON utilities
# =========================

def load_json(path: str | Path) -> Any:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# =========================
# Example usage
# =========================

if __name__ == "__main__":
    ctx = AnalysisContext(
        climate={"type": "난조", "delay": 0.8, "volatility": 1.3},
        strength={"label": "중화"},
        gyeok={"label": "정재격"},
        hidden={"인": {"본기": "갑", "중기": "병", "여기": "무"}},
        tongguan=[{"충돌": ("목", "토"), "통관": "화", "성립": True}],
        cheyong={"체": "정재격", "용": "관", "결과": "재생관 성립"},
        events=[{"event_type": "결혼", "confidence": 0.82}],
        timeline=[{"year": 2026, "label": "관계 전환"}],
        cases=[{"id": "case_marry_001", "_score": 4.2}],
        medicine={"조언": "조후 보정"},
        has_structure=True,
        luck_flow_match=True,
        has_conflict_or_combo=True,
    )

    report = TongByunIntegration().finalize(ctx)
    print(json.dumps(report, ensure_ascii=False, indent=2))