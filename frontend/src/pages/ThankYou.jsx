import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function ThankYou() {
  const { t } = useTranslation();
  return (
    <div className="container" style={{ padding: "60px 0", textAlign: "center" }}>
      <h2 style={{ color: "var(--bronze)" }}>{t("thankYou.title")}</h2>
      <p className="help">{t("thankYou.description")}</p>
      <div style={{ marginTop: 16 }}>
        <Link className="btn" to="/">
          {t("thankYou.cta")}
        </Link>
      </div>
    </div>
  );
}
