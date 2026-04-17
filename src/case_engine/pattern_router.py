from __future__ import annotations

from typing import Any, Dict, List


class PatternRouter:
    """차트의 핵심 패턴을 통변법으로 라우팅한다."""

    def detect(self, chart: Dict[str, Any]) -> List[str]:
        ten_gods = chart.get("십성", []) or []
        strength = chart.get("strength", "")
        patterns: List[str] = []

        if "재성" in ten_gods and strength == "신약":
            patterns.append("재다신약")
        if "식상" in ten_gods and "재성" in ten_gods:
            patterns.append("식상생재")
        if "관성" in ten_gods and "인성" in ten_gods:
            patterns.append("관인상생")
        if "상관" in ten_gods and "정관" in ten_gods:
            patterns.append("상관견관")
        if "식신" in ten_gods and "칠살" in ten_gods:
            patterns.append("식신제살")

        # 기초 패턴이 없을 때도 후속 검색이 가능하도록 중립 패턴 제공
        if not patterns:
            patterns.append("중립")

        return patterns
