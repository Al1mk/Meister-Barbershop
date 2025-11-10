import React from "react";
import "./BarberCard.css";

export default function BarberCard({ name, image, role, shortTag }) {
  return (
    <div className="barber-card">
      <img src={image} alt={`${name} – Barber`} className="barber-photo" loading="lazy" />
      <h3 className="barber-name">
        {name}
        {shortTag && <span className="barber-role">({shortTag})</span>}
      </h3>
      {role && <p className="barber-service">{role}</p>}
    </div>
  );
}
