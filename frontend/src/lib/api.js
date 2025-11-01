import i18n from "../i18n/index.js";

const DEFAULT_API_BASE = import.meta.env.PROD ? "/api" : "http://localhost:8000";
export const API_BASE = import.meta.env.VITE_API_BASE
  ? import.meta.env.VITE_API_BASE.replace(/\/+$/, "")
  : DEFAULT_API_BASE;

function buildUrl(path) {
  const base = import.meta.env.VITE_API_BASE || "/api";
  const joined = `${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  return new URL(joined, window.location.origin).toString();
}

async function parseResponse(response) {
  const raw = await response.text();
  let data = null;
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch (_err) {
      data = raw;
    }
  }
  return { data, raw };
}

function extractError(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data[0] ?? fallback;
  return (
    data.detail ??
    data.error ??
    (Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : undefined) ??
    (Array.isArray(data.start_at) ? data.start_at[0] : undefined) ??
    (Array.isArray(data.duration_minutes) ? data.duration_minutes[0] : undefined) ??
    (Array.isArray(data.service_type) ? data.service_type[0] : undefined) ??
    (Array.isArray(data.customer) ? data.customer[0] : undefined) ??
    fallback
  );
}

function buildAdminHeaders(password) {
  const token = btoa(`admin:${password ?? ""}`);
  return {
    Authorization: `Basic ${token}`,
  };
}

async function adminFetch(path, { method = "GET", body, password } = {}) {
  const headers = buildAdminHeaders(password);
  let payload;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const response = await fetch(buildUrl(path), {
    method,
    headers,
    body: payload,
  });
  const { data, raw } = await parseResponse(response);
  return { ok: response.ok, status: response.status, data, raw };
}

export async function getBarbers() {
  const response = await fetch(buildUrl("/barbers/"));
  if (!response.ok) throw new Error(i18n.t("booking.errors.loadBarbers"));
  return response.json();
}

export async function getSlots(barberId, dateISO, { serviceType, durationMinutes } = {}) {
  const url = new URL(buildUrl("/appointments/slots/"));
  url.searchParams.set("barber_id", barberId);
  url.searchParams.set("date", dateISO);
  if (serviceType) {
    url.searchParams.set("service_type", serviceType);
  }
  if (durationMinutes) {
    url.searchParams.set("duration_minutes", String(durationMinutes));
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(i18n.t("booking.errors.loadSlots"));
  return response.json();
}

export async function getAvailability(barberId, startISO, endISO, { serviceType, durationMinutes } = {}) {
  const url = new URL(buildUrl("/appointments/availability/"));
  url.searchParams.set("barber_id", barberId);
  url.searchParams.set("start", startISO);
  url.searchParams.set("end", endISO);
  if (serviceType) {
    url.searchParams.set("service_type", serviceType);
  }
  if (durationMinutes) {
    url.searchParams.set("duration_minutes", String(durationMinutes));
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(i18n.t("booking.errors.loadSlots"));
  return response.json();
}

export async function createAppointment(payload) {
  const response = await fetch(buildUrl("/appointments/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const { data, raw } = await parseResponse(response);

  if (!response.ok) {
    const fallback = i18n.t("booking.errors.generic");
    const message = extractError(data, fallback);
    throw new Error(message || raw || fallback);
  }

  return data;
}

export async function sendContact(payload) {
  const response = await fetch(buildUrl("/contact/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const { data, raw } = await parseResponse(response);

  if (!response.ok) {
    const fallback = i18n.t("contact.error");
    const message = extractError(data, fallback);
    throw new Error(message || raw || fallback);
  }

  return data;
}

export async function getReviews(lang) {
  const url = new URL(buildUrl("/reviews/"));
  if (lang) {
    url.searchParams.set("lang", lang);
  }
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(i18n.t("home.reviews.error"));
  return response.json();
}

export function resolveMedia(path) {
  if (!path) return null;
  return buildUrl(path);
}

export async function listTimeOff(barberId, password) {
  const { ok, data, raw } = await adminFetch(`/admin/barbers/${barberId}/timeoff`, { password });
  if (!ok) {
    const fallback = "Failed to load time-off";
    throw new Error(extractError(data, fallback) || raw || fallback);
  }
  return data;
}

export async function createTimeOff(barberId, payload, password) {
  return adminFetch(`/admin/barbers/${barberId}/timeoff`, {
    method: "POST",
    body: payload,
    password,
  });
}

export async function deleteTimeOff(timeOffId, password) {
  const { ok, data, raw } = await adminFetch(`/admin/timeoff/${timeOffId}`, {
    method: "DELETE",
    password,
  });
  if (!ok) {
    const fallback = "Failed to delete time-off";
    throw new Error(extractError(data, fallback) || raw || fallback);
  }
}

export async function fetchTimeOffConflicts(params, password) {
  const url = new URL(buildUrl("/admin/timeoff/conflicts"));
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, value);
    }
  });
  const { ok, data, raw } = await adminFetch(url.toString(), { password });
  if (!ok) {
    const fallback = "Failed to load conflicts";
    throw new Error(extractError(data, fallback) || raw || fallback);
  }
  return data;
}

export { extractError };
