const normalizeName = (value = "") => value.trim().toLowerCase();

const BARBER_DETAILS = {
  ehsan: {
    taglineKey: "booking.barbers.details.ehsan.tagline",
    availabilityKey: "booking.barbers.details.ehsan.availability",
    languages: ["Deutsch"],
  },
  iman: {
    taglineKey: "booking.barbers.details.iman.tagline",
    availabilityKey: "booking.barbers.details.iman.availability",
    languages: ["Deutsch"],
  },
  javad: {
    taglineKey: "booking.barbers.details.javad.tagline",
    availabilityKey: "booking.barbers.details.javad.availability",
    languages: ["Deutsch"],
  },
  ali: {
    taglineKey: "booking.barbers.details.ali.tagline",
    availabilityKey: "booking.barbers.details.ali.availability",
    languages: ["Deutsch", "English"],
  },
  alishaun: {
    taglineKey: "booking.barbers.details.alishaun.tagline",
    availabilityKey: "booking.barbers.details.alishaun.availability",
    languages: ["Deutsch", "English"],
  },
};

const DEFAULT_DETAILS = {
  taglineKey: "booking.barbers.details.default.tagline",
  availabilityKey: "booking.barbers.details.default.availability",
  languages: ["Deutsch"],
};

export function getBarberDetails(name) {
  if (!name) {return DEFAULT_DETAILS;}
  const key = normalizeName(name);
  return BARBER_DETAILS[key] ?? DEFAULT_DETAILS;
}
