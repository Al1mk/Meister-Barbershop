/**
 * Single source of truth for team member data
 * Used by both Booking page and Our Team section
 */

export const teamMembers = [
  {
    id: 1,
    name: "Ehsan",
    slug: "ehsan",
    image: "/images/barbers/ehsan.jpg",
    languages: ["Deutsch"],
  },
  {
    id: 2,
    name: "Iman",
    slug: "iman",
    image: "/images/barbers/iman.jpg",
    languages: ["Deutsch"],
  },
  {
    id: 3,
    name: "Javad",
    slug: "javad",
    image: "/images/barbers/javad.jpg",
    languages: ["Deutsch"],
  },
  {
    id: 4,
    name: "Ali",
    slug: "ali",
    image: "/images/barbers/ali.jpg",
    languages: ["Deutsch", "English"],
  },
  {
    id: 5,
    name: "Alishaun",
    slug: "alishaun",
    image: "/images/barbers/alishaun.jpg",
    languages: ["Deutsch", "English"],
  },
];

// Export as 'team' for backwards compatibility with Booking page
export const team = teamMembers;

/**
 * Get team member by name (case-insensitive)
 */
export function getTeamMemberByName(name) {
  if (!name) {return null;}
  const normalized = name.trim().toLowerCase();
  return teamMembers.find(member => member.name.toLowerCase() === normalized) || null;
}

/**
 * Get all active team members
 */
export function getActiveTeamMembers() {
  return teamMembers;
}
