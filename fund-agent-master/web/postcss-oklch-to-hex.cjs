// postcss-oklch-to-hex.cjs
const Color = require('colorjs.io').default;

function coordsToHex(coords) {
  const toHexByte = (x) => {
    const clamped = Math.max(0, Math.min(1, x));
    const byte = Math.round(clamped * 255);
    return byte.toString(16).padStart(2, '0');
  };
  return '#' + coords.map(toHexByte).join('');
}

function parseOklch(str) {
  const match = str.match(/oklch\(\s*([^\)]+)\s*\)/i);
  if (!match) return null;

  try {
    const color = new Color(`oklch(${match[1]})`);
    let srgb = color.to('srgb');
    if (!srgb.inGamut()) {
      srgb = srgb.toGamut();
    }
    return coordsToHex(srgb.coords).toLowerCase();
  } catch (e) {
    console.warn('⚠️ Failed to parse OKLCH:', str, e.message);
    return null;
  }
}

module.exports = () => {
  return {
    postcssPlugin: 'postcss-oklch-to-hex',
    Declaration(decl) {
      if (typeof decl.value !== 'string') return;
      if (/oklch\(/i.test(decl.value)) {
        const newVal = decl.value.replace(/oklch\([^)]+\)/gi, (match) => {
          const hex = parseOklch(match);
          return hex || match;
        });
        decl.value = newVal;
      }
    }
  };
};

module.exports.postcss = true;