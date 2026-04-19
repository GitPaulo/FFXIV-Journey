import { writable } from "svelte/store";

const AUTO_MODE_KEY = "ffxiv-journey:auto-mode";
const SHOW_PROGRESS_KEY = "ffxiv-journey:show-progress";

function storedBoolean(key: string, fallback: boolean) {
  const stored = typeof window !== "undefined" ? localStorage.getItem(key) : null;
  return stored !== null ? stored === "true" : fallback;
}

export const autoMode = writable(storedBoolean(AUTO_MODE_KEY, true));
export const showScrollToTop = writable(false);
export const showProgress = writable(storedBoolean(SHOW_PROGRESS_KEY, true));

if (typeof window !== "undefined") {
  autoMode.subscribe((v) => localStorage.setItem(AUTO_MODE_KEY, String(v)));
  showProgress.subscribe((v) => localStorage.setItem(SHOW_PROGRESS_KEY, String(v)));
}

export function toggleAutoMode() {
  autoMode.update((value) => !value);
}

export function toggleProgressVisibility() {
  showProgress.update((value) => !value);
}

export function enableScrollToTop() {
  showScrollToTop.set(true);
}

export function disableScrollToTop() {
  showScrollToTop.set(false);
}
