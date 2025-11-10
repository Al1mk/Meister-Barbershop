import { useEffect, useMemo, useRef, useState } from "react";
import "./ImageSlider.css";

// Only include images that exist (1-5 for now, can add 6-10 later)
const SOURCES = [
  "/images/1.jpg",
  "/images/2.jpg",
  "/images/3.jpg",
  "/images/4.jpg",
  "/images/5.jpg",
];

const INTERVAL_MS = 10000; // 10 seconds
const XFADE_MS = 1000;     // 1 second crossfade

export default function MeisterCard() {
  const images = useMemo(() => SOURCES, []);

  useEffect(() => {
    images.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  }, [images]);

  const [active, setActive] = useState(0);
  const [fading, setFading] = useState(false);
  const [layers, setLayers] = useState([
    { key: 0, bg: images[0] },
    { key: 1, bg: images[1] },
  ]);
  const nextIdxRef = useRef(1);

  useEffect(() => {
    const t = setInterval(() => {
      const next = nextIdxRef.current % images.length;
      const hidden = (active + 1) % 2;

      setLayers((prev) => {
        const copy = [...prev];
        copy[hidden] = { ...copy[hidden], bg: images[next], key: next };
        return copy;
      });

      setTimeout(() => {
        setFading(true);
        setTimeout(() => {
          setFading(false);
          setActive(hidden);
          nextIdxRef.current = next + 1;
        }, XFADE_MS);
      }, 20);
    }, INTERVAL_MS);

    return () => clearInterval(t);
  }, [active, images]);

  return (
    <div className="meister-card-wrapper">
      <div
        key={layers[0].key}
        className={`slide-layer ${active === 0 ? "is-top" : "is-bottom"} ${fading ? "fade-blur-out" : "fade-blur-in"}`}
        style={{ backgroundImage: `url(${layers[0].bg})` }}
      />
      <div
        key={layers[1].key}
        className={`slide-layer ${active === 1 ? "is-top" : "is-bottom"} ${fading ? "fade-blur-in" : "fade-blur-out"}`}
        style={{ backgroundImage: `url(${layers[1].bg})` }}
      />
      <div className="card-content">
        <div className="brand-title">
          MEISTER<br />BARBERSHOP
        </div>
      </div>
    </div>
  );
}
