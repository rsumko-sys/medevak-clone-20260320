"""Discord webhook notifications for operational events.

Fire-and-forget: errors are logged but never propagate to the caller.
Disabled automatically when DISCORD_WEBHOOK_URL is not set.
"""
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx

from app.core.config import DISCORD_WEBHOOK_URL

if TYPE_CHECKING:
    from app.models.cases import Case

logger = logging.getLogger(__name__)

# Triage → Discord embed color (decimal int) + label
_TRIAGE_META = {
    "!":         (15158332, "🔴 НЕГАЙНО"),        # red
    "IMMEDIATE": (15158332, "🔴 НЕГАЙНО"),
    "+":         (9807270,  "⚫ ОЧІКУВАНИЙ"),      # dark grey
    "EXPECTANT": (9807270,  "⚫ ОЧІКУВАНИЙ"),
    "T1":        (15158332, "🔴 ТРІАЖ-1"),
    "T2":        (16776960, "🟡 ТРІАЖ-2"),
    "T3":        (3066993,  "🟢 ТРІАЖ-3"),
    "RED":       (15158332, "🔴 ЧЕРВОНИЙ"),
    "YELLOW":    (16776960, "🟡 ЖОВТИЙ"),
    "GREEN":     (3066993,  "🟢 ЗЕЛЕНИЙ"),
    "BLACK":     (2303786,  "⚫ ЧОРНИЙ"),
    "DELAYED":   (16776960, "🟡 ВІДКЛАДЕНИЙ"),
    "MINIMAL":   (3066993,  "🟢 МІНІМАЛЬНИЙ"),
}
_DEFAULT_COLOR = (10181046, "⬜ НЕВІДОМО")  # grey


def _triage_meta(code: str | None) -> tuple[int, str]:
    if not code:
        return _DEFAULT_COLOR
    return _TRIAGE_META.get(str(code).upper(), _TRIAGE_META.get(str(code), _DEFAULT_COLOR))


async def notify_new_case(case: "Case") -> None:
    """Send a Discord embed when a new case is created. Silent no-op if webhook not configured."""
    if not DISCORD_WEBHOOK_URL:
        return

    color, triage_label = _triage_meta(getattr(case, "triage_code", None))

    callsign = getattr(case, "callsign", None) or getattr(case, "full_name", None) or "—"
    unit = getattr(case, "unit", None) or "—"
    mechanism = getattr(case, "mechanism_of_injury", None) or getattr(case, "mechanism", None) or "—"
    case_id = str(getattr(case, "id", ""))
    ts = getattr(case, "created_at", None)
    time_str = ts.strftime("%d %b %Y / %H:%M UTC") if ts else datetime.now(timezone.utc).strftime("%d %b %Y / %H:%M UTC")

    embed = {
        "title": "🚨 НОВА ЕВАКОЗАЯВКА",
        "color": color,
        "fields": [
            {"name": "Позивний", "value": callsign, "inline": True},
            {"name": "Підрозділ", "value": unit, "inline": True},
            {"name": "Тріаж", "value": triage_label, "inline": True},
            {"name": "Механізм травми", "value": mechanism, "inline": False},
            {"name": "ID кейсу", "value": f"`{case_id}`", "inline": False},
        ],
        "footer": {"text": f"MEDEVAK • {time_str}"},
        "timestamp": ts.isoformat() if ts else datetime.now(timezone.utc).isoformat(),
    }

    payload = {"embeds": [embed]}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            if resp.status_code not in (200, 204):
                logger.warning("Discord webhook returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Discord notification failed (non-critical): %s", exc)
