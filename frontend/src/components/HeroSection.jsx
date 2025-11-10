import React, { useState, useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import "./HeroSection.css";

export default function HeroSection() {
  const { t } = useTranslation();
  
  const images = useMemo(
    () => [
      { base: "salon1", alt: "Meister Barbershop Interior 1" },
      { base: "salon2", alt: "Meister Barbershop Interior 2" },
      { base: "salon3", alt: "Meister Barbershop Interior 3" },
    ],
    []
  );

  const [index, setIndex] = useState(0);
  const [prev, setPrev] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const intervalRef = useRef(null);

  // Check for reduced motion preference
  const prefersReducedMotion = useMemo(() => {
    if (typeof window === 'undefined') {return false;}
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }, []);

  // Slideshow interval management
  useEffect(() => {
    // Don't start slideshow if reduced motion is preferred
    if (prefersReducedMotion) {
      return;
    }

    // Don't run interval if paused
    if (isPaused) {
      return;
    }

    intervalRef.current = setInterval(() => {
      setPrev(index);
      setIndex((i) => (i + 1) % images.length);
    }, 5000); // 5 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [images.length, index, isPaused, prefersReducedMotion]);

  // Handle tab visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPaused(document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return (
    <section className="hero">
      <div className="hero-text">
        <div className="hero-subtitle">Meister</div>
        <h1 className="hero-title">{t("home.title")}</h1>
        <p className="hero-desc">
          {t("home.subtitle")}
        </p>
        <div className="hero-buttons">
          <a href="/booking" className="btn-primary">{t("home.bookCta")}</a>
          <a href="/location" className="btn-secondary">{t("home.locationCta")}</a>
        </div>
      </div>

      <div className="hero-image slideshow">
        {images.map((img, i) => (
          <picture
            key={img.base}
            className={
              "slide" +
              (i === index ? " slide--active" : "") +
              (i === prev ? " slide--prev" : "")
            }
          >
            <source
              type="image/avif"
              srcSet={`/images/salon/${img.base}-480.avif 480w, /images/salon/${img.base}-768.avif 768w, /images/salon/${img.base}-1200.avif 1200w`}
              sizes="(max-width: 767px) 100vw, 50vw"
            />
            <source
              type="image/webp"
              srcSet={`/images/salon/${img.base}-480.webp 480w, /images/salon/${img.base}-768.webp 768w, /images/salon/${img.base}-1200.webp 1200w`}
              sizes="(max-width: 767px) 100vw, 50vw"
            />
            <img
              src={`/images/salon/${img.base}-1200.jpg`}
              srcSet={`/images/salon/${img.base}-480.jpg 480w, /images/salon/${img.base}-768.jpg 768w, /images/salon/${img.base}-1200.jpg 1200w`}
              sizes="(max-width: 767px) 100vw, 50vw"
              alt={img.alt}
              width="1200"
              height="1600"
              loading={i === 0 ? "eager" : "lazy"}
              decoding={i === 0 ? "sync" : "async"}
              fetchPriority={i === 0 ? "high" : undefined}
            />
          </picture>
        ))}
      </div>
    </section>
  );
}
