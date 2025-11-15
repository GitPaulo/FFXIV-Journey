/**
 * Sanitize FFXIV Mark-up into a human-readable string
 * @param str The string to sanitize
 * @returns string
 */
export function sanitizeFFXIVMarkUp(str: string | null): string {
  return str ? str.replace(/<[^>]*>/g, "") : "This quest has no description.";
}

/**
 * Returns the Garland Tools URL for a given quest.
 * @param questId The unique ID of the quest.
 * @returns The URL to the quest on Garland Tools.
 */
export function getGarlandToolsQuestURLByID(questId: number): string {
  return `https://www.garlandtools.org/db/#quest/${questId}`;
}

/**
 * Creates a set of particles to simulate magic.
 * @param inputElement The input element to attach the particles to.
 */
export function createMagicParticles(inputElement: HTMLInputElement) {
  const container = inputElement.closest("li");
  if (!container) return;

  for (let i = 0; i < 8; i++) {
    // Adjust the number of particles as desired
    const particle = document.createElement("span");
    particle.classList.add("particle");

    // Randomize direction
    particle.style.setProperty("--x", `${Math.random() * 35 - 20}px`);
    particle.style.setProperty("--y", `${Math.random() * 38 - 20}px`);

    container.appendChild(particle);

    // Remove particle after animation
    setTimeout(() => particle.remove(), 750);
  }
}

/**
 * Is the current device a mobile device
 * @returns boolean
 */
export function isMobile() {
  // Check for mobile width OR small height (landscape mode on mobile)
  const isMobileWidth = window.matchMedia("(max-width: 639px)").matches;
  const isLandscapeMobile = window.matchMedia("(max-width: 1024px) and (max-height: 600px)").matches;
  return isMobileWidth || isLandscapeMobile;
}
