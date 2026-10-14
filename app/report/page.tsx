'use client';
// Public page: residents report a road problem without an account and get a tracking code.
import {useState} from 'react';
import dynamic from 'next/dynamic';
import {tx, useLang, LangSwitch} from '@/lib/i18n';
import {instance} from '@/lib/instance';
import AddressSuggest from '@/components/address-suggest';
import type {Picked} from '@/components/location-picker';

const LocationPicker = dynamic(() => import('@/components/location-picker'), {ssr: false, loading: () => <div className="picker-map picker-loading"/>});

export default function ReportPage() {
  useLang();
  const [where, setWhere] = useState<Picked | null>(null);
  const [address, setAddress] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState<{code: string; merged: boolean} | null>(null);
  const [preview, setPreview] = useState('');

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    if (!where) { setError(tx('Mark the location on the map, or use your location.')); return; }
    const f = new FormData(e.currentTarget);
    f.set('lat', String(where.lat)); f.set('lng', String(where.lng));
    if (where.accuracy) f.set('accuracy', String(where.accuracy));
    f.set('address', address);
    f.set('dangerous', f.get('dangerous') === 'on' ? 'true' : 'false');
    const photo = f.get('photo');
    if (photo instanceof File && photo.size === 0) f.delete('photo');
    setBusy(true);
    try {
      const r = await fetch('/api/public/report', {method: 'POST', body: f});
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(tx(d.error || 'The report could not be sent. Please try again.')); return; }
      setDone({code: d.code, merged: !!d.merged});
      window.scrollTo({top: 0, behavior: 'smooth'});
    } catch { setError(tx('No connection. Check your internet and try again.')); }
    finally { setBusy(false); }
  }

  return <main className="public-page">
    <header className="public-head">
      <a href="/concept"><img src={instance.logo} alt={tx('PaveLedger')}/></a>
      <LangSwitch/>
    </header>
    <section className="public-card">
      {done ? <div className="report-done" role="status">
        <p className="eyebrow">{tx('REPORT RECEIVED')}</p>
        <h1>{tx('Thank you. Your report has been sent.')}</h1>
        <p className="muted">{tx(done.merged ? 'This problem was already reported nearby, so your report was added to it. That helps the team prioritise it.' : 'The road maintenance team will review it. You can follow its progress with this code.')}</p>
        <div className="track-code"><span>{tx('Tracking code')}</span><strong>{done.code}</strong></div>
        <a className="primary" href={'/track/' + encodeURIComponent(done.code)}>{tx('Follow this report')}</a>
        <p className="muted small">{tx('Save the code or bookmark the page. No account is needed to check it.')}</p>
        <button type="button" className="text-button" onClick={() => { setDone(null); setWhere(null); setAddress(''); setPreview(''); }}>{tx('Report another problem')}</button>
      </div> : <>
        <p className="eyebrow">{tx('REPORT A ROAD PROBLEM')}</p>
        <h1>{tx('Seen a pothole or road damage?')}</h1>
        <p className="muted">{tx('Tell the municipality where it is. It takes a minute, and you get a code to follow the repair.')}</p>
        <form className="form report-form" onSubmit={submit} noValidate>
          <fieldset>
            <legend>{tx('1. Where is it?')}</legend>
            <AddressSuggest publicLookup value={address} onChange={setAddress} placeholder={tx('Street and number, or a nearby landmark')}
              onPick={s => { setAddress(s.label); setWhere({lat: s.lat, lng: s.lng, accuracy: 20}); }} inputProps={{'aria-label': tx('Address')}}/>
            <LocationPicker value={where} onChange={setWhere}/>
          </fieldset>
          <fieldset>
            <legend>{tx('2. What is the problem?')}</legend>
            <label>{tx('Description')}<textarea name="description" rows={4} required minLength={5} maxLength={1000} placeholder={tx('For example: deep pothole in the right lane, about half a metre wide.')}/></label>
            <label className="check"><input type="checkbox" name="dangerous"/> {tx('It is dangerous (risk of an accident or injury)')}</label>
          </fieldset>
          <fieldset>
            <legend>{tx('3. Photo (optional)')}</legend>
            <label className="photo-pick">
              <input type="file" name="photo" accept="image/jpeg,image/png,image/webp" capture="environment"
                onChange={e => { const f = e.target.files?.[0]; setPreview(f ? URL.createObjectURL(f) : ''); }}/>
              {preview ? <img src={preview} alt={tx('Selected photo')}/> : <span>{tx('Take or choose a photo')}</span>}
            </label>
            <p className="muted small">{tx('Please avoid faces and number plates.')}</p>
          </fieldset>
          <fieldset>
            <legend>{tx('4. Your email (optional)')}</legend>
            <label>{tx('Email')}<input type="email" name="email" autoComplete="email" placeholder={tx('Only used if the team needs to ask you something')}/></label>
          </fieldset>
          <label className="hp" aria-hidden="true">Website<input name="website" tabIndex={-1} autoComplete="off"/></label>
          {error && <p className="access-error" role="alert">{error}</p>}
          <button className="primary" disabled={busy}>{tx(busy ? 'Sending…' : 'Send report')}</button>
          <p className="muted small">{tx('Your report is stored by the municipality to plan repairs. It is not an emergency service: for immediate danger, call {0}.', [instance.emergency])}</p>
        </form>
      </>}
      <p className="public-links"><a href="/track">{tx('Check a report with your code')}</a></p>
    </section>
  </main>;
}
