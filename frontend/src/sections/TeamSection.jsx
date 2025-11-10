import React from "react";
import { team } from "../data/team";
import BarberCard from "../components/BarberCard";
import "./TeamSection.css";

export default function TeamSection() {
  return (
    <section id="team" className="team-section">
      <h2 className="team-title">Unser Team</h2>
      <div className="team-grid">
        {team.map(member => (
          <BarberCard key={member.name} {...member} />
        ))}
      </div>
    </section>
  );
}
