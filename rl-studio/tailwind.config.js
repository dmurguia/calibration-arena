/** Calibrated Co. palette (brand kit 3.0) plus two muted status tones for charts. */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F4F1E9',
        card: '#FAF9F6',
        ink: { DEFAULT: '#464643', deep: '#2F2F2D' },
        graphite: '#656460',
        steel: '#929698',
        leather: { DEFAULT: '#70543E', tint: '#EFE8DD' },
        hairline: '#4646432B',
        good: { DEFAULT: '#4E6B4F', tint: '#E6ECE2' },
        bad: { DEFAULT: '#9A4A36', tint: '#F3E3DC' },
        warn: { DEFAULT: '#A27A2C', tint: '#F4EBD6' },
      },
      fontFamily: {
        identity: ['"Archivo Black"', 'sans-serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      keyframes: {
        fadein: { from: { opacity: '0', transform: 'translateY(4px)' }, to: { opacity: '1', transform: 'none' } },
        pulsedot: { '0%,100%': { opacity: '1' }, '50%': { opacity: '.3' } },
      },
      animation: {
        fadein: 'fadein .35s cubic-bezier(.4,0,.2,1) both',
        pulsedot: 'pulsedot 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
