// Original line icons share the site's instrument-like geometry. Labels live in
// adjacent text, so these decorative SVGs stay out of the accessibility tree.
const drawings = {
  arrow: '<path d="M9 23 23 9M9 9h14v14"/>',
  pause: '<path d="M11 7v18M21 7v18"/>',
  play: '<path d="m11 6 15 10-15 10V6Z"/>',
  message: '<path d="M7 7h18a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3H14l-7 5v-5a3 3 0 0 1-3-3V10a3 3 0 0 1 3-3Z"/><path d="M10 13h12M10 17h8"/>',
  data: '<rect x="8" y="5" width="18" height="22" rx="3"/><path d="M8 9H5a2 2 0 0 0-2 2v17a2 2 0 0 0 2 2h17M13 11h8M13 16h8M13 21h4"/>',
  evaluate: '<path d="M12 5H7a2 2 0 0 0-2 2v5M20 5h5a2 2 0 0 1 2 2v5M27 20v5a2 2 0 0 1-2 2h-5M12 27H7a2 2 0 0 1-2-2v-5M10 16l4 4 8-9"/>',
  environment: '<rect x="3" y="5" width="26" height="22" rx="3"/><path d="M3 11h26M7 8h.01M11 8h.01M9 16l4 3-4 3M17 23h6"/>',
  collaborate: '<circle cx="11" cy="10" r="4"/><path d="M3 27v-3a8 8 0 0 1 16 0v3M22 6a4 4 0 0 1 0 8M23 18a7 7 0 0 1 6 7v2"/>',
  build: '<path d="m16 3 12 7v13l-12 7-12-7V10L16 3ZM4 10l12 7 12-7M16 17v13M10 6l12 7v6"/>',
  tune: '<path d="M5 7h22M5 16h22M5 25h22"/><circle cx="11" cy="7" r="3" fill="var(--paper)"/><circle cx="22" cy="16" r="3" fill="var(--paper)"/><circle cx="13" cy="25" r="3" fill="var(--paper)"/>',
  craft: '<path d="m8 26 3-8L23 6a3 3 0 0 1 4 4L15 22l-7 4ZM19 10l4 4M11 18l4 4M4 29h24M5 4v7M2 7h6"/>',
  question: '<circle cx="16" cy="16" r="13"/><path d="M12 11a4 4 0 1 1 6 3.5c-1.5.9-2 1.5-2 3.5M16 23h.01"/>',
};

export function icon(name) {
  if (!drawings[name]) throw new Error(`Unknown icon: ${name}`);
  return `<svg class="icon icon-${name}" viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${drawings[name]}</svg>`;
}
