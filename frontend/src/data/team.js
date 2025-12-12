/**
 * LOCAL METADATA ONLY - Images and languages for team members.
 *
 * CRITICAL: IDs are fetched from API (/api/barbers/) at runtime.
 * This file contains ONLY display metadata (images, languages).
 * Matching is done by name/slug to prevent ID drift.
 */

export const teamMetadata = [
  {
    name: "Ali",
    slug: "ali",
    image: "/images/barbers/ali.jpg",
    languages: ["Deutsch", "English"],
  },
  {
    name: "Ehsan",
    slug: "ehsan",
    image: "/images/barbers/ehsan.jpg",
    languages: ["Deutsch"],
  },
  {
    name: "Iman",
    slug: "iman",
    image: "/images/barbers/iman.jpg",
    languages: ["Deutsch"],
  },
  {
    name: "Javad",
    slug: "javad",
    image: "/images/barbers/javad.jpg",
    languages: ["Deutsch"],
  },
  {
    name: "Alishan",
    slug: "alishan",
    image: "/images/barbers/alishan.jpg",
    languages: ["Deutsch", "English"],
  },
];

/**
 * Enrich barber data from API with local metadata (images, languages).
 * Matches by name (case-insensitive) to avoid ID drift.
 */
export function enrichBarberWithMetadata(barber) {
  if (!barber || !barber.name) {return barber;}
  const normalized = barber.name.trim().toLowerCase();
  const metadata = teamMetadata.find(m => m.name.toLowerCase() === normalized);
  if (metadata) {
    return { ...barber, image: metadata.image, languages: metadata.languages, slug: metadata.slug };
  }
  return barber;
}

/**
 * Enrich array of barbers with metadata
 */
export function enrichBarbersWithMetadata(barbers) {
  if (!Array.isArray(barbers)) {return [];}
  return barbers.map(enrichBarberWithMetadata);
}

// DEPRECATED: Export for backwards compatibility (will be removed)
// Use enrichBarberWithMetadata + API fetch instead
export const team = teamMetadata;
