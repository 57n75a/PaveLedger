'use client';
import {tx, useLang} from '@/lib/i18n';
import {useMemo, useState} from 'react';
import * as XLSX from 'xlsx';
import {toast} from 'sonner';
import {CheckCircle2, AlertTriangle, Copy as CopyIcon, Download, FileSpreadsheet} from 'lucide-react';
import {CONTRACT_SCHEMA, MAX_IMPORT_ROWS, autoMapColumns, checkRow, contractKey, type ContractRow} from '@/lib/contract-schema';

type Existing = {contractor: string; road: string; start: string; end: string};
const EXAMPLES: Record<string, string>[] = [
  Object.fromEntries(CONTRACT_SCHEMA.map(f => [f.key, f.example])),
  {contractor: 'Niskogradnja Zlatibor a.d.', road: 'Užička', start: '15.04.2026', end: '14.04.2029', poc: 'Jelena Jovanović', email: 'jelena@niskogradnja-zlatibor.rs', phone: '', scope: '', additionalRoads: '', address: '', addressCountry: '', notes: '', scopeLat: '', scopeLng: '', scopeRadius: ''},
];

function save(name: string, content: string, type: string) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([content], {type})); a.download = name; a.click(); URL.revokeObjectURL(a.href);
}
const csvCell = (v: string) => /[",;\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
const xmlEsc = (v: string) => v.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Header row and two example rows; the header uses the schema keys so columns map automatically. */
export function downloadTemplate(kind: 'csv' | 'xlsx' | 'xml') {
  const keys = CONTRACT_SCHEMA.map(f => f.key);
  if (kind === 'csv') {
    // BOM so Excel opens č, ć, š, ž and đ correctly.
    save('PaveLedger_contracts_template.csv', '﻿' + [keys.join(','), ...EXAMPLES.map(r => keys.map(k => csvCell(r[k] || '')).join(','))].join('\r\n') + '\r\n', 'text/csv;charset=utf-8');
    return;
  }
  if (kind === 'xml') {
    const body = EXAMPLES.map(r => '  <contract>\n' + keys.filter(k => r[k]).map(k => `    <${k}>${xmlEsc(r[k])}</${k}>`).join('\n') + '\n  </contract>').join('\n');
    save('PaveLedger_contracts_template.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<contracts>\n${body}\n</contracts>\n`, 'application/xml');
    return;
  }
  const wb = XLSX.utils.book_new();
  const data = XLSX.utils.aoa_to_sheet([keys, ...EXAMPLES.map(r => keys.map(k => r[k] || ''))]);
  data['!cols'] = keys.map(k => ({wch: Math.max(14, k.length + 2)}));
  XLSX.utils.book_append_sheet(wb, data, tx('Contracts').slice(0, 31));
  const guide = XLSX.utils.aoa_to_sheet([
    [tx('Column'), tx('Field'), tx('Required'), tx('Format'), tx('Example'), tx('Description')],
    ...CONTRACT_SCHEMA.map(f => [f.key, tx(f.label), f.required ? tx('Yes') : tx('No'), tx(f.format), f.example, tx(f.help)]),
    [],
    [tx('Rules')],
    ...IMPORT_RULES.map(r => [tx(r)]),
  ]);
  guide['!cols'] = [{wch: 16}, {wch: 24}, {wch: 10}, {wch: 36}, {wch: 34}, {wch: 70}];
  XLSX.utils.book_append_sheet(wb, guide, tx('Guidelines').slice(0, 31));
  XLSX.writeFile(wb, 'PaveLedger_contracts_template.xlsx');
}

export const IMPORT_RULES = [
  'One row per contract. Keep the header row; extra columns are ignored.',
  'Required: contractor, road, start, end, poc and email. Everything else is optional.',
  'Dates as YYYY-MM-DD (2026-03-01) or DD.MM.YYYY (01.03.2026). Slashes are not accepted because 03/01 is ambiguous.',
  'Spell the road exactly as it appears in tickets, so the contract can be matched to them.',
  'List extra streets in additionalRoads, separated by semicolons.',
  'For a map area, fill scopeLat, scopeLng and scopeRadius together.',
  'A row with the same firm, road and warranty dates as an existing contract is skipped as a duplicate.',
  'Up to 200 rows per import. Save CSV files as UTF-8 so letters such as č and đ survive.',
];

// XML: records are the elements that hold a contractor field; falls back to the most repeated element.
function xmlRecords(text: string): Record<string, string>[] | null {
  const doc = new DOMParser().parseFromString(text, 'application/xml');
  if (doc.querySelector('parsererror')) return null;
  const all = Array.from(doc.getElementsByTagName('*'));
  const contractorNames = ['contractor', ...CONTRACT_SCHEMA[0].aliases].map(s => s.toLowerCase());
  const marker = all.find(el => contractorNames.includes(el.tagName.toLowerCase()) && el.parentElement);
  let tag = marker?.parentElement?.tagName || '';
  if (!tag) { const counts = new Map<string, number>(); all.forEach(el => counts.set(el.tagName, (counts.get(el.tagName) || 0) + 1)); let max = 1; counts.forEach((c, t) => { if (c > max) { max = c; tag = t; } }); }
  if (!tag) return [];
  return Array.from(doc.getElementsByTagName(tag)).map(rec => { const o: Record<string, string> = {}; Array.from(rec.children).forEach(ch => { o[ch.tagName] = ch.textContent || ''; }); return o; });
}

export default function ContractImport({mutate, busy, onDone, existing = []}: {mutate: (b: any) => Promise<boolean>; busy: boolean; onDone: () => void; existing?: Existing[]}) {
  useLang();
  const [rows, setRows] = useState<Record<string, any>[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [deselected, setDeselected] = useState<Set<number>>(new Set());
  const [fileKind, setFileKind] = useState<'table' | 'xml' | 'pdf' | null>(null);
  const [fileName, setFileName] = useState('');

  async function handleFile(file: File) {
    const name = file.name.toLowerCase();
    setFileName(file.name); setDeselected(new Set());
    if (name.endsWith('.pdf')) { setFileKind('pdf'); setRows([]); setColumns([]); return; }
    let json: Record<string, any>[] | null;
    if (name.endsWith('.xml')) {
      json = xmlRecords(await file.text());
      if (json === null) { toast.error(tx('Could not parse this XML file')); return; }
      if (!json.length) { toast.error(tx('Could not find repeated records in this XML file')); return; }
      setFileKind('xml');
    } else {
      // CSV is read as plain text so the library does not guess dates (01.05.2026 must stay 1 May). Excel date cells keep their real dates.
      const wb = name.endsWith('.csv')
        ? XLSX.read(new TextDecoder('utf-8').decode(await file.arrayBuffer()).replace(/^\ufeff/, ''), {type: 'string', raw: true})
        : XLSX.read(await file.arrayBuffer(), {type: 'array', cellDates: true});
      const sheet = wb.Sheets[wb.SheetNames[0]];
      json = XLSX.utils.sheet_to_json(sheet, {defval: '', raw: true});
      setFileKind('table');
    }
    json = json.filter(r => Object.values(r).some(v => String(v ?? '').trim() !== ''));
    if (!json.length) { toast.error(tx('No rows found in this file')); return; }
    if (json.length > MAX_IMPORT_ROWS) toast.warning(tx('This file has {0} rows. Only the first {1} can be imported at a time.', [json.length, MAX_IMPORT_ROWS]));
    const cols = Array.from(new Set(json.flatMap(r => Object.keys(r))));
    setColumns(cols); setRows(json.slice(0, MAX_IMPORT_ROWS)); setMapping(autoMapColumns(cols));
  }

  // Check every row against the schema and against existing contracts.
  const checked = useMemo(() => {
    const seen = new Set(existing.map(contractKey));
    return rows.map(r => {
      const raw: Record<string, unknown> = {};
      for (const f of CONTRACT_SCHEMA) raw[f.key] = mapping[f.key] ? r[mapping[f.key]] : '';
      const res = checkRow(raw);
      let duplicate = false;
      if (res.value) { const k = contractKey(res.value); duplicate = seen.has(k); seen.add(k); }
      return {...res, duplicate, raw};
    });
  }, [rows, mapping, existing]);
  const ready = checked.map((c, i) => ({c, i})).filter(({c, i}) => c.value && !c.duplicate && !deselected.has(i));
  const invalid = checked.filter(c => !c.value).length, dupes = checked.filter(c => c.duplicate).length;
  const missingRequired = CONTRACT_SCHEMA.filter(f => f.required && !mapping[f.key]);

  async function doImport() {
    const items = ready.map(({c}) => c.value as ContractRow);
    if (!items.length) return;
    if (await mutate({action: 'bulkImportContracts', items})) onDone();
  }

  return <div className="form import">
    <details className="import-guide">
      <summary><FileSpreadsheet size={16}/>{tx('Import schema and guidelines')}</summary>
      <p className="muted">{tx('Download a template, fill one row per contract, and upload it here. Columns are matched automatically when the header uses the names below.')}</p>
      <div className="button-row">
        <button type="button" className="secondary" onClick={() => downloadTemplate('xlsx')}><Download size={15}/>{tx('Excel template')}</button>
        <button type="button" className="secondary" onClick={() => downloadTemplate('csv')}><Download size={15}/>{tx('CSV template')}</button>
        <button type="button" className="secondary" onClick={() => downloadTemplate('xml')}><Download size={15}/>{tx('XML template')}</button>
      </div>
      <p className="footnote">{tx('For automated exports from other systems:')} <a className="text-button" href="/schemas/contract-import.schema.json" target="_blank" rel="noopener">{tx('JSON Schema')}</a></p>
      <div className="import-schema"><table>
        <thead><tr><th>{tx('Column')}</th><th>{tx('Field')}</th><th>{tx('Format')}</th><th>{tx('Example')}</th></tr></thead>
        <tbody>{CONTRACT_SCHEMA.map(f => <tr key={f.key}>
          <td><code>{f.key}</code>{f.required && <b className="req" title={tx('Required')}>*</b>}</td>
          <td>{tx(f.label)}<small>{tx(f.help)}</small></td>
          <td>{tx(f.format)}</td>
          <td><span className="ex">{f.example}</span></td>
        </tr>)}</tbody>
      </table></div>
      <h4>{tx('Rules')}</h4>
      <ul className="import-rules">{IMPORT_RULES.map(r => <li key={r}>{tx(r)}</li>)}</ul>
    </details>

    <label>{tx('Source file (XLSX, XLS, CSV, or XML)')}<input type="file" accept=".xlsx,.xls,.csv,.xml,.pdf" onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }}/></label>
    {fileKind === 'pdf' && <p className="footnote">{tx("PDF structured import isn't supported — PDF layouts vary too much to map reliably. Convert the file to XLSX or CSV first, or enter these contracts manually.")}</p>}

    {rows.length > 0 && <>
      <h3>{tx('Map columns')}</h3>
      <p className="muted">{tx('{0}: {1} rows found. Check that each field points to the right column.', [fileName, rows.length])}</p>
      <div className="import-map">{CONTRACT_SCHEMA.map(f => <label key={f.key}>
        <span>{tx(f.label)}{f.required && <b className="req">*</b>}</span>
        <select value={mapping[f.key] || ''} onChange={e => setMapping({...mapping, [f.key]: e.target.value})}>
          <option value="">{tx('-- not mapped --')}</option>{columns.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </label>)}</div>
      {missingRequired.length > 0 && <p className="import-warn"><AlertTriangle size={15}/>{tx('Required fields not mapped: {0}', [missingRequired.map(f => tx(f.label)).join(', ')])}</p>}

      <h3>{tx('Check rows')}</h3>
      <p className="import-summary">
        <span className="ok"><CheckCircle2 size={14}/>{tx('Ready: {0}', [ready.length])}</span>
        {invalid > 0 && <span className="bad"><AlertTriangle size={14}/>{tx('With errors: {0}', [invalid])}</span>}
        {dupes > 0 && <span className="dup"><CopyIcon size={14}/>{tx('Duplicates: {0}', [dupes])}</span>}
      </p>
      <div className="import-rows">
        {checked.map((c, i) => {
          const label = [c.raw.contractor, c.raw.road].map(v => String(v ?? '').trim()).filter(Boolean).join(' — ') || tx('(empty row)');
          return <label key={i} className={'import-row' + (c.value ? c.duplicate ? ' dup' : '' : ' bad')}>
            <input type="checkbox" disabled={!c.value || c.duplicate} checked={!!c.value && !c.duplicate && !deselected.has(i)} onChange={e => { const s = new Set(deselected); e.target.checked ? s.delete(i) : s.add(i); setDeselected(s); }}/>
            <span><b>{tx('Row {0}', [typeof rows[i].__rowNum__ === 'number' ? rows[i].__rowNum__ + 1 : i + 1])}</b> {label}
              {c.value && !c.duplicate && <small>{tx('{0} to {1}', [c.value.start, c.value.end])} · {c.value.email}</small>}
              {c.duplicate && <small>{tx('Already registered with the same firm, road and dates. It will be skipped.')}</small>}
              {c.errors.map(e => <small key={e} className="err">{tx(e)}</small>)}
            </span>
          </label>;
        })}
      </div>
      <button className="primary" disabled={busy || !ready.length || missingRequired.length > 0} onClick={doImport}>{tx('Import {0} contract{1}', [ready.length, ready.length === 1 ? '' : 's'])}</button>
      {(invalid > 0 || dupes > 0) && <p className="footnote">{tx('Rows with errors and duplicates are not imported. Fix them in the file and upload it again, or import the ready rows now.')}</p>}
    </>}
  </div>;
}
