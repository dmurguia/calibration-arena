// Calibrated Co. palette (brand kit 3.0). Six colors only; legacy names alias into it.
const ink = { DEFAULT: '#464643', hover: '#70543E' }
const leather = { DEFAULT: '#70543E', tint: '#FAF9F6' }

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F4F1E9',
        panel: '#F4F1E9',
        card: '#FAF9F6',
        hairline: '#46464333',
        ink: '#464643',
        muted: '#656460',
        graphite: '#656460',
        steel: '#929698',
        leather,
        chalk: '#FAF9F6',
        // Legacy names kept so existing utilities resolve to the Calibrated palette.
        spruce: ink,
        forest: ink,
        needle: leather,
        rust: leather,
        moss: { DEFAULT: '#FAF9F6', tint: '#FAF9F6' },
      },
      fontFamily: {
        identity: ['"Archivo Black"', 'sans-serif'],
        display: ['"IBM Plex Sans"', 'sans-serif'],
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      borderRadius: {
        none: '0',
        sm: '0',
        DEFAULT: '0',
        md: '0',
        lg: '0',
        xl: '0',
        '2xl': '0',
        '3xl': '0',
      },
      boxShadow: {
        whisper: 'none',
        lift: 'none',
      },
      transitionTimingFunction: {
        resolve: 'cubic-bezier(.4,0,.2,1)',
      },
    },
  },
  plugins: [],
}
