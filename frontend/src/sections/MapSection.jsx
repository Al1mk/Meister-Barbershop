import React from "react";
import { useTranslation } from "react-i18next";
import "./MapSection.css";

/**
 * MapSection
 * - Title uses i18n: home.map.title
 * - CTA button uses i18n: home.map.cta
 * - Whole map is clickable via transparent overlay link → Google Maps
 * - Directions button opens Google Maps Directions in new tab
 * - Coordinates: 49.5897,11.0089 (Erlangen)
 * - Address: Hauptstraße 12, 91054 Erlangen
 */
export default function MapSection() {
  const { t } = useTranslation();
  const lat = 49.5897;
  const lng = 11.0089;

  const gmapsPlaceUrl = `https://www.google.com/maps/place/Hauptstraße+12,+91054+Erlangen,+Germany/@${lat},${lng},18z`;
  const gmapsDirectionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;

  // Embed map (kept generic; if you had a previous embed src, keep it here)
  const embedSrc = `https://www.google.com/maps?q=${lat},${lng}&z=16&output=embed`;

  return (
    <section id="map" className="map-section">
      <h2 className="map-title">{t("home.map.title")}</h2>

      <div className="map-wrap">
        {/* Transparent full-overlay link so clicking the map opens Google Maps */}
        <a
          className="map-overlay-link"
          href="https://www.google.com/maps/place/Hauptstraße+12,+91054+Erlangen,+Germany/@49.5897,11.0089,18z"
          target="_blank"
          rel="noopener noreferrer"
          aria-label={t('home.map.openInMaps', 'Open in Google Maps')}
          tabIndex="0"
          data-hint={t('home.map.hint', 'Open in Google Maps')}
        />
        <iframe
          className="map-iframe"
          src={embedSrc}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          aria-label="Google Map"
        />
      </div>

      <div className="map-cta-wrap">
        <a
          className="map-cta-btn map-cta"
          href={gmapsDirectionsUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          {t("home.map.cta")}
        </a>
      </div>
    </section>
  );
}
