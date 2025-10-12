import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";

const WEEK_ORDER = [1, 2, 3, 4, 5, 6, 0]; // Monday first

function isoToUTCDate(iso) {
  return new Date(`${iso}T00:00:00Z`);
}

function dateToISO(date) {
  return date.toISOString().slice(0, 10);
}

function addDaysISO(iso, amount) {
  const date = isoToUTCDate(iso);
  date.setUTCDate(date.getUTCDate() + amount);
  return dateToISO(date);
}

function startOfMonthISO(iso) {
  const date = isoToUTCDate(iso);
  date.setUTCDate(1);
  return dateToISO(date);
}

function addMonthsISO(iso, amount) {
  const date = isoToUTCDate(iso);
  date.setUTCMonth(date.getUTCMonth() + amount, 1);
  return dateToISO(date);
}

function compareISO(a, b) {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

const FALLBACK_LABELS = {
  previous: "Previous month",
  next: "Next month",
  loading: "Loading availability…",
};

export default function CalendarPicker({
  id,
  locale,
  month,
  onMonthChange,
  minDate,
  selectedDate,
  onSelectDate,
  getDateState,
  loading = false,
  timeZone = "Europe/Berlin",
  labels = {},
}) {
  const mergedLabels = { ...FALLBACK_LABELS, ...labels };

  const monthDate = useMemo(() => isoToUTCDate(month), [month]);

  const monthFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        month: "long",
        year: "numeric",
        timeZone,
      }),
    [locale, timeZone]
  );

  const weekdayFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        weekday: "short",
        timeZone,
      }),
    [locale, timeZone]
  );

  const weekdayLabels = useMemo(() => {
    const referenceMonday = new Date(Date.UTC(2024, 0, 1)); // Monday
    return WEEK_ORDER.map((offset) => {
      const date = new Date(referenceMonday);
      const diff = (offset + 7 - 1) % 7; // offset from Monday
      date.setUTCDate(referenceMonday.getUTCDate() + diff);
      return weekdayFormatter.format(date);
    });
  }, [weekdayFormatter]);

  const startOfGrid = useMemo(() => {
    const firstOfMonth = isoToUTCDate(month);
    const offset = (firstOfMonth.getUTCDay() + 6) % 7; // convert Sunday=0 -> Monday=0
    firstOfMonth.setUTCDate(firstOfMonth.getUTCDate() - offset);
    return dateToISO(firstOfMonth);
  }, [month]);

  const days = useMemo(
    () => Array.from({ length: 42 }, (_, index) => addDaysISO(startOfGrid, index)),
    [startOfGrid]
  );

  const dayLabelFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
        timeZone,
      }),
    [locale, timeZone]
  );

  const dayEntries = useMemo(() => {
    return days.map((iso) => {
      const outside = startOfMonthISO(iso) !== month;
      const state = outside ? { disabled: true, outside: true } : getDateState(iso);
      return { iso, outside, state };
    });
  }, [days, getDateState, month]);

  const dayEntryMap = useMemo(() => {
    const map = new Map();
    dayEntries.forEach((entry) => {
      map.set(entry.iso, entry);
    });
    return map;
  }, [dayEntries]);

  const firstEnabledEntry = useMemo(
    () => dayEntries.find((entry) => !entry.state.disabled && !entry.outside),
    [dayEntries]
  );

  const selectedEntry = useMemo(() => dayEntryMap.get(selectedDate || ""), [dayEntryMap, selectedDate]);

  const initialFocus = useMemo(() => {
    if (selectedEntry && !selectedEntry.state.disabled && !selectedEntry.outside) {
      return selectedEntry.iso;
    }
    return firstEnabledEntry?.iso || null;
  }, [firstEnabledEntry, selectedEntry]);

  const [focusDate, setFocusDate] = useState(initialFocus);

  useEffect(() => {
    setFocusDate(initialFocus);
  }, [initialFocus]);

  const requestFrameRef = useRef(null);
  if (!requestFrameRef.current) {
    requestFrameRef.current =
      typeof window !== "undefined" && window.requestAnimationFrame
        ? window.requestAnimationFrame.bind(window)
        : (callback) => setTimeout(callback, 16);
  }

  const buttonRefs = useRef(new Map());

  const focusButton = useCallback(
    (iso, attempt = 0) => {
      if (!iso) return;
      const schedule = requestFrameRef.current;
      schedule(() => {
        const node = buttonRefs.current.get(iso);
        if (node) {
          node.focus();
        } else if (attempt < 4) {
          focusButton(iso, attempt + 1);
        }
      });
    },
    []
  );

  const changeMonth = useCallback(
    (delta) => {
      const nextMonth = addMonthsISO(month, delta);
      if (nextMonth !== month) {
        onMonthChange?.(nextMonth);
      }
    },
    [month, onMonthChange]
  );

  const handleSelect = useCallback(
    (iso, state) => {
      if (state.disabled) return;
      onSelectDate?.(iso);
      setFocusDate(iso);
    },
    [onSelectDate]
  );

  const handleKeyDown = useCallback(
    (event, entry) => {
      const { iso } = entry;
      const moveFocus = (step) => {
        let candidate = iso;
        for (let i = 0; i < 42; i += 1) {
          candidate = addDaysISO(candidate, step);
          if (compareISO(candidate, minDate) < 0) {
            if (step < 0) {
              return false;
            }
            continue;
          }
          if (startOfMonthISO(candidate) !== month) {
            return false;
          }
          const candidateEntry = dayEntryMap.get(candidate);
          if (!candidateEntry) {
            return false;
          }
          if (!candidateEntry.state.disabled && !candidateEntry.outside) {
            setFocusDate(candidate);
            focusButton(candidate);
            return true;
          }
        }
        return false;
      };

      switch (event.key) {
        case "ArrowRight":
          event.preventDefault();
          moveFocus(1);
          break;
        case "ArrowLeft":
          event.preventDefault();
          moveFocus(-1);
          break;
        case "ArrowDown":
          event.preventDefault();
          moveFocus(7);
          break;
        case "ArrowUp":
          event.preventDefault();
          moveFocus(-7);
          break;
        case "Home": {
          event.preventDefault();
          const weekday = (isoToUTCDate(iso).getUTCDay() + 6) % 7;
          if (weekday === 0) {
            setFocusDate(iso);
            focusButton(iso);
          } else {
            moveFocus(-weekday);
          }
          break;
        }
        case "End": {
          event.preventDefault();
          const weekday = (isoToUTCDate(iso).getUTCDay() + 6) % 7;
          if (weekday === 6) {
            setFocusDate(iso);
            focusButton(iso);
          } else {
            moveFocus(6 - weekday);
          }
          break;
        }
        case "PageUp":
          event.preventDefault();
          changeMonth(-1);
          break;
        case "PageDown":
          event.preventDefault();
          changeMonth(1);
          break;
        case "Enter":
        case " ":
          event.preventDefault();
          if (!entry.state.disabled) {
            handleSelect(iso, entry.state);
          }
          break;
        case "Escape":
          event.preventDefault();
          event.currentTarget.blur();
          break;
        default:
          break;
      }
    },
    [changeMonth, dayEntryMap, focusButton, handleSelect, minDate, month]
  );

  const monthLabel = monthFormatter.format(monthDate);

  const validFocusIso = useMemo(() => {
    if (!focusDate) return null;
    const entry = dayEntryMap.get(focusDate);
    if (entry && !entry.state.disabled && !entry.outside) {
      return focusDate;
    }
    return null;
  }, [dayEntryMap, focusDate]);

  const tabStopIso = useMemo(() => {
    if (validFocusIso) return validFocusIso;
    if (selectedEntry && !selectedEntry.state.disabled && !selectedEntry.outside) {
      return selectedEntry.iso;
    }
    return firstEnabledEntry?.iso || null;
  }, [firstEnabledEntry, selectedEntry, validFocusIso]);

  const weeks = useMemo(() => {
    const chunked = [];
    for (let index = 0; index < dayEntries.length; index += 7) {
      chunked.push(dayEntries.slice(index, index + 7));
    }
    return chunked;
  }, [dayEntries]);

  const hasMountedRef = useRef(false);
  useEffect(() => {
    if (hasMountedRef.current && tabStopIso) {
      focusButton(tabStopIso, 1);
    }
    hasMountedRef.current = true;
  }, [focusButton, tabStopIso]);

  const noFocusable = tabStopIso === null;

  return (
    <div className="calendar" id={id} aria-label={monthLabel}>
      <div className="calendar-header">
        <button
          type="button"
          className="calendar-nav"
          onClick={() => changeMonth(-1)}
          aria-label={mergedLabels.previous}
        >
          ‹
        </button>
        <div className="calendar-title" aria-live="polite">
          {monthLabel}
        </div>
        <button
          type="button"
          className="calendar-nav"
          onClick={() => changeMonth(1)}
          aria-label={mergedLabels.next}
        >
          ›
        </button>
      </div>
      {loading && <div className="calendar-loading">{mergedLabels.loading}</div>}
      <div className="calendar-weekdays" role="row">
        {weekdayLabels.map((label) => (
          <div key={label} className="calendar-weekday" role="columnheader">
            {label}
          </div>
        ))}
      </div>
      <div className="calendar-grid" role="grid" aria-readonly="true">
        {weeks.map((week, weekIndex) => (
          <div key={`week-${weekIndex}`} className="calendar-week" role="row">
            {week.map((entry, dayIndex) => {
              const { iso, outside, state } = entry;
              const isSelected = selectedDate === iso;
              const isTabStop = !state.disabled && !outside && tabStopIso === iso;
              let tabIndex = isTabStop ? 0 : -1;
              if (noFocusable && weekIndex === 0 && dayIndex === 0) {
                tabIndex = 0;
              }
              const labelParts = [dayLabelFormatter.format(isoToUTCDate(iso))];
              if (state.reason) {
                labelParts.push(state.reason);
              } else if (state.info) {
                labelParts.push(state.info);
              }
              const ariaLabel = labelParts.join(" — ");
              const title = state.reason || state.info || undefined;

              return (
                <div key={iso} className="calendar-cell" role="gridcell" aria-selected={isSelected}>
                  <button
                    type="button"
                    ref={(node) => {
                      if (node) {
                        buttonRefs.current.set(iso, node);
                      } else {
                        buttonRefs.current.delete(iso);
                      }
                    }}
                    className={`calendar-day${isSelected ? " is-selected" : ""}${state.disabled ? " is-disabled" : ""}${outside ? " is-outside" : ""}`}
                    onClick={() => handleSelect(iso, state)}
                    onKeyDown={(event) => handleKeyDown(event, entry)}
                    onFocus={() => setFocusDate(iso)}
                    disabled={state.disabled}
                    tabIndex={tabIndex}
                    aria-label={ariaLabel}
                    title={title}
                  >
                    <span className="calendar-day-number">{Number(iso.slice(-2))}</span>
                    {!state.disabled && state.free > 0 && (
                      <span className="calendar-day-info">{state.free}</span>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
