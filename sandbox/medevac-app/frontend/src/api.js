const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8011";
const WS_BASE =
  import.meta.env.VITE_WS_BASE_URL ||
  API_BASE.replace(/^http:\/\//, "ws://").replace(/^https:\/\//, "wss://");

function buildHeaders(token, idempotencyKey) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  return headers;
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = payload?.detail || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return payload;
}

export function getWsUrl(token) {
  const encoded = encodeURIComponent(token || "");
  return `${WS_BASE}/ws/events?access_token=${encoded}`;
}

export function health() {
  return request("/health", { method: "GET" });
}

export function getPositions(token) {
  return request("/positions", {
    method: "GET",
    headers: buildHeaders(token),
  });
}

export function getCases(token) {
  return request("/cases", {
    method: "GET",
    headers: buildHeaders(token),
  });
}

export function createCase(payload, token, idempotencyKey) {
  return request("/cases", {
    method: "POST",
    headers: buildHeaders(token, idempotencyKey),
    body: JSON.stringify(payload),
  });
}

export function getRecommendation(caseId, token) {
  return request(`/cases/${caseId}/recommendation`, {
    method: "GET",
    headers: buildHeaders(token),
  });
}

export function commitRecommendation(caseId, token, idempotencyKey) {
  return request(`/cases/${caseId}/commit`, {
    method: "POST",
    headers: buildHeaders(token, idempotencyKey),
  });
}
