import dateparser
from datetime import datetime, timedelta

def parse_date(text, ref_date=None):
    if ref_date is None:
        ref_date = datetime.now()

    # Manuelle Regeln für spezielle Zeitangaben
    text = text.lower()
    now = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)

    if text in ["heute abend"]:
        return (now + timedelta(hours=18))
    elif text in ["heute nacht"]:
        return (now + timedelta(hours=22))
    elif text in ["morgen"]:
        return (now + timedelta(days=1))
    elif text in ["übermorgen"]:
        return (now + timedelta(days=2))
    
    # Wochentage behandeln
    weekdays = {
        "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
        "freitag": 4, "samstag": 5, "sonntag": 6
    }
    for day, num in weekdays.items():
        if f"am {day}" in text:
            days_ahead = (num - now.weekday()) % 7
            if days_ahead == 0:  # Falls heute schon dieser Wochentag ist, nimm nächste Woche
                days_ahead = 7
            return (now + timedelta(days=days_ahead))

    # "Nächste Woche Freitag" behandeln
    if "nächste woche" in text:
        for day, num in weekdays.items():
            if day in text:
                days_ahead = (num - now.weekday()) % 7 + 7
                return (now + timedelta(days=days_ahead))

    # Standard-Fallback mit dateparser
    parsed_date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': ref_date})
    if parsed_date:
        return parsed_date

    return None


if __name__ == "__main__":
    # Testfälle
    test_inputs = [
        "20.02.",
        "20.2.",
        "Heute Abend",
        "Heute Nacht",
        "Morgen",
        "Am Dienstag",
        "Nächste Woche Freitag",
        "In 3 Tagen",
        "Übermorgen um 15 Uhr"
    ]

    for text in test_inputs:
        print(f"{text} → {parse_date(text)}")
