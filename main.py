from core.engine import SajuEngineMaster

if __name__ == "__main__":
    engine = SajuEngineMaster()

    chart = {
        "year": "丙寅",
        "month": "庚寅",
        "day": "丁亥",
        "hour": "丙午",
        "일간": "丁",
        "일지": "亥"
    }

    result = engine.run(chart)

    print(result)
