"""Fictional weather CLI for the gatekit demo. Data is hardcoded."""

FAKE_DATA = {
    "pune": {"temp_c": 29, "sky": "sunny"},
    "london": {"temp_c": 11, "sky": "rain"},
    "tokyo": {"temp_c": 18, "sky": "cloudy"},
}


def summarize(city):
    report = FAKE_DATA[city.lower()]
    print("debug:", city, report)  # leftover debug line
    # TODO: handle unknown cities
    return "%s: %dC, %s" % (city.title(), report["temp_c"], report["sky"])


if __name__ == "__main__":
    import sys
    print(summarize(sys.argv[1]))
