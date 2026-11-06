/**
 * tabs/regulatory/RegulatoryTab.tsx — Regulatory tab of the unified Copper Retirement Accelerator (ACC-APP-PORT-REG).
 * Ported 2026-10-24 from the retired standalone regulatory-assistant app. Real sources only:
 *   Matrix  -> /api/regulatory/matrix  (jurisdiction_requirements_cited, official_url on every row)
 *   Ask     -> /api/regulatory/ask     (real chunks only, every answer lists Sources chips; uncited = suppressed)
 *   Sources -> /api/regulatory/sources (regulatory_source_register)
 * Citation display per BRAND_GUIDE §0.2 (CitationLink). Colors from styles/tokens.css only.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { Search, AlertTriangle, SearchX } from 'lucide-react';
import { TabHeader, TabBar, KpiCard, EmptyState, CitationLink, StatusBadge, getStatusBadge, isCitableStatus, panelId, tabId } from '../../components/shared';

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
interface AskResult { answer: string | null; grounded: boolean; insufficient?: boolean; cited?: number[]; sources: AskSource[]; mode: string; llm_error?: string; jurisdiction_applied?: string; jurisdiction_source?: 'selector' | 'detected_in_question' | 'federal_cue' | 'none' }
// null = that sub-query failed (non-403); server sets degraded:true. Render '—', never 0 (ACC-QA-R11-DIFF-REVIEW).
type N = number | null;
interface Kpis { requirements: N; verified: N; gaps: N; jurisdictions: N; sources: N; verified_sources: N; real_chunks: N; citable?: N; derived?: N; no_state_rule?: N; degraded?: boolean; degraded_sources?: string[] }
const dash = (v: N | undefined) => (v == null ? '—' : v.toLocaleString());

const JURISDICTIONS = [
  { id: 'ALL', label: 'All (federal + 6 states)' }, { id: 'US', label: 'Federal only' },
  { id: 'WA', label: 'Washington' }, { id: 'AZ', label: 'Arizona' }, { id: 'CO', label: 'Colorado' },
  { id: 'MN', label: 'Minnesota' }, { id: 'OR', label: 'Oregon' }, { id: 'ID', label: 'Idaho' },
];
// DEC-ASK-KILL-CRITERION-20261104 (B): Ask ships as Beta BY DEFAULT. Set to false only after ACC-ML-ASK-FINAL-GATE PASSES.
const ASK_BETA = true;
// ACC-APP-DES-R11-POLISH: human labels for server degraded_sources keys (no UC table names in the UI).
const DEGRADED_LABELS: Record<string, string> = { jurisdiction_requirements_cited: 'jurisdiction matrix', regulatory_source_register: 'source register', regulatory_doc_chunks: 'document text' };
const ASK_BETA_NOTE = 'Answers may be incomplete; verify against the linked official source.';
const SUBS = [{ id: 'matrix', label: 'Jurisdiction matrix' }, { id: 'ask', label: ASK_BETA ? 'Ask the sources (Beta)' : 'Ask the sources' }, { id: 'sources', label: 'Source register' }] as const;
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

/** A row is citable only if its status is citable (BRAND_GUIDE #status-badges) AND it carries an official URL (charter citation rule). */
const rowVerified = (r: { verification_status: string; official_url: string | null }) => isCitableStatus(r.verification_status) && !!r.official_url;

function StatusCell({ status, hasUrl = true }: { status: string; hasUrl?: boolean }) {
  if (!hasUrl) {
    return <span className="inline-flex items-center gap-1 text-xs text-warning"><AlertTriangle size={14} strokeWidth={1.5} aria-hidden="true" />Flagged gap (no official source)</span>;
  }
  // ACC-APP-REG-BADGE-STATUS: one badge per status (Verified / Derived / No state requirement / Unverified).
  return <StatusBadge status={status} />;
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
      <span role="status">{rows.length} requirements · {rows.length - gapCount} citable · {gapCount} flagged gaps</span>
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
                <td className="p-2 whitespace-nowrap">{getStatusBadge(r.verification_status).kind === 'no_state_rule' && r.official_url ? 'None in cited sections' : verified && r.value_numeric ? `${Number(r.value_numeric)} ${(r.value_unit || '').replace(/_/g, ' ')}` : '—'}</td>
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

// ACC-APP-REG-INSUFFICIENT-UI: BRAND_GUIDE #ask-insufficient (binding). Strip the model's prefix token; never render it.
const INSUFFICIENT_PREFIX = /^\s*INSUFFICIENT SOURCES:\s*/i;
const jurName = (code?: string) => (!code || code === 'US' || code.startsWith('US-') ? 'Federal' : JURISDICTIONS.find((j) => j.id === code)?.label || code);

function InsufficientSourceCard({ s }: { s: AskSource }) {
  const [open, setOpen] = useState(false);
  const exId = `reg-ins-ex-${s.n}`;
  return (
    <li className="rounded border border-border bg-card p-3 space-y-2">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <CitationLink title={s.title} url={s.url} verificationStatus={s.verification_status} citation={s.citation} lastVerified={s.last_verified} />
        <span className="rounded border border-border bg-muted px-2 py-0.5 text-xs text-foreground">{jurName(s.jurisdiction)}</span>
      </div>
      {s.excerpt && (
        <>
          <blockquote id={exId} className={`border-l-2 border-border pl-3 text-sm text-muted-foreground whitespace-pre-wrap ${open ? '' : 'line-clamp-4'}`}>{s.excerpt}</blockquote>
          <button type="button" aria-expanded={open} aria-controls={exId} onClick={() => setOpen((v) => !v)}
            className="text-xs font-medium text-secondary underline min-h-[44px] md:min-h-0 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
            {open ? 'Show less' : 'Show more'}
          </button>
        </>
      )}
    </li>
  );
}

function AskInsufficient({ res, question, onAsk }: { res: AskResult; question: string; onAsk: (text: string) => void }) {
  const reason = (res.answer || '').replace(INSUFFICIENT_PREFIX, '').trim();
  // Retrieval order, not filtered by `cited`; never a card without a URL.
  const cards = res.sources.filter((s) => !!s.url).slice(0, 3);
  const top = cards[0];
  const needState = !res.jurisdiction_applied || res.jurisdiction_applied === 'ALL';
  const chip = 'rounded-full border border-input bg-card px-3 py-1 text-xs text-secondary hover:bg-muted min-h-[44px] md:min-h-0 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none';
  return (
    <div role="status" data-state="insufficient" className="rounded-lg border border-border bg-card p-4 space-y-3" style={{ borderLeft: '4px solid rgb(var(--color-warning-text))' }}>
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <SearchX size={16} strokeWidth={1.5} aria-hidden="true" />
        The official sources found don't fully answer this question.
      </h3>
      <p className="text-sm text-foreground whitespace-pre-wrap"><span className="font-medium">What's missing: </span>{reason || 'The retrieved passages cover related rules but not the specific point asked.'}</p>
      {cards.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-secondary mb-1">Closest official sources</p>
          <ol className="space-y-2">{cards.map((s) => <InsufficientSourceCard key={s.n} s={s} />)}</ol>
        </div>
      )}
      <div>
        <p className="text-xs font-semibold text-secondary mb-1">Try a narrower question</p>
        <div className="flex flex-wrap gap-2">
          {top?.citation && <button type="button" className={chip} onClick={() => onAsk(`What does ${top.citation} require?`)}>What does {top.citation} require?</button>}
          {needState
            ? <button type="button" className={chip} onClick={() => document.getElementById('reg-jur')?.focus()}>Pick a state above</button>
            : top && <button type="button" className={chip} onClick={() => onAsk(`${question} (${jurName(top.jurisdiction)})`)}>{question} ({jurName(top.jurisdiction)})</button>}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">Answers come only from official text. When the text is silent, we show the closest sources instead of guessing. Not legal advice.</p>
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
      {ASK_BETA && (
        <div data-state="beta" className="flex flex-wrap items-center gap-2 rounded border border-border bg-card px-3 py-2">
          <span className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-xs font-medium text-warning" title="Beta: did not yet pass the 80% grounded-answer gate">
            <AlertTriangle size={14} strokeWidth={1.5} aria-hidden="true" />Beta
          </span>
          <span className="text-xs text-foreground">{ASK_BETA_NOTE}</span>
        </div>
      )}
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
      {res && res.insufficient && (
        <div aria-live="polite" className="space-y-2">
          {res.jurisdiction_applied && res.jurisdiction_applied !== 'ALL' && (
            <p className="text-xs text-muted-foreground">
              {res.jurisdiction_source === 'federal_cue'
                ? 'Sources limited to federal rules (federal topic detected in your question).'
                : `Sources limited to ${res.jurisdiction_applied} + federal${res.jurisdiction_source === 'detected_in_question' ? ' (state detected in your question)' : ''}.`}
            </p>
          )}
          <AskInsufficient res={res} question={q} onAsk={(t) => submit(undefined, t)} />
        </div>
      )}
      {res && !res.insufficient && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-3" aria-live="polite">
          {res.jurisdiction_applied && res.jurisdiction_applied !== 'ALL' && (
            <p className="text-xs text-muted-foreground">
              {res.jurisdiction_source === 'federal_cue'
                ? 'Sources limited to federal rules (federal topic detected in your question).'
                : `Sources limited to ${res.jurisdiction_applied} + federal${res.jurisdiction_source === 'detected_in_question' ? ' (state detected in your question)' : ''}.`}
            </p>
          )}
          {res.answer && <p className="text-sm whitespace-pre-wrap text-foreground">{res.answer}</p>}
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
        <KpiCard label="Requirements citable" value={kpis && kpis.requirements != null ? `${dash(kpis.citable ?? kpis.verified)} / ${dash(kpis.requirements)}` : '—'} sub={kpis && kpis.requirements != null ? `${dash(kpis.verified)} verified · ${dash(kpis.derived ?? 0)} derived · ${dash(kpis.no_state_rule ?? 0)} no state rule · ${dash(kpis.jurisdictions)} jurisdictions` : kpis ? 'Could not load' : undefined} valueClass="text-success" />
        <KpiCard label="Flagged gaps" value={kpis ? dash(kpis.gaps) : '—'} sub={kpis && kpis.gaps == null ? 'Could not load' : 'Unverified or no official source'} valueClass="text-warning" />
        <KpiCard label="Official sources verified" value={kpis && kpis.sources != null ? `${dash(kpis.verified_sources)} / ${dash(kpis.sources)}` : '—'} sub={kpis && kpis.sources == null ? 'Could not load' : 'FCC, eCFR, OSHA, PHMSA, EPA, states'} />
        <KpiCard label="Parsed official text chunks" value={kpis ? dash(kpis.real_chunks) : '—'} sub={kpis && kpis.real_chunks == null ? 'Could not load' : 'Synthetic text excluded'} />
      </div>
      {kpis?.degraded && (
        <p role="status" data-state="degraded" className="mb-3 rounded border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
          Some regulatory KPIs could not load ({(kpis.degraded_sources || []).map((s) => DEGRADED_LABELS[s] || 'regulatory data').join(', ')}); affected tiles show —.
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <TabBar tabs={SUBS} activeId={sub} onChange={setSub} idPrefix="reg" ariaLabel="Regulatory views" />
        <label className="text-xs text-muted-foreground flex items-center gap-2">Jurisdiction
          <select id="reg-jur" value={jur} onChange={(e) => setJur(e.target.value)} className="rounded border border-input bg-card px-2 py-1 text-sm text-foreground">
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
