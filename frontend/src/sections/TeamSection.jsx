import React, { useState, useEffect } from "react";
import { enrichBarbersWithMetadata } from "../data/team";
import { getBarbers } from "../lib/api";
import BarberCard from "../components/BarberCard";
import "./TeamSection.css";

export default function TeamSection() {
  const [barbers, setBarbers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isActive = true;

    (async () => {
      try {
        const apiBarbers = await getBarbers();
        if (!isActive) {return;}

        const enrichedBarbers = enrichBarbersWithMetadata(apiBarbers);
        setBarbers(enrichedBarbers);
        setError(null);
      } catch (err) {
        if (!isActive) {return;}
        console.error("[TeamSection] Failed to load barbers:", err);
        setError("Team konnte nicht geladen werden");
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    })();

    return () => {
      isActive = false;
    };
  }, []);

  if (loading) {
    return (
      <section id="team" className="team-section" aria-label="Our Team">
        <h2 className="team-title">Unser Team</h2>
        <div className="help" style={{ textAlign: "center", padding: "2rem" }}>
          Lädt...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id="team" className="team-section" aria-label="Our Team">
        <h2 className="team-title">Unser Team</h2>
        <div className="help" style={{ textAlign: "center", padding: "2rem", color: "var(--danger)" }}>
          {error}
        </div>
      </section>
    );
  }

  return (
    <section id="team" className="team-section" aria-label="Our Team">
      <h2 className="team-title">Unser Team</h2>
      <div className="team-grid" role="list">
        {barbers.map((barber) => (
          <BarberCard key={barber.id} barber={barber} />
        ))}
      </div>
    </section>
  );
}
