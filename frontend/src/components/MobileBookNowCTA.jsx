import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";

const MOBILE_BREAKPOINT = 768;

export default function MobileBookNowCTA() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);

  // Check if we're on a relevant page (home or booking, not admin)
  const isRelevantPage = location.pathname === "/" || location.pathname === "/booking";

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleClick = () => {
    // If we're already on the booking page, scroll to the booking section
    if (location.pathname === "/booking") {
      const bookingSection = document.getElementById("booking-section");
      if (bookingSection) {
        bookingSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } else {
      // Navigate to booking page
      navigate("/booking");
    }
  };

  // Only render if mobile and on relevant page
  if (!isMobile || !isRelevantPage) {
    return null;
  }

  return (
    <button
      type="button"
      className="mobile-book-now-cta"
      onClick={handleClick}
      aria-label={t("mobileBookNow.ariaLabel")}
    >
      {t("mobileBookNow.text")}
    </button>
  );
}
