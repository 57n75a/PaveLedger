'use client';
// One-click monthly council report as a PDF: key figures, six-month trend, teams, contractors and oldest open work.
import {useState} from 'react';
import {FileText} from 'lucide-react';
import {toast} from 'sonner';
import {tx, useLang, locale} from '@/lib/i18n';
import {instance} from '@/lib/instance';
import {councilReport, shiftMonth, type CouncilReport} from '@/lib/council-report';
import type {Ticket} from '@/lib/domain';

const NAVY: [number, number, number] = [21, 42, 64], RED: [number, number, number] = [201, 32, 61], GREY: [number, number, number] = [107, 122, 144], LIGHT: [number, number, number] = [243, 246, 250];
const monthName = (m: string) => new Date(m + '-15T00:00:00Z').toLocaleDateString(locale(), {month: 'long', year: 'numeric', timeZone: 'UTC'});
const num = (n: number | null, digits = 0) => n === null ? '—' : n.toLocaleString(locale(), {maximumFractionDigits: digits});

async function imageData(url: string): Promise<{data: string; w: number; h: number} | null> {
  if (!url || url.endsWith('.svg')) return null;
  try {
    const blob = await (await fetch(url)).blob();
    const data = await new Promise<string>((ok, bad) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.onerror = bad; r.readAsDataURL(blob); });
    const size = await new Promise<{w: number; h: number}>(ok => { const i = new Image(); i.onload = () => ok({w: i.naturalWidth, h: i.naturalHeight}); i.onerror = () => ok({w: 3, h: 1}); i.src = data; });
    return {data, ...size};
  } catch { return null; }
}

export async function downloadCouncilReport(r: CouncilReport, opts: {workspace: string; logo?: string; currency?: string}) {
  const [{default: jsPDF}, {default: autoTable}, {pdfFonts}] = await Promise.all([import('jspdf'), import('jspdf-autotable'), import('@/lib/pdf-fonts')]);
  const doc = new jsPDF({unit: 'mm', format: 'a4'});
  try { await pdfFonts(doc); } catch { toast.error(tx('Could not load the PDF font. Letters such as č, ć and đ may not display.')); }
  const font = doc.getFont().fontName;
  const W = 210, M = 14;
  const generated = new Date().toLocaleDateString(locale(), {dateStyle: 'long'});

  // Header band
  doc.setFillColor(...NAVY); doc.rect(0, 0, W, 38, 'F');
  const logo = await imageData(opts.logo || instance.logo);
  if (logo) { doc.setFillColor(255, 255, 255); doc.roundedRect(M, 8, 52, 22, 2, 2, 'F'); const h = Math.min(18, 48 * logo.h / logo.w); doc.addImage(logo.data, 'PNG', M + 2, 8 + (22 - h) / 2, h * logo.w / logo.h, h); }
  const tx0 = logo ? M + 58 : M;
  doc.setTextColor(255, 255, 255); doc.setFont(font, 'bold'); doc.setFontSize(17);
  doc.text(tx('Monthly road maintenance report'), tx0, 17);
  doc.setFont(font, 'normal'); doc.setFontSize(11);
  doc.text(monthName(r.month) + ' · ' + opts.workspace, tx0, 25);
  doc.setFontSize(8.5); doc.setTextColor(185, 199, 216);
  doc.text(tx('Prepared {0} from the PaveLedger workspace record', [generated]), tx0, 31);

  // Key figures
  const delta = (a: number, b: number) => a === b ? tx('same as last month') : (a > b ? '+' : '') + num(a - b) + ' ' + tx('vs last month');
  const tiles: [string, string, string, boolean?][] = [
    [tx('Reported'), num(r.opened), delta(r.opened, r.previous.opened)],
    [tx('Repaired and verified'), num(r.closed), delta(r.closed, r.previous.closed)],
    [tx('Open at month end'), num(r.openAtEnd), tx('{0} past due', [num(r.overdueAtEnd)]), r.overdueAtEnd > 0],
    [tx('Average days to close'), num(r.avgDaysToClose, 1), tx('report to verified repair')],
    [tx('Urgent still open'), num(r.urgentOpenAtEnd), tx('at month end'), r.urgentOpenAtEnd > 0],
    [tx('Resident reports'), num(r.residentReports), tx('received this month')],
    [tx('Warranty repairs'), num(r.warrantyRepairs), tx('paid by the contractor')],
    [tx('Not a defect'), num(r.rejected), tx('reviewed and closed')],
  ];
  const tw = (W - 2 * M - 3 * 4) / 4;
  tiles.forEach(([label, value, sub, warn], i) => {
    const x = M + (i % 4) * (tw + 4), y = 46 + Math.floor(i / 4) * 30;
    doc.setFillColor(...LIGHT); doc.roundedRect(x, y, tw, 26, 2, 2, 'F');
    doc.setFontSize(8); doc.setTextColor(...GREY); doc.setFont(font, 'normal'); doc.text(doc.splitTextToSize(label, tw - 6)[0], x + 3, y + 6);
    doc.setFontSize(18); doc.setFont(font, 'bold'); doc.setTextColor(...(warn ? RED : NAVY)); doc.text(value, x + 3, y + 16);
    doc.setFontSize(7.5); doc.setFont(font, 'normal'); doc.setTextColor(...GREY); doc.text(doc.splitTextToSize(sub, tw - 6)[0], x + 3, y + 22);
  });

  // Six-month trend chart
  let y = 112;
  doc.setTextColor(...NAVY); doc.setFont(font, 'bold'); doc.setFontSize(12); doc.text(tx('Six-month trend'), M, y);
  doc.setFont(font, 'normal'); doc.setFontSize(8); doc.setTextColor(...GREY);
  doc.setFillColor(...NAVY); doc.rect(W - M - 62, y - 3, 3, 3, 'F'); doc.text(tx('Reported'), W - M - 57, y - 0.5);
  doc.setFillColor(31, 138, 87); doc.rect(W - M - 30, y - 3, 3, 3, 'F'); doc.text(tx('Repaired'), W - M - 25, y - 0.5);
  const chartTop = y + 6, chartH = 42, chartW = W - 2 * M;
  const max = Math.max(1, ...r.trend.flatMap(t => [t.opened, t.closed]));
  doc.setDrawColor(225, 230, 237); doc.line(M, chartTop + chartH, M + chartW, chartTop + chartH);
  const slot = chartW / r.trend.length, bw = Math.min(10, slot / 3.2);
  r.trend.forEach((t, i) => {
    const cx = M + slot * i + slot / 2;
    ([[t.opened, NAVY, -bw - 0.6], [t.closed, [31, 138, 87] as [number, number, number], 0.6]] as [number, [number, number, number], number][]).forEach(([v, c, off]) => {
      const h = v / max * (chartH - 8);
      doc.setFillColor(...c); doc.rect(cx + off, chartTop + chartH - h, bw, h, 'F');
      doc.setFontSize(7.5); doc.setTextColor(...NAVY); doc.text(String(v), cx + off + bw / 2, chartTop + chartH - h - 1.5, {align: 'center'});
    });
    doc.setFontSize(7.5); doc.setTextColor(...(t.month === r.month ? RED : GREY));
    doc.text(new Date(t.month + '-15T00:00:00Z').toLocaleDateString(locale(), {month: 'short', year: '2-digit', timeZone: 'UTC'}), cx, chartTop + chartH + 5, {align: 'center'});
  });
  y = chartTop + chartH + 14;

  const table = (title: string, head: string[], body: (string | number)[][], startY: number) => {
    doc.setTextColor(...NAVY); doc.setFont(font, 'bold'); doc.setFontSize(12); doc.text(title, M, startY);
    autoTable(doc, {startY: startY + 3, head: [head], body: body.map(row => row.map(String)), margin: {left: M, right: M},
      styles: {font, fontSize: 8.5, cellPadding: 2.2, textColor: [40, 52, 70]}, headStyles: {fillColor: NAVY, textColor: 255, fontStyle: 'bold'},
      alternateRowStyles: {fillColor: [248, 250, 252]}});
    return (doc as any).lastAutoTable.finalY + 10;
  };
  y = table(tx('By priority'), [tx('Priority'), tx('Reported'), tx('Repaired and verified')], r.bySeverity.map(s => [tx(s.severity), s.opened, s.closed]), y);
  y = table(tx('By team'), [tx('Team'), tx('Reported'), tx('Repaired and verified'), tx('Open at month end')], r.byTeam.map(s => [tx(s.team), s.opened, s.closed, s.openAtEnd]), y);

  // Page 2: contractors, oldest open work, costs
  doc.addPage(); y = 20;
  if (r.contractors.length) y = table(tx('Contractor performance'), [tx('Contractor'), tx('Grade'), tx('On time'), tx('Fixed first time'), tx('Average repair'), tx('Overdue now')],
    r.contractors.map(c => [tx(c.contractor), c.grade || '—', c.onTimeRate === null ? '—' : Math.round(c.onTimeRate * 100) + '%', c.reopenRate === null ? '—' : Math.round((1 - c.reopenRate) * 100) + '%', c.avgRepairDays === null ? '—' : tx('{0} days', [num(c.avgRepairDays, 1)]), c.overdueOpen]), y);
  if (r.oldestOpen.length) y = table(tx('Oldest open tickets'), [tx('Ticket'), tx('Road'), tx('Team'), tx('Priority'), tx('Status'), tx('Days open')],
    r.oldestOpen.map(o => [o.id, tx(o.road), tx(o.team), tx(o.severity), tx(o.status), o.days]), y);
  if (r.costs) {
    const money = (n: number) => n.toLocaleString(locale(), {style: 'currency', currency: opts.currency || instance.currency, maximumFractionDigits: 0});
    y = table(tx('Repair costs (tickets closed this month)'), [tx('Estimated'), tx('Actual'), tx('Recovered under warranty')], [[money(r.costs.estimated), money(r.costs.actual), money(r.costs.recovered)]], y);
  }
  doc.setFontSize(8); doc.setTextColor(...GREY); doc.setFont(font, 'normal');
  doc.text(doc.splitTextToSize(tx('Definitions: "Reported" counts tickets created in the month. "Repaired and verified" counts tickets closed after a verified repair. Duplicates are excluded. Contractor repair times are measured from the contractor notice.'), W - 2 * M), M, Math.min(y, 270));

  const pages = doc.getNumberOfPages();
  for (let p = 1; p <= pages; p++) {
    doc.setPage(p); doc.setFontSize(7.5); doc.setTextColor(...GREY);
    doc.text(instance.brand + ' · ' + monthName(r.month), M, 290);
    doc.text(tx('Page {0} of {1}', [String(p), String(pages)]), W - M, 290, {align: 'right'});
  }
  doc.save(`PaveLedger_Council_Report_${r.month}.pdf`);
}

export default function CouncilReportPanel({tickets, workspace, logo}: {tickets: Ticket[]; workspace: string; logo?: string}) {
  useLang();
  const thisMonth = new Date().toISOString().slice(0, 7);
  const months = Array.from({length: 12}, (_, i) => shiftMonth(thisMonth, -i));
  const [month, setMonth] = useState(new Date().getUTCDate() <= 7 ? shiftMonth(thisMonth, -1) : thisMonth);
  const [busy, setBusy] = useState(false);
  const r = councilReport(tickets, month, new Date().toISOString());
  return <section className="panel council">
    <div className="council-icon"><FileText size={22}/></div>
    <div className="council-text">
      <h2>{tx('Monthly council report')}</h2>
      <p>{tx('A two-page PDF for council sessions and budget meetings: key figures, six-month trend, teams, contractors and the oldest open work.')}</p>
      <p className="council-preview">{tx('{0}: {1} reported, {2} repaired, {3} open at month end.', [monthName(month), String(r.opened), String(r.closed), String(r.openAtEnd)])}</p>
    </div>
    <div className="council-actions">
      <select value={month} onChange={e => setMonth(e.target.value)} aria-label={tx('Report month')}>
        {months.map(m => <option key={m} value={m}>{monthName(m)}{m === thisMonth ? ' · ' + tx('so far') : ''}</option>)}
      </select>
      <button className="primary" disabled={busy} onClick={async () => { setBusy(true); try { await downloadCouncilReport(r, {workspace, logo}); } catch { toast.error(tx('The report could not be created. Please try again.')); } finally { setBusy(false); } }}>
        {tx(busy ? 'Preparing…' : 'Download PDF')}
      </button>
    </div>
  </section>;
}
