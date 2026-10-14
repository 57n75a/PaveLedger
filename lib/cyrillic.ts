// Serbian Latin to Cyrillic, for the Cyrillic interface option. The Latin translations are the single source;
// Cyrillic is derived as text is shown. Codes, acronyms, brand names, Roman numerals, emails and web addresses stay Latin.

const PAIRS: [string, string][] = [
  ['DŽ', 'Џ'], ['Dž', 'Џ'], ['dž', 'џ'], ['LJ', 'Љ'], ['Lj', 'Љ'], ['lj', 'љ'], ['NJ', 'Њ'], ['Nj', 'Њ'], ['nj', 'њ'],
];
const SINGLE: Record<string, string> = {
  A: 'А', B: 'Б', V: 'В', G: 'Г', D: 'Д', Đ: 'Ђ', E: 'Е', Ž: 'Ж', Z: 'З', I: 'И', J: 'Ј', K: 'К', L: 'Л', M: 'М', N: 'Н', O: 'О', P: 'П', R: 'Р', S: 'С', T: 'Т', Ć: 'Ћ', U: 'У', F: 'Ф', H: 'Х', C: 'Ц', Č: 'Ч', Š: 'Ш',
  a: 'а', b: 'б', v: 'в', g: 'г', d: 'д', đ: 'ђ', e: 'е', ž: 'ж', z: 'з', i: 'и', j: 'ј', k: 'к', l: 'л', m: 'м', n: 'н', o: 'о', p: 'п', r: 'р', s: 'с', t: 'т', ć: 'ћ', u: 'у', f: 'ф', h: 'х', c: 'ц', č: 'ч', š: 'ш',
};
// Kept in Latin: technical acronyms, scorecard grades (A-D), product and brand names.
const KEEP = new Set(['PDF', 'CSV', 'XML', 'JSON', 'GPS', 'SMS', 'URL', 'API', 'AI', 'ID', 'UUID', 'OK', 'PNG', 'JPEG', 'JPG', 'WebP', 'MB', 'KB', 'RSD', 'EUR', 'CAD', 'PDV',
  'RS', 'CA', 'EU', 'USA', 'CAN', 'SRB', 'EN', 'FR', 'LAT', 'PL', 'CT', 'DEMO', 'SHA',
  'A', 'B', 'C', 'D', 'PaveLedger', 'Google', 'OpenStreetMap', 'Leaflet', 'Supabase', 'Vercel', 'Neo4j', 'Cypher', 'Excel', 'Viber', 'WhatsApp', 'Resend', 'Photon', 'Nominatim', 'Chrome', 'Safari', 'Android', 'iPhone', 'iOS']);
const ROMAN = /^(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XX)$/;

function word(w: string): string {
  if (KEEP.has(w) || ROMAN.test(w) || /[qwxyQWXY]/.test(w) || /[a-z][A-Z]/.test(w)) return w;
  let out = '';
  for (let i = 0; i < w.length; i++) {
    const two = w.slice(i, i + 2);
    const pair = PAIRS.find(([l]) => l === two);
    if (pair) { out += pair[1]; i++; continue; }
    out += SINGLE[w[i]] ?? w[i];
  }
  return out;
}

/** Transliterate text, leaving codes (anything with digits), emails, web addresses and file names untouched. */
export function toCyrillic(text: string): string {
  if (!text || !/[A-Za-zČčĆćŽžŠšĐđ]/.test(text)) return text;
  return text.split(/(\s+)/).map(chunk => {
    if (/^\s*$/.test(chunk)) return chunk;
    if (/\d/.test(chunk) && /[A-Za-z]/.test(chunk) && /[-_#/:.]|^[A-Z]{1,4}\d/.test(chunk)) return chunk; // RS-DEMO-003, PL-2026-AB12, 4G
    if (/@|:\/\/|^www\.|\.(?:rs|ca|com|org|net|app|jpg|png|pdf|csv|xlsx|xml)\b/i.test(chunk)) return chunk;
    return chunk.replace(/[A-Za-zČčĆćŽžŠšĐđ]+/g, word);
  }).join('');
}
