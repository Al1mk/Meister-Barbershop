import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ReviewsCarousel from "../components/ReviewsCarousel.jsx";
import MeisterCard from "../components/MeisterCard.jsx";

const DEFAULT_DESTINATION = {
  lat: "49.595217",
  lng: "11.0048712",
};

const getDestinationParam = () => {
  const placeId = import.meta.env.VITE_SHOP_PLACE_ID;
  const lat = import.meta.env.VITE_SHOP_LAT;
  const lng = import.meta.env.VITE_SHOP_LNG;
  if (placeId) {
    return `destination=place_id:${encodeURIComponent(placeId)}`;
  }
  if (lat && lng) {
    return `destination=${encodeURIComponent(`${lat},${lng}`)}`;
  }
  return `destination=${encodeURIComponent(`${DEFAULT_DESTINATION.lat},${DEFAULT_DESTINATION.lng}`)}`;
};

export default function Home() {
  const { t } = useTranslation();
  const features = useMemo(() => ["quality", "speed", "hygiene"], []);
  const featureRefs = useRef([]);
  const offerRef = useRef(null);
  const heroVisualRef = useRef(null);
  const prefersReducedMotionRef = useRef(false);
  const [directionsUrl, setDirectionsUrl] = useState(() => {
    const destination = getDestinationParam();
    const travelMode = "travelmode=driving";
    return `https://www.google.com/maps/dir/?api=1&${destination}&${travelMode}`;
  });

  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) {return;}
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => {
      prefersReducedMotionRef.current = mediaQuery.matches;
      setPrefersReducedMotion(mediaQuery.matches);
    };
    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);
    return () => mediaQuery.removeEventListener("change", updatePreference);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || prefersReducedMotion) {
      if (heroVisualRef.current) {
        heroVisualRef.current.style.transform = "translateY(0px)";
      }
      return;
    }
    const element = heroVisualRef.current;
    if (!element) {return;}
    let frame = null;
    let lastValue = 0;

    const clampOffset = () => {
      if (!element) {return;}
      const scrollY = window.scrollY || window.pageYOffset || 0;
      const maxOffset = window.innerWidth < 768 ? 12 : 20;
      const next = Math.min(maxOffset, scrollY * 0.12);
      if (Math.abs(next - lastValue) < 0.5) {return;}
      element.style.transform = `translateY(${next.toFixed(2)}px)`;
      lastValue = next;
    };

    const onScroll = () => {
      if (frame) {return;}
      frame = requestAnimationFrame(() => {
        frame = null;
        clampOffset();
      });
    };

    clampOffset();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) {cancelAnimationFrame(frame);}
      if (element) {element.style.transform = "";}
    };
  }, [prefersReducedMotion]);

  useEffect(() => {
    if (typeof window === "undefined") {return;}
    if (!navigator.geolocation) {return;}
    const destination = getDestinationParam();
    const travelMode = "travelmode=driving";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const origin = `origin=${encodeURIComponent(`${latitude},${longitude}`)}`;
        setDirectionsUrl(`https://www.google.com/maps/dir/?api=1&${destination}&${origin}&${travelMode}`);
      },
      () => {
        setDirectionsUrl(`https://www.google.com/maps/dir/?api=1&${destination}&${travelMode}`);
      },
      { enableHighAccuracy: true, timeout: 5000 }
    );
  }, []);

  useEffect(() => {
    const elements = [];
    featureRefs.current.forEach((el) => {
      if (el) {elements.push(el);}
    });
    if (offerRef.current) {
      elements.push(offerRef.current);
    }
    if (!elements.length) {return;}

    if (prefersReducedMotionRef.current) {
      elements.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2, rootMargin: "0px 0px -60px 0px" }
    );

    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [features.length, prefersReducedMotion]);

  const openDirections = useCallback(() => {
    if (!directionsUrl) {return;}
    window.open(directionsUrl, "_blank", "noopener,noreferrer");
  }, [directionsUrl]);

  const handleOverlayKey = useCallback(
    (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openDirections();
      }
    },
    [openDirections]
  );

  return (
    <div className="container">
      <div className="hero">
        <div style={{ flex: 1 }}>
          <span className="badge">{t("home.badge")}</span>
          <h2>{t("home.title")}</h2>
          <p>{t("home.subtitle")}</p>
          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <Link to="/booking" className="btn">{t("home.bookCta")}</Link>
            <a className="btn outline" href="#map">{t("home.locationCta")}</a>
          </div>
        </div>
        <div className="hero-visual" ref={heroVisualRef}>
          <MeisterCard />
        </div>
      </div>

      <div ref={offerRef} className="student-offer reveal-item" role="status">
        <div className="student-offer__content">
          <div className="student-offer__title">{t("home.studentOffer.title")}</div>
          <div className="student-offer__subtitle">{t("home.studentOffer.subtitle")}</div>
          <div className="student-offer__note">{t("home.studentOffer.note")}</div>
        </div>
      </div>

      <ReviewsCarousel />

      <div className="grid grid-3" style={{ marginTop: 24 }}>
        {features.map((key, index) => (
          <div
            ref={(el) => {
              featureRefs.current[index] = el;
            }}
            className="card feature-card reveal-item"
            key={key}
            style={{ padding: 16 }}
          >
            <div style={{ fontWeight: 700, color: "var(--bronze)" }}>{t(`home.features.${key}.title`)}</div>
            <div className="help">{t(`home.features.${key}.description`)}</div>
          </div>
        ))}
      </div>

      <div id="map" className="card map-card" style={{ marginTop: 24, overflow: "hidden", position: "relative" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid #1f1f1f" }}>
          <strong>{t("home.locationTitle")}:</strong> {t("home.locationDetail")}
        </div>
        <div className="map-frame-wrapper">
          <iframe
            title="Meister Location"
            width="100%"
            height="360"
            style={{ border: 0 }}
            loading="lazy"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
            src="https://www.google.com/maps?ll=49.595217,11.0048712&q=49.595217,11.0048712&z=19&hl=de&output=embed"
          />
          <button
            type="button"
            className="map-overlay"
            aria-label={t("home.directionsCta")}
            onClick={openDirections}
            onKeyDown={handleOverlayKey}
          />
        </div>
        <div className="map-actions">
          <a
            className="btn directions-cta"
            href={directionsUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("home.directionsCta")}
          </a>
        </div>
      </div>
    </div>
  );
}
