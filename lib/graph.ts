// Connections graph: tickets, people, teams, roads, contracts and contractors as nodes and relationships.
// Built from the role-filtered workspace the viewer already has, so it never shows more than they may see.
// The shape mirrors a property graph (labels, relationship types, properties) so it can be synced to Neo4j later;
// toCypher() produces the equivalent MERGE statements.
import type {State, Member} from './domain.ts';

export type NodeType = 'Ticket' | 'Team' | 'Person' | 'Road' | 'Contract' | 'Contractor' | 'Evidence';
export type RelType = 'IN_TEAM' | 'ASSIGNED_TO' | 'REPORTED_BY' | 'ON_ROAD' | 'COVERED_BY' | 'HANDLED_BY' | 'HELD_BY' | 'APPLIES_TO' | 'MEMBER_OF' | 'WORKS_FOR' | 'DUPLICATE_OF' | 'HAS_EVIDENCE';
export type GraphNode = {id: string; type: NodeType; label: string; props: Record<string, string | number | boolean>};
export type GraphEdge = {source: string; target: string; type: RelType};
export type Graph = {nodes: GraphNode[]; edges: GraphEdge[]};

export const NODE_TYPES: NodeType[] = ['Ticket', 'Team', 'Person', 'Road', 'Contract', 'Contractor', 'Evidence'];

const key = (type: NodeType, raw: string) => type + ':' + raw.trim().toLowerCase();

export function buildGraph(s: Pick<State, 'tickets' | 'members' | 'teams' | 'contracts'>, opts: {evidence?: boolean} = {}): Graph {
  const nodes = new Map<string, GraphNode>();
  const edges: GraphEdge[] = [];
  const seen = new Set<string>();
  const node = (type: NodeType, raw: string, label: string, props: GraphNode['props'] = {}) => {
    const id = key(type, raw);
    const n = nodes.get(id);
    if (n) Object.assign(n.props, props); else nodes.set(id, {id, type, label, props});
    return id;
  };
  const edge = (source: string, target: string, type: RelType) => {
    const k = source + '|' + type + '|' + target;
    if (source === target || seen.has(k)) return;
    seen.add(k); edges.push({source, target, type});
  };
  const people = new Map<string, Member>(s.members.map(m => [m.id, m]));
  const person = (id: string) => {
    const m = people.get(id);
    return m ? node('Person', m.id, m.name, {role: m.customRole || m.role, active: m.active !== false}) : null;
  };

  for (const team of s.teams) node('Team', team, team);
  for (const m of s.members) {
    const p = person(m.id)!;
    for (const team of m.teams || []) edge(p, node('Team', team, team), 'MEMBER_OF');
    if (m.contractor) edge(p, node('Contractor', m.contractor, m.contractor), 'WORKS_FOR');
  }
  for (const c of s.contracts) {
    const id = node('Contract', c.id, c.id, {start: c.start, end: c.end, scope: c.scope || ''});
    edge(id, node('Contractor', c.contractor, c.contractor), 'HELD_BY');
    for (const road of [c.road, ...(c.additionalRoads || [])].filter(Boolean)) edge(id, node('Road', road, road), 'APPLIES_TO');
  }
  for (const t of s.tickets) {
    const id = node('Ticket', t.id, t.id, {title: t.title, road: t.road, status: t.status, severity: t.severity, created: t.created, archived: !!t.archived});
    edge(id, node('Road', t.road, t.road), 'ON_ROAD');
    if (t.team) edge(id, node('Team', t.team, t.team), 'IN_TEAM');
    const a = t.analyst && person(t.analyst); if (a) edge(id, a, 'ASSIGNED_TO');
    const r = t.reportedBy && person(t.reportedBy); if (r) edge(id, r, 'REPORTED_BY');
    if (t.contractId && s.contracts.some(c => c.id === t.contractId)) edge(id, key('Contract', t.contractId), 'COVERED_BY');
    if (t.contractor) edge(id, node('Contractor', t.contractor, t.contractor), 'HANDLED_BY');
    if (t.duplicateOf) edge(id, node('Ticket', t.duplicateOf, t.duplicateOf), 'DUPLICATE_OF');
    if (opts.evidence) for (const e of t.evidence || []) edge(id, node('Evidence', t.id + '/' + e.id, e.name, {purpose: e.purpose, capturedAt: e.capturedAt}), 'HAS_EVIDENCE');
  }
  return {nodes: [...nodes.values()], edges};
}

/** Nodes directly connected to a node. */
export function neighbours(g: Graph, id: string): Set<string> {
  const out = new Set<string>([id]);
  for (const e of g.edges) { if (e.source === id) out.add(e.target); if (e.target === id) out.add(e.source); }
  return out;
}

const cy = (v: unknown) => typeof v === 'number' || typeof v === 'boolean' ? String(v) : "'" + String(v).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
const props = (o: Record<string, unknown>) => '{' + Object.entries(o).map(([k, v]) => k + ': ' + cy(v)).join(', ') + '}';

/** Cypher MERGE statements for loading this graph into Neo4j. */
export function toCypher(g: Graph): string {
  const lines = ['// PaveLedger connections graph. Run in Neo4j Browser or cypher-shell.', 'CREATE CONSTRAINT pl_node IF NOT EXISTS FOR (n:PaveLedger) REQUIRE n.key IS UNIQUE;'];
  for (const n of g.nodes) lines.push(`MERGE (n:PaveLedger:${n.type} {key: ${cy(n.id)}}) SET n += ${props({name: n.label, ...n.props})};`);
  for (const e of g.edges) lines.push(`MATCH (a:PaveLedger {key: ${cy(e.source)}}), (b:PaveLedger {key: ${cy(e.target)}}) MERGE (a)-[:${e.type}]->(b);`);
  return lines.join('\n') + '\n';
}
