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
 * Detects if the user is on a mobile/touch device.
 * @returns True if the device supports touch events or has a mobile viewport.
 */
export function isMobile(): boolean {
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  const isMobileWidth = window.matchMedia("(max-width: 639px)").matches;
  const isLandscapeMobile = window.matchMedia("(max-width: 1024px) and (max-height: 600px)").matches;
  return hasTouch || isMobileWidth || isLandscapeMobile;
}

/**
 * Creates a set of particles to simulate magic.
 * @param inputElement The input element to attach the particles to.
 */
export function createMagicParticles(inputElement: HTMLInputElement) {
  const container = inputElement.closest("li");
  if (!container) return;

  for (let i = 0; i < 8; i++) {
    const particle = document.createElement("span");
    particle.classList.add("particle");

    particle.style.setProperty("--x", `${Math.random() * 35 - 20}px`);
    particle.style.setProperty("--y", `${Math.random() * 38 - 20}px`);

    container.appendChild(particle);

    setTimeout(() => particle.remove(), 750);
  }
}
