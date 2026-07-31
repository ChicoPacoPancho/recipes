/** Client-side unit formatting utilities. */

const VOLUME_UNITS = new Set([
  'ml', 'milliliter', 'milliliters', 'l', 'liter', 'liters',
  'tsp', 'teaspoon', 'teaspoons', 'tbsp', 'tablespoon', 'tablespoons',
  'fl oz', 'fluid ounce', 'fluid ounces', 'cup', 'cups',
  'pint', 'pints', 'quart', 'quarts', 'gallon', 'gallons',
]);

const WEIGHT_UNITS = new Set([
  'g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms',
  'oz', 'ounce', 'ounces', 'lb', 'pound', 'pounds',
]);

export function isConvertibleUnit(unit) {
  if (!unit) return false;
  const u = unit.toLowerCase().trim();
  return VOLUME_UNITS.has(u) || WEIGHT_UNITS.has(u);
}

/** Format quantity for display using common fractions. */
export function formatQuantity(qty) {
  if (qty === null || qty === undefined || qty === '') return '';
  const num = Number(qty);
  if (isNaN(num)) return String(qty);
  if (num === Math.floor(num)) return String(Math.floor(num));

  const whole = Math.floor(num);
  const frac = num - whole;

  const fractions = [
    [0.125, '⅛'], [0.25, '¼'], [0.333, '⅓'], [0.375, '⅜'],
    [0.5, '½'], [0.625, '⅝'], [0.667, '⅔'], [0.75, '¾'], [0.875, '⅞'],
  ];

  for (const [val, symbol] of fractions) {
    if (Math.abs(frac - val) < 0.02) {
      return whole > 0 ? `${whole} ${symbol}` : symbol;
    }
  }

  return num % 1 === 0 ? String(num) : num.toFixed(1);
}

/** Format minutes into a human-readable string. */
export function formatTime(minutes) {
  if (!minutes) return '';
  if (minutes < 60) return `${minutes} min`;
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) return `${hrs} hr`;
  return `${hrs} hr ${mins} min`;
}

/** Format seconds into mm:ss or hh:mm:ss. */
export function formatTimer(seconds) {
  if (seconds < 0) seconds = 0;
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const pad = n => String(n).padStart(2, '0');
  if (hrs > 0) return `${hrs}:${pad(mins)}:${pad(secs)}`;
  return `${pad(mins)}:${pad(secs)}`;
}
