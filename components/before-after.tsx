'use client';
// Side-by-side proof of a repair: drag the handle (or use the arrow keys) to compare before and after.
import {useRef, useState} from 'react';
import {tx, useLang, locale} from '@/lib/i18n';

const day = (iso: string) => new Date(iso).toLocaleDateString(locale(), {dateStyle: 'medium'});

export default function BeforeAfter({before, after, beforeAt, afterAt, afterLabel, illustrative}: {
  before: string; after: string; beforeAt: string; afterAt: string; afterLabel: string; illustrative?: boolean;
}) {
  useLang();
  const [pos, setPos] = useState(50);
  const [mode, setMode] = useState<'slider' | 'side'>('slider');
  const box = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const move = (clientX: number) => {
    const r = box.current?.getBoundingClientRect();
    if (r && r.width) setPos(Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100)));
  };
  const days = Math.max(0, Math.round((Date.parse(afterAt) - Date.parse(beforeAt)) / 86_400_000));

  return <section className="before-after">
    <div className="ba-head">
      <h3>{tx('Before and after')}</h3>
      <div className="map-seg" role="group" aria-label={tx('Comparison view')}>
        <button type="button" className={mode === 'slider' ? 'active' : ''} onClick={() => setMode('slider')}>{tx('Slider')}</button>
        <button type="button" className={mode === 'side' ? 'active' : ''} onClick={() => setMode('side')}>{tx('Side by side')}</button>
      </div>
    </div>
    {mode === 'slider' ? <div ref={box} className="ba-slider"
      onPointerDown={e => { dragging.current = true; (e.target as HTMLElement).setPointerCapture?.(e.pointerId); move(e.clientX); }}
      onPointerMove={e => { if (dragging.current) move(e.clientX); }}
      onPointerUp={() => { dragging.current = false; }} onPointerCancel={() => { dragging.current = false; }}>
      <img src={after} alt={tx('After: {0}', [tx(afterLabel)])} draggable={false}/>
      <div className="ba-before" style={{clipPath: `inset(0 ${100 - pos}% 0 0)`}}><img src={before} alt={tx('Before: reported damage')} draggable={false}/></div>
      <span className="ba-tag left">{tx('Before')} · {day(beforeAt)}</span>
      <span className="ba-tag right">{tx('After')} · {day(afterAt)}</span>
      <div className="ba-handle" style={{left: pos + '%'}} role="slider" tabIndex={0} aria-label={tx('Drag to compare before and after')}
        aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pos)}
        onKeyDown={e => { if (e.key === 'ArrowLeft') setPos(p => Math.max(0, p - 5)); if (e.key === 'ArrowRight') setPos(p => Math.min(100, p + 5)); }}>
        <i/>
      </div>
    </div> : <div className="ba-side">
      <figure><img src={before} alt={tx('Before: reported damage')}/><figcaption>{tx('Before')} · {day(beforeAt)}</figcaption></figure>
      <figure><img src={after} alt={tx('After: {0}', [tx(afterLabel)])}/><figcaption>{tx('After')} · {day(afterAt)}</figcaption></figure>
    </div>}
    <p className="muted small">{tx('{0} days from report to repair photo.', [String(days)])}{illustrative ? ' ' + tx('Demo images are illustrations, not field evidence.') : ''}</p>
  </section>;
}
