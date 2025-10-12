import React, {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
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
  const sheetRef = useRef(null);
  const bookButtonRef = useRef(null);
  const dragStartRef = useRef(null);
  const frameRef = useRef(null);
  const dragOffsetRef = useRef(0);

  const [isHovering, setIsHovering] = useState(false);
  const [focusInside, setFocusInside] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const [isTouchMode, setIsTouchMode] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    try {
      return (
        window.matchMedia("(hover: none)").matches ||
        window.matchMedia("(pointer: coarse)").matches
      );
    } catch (_err) {
      return false;
    }
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [modalActive, setModalActive] = useState(false);

  const headingId = useId();
  const availabilityId = useId();
  const popoverHeadingId = useId();
  const modalHeadingId = useId();

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

  const details = useMemo(() => getBarberDetails(displayName), [displayName]);
  const tagline = t(details.taglineKey);
  const availability = t(details.availabilityKey);

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

  const showPopover = !isTouchMode && (isHovering || focusInside);
  const liveAnnouncement = showPopover
    ? `${displayName}. ${availability}. ${tagline}`
    : "";

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

  useEffect(() => {
    dragOffsetRef.current = dragOffset;
  }, [dragOffset]);

  const openModal = useCallback(() => {
    if (!isTouchMode) return;
    setModalVisible(true);
    requestAnimationFrame(() => setModalActive(true));
  }, [isTouchMode]);

  const closeModal = useCallback(() => {
    setModalActive(false);
    setDragOffset(0);
    dragStartRef.current = null;
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (!modalVisible) return undefined;
    if (!modalActive) {
      const timeout = setTimeout(() => {
        setModalVisible(false);
      }, 300);
      return () => clearTimeout(timeout);
    }
    return undefined;
  }, [modalActive, modalVisible]);

  useEffect(() => {
    if (!modalVisible || !modalActive) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [modalActive, modalVisible]);

  useEffect(() => {
    if (!modalActive || !bookButtonRef.current) return undefined;
    const id = requestAnimationFrame(() => {
      bookButtonRef.current?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(id);
  }, [modalActive]);

  useEffect(() => {
    if (!showPopover && !modalActive) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        if (modalActive) {
          closeModal();
        }
        setIsHovering(false);
        setFocusInside(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [closeModal, modalActive, showPopover]);

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
    setIsHovering(false);
    setFocusInside(false);
    if (modalActive) {
      closeModal();
    }
  }, [barber?.id, closeModal, handleSelect, modalActive, navigate, onBook]);

  const handleCardClick = useCallback(() => {
    handleSelect();
    if (isTouchMode) {
      openModal();
    }
  }, [handleSelect, isTouchMode, openModal]);

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === " " || event.key === "Spacebar") {
        event.preventDefault();
        handleSelect();
      }
      if (event.key === "Enter") {
        event.preventDefault();
        if (isTouchMode) {
          openModal();
        } else {
          setFocusInside(true);
        }
      }
      if (event.key === "Escape") {
        event.preventDefault();
        setIsHovering(false);
        setFocusInside(false);
      }
    },
    [handleSelect, isTouchMode, openModal]
  );

  const handleFocus = useCallback(() => {
    setFocusInside(true);
  }, []);

  const handleBlur = useCallback((event) => {
    if (
      wrapperRef.current &&
      event.relatedTarget &&
      wrapperRef.current.contains(event.relatedTarget)
    ) {
      return;
    }
    setFocusInside(false);
  }, []);

  const handlePointerDown = useCallback(
    (event) => {
      if (!isTouchMode) return;
      if (event.pointerType === "mouse") return;
      dragStartRef.current = event.clientY;
      setIsDragging(true);
      sheetRef.current?.setPointerCapture?.(event.pointerId);
    },
    [isTouchMode]
  );

  const handlePointerMove = useCallback((event) => {
    if (dragStartRef.current === null) return;
    const delta = Math.max(0, event.clientY - dragStartRef.current);
    setDragOffset(delta);
  }, []);

  const handlePointerEnd = useCallback(
    (event) => {
      if (dragStartRef.current === null) return;
      const shouldClose = dragOffsetRef.current > 90;
      dragStartRef.current = null;
      setIsDragging(false);
      sheetRef.current?.releasePointerCapture?.(event.pointerId);
      if (shouldClose) {
        closeModal();
      } else {
        setDragOffset(0);
      }
    },
    [closeModal]
  );

  const handleOverlayClick = useCallback(
    (event) => {
      if (event.target === event.currentTarget) {
        closeModal();
      }
    },
    [closeModal]
  );

  const showInitial = !photo || errored;
  const showSkeleton = photo && !errored && !loaded;
  const cardClasses = ["card", "barber-card"];
  if (showPopover) cardClasses.push("is-active");
  if (selected) cardClasses.push("is-selected");

  const sheetClasses = ["barber-sheet"];
  if (modalActive) sheetClasses.push("is-open");
  if (isDragging) sheetClasses.push("dragging");

  const overlayClasses = ["barber-sheet-overlay"];
  if (modalActive) overlayClasses.push("is-open");

  const sheetStyle =
    modalActive || isDragging ? { transform: `translateY(${dragOffset}px)` } : undefined;

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
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {liveAnnouncement}
      </div>
      <div
        ref={cardRef}
        role="button"
        tabIndex={0}
        aria-pressed={selected}
        aria-haspopup={isTouchMode ? "dialog" : "true"}
        aria-expanded={isTouchMode ? modalActive : showPopover}
        aria-labelledby={headingId}
        aria-describedby={availabilityId}
        className={cardClasses.join(" ")}
        onClick={handleCardClick}
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
            {showInitial && <span className="avatar-initial">{initials}</span>}
          </div>
          <div className="barber-card__meta">
            <span id={headingId} className="barber-card__name">
              {displayName}
            </span>
            <span id={availabilityId} className="barber-card__availability">
              {availability}
            </span>
            <span className="barber-card__tagline">{tagline}</span>
          </div>
        </div>
      </div>

      {!isTouchMode && (
        <div
          className={`barber-popover${showPopover ? " is-visible" : ""}`}
          role="dialog"
          aria-modal="false"
          aria-labelledby={popoverHeadingId}
          tabIndex={-1}
        >
          <div className="barber-popover__header">
            <div className="barber-popover__thumb">
              {photo && !errored ? (
                <img src={photo} alt="" aria-hidden="true" />
              ) : (
                <span className="avatar-initial">{initials}</span>
              )}
            </div>
            <div>
              <div id={popoverHeadingId} className="barber-popover__name">
                {displayName}
              </div>
              <div className="barber-popover__body" style={{ margin: 0 }}>
                <span>
                  <strong>{t("booking.barbers.availabilityLabel")}:</strong> {availability}
                </span>
              </div>
            </div>
          </div>
          <div className="barber-popover__body">
            <span>
              <strong>{t("booking.barbers.taglineLabel")}:</strong> {tagline}
            </span>
          </div>
          <div className="barber-popover__actions">
            <button
              type="button"
              className="btn barber-card__button"
              onClick={handleBook}
              aria-label={t("booking.barbers.bookLabel", { name: displayName })}
            >
              {t("booking.barbers.book")}
            </button>
          </div>
        </div>
      )}

      {modalVisible &&
        createPortal(
          <div
            className={overlayClasses.join(" ")}
            role="presentation"
            onClick={handleOverlayClick}
          >
            <div
              ref={sheetRef}
              className={sheetClasses.join(" ")}
              role="dialog"
              aria-modal="true"
              aria-labelledby={modalHeadingId}
              aria-live="polite"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerEnd}
              onPointerCancel={handlePointerEnd}
              style={sheetStyle}
            >
              <div className="barber-sheet__handle" aria-hidden="true" />
              <div className="barber-sheet__header">
                <div className="barber-sheet__thumb">
                  {photo && !errored ? (
                    <img src={photo} alt="" aria-hidden="true" />
                  ) : (
                    <span className="avatar-initial">{initials}</span>
                  )}
                </div>
                <div>
                  <div id={modalHeadingId} className="barber-sheet__name">
                    {displayName}
                  </div>
                  <div className="barber-sheet__details">
                    <span>
                      <strong>{t("booking.barbers.availabilityLabel")}:</strong> {availability}
                    </span>
                    <span>
                      <strong>{t("booking.barbers.taglineLabel")}:</strong> {tagline}
                    </span>
                  </div>
                </div>
              </div>
              <div className="barber-sheet__actions">
                <button
                  ref={bookButtonRef}
                  type="button"
                  className="btn"
                  onClick={handleBook}
                  aria-label={t("booking.barbers.bookLabel", { name: displayName })}
                >
                  {t("booking.barbers.book")}
                </button>
                <button
                  type="button"
                  className="barber-sheet__close"
                  onClick={closeModal}
                >
                  {t("booking.buttons.previous")}
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
