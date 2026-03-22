import { useEffect, useMemo, useState } from "react";
import {
  commitRecommendation,
  createCase,
  getCases,
  getPositions,
  getRecommendation,
  getWsUrl,
  health,
} from "./api";

const TOKENS = {
  admin: "dev-admin-token",
  dispatcher: "dev-dispatcher-token",
  medic: "dev-medic-token",
};

function uid() {
  return `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
}

function toUpperName(value) {
  return String(value || "").replaceAll("_", " ").toUpperCase();
}

export default function App() {
  const [role, setRole] = useState(localStorage.getItem("medevac.role") || "dispatcher");
  const [token, setToken] = useState(localStorage.getItem("medevac.token") || TOKENS.dispatcher);

  const [positions, setPositions] = useState([]);
  const [cases, setCases] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [recommendation, setRecommendation] = useState(null);

  const [conn, setConn] = useState("offline");
  const [lastEvent, setLastEvent] = useState("-");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    localStorage.setItem("medevac.role", role);
  }, [role]);

  useEffect(() => {
    localStorage.setItem("medevac.token", token);
  }, [token]);

  async function loadAll(caseIdHint) {
    try {
      setError("");
      const [h, p, c] = await Promise.all([health(), getPositions(token), getCases(token)]);
      setConn(h?.ok ? "online" : "degraded");
      setPositions(Array.isArray(p) ? p : []);
      setCases(Array.isArray(c) ? c : []);

      const preferredCaseId = caseIdHint || activeCaseId || (c?.[0] && c[0].id);
      if (preferredCaseId) {
        const rec = await getRecommendation(preferredCaseId, token);
        setActiveCaseId(preferredCaseId);
        setRecommendation(rec);
      }
    } catch (e) {
      setConn("offline");
      setError(e.message || "Connection error");
    }
  }

  useEffect(() => {
    loadAll();
    const timer = setInterval(() => loadAll(), 7000);
    return () => clearInterval(timer);
  }, [token]);

  useEffect(() => {
    if (!token) return undefined;

    const socket = new WebSocket(getWsUrl(token));
    let pingTimer = null;

    socket.onopen = () => {
      setConn("online");
      pingTimer = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send("ping");
      }, 15000);
    };

    socket.onmessage = (evt) => {
      setLastEvent(evt.data || "event");
      loadAll();
    };

    socket.onclose = () => {
      if (pingTimer) clearInterval(pingTimer);
      setConn((prev) => (prev === "online" ? "degraded" : prev));
    };

    return () => {
      if (pingTimer) clearInterval(pingTimer);
      socket.close();
    };
  }, [token]);

  const activeCase = useMemo(() => {
    return cases.find((item) => item.id === activeCaseId) || cases[0] || null;
  }, [cases, activeCaseId]);

  const needs = useMemo(() => activeCase?.needs || [], [activeCase]);

  const decisions = useMemo(() => {
    if (!recommendation?.plan) return [];
    return recommendation.plan.filter((row) => row.position_id !== null);
  }, [recommendation]);

  const shortages = useMemo(() => {
    if (!recommendation?.plan) return [];
    return recommendation.plan.filter((row) => row.position_id === null);
  }, [recommendation]);

  async function handleCreateCase() {
    setBusy(true);
    try {
      const payload = {
        x: 2,
        y: 3,
        needs: [
          { item_name: "hemostatic", qty: 5 },
          { item_name: "bandage", qty: 3 },
        ],
      };
      const created = await createCase(payload, token, `case-${uid()}`);
      await loadAll(created.case_id);
    } catch (e) {
      setError(e.message || "Create case failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm() {
    if (!activeCase?.id) return;
    setBusy(true);
    try {
      await commitRecommendation(activeCase.id, token, `commit-${activeCase.id}-${uid()}`);
      await loadAll(activeCase.id);
    } catch (e) {
      setError(e.message || "Commit failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleAnnounce() {
    if (!activeCase || decisions.length === 0) return;
    const lines = decisions.map((d) => `${d.position}: ${d.qty} ${d.item_name}`).join("; ");
    const text = `CASE ${activeCase.id}: ${lines}`;
    await navigator.clipboard.writeText(text);
    setLastEvent("announcement copied");
  }

  async function handleRefreshDecision() {
    if (!activeCase?.id) return;
    setBusy(true);
    try {
      const rec = await getRecommendation(activeCase.id, token);
      setRecommendation(rec);
      setLastEvent("decision recalculated");
    } catch (e) {
      setError(e.message || "Refresh failed");
    } finally {
      setBusy(false);
    }
  }

  function roleColor(value) {
    if (value === "dispatcher") return "#dfaa4f";
    if (value === "admin") return "#7ac7ff";
    return "#85c96d";
  }

  return (
    <div className="app-bg">
      <div className="mobile-card">
        <header className="head-row">
          <button className="icon-btn" aria-label="back">&lt;</button>
          <div>
            <div className="title">АЗОВ / ПОЛЕВИЙ КОНТУР</div>
            <div className="subtitle">TACTICAL DECISION NODE</div>
          </div>
          <div className="head-actions">
            <button className="icon-btn" onClick={handleCreateCase} disabled={busy}>+</button>
            <button className="icon-btn" onClick={() => setLastEvent("voice mode placeholder")}>
              mic
            </button>
          </div>
        </header>

        <section className="state-strip">
          <div>
            <span className="label">STATE:</span>
            <span className={`status ${conn}`}>{conn}</span>
          </div>
          <div className="mini-line">last: {lastEvent}</div>
        </section>

        <section className="panel">
          <div className="panel-title">ACTIVE CASE</div>
          <div className="line">GRID B3 / DIST: 5 KM</div>
          <div className="line">ID: {activeCase?.id || "none"}</div>
        </section>

        <section className="section">
          <div className="section-title">NEEDS</div>
          {(needs.length ? needs : [{ item_name: "none", qty: 0 }]).map((n, idx) => (
            <div className="row-box" key={`${n.item_name}-${idx}`}>
              <span>{toUpperName(n.item_name)}</span>
              <strong>x{n.qty}</strong>
            </div>
          ))}
        </section>

        <section className="section">
          <div className="section-title">DECISION</div>
          {decisions.length === 0 && <div className="row-box muted">No dispatch plan</div>}
          {decisions.map((d, idx) => (
            <div className="row-box" key={`${d.position}-${idx}`}>
              <span>
                {d.position} {" -> "} {d.qty} {toUpperName(d.item_name)}
              </span>
              <span className="km">{d.distance} km</span>
            </div>
          ))}
          {shortages.map((d, idx) => (
            <div className="row-box warn" key={`s-${idx}`}>
              <span>NOT ENOUGH {toUpperName(d.item_name)}</span>
              <strong>x{d.qty}</strong>
            </div>
          ))}
        </section>

        <section className="section">
          <div className="section-title">ACTION PANEL</div>
          <div className="btn-grid">
            <button className="action-btn" onClick={handleAnnounce} disabled={busy || decisions.length === 0}>
              Оголосити
            </button>
            <button className="action-btn" onClick={handleRefreshDecision} disabled={busy || !activeCase}>
              Редагувати
            </button>
            <button className="action-btn danger" onClick={handleConfirm} disabled={busy || !activeCase}>
              Підтвердити
            </button>
          </div>
        </section>

        <section className="section">
          <div className="section-title">POSITIONS SNAPSHOT</div>
          <div className="pill-grid">
            {positions.map((p) => {
              const total = (p.items || []).reduce((acc, i) => acc + Number(i.qty || 0), 0);
              return (
                <div className="pill" key={p.id}>
                  <span className="dot" />
                  <span>{toUpperName(p.name)}</span>
                  <strong>{total}</strong>
                </div>
              );
            })}
          </div>

          <div className="bars">
            {positions.map((p) => {
              const total = (p.items || []).reduce((acc, i) => acc + Number(i.qty || 0), 0);
              const width = Math.max(8, Math.min(100, total));
              return (
                <div className="bar-row" key={`bar-${p.id}`}>
                  <span>{toUpperName(p.name)}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="section compact">
          <div className="section-title">ACCESS</div>
          <div className="controls">
            <label>
              Role
              <select
                value={role}
                onChange={(e) => {
                  const nextRole = e.target.value;
                  setRole(nextRole);
                  setToken(TOKENS[nextRole]);
                }}
                style={{ borderColor: roleColor(role) }}
              >
                <option value="dispatcher">dispatcher</option>
                <option value="medic">medic</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <label>
              Bearer token
              <input
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Bearer token"
              />
            </label>
          </div>
          {error && <div className="error">{error}</div>}
        </section>
      </div>
    </div>
  );
}
