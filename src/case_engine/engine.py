from __future__ import annotations

from typing import Any, Dict, List, Optional

from .case_builder import CaseBuilder
from .pattern_router import PatternRouter


class DoctrineDrivenSajuEngine:
    """기존 사주엔진 결과에 통변법 사례를 접붙이는 통합 어댑터."""

    def __init__(self) -> None:
        self.router = PatternRouter()
        self.builder = CaseBuilder()

    def enrich(self, chart: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        patterns = self.router.detect(chart)
        cases: List[Dict[str, Any]] = []

        for i, pattern in enumerate(patterns, start=1):
            cases.append(
                self.builder.build_from_pattern(
                    case_id=f"AUTO_{i:04d}",
                    chart_key=base_result.get("chart_key", ""),
                    topic=base_result.get("topic", "일반"),
                    pattern=pattern,
                )
            )

        merged = dict(base_result)
        merged["detected_patterns"] = patterns
        merged["doctrine_cases"] = cases
        merged["doctrine_mode"] = True
        return merged

    def interpret(self, chart: Dict[str, Any], base_result: Dict[str, Any], top_k: int = 3) -> Dict[str, Any]:
        enriched = self.enrich(chart, base_result)
        return {
            "base": base_result,
            "enriched": enriched,
            "top_cases": enriched.get("doctrine_cases", [])[:top_k],
        }
