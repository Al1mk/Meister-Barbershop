import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import "./HeroSection.css";

const HERO_IMAGES = [
  "/images/1.jpg",
  "/images/2.jpg",
  "/images/3.jpg"
];

export default function HeroSection() {
  const { t } = useTranslation();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prevIndex) => 
        (prevIndex + 1) % HERO_IMAGES.length
      );
    }, 4000); // Change image every 4 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <section className="hero">
      <div className="hero-text">
        <h2 className="hero-subtitle">{t("home.badge")}</h2>
        <h1 className="hero-title">{t("home.title")}</h1>
        <p className="hero-desc">
          {t("home.subtitle")}
        </p>
      </div>

      <div className="hero-image">
        <div className="hero-slideshow">
          {HERO_IMAGES.map((img, index) => (
            <img
              key={img}
              src={img}
              alt="Meister Barbershop Interior"
              className={`hero-slide ${index === currentImageIndex ? 'active' : ''}`}
              loading={index === 0 ? "eager" : "lazy"}
            />
          ))}
        </div>
      </div>

      <div className="hero-buttons">
        <a href="/booking" className="btn-primary">{t("home.bookCta")}</a>
        <a href="/location" className="btn-secondary">{t("home.locationCta")}</a>
      </div>
    </section>
  );
}
