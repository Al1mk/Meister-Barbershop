import React, { useEffect, useMemo, useState } from "react";
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";

import {
  getBarbers,
  listTimeOff,
  createTimeOff,
  deleteTimeOff,
  fetchTimeOffConflicts,
  extractError,
} from "../lib/api.js";

const SESSION_KEY = "meister-admin-password";

function parseISOToDate(value) {
  if (!value) {return null;}
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
}

function formatDate(date) {
  return date.toLocaleDateString("en-CA");
}

function formatRangeLabel(start, end) {
  if (!start) {return "";}
  const endLabel = end ? formatDate(end) : formatDate(start);
  const startLabel = formatDate(start);
  return startLabel === endLabel ? startLabel : `${startLabel} → ${endLabel}`;
}

export default function AdminSchedule() {
  const [barbers, setBarbers] = useState([]);
  const [selectedBarberId, setSelectedBarberId] = useState(null);
  const [timeOffs, setTimeOffs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [password, setPassword] = useState(() => {
    if (typeof window === "undefined") {return "";}
    return window.sessionStorage.getItem(SESSION_KEY) || "";
  });
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [range, setRange] = useState({ from: undefined, to: undefined });
  const [reason, setReason] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);
  const [conflictsPreview, setConflictsPreview] = useState(null);
  const [conflictsPreviewError, setConflictsPreviewError] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [blockingConflicts, setBlockingConflicts] = useState(null);
  const [pendingForcePayload, setPendingForcePayload] = useState(null);

  useEffect(() => {
    let mounted = true;
    getBarbers()
      .then((items) => {
        if (!mounted) {return;}
        setBarbers(items);
        if (items.length && !selectedBarberId) {
          setSelectedBarberId(items[0].id);
        }
      })
      .catch((error) => {
        console.error(error);
        if (mounted) {
          setAuthError("Could not load barbers. Please refresh.");
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!barbers.length || !password || authorized) {return;}
    verifyPassword(password);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [barbers]);

  useEffect(() => {
    if (!authorized || !selectedBarberId) {return;}
    refreshTimeOffs(selectedBarberId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authorized, selectedBarberId]);

  useEffect(() => {
    if (!authorized || !password || !selectedBarberId) {
      setConflictsPreview(null);
      setConflictsPreviewError("");
      return;
    }
    if (!range?.from) {
      setConflictsPreview(null);
      setConflictsPreviewError("");
      return;
    }
    const fromDate = range.from;
    const toDate = range.to ?? range.from;
    let cancelled = false;
    setPreviewLoading(true);
    fetchTimeOffConflicts(
      {
        barber_id: selectedBarberId,
        start_date: formatDate(fromDate),
        end_date: formatDate(toDate),
      },
      password,
    )
      .then((data) => {
        if (cancelled) {return;}
        setConflictsPreview(data);
        setConflictsPreviewError("");
      })
      .catch((error) => {
        if (cancelled) {return;}
        setConflictsPreview(null);
        setConflictsPreviewError(error.message || "Could not check conflicts");
      })
      .finally(() => {
        if (!cancelled) {
          setPreviewLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [authorized, password, range, selectedBarberId]);

  async function verifyPassword(candidate) {
    if (!barbers.length) {return;}
    const barberId = selectedBarberId || barbers[0]?.id;
    if (!barberId) {return;}

    setVerifying(true);
    setAuthError("");
    try {
      await listTimeOff(barberId, candidate);
      setAuthorized(true);
      setPassword(candidate);
      setSelectedBarberId(barberId);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(SESSION_KEY, candidate);
      }
      setActionMessage("");
      setActionError("");
    } catch (error) {
      console.error(error);
      setAuthorized(false);
      setPassword("");
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(SESSION_KEY);
      }
      setAuthError("Password incorrect or server rejected access.");
    } finally {
      setVerifying(false);
    }
  }

  async function refreshTimeOffs(barberId) {
    if (!authorized || !password) {return;}
    setLoading(true);
    setActionError("");
    try {
      const records = await listTimeOff(barberId, password);
      setTimeOffs(records);
    } catch (error) {
      console.error(error);
      setActionError(error.message || "Failed to load time-off records");
    } finally {
      setLoading(false);
    }
  }

  function handlePasswordSubmit(event) {
    event.preventDefault();
    if (!passwordInput.trim()) {
      setAuthError("Password is required");
      return;
    }
    verifyPassword(passwordInput.trim());
  }

  function handleBarberSelect(barberId) {
    setSelectedBarberId(barberId);
    setRange({ from: undefined, to: undefined });
    setBlockingConflicts(null);
    setPendingForcePayload(null);
  }

  async function handleBlock(force = false) {
    if (!range?.from || !selectedBarberId) {return;}
    const fromDate = range.from;
    const toDate = range.to ?? range.from;
    const payload = {
      start_date: formatDate(fromDate),
      end_date: formatDate(toDate),
      reason: reason.trim(),
      force,
    };

    setSaving(true);
    setActionError("");
    setActionMessage("");
    setBlockingConflicts(null);
    setPendingForcePayload(null);

    try {
      const response = await createTimeOff(selectedBarberId, payload, password);
      if (response.ok) {
        setActionMessage("Blocked successfully.");
        setReason("");
        setRange({ from: undefined, to: undefined });
        setBlockingConflicts(null);
        setPendingForcePayload(null);
        await refreshTimeOffs(selectedBarberId);
        return;
      }
      if (response.status === 409) {
        setBlockingConflicts(response.data?.conflicts || null);
        setPendingForcePayload({ ...payload, force: true });
        setActionError(response.data?.detail || "Conflicts detected. Force to proceed?");
        return;
      }
      const message = extractError(response.data, "Unable to block time-off");
      setActionError(message);
    } catch (error) {
      console.error(error);
      setActionError(error.message || "Unable to save time-off");
    } finally {
      setSaving(false);
    }
  }

  async function handleForce() {
    if (!pendingForcePayload) {return;}
    await handleBlock(true);
    setPendingForcePayload(null);
  }

  async function handleDelete(timeOffId) {
    if (typeof window !== "undefined" && !window.confirm("Remove this time-off?")) {return;}
    setSaving(true);
    setActionError("");
    try {
      await deleteTimeOff(timeOffId, password);
      setActionMessage("Time-off removed.");
      await refreshTimeOffs(selectedBarberId);
    } catch (error) {
      console.error(error);
      setActionError(error.message || "Failed to delete time-off");
    } finally {
      setSaving(false);
    }
  }

  const modifiers = useMemo(() => {
    if (!timeOffs.length) {return {};}
    return {
      timeOff: timeOffs.map((record) => ({
        from: parseISOToDate(record.start_date),
        to: parseISOToDate(record.end_date),
      })),
    };
  }, [timeOffs]);

  const modifiersClassNames = useMemo(() => ({ timeOff: "timeoff-day" }), []);

  const selectedRangeLabel = range?.from ? formatRangeLabel(range.from, range.to ?? range.from) : "";

  if (!authorized) {
    return (
      <div className="admin-wrapper">
        <div className="admin-card">
          <h2>Admin Schedule Access</h2>
          <p>Enter the admin password to manage barber time-off.</p>
          <form onSubmit={handlePasswordSubmit} className="admin-login-form">
            <label htmlFor="admin-password">Password</label>
            <input
              id="admin-password"
              type="password"
              value={passwordInput}
              onChange={(event) => setPasswordInput(event.target.value)}
              placeholder="••••••"
              required
            />
            {authError && <div className="admin-error">{authError}</div>}
            <button type="submit" disabled={verifying}>
              {verifying ? "Verifying…" : "Unlock"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-wrapper">
      <aside className="admin-sidebar">
        <h2>Barbers</h2>
        <ul>
          {barbers.map((barber) => (
            <li key={barber.id}>
              <button
                type="button"
                className={barber.id === selectedBarberId ? "active" : ""}
                onClick={() => handleBarberSelect(barber.id)}
              >
                {barber.name}
              </button>
            </li>
          ))}
        </ul>
        {timeOffs.length > 0 && (
          <div className="admin-timeoff-list">
            <h3>Current blocks</h3>
            <ul>
              {timeOffs.map((record) => (
                <li key={record.id}>
                  <div>
                    <strong>{formatRangeLabel(parseISOToDate(record.start_date), parseISOToDate(record.end_date))}</strong>
                    {record.reason ? <span className="muted"> — {record.reason}</span> : null}
                  </div>
                  <button type="button" onClick={() => handleDelete(record.id)} disabled={saving}>
                    Unblock
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>
      <section className="admin-calendar">
        <header>
          <h2>Manage Time-Off</h2>
          {actionMessage && <div className="admin-success">{actionMessage}</div>}
          {actionError && <div className="admin-error">{actionError}</div>}
        </header>
        <DayPicker
          mode="range"
          selected={range}
          onSelect={setRange}
          disabled={{ before: new Date() }}
          modifiers={modifiers}
          modifiersClassNames={modifiersClassNames}
          numberOfMonths={2}
        />
        <div className="admin-controls">
          <div>
            <label htmlFor="timeoff-reason">Reason (optional)</label>
            <input
              id="timeoff-reason"
              type="text"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Vacation, training, etc."
            />
          </div>
          <div className="admin-control-row">
            <div>
              <strong>Selected:</strong> {selectedRangeLabel || "Select a range"}
            </div>
            <button
              type="button"
              onClick={() => handleBlock(false)}
              disabled={!range?.from || saving || loading}
            >
              Block selected
            </button>
            {pendingForcePayload && (
              <button type="button" className="force" onClick={handleForce} disabled={saving}>
                Force block
              </button>
            )}
          </div>
        </div>
        <div className="admin-conflicts">
          {previewLoading && <p className="muted">Checking conflicts…</p>}
          {conflictsPreviewError && <p className="admin-error">{conflictsPreviewError}</p>}
          {conflictsPreview && (conflictsPreview.appointments?.length || conflictsPreview.time_off?.length) ? (
            <div>
              <h3>Potential Conflicts</h3>
              {conflictsPreview.time_off?.length ? (
                <div>
                  <strong>Existing blocks:</strong>
                  <ul>
                    {conflictsPreview.time_off.map((item) => (
                      <li key={`timeoff-${item.id}`}>
                        {formatRangeLabel(parseISOToDate(item.start_date), parseISOToDate(item.end_date))} — {item.reason || "No reason"}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {conflictsPreview.appointments?.length ? (
                <div>
                  <strong>Appointments:</strong>
                  <ul>
                    {conflictsPreview.appointments.map((item) => (
                      <li key={`appt-${item.id}`}>
                        {new Date(item.start_at).toLocaleString()} — {item.customer?.name || "Guest"}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="muted">No conflicts detected for the selected range.</p>
          )}
          {blockingConflicts && (
            <div className="admin-warning">
              <h3>Conflicts found</h3>
              {blockingConflicts.time_off?.length ? (
                <div>
                  <strong>Existing blocks:</strong>
                  <ul>
                    {blockingConflicts.time_off.map((item) => (
                      <li key={`block-${item.id}`}>
                        {formatRangeLabel(parseISOToDate(item.start_date), parseISOToDate(item.end_date))}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {blockingConflicts.appointments?.length ? (
                <div>
                  <strong>Appointments to cancel:</strong>
                  <ul>
                    {blockingConflicts.appointments.map((item) => (
                      <li key={`block-appt-${item.id}`}>
                        {new Date(item.start_at).toLocaleString()} — {item.customer?.name || "Guest"}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
