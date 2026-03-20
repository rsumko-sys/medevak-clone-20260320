"""Whisper transcription proxy — forwards audio to whisper-api.com, polls until done."""
import asyncio
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

WHISPER_SUBMIT  = "https://api.whisper-api.com/transcribe"
WHISPER_STATUS  = "https://api.whisper-api.com/status/{task_id}"
POLL_INTERVAL   = 1.5   # seconds between polls
POLL_TIMEOUT    = 90.0  # give up after this many seconds


@router.post("")
async def transcribe(
    file: Annotated[UploadFile, File(...)],
    user: Annotated[dict, Depends(get_current_user)],
    x_whisper_key: Annotated[str | None, Header()] = None,
):
    if not x_whisper_key:
        raise HTTPException(status_code=400, detail="X-Whisper-Key header required")

    audio_bytes = await file.read()

    async with httpx.AsyncClient(timeout=POLL_TIMEOUT + 10) as client:
        # ── 1. Submit ────────────────────────────────────────────────────────
        try:
            submit = await client.post(
                WHISPER_SUBMIT,
                headers={"X-API-Key": x_whisper_key},
                files={"file": (file.filename or "audio.webm", audio_bytes, file.content_type or "audio/webm")},
                data={"language": "uk", "format": "json", "model_size": "large-v2"},
            )
        except httpx.RequestError as exc:
            logger.error("Whisper submit failed: %s", exc)
            raise HTTPException(status_code=502, detail=f"Whisper API unreachable: {exc}")

        if not submit.is_success:
            logger.error("Whisper submit error %s: %s", submit.status_code, submit.text[:200])
            raise HTTPException(status_code=submit.status_code, detail=submit.text[:500])

        body = submit.json()

        # If the API returned text directly (synchronous mode), return it
        if body.get("text") is not None:
            return {"text": body["text"]}

        task_id = body.get("task_id")
        if not task_id:
            raise HTTPException(status_code=502, detail=f"Unexpected Whisper response: {body}")

        # ── 2. Poll until completed ──────────────────────────────────────────
        deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(POLL_INTERVAL)
            try:
                status_resp = await client.get(
                    WHISPER_STATUS.format(task_id=task_id),
                    headers={"X-API-Key": x_whisper_key},
                )
            except httpx.RequestError as exc:
                logger.warning("Whisper poll error: %s", exc)
                continue

            if not status_resp.is_success:
                continue

            status_body = status_resp.json()
            job_status = status_body.get("status", "")

            if job_status == "completed":
                result = status_body.get("result") or status_body.get("text") or ""
                return {"text": result}

            if job_status in ("failed", "error"):
                err = status_body.get("error") or "Transcription failed"
                raise HTTPException(status_code=500, detail=err)

            # still "queued" or "processing" — keep polling

        raise HTTPException(status_code=504, detail="Whisper transcription timed out")
