'use client';
// Public progress view for a resident report: the seven repair steps with dates. No internal details.
import {useEffect, useState} from 'react';
import {Check} from 'lucide-react';
import {tx, useLang, LangSwitch, locale} from '@/lib/i18n';
import {instance} from '@/lib/instance';
import type {PublicStatus} from '@/lib/public-report';

const OUTCOME: Record<PublicStatus['outcome'], string> = {
  'in-progress': 'The team is working on it.',
  'repaired': 'Repaired and checked. Thank you for reporting it.',
  'not-a-defect': 'The team reviewed this location and found no repair was needed.',
  'merged': 'This report was combined with an earlier report of the same problem. Its progress is shown below.',
  'on-hold': 'Work is paused for now, for example while waiting for better weather or materials.',
};
const day = (iso?: string) => iso ? new Date(iso).toLocaleDateString(locale(), {dateStyle: 'medium'}) : '';

export default function PublicTrack({initialCode}: {initialCode?: string}) {
  useLang();
  const [code, setCode] = useState(initialCode || '');
  const [data, setData] = useState<PublicStatus | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function look(c: string) {
    if (!c.trim()) return;
    setBusy(true); setError('');
    try {
      const r = await fetch('/api/public/track?code=' + encodeURIComponent(c.trim()));
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setData(null); setError(tx(d.error || 'No report was found with this code. Check the code and try again.')); return; }
      setData(d);
      if (!initialCode || initialCode !== d.code) history.replaceState(null, '', '/track/' + encodeURIComponent(d.code));
    } catch { setError(tx('No connection. Check your internet and try again.')); }
    finally { setBusy(false); }
  }
  useEffect(() => { if (initialCode) void look(initialCode); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <main className="public-page">
    <header className="public-head">
      <a href="/concept"><img src={instance.logo} alt={tx('PaveLedger')}/></a>
      <LangSwitch/>
    </header>
    <section className="public-card">
      <p className="eyebrow">{tx('FOLLOW A REPORT')}</p>
      <h1>{tx('Where is my report?')}</h1>
      <form className="track-form" onSubmit={e => { e.preventDefault(); void look(code); }}>
        <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="ABCDE-23456" aria-label={tx('Tracking code')} autoCapitalize="characters" spellCheck={false}/>
        <button className="primary" disabled={busy}>{tx(busy ? 'Checking…' : 'Check')}</button>
      </form>
      {error && <p className="access-error" role="alert">{error}</p>}
      {data && <div className="track-result">
        <h2>{data.address || tx(data.road)}</h2>
        <p className="muted">{tx('Reported {0} · last update {1}', [day(data.reported), day(data.updated)])}{data.reports > 1 ? ' · ' + tx('{0} residents reported this', [String(data.reports)]) : ''}</p>
        <p className={'track-outcome ' + data.outcome}>{tx(OUTCOME[data.outcome])}</p>
        <ol className="track-steps">
          {data.steps.map((s, i) => <li key={s.label} className={s.state}>
            <span className="dot">{s.state === 'done' ? <Check size={14}/> : i + 1}</span>
            <div><strong>{tx(s.label)}</strong>{s.at && <small>{day(s.at)}</small>}{s.state === 'skipped' && <small>{tx('Not needed')}</small>}</div>
          </li>)}
        </ol>
      </div>}
      <p className="public-links"><a href="/report">{tx('Report another problem')}</a></p>
    </section>
  </main>;
}
