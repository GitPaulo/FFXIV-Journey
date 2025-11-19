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

// Open a modal with the given title and message.
export function openModal(
  title: string,
  message: string,
  onConfirm: () => void,
  onCancel: () => void,
  confirmLabel: string = "Confirm",
  cancelLabel: string = "Cancel",
  allowCancel: boolean = true,
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

// Close the modal.
export function closeModal(): void {
  modalState.update((state) => ({ ...state, show: false }));
}
