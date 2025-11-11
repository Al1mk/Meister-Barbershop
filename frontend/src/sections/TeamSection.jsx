import React from "react";
import { team } from "../data/team";
import BarberCard from "../components/BarberCard";
import "./TeamSection.css";

export default function TeamSection() {
  return (
    <section id="team" className="team-section" aria-label="Our Team">
      <h2 className="team-title">Unser Team</h2>
      <div className="team-grid" role="list">
        {team.map((barber) => (
          <BarberCard key={barber.slug} barber={barber} />
        ))}
      </div>
    </section>
  );
}
