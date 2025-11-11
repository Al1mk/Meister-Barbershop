import React from "react";
import { useTranslation } from "react-i18next";
import "./BarberCard.css";

export default function BarberCard({ 
  name, 
  image, 
  languages = [],
  barber,
  selected,
  onSelect,
  onBook
}) {
  const { t } = useTranslation();
  
  // Support two modes: simple display (team page) or booking selection
  const isBookingMode = Boolean(barber);
  const displayName = isBookingMode ? barber.displayName || name : name;
  const displayImage = isBookingMode ? (barber.image || image) : image;
  const displayLanguages = isBookingMode ? (barber.languages || languages) : languages;
  
  const cardClass = isBookingMode 
    ? `barber-card barber-card-booking ${selected ? 'barber-card-selected' : ''}`
    : 'barber-card';
    
  const handleClick = isBookingMode && onSelect ? onSelect : undefined;
  
  return (
    <div 
      className={cardClass} 
      role="listitem" 
      aria-label={`Barber ${displayName}`}
      onClick={handleClick}
      style={{ cursor: isBookingMode ? 'pointer' : 'default' }}
    >
      {displayImage && (
        <img
          src={displayImage}
          alt={`${displayName} – Barber`}
          className="barber-photo"
          loading="lazy"
          width="320"
          height="400"
        />
      )}
      <div className="barber-info">
        <div className="barber-name">{displayName}</div>
        {displayLanguages && displayLanguages.length > 0 && (
          <div className="barber-langs" aria-label="Languages">
            {displayLanguages.map((lng) => (
              <span key={lng} className="lang-pill">{lng}</span>
            ))}
          </div>
        )}
        {isBookingMode && onBook && (
          <button 
            className="barber-book-btn"
            onClick={(e) => { e.stopPropagation(); onBook(); }}
            disabled={!selected}
          >
            {t("booking.barbers.book")}
          </button>
        )}
      </div>
    </div>
  );
}
