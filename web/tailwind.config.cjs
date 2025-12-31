/**
 * Minimal Tailwind config — ensures Tailwind scans the right files during
 * production build so utilities used in JSX/TSX are preserved.
 *
 * Adjust the `content` globs if your source lives in other folders. If you
 * generate class names dynamically at runtime (e.g. `bg-${color}`), add a
 * `safelist` for those patterns so Tailwind doesn't purge them.
 */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx,html}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  // Example safelist (uncomment and adjust if you use dynamic classnames):
  // safelist: [
  //   { pattern: /^(bg|text|border)-(red|green|blue)-(100|200|300)$/ },
  // ],
}
