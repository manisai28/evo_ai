import re
from backend.tasks import set_reminder, add_note, get_notes, get_weather, web_search, send_email, calculate

def detect_task(msg: str):
    msg = msg.lower()

    match = re.match(r"remind me in (\d+) minutes? to (.+)", msg)
    if match:
        return set_reminder.delay(match.group(2), int(match.group(1)))

    if msg.startswith("note "):
        return add_note.delay(msg.replace("note ", ""))
    if msg.startswith("show notes"):
        return get_notes.delay()

    if msg.startswith("weather "):
        city = msg.replace("weather ", "")
        return get_weather.delay(city)

    if msg.startswith("search "):
        query = msg.replace("search ", "")
        return web_search.delay(query)

    if msg.startswith("email "):
        match = re.match(r"email (.+?) subject:(.+?) body:(.+)", msg)
        if match:
            return send_email.delay(
                match.group(1).strip(),
                match.group(2).strip(),
                match.group(3).strip()
            )

    if msg.startswith("calc "):
        expr = msg.replace("calc ", "")
        return calculate.delay(expr)

    return None
