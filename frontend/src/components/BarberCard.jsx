import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "./BarberCard.css";

export default function BarberCard({ barber, selected, onSelect, onBook }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const displayName = barber?.name || "";
  const photo = barber?.image || barber?.photo || "";
  const languages = barber?.languages || [];

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
      <div className="barber-avatar">
        {photo && (
          <img
            className="barber-photo"
            src={photo}
            alt={`${displayName} – Barber`}
            loading="lazy"
            decoding="async"
            width="200"
            height="200"
          />
        )}
      </div>
      <div className="barber-info">
        <div className="barber-name">{displayName}</div>
        {languages.length > 0 && (
          <div className="barber-langs">
            {languages.map((lang) => (
              <span key={lang} className="lang-pill">
                {lang}
              </span>
            ))}
          </div>
        )}
        <button className="barber-book-btn" onClick={handleBook}>
          {t("booking.book", "Book")}
        </button>
      </div>
    </div>
  );
}
