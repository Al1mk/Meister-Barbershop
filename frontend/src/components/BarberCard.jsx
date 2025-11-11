import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { resolveMedia } from "../lib/api.js";
import { getBarberDetails } from "../data/barbers.js";
import "./BarberCard.css";

export default function BarberCard({ barber, selected, onSelect, onBook }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const displayName = barber?.name || "";
  const photo = resolveMedia(barber?.photo);
  const details = useMemo(() => getBarberDetails(displayName), [displayName]);
  const languages = details.languages || [];

  const handleBook = () => {
    if (typeof onSelect === "function") {
      onSelect();
    }
    if (typeof onBook === "function") {
      onBook();
    } else if (barber?.id) {
      navigate("/booking", { state: { barberId: barber.id } });
    } else {
      navigate("/booking");
    }
  };

  return (
    <div className="barber-card">
      {photo && (
        <img
          className="barber-photo"
          src={photo}
          alt={`${displayName} – Barber`}
          loading="lazy"
          decoding="async"
          width="800"
          height="1000"
          sizes="(max-width: 479px) 92vw, (max-width: 767px) 45vw, (max-width: 1023px) 30vw, 230px"
        />
      )}
      <div className="barber-info">
        <div className="barber-name">{displayName}</div>
        <div className="barber-langs">
          {languages.map((lang) => (
            <span key={lang} className="lang-pill">
              {lang}
            </span>
          ))}
        </div>
      </div>
      <button className="barber-book-btn" onClick={handleBook}>
        {t("booking.book", "Book")}
      </button>
    </div>
  );
}
