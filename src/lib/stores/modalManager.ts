import { writable } from "svelte/store";

export interface ModalState {
  show: boolean;
  title: string;
  message: string;
  onConfirm: (() => void) | null;
  onCancel: (() => void) | null;
  confirmLabel: string;
  cancelLabel: string;
  allowCancel: boolean;
}

export const modalState = writable<ModalState>({
  show: false,
  title: "",
  message: "",
  onConfirm: null,
  onCancel: null,
  confirmLabel: "Confirm",
  cancelLabel: "Cancel",
  allowCancel: true,
});

/**
 *  Opens a modal with the given title and message.
 * @param title
 * @param message
 * @param onConfirm
 * @param onCancel
 * @param confirmLabel
 * @param cancelLabel
 */
export function openModal(
  title: string,
  message: string,
  onConfirm: () => void,
  onCancel: () => void,
  confirmLabel: string = "Confirm",
  cancelLabel: string = "Cancel",
  allowCancel: boolean = true
): void {
  modalState.set({
    show: true,
    title,
    message,
    onConfirm,
    onCancel,
    confirmLabel,
    cancelLabel,
    allowCancel,
  });
}

/**
 * Closes the modal.
 */
export function closeModal(): void {
  modalState.update((state) => ({ ...state, show: false }));
}
