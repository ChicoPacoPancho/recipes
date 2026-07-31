/** Stickers for recipe ratings - fun for kids and adults alike. */
export const STICKERS = [
  { id: 'love', emoji: '❤️', label: 'Love it!' },
  { id: 'drool', emoji: '🤤', label: 'Drooling!' },
  { id: 'yummy', emoji: '😋', label: 'Yummy!' },
  { id: 'fire', emoji: '🔥', label: 'Fire!' },
  { id: 'chef', emoji: '👨‍🍳', label: "Chef's kiss!" },
  { id: 'star', emoji: '⭐', label: 'Star!' },
  { id: 'trophy', emoji: '🏆', label: 'Winner!' },
  { id: 'sparkles', emoji: '✨', label: 'Magical!' },
  { id: 'rainbow', emoji: '🌈', label: 'Colorful!' },
  { id: 'party', emoji: '🎉', label: 'Party!' },
  { id: 'mindblown', emoji: '🤯', label: 'Mind blown!' },
  { id: 'thumbsup', emoji: '👍', label: 'Good!' },
  { id: 'ok', emoji: '😐', label: "It's okay" },
  { id: 'thumbsdown', emoji: '👎', label: 'Not great' },
  { id: 'no', emoji: '🙅', label: 'No thanks' },
  { id: 'sick', emoji: '🤢', label: 'Yuck!' },
];

export function getStickerByID(id) {
  return STICKERS.find(s => s.id === id) || null;
}

/** Map a 1-5 score to a default sticker. */
export function scoreToSticker(score) {
  const map = { 1: 'sick', 2: 'thumbsdown', 3: 'ok', 4: 'yummy', 5: 'love' };
  return map[score] || 'ok';
}
