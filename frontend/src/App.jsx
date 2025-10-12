import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import logo from "./assets/faravahar.png";
import globeIcon from "./assets/globe.svg";
import flagUs from "./assets/flags/us.png";
import flagDe from "./assets/flags/de.png";

import Home from "./pages/Home.jsx";
import Booking from "./pages/Booking.jsx";
import Contact from "./pages/Contact.jsx";
import ThankYou from "./pages/ThankYou.jsx";
import NotFound from "./pages/NotFound.jsx";

const languages = [
  { code: "en", flag: flagUs, alt: "English (United States)" },
  { code: "de", flag: flagDe, alt: "Deutsch (Deutschland)" },
];

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const hoverTimeout = useRef(null);

  const current = languages.find((item) => item.code === i18n.language) || languages[0];

  const clearHoverTimeout = () => {
    if (hoverTimeout.current) {
      clearTimeout(hoverTimeout.current);
      hoverTimeout.current = null;
    }
  };

  const close = () => {
    clearHoverTimeout();
    setOpen(false);
  };
  const openMenu = () => {
    clearHoverTimeout();
    setOpen(true);
  };
  const toggle = () => {
    clearHoverTimeout();
    setOpen((prev) => !prev);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        close();
      }
    };
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        close();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
      clearHoverTimeout();
    };
  }, []);

  const scheduleClose = () => {
    clearHoverTimeout();
    hoverTimeout.current = setTimeout(() => {
      setOpen(false);
    }, 150);
  };

  const handleToggleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      const firstItem = containerRef.current?.querySelector("button[data-language]");
      firstItem?.focus();
    }
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  };

  const handleSelect = (code) => {
    i18n.changeLanguage(code);
    close();
  };

  const handleItemKeyDown = (event, code) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleSelect(code);
    }
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  };

  const handleBlur = (event) => {
    if (!containerRef.current?.contains(event.relatedTarget)) {
      close();
    }
  };

  return (
    <div
      className={`language-switcher${open ? " open" : ""}`}
      ref={containerRef}
      onMouseEnter={openMenu}
      onMouseLeave={scheduleClose}
      onBlur={handleBlur}
    >
      <button
        type="button"
        className="language-button"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={toggle}
        onKeyDown={handleToggleKeyDown}
        onFocus={openMenu}
      >
        <img src={globeIcon} alt={t("languageSwitcher.label") || "Language"} className="language-icon" />
        <img src={current.flag} alt={current.alt} className="language-flag" />
      </button>
      {open && (
        <ul className="language-menu" role="menu" onMouseEnter={openMenu} onMouseLeave={scheduleClose}>
          {languages.map((lang) => (
            <li key={lang.code} role="none">
              <button
                type="button"
                role="menuitem"
                data-language={lang.code}
                className={`language-option${current.code === lang.code ? " active" : ""}`}
                onClick={() => handleSelect(lang.code)}
                onKeyDown={(event) => handleItemKeyDown(event, lang.code)}
              >
                <img src={lang.flag} alt={lang.alt} className="language-option-flag" />
                <span>{t(`languageSwitcher.languages.${lang.code}`)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const Nav = () => {
  const { t } = useTranslation();
  return (
    <header className="navbar">
      <div className="nav-left">
        <LanguageSwitcher />
        <div className="brand">
          <img src={logo} alt={t("brand") || "Meister Barbershop"} className="logo-img" width={40} height={40} />
          <h1 className="title">{t("brand")}</h1>
        </div>
      </div>
      <nav className="nav-links">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>{t("nav.home")}</NavLink>
        <NavLink to="/booking" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>{t("nav.booking")}</NavLink>
        <NavLink to="/contact" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>{t("nav.contact")}</NavLink>
      </nav>
    </header>
  );
};

const Footer = () => {
  const { t } = useTranslation();
  return (
    <footer className="footer">
      <div className="container" style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>© {new Date().getFullYear()} {t("brand")}</div>
        <div className="help">
          {t("footer.address")} — <span style={{ color: "var(--bronze)" }}>{t("footer.open")}</span>
        </div>
      </div>
    </footer>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/booking" element={<Booking />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/thanks" element={<ThankYou />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}
