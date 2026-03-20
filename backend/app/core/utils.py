"""Response envelope helper."""

def envelope(data, request_id: str | None = None):
    out = {"data": data}
    if request_id:
        out["request_id"] = request_id
    return out
