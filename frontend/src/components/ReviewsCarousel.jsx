import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getReviews } from "../lib/api.js";
import usePrefersReducedMotion from "../hooks/usePrefersReducedMotion.js";

const AUTOPLAY_INTERVAL = 5000;
const MAX_TEXT_LENGTH = 220;

const formatRelativeTime = (timestamp, locale) => {
  if (!timestamp) return "";
  let date;
  if (typeof timestamp === "number") {
    date = new Date(timestamp * 1000);
  } else {
    date = new Date(timestamp);
  }
  if (Number.isNaN(date.getTime())) return "";
  const now = Date.now();
  const diff = now - date.getTime();
  const units = [
    { limit: 1000 * 60, divisor: 1000, unit: "second" },
    { limit: 1000 * 60 * 60, divisor: 1000 * 60, unit: "minute" },
    { limit: 1000 * 60 * 60 * 24, divisor: 1000 * 60 * 60, unit: "hour" },
    { limit: 1000 * 60 * 60 * 24 * 7, divisor: 1000 * 60 * 60 * 24, unit: "day" },
    { limit: 1000 * 60 * 60 * 24 * 30, divisor: 1000 * 60 * 60 * 24 * 7, unit: "week" },
    { limit: 1000 * 60 * 60 * 24 * 365, divisor: 1000 * 60 * 60 * 24 * 30, unit: "month" },
    { limit: Infinity, divisor: 1000 * 60 * 60 * 24 * 365, unit: "year" },
  ];
  const absDiff = Math.abs(diff);
  for (const { limit, divisor, unit } of units) {
    if (absDiff < limit) {
      const value = Math.round(diff / divisor);
      const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
      return rtf.format(-value, unit);
    }
  }
  return date.toLocaleDateString(locale);
};

const StarRating = ({ value, label }) => {
  const widthPercent = Math.max(0, Math.min(100, (value / 5) * 100));
  return (
    <div className="reviews-stars" aria-label={label} role="img">
      <div className="reviews-stars__base">★★★★★</div>
      <div className="reviews-stars__fill" style={{ width: `${widthPercent}%` }}>★★★★★</div>
    </div>
  );
};

const truncateText = (text) => {
  if (!text) return "";
  if (text.length <= MAX_TEXT_LENGTH) return text;
  return `${text.slice(0, MAX_TEXT_LENGTH).trim()}…`;
};

export default function ReviewsCarousel() {
  console.log("📢 ReviewsCarousel mounted");
  const { t, i18n } = useTranslation();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [itemsPerView, setItemsPerView] = useState(1);
  const [isPaused, setIsPaused] = useState(false);
  const intervalRef = useRef(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  const reviews = data?.reviews || [];
  const maxIndex = Math.max(0, reviews.length - itemsPerView);
  const effectiveItemsPerView = Math.max(itemsPerView, 1);
  const hasMultiple = reviews.length > effectiveItemsPerView;

  useEffect(() => {
    let cancelled = false;
    setError("");
    console.log("📡 Fetching reviews from /api/reviews/ with lang:", i18n.language);
    getReviews(i18n.language)
      .then((payload) => {
        if (!cancelled) {
          console.log("✅ Reviews fetched successfully:", payload);
          setData(payload);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error("❌ Failed to fetch reviews:", err);
          setError(t("home.reviews.error"));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [i18n.language, t]);

  useEffect(() => {
    const evaluate = () => {
      const width = window.innerWidth;
      if (width >= 1024) {
        const perView = Math.min(3, Math.max(reviews.length, 1));
        setItemsPerView(perView);
      } else {
        setItemsPerView(1);
      }
    };
    evaluate();
    window.addEventListener("resize", evaluate);
    return () => window.removeEventListener("resize", evaluate);
  }, [reviews.length]);

  useEffect(() => {
    setCurrentIndex(0);
  }, [itemsPerView, reviews.length]);

  const next = useCallback(() => {
    setCurrentIndex((prev) => {
      if (!hasMultiple) return 0;
      return prev >= maxIndex ? 0 : prev + 1;
    });
  }, [hasMultiple, maxIndex]);

  const prev = useCallback(() => {
    setCurrentIndex((prev) => {
      if (!hasMultiple) return 0;
      if (prev <= 0) {
        return maxIndex;
      }
      return prev - 1;
    });
  }, [hasMultiple, maxIndex]);

  useEffect(() => {
    if (prefersReducedMotion || !hasMultiple) return undefined;
    if (isPaused) return undefined;
    intervalRef.current = setInterval(next, AUTOPLAY_INTERVAL);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [next, prefersReducedMotion, isPaused, hasMultiple]);

  const handlePause = (state) => () => {
    setIsPaused(state);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const ratingFormatter = useMemo(
    () => new Intl.NumberFormat(i18n.language, { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
    [i18n.language]
  );

  const countFormatter = useMemo(
    () => new Intl.NumberFormat(i18n.language),
    [i18n.language]
  );

  const trackStyle = {
    transform: `translateX(calc(-${currentIndex} * (100% / var(--total-items, 1))))`,
    '--items-per-view': effectiveItemsPerView,
    '--total-items': Math.max(reviews.length, 1),
  };

  const sectionTitle = t("home.reviews.title");

  return (
    <section
      className="reviews-section"
      role="region"
      aria-label={sectionTitle}
      aria-live="polite"
      onMouseEnter={handlePause(true)}
      onMouseLeave={handlePause(false)}
      onFocusCapture={handlePause(true)}
      onBlurCapture={handlePause(false)}
    >
      <div className="reviews-header">
        <div>
          <h3>{sectionTitle}</h3>
          {data?.rating && (
            <div className="reviews-summary">
              <span className="reviews-rating">
                {ratingFormatter.format(data.rating)}
                <StarRating value={data.rating} label={t("home.reviews.ratingLabel", { rating: ratingFormatter.format(data.rating) })} />
              </span>
              {typeof data.userRatingCount === "number" && (
                <span className="reviews-count">
                  {t("home.reviews.totalLabel", { count: data.userRatingCount })}
                </span>
              )}
            </div>
          )}
        </div>
        {data?.place_url && (
          <a
            className="btn outline reviews-cta"
            href={data.place_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("home.reviews.cta")}
          </a>
        )}
      </div>

      {error && <div className="error">{error}</div>}
      {!error && (!reviews.length ? <div className="help">{t("home.reviews.empty")}</div> : (
        <div className="reviews-carousel">
          <div className={`reviews-track${prefersReducedMotion ? " reduced-motion" : ""}`} style={trackStyle} role="list">
            {reviews.map((review, idx) => {
              const truncated = truncateText(review.text);
              const reviewLink = review.sourceUrl;
              const relative = review.time ? formatRelativeTime(review.time, i18n.language) : "";
              return (
                <article className="review-card" role="listitem" key={`${review.authorName || "review"}-${idx}`}>
                  <header className="review-card__header">
                    <div className="review-card__name">{review.authorName || "Google User"}</div>
                    <StarRating
                      value={review.rating || 0}
                      label={t("home.reviews.ratingLabel", { rating: ratingFormatter.format(review.rating || 0) })}
                    />
                  </header>
                  <div className="review-card__body">
                    <p>{truncated}</p>
                    {reviewLink && (
                      <a href={reviewLink} target="_blank" rel="noopener noreferrer">
                        {t("home.reviews.readMore")}
                      </a>
                    )}
                  </div>
                  {relative && (
                    <footer className="review-card__footer">
                      <span>{relative}</span>
                    </footer>
                  )}
                </article>
              );
            })}
          </div>
          {hasMultiple && (
            <div className="reviews-controls">
              <button type="button" className="reviews-nav" onClick={prev} aria-label={t("home.reviews.prev")}>
                ‹
              </button>
              <button type="button" className="reviews-nav" onClick={next} aria-label={t("home.reviews.next")}>
                ›
              </button>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
