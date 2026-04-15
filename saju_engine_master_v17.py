# saju_engine_master_v17.py
# 🔥 V17 FINAL — Full Integrated Saju AI Engine

from collections import defaultdict

# =========================
# 1. Month Authority (월령)
# =========================
class MonthAuthority:
    def apply(self, chart):
        return {
            "월지": chart["월지"],
            "오행": chart["월령오행"],
            "power": 1.5
        }


# =========================
# 2. Energy Engine (지장간 기반)
# =========================
class EnergyEngine:
    ROOT_WEIGHT = {"정기": 1.0, "중기": 0.5, "여기": 0.2}

    def calculate(self, chart):
        energy = defaultdict(float)

        for branch, hidden in chart["지장간"].items():
            for h in hidden:
                base = self.ROOT_WEIGHT[h["type"]]

                if branch == chart["월지"]:
                    base *= 1.8

                if chart.get("충"):
                    base *= 0.7

                energy[h["stem"]] += base

        return dict(energy)


# =========================
# 3. Tonggwan (통관)
# =========================
class TonggwanEngine:
    def check(self, energy):
        elements = list(energy.keys())

        if "수" in elements and "화" in elements:
            if "목" in elements:
                return "통관성립"
        return None


# =========================
# 4. Gyeok Engine (격국)
# =========================
class GyeokEngine:
    def detect(self, chart):
        main = chart["월령오행"]

        if main == "화":
            return "정관격"
        elif main == "수":
            return "재격"
        return "일반격"


class GyeokValidator:
    def validate(self, gyeok, chart):
        if gyeok == "상관격":
            if "인성" not in chart.get("십성", []):
                return "파격"
        return "정격"


# =========================
# 5. Yongshin Engine
# =========================
class YongshinEngine:
    def select(self, chart):

        if chart.get("climate") == "한습":
            return "화"

        if chart.get("strength") == "신강":
            return "재성"

        return "인성"


# =========================
# 6. Reaction Engine
# =========================
class ReactionEngine:
    def react(self, structure, luck):

        if luck == structure["용신"]:
            return "상승"

        if structure["strength"] == "신강":
            return "확장"

        return "소모"


# =========================
# 7. Interaction Engine
# =========================
class InteractionEngine:
    def detect(self, chart, luck):

        interactions = []

        if chart.get("충"):
            interactions.append("충")

        if chart.get("합"):
            interactions.append("합")

        if chart.get("원진"):
            interactions.append("원진")

        return interactions


# =========================
# 8. Event Engine (AND 조건)
# =========================
class EventEngine:

    def check(self, structure, luck, interaction, reaction):

        if not structure:
            return None

        if not luck:
            return None

        if not interaction:
            return None

        return {
            "event": self.map_event(reaction),
            "reaction": reaction
        }

    def map_event(self, reaction):

        mapping = {
            "상승": "성공/확장",
            "확장": "기회 증가",
            "소모": "손실/갈등"
        }

        return mapping.get(reaction, "변화")


# =========================
# 9. Timeline Engine
# =========================
class TimelineEngine:

    def simulate(self, chart, luck_flow):

        timeline = []

        for year, luck in luck_flow:

            reaction = chart["reaction_engine"].react(chart["structure"], luck)

            interaction = chart["interaction_engine"].detect(chart, luck)

            event = chart["event_engine"].check(
                chart["structure"],
                luck,
                interaction,
                reaction
            )

            if event:
                timeline.append({
                    "year": year,
                    "event": event["event"],
                    "reaction": reaction
                })

        return timeline


# =========================
# 🔥 10. MASTER ENGINE
# =========================
class SajuEngineMasterV17:

    def __init__(self):

        self.month = MonthAuthority()
        self.energy = EnergyEngine()
        self.tonggwan = TonggwanEngine()
        self.gyeok = GyeokEngine()
        self.validator = GyeokValidator()
        self.yong = YongshinEngine()
        self.reactor = ReactionEngine()
        self.interaction = InteractionEngine()
        self.event = EventEngine()
        self.timeline = TimelineEngine()

    def run(self, chart, luck_flow):

        # 1. 월령
        chart["month"] = self.month.apply(chart)

        # 2. 에너지
        chart["energy"] = self.energy.calculate(chart)

        # 3. 격국
        gyeok = self.gyeok.detect(chart)
        chart["격국"] = self.validator.validate(gyeok, chart)

        # 4. 용신
        yong = self.yong.select(chart)
        chart["용신"] = yong

        # 5. 통관
        chart["통관"] = self.tonggwan.check(chart["energy"])

        # 구조 정의
        chart["structure"] = {
            "strength": chart.get("strength", "중화"),
            "용신": yong
        }

        # 엔진 연결
        chart["reaction_engine"] = self.reactor
        chart["interaction_engine"] = self.interaction
        chart["event_engine"] = self.event

        # 6. 타임라인
        timeline = self.timeline.simulate(chart, luck_flow)

        return {
            "격국": chart["격국"],
            "용신": yong,
            "통관": chart["통관"],
            "energy": chart["energy"],
            "timeline": timeline
        }


# =========================
# ▶ 실행 예시
# =========================
if __name__ == "__main__":

    chart = {
        "월지": "寅",
        "월령오행": "목",
        "지장간": {
            "寅": [{"stem": "甲", "type": "정기"}],
            "亥": [{"stem": "壬", "type": "중기"}]
        },
        "strength": "신강",
        "climate": "조열",
        "충": True
    }

    luck_flow = [
        (25, "재성"),
        (30, "용신"),
        (35, "관성")
    ]

    engine = SajuEngineMasterV17()
    result = engine.run(chart, luck_flow)

    print(result)
