import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { resolveMedia } from "../lib/api.js";
import usePrefersReducedMotion from "../hooks/usePrefersReducedMotion.js";
import { getBarberDetails } from "../data/barbers.js";

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

export default function BarberCard({ barber, selected, onSelect, onBook }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const prefersReducedMotion = usePrefersReducedMotion();

  const cardRef = useRef(null);
  const wrapperRef = useRef(null);
  const frameRef = useRef(null);

  const [isHovering, setIsHovering] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isTouchMode, setIsTouchMode] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    try {
      return (
        window.matchMedia("(hover: none)").matches ||
        window.matchMedia("(pointer: coarse)").matches ||
        window.innerWidth <= 900
      );
    } catch (_err) {
      return false;
    }
  });

  const displayName = barber?.displayName || barber?.name || "";
  const primaryInitial =
    barber?.displayInitial || (displayName ? displayName.charAt(0).toUpperCase() : "");
  const fallbackInitial =
    !primaryInitial && barber?.name ? barber.name.trim().charAt(0).toUpperCase() : "";
  const initials = primaryInitial || fallbackInitial || "?";
  const photo = resolveMedia(barber?.photo);

  const [loaded, setLoaded] = useState(false);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    setLoaded(false);
    setErrored(false);
  }, [photo]);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return undefined;
    const hoverQuery = window.matchMedia("(hover: none)");
    const pointerQuery = window.matchMedia("(pointer: coarse)");
    const update = () => {
      setIsTouchMode(
        hoverQuery.matches || pointerQuery.matches || window.innerWidth <= 900
      );
    };
    update();
    hoverQuery.addEventListener("change", update);
    pointerQuery.addEventListener("change", update);
    window.addEventListener("resize", update);
    return () => {
      hoverQuery.removeEventListener("change", update);
      pointerQuery.removeEventListener("change", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  const details = useMemo(() => getBarberDetails(displayName), [displayName]);
  const tagline = t(details.taglineKey);
  const availability = t(details.availabilityKey);
  const defaultDescription = t("booking.barberCard.description");

  const infoId = useMemo(() => {
    if (typeof barber?.id !== "undefined" && barber?.id !== null) {
      return `barber-${barber.id}`;
    }
    const base = (displayName || "barber")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return `barber-${base || "card"}`;
  }, [barber?.id, displayName]);

  const showSkeleton = photo && !errored && !loaded;

  const resetTilt = useCallback(() => {
    if (!cardRef.current) return;
    cardRef.current.style.setProperty("--tiltX", "0deg");
    cardRef.current.style.setProperty("--tiltY", "0deg");
  }, []);

  useEffect(() => {
    if (prefersReducedMotion) {
      resetTilt();
    }
  }, [prefersReducedMotion, resetTilt]);

  const applyTilt = useCallback(
    (clientX, clientY) => {
      if (!cardRef.current || prefersReducedMotion) return;
      const rect = cardRef.current.getBoundingClientRect();
      const offsetX = clientX - (rect.left + rect.width / 2);
      const offsetY = clientY - (rect.top + rect.height / 2);
      const rotateX = clamp((-offsetY / (rect.height / 2)) * 5, -5, 5);
      const rotateY = clamp((offsetX / (rect.width / 2)) * 5, -5, 5);
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      frameRef.current = requestAnimationFrame(() => {
        if (!cardRef.current) return;
        cardRef.current.style.setProperty("--tiltX", `${rotateX.toFixed(2)}deg`);
        cardRef.current.style.setProperty("--tiltY", `${rotateY.toFixed(2)}deg`);
      });
    },
    [prefersReducedMotion]
  );

  useEffect(
    () => () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    },
    []
  );

  const handleSelect = useCallback(() => {
    if (typeof onSelect === "function") {
      onSelect();
    }
  }, [onSelect]);

  const handleBook = useCallback(() => {
    handleSelect();
    if (typeof onBook === "function") {
      onBook();
    } else if (barber?.id) {
      navigate("/booking", { state: { barberId: barber.id } });
    } else {
      navigate("/booking");
    }
  }, [barber?.id, handleSelect, navigate, onBook]);

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === " " || event.key === "Spacebar" || event.key === "Enter") {
        event.preventDefault();
        handleSelect();
      }
      if (event.key === "Escape") {
        event.preventDefault();
        setIsHovering(false);
        setIsFocused(false);
      }
    },
    [handleSelect]
  );

  const handleFocus = useCallback(() => {
    setIsFocused(true);
  }, []);

  const handleBlur = useCallback((event) => {
    if (
      wrapperRef.current &&
      event.relatedTarget &&
      wrapperRef.current.contains(event.relatedTarget)
    ) {
      return;
    }
    setIsFocused(false);
  }, []);

  const showDetails = isTouchMode || isHovering || isFocused || selected;
  const bookTabIndex = showDetails ? 0 : -1;

  return (
    <div
      ref={wrapperRef}
      className="barber-card-wrapper"
      onMouseEnter={() => !isTouchMode && setIsHovering(true)}
      onMouseLeave={() => {
        setIsHovering(false);
        if (!prefersReducedMotion) resetTilt();
      }}
      onFocusCapture={handleFocus}
      onBlurCapture={handleBlur}
      onMouseMove={(event) => {
        if (!isTouchMode) {
          applyTilt(event.clientX, event.clientY);
        }
      }}
    >
      <div
        ref={cardRef}
        role="button"
        tabIndex={0}
        aria-pressed={selected}
        aria-labelledby={`${infoId}-title`}
        aria-describedby={`${infoId}-details`}
        className={`card barber-card${showDetails ? " is-active" : ""}${
          selected ? " is-selected" : ""
        }`}
        onClick={handleSelect}
        onKeyDown={handleKeyDown}
      >
        <div className="barber-card__content">
          <div className="avatar-shell">
            {showSkeleton && <div className="avatar-skeleton" aria-hidden="true" />}
            {photo && !errored && (
              <img
                src={photo}
                loading="lazy"
                alt={displayName || t("booking.barberCard.altFallback")}
                className={`avatar-img ${loaded ? "is-visible" : ""}`}
                onLoad={() => setLoaded(true)}
                onError={() => {
                  setErrored(true);
                  setLoaded(true);
                }}
              />
            )}
            {(!photo || errored) && <span className="avatar-initial">{initials}</span>}
          </div>
          <div className="barber-card__meta">
            <span id={`${infoId}-title`} className="barber-card__name">
              {displayName}
            </span>
            <span className="barber-card__description">{defaultDescription}</span>
          </div>
        </div>

        <div
          id={`${infoId}-details`}
          className={`barber-card__info${showDetails ? " is-visible" : ""}`}
          aria-hidden={!showDetails && !isTouchMode}
        >
          <div className="barber-card__info-text">
            <span className="barber-card__info-availability">{availability}</span>
            <span className="barber-card__info-divider" aria-hidden="true">
              •
            </span>
            <span className="barber-card__info-tagline">{tagline}</span>
          </div>
          <button
            type="button"
            className="btn barber-card__book"
            onClick={(event) => {
              event.stopPropagation();
              handleBook();
            }}
            tabIndex={bookTabIndex}
            aria-label={t("booking.barbers.bookLabel", { name: displayName })}
          >
            {t("booking.barbers.book")}
          </button>
        </div>
      </div>
    </div>
  );
}
