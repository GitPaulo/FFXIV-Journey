import { writable } from "svelte/store";

const STORAGE_KEY = "theme";

function getInitialTheme(): boolean {
  if (typeof window === "undefined") return false;

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored !== null) return stored === "dark";

  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export const darkMode = writable(getInitialTheme());

export function toggleDarkMode() {
  // Enable transitions only during explicit toggle
  document.documentElement.classList.add("theme-transition");
  darkMode.update((value) => !value);
  // Remove after transitions complete
  setTimeout(() => {
    document.documentElement.classList.remove("theme-transition");
  }, 350);
}

// Apply theme class to <html> and persist to localStorage
if (typeof window !== "undefined") {
  darkMode.subscribe((isDark) => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem(STORAGE_KEY, isDark ? "dark" : "light");
  });

  // Listen for system theme changes (auto-follows when no explicit preference stored)
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      const stored = localStorage.getItem(STORAGE_KEY);
      // Only auto-follow if user hasn't explicitly set a preference,
      // or on mobile where we always follow system
      if (!stored || window.innerWidth < 640) {
        document.documentElement.classList.add("theme-transition");
        darkMode.set(e.matches);
        localStorage.removeItem(STORAGE_KEY);
        setTimeout(() => {
          document.documentElement.classList.remove("theme-transition");
        }, 350);
      }
    });
}
