from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from .doctrine_catalog import build_doctrine_index


@dataclass
class CaseRecord:
    case_id: str
    chart_key: str
    topic: str
    pattern: str
    event: str
    core_issue: str
    interpretation_logic: str
    tags: List[str]
    sources: List[str]
    confidence: float


class CaseBuilder:
    def __init__(self) -> None:
        self.doctrine_index = build_doctrine_index()

    def build_from_pattern(self, case_id: str, chart_key: str, topic: str, pattern: str) -> Dict[str, Any]:
        entry = self.doctrine_index.get(pattern)
        if not entry:
            return {
                "case_id": case_id,
                "chart_key": chart_key,
                "topic": topic,
                "pattern": pattern,
                "event": "일반",
                "core_issue": "판례 미분류",
                "interpretation_logic": "해당 패턴이 doctrine catalog에 없음",
                "tags": [topic, pattern],
                "sources": [],
                "confidence": 0.50,
            }

        record = CaseRecord(
            case_id=case_id,
            chart_key=chart_key,
            topic=topic,
            pattern=pattern,
            event=entry.event,
            core_issue=f"{pattern} 구조에서 {entry.event}로 수렴하는 사례",
            interpretation_logic=entry.logic,
            tags=list(dict.fromkeys([topic, pattern] + entry.tags)),
            sources=entry.sources,
            confidence=entry.confidence,
        )
        return asdict(record)
