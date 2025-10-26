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
import AdminSchedule from "./pages/AdminSchedule.jsx";

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <header className="navbar">
      <div className="nav-brand-row">
        <div className="brand">
          <img src={logo} alt={t("brand") || "Meister Barbershop"} className="logo-img" width={40} height={40} />
          <h1 className="title">{t("brand")}</h1>
        </div>
        <div className="nav-right-mobile">
          <LanguageSwitcher />
          <button 
            className="hamburger" 
            onClick={toggleMobileMenu}
            aria-label="Toggle menu"
            aria-expanded={mobileMenuOpen}
          >
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
          </button>
        </div>
      </div>
      <nav className={`nav-links ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <NavLink 
          to="/" 
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          onClick={closeMobileMenu}
        >
          {t("nav.home")}
        </NavLink>
        <NavLink 
          to="/booking" 
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          onClick={closeMobileMenu}
        >
          {t("nav.booking")}
        </NavLink>
        <NavLink 
          to="/contact" 
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          onClick={closeMobileMenu}
        >
          {t("nav.contact")}
        </NavLink>
        <div className="nav-desktop-lang">
          <LanguageSwitcher />
        </div>
      </nav>
    </header>
  );
};

const Footer = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({ name: "", phone: "", message: "" });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setStatus({ type: "", message: "" });

    try {
      const apiBase = import.meta.env.VITE_API_BASE || "/api";
      const response = await fetch(`${apiBase}/contact/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok && data.ok) {
        setStatus({ type: "success", message: t("footer.contact.success") || "Thanks, we'll get back to you." });
        setFormData({ name: "", phone: "", message: "" });
      } else {
        setStatus({ type: "error", message: t("footer.contact.error") || "Something went wrong, please try again." });
      }
    } catch (error) {
      setStatus({ type: "error", message: t("footer.contact.error") || "Something went wrong, please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-info">
            <div>© {new Date().getFullYear()} {t("brand")}</div>
            <div className="help">
              {t("footer.address")} — <span style={{ color: "var(--bronze)" }}>{t("footer.open")}</span>
            </div>
          </div>
          
          <div className="footer-contact">
            <h3>{t("footer.contact.title") || "Contact / Kontakt"}</h3>
            <form onSubmit={handleSubmit} className="contact-form">
              <div className="form-group">
                <label htmlFor="contact-name" className="label">
                  {t("footer.contact.name") || "Name"} <span className="required">*</span>
                </label>
                <input
                  id="contact-name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="contact-phone" className="label">
                  {t("footer.contact.phone") || "Phone"}
                </label>
                <input
                  id="contact-phone"
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="input"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="contact-message" className="label">
                  {t("footer.contact.message") || "Message"} <span className="required">*</span>
                </label>
                <textarea
                  id="contact-message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  className="input textarea"
                  rows="4"
                  required
                />
              </div>
              
              <button type="submit" className="btn" disabled={submitting}>
                {submitting ? (t("footer.contact.sending") || "Sending...") : (t("footer.contact.submit") || "Send Message")}
              </button>
              
              {status.message && (
                <div className={`form-status ${status.type}`}>
                  {status.message}
                </div>
              )}
            </form>
          </div>
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
        <Route path="/admin/schedule" element={<AdminSchedule />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}
