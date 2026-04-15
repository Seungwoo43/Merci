# saju_timeline_simulator_v11.py

class ReactionEngine:

    def react(self, structure, incoming_luck):

        strength = structure.get("strength")
        pattern = structure.get("pattern")
        hidden = structure.get("hidden_trigger")

        # 1. 강약 반응
        if strength == "신강":
            base = "주도"
        else:
            base = "수동"

        # 2. 격국 반응
        if pattern == "재성":
            if incoming_luck == "재성":
                return "돈 확대"
            else:
                return "기회 상실"

        if pattern == "관성":
            if incoming_luck == "재성":
                return "책임 증가"

        # 3. 지장간 반응
        if hidden == incoming_luck:
            return "내면 폭발"

        return base


class TimelineEngineV11:

    EVENTS = {
        "E1": "연애 시작",
        "E2": "결혼",
        "E3": "이별",
        "E4": "출산",
        "E5": "취업",
        "E6": "승진",
        "E7": "금전 상승",
        "E8": "금전 손실",
        "E9": "이사",
        "E10": "건강 문제"
    }

    TRIGGERS = {
        "연애 시작": ["도화", "합"],
        "결혼": ["정관", "합"],
        "이별": ["충", "원진"],
        "금전 상승": ["재성"],
        "금전 손실": ["충"],
    }

    def __init__(self, base_engine):
        self.base_engine = base_engine
        self.reactor = ReactionEngine()

    def simulate(self, chart, luck_flow):

        base = self.base_engine.analyze(chart)
        structure = base.get("구조", {})

        timeline = []

        for year, luck in luck_flow:

            interaction = self._interaction(base, luck)

            reaction = self.reactor.react(structure, luck)

            event = self._detect_event(luck, interaction, reaction)

            if event:
                timeline.append({
                    "year": year,
                    "event": event,
                    "reaction": reaction
                })

        return timeline

    def _interaction(self, base, luck):
        # 간단 예시
        if "충" in str(base.get("형충합파")):
            return "충"
        return "없음"

    def _detect_event(self, luck, interaction, reaction):

        for event, triggers in self.TRIGGERS.items():

            if luck in triggers or interaction in triggers:
                return event

        return None


# 사용 예시
if __name__ == "__main__":

    from saju_engine_final_v1 import SajuEngineFinalV1

    class DummyCore:
        def get_hidden_stems(self, x): return {}
        def get_tengod(self, a,b): return "재성"
        def get_12unseong(self,a,b): return "건록"
        def detect_conflicts(self,x): return []
        def get_shinsal(self,x): return []
        def get_climate(self,x): return "중화"
        def get_strength(self,a,b): return "신강"
        def get_pattern(self,a,b): return "재성"

    base_engine = SajuEngineFinalV1(DummyCore())
    simulator = TimelineEngineV11(base_engine)

    chart = {
        "year":"丙寅",
        "month":"庚寅",
        "day":"丁亥",
        "hour":"丙午"
    }

    luck_flow = [
        (24, "도화"),
        (28, "정관"),
        (31, "재성"),
        (35, "충")
    ]

    result = simulator.simulate(chart, luck_flow)

    for r in result:
        print(r)
