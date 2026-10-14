'use client';
import {useEffect, useId, useRef, useState} from 'react';
import {MapPin} from 'lucide-react';
import {authorizedFetch} from '@/lib/supabase-browser';
import {tx, useLang, getLang} from '@/lib/i18n';

export type Suggestion = {label: string; lat: number; lng: number; street: string; city: string};

/** Address field with suggestions from this deployment's country as you type. */
export default function AddressSuggest({value, onChange, onPick, placeholder, near, inputProps}: {
  value: string; onChange: (v: string) => void; onPick: (s: Suggestion) => void; placeholder?: string;
  near?: {lat: number; lng: number} | null; inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
}) {
  useLang();
  const [items, setItems] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [state, setState] = useState<'idle' | 'loading' | 'none' | 'error'>('idle');
  const typed = useRef(false);
  const listId = useId();

  useEffect(() => {
    const q = value.trim();
    if (!typed.current || q.length < 3) { setItems([]); setState('idle'); return; }
    let cancelled = false;
    const timer = setTimeout(async () => {
      setState('loading');
      try {
        const p = new URLSearchParams({q, lang: getLang()});
        if (near) { p.set('nearLat', String(near.lat)); p.set('nearLng', String(near.lng)); }
        const r = await authorizedFetch('/api/geocode/suggest?' + p.toString());
        const d = await r.json();
        if (cancelled) return;
        if (!r.ok) { setItems([]); setState('error'); return; }
        setItems(d); setActive(-1); setState(d.length ? 'idle' : 'none'); setOpen(true);
      } catch { if (!cancelled) { setItems([]); setState('error'); } }
    }, 350);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [value, near?.lat, near?.lng]);

  const pick = (s: Suggestion) => { typed.current = false; onPick(s); setOpen(false); setItems([]); };
  const showList = open && (items.length > 0 || state === 'none' || state === 'error');

  return <div className="addr-suggest">
    <input {...inputProps} value={value} placeholder={placeholder} autoComplete="off"
      role="combobox" aria-expanded={showList} aria-controls={listId} aria-autocomplete="list" aria-activedescendant={active >= 0 ? listId + '-' + active : undefined}
      onChange={e => { typed.current = true; onChange(e.target.value); }}
      onFocus={() => items.length && setOpen(true)}
      onBlur={() => setTimeout(() => setOpen(false), 150)}
      onKeyDown={e => {
        if (!showList || !items.length) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => (a + 1) % items.length); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => (a <= 0 ? items.length - 1 : a - 1)); }
        else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); pick(items[active]); }
        else if (e.key === 'Escape') setOpen(false);
      }}/>
    {state === 'loading' && <span className="addr-spin" aria-hidden="true"/>}
    {showList && <ul className="addr-list" id={listId} role="listbox">
      {items.map((s, i) => <li key={s.label + i} id={listId + '-' + i} role="option" aria-selected={i === active} className={i === active ? 'active' : ''}
        onMouseDown={e => { e.preventDefault(); pick(s); }} onMouseEnter={() => setActive(i)}>
        <MapPin size={15}/><span>{s.label}</span>
      </li>)}
      {state === 'none' && <li className="addr-empty">{tx('No matching address. Try the street and city, or enter coordinates.')}</li>}
      {state === 'error' && <li className="addr-empty">{tx('Address suggestions are unavailable right now. You can still use Find address on map or coordinates.')}</li>}
    </ul>}
  </div>;
}
