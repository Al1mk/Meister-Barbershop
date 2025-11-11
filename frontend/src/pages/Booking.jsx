import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";

import { getBarbers, getSlots, createAppointment, getAvailability } from "../lib/api.js";
import { team } from "../data/team.js";
import BarberCard from "../components/BarberCard.jsx";
import TimeSlotPicker from "../components/TimeSlotPicker.jsx";
import CalendarPicker from "../components/CalendarPicker.jsx";

const NAME_MAP = {
  "جواد": "Javad",
  "ایمان": "Iman",
  "علی": "Ali",
  "احسان": "Ehsan",
};

const TIME_ZONE = "Europe/Berlin";
const SERVICE_DURATION = { haircut: 30, hair_beard: 45 };
const SERVICE_ORDER = ["haircut", "hair_beard"];
const DEFAULT_SERVICE = "haircut";

function normalizeBarber(barber) {
  if (!barber) {
    return barber;
  }
  const trimmedName = typeof barber.name === "string" ? barber.name.trim() : "";
  const displayName = NAME_MAP[trimmedName] || trimmedName;
  const initial = displayName ? displayName.charAt(0).toUpperCase() : "";
  return { ...barber, name: trimmedName, displayName, displayInitial: initial };
}

function enrichBarberWithTeamData(barber) {
  if (!barber || !barber.displayName) {return barber;}
  const slug = barber.displayName.toLowerCase();
  const teamMember = team.find(t => t.slug === slug);
  if (teamMember) {
    return { ...barber, image: teamMember.image, languages: teamMember.languages };
  }
  return barber;
}

function isoToUTCDate(value) {
  return new Date(`${value}T00:00:00Z`);
}

function dateToISO(date) {
  return date.toISOString().slice(0, 10);
}

function normalizeToBerlinISO(value) {
  if (!value) {return "";}
  if (typeof value === "string" && value.length >= 10) {
    return value.slice(0, 10);
  }
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    const formatter = new Intl.DateTimeFormat("en-CA", {
      timeZone: TIME_ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    return formatter.format(value);
  }
  return "";
}

function isoTodayInBerlin() {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(new Date());
}

function isoTomorrowInBerlin() {
  const todayIso = isoTodayInBerlin();
  const date = isoToUTCDate(todayIso);
  date.setUTCDate(date.getUTCDate() + 1);
  return dateToISO(date);
}

function startOfMonthISO(iso) {
  const date = isoToUTCDate(iso);
  date.setUTCDate(1);
  return dateToISO(date);
}

function endOfMonthISO(iso) {
  const date = isoToUTCDate(iso);
  date.setUTCMonth(date.getUTCMonth() + 1, 0);
  return dateToISO(date);
}

function addMonthsISO(iso, amount) {
  const date = isoToUTCDate(iso);
  date.setUTCMonth(date.getUTCMonth() + amount, 1);
  return dateToISO(date);
}

function compareISO(a, b) {
  if (a === b) {return 0;}
  return a < b ? -1 : 1;
}

function getWeekday(dateStr) {
  return isoToUTCDate(dateStr).getUTCDay();
}

function isSunday(dateStr) {
  return getWeekday(dateStr) === 0;
}

function allowedWeekdaysForBarber(barber) {
  // All barbers work Monday to Saturday (1-6)
  return new Set([1, 2, 3, 4, 5, 6]);
}

function isBarberAvailableOn(dateStr, barber) {
  const allowed = allowedWeekdaysForBarber(barber);
  const weekday = getWeekday(dateStr);
  return allowed.has(weekday);
}

function availabilityKey(monthIso, serviceType, duration) {
  return `${monthIso}|${serviceType || "custom"}|${duration}`;
}

function buildStartStamp(dateStr, slot) {
  const localString = `${dateStr}T${slot}:00`;
  const localDate = new Date(localString);
  if (Number.isNaN(localDate.getTime())) {
    throw new Error("invalid-time");
  }
  return localString;
}

export default function Booking() {
  const nav = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();

  const [step, setStep] = useState(1);
  const [barbers, setBarbers] = useState([]);
  const preselectedBarberId = location.state?.barberId ?? null;
  const [barberId, setBarberId] = useState(() => preselectedBarberId);
  const [serviceType, setServiceType] = useState(DEFAULT_SERVICE);

  const minDateISO = useMemo(() => isoTomorrowInBerlin(), []);
  const [calendarMonth, setCalendarMonth] = useState(() => startOfMonthISO(minDateISO));
  const [monthAvailability, setMonthAvailability] = useState({});
  const [loadingMonthKey, setLoadingMonthKey] = useState(null);
  const [availabilityError, setAvailabilityError] = useState("");

  const [dateStr, setDateStr] = useState("");
  const [slots, setSlots] = useState([]);
  const [slot, setSlot] = useState("");
  const [slotsLoading, setSlotsLoading] = useState(false);

  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const weekdays = t("weekdays", { returnObjects: true });
  const serviceDuration = useMemo(() => SERVICE_DURATION[serviceType] ?? SERVICE_DURATION.haircut, [serviceType]);

  const chosenBarber = useMemo(
    () => barbers.find((item) => item.id === barberId),
    [barbers, barberId]
  );

  const monthKey = availabilityKey(calendarMonth, serviceType, serviceDuration);
  const monthLoading = loadingMonthKey === monthKey && typeof monthAvailability[monthKey] === "undefined";

  const formTrimmed = {
    name: form.name.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
  };

  const canNext1 = Boolean(barberId);
  const canNext2 = Boolean(dateStr);

  const serviceOptions = useMemo(
    () => SERVICE_ORDER.map((type) => ({
      type,
      title: t(`booking.services.${type}.title`),
      durationLabel: t(`booking.services.${type}.duration`),
    })),
    [t]
  );

  useEffect(() => {
    let isActive = true;
    (async () => {
      try {
        const data = await getBarbers();
        if (!isActive) {return;}
        const normalized = Array.isArray(data) ? data.map((item) => enrichBarberWithTeamData(normalizeBarber(item))) : [];
        setBarbers(normalized);
        setError("");
      } catch (err) {
        if (!isActive) {return;}
        setError(t("booking.errors.loadBarbers"));
      }
    })();
    return () => {
      isActive = false;
    };
  }, [t]);

  useEffect(() => {
    setDateStr("");
    setSlot("");
    setSlots([]);
    setCalendarMonth(startOfMonthISO(minDateISO));
    setMonthAvailability({});
    setLoadingMonthKey(null);
    setAvailabilityError("");
  }, [barberId, minDateISO]);

  useEffect(() => {
    if (!preselectedBarberId) {return;}
    setBarberId(preselectedBarberId);
    setStep(2);
    nav(location.pathname, { replace: true, state: {} });
  }, [location.pathname, nav, preselectedBarberId]);

  useEffect(() => {
    setSlot("");
    setSlots([]);
    setMonthAvailability({});
    setLoadingMonthKey(null);
    setAvailabilityError("");
  }, [serviceType]);

  const getDateState = useCallback(
    (iso) => {
      if (!iso) {
        return { disabled: true };
      }

      if (compareISO(iso, minDateISO) < 0) {
        return { disabled: true, reason: t("booking.calendar.past") };
      }

      if (isSunday(iso)) {
        return { disabled: true, reason: t("booking.calendar.closed") };
      }

      if (!isBarberAvailableOn(iso, chosenBarber)) {
        return { disabled: true, reason: t("booking.calendar.barberUnavailable") };
      }

      const monthIso = startOfMonthISO(iso);
      const key = availabilityKey(monthIso, serviceType, serviceDuration);
      const availability = monthAvailability[key];
      if (availability === null) {
        return { disabled: false, info: t("booking.calendar.error") };
      }

      if (typeof availability === "undefined") {
        const pending = loadingMonthKey === key;
        return {
          disabled: false,
          pending,
          info: pending ? t("booking.calendar.loading") : undefined,
        };
      }

      const freeCount = availability[iso] ?? 0;
      if (freeCount === 0) {
        return { disabled: true, reason: t("booking.calendar.fullyBooked") };
      }

      return {
        disabled: false,
        free: freeCount,
        info: t("booking.calendar.available", { count: freeCount }),
      };
    },
    [chosenBarber, minDateISO, monthAvailability, loadingMonthKey, serviceType, serviceDuration, t]
  );

  const selectedDateState = useMemo(() => {
    const normalized = normalizeToBerlinISO(dateStr);
    return normalized ? getDateState(normalized) : { disabled: true };
  }, [dateStr, getDateState]);

  useEffect(() => {
    if (!barberId) {
      return;
    }

    const key = availabilityKey(calendarMonth, serviceType, serviceDuration);
    if (typeof monthAvailability[key] !== "undefined") {
      return;
    }

    let cancelled = false;
    setLoadingMonthKey(key);
    setAvailabilityError("");

    (async () => {
      try {
        const endIso = endOfMonthISO(calendarMonth);
        const data = await getAvailability(barberId, calendarMonth, endIso, {
          serviceType,
          durationMinutes: serviceDuration,
        });
        if (cancelled) {return;}
        const entries = {};
        if (data?.days?.length) {
          data.days.forEach((item) => {
            if (item?.date) {
              entries[item.date] = typeof item.free === "number" ? item.free : 0;
            }
          });
        }
        setMonthAvailability((prev) => ({ ...prev, [key]: entries }));
        setError("");
      } catch (err) {
        if (!cancelled) {
          setMonthAvailability((prev) => ({ ...prev, [key]: null }));
          setAvailabilityError(t("booking.calendar.error"));
          setError(t("booking.errors.loadSlots"));
        }
      } finally {
        if (!cancelled) {
          setLoadingMonthKey((current) => (current === key ? null : current));
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [barberId, calendarMonth, monthAvailability, serviceDuration, serviceType, t]);

  useEffect(() => {
    const normalizedDate = normalizeToBerlinISO(dateStr);
    if (!barberId || !normalizedDate || selectedDateState.disabled) {
      setSlots([]);
      setSlotsLoading(false);
      return;
    }

    let cancelled = false;
    setSlotsLoading(true);
    setError("");

    (async () => {
      try {
        console.log("📡 Fetching slots from /api/appointments/slots/ with params:", {
          barberId,
          date: normalizedDate,
          serviceType,
          durationMinutes: serviceDuration
        });
        const data = await getSlots(barberId, normalizedDate, {
          serviceType,
          durationMinutes: serviceDuration,
        });
        if (cancelled) {return;}
        console.log("✅ Slots fetched successfully:", data);
        setSlots(Array.isArray(data.slots) ? data.slots : []);
      } catch (err) {
        if (!cancelled) {
          console.error("❌ Failed to fetch slots:", err);
          setSlots([]);
          setError(t("booking.errors.loadSlots"));
        }
      } finally {
        if (!cancelled) {
          setSlotsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [barberId, dateStr, selectedDateState.disabled, serviceDuration, serviceType, t]);

  const formatDate = useCallback(
    (value) => {
      try {
        return new Intl.DateTimeFormat(i18n.language, {
          dateStyle: "medium",
        }).format(new Date(`${value}T00:00:00`));
      } catch (err) {
        return value;
      }
    },
    [i18n.language]
  );

  const formatTime = useCallback(
    (value) => {
      try {
        return new Intl.DateTimeFormat(i18n.language, {
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date(`1970-01-01T${value}:00`));
      } catch (err) {
        return value;
      }
    },
    [i18n.language]
  );

  useEffect(() => {
    if (!dateStr) {return;}
    const normalized = normalizeToBerlinISO(dateStr);
    if (!normalized) {return;}
    const state = getDateState(normalized);
    if (state.disabled) {
      setDateStr("");
      setSlot("");
      setSlots([]);
    }
  }, [getDateState, chosenBarber, serviceType]);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const { name, email, phone } = formTrimmed;
      if (!name || !email || !phone || !slot || !dateStr) {
        throw new Error("missing-fields");
      }
      const start_at = buildStartStamp(dateStr, slot);
      const payload = {
        barber: barberId,
        start_at,
        service_type: serviceType,
        duration_minutes: serviceDuration,
        customer: { name, email, phone },
      };
      await createAppointment(payload);
      nav("/thanks");
    } catch (err) {
      if (err.message === "missing-fields") {
        setError(t("booking.errors.missingFields"));
      } else if (err.message === "invalid-time") {
        setError(t("booking.errors.generic"));
      } else {
        setError(err.message || t("booking.errors.generic"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="booking-section" className="container">
      <h2 style={{ color: "var(--bronze)" }}>{t("booking.title")}</h2>
      <div className="help">{t("booking.step", { current: step, total: 3 })}</div>

      {step === 1 && (
        <div className="barber-card-grid">
          {barbers.map((b) => (
            <BarberCard
              key={b.id}
              barber={b}
              selected={barberId === b.id}
              onSelect={() => setBarberId(b.id)}
              onBook={() => setStep(2)}
            />
          ))}
        </div>
      )}

      {step === 2 && (
        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <label className="label" htmlFor="booking-calendar">
            {t("booking.selectDateLabel")}
          </label>
          <CalendarPicker
            id="booking-calendar"
            locale={i18n.language}
            month={calendarMonth}
            onMonthChange={(nextMonth) => setCalendarMonth(nextMonth)}
            minDate={minDateISO}
            selectedDate={normalizeToBerlinISO(dateStr)}
            onSelectDate={(value) => {
              const normalized = normalizeToBerlinISO(value);
              setDateStr(normalized);
              setSlot("");
              if (normalized) {
                setCalendarMonth(startOfMonthISO(normalized));
              }
            }}
            getDateState={getDateState}
            loading={monthLoading}
            timeZone={TIME_ZONE}
            labels={{
              previous: t("booking.calendar.previousMonth"),
              next: t("booking.calendar.nextMonth"),
              loading: t("booking.calendar.loadingInline"),
            }}
          />
          <div className="help" style={{ marginTop: 8 }}>
            {dateStr && weekdays?.length
              ? t("booking.weekdayLabel", {
                  weekday: weekdays[getWeekday(dateStr)] ?? "",
                })
              : t("booking.calendar.hint")}
          </div>
          {dateStr && selectedDateState.info && !availabilityError && (
            <div className="help" style={{ marginTop: 4 }}>
              {selectedDateState.info}
            </div>
          )}
          {availabilityError && (
            <div className="help" style={{ marginTop: 8, color: "var(--danger)" }}>
              {availabilityError}
            </div>
          )}
        </div>
      )}

      {step === 3 && (
        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div className="card" style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label className="label">{t("booking.services.label")}</label>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {serviceOptions.map(({ type, title, durationLabel }) => {
                  const active = serviceType === type;
                  return (
                    <button
                      key={type}
                      type="button"
                      className={`btn ${active ? "" : "outline"}`}
                      onClick={() => setServiceType(type)}
                      aria-pressed={active}
                      style={{ flexDirection: "column", alignItems: "flex-start" }}
                    >
                      <span>{title}</span>
                      <span className="help">{durationLabel}</span>
                    </button>
                  );
                })}
              </div>
              <div className="help" style={{ marginTop: 8 }}>
                {t("booking.services.helper")}
              </div>
            </div>

            <div>
              <label className="label">{t("booking.availableSlots")}</label>
              {slotsLoading ? (
                <div className="help">{t("booking.calendar.loadingInline")}</div>
              ) : !dateStr ? (
                <div className="help">{t("booking.calendar.hint")}</div>
              ) : availabilityError ? (
                <div className="help" style={{ color: "var(--danger)" }}>
                  {availabilityError}
                </div>
              ) : slots.length ? (
                <TimeSlotPicker slots={slots} value={slot} onChange={setSlot} />
              ) : (
                <div className="help">{t("timeslot.empty")}</div>
              )}
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{t("booking.summary.title")}</div>
            <div className="help">
              {t("booking.summary.barber")}: {chosenBarber?.displayName || chosenBarber?.name || "-"}
            </div>
            <div className="help">
              {t("booking.summary.date")}: {dateStr ? formatDate(dateStr) : "-"}
            </div>
            <div className="help">
              {t("booking.summary.time")}: {slot ? formatTime(slot) : "-"}
            </div>
            <div className="help">
              {t("booking.summary.service")}: {t(`booking.services.${serviceType}.title`)}
            </div>

            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
              <label className="label">{t("booking.customer.name")}</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm((v) => ({ ...v, name: e.target.value }))}
              />
              <label className="label">{t("booking.customer.email")}</label>
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={(e) => setForm((v) => ({ ...v, email: e.target.value }))}
              />
              <label className="label">{t("booking.customer.phone")}</label>
              <input
                className="input"
                value={form.phone}
                onChange={(e) => setForm((v) => ({ ...v, phone: e.target.value }))}
              />
              <div className="help" style={{ marginTop: 4 }}>
                {t("booking.customer.helper")}
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        {step > 1 && (
          <button className="btn outline" onClick={() => setStep((s) => s - 1)}>
            {t("booking.buttons.previous")}
          </button>
        )}
        {step === 1 && (
          <button className="btn" disabled={!canNext1} onClick={() => setStep(2)}>
            {t("booking.buttons.next")}
          </button>
        )}
        {step === 2 && (
          <button className="btn" disabled={!canNext2 || selectedDateState.disabled} onClick={() => setStep(3)}>
            {t("booking.buttons.next")}
          </button>
        )}
        {step === 3 && (
          <button
            className="btn"
            onClick={handleSubmit}
            disabled={
              loading ||
              !formTrimmed.name ||
              !formTrimmed.email ||
              !formTrimmed.phone ||
              !slot ||
              slotsLoading
            }
          >
            {loading ? t("booking.loading") : t("booking.buttons.confirm")}
          </button>
        )}
      </div>

      {error && (
        <div className="error" style={{ marginTop: 10 }}>
          {error}
        </div>
      )}
    </div>
  );
}
