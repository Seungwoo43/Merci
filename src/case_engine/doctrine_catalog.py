from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DoctrineEntry:
    pattern: str
    event: str
    logic: str
    tags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0


# 1차 통변법 카탈로그: 고서 축 + 사건 축을 연결하는 최소 실행 세트
DOCTRINE_ENTRIES: List[DoctrineEntry] = [
    DoctrineEntry(
        pattern="재다신약",
        event="재물손실",
        logic="재성이 많고 일간이 약하면 재를 감당하지 못해 손실과 유출이 커지는 패턴",
        tags=["재성", "신약", "손실", "투자"],
        sources=["子平真诠", "三命通会", "渊海子平"],
        confidence=0.90,
    ),
    DoctrineEntry(
        pattern="식상생재",
        event="사업성공",
        logic="식상에서 재성으로 흐름이 이어지면 생산성과 수익화가 연결되는 패턴",
        tags=["식상", "재성", "사업", "수익"],
        sources=["三命通会", "渊海子平"],
        confidence=0.88,
    ),
    DoctrineEntry(
        pattern="관인상생",
        event="직업안정",
        logic="관성과 인성이 연결되면 규범과 자격이 살아나 안정 직업과 승진으로 수렴하는 패턴",
        tags=["관성", "인성", "직업", "승진"],
        sources=["子平真诠", "三命通会"],
        confidence=0.91,
    ),
    DoctrineEntry(
        pattern="상관견관",
        event="직장충돌",
        logic="상관이 관성을 건드리면 규칙과 제도와의 충돌이 사건으로 드러나는 패턴",
        tags=["상관", "정관", "충돌", "구설"],
        sources=["三命通会", "渊海子平"],
        confidence=0.89,
    ),
    DoctrineEntry(
        pattern="식신제살",
        event="위기극복",
        logic="식신이 칠살을 제어하면 압박을 통제하고 실무적 해결로 전환되는 패턴",
        tags=["식신", "칠살", "제어", "극복"],
        sources=["三命通会", "渊海子平"],
        confidence=0.86,
    ),
]


def build_doctrine_index() -> Dict[str, DoctrineEntry]:
    return {entry.pattern: entry for entry in DOCTRINE_ENTRIES}
