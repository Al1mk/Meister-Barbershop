import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="container" style={{ padding: "80px 0", textAlign: "center" }}>
      <h2>{t("notFound.title")}</h2>
      <Link className="btn" to="/">
        {t("notFound.cta")}
      </Link>
    </div>
  );
}
