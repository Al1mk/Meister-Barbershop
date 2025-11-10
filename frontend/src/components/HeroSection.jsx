import React from "react";
import { useTranslation } from "react-i18next";
import "./HeroSection.css";

export default function HeroSection() {
  const { t } = useTranslation();
  
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
        <img
          src="/images/salon-main.jpg"
          alt="Meister Barbershop Interior"
          loading="eager"
        />
      </div>

      <div className="hero-buttons">
        <a href="/booking" className="btn-primary">{t("home.bookCta")}</a>
        <a href="/location" className="btn-secondary">{t("home.locationCta")}</a>
      </div>
    </section>
  );
}
