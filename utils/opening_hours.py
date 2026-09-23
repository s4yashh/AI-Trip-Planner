"""Conservative OSM weekly-hours support. Unsupported expressions stay unknown."""
import re

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def windows(expression, day):
    if not expression:
        return None
    if expression == "24/7":
        return [(0, 1440)]
    result = []
    for rule in expression.split(";"):
        match = re.fullmatch(r"\s*(?:(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?\s+)?(off|closed|\d\d:\d\d-\d\d:\d\d(?:,\d\d:\d\d-\d\d:\d\d)*)\s*", rule)
        if not match:
            return None
        first, last, hours = match.groups()
        weekdays = set(range(7))
        if first:
            start, end = DAYS.index(first), DAYS.index(last or first)
            weekdays = {(start + i) % 7 for i in range((end - start) % 7 + 1)}
        if day.weekday() not in weekdays:
            continue
        if hours in {"off", "closed"}:
            result = []
            continue
        for period in hours.split(","):
            a, b = period.split("-")
            start, end = minutes(a), minutes(b)
            if not 0 <= start < end <= 1440:
                return None
            result.append((start, end))
    return result


def minutes(value):
    hours, minute = map(int, value.split(":"))
    return hours * 60 + minute


def indoor(place):
    return place.kind in {"museum", "gallery"} or place.tags.get("indoor") == "yes"
