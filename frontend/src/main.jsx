import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./i18n/index.js";
import "./styles.css";
import { initSentry } from "./lib/sentry.js";

// Initialize Sentry error tracking (only if VITE_SENTRY_DSN is set)
initSentry();

createRoot(document.getElementById("root")).render(<App />);
