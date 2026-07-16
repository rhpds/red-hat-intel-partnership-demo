"""Parse Server-Sent Events from a streaming response into structured dicts."""

import json


def parse_sse(text: str) -> list[dict]:
    events = []
    current_event = None
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            raw = line[len("data:"):].strip()
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                data = {"raw": raw}
            events.append({"event": current_event, "data": data})
            current_event = None
    return events


def get_events_by_type(events: list[dict], event_type: str) -> list[dict]:
    return [e for e in events if e["event"] == event_type]


def get_token_text(events: list[dict]) -> str:
    tokens = get_events_by_type(events, "token")
    return "".join(t["data"].get("content", "") for t in tokens)
