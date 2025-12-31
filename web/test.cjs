// test.cjs
const Color = require('colorjs.io').default;

function oklchToHex(oklchStr) {
  try {
    const color = new Color(oklchStr);
    let srgb = color.to('srgb');

    // 色域映射（v0.5.2 支持 toGamut）
    if (!srgb.inGamut()) {
      srgb = srgb.toGamut();
    }

    const [r, g, b] = srgb.coords;

    const toHexByte = (x) => {
      const clamped = Math.max(0, Math.min(1, x));
      const byte = Math.round(clamped * 255);
      return byte.toString(16).padStart(2, '0');
    };

    return '#' + [r, g, b].map(toHexByte).join('');
  } catch (e) {
    console.error('Convert error:', e.message);
    return oklchStr; // fallback
  }
}

console.log(oklchToHex('oklch(0 0 0)'));               // #000000
console.log(oklchToHex('oklch(100% 0 0)'));            // #ffffff
console.log(oklchToHex('oklch(97.1% .013 17.38)'));   // e.g. #f9f6f2