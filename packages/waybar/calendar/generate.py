"""Build an offline holiday index from pinned python-holidays and local dates."""
import json
from datetime import date
import holidays


def generate():
    result = {"first_year": 2020, "last_year": 2040, "dates": {}}
    def add(day, region, name):
        entries = result["dates"].setdefault(str(day), [])
        if not any(e["region"] == region and e["name"] == name for e in entries):
            entries.append({"region": region, "name": name})
    for country, subdivision, region in [("ES", "CT", "cat"), ("AR", None, "ar"), ("US", None, "us")]:
        calendar = holidays.country_holidays(country, subdiv=subdivision,
            years=range(2020, 2041), language="en_US", observed=True)
        for day, name in sorted(calendar.items()):
            # Bridge days are not mandatory public holidays in Argentina.
            name = name.replace("Bridge Public Holiday", "Tourism non-working day (optional)")
            if country == "AR":
                name = name.replace("Maundy Thursday", "Maundy Thursday (optional non-working day)")
            add(day, region, name)
    # Spain drops a national holiday from the working calendar when it falls on
    # a Sunday and the region does not move it (SUN_TO_NONE). Keep the date
    # itself, e.g. Constitution Day on Sunday 6 December 2026, because it is
    # still a national holiday even though it creates no extra day off.
    national = holidays.country_holidays("ES", years=range(2020, 2041),
        language="en_US", observed=False)
    for day, name in sorted(national.items()):
        add(day, "cat", name)
    # Barcelona's two local public holidays are declared each year, not inferred.
    for year, whit in [(2026, "05-25"), (2027, "05-17")]:
        add(date.fromisoformat(f"{year}-{whit}"), "cat", "Barcelona: Whit Monday / Segona Pasqua")
        add(date(year, 9, 24), "cat", "Barcelona: La Mercè")
    return result

if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, sort_keys=True))
