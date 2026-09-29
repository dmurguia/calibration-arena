interface CalibratedMarkProps {
  size?: number
  className?: string
  title?: string
}

/**
 * The Calibrated Co. C mark, from the supplied brand kit 3.0 SVG
 * (public/brand/calibrated-mark-ink.svg). Inherits currentColor so it reads
 * as charcoal on paper and paper on charcoal. Never redraw or recolor it.
 */
export function CalibratedMark({ size = 24, className = '', title }: CalibratedMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 220 220"
      fill="currentColor"
      className={className}
      role={title ? 'img' : 'presentation'}
      aria-hidden={title ? undefined : true}
    >
      {title ? <title>{title}</title> : null}
      <path d="M180 48 C154 16 121 10 96 15 C51 22 20 57 13 102 C5 146 30 184 68 197 C110 214 153 194 179 164 L165 150 C142 176 111 188 81 177 C51 167 38 140 38 114 C37 76 64 39 99 31 C126 24 151 33 169 59 Z" />
      <path d="M151 106 L205 105 L205 122 L141 121 Z" />
    </svg>
  )
}
