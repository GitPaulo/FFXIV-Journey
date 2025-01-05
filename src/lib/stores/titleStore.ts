import { writable } from "svelte/store";

export const showHideTooltip = writable(false);
export const showTitle = writable(true);

export function toggleTitleVisibility() {
  showTitle.update((value) => !value);
}

export function enableHideTooltip() {
  showHideTooltip.set(true);
}

export function disableHideTooltip() {
  showHideTooltip.set(false);
}
