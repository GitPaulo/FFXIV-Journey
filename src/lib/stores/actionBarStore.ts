import { writable } from "svelte/store";

export const autoMode = writable(true);
export const showToggleTooltip = writable(false);
export const showScrollToTop = writable(false);

export function toggleAutoMode() {
  autoMode.update((value) => !value);
}

export function enableToggleTooltip() {
  showToggleTooltip.set(true);
}

export function disableToggleTooltip() {
  showToggleTooltip.set(false);
}

export function enableScrollToTop() {
  showScrollToTop.set(true);
}

export function disableScrollToTop() {
  showScrollToTop.set(false);
}
