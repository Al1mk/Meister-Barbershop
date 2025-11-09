import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { sendContact } from "../lib/api.js";

export default function Contact() {
  const { t } = useTranslation();
  const [f, setF] = useState({ name: "", email: "", phone: "", message: "" });
  const [ok, setOk] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const trimmed = {
    name: f.name.trim(),
    email: f.email.trim(),
    phone: f.phone.trim(),
    message: f.message.trim(),
  };
  const canSubmit = Boolean(trimmed.name && trimmed.message && (trimmed.email || trimmed.phone));

  async function submit(event) {
    event.preventDefault();
    setOk("");
    setErr("");
    if (!canSubmit) {
      setErr(t("alerts.contactInvalid"));
      return;
    }
    setLoading(true);
    try {
      await sendContact(trimmed);
      setOk(t("contact.success"));
      setF({ name: "", email: "", phone: "", message: "" });
    } catch (error) {
      setErr(error.message || t("contact.error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h2 style={{ color: "var(--bronze)" }}>{t("contact.title")}</h2>
      <form className="card" style={{ padding: 16, marginTop: 12 }} onSubmit={submit}>
        <label className="label">{t("contact.name")}</label>
        <input className="input" value={f.name} onChange={(e) => setF((v) => ({ ...v, name: e.target.value }))} />
        <label className="label">{t("contact.email")}</label>
        <input className="input" type="email" value={f.email} onChange={(e) => setF((v) => ({ ...v, email: e.target.value }))} />
        <label className="label">{t("contact.phone")}</label>
        <input className="input" value={f.phone} onChange={(e) => setF((v) => ({ ...v, phone: e.target.value }))} />
        <label className="label">{t("contact.message")}</label>
        <textarea className="input" rows={5} value={f.message} onChange={(e) => setF((v) => ({ ...v, message: e.target.value }))} />
        <div style={{ display: "flex", gap: 12, marginTop: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button className="btn" type="submit" disabled={loading || !canSubmit}>
            {loading ? t("contact.sending") : t("contact.submit")}
          </button>
          {ok && <div className="success">{ok}</div>}
          {err && <div className="error">{err}</div>}
        </div>
        {!canSubmit && (
          <div className="help" style={{ marginTop: 8 }}>
            {t("contact.helper")}
          </div>
        )}
      </form>

      <div className="card" style={{ marginTop: 24, overflow: "hidden" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid #1f1f1f" }}>
          <strong>{t("home.locationTitle")}:</strong> {t("home.locationDetail")}
        </div>
        <iframe
          title="Meister Location"
          width="100%"
          height="360"
          style={{ border: 0 }}
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src="https://www.google.com/maps?ll=49.5952204,11.0022963https://www.google.com/maps?ll=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedq=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedz=19https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedhl=dehttps://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedoutput=embedq=49.5952204,11.0022963https://www.google.com/maps?ll=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedq=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedz=19https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedhl=dehttps://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedoutput=embedz=19https://www.google.com/maps?ll=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedq=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedz=19https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedhl=dehttps://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedoutput=embedhl=dehttps://www.google.com/maps?ll=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedq=49.5952204,11.0022963https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedz=19https://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedhl=dehttps://www.google.com/maps?q=Hauptstr.+12,+91054+Erlangen,+Germany&output=embedoutput=embedoutput=embed"
        />
      </div>
    </div>
  );
}
