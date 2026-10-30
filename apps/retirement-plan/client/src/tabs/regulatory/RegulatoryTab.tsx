/**
 * tabs/regulatory/RegulatoryTab.tsx — Regulatory tab of the unified Copper Retirement Accelerator (ACC-APP-PORT-REG).
 * Ported 2026-10-24 from the retired standalone regulatory-assistant app. Real sources only:
 *   Matrix  -> /api/regulatory/matrix  (jurisdiction_requirements_cited, official_url on every row)
 *   Ask     -> /api/regulatory/ask     (real chunks only, every answer lists Sources chips; uncited = suppressed)
 *   Sources -> /api/regulatory/sources (regulatory_source_register)
 * Citation display per BRAND_GUIDE §0.2 (CitationLink). Colors from styles/tokens.css only.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { Search, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { TabHeader, TabBar, KpiCard, EmptyState, CitationLink, isVerifiedStatus, panelId, tabId } from '../../components/shared';

interface MatrixRow {
  requirement_key: string; jurisdiction_code: string; jurisdiction_name: string; jurisdiction_level: string;
  requirement_type: string; requirement_summary: string; value_numeric: string | null; value_unit: string | null;
  verification_status: string; source_id: string; citation: string; official_url: string | null; notes: string | null;
  source_title: string | null; last_verified: string | null;
  citation_url?: string | null; citation_verified_on?: string | null; // ACC-APP-JUR-CITATION-URL
}
interface SourceRow {
  source_id: string; jurisdiction: string; level: string; authority: string; topic: string; title: string;
  citation: string; official_url: string; verification_status: string; last_verified: string | null; effective_date: string | null;
}
interface AskSource { n: number; title: string; citation: string; url: string; jurisdiction: string; verification_status?: string; last_verified?: string; excerpt: string }
interface AskResult { answer: string | null; grounded: boolean; insufficient?: boolean; cited?: number[]; sources: AskSource[]; mode: string; llm_error?: string; jurisdiction_applied?: string; jurisdiction_source?: 'selector' | 'detected_in_question' | 'none' }
interface Kpis { requirements: number; verified: number; gaps: number; jurisdictions: number; sources: number; verified_sources: number; real_chunks: number }

const JURISDICTIONS = [
  { id: 'ALL', label: 'All (federal + 6 states)' }, { id: 'US', label: 'Federal only' },
  { id: 'WA', label: 'Washington' }, { id: 'AZ', label: 'Arizona' }, { id: 'CO', label: 'Colorado' },
  { id: 'MN', label: 'Minnesota' }, { id: 'OR', label: 'Oregon' }, { id: 'ID', label: 'Idaho' },
];
const SUBS = [{ id: 'matrix', label: 'Jurisdiction matrix' }, { id: 'ask', label: 'Ask the sources' }, { id: 'sources', label: 'Source register' }] as const;
type Sub = (typeof SUBS)[number]['id'];
const SUGGESTED = [
  'How much advance public notice is required before a copper retirement?',
  'When is Section 214 discontinuance authority required?',
  'How many days before digging must an excavator call 811?',
  'What are the worker safety rules for handling lead-sheathed cable?',
];

const humanize = (s: string) => s.replace(/^811_/, '811 ').replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body.data as T;
}

/** A row is verified only if its status is verified_* AND it carries an official URL (charter citation rule). */
const rowVerified = (r: { verification_status: string; official_url: string | null }) => isVerifiedStatus(r.verification_status) && !!r.official_url;

function StatusCell({ status, hasUrl = true }: { status: string; hasUrl?: boolean }) {
  if (!hasUrl) {
    return <span className="inline-flex items-center gap-1 text-xs text-warning"><AlertTriangle size={14} strokeWidth={1.5} aria-hidden="true" />Flagged gap (no official source)</span>;
  }
  return isVerifiedStatus(status) ? (
    <span className="inline-flex items-center gap-1 text-xs text-success"><CheckCircle2 size={14} strokeWidth={1.5} aria-hidden="true" />Verified</span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs text-warning"><AlertTriangle size={14} strokeWidth={1.5} aria-hidden="true" />Flagged gap ({status.replace(/_/g, ' ').toLowerCase()})</span>
  );
}

function MatrixView({ jur }: { jur: string }) {
  const [rows, setRows] = useState<MatrixRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [gapsOnly, setGapsOnly] = useState(false);
  useEffect(() => {
    setRows(null); setErr(null);
    getJson<MatrixRow[]>(`/api/regulatory/matrix?jurisdiction=${encodeURIComponent(jur)}`).then(setRows).catch((e) => setErr(e.message));
  }, [jur]);
  if (err) return <EmptyState title="Could not load the jurisdiction matrix"><p>{err}</p></EmptyState>;
  if (!rows) return <p className="text-sm text-muted-foreground">Loading cited requirements…</p>;
  // ACC-DES-DEF-REG-MATRIX-HIDDEN-GAPS: render EVERY row; rows without an official URL show as flagged gaps, never hidden.
  const gapCount = rows.filter((r) => !rowVerified(r)).length;
  const shown = gapsOnly ? rows.filter((r) => !rowVerified(r)) : rows;
  if (!rows.length) return <EmptyState title="No requirements recorded for this jurisdiction" />;
  return (
    <div>
    <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-xs text-muted-foreground">
      <span role="status">{rows.length} requirements · {rows.length - gapCount} verified · {gapCount} flagged gaps</span>
      <label className="inline-flex items-center gap-2">
        <input type="checkbox" checked={gapsOnly} onChange={(e) => setGapsOnly(e.target.checked)} className="accent-primary" />
        Show gaps only
      </label>
    </div>
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <table className="w-full text-sm">
        <caption className="sr-only">Copper retirement requirements by jurisdiction, each with its official source</caption>
        <thead className="bg-muted text-left text-xs text-muted-foreground">
          <tr><th scope="col" className="p-2">Jurisdiction</th><th scope="col" className="p-2">Requirement</th><th scope="col" className="p-2">What the source says</th><th scope="col" className="p-2">Value</th><th scope="col" className="p-2">Status</th><th scope="col" className="p-2">Official source</th></tr>
        </thead>
        <tbody>
          {shown.map((r) => {
            const verified = rowVerified(r);
            return (
              <tr key={r.requirement_key} className="border-t border-border align-top">
                <td className="p-2 whitespace-nowrap font-medium text-secondary">{r.jurisdiction_code === 'US' ? 'Federal' : r.jurisdiction_name}</td>
                <td className="p-2 whitespace-nowrap">{humanize(r.requirement_type)}</td>
                <td className="p-2 max-w-md">
                  {!verified && <span className="font-medium text-warning">Not a verified fact: </span>}
                  {r.requirement_summary}
                  {r.notes && <p className="text-xs text-muted-foreground mt-1">{r.notes}</p>}
                </td>
                <td className="p-2 whitespace-nowrap">{verified && r.value_numeric ? `${Number(r.value_numeric)} ${(r.value_unit || '').replace(/_/g, ' ')}` : '—'}</td>
                <td className="p-2 whitespace-nowrap"><StatusCell status={r.verification_status} hasUrl={!!r.official_url} /></td>
                <td className="p-2 min-w-[14rem]"><CitationLink title={r.source_title || r.citation || r.source_id} url={r.official_url} citationUrl={r.citation_url} verificationStatus={r.verification_status} citation={r.citation} lastVerified={r.citation_verified_on || r.last_verified} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    </div>
  );
}

function AskView({ jur }: { jur: string }) {
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<AskResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const submit = async (e?: FormEvent, text?: string) => {
    e?.preventDefault();
    const question = (text ?? q).trim();
    if (question.length < 3) return;
    setQ(question); setBusy(true); setErr(null); setRes(null);
    try {
      setRes(await getJson<AskResult>('/api/regulatory/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, jurisdiction: jur }) }));
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  };
  const chips = res ? res.sources.filter((s) => !res.cited?.length || res.cited.includes(s.n)).slice(0, 5) : [];
  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Answers are generated only from real official documents (FCC, eCFR, OSHA, PHMSA, EPA, state statutes). Synthetic demo text is excluded.
        Retrieval: semantic + keyword search over parsed official text, filtered to the selected (or named) state plus federal rules. Not legal advice.
      </p>
      <form onSubmit={submit} className="flex gap-2">
        <label htmlFor="reg-q" className="sr-only">Regulatory question</label>
        <input id="reg-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about notice periods, Section 214, 811, lead cable…"
          className="flex-1 rounded border border-input bg-card px-3 py-2 text-sm" maxLength={500} />
        <button type="submit" disabled={busy} className="inline-flex items-center gap-1 rounded bg-primary-strong px-3 py-2 text-sm text-primary-foreground disabled:opacity-60">
          <Search size={16} strokeWidth={1.5} aria-hidden="true" />{busy ? 'Searching…' : 'Ask'}
        </button>
      </form>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED.map((s) => (
          <button key={s} type="button" onClick={() => submit(undefined, s)} className="rounded-full border border-input bg-card px-3 py-1 text-xs text-secondary hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">{s}</button>
        ))}
      </div>
      {err && <EmptyState title="The question could not be answered"><p>{err}</p></EmptyState>}
      {res && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-3" aria-live="polite">
          {res.jurisdiction_applied && res.jurisdiction_applied !== 'ALL' && (
            <p className="text-xs text-muted-foreground">
              Sources limited to {res.jurisdiction_applied} + federal{res.jurisdiction_source === 'detected_in_question' ? ' (state detected in your question)' : ''}.
            </p>
          )}
          {res.answer && <p className={`text-sm whitespace-pre-wrap ${res.insufficient ? 'text-warning' : 'text-foreground'}`}>{res.answer}</p>}
          {res.llm_error && <p className="text-xs text-warning">{res.llm_error}</p>}
          {chips.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-secondary mb-1">Sources</p>
              <ol className="flex flex-wrap gap-x-4 gap-y-2">
                {chips.map((s) => (
                  <li key={s.n} className="flex gap-1 text-xs"><span className="text-muted-foreground">[S{s.n}]</span>
                    <CitationLink title={s.title} url={s.url} verificationStatus={s.verification_status} citation={s.citation} lastVerified={s.last_verified} /></li>
                ))}
              </ol>
            </div>
          )}
          {res.mode === 'passages_only' && chips.map((s) => (
            <blockquote key={`x${s.n}`} className="border-l-2 border-border pl-3 text-xs text-muted-foreground">[S{s.n}] {s.excerpt}…</blockquote>
          ))}
        </div>
      )}
    </div>
  );
}

function SourcesView({ jur }: { jur: string }) {
  const [rows, setRows] = useState<SourceRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { getJson<SourceRow[]>('/api/regulatory/sources').then(setRows).catch((e) => setErr(e.message)); }, []);
  if (err) return <EmptyState title="Could not load the source register"><p>{err}</p></EmptyState>;
  if (!rows) return <p className="text-sm text-muted-foreground">Loading official sources…</p>;
  const isFed = (j: string) => j === 'US' || j.startsWith('US-');
  const shown = rows.filter((r) => jur === 'ALL' || r.jurisdiction === jur || isFed(r.jurisdiction)); // state view = state + federal baseline
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <table className="w-full text-sm">
        <caption className="sr-only">Official regulatory source register</caption>
        <thead className="bg-muted text-left text-xs text-muted-foreground">
          <tr><th scope="col" className="p-2">Jurisdiction</th><th scope="col" className="p-2">Authority</th><th scope="col" className="p-2">Topic</th><th scope="col" className="p-2">Source</th><th scope="col" className="p-2">Status</th></tr>
        </thead>
        <tbody>
          {shown.map((r) => (
            <tr key={r.source_id} className="border-t border-border align-top">
              <td className="p-2 whitespace-nowrap font-medium text-secondary">{r.jurisdiction}</td>
              <td className="p-2">{r.authority}</td>
              <td className="p-2">{r.topic?.replace(/_/g, ' ')}</td>
              <td className="p-2 min-w-[16rem]"><CitationLink title={r.title} url={r.official_url} verificationStatus={r.verification_status} citation={r.citation} lastVerified={r.last_verified} /></td>
              <td className="p-2 whitespace-nowrap"><StatusCell status={r.verification_status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RegulatoryTab() {
  const [jur, setJur] = useState('ALL');
  const [sub, setSub] = useState<Sub>('matrix');
  const [kpis, setKpis] = useState<Kpis | null>(null);
  useEffect(() => { getJson<Kpis>('/api/regulatory/kpis').then(setKpis).catch(() => setKpis(null)); }, []);
  return (
    <div>
      <TabHeader title="Regulatory" question="Are we clear on notice, 811 and permit rules in every jurisdiction?"
        badges={<span className="rounded border border-border bg-card px-2 py-0.5 text-xs font-medium text-success">REAL OFFICIAL SOURCES</span>} />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <KpiCard label="Requirements verified" value={kpis ? `${kpis.verified} / ${kpis.requirements}` : '—'} sub={kpis ? `${kpis.jurisdictions} jurisdictions` : undefined} valueClass="text-success" />
        <KpiCard label="Flagged gaps" value={kpis ? kpis.gaps : '—'} sub="Unverified, conflict, not found or state gap" valueClass="text-warning" />
        <KpiCard label="Official sources verified" value={kpis ? `${kpis.verified_sources} / ${kpis.sources}` : '—'} sub="FCC, eCFR, OSHA, PHMSA, EPA, states" />
        <KpiCard label="Parsed official text chunks" value={kpis ? kpis.real_chunks.toLocaleString() : '—'} sub="Synthetic text excluded" />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <TabBar tabs={SUBS} activeId={sub} onChange={setSub} idPrefix="reg" ariaLabel="Regulatory views" />
        <label className="text-xs text-muted-foreground flex items-center gap-2">Jurisdiction
          <select value={jur} onChange={(e) => setJur(e.target.value)} className="rounded border border-input bg-card px-2 py-1 text-sm text-foreground">
            {JURISDICTIONS.map((j) => <option key={j.id} value={j.id}>{j.label}</option>)}
          </select>
        </label>
      </div>
      <section role="tabpanel" id={panelId('reg', sub)} aria-labelledby={tabId('reg', sub)}>
        {sub === 'matrix' && <MatrixView jur={jur} />}
        {sub === 'ask' && <AskView jur={jur} />}
        {sub === 'sources' && <SourcesView jur={jur} />}
      </section>
    </div>
  );
}
