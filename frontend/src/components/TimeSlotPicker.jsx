import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";

export default function TimeSlotPicker({ slots, value, onChange }) {
  const { t, i18n } = useTranslation();

  const timeFormatter = useMemo(() => {
    try {
      return new Intl.DateTimeFormat(i18n.language, {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (e) {
      return null;
    }
  }, [i18n.language]);

  if (!slots?.length) {
    return <div className="help">{t("timeslot.empty")}</div>;
  }

  return (
    <div className="kiosk">
      {slots.map((slot) => {
        const active = value === slot;
        const formatted = timeFormatter
          ? timeFormatter.format(new Date(`1970-01-01T${slot}:00`))
          : slot;
        return (
          <button
            type="button"
            key={slot}
            className={`slot ${active ? "active" : ""}`}
            onClick={() => onChange(slot)}
          >
            {formatted}
          </button>
        );
      })}
    </div>
  );
}
