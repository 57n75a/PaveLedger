'use client';
// Interface language. English is the source text; each deployment offers the languages in its instance profile
// (Serbia: Serbian Latin and English; Canada: English and French) and starts in the profile's default.
// Text is keyed by its English wording, so stored values (statuses, roles, actions) stay English in the database
// and are translated only when shown. Keys with {0}, {1}… are templates and also match dynamic server messages.
import React, {createContext, useContext, useEffect, useState} from 'react';
import {sr} from './i18n-sr';
import {fr} from './i18n-fr';
import {instance, type Lang} from './instance';
import {toCyrillic} from './cyrillic';
export type {Lang} from './instance';

export const LANGS: Lang[] = instance.languages;
// Cyrillic uses the Serbian (Latin) translations and is transliterated as it is shown.
const DICTS: Partial<Record<Lang, Record<string, string>>> = {sr, 'sr-cyrl': sr, fr};
const STORAGE_KEY = 'paveledger-lang';
let current: Lang = instance.defaultLang;
const dict = () => DICTS[current];

export function getLang(): Lang { return current; }
/** Locale for dates and numbers in the current language. */
export function locale(): string | undefined { return instance.locales[current]; }

const cache = new Map<string, string>();
const templateCache = new Map<Lang, {re: RegExp; out: string}[]>();
function compiled() {
  const have = templateCache.get(current); if (have) return have;
  const d = dict() || {}; const list: {re: RegExp; out: string}[] = [];
  for (const k of Object.keys(d)) {
    if (!/\{\d+\}/.test(k)) continue;
    try { list.push({re: new RegExp('^' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\{(\d+)\\\}/g, '(?<v$1>[\\s\\S]+?)') + '$'), out: d[k]}); } catch {}
  }
  templateCache.set(current, list); return list;
}
function fill(pattern: string, vars: unknown[]) { return pattern.replace(/\{(\d+)\}/g, (m, i) => (Number(i) < vars.length ? String(vars[Number(i)] ?? '') : m)); }

function lookup(key: string): string | undefined {
  const d = dict(); if (!d) return undefined;
  if (Object.prototype.hasOwnProperty.call(d, key)) return d[key];
  const hit = cache.get(current + '\u0000' + key);
  if (hit !== undefined) return hit;
  let out: string | undefined;
  for (const {re, out: target} of compiled()) {
    const m = re.exec(key);
    if (m) { const g = m.groups || {}; out = target.replace(/\{(\d+)\}/g, (_, i) => translate(g['v' + i] ?? '')); break; }
  }
  if (cache.size > 5000) cache.clear();
  cache.set(current + '\u0000' + key, out ?? key);
  return out;
}
function translate(text: string): string {
  if (!dict() || !text || !/[A-Za-z]/.test(text)) return text;
  const lead = text.match(/^\s*/)![0], trail = text.slice(lead.length).match(/\s*$/)![0];
  const core = text.slice(lead.length, text.length - trail.length);
  const found = lookup(core);
  return found === undefined ? text : lead + found + trail;
}

function tLatin<T>(key: T, vars?: unknown[]): T {
  if (typeof key !== 'string') return key;
  if (!vars) return translate(key) as T;
  const d = dict();
  if (!d) return fill(key, vars) as T;
  const lead = key.match(/^\s*/)![0], trail = key.slice(lead.length).match(/\s*$/)![0];
  const core = key.slice(lead.length, key.length - trail.length);
  const pattern = Object.prototype.hasOwnProperty.call(d, core) ? d[core] : core;
  const filled = lead + fill(pattern, vars) + trail;
  // An untranslated template may still match a server message pattern once filled.
  return (pattern === core ? translate(filled) : filled) as T;
}

/** Translate English UI text. Non-string values pass through unchanged. */
export function t<T>(key: T, vars?: unknown[]): T {
  const out = tLatin(key, vars);
  return (current === 'sr-cyrl' && typeof out === 'string' ? toCyrillic(out) : out) as T;
}

const LangContext = createContext<{lang: Lang; setLang: (l: Lang) => void}>({lang: instance.defaultLang, setLang: () => {}});
const HTML_LANG: Record<Lang, string> = {sr: 'sr-Latn', 'sr-cyrl': 'sr-Cyrl', en: 'en', fr: 'fr-CA'};

export function LangProvider({children}: {children: React.ReactNode}) {
  const [lang, setState] = useState<Lang>(instance.defaultLang);
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch {}
    if (saved && (LANGS as string[]).includes(saved)) { current = saved as Lang; setState(saved as Lang); }
  }, []);
  useEffect(() => { document.documentElement.lang = HTML_LANG[lang]; }, [lang]);
  const setLang = (l: Lang) => { current = l; cache.clear(); try { localStorage.setItem(STORAGE_KEY, l); } catch {} setState(l); };
  current = lang;
  return <LangContext.Provider value={{lang, setLang}}>{children}</LangContext.Provider>;
}

/** Re-render this component when the language changes. */
export function useLang() { return useContext(LangContext); }

export function Flag({lang, size = 20}: {lang: Lang; size?: number}) {
  const w = size, h = Math.round(size * 2 / 3);
  // Official state flag of Serbia with the coat of arms (artwork: flag-icons, MIT), fitted to 3:2.
  if (lang === 'sr' || lang === 'sr-cyrl') return <img src="/flags/rs.png" width={w} height={h} alt="" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0, display: 'block', objectFit: 'cover'}}/>;
  if (lang === 'fr') return <svg width={w} height={h} viewBox="0 0 3 2" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0}}><rect width="1" height="2" fill="#002654"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ce1126"/></svg>;
  // English shows the Canadian flag on the Canadian instance and the UK flag elsewhere.
  if (instance.id === 'ca') return <svg width={w} height={h} viewBox="0 0 120 80" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0}}><rect width="120" height="80" fill="#fff"/><rect width="30" height="80" fill="#d52b1e"/><rect x="90" width="30" height="80" fill="#d52b1e"/><path fill="#d52b1e" d="M60 14l-5 10-6-3 3 15-8-8-2 4-8-2 3 9-4 2 15 12-2 5 13-2v13h2V56l13 2-2-5 15-12-4-2 3-9-8 2-2-4-8 8 3-15-6 3z"/></svg>;
  return <svg width={w} height={h} viewBox="0 0 60 40" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0}}><clipPath id="pl-uk"><rect width="60" height="40"/></clipPath><g clipPath="url(#pl-uk)"><rect width="60" height="40" fill="#012169"/><path d="M0,0 60,40M60,0 0,40" stroke="#fff" strokeWidth="8"/><path d="M0,0 60,40M60,0 0,40" stroke="#C8102E" strokeWidth="3"/><path d="M30,0V40M0,20H60" stroke="#fff" strokeWidth="12"/><path d="M30,0V40M0,20H60" stroke="#C8102E" strokeWidth="7"/></g></svg>;
}

const NAMES: Record<Lang, string> = {sr: 'Srpski (latinica)', 'sr-cyrl': 'Српски (ћирилица)', en: 'English', fr: 'Français'};
const CODES: Record<Lang, string> = {sr: 'LAT', 'sr-cyrl': 'ЋИР', en: 'EN', fr: 'FR'};
const LABEL: Record<Lang, string> = {sr: 'Jezik', 'sr-cyrl': 'Језик', en: 'Language', fr: 'Langue'};

/** Language dropdown: the current flag with an arrow, and the flags stacked directly beneath it. Opens on hover (desktop) or tap. */
export function LangSwitch() {
  const {lang, setLang} = useLang();
  const [open, setOpen] = useState(false);
  const closeTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const hoverable = () => typeof window !== 'undefined' && window.matchMedia('(hover: hover)').matches;
  const cancelClose = () => { if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; } };
  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('click', close); window.addEventListener('keydown', key);
    return () => { window.removeEventListener('click', close); window.removeEventListener('keydown', key); };
  }, [open]);
  useEffect(() => cancelClose, []);
  // Current language first, then the others, one under the other.
  const ordered = [lang, ...LANGS.filter(l => l !== lang)];
  return <div className={'lang-switch' + (open ? ' open' : '')} onClick={e => e.stopPropagation()}
    onMouseEnter={() => { if (hoverable()) { cancelClose(); setOpen(true); } }}
    onMouseLeave={() => { if (hoverable()) { cancelClose(); closeTimer.current = setTimeout(() => setOpen(false), 150); } }}>
    <button type="button" className="lang-trigger" aria-haspopup="listbox" aria-expanded={open} aria-label={LABEL[lang] + ': ' + NAMES[lang]} title={NAMES[lang]} onClick={() => (hoverable() ? setOpen(true) : setOpen(o => !o))}>
      <Flag lang={lang} size={22}/>{LANGS.length > 1 && <span className="lang-code">{CODES[lang]}</span>}
      <svg className="lang-caret" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
    </button>
    {open && <ul className="lang-menu" role="listbox" aria-label={LABEL[lang]}>{ordered.map(l => <li key={l} role="option" aria-selected={l === lang}>
      <button type="button" className={l === lang ? 'active' : ''} title={NAMES[l]} aria-label={NAMES[l]} onClick={() => { setLang(l); setOpen(false); }}><Flag lang={l} size={22}/><span className="lang-code">{CODES[l]}</span></button>
    </li>)}</ul>}
  </div>;
}

/** Pick a value per language, for examples and data that should not be looked up by English text. */
export function byLang<T>(values: Partial<Record<Lang, T>> & {en: T}): T {
  if (current === 'sr-cyrl' && values['sr-cyrl'] === undefined && values.sr !== undefined) return (typeof values.sr === 'string' ? toCyrillic(values.sr) : values.sr) as T;
  return values[current] ?? values.en;
}

/** Alias used in components where `t` is a common variable name. */
export const tx = t;
