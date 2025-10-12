import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import enCommon from "./locales/en/common.json";
import deCommon from "./locales/de/common.json";

const resources = {
  en: { common: enCommon },
  de: { common: deCommon },
};

const detectionOptions = {
  order: ["localStorage", "querystring", "navigator"],
  caches: ["localStorage"],
  lookupQuerystring: "lang",
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    supportedLngs: ["en", "de"],
    defaultNS: "common",
    ns: ["common"],
    interpolation: { escapeValue: false },
    detection: detectionOptions,
    returnNull: false,
  });

const updateLangAttribute = (lng) => {
  if (typeof document !== "undefined") {
    const language = lng || "en";
    document.documentElement.lang = language;
    document.documentElement.dir = "ltr";
  }
};

if (i18n.language) {
  updateLangAttribute(i18n.language);
}

i18n.on("languageChanged", (lng) => {
  updateLangAttribute(lng);
});

i18n.on("initialized", (options) => {
  updateLangAttribute(options?.lng || i18n.language);
});

export default i18n;
