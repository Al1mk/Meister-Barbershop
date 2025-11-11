const normalizeName = (value = "") => value.trim().toLowerCase();

const BARBER_DETAILS = {
  ehsan: {
    taglineKey: "booking.barbers.details.ehsan.tagline",
    availabilityKey: "booking.barbers.details.ehsan.availability",
    languages: ["DE", "FA"],
  },
  iman: {
    taglineKey: "booking.barbers.details.iman.tagline",
    availabilityKey: "booking.barbers.details.iman.availability",
    languages: ["DE", "FA"],
  },
  javad: {
    taglineKey: "booking.barbers.details.javad.tagline",
    availabilityKey: "booking.barbers.details.javad.availability",
    languages: ["DE", "FA", "EN"],
  },
  ali: {
    taglineKey: "booking.barbers.details.ali.tagline",
    availabilityKey: "booking.barbers.details.ali.availability",
    languages: ["DE", "FA"],
  },
  reza: {
    taglineKey: "booking.barbers.details.reza.tagline",
    availabilityKey: "booking.barbers.details.reza.availability",
    languages: ["DE", "FA"],
  },
};

const DEFAULT_DETAILS = {
  taglineKey: "booking.barbers.details.default.tagline",
  availabilityKey: "booking.barbers.details.default.availability",
  languages: ["DE"],
};

export function getBarberDetails(name) {
  if (!name) {return DEFAULT_DETAILS;}
  const key = normalizeName(name);
  return BARBER_DETAILS[key] ?? DEFAULT_DETAILS;
}
