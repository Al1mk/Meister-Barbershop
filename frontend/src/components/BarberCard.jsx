import React from "react";
import "./BarberCard.css";

export default function BarberCard({ name, image, role }) {
  const displayName = name === "Ehsan"
    ? (
      <>
        Ehsan <span className="barber-role">(Chef)</span>
      </>
    )
    : name;

  return (
    <div className="barber-card">
      <img src={image} alt={name} className="barber-photo" />
      <h3 className="barber-name">{displayName}</h3>
      {role && <p className="barber-service">{role}</p>}
    </div>
  );
}
