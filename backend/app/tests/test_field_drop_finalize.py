import uuid


def _auth_headers(user_id: str = "test-user", idem: str | None = None) -> dict[str, str]:
    headers = {
        "X-User-ID": user_id,
        "Content-Type": "application/json",
    }
    if idem:
        headers["Idempotency-Key"] = idem
    return headers


def _create_request(
    client,
    *,
    x: float = 1.0,
    y: float = 1.0,
    urgency: str = "high",
    radius_km: float = 50.0,
    required: list[dict] | None = None,
) -> str:
    payload = {
        "x": x,
        "y": y,
        "urgency": urgency,
        "radius_km": radius_km,
        "required": required or [{"item_name": "bandage", "qty": 1}],
    }
    res = client.post(
        "/api/v1/field-drop/requests",
        json=payload,
        headers=_auth_headers(idem=f"create-{uuid.uuid4()}"),
    )
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["status"] == "DRAFT"
    return body["id"]


def _commit_request(client, request_id: str, idem: str | None = None):
    return client.post(
        f"/api/v1/field-drop/requests/{request_id}/commit",
        json={},
        headers=_auth_headers(idem=idem or f"commit-{uuid.uuid4()}"),
    )


def _finalize_request(
    client,
    request_id: str,
    *,
    method: str = "RADIO",
    note: str | None = "підтвердили по рації",
    idem: str | None = None,
):
    return client.post(
        f"/api/v1/field-drop/requests/{request_id}/finalize",
        json={
            "result": "completed",
            "method": method,
            "note": note,
        },
        headers=_auth_headers(idem=idem or f"finalize-{uuid.uuid4()}"),
    )


def test_field_drop_finalize_fresh_from_dispatched(client):
    request_id = _create_request(
        client,
        required=[{"item_name": "bandage", "qty": 1}],
    )

    commit_res = _commit_request(client, request_id)
    assert commit_res.status_code == 200, commit_res.text
    commit_data = commit_res.json()["data"]
    assert commit_data["request_id"] == request_id
    assert commit_data["already_committed"] is False
    assert commit_data["request_status"] in {"DISPATCHED", "PARTIAL"}

    finalize_res = _finalize_request(
        client,
        request_id,
        method="RADIO",
        note="підтвердили по рації",
    )
    assert finalize_res.status_code == 200, finalize_res.text

    data = finalize_res.json()["data"]
    assert data["request_id"] == request_id
    assert data["ok"] is True
    assert data["previous_status"] in {"DISPATCHED", "PARTIAL"}
    assert data["request_status"] == "COMPLETED"
    assert data["finalized_by"] == "test-user"
    assert data["method"] == "RADIO"
    assert data["note"] == "підтвердили по рації"
    assert data["finalized_at"] is not None


def test_field_drop_finalize_repeat_is_idempotent(client):
    request_id = _create_request(
        client,
        required=[{"item_name": "bandage", "qty": 1}],
    )

    commit_res = _commit_request(client, request_id, idem="commit-repeat-case")
    assert commit_res.status_code == 200, commit_res.text

    first_res = _finalize_request(
        client,
        request_id,
        method="DISCORD",
        note="підтверджено в дискорді",
        idem="finalize-repeat-case",
    )
    assert first_res.status_code == 200, first_res.text
    first = first_res.json()["data"]
    assert first["request_status"] == "COMPLETED"
    assert first["method"] == "DISCORD"

    # replay same idempotency key
    second_res = _finalize_request(
        client,
        request_id,
        method="DISCORD",
        note="підтверджено в дискорді",
        idem="finalize-repeat-case",
    )
    assert second_res.status_code == 200, second_res.text
    second = second_res.json()["data"]

    assert second["request_id"] == request_id
    assert second["request_status"] == "COMPLETED"
    assert second["method"] == "DISCORD"
    assert second["finalized_by"] == "test-user"
    assert second["note"] == "підтверджено в дискорді"
    assert second["finalized_at"] == first["finalized_at"]


def test_field_drop_finalize_from_draft_returns_409(client):
    request_id = _create_request(
        client,
        required=[{"item_name": "bandage", "qty": 1}],
    )

    res = _finalize_request(
        client,
        request_id,
        method="MANUAL",
        note="не можна фіналізувати з draft",
    )
    assert res.status_code == 409, res.text
    body = res.json()
    assert "cannot be finalized" in body["detail"].lower()


def test_field_drop_finalize_from_failed_returns_409(client):
    # impossible item to force applied_count == 0 -> FAILED
    request_id = _create_request(
        client,
        required=[{"item_name": "nonexistent_finalize_test_item", "qty": 999999}],
    )

    commit_res = _commit_request(client, request_id)
    assert commit_res.status_code == 200, commit_res.text
    commit_data = commit_res.json()["data"]

    assert commit_data["request_id"] == request_id
    assert commit_data["already_committed"] is False
    assert commit_data["request_status"] == "FAILED"
    assert commit_data["applied"] == []
    assert commit_data["logs_created"] == 0

    finalize_res = _finalize_request(
        client,
        request_id,
        method="VOICE",
        note="не має права фіналізуватись після failed",
    )
    assert finalize_res.status_code == 409, finalize_res.text
    body = finalize_res.json()
    assert "cannot be finalized" in body["detail"].lower()
