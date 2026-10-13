// Import schema for contractor contracts. Shared by the import screen (row checks, templates, guidelines)
// and the server (final validation), so both apply exactly the same rules.
// Messages are English source text; the interface translates them.

export type FieldType = 'text' | 'date' | 'email' | 'phone' | 'list' | 'number' | 'country';
export type SchemaField = {
  key: string;
  label: string;
  required: boolean;
  type: FieldType;
  max?: number;
  min?: number;
  example: string;
  /** Short format rule shown in the guidelines. */
  format: string;
  /** What the field is for. */
  help: string;
  /** Header names recognised automatically, compared without spaces, accents or punctuation. */
  aliases: string[];
};

export const MAX_IMPORT_ROWS = 200;
export const COUNTRIES = ['SRB', 'EU', 'USA', 'CAN'] as const;

export const CONTRACT_SCHEMA: SchemaField[] = [
  {key: 'contractor', label: 'Contractor firm', required: true, type: 'text', max: 120, example: 'Putevi Užice d.o.o.', format: 'Text, up to 120 characters', help: 'Registered name of the firm. Use the same spelling every time so its contracts group together.', aliases: ['contractor', 'company', 'firm', 'vendor', 'izvodjac', 'izvođač', 'firma', 'preduzece', 'preduzeće']},
  {key: 'road', label: 'Road name', required: true, type: 'text', max: 120, example: 'Kralja Petra I', format: 'Text, up to 120 characters', help: 'Main street or road the warranty covers, spelled exactly as in tickets.', aliases: ['road', 'street', 'location', 'put', 'ulica', 'deonica', 'lokacija']},
  {key: 'start', label: 'Warranty begins', required: true, type: 'date', example: '2026-03-01', format: 'YYYY-MM-DD or DD.MM.YYYY', help: 'First day of the warranty period.', aliases: ['start', 'begin', 'from', 'warrantystart', 'pocetak', 'početak', 'pocetakgarancije', 'od', 'datumod']},
  {key: 'end', label: 'Warranty ends', required: true, type: 'date', example: '2028-03-01', format: 'YYYY-MM-DD or DD.MM.YYYY, not before the start', help: 'Last day of the warranty period.', aliases: ['end', 'expiry', 'expires', 'until', 'to', 'warrantyend', 'kraj', 'krajgarancije', 'istek', 'do', 'datumdo']},
  {key: 'poc', label: 'Point of contact', required: true, type: 'text', max: 120, example: 'Marko Petrović', format: 'Text, up to 120 characters', help: 'Person at the firm who receives repair notices.', aliases: ['poc', 'contact', 'contactperson', 'kontakt', 'kontaktosoba', 'odgovornolice', 'odgovorno lice']},
  {key: 'email', label: 'Contact email', required: true, type: 'email', max: 250, example: 'marko@putevi-uzice.rs', format: 'A valid email address', help: 'Where repair notices are sent. Check it carefully.', aliases: ['email', 'mail', 'contactemail', 'eposta', 'e-pošta', 'imejl']},
  {key: 'phone', label: 'Phone number', required: false, type: 'phone', max: 40, example: '+381 31 123 456', format: 'Digits, spaces, +, -, ( ), up to 40 characters', help: 'Phone for urgent coordination.', aliases: ['phone', 'tel', 'telephone', 'mobile', 'telefon', 'mobilni', 'broj']},
  {key: 'scope', label: 'Work scope', required: false, type: 'text', max: 2000, example: 'Kolovoz od raskrsnice sa ul. Omladinska do mosta, obe trake', format: 'Text, up to 2,000 characters', help: 'What the warranty covers on that road, such as a section, lanes or chainage.', aliases: ['scope', 'workscope', 'description', 'obim', 'obimradova', 'opis', 'opisradova']},
  {key: 'additionalRoads', label: 'Additional streets', required: false, type: 'list', max: 1000, example: 'Vuka Karadžića; Dušanova', format: 'Street names separated by ; or new lines', help: 'Other streets covered by the same contract.', aliases: ['additionalroads', 'otherroads', 'additionalstreets', 'dodatneulice', 'ostaleulice']},
  {key: 'address', label: 'Firm address', required: false, type: 'text', max: 300, example: 'Nikole Pašića 12, Užice', format: 'Text, up to 300 characters', help: 'Postal address of the firm.', aliases: ['address', 'firmaddress', 'adresa', 'adresafirme', 'sediste', 'sedište']},
  {key: 'addressCountry', label: 'Country or region', required: false, type: 'country', example: 'SRB', format: 'SRB, EU, USA or CAN', help: 'Country of the firm address. Leave empty if unknown.', aliases: ['country', 'region', 'addresscountry', 'drzava', 'država', 'zemlja']},
  {key: 'notes', label: 'Notes', required: false, type: 'text', max: 4000, example: 'Ugovor br. 404-17/2026', format: 'Text, up to 4,000 characters', help: 'Internal notes, such as the contract number.', aliases: ['notes', 'note', 'comments', 'napomena', 'napomene', 'beleske', 'beleške']},
  {key: 'scopeLat', label: 'Area latitude', required: false, type: 'number', min: -90, max: 90, example: '43.8563', format: 'Decimal degrees, -90 to 90', help: 'Centre of the covered area on the map. Use together with longitude and radius.', aliases: ['scopelat', 'lat', 'latitude', 'sirina', 'širina', 'geosirina']},
  {key: 'scopeLng', label: 'Area longitude', required: false, type: 'number', min: -180, max: 180, example: '19.8487', format: 'Decimal degrees, -180 to 180', help: 'Centre of the covered area on the map.', aliases: ['scopelng', 'lng', 'lon', 'longitude', 'duzina', 'dužina', 'geoduzina']},
  {key: 'scopeRadius', label: 'Area radius (m)', required: false, type: 'number', min: 50, max: 50000, example: '500', format: 'Whole metres, 50 to 50,000', help: 'Radius around the centre. Tickets inside it are matched to this contract.', aliases: ['scoperadius', 'radius', 'radijus', 'poluprecnik', 'poluprečnik']},
];

const fold = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'dj').replace(/[^a-z0-9]/g, '');

/** Pick the source column for each schema field from the file's headers. */
export function autoMapColumns(columns: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  const used = new Set<string>();
  // Exact matches first (key or alias), then "header contains alias".
  for (const pass of ['exact', 'contains'] as const) {
    for (const f of CONTRACT_SCHEMA) {
      if (out[f.key]) continue;
      const names = [f.key, ...f.aliases].map(fold).filter(n => n.length > 1);
      const hit = columns.find(c => !used.has(c) && (pass === 'exact' ? names.includes(fold(c)) : names.some(n => n.length > 3 && fold(c).includes(n))));
      if (hit) { out[f.key] = hit; used.add(hit); }
    }
  }
  return out;
}

const pad = (n: number) => String(n).padStart(2, '0');
const validYmd = (y: number, m: number, d: number) => { const dt = new Date(Date.UTC(y, m - 1, d)); return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d && y >= 1990 && y <= 2100; };

/** Normalise a date to YYYY-MM-DD. Accepts YYYY-MM-DD, DD.MM.YYYY, Excel serial numbers and Date objects. */
export function parseDate(v: unknown): string | null {
  if (v instanceof Date && !isNaN(v.getTime())) return `${v.getFullYear()}-${pad(v.getMonth() + 1)}-${pad(v.getDate())}`;
  if (typeof v === 'number' && v > 20000 && v < 80000) { const d = new Date(Date.UTC(1899, 11, 30) + Math.round(v) * 86400000); return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`; }
  const s = String(v ?? '').trim();
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ].*)?$/);
  if (m && validYmd(+m[1], +m[2], +m[3])) return `${m[1]}-${pad(+m[2])}-${pad(+m[3])}`;
  m = s.match(/^(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})\.?$/);
  if (m && validYmd(+m[3], +m[2], +m[1])) return `${m[3]}-${pad(+m[2])}-${pad(+m[1])}`;
  if (/^\d{5}$/.test(s)) return parseDate(Number(s));
  return null;
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const COUNTRY_ALIASES: Record<string, string> = {srb: 'SRB', rs: 'SRB', serbia: 'SRB', srbija: 'SRB', eu: 'EU', europe: 'EU', evropa: 'EU', usa: 'USA', us: 'USA', sad: 'USA', unitedstates: 'USA', can: 'CAN', ca: 'CAN', canada: 'CAN', kanada: 'CAN'};

export type ContractRow = {contractor: string; road: string; start: string; end: string; poc: string; email: string; phone: string; scope: string; additionalRoads: string[]; address: string; addressCountry: string; notes: string; scopeLat?: number; scopeLng?: number; scopeRadius?: number};
export type RowCheck = {value: ContractRow | null; errors: string[]};

/** Validate and normalise one row. Errors are English templates with {0} for the field label. */
export function checkRow(raw: Record<string, unknown>): RowCheck {
  const errors: string[] = [];
  const out: Record<string, any> = {};
  const err = (f: SchemaField, msg: string) => errors.push(msg.replace('{0}', f.label));
  for (const f of CONTRACT_SCHEMA) {
    const v = raw[f.key];
    const text = v instanceof Date ? '' : Array.isArray(v) ? v.map(x => String(x).trim()).filter(Boolean).join('; ') : String(v ?? '').trim();
    const empty = v == null || (text === '' && !(v instanceof Date));
    if (empty) { if (f.required) err(f, '{0} is required.'); continue; }
    switch (f.type) {
      case 'date': { const d = parseDate(v); if (!d) err(f, '{0}: use YYYY-MM-DD or DD.MM.YYYY.'); else out[f.key] = d; break; }
      case 'email': if (!EMAIL.test(text) || text.length > (f.max || 250)) err(f, '{0}: not a valid email address.'); else out[f.key] = text.toLowerCase(); break;
      case 'phone': if (!/^[+\d\s().\-/]{5,40}$/.test(text)) err(f, '{0}: use digits, spaces and + - ( ) only.'); else out[f.key] = text; break;
      case 'number': {
        const n = Number(text.replace(',', '.'));
        if (!Number.isFinite(n) || (f.min !== undefined && n < f.min) || (f.max !== undefined && n > f.max)) err(f, '{0}: out of range.'); else out[f.key] = n;
        break;
      }
      case 'country': { const c = COUNTRY_ALIASES[text.toLowerCase().replace(/[^a-z]/g, '')]; if (!c) err(f, '{0}: use SRB, EU, USA or CAN.'); else out[f.key] = c; break; }
      case 'list': { const list = text.split(/[;\n]/).map(x => x.trim()).filter(Boolean); if (text.length > (f.max || 1000)) err(f, '{0} is too long.'); else out[f.key] = list; break; }
      default: if (f.max && text.length > f.max) err(f, '{0} is too long.'); else out[f.key] = text.replace(/\s+/g, ' ');
    }
  }
  if (out.start && out.end && out.end < out.start) errors.push('Warranty ends before it begins.');
  const area = ['scopeLat', 'scopeLng', 'scopeRadius'].filter(k => out[k] !== undefined).length;
  if (area > 0 && area < 3) errors.push('Map area needs latitude, longitude and radius together.');
  if (errors.length) return {value: null, errors};
  return {value: {phone: '', scope: '', additionalRoads: [], address: '', addressCountry: '', notes: '', ...out} as unknown as ContractRow, errors};
}

/** Contracts count as duplicates when firm, road and warranty dates match. */
export const contractKey = (c: {contractor: string; road: string; start: string; end: string}) => [fold(c.contractor), fold(c.road), c.start, c.end].join('|');
