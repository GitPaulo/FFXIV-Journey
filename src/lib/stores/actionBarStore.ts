import { writable } from "svelte/store";

export const autoMode = writable(true);
export const showScrollToTop = writable(false);

export function toggleAutoMode() {
  autoMode.update((value) => !value);
}

export function enableScrollToTop() {
  showScrollToTop.set(true);
}

export function disableScrollToTop() {
  showScrollToTop.set(false);
}
