import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ReviewsCarousel from "../components/ReviewsCarousel.jsx";
import HeroSection from "../components/HeroSection.jsx";
import TeamSection from "../sections/TeamSection.jsx";
import MapSection from "../sections/MapSection.jsx";

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

      <TeamSection />

      <MapSection />
    </div>
  );
}
