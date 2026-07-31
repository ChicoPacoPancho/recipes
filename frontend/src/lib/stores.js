import { writable } from 'svelte/store';

/** Currently active household member (selected via settings). */
export const currentMember = writable(
  JSON.parse(localStorage.getItem('currentMember') || 'null')
);
currentMember.subscribe(value => {
  localStorage.setItem('currentMember', JSON.stringify(value));
});

/** Preferred unit system: 'imperial' or 'metric'. */
export const unitSystem = writable(
  localStorage.getItem('unitSystem') || 'imperial'
);
unitSystem.subscribe(value => {
  localStorage.setItem('unitSystem', value);
});

/** Shopping list badge count. */
export const shoppingCount = writable(0);

/** Toast notification. */
export const toast = writable(null);
let toastTimeout;
export function showToast(message, type = 'success', duration = 3000) {
  clearTimeout(toastTimeout);
  toast.set({ message, type });
  toastTimeout = setTimeout(() => toast.set(null), duration);
}
