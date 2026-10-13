'use client';
import {useEffect, useMemo, useRef, useState} from 'react';
import {Search, Maximize2, Download, ArrowUpRight, X, ZoomIn, ZoomOut} from 'lucide-react';
import {tx, useLang} from '@/lib/i18n';
import {colors, type State} from '@/lib/domain';
import {buildGraph, neighbours, toCypher, NODE_TYPES, type Graph, type GraphNode, type NodeType, type RelType} from '@/lib/graph';

const TYPE_COLOR: Record<NodeType, string> = {Ticket: '#365cbf', Team: '#0f766e', Person: '#7c3aed', Road: '#64748b', Contract: '#b45309', Contractor: '#be123c', Evidence: '#0891b2'};
const TYPE_PLURAL: Record<NodeType, string> = {Ticket: 'Tickets', Team: 'Teams', Person: 'People', Road: 'Roads', Contract: 'Contracts', Contractor: 'Contractors', Evidence: 'Evidence files'};
const TYPE_SINGULAR: Record<NodeType, string> = {Ticket: 'Ticket', Team: 'Team', Person: 'Person', Road: 'Road', Contract: 'Contract', Contractor: 'Contractor', Evidence: 'Evidence file'};
const RADIUS: Record<NodeType, number> = {Team: 14, Contractor: 13, Contract: 10, Road: 9, Person: 9, Ticket: 7, Evidence: 5};
const REL: Record<RelType, [string, string]> = { // [outgoing, incoming]
  IN_TEAM: ['in team', 'team ticket'], ASSIGNED_TO: ['assigned to', 'assigned ticket'], REPORTED_BY: ['reported by', 'reported ticket'],
  ON_ROAD: ['on road', 'ticket on this road'], COVERED_BY: ['covered by contract', 'covered ticket'], HANDLED_BY: ['handled by contractor', 'ticket handled'],
  HELD_BY: ['contract held by', 'holds contract'], APPLIES_TO: ['applies to road', 'contract for this road'], MEMBER_OF: ['member of', 'member'],
  WORKS_FOR: ['works for', 'employee'], DUPLICATE_OF: ['duplicate of', 'has duplicate'], HAS_EVIDENCE: ['evidence', 'evidence of ticket'],
};
const shortLabel = (n: GraphNode) => n.type === 'Ticket' ? '#' + (n.label.split('-').pop() || n.label) : n.label.length > 28 ? n.label.slice(0, 27) + '…' : n.label;
const OPEN = (st: unknown) => !['Verified closed', 'Rejected', 'Duplicate'].includes(String(st));

type Pos = {x: number; y: number; vx: number; vy: number; fixed?: boolean};
const hash = (s: string) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return (h >>> 0) / 4294967295; };

function download(name: string, content: string, type: string) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([content], {type})); a.download = name; a.click(); URL.revokeObjectURL(a.href); }

export default function GraphView({data, onOpenTicket}: {data: Pick<State, 'tickets' | 'members' | 'teams' | 'contracts'>; onOpenTicket: (id: string) => void}) {
  useLang();
  const [types, setTypes] = useState<Set<NodeType>>(new Set(['Ticket', 'Team', 'Person', 'Road', 'Contract', 'Contractor']));
  const [scope, setScope] = useState<'open' | 'all' | 'closed'>('open');
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [view, setView] = useState({x: 0, y: 0, k: 1});
  const [, setFrame] = useState(0);
  const svgRef = useRef<SVGSVGElement>(null);
  const pos = useRef(new Map<string, Pos>());
  const alpha = useRef(1);
  const drag = useRef<{id?: string; px: number; py: number; vx: number; vy: number; moved: boolean} | null>(null);

  // Full graph, then filtered by type and ticket scope. Nodes left without any edge are dropped (except teams).
  const full = useMemo(() => buildGraph(data, {evidence: types.has('Evidence')}), [data, types]);
  const graph: Graph = useMemo(() => {
    const keepTicket = (n: GraphNode) => scope === 'all' || (scope === 'open' ? OPEN(n.props.status) : !OPEN(n.props.status));
    const ids = new Set(full.nodes.filter(n => types.has(n.type) && (n.type !== 'Ticket' || keepTicket(n))).map(n => n.id));
    const edges = full.edges.filter(e => ids.has(e.source) && ids.has(e.target));
    const linked = new Set(edges.flatMap(e => [e.source, e.target]));
    const nodes = full.nodes.filter(n => ids.has(n.id) && (linked.has(n.id) || n.type === 'Team'));
    return {nodes, edges};
  }, [full, types, scope]);
  const degree = useMemo(() => { const d = new Map<string, number>(); for (const e of graph.edges) { d.set(e.source, (d.get(e.source) || 0) + 1); d.set(e.target, (d.get(e.target) || 0) + 1); } return d; }, [graph]);
  const radius = (n: GraphNode) => RADIUS[n.type] + Math.min(8, Math.sqrt(degree.get(n.id) || 0) * 1.4);

  // Seed new nodes near a stable spot per type; restart the layout when the graph changes.
  useEffect(() => {
    const ring = NODE_TYPES.indexOf.bind(NODE_TYPES);
    for (const n of graph.nodes) if (!pos.current.has(n.id)) {
      const a = ring(n.type) / NODE_TYPES.length * Math.PI * 2 + hash(n.id) * 0.9, r = 140 + hash(n.id + 'r') * 160;
      pos.current.set(n.id, {x: Math.cos(a) * r, y: Math.sin(a) * r, vx: 0, vy: 0});
    }
  }, [graph]);

  // Force layout: repulsion, springs along edges, gentle pull to the centre. Runs a few ticks per frame until it settles.
  const graphRef = useRef(graph); graphRef.current = graph;
  const running = useRef(0);
  const fitOnSettle = useRef(true);
  const step = () => {
    const g = graphRef.current, ns = g.nodes, P = pos.current;
    for (let n = 0; n < 3 && alpha.current > 0.01; n++) {
      const a = alpha.current;
      for (let i = 0; i < ns.length; i++) {
        const p = P.get(ns[i].id); if (!p) continue;
        for (let j = i + 1; j < ns.length; j++) {
          const o = P.get(ns[j].id); if (!o) continue;
          let dx = p.x - o.x, dy = p.y - o.y; let d2 = dx * dx + dy * dy;
          if (d2 > 250000) continue;
          if (d2 < 1) { dx = hash(ns[i].id) - 0.5; dy = hash(ns[j].id) - 0.5; d2 = 1; }
          const f = 2600 * a / d2, d = Math.sqrt(d2);
          p.vx += dx / d * f; p.vy += dy / d * f; o.vx -= dx / d * f; o.vy -= dy / d * f;
        }
        p.vx -= p.x * 0.003 * a; p.vy -= p.y * 0.003 * a;
      }
      for (const e of g.edges) {
        const s = P.get(e.source), t = P.get(e.target); if (!s || !t) continue;
        const dx = t.x - s.x, dy = t.y - s.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
        const rest = e.type === 'ON_ROAD' || e.type === 'APPLIES_TO' ? 70 : e.type === 'HAS_EVIDENCE' ? 35 : 100;
        const f = (d - rest) * 0.05 * a;
        t.vx -= dx / d * f; t.vy -= dy / d * f; s.vx += dx / d * f; s.vy += dy / d * f;
      }
      for (const nd of ns) { const p = P.get(nd.id); if (!p) continue; if (p.fixed) { p.vx = p.vy = 0; continue; } p.vx *= 0.6; p.vy *= 0.6; p.x += p.vx; p.y += p.vy; }
      alpha.current *= 0.985;
    }
    setFrame(f => f + 1);
    if (alpha.current > 0.01) running.current = requestAnimationFrame(step);
    else { running.current = 0; if (fitOnSettle.current) { fitOnSettle.current = false; fit(); } }
  };
  const kick = (to: number) => { alpha.current = Math.max(alpha.current, to); if (!running.current) running.current = requestAnimationFrame(step); };
  useEffect(() => { fitOnSettle.current = true; kick(1); }, [graph]);
  useEffect(() => () => { if (running.current) cancelAnimationFrame(running.current); }, []);

  function fit() {
    const g = graphRef.current, svg = svgRef.current; if (!svg || !g.nodes.length) return;
    const pts = g.nodes.map(n => pos.current.get(n.id)).filter(Boolean) as Pos[]; if (!pts.length) return;
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    const minX = Math.min(...xs) - 40, maxX = Math.max(...xs) + 40, minY = Math.min(...ys) - 40, maxY = Math.max(...ys) + 40;
    const {width, height} = svg.getBoundingClientRect();
    const k = Math.min(2, Math.max(0.2, Math.min(width / (maxX - minX), height / (maxY - minY))));
    setView({k, x: width / 2 - (minX + maxX) / 2 * k, y: height / 2 - (minY + maxY) / 2 * k});
  }
  const zoomBy = (f: number, cx?: number, cy?: number) => setView(v => {
    const svg = svgRef.current!; const r = svg.getBoundingClientRect();
    const px = cx ?? r.width / 2, py = cy ?? r.height / 2; const k = Math.min(4, Math.max(0.15, v.k * f));
    return {k, x: px - (px - v.x) * (k / v.k), y: py - (py - v.y) * (k / v.k)};
  });
  useEffect(() => {
    const svg = svgRef.current; if (!svg) return;
    const wheel = (e: WheelEvent) => { e.preventDefault(); const r = svg.getBoundingClientRect(); zoomBy(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - r.left, e.clientY - r.top); };
    svg.addEventListener('wheel', wheel, {passive: false});
    return () => svg.removeEventListener('wheel', wheel);
  }, []);

  const toWorld = (cx: number, cy: number) => { const r = svgRef.current!.getBoundingClientRect(); return {x: (cx - r.left - view.x) / view.k, y: (cy - r.top - view.y) / view.k}; };
  const onPointerDown = (e: React.PointerEvent, id?: string) => {
    e.stopPropagation(); (e.target as Element).setPointerCapture?.(e.pointerId);
    drag.current = {id, px: e.clientX, py: e.clientY, vx: view.x, vy: view.y, moved: false};
  };
  const onPointerMove = (e: React.PointerEvent) => {
    const d = drag.current; if (!d) return;
    if (Math.abs(e.clientX - d.px) + Math.abs(e.clientY - d.py) > 3) d.moved = true;
    if (d.id) { const p = pos.current.get(d.id)!; const w = toWorld(e.clientX, e.clientY); p.x = w.x; p.y = w.y; p.fixed = true; kick(0.12); }
    else setView(v => ({...v, x: d.vx + e.clientX - d.px, y: d.vy + e.clientY - d.py}));
  };
  const onPointerUp = () => {
    const d = drag.current; drag.current = null; if (!d) return;
    if (!d.moved) setSelected(d.id ?? null);
  };
  const query = q.trim().toLowerCase();
  const matches = useMemo(() => query.length < 2 ? [] : graph.nodes.filter(n => (n.label + ' ' + (n.props.title || '')).toLowerCase().includes(query)), [graph, query]);
  const focus = selected && graph.nodes.some(n => n.id === selected) ? neighbours(graph, selected) : null;
  const matchIds = new Set(matches.map(n => n.id));
  const sel = graph.nodes.find(n => n.id === selected);
  const byId = new Map(graph.nodes.map(n => [n.id, n]));
  const connections = sel ? graph.edges.filter(e => e.source === sel.id || e.target === sel.id).map(e => {
    const out = e.source === sel.id; return {rel: REL[e.type][out ? 0 : 1], other: byId.get(out ? e.target : e.source)!};
  }).filter(c => c.other).sort((a, b) => a.rel.localeCompare(b.rel)) : [];
  const nodeColor = (n: GraphNode) => n.type === 'Ticket' ? colors[String(n.props.status)] || TYPE_COLOR.Ticket : TYPE_COLOR[n.type];
  const toggle = (t: NodeType) => setTypes(s => { const n = new Set(s); n.has(t) ? n.delete(t) : n.add(t); return n; });
  const counts = useMemo(() => { const c = {} as Record<NodeType, number>; for (const n of full.nodes) c[n.type] = (c[n.type] || 0) + 1; return c; }, [full]);

  return <section className="panel graph-panel">
    <div className="graph-toolbar">
      <div className="graph-chips" role="group" aria-label={tx('Show in graph')}>
        {NODE_TYPES.map(t => <button key={t} type="button" className={'graph-chip' + (types.has(t) ? ' on' : '')} aria-pressed={types.has(t)} onClick={() => toggle(t)}>
          <i style={{background: TYPE_COLOR[t]}}/>{tx(TYPE_PLURAL[t])}{t !== 'Evidence' && <small>{counts[t] || 0}</small>}
        </button>)}
      </div>
      <div className="graph-tools">
        <select aria-label={tx('Tickets shown')} value={scope} onChange={e => setScope(e.target.value as any)}>
          <option value="open">{tx('Open tickets')}</option><option value="all">{tx('All tickets')}</option><option value="closed">{tx('Closed tickets')}</option>
        </select>
        <div className="search graph-search"><Search size={16}/><input aria-label={tx('Find in graph')} placeholder={tx('Find a ticket, person, road…')} value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && matches[0]) setSelected(matches[0].id); }}/></div>
      </div>
    </div>
    <div className="graph-body">
      <div className="graph-canvas">
        <svg ref={svgRef} role="img" aria-label={tx('Connections graph: {0} items and {1} links', [graph.nodes.length, graph.edges.length])}
          onPointerDown={e => onPointerDown(e)} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerLeave={() => setHover(null)}>
          <g transform={`translate(${view.x},${view.y}) scale(${view.k})`}>
            {graph.edges.map((e, i) => { const s = pos.current.get(e.source), t = pos.current.get(e.target); if (!s || !t) return null;
              const lit = focus ? focus.has(e.source) && focus.has(e.target) && (e.source === selected || e.target === selected) : false;
              return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} className={'graph-edge' + (lit ? ' lit' : '') + (focus && !lit ? ' dim' : '')}/>; })}
            {graph.nodes.map(n => { const p = pos.current.get(n.id); if (!p) return null; const r = radius(n);
              const dim = (focus && !focus.has(n.id)) || (matchIds.size > 0 && !matchIds.has(n.id) && !focus);
              const showLabel = n.type !== 'Ticket' && n.type !== 'Evidence' || n.id === hover || n.id === selected || matchIds.has(n.id) || (focus?.has(n.id) && view.k > 0.6);
              return <g key={n.id} className={'graph-node' + (dim ? ' dim' : '') + (n.id === selected ? ' sel' : '') + (matchIds.has(n.id) ? ' match' : '')} transform={`translate(${p.x},${p.y})`}
                onPointerDown={e => onPointerDown(e, n.id)} onPointerEnter={() => setHover(n.id)} onPointerLeave={() => setHover(h => h === n.id ? null : h)}>
                <circle r={r} fill={nodeColor(n)} stroke={n.type === 'Ticket' ? TYPE_COLOR.Ticket : '#fff'} strokeWidth={n.type === 'Ticket' ? 1.5 : 2}/>
                {showLabel && <text y={r + 11} textAnchor="middle">{shortLabel(n)}</text>}
                <title>{tx(TYPE_SINGULAR[n.type]) + ': ' + n.label + (n.props.status ? ' · ' + tx(String(n.props.status)) : '')}</title>
              </g>; })}
          </g>
        </svg>
        <div className="graph-zoom">
          <button type="button" className="icon-btn" aria-label={tx('Zoom in')} onClick={() => zoomBy(1.25)}><ZoomIn size={17}/></button>
          <button type="button" className="icon-btn" aria-label={tx('Zoom out')} onClick={() => zoomBy(0.8)}><ZoomOut size={17}/></button>
          <button type="button" className="icon-btn" aria-label={tx('Fit to screen')} title={tx('Fit to screen')} onClick={fit}><Maximize2 size={16}/></button>
        </div>
        <p className="graph-hint">{tx('Drag to move, scroll to zoom, click a dot to see its connections.')}</p>
      </div>
      <aside className="graph-side">
        {sel ? <>
          <div className="graph-side-head">
            <span className="graph-type"><i style={{background: nodeColor(sel)}}/>{tx(TYPE_SINGULAR[sel.type])}</span>
            <button type="button" className="icon-btn" aria-label={tx('Close')} onClick={() => setSelected(null)}><X size={16}/></button>
          </div>
          <h3>{sel.label}</h3>
          {sel.type === 'Ticket' && <>
            {sel.props.title && <p className="muted">{tx(String(sel.props.title))}</p>}
            <p className="graph-facts"><b style={{color: colors[String(sel.props.status)]}}>{tx(String(sel.props.status))}</b> · {tx(String(sel.props.severity))}</p>
            <button type="button" className="primary" onClick={() => onOpenTicket(sel.label)}>{tx('Open ticket')}<ArrowUpRight size={16}/></button>
          </>}
          {sel.type === 'Person' && <p className="graph-facts">{tx(String(sel.props.role))}{sel.props.active === false ? ' · ' + tx('Suspended') : ''}</p>}
          {sel.type === 'Contract' && <p className="graph-facts">{tx('{0} to {1}', [sel.props.start, sel.props.end])}</p>}
          <h4>{tx('Connections ({0})', [connections.length])}</h4>
          <ul className="graph-links">{connections.map((c, i) => <li key={i}><button type="button" onClick={() => setSelected(c.other.id)}>
            <i style={{background: nodeColor(c.other)}}/><span><small>{tx(c.rel)}</small>{c.other.label}{c.other.type === 'Ticket' && <small>{[c.other.props.road, tx(String(c.other.props.status))].filter(Boolean).join(' · ')}</small>}</span>
          </button></li>)}</ul>
        </> : <>
          <h3>{tx('How information flows')}</h3>
          <p className="muted">{tx('Each dot is a ticket, person, team, road, contract or contractor. Lines show who a ticket is assigned to, which road it is on, and which contract and contractor are responsible.')}</p>
          <ul className="graph-legend">{NODE_TYPES.filter(t => types.has(t)).map(t => <li key={t}><i style={{background: TYPE_COLOR[t]}}/>{tx(TYPE_PLURAL[t])}</li>)}</ul>
          <p className="footnote">{tx('Ticket dots take the colour of their current stage.')}</p>
          {matches.length > 0 && <><h4>{tx('Search results ({0})', [matches.length])}</h4><ul className="graph-links">{matches.slice(0, 12).map(n => <li key={n.id}><button type="button" onClick={() => setSelected(n.id)}><i style={{background: nodeColor(n)}}/><span><small>{tx(TYPE_SINGULAR[n.type])}</small>{n.label}</span></button></li>)}</ul></>}
        </>}
        <div className="graph-export">
          <button type="button" className="secondary" onClick={() => download('PaveLedger_graph.cypher', toCypher(graph), 'text/plain')}><Download size={15}/>{tx('Export for Neo4j')}</button>
          <button type="button" className="text-button" onClick={() => download('PaveLedger_graph.json', JSON.stringify(graph, null, 1), 'application/json')}>{tx('Export JSON')}</button>
        </div>
      </aside>
    </div>
  </section>;
}
