import React, { useState, useCallback, useMemo, useId } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "./BarberCard.css";

/**
 * Get initials from name for fallback avatar
 */
function getInitials(name) {
  if (!name) {return "?";}
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Generate responsive image sources for WebP
 */
function getResponsiveImageSources(imagePath) {
  if (!imagePath) {return null;}

  // Extract base path without extension
  const basePath = imagePath.replace(/\.(jpg|jpeg|png)$/i, "");

  return {
    webp: {
      "1x": `${basePath}.webp`,
      "2x": `${basePath}@2x.webp`,
    },
    fallback: imagePath,
  };
}

export default function BarberCard({ barber, selected, onSelect, onBook, isBookingMode = false }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const nameId = useId();
  const langsId = useId();

  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  // Data integrity: validate barber object
  const displayName = barber?.name || "";
  const barberId = barber?.id;
  const slug = barber?.slug || displayName.toLowerCase();
  const imagePath = barber?.image || barber?.photo || "";
  const languages = Array.isArray(barber?.languages) ? barber.languages : [];

  // Runtime assertion for data integrity
  if (process.env.NODE_ENV !== "production" && isBookingMode && !barberId) {
    console.error("[BarberCard] Missing barber ID in booking mode:", barber);
  }

  // Get initials for fallback
  const initials = useMemo(() => getInitials(displayName), [displayName]);

  // Get responsive image sources
  const imageSources = useMemo(() => getResponsiveImageSources(imagePath), [imagePath]);

  // Localize language names
  const localizeLanguage = useCallback(
    (lang) => {
      const key = `languages.${lang.toLowerCase()}`;
      return t(key, lang);
    },
    [t]
  );

  const handleImageLoad = useCallback(() => {
    setImageLoading(false);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
    setImageLoading(false);
    // Log to console (can be replaced with Sentry)
    console.warn(`[BarberCard] Image failed to load for ${displayName}:`, imagePath);
  }, [displayName, imagePath]);

  const handleCardClick = useCallback(() => {
    if (typeof onSelect === "function") {
      onSelect();
    }
  }, [onSelect]);

  const handleBookClick = useCallback(
    (event) => {
      event.stopPropagation();

      if (typeof onSelect === "function") {
        onSelect();
      }

      if (typeof onBook === "function") {
        onBook();
      } else if (barberId) {
        navigate("/booking", { state: { barberId } });
      } else {
        navigate("/booking");
      }
    },
    [barberId, navigate, onBook, onSelect]
  );

  const showFallback = imageError || !imageSources;

  return (
    <div
      className={`barber-card ${selected ? "barber-card--selected" : ""}`}
      role="group"
      aria-labelledby={nameId}
      onClick={isBookingMode ? handleCardClick : undefined}
      style={{ cursor: isBookingMode ? "pointer" : "default" }}
    >
      <div className="barber-avatar" aria-hidden="true">
        {imageLoading && !showFallback && <div className="barber-avatar-skeleton" />}

        {!showFallback && imageSources ? (
          <picture>
            <source
              type="image/webp"
              srcSet={`${imageSources.webp["1x"]} 1x, ${imageSources.webp["2x"]} 2x`}
            />
            <img
              className={`barber-photo ${imageLoading ? "barber-photo--loading" : ""}`}
              src={imageSources.fallback}
              alt={`${displayName} – barber portrait`}
              loading="lazy"
              decoding="async"
              width="192"
              height="192"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </picture>
        ) : (
          <div className="barber-avatar-fallback" aria-label={`${displayName} initials`}>
            {initials}
          </div>
        )}
      </div>

      <div className="barber-info">
        <div id={nameId} className="barber-name">
          {displayName}
        </div>

        {languages.length > 0 && (
          <ul
            id={langsId}
            className="barber-langs"
            aria-label={t("booking.barbers.languagesLabel", "Languages spoken")}
          >
            {languages.map((lang) => (
              <li key={lang} className="lang-pill">
                {localizeLanguage(lang)}
              </li>
            ))}
          </ul>
        )}

        <button
          className="barber-book-btn"
          onClick={handleBookClick}
          aria-label={t("booking.barbers.bookWithLabel", { name: displayName }, `Book with ${displayName}`)}
        >
          {t("booking.barbers.book", "Book")}
        </button>
      </div>
    </div>
  );
}
