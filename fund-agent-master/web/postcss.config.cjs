// postcss.config.cjs
const oklchToHex = require('./postcss-oklch-to-hex.cjs');
const autoprefixer = require('autoprefixer');

module.exports = {
  plugins: [
    oklchToHex,
    autoprefixer,
  ],
};