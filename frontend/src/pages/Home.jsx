import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ReviewsCarousel from "../components/ReviewsCarousel.jsx";
import HeroSection from "../components/HeroSection.jsx";

const DEFAULT_DESTINATION = {
  lat: "49.595217",
  lng: "11.0048712",
};

const getDestinationParam = () => {
  const placeId = import.meta.env.VITE_SHOP_PLACE_ID;
  const lat = import.meta.env.VITE_SHOP_LAT;
  const lng = import.meta.env.VITE_SHOP_LNG;
  if (placeId) {
    return "destination=place_id:" + encodeURIComponent(placeId);
  }
  if (lat && lng) {
    return "destination=" + encodeURIComponent(lat + "," + lng);
  }
  return "destination=" + encodeURIComponent(DEFAULT_DESTINATION.lat + "," + DEFAULT_DESTINATION.lng);
};

export default function Home() {
  const { t } = useTranslation();
  const features = useMemo(() => ["quality", "speed", "hygiene"], []);
  const featureRefs = useRef([]);
  const offerRef = useRef(null);
  const [directionsUrl, setDirectionsUrl] = useState(() => {
    const destination = getDestinationParam();
    const travelMode = "travelmode=driving";
    return "https://www.google.com/maps/dir/?api=1&" + destination + "&" + travelMode;
  });

  return (
    <div className="container">
      <HeroSection />

      <div ref={offerRef} className="student-offer reveal-item" role="status">
        <div className="student-offer__content">
          <div className="student-offer__title">{t("home.studentOffer.title")}</div>
          <div className="student-offer__subtitle">{t("home.studentOffer.subtitle")}</div>
          <div className="student-offer__note">{t("home.studentOffer.note")}</div>
        </div>
      </div>

      <ReviewsCarousel />

      <div className="grid grid-3" style={{ marginTop: 24 }}>
        {features.map((f, idx) => (
          <div key={f} ref={(el) => (featureRefs.current[idx] = el)} className="card-feature reveal-item">
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div className="icon" style={{ background: "var(--bronze)", borderRadius: "50%", width: 48, height: 48, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
                {idx === 0 ? "⭐" : idx === 1 ? "⚡" : "🧼"}
              </div>
              <div>
                <h3 style={{ margin: 0 }}>{t("home.features." + f + ".title")}</h3>
                <p style={{ margin: 0, fontSize: 14, color: "#888" }}>{t("home.features." + f + ".desc")}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="map-container" id="map">
        <h2 style={{ textAlign: "center", marginBottom: 24 }}>{t("home.map.title")}</h2>
        <iframe
          title={t("home.map.title")}
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d647.9456318!2d11.0022963!3d49.5952204!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47a1501441d61667%3A0x32aba2711ff76f1e!2sMeister%20Barbershop!5e0!3m2!1sen!2sde!4v1234567890"
          width="100%"
          height="450"
          style={{ border: 0, borderRadius: 12 }}
          allowFullScreen
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
        />
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <a href={directionsUrl} target="_blank" rel="noopener noreferrer" className="btn">{t("home.map.cta")}</a>
        </div>
      </div>
    </div>
  );
}
