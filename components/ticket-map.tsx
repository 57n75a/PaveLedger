'use client';
// City-wide map of every ticket the viewer can see, coloured by severity, with filters.
import {useEffect, useMemo, useRef, useState} from 'react';
import 'leaflet/dist/leaflet.css';
import {tx, useLang} from '@/lib/i18n';
import {instance} from '@/lib/instance';

type MapTicket = {id: string; title: string; road: string; address?: string; lat: number; lng: number; severity: string; status: string; team: string; contractor?: string; reopened?: number; observations?: number};

const SEVERITY_COLOR: Record<string, string> = {Urgent: '#c9203d', Standard: '#e0892b', Low: '#3b7dd8'};
const CLOSED = ['Verified closed', 'Rejected', 'Duplicate'];
const esc = (s: string) => s.replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c] as string));

export default function TicketMap({tickets, teams, onOpenTicket}: {tickets: MapTicket[]; teams: string[]; onOpenTicket: (id: string) => void}) {
  useLang();
  const box = useRef<HTMLDivElement>(null);
  const lib = useRef<any>(null), map = useRef<any>(null), layer = useRef<any>(null);
  const openRef = useRef(onOpenTicket); openRef.current = onOpenTicket;
  const [ready, setReady] = useState(false);
  const [state, setState] = useState<'open' | 'closed' | 'all'>('open');
  const [team, setTeam] = useState('all');
  const [sev, setSev] = useState<Record<string, boolean>>({Urgent: true, Standard: true, Low: true});

  const shown = useMemo(() => tickets.filter(t =>
    Number.isFinite(t.lat) && Number.isFinite(t.lng) &&
    (state === 'all' || (state === 'open') !== CLOSED.includes(t.status)) &&
    (team === 'all' || t.team === team) &&
    (sev[t.severity] ?? true)
  ), [tickets, state, team, sev]);

  // Create the map once.
  useEffect(() => {
    let dead = false;
    (async () => {
      const mod: any = await import('leaflet');
      const L: any = mod.default || mod;
      if (dead || !box.current) return;
      lib.current = L;
      const m = L.map(box.current, {scrollWheelZoom: true}).setView([instance.mapCenter.lat, instance.mapCenter.lng], 12);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors', referrerPolicy: 'strict-origin-when-cross-origin'}).addTo(m);
      layer.current = L.layerGroup().addTo(m);
      m.on('popupopen', (e: any) => {
        const btn = e.popup.getElement()?.querySelector('[data-open-ticket]');
        if (btn) btn.addEventListener('click', () => openRef.current(btn.getAttribute('data-open-ticket')));
      });
      map.current = m;
      setReady(true);
    })();
    return () => { dead = true; map.current?.remove(); map.current = null; };
  }, []);

  // Redraw markers when filters or data change, and fit the view to them.
  useEffect(() => {
    const L = lib.current, m = map.current, g = layer.current;
    if (!ready || !L || !m || !g) return;
    g.clearLayers();
    const pts: [number, number][] = [];
    for (const t of shown) {
      const isClosed = CLOSED.includes(t.status);
      const color = SEVERITY_COLOR[t.severity] || '#6b7a90';
      const radius = Math.min(14, 7 + Math.max(0, (t.observations || 1) - 1));
      const mk = L.circleMarker([t.lat, t.lng], {radius, color: '#fff', weight: 2, fillColor: color, fillOpacity: isClosed ? 0.35 : 0.9});
      mk.bindTooltip(esc(t.road), {direction: 'top'});
      mk.bindPopup(
        `<div class="map-pop"><small>${esc(t.id)} · ${esc(tx(t.severity))}</small><strong>${esc(tx(t.title || t.road))}</strong>` +
        `<span>${esc(t.address || t.road)}</span><span>${esc(tx(t.status))} · ${esc(t.team)}</span>` +
        (t.reopened ? `<span class="map-warn">${esc(tx('Reopened {0} times', [String(t.reopened)]))}</span>` : '') +
        `<button type="button" data-open-ticket="${esc(t.id)}">${esc(tx('Open ticket'))}</button></div>`
      );
      mk.addTo(g);
      pts.push([t.lat, t.lng]);
    }
    const fit = () => {
      m.invalidateSize();
      if (pts.length === 1) m.setView(pts[0], 15);
      else if (pts.length > 1) m.fitBounds(pts, {padding: [40, 40], maxZoom: 16});
    };
    fit();
    // The panel may still be laying out on first show; fit again once it has its final size.
    const t = setTimeout(fit, 200);
    return () => clearTimeout(t);
  }, [shown, ready]);

  const counts = {Urgent: 0, Standard: 0, Low: 0} as Record<string, number>;
  shown.forEach(t => { counts[t.severity] = (counts[t.severity] || 0) + 1; });

  return <section className="panel ticket-map">
    <div className="section-head">
      <div><h2>{tx('Ticket map')}</h2><p>{tx('{0} tickets shown. Click a point to see the ticket.', [String(shown.length)])}</p></div>
    </div>
    <div className="map-filters">
      <div className="map-seg" role="group" aria-label={tx('Status')}>
        {(['open', 'closed', 'all'] as const).map(v => <button key={v} type="button" className={state === v ? 'active' : ''} onClick={() => setState(v)}>{tx(v === 'open' ? 'Open' : v === 'closed' ? 'Closed' : 'All')}</button>)}
      </div>
      <select value={team} onChange={e => setTeam(e.target.value)} aria-label={tx('Team')}>
        <option value="all">{tx('All teams')}</option>
        {teams.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
      <div className="map-legend">
        {Object.keys(SEVERITY_COLOR).map(s => <label key={s}>
          <input type="checkbox" checked={sev[s]} onChange={e => setSev({...sev, [s]: e.target.checked})}/>
          <i style={{background: SEVERITY_COLOR[s]}}/>{tx(s)} <b>{counts[s] || 0}</b>
        </label>)}
      </div>
    </div>
    <div ref={box} className="map-canvas" role="region" aria-label={tx('Ticket map')}/>
    <p className="muted map-note">{tx('Larger points have more observations. Faded points are closed.')}</p>
  </section>;
}
