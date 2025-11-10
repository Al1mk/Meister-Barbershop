import React from "react";
import "./HeroSection.css";

export default function HeroSection() {
  return (
    <section className="hero">
      <div className="hero-text">
        <h2 className="hero-subtitle">Meister</h2>
        <h1 className="hero-title">Buche deinen nächsten Haarschnitt online</h1>
        <p className="hero-desc">
          Montag bis Samstag, jeweils einstündige Termine.
        </p>
      </div>

      <div className="hero-image">
        <img
          src="/images/hero/main.jpg"
          alt="Meister Barbershop Interior"
          loading="eager" fetchpriority="high"
        />
      </div>

      <div className="hero-buttons">
        <a href="/booking" className="btn-primary">Termin buchen</a>
        <a href="/location" className="btn-secondary">Standort anzeigen</a>
      </div>
    </section>
  );
}
