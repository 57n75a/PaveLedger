'use client';
// Interface language. Serbian (Latin) is the default; English is the source text.
// Text is keyed by its English wording, so stored values (statuses, roles, actions) stay English in the database
// and are translated only when shown. Keys with {0}, {1}… are templates and also match dynamic server messages.
import React, {createContext, useContext, useEffect, useState} from 'react';
import {sr} from './i18n-sr';

export type Lang = 'sr' | 'en';
export const LANGS: Lang[] = ['sr', 'en'];
const STORAGE_KEY = 'paveledger-lang';
let current: Lang = 'sr';

export function getLang(): Lang { return current; }
/** Locale for dates and numbers. English keeps the browser default, as before. */
export function locale(): string | undefined { return current === 'sr' ? 'sr-Latn-RS' : undefined; }

const cache = new Map<string, string>();
let templates: {re: RegExp; out: string}[] | null = null;
function compiled() {
  if (templates) return templates;
  templates = [];
  for (const k of Object.keys(sr)) {
    if (!/\{\d+\}/.test(k)) continue;
    try { templates.push({re: new RegExp('^' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\{(\d+)\\\}/g, '(?<v$1>[\\s\\S]+?)') + '$'), out: sr[k]}); } catch {}
  }
  return templates;
}
function fill(pattern: string, vars: unknown[]) { return pattern.replace(/\{(\d+)\}/g, (m, i) => (Number(i) < vars.length ? String(vars[Number(i)] ?? '') : m)); }

function lookup(key: string): string | undefined {
  if (Object.prototype.hasOwnProperty.call(sr, key)) return sr[key];
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  let out: string | undefined;
  for (const {re, out: target} of compiled()) {
    const m = re.exec(key);
    if (m) { const g = m.groups || {}; out = target.replace(/\{(\d+)\}/g, (_, i) => translate(g['v' + i] ?? '')); break; }
  }
  if (cache.size > 5000) cache.clear();
  cache.set(key, out ?? key);
  return out;
}
function translate(text: string): string {
  if (current === 'en' || !text || !/[A-Za-z]/.test(text)) return text;
  const lead = text.match(/^\s*/)![0], trail = text.slice(lead.length).match(/\s*$/)![0];
  const core = text.slice(lead.length, text.length - trail.length);
  const found = lookup(core);
  return found === undefined ? text : lead + found + trail;
}

/** Translate English UI text. Non-string values pass through unchanged. */
export function t<T>(key: T, vars?: unknown[]): T {
  if (typeof key !== 'string') return key;
  if (!vars) return translate(key) as T;
  if (current === 'en') return fill(key, vars) as T;
  const lead = key.match(/^\s*/)![0], trail = key.slice(lead.length).match(/\s*$/)![0];
  const core = key.slice(lead.length, key.length - trail.length);
  const pattern = Object.prototype.hasOwnProperty.call(sr, core) ? sr[core] : core;
  const filled = lead + fill(pattern, vars) + trail;
  // An untranslated template may still match a server message pattern once filled.
  return (pattern === core ? translate(filled) : filled) as T;
}

const LangContext = createContext<{lang: Lang; setLang: (l: Lang) => void}>({lang: 'sr', setLang: () => {}});

export function LangProvider({children}: {children: React.ReactNode}) {
  const [lang, setState] = useState<Lang>('sr');
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch {}
    if (saved === 'en' || saved === 'sr') { current = saved; setState(saved); }
  }, []);
  useEffect(() => { document.documentElement.lang = lang === 'sr' ? 'sr-Latn' : 'en'; }, [lang]);
  const setLang = (l: Lang) => { current = l; cache.clear(); try { localStorage.setItem(STORAGE_KEY, l); } catch {} setState(l); };
  current = lang;
  return <LangContext.Provider value={{lang, setLang}}>{children}</LangContext.Provider>;
}

/** Re-render this component when the language changes. */
export function useLang() { return useContext(LangContext); }

export function Flag({lang, size = 20}: {lang: Lang; size?: number}) {
  const w = size, h = Math.round(size * 2 / 3);
  if (lang === 'sr') return <svg width={w} height={h} viewBox="0 0 3 2" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0}}><rect width="3" height="2" fill="#fff"/><rect width="3" height="1.333" fill="#0c4076"/><rect width="3" height="0.667" fill="#c6363c"/></svg>;
  return <svg width={w} height={h} viewBox="0 0 60 40" aria-hidden="true" style={{borderRadius: 2, boxShadow: '0 0 0 1px #0002', flexShrink: 0}}><clipPath id="pl-uk"><rect width="60" height="40"/></clipPath><g clipPath="url(#pl-uk)"><rect width="60" height="40" fill="#012169"/><path d="M0,0 60,40M60,0 0,40" stroke="#fff" strokeWidth="8"/><path d="M0,0 60,40M60,0 0,40" stroke="#C8102E" strokeWidth="3"/><path d="M30,0V40M0,20H60" stroke="#fff" strokeWidth="12"/><path d="M30,0V40M0,20H60" stroke="#C8102E" strokeWidth="7"/></g></svg>;
}

const NAMES: Record<Lang, string> = {sr: 'Srpski', en: 'English'};

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
    <button type="button" className="lang-trigger" aria-haspopup="listbox" aria-expanded={open} aria-label={lang === 'sr' ? 'Jezik: Srpski' : 'Language: English'} title={NAMES[lang]} onClick={() => (hoverable() ? setOpen(true) : setOpen(o => !o))}>
      <Flag lang={lang} size={22}/>
      <svg className="lang-caret" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
    </button>
    {open && <ul className="lang-menu" role="listbox" aria-label={lang === 'sr' ? 'Jezik' : 'Language'}>{ordered.map(l => <li key={l} role="option" aria-selected={l === lang}>
      <button type="button" className={l === lang ? 'active' : ''} title={NAMES[l]} aria-label={NAMES[l]} onClick={() => { setLang(l); setOpen(false); }}><Flag lang={l} size={22}/></button>
    </li>)}</ul>}
  </div>;
}

/** Pick a value per language, for examples and data that should not be looked up by English text. */
export function byLang<T>(values: Record<Lang, T>): T { return values[current]; }

/** Alias used in components where `t` is a common variable name. */
export const tx = t;
