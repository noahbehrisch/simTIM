def format_time(hours: float) -> str:
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02d}:{m:02d}"


def parse_event(event):
    if hasattr(event, "time") and hasattr(event, "event_type") and hasattr(event, "data"):
        return event.time, event.event_type, event.data
    elif isinstance(event, (list, tuple)) and len(event) >= 3:
        return event[0], event[1], event[2]
    return None, None, None
