/**
 * tabs/commodity/CommodityTab.tsx — Commodity & Value tab of the unified Copper Retirement Accelerator (ACC-APP-PORT-COMMODITY).
 * Ported 2026-10-25 from the standalone commodity-dashboard app (mock-only) onto existing UC data.
 * Answers: "What is the recovered copper worth, and when should we sell?"
 *   Price history -> /api/commodity/prices      REAL IMF PCOPPUSDM (FRED), cited per point
 *   Forecast      -> /api/commodity/forecast    label driven by table comment (SYNTHETIC until DEC-COMMODITY-REAL-RETRAIN)
 *   ROI sliders   -> /api/commodity/assumptions low/base/high per input, each with its source URL or PARTNER INPUT label
 *   Value base    -> /api/commodity/value       v_partner_value_wire_center (NIST lb/kft x SYNTHETIC plant)
 *   Workforce     -> /api/commodity/contractors gold_contractor_scorecard (SYNTHETIC)
 * Regulatory filing cost is NOT in the ROI (DEC-ROI-FILING-COST); FCC fee bounds are shown only as a labeled reference.
 * Colors from styles/tokens.css only.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { TabHeader, KpiCard, EmptyState, SyntheticBadge, CitationLink } from '../../components/shared';

interface PricePoint { month: string; usd_lb: number | null; usd_ton: number | null; source: string; source_url: string; is_synthetic: boolean }
interface Forecast { synthetic: boolean; table_comment: string; model_version: string | null; generated: string | null; points: { month: string; usd_lb: number | null }[] }
interface Assumption {
  code: string; group: string; awg: number | null; low: number | null; base: number | null; high: number | null; unit: string;
  source_url: string | null; source_label: string | null; is_synthetic: boolean; comment: string | null;
}
interface ValueData {
  totals: { wire_centers: number; copper_lbs: number; working_lines: number; migration_cost: number; decommission_cost: number; fiber_build_cost: number; customers_impacted: number; customers_migrated: number; retired_wcs: number };
  waves: { wave: string; wcs: number; copper_lbs: number; lines: number; customers: number }[];
  wire_centers: { id: string; name: string; state: string; wave: string; copper_lbs: number; lines: number; fiber_ready: boolean; customers: number }[];
}
interface Contractor { name: string; type: string; state: string; safety: number | null; rating: number | null; sla: number | null; incidents: number; insurance_expired: boolean; cert_risk: boolean; dispatch: string }
type Level = 'low' | 'base' | 'high';

const LEVELS: Level[] = ['low', 'base', 'high'];
const LEVEL_LABEL: Record<Level, string> = { low: 'Low', base: 'Base', high: 'High' };
// ROI inputs the calculator drives (codes in roi_calculator_assumptions).
const INPUTS: { code: string; label: string; fmt: (v: number) => string }[] = [
  { code: 'salvage_recovery_rate', label: 'Copper recovery rate', fmt: (v) => `${Math.round(v * 100)}%` },
  { code: 'copper_price_usd_lb', label: 'Copper price', fmt: (v) => `$${v.toFixed(2)}/lb` },
  { code: 'salvage_cost_usd_lb', label: 'Salvage cost', fmt: (v) => `$${v.toFixed(2)}/lb` },
  { code: 'opex_saved_per_line_year', label: 'Copper O&M per line', fmt: (v) => `$${Math.round(v)}/line/yr` },
  { code: 'opex_reduction_pct_fiber_vs_copper', label: 'O&M avoided on fiber', fmt: (v) => `${Math.round(v * 100)}%` },
];

const fmtInt = (n: number | null | undefined) => (n == null ? '—' : Math.round(n).toLocaleString('en-US'));
const fmtUsd = (n: number | null | undefined) => {
  if (n == null || !Number.isFinite(n)) return '—';
  const a = Math.abs(n), s = n < 0 ? '-' : '';
  if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `${s}$${(a / 1e3).toFixed(1)}K`;
  return `${s}$${Math.round(a)}`;
};

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body.data as T;
}
function useApi<T>(url: string): { data: T | null; err: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    setData(null); setErr(null);
    getJson<T>(url).then((d) => live && setData(d)).catch((e) => live && setErr((e as Error).message));
    return () => { live = false; };
  }, [url]);
  return { data, err };
}

function Card({ title, badges, children }: { title: string; badges?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h3 className="text-base font-semibold text-secondary">{title}</h3>
        {badges && <div className="flex items-center gap-2">{badges}</div>}
      </div>
      {children}
    </section>
  );
}

/** Dependency-free SVG line chart: real IMF history (solid) + forecast (dashed). */
function PriceChart({ history, forecast }: { history: PricePoint[]; forecast: Forecast | null }) {
  const W = 720, H = 260, L = 48, R = 12, T = 12, B = 28;
  const hist = history.filter((p) => p.usd_lb != null) as (PricePoint & { usd_lb: number })[];
  const fc = (forecast?.points ?? []).filter((p) => p.usd_lb != null) as { month: string; usd_lb: number }[];
  const months = Array.from(new Set([...hist.map((p) => p.month), ...fc.map((p) => p.month)])).sort();
  if (!months.length) return <EmptyState title="No price data" />;
  const vals = [...hist.map((p) => p.usd_lb), ...fc.map((p) => p.usd_lb)];
  const lo = Math.floor(Math.min(...vals) * 2) / 2, hi = Math.ceil(Math.max(...vals) * 2) / 2;
  const x = (m: string) => L + (months.indexOf(m) / Math.max(months.length - 1, 1)) * (W - L - R);
  const y = (v: number) => T + ((hi - v) / Math.max(hi - lo, 0.01)) * (H - T - B);
  const path = (pts: { month: string; usd_lb: number }[]) => pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.month).toFixed(1)},${y(p.usd_lb).toFixed(1)}`).join(' ');
  const ticks = [lo, (lo + hi) / 2, hi];
  const yearTicks = months.filter((m) => m.endsWith('-01-01'));
  const last = hist[hist.length - 1];
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
        aria-label={`Copper price USD per lb, ${months[0]} to ${months[months.length - 1]}. Latest real ${last ? `${last.month}: $${last.usd_lb.toFixed(2)}` : 'n/a'}.`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} style={{ stroke: 'rgb(var(--color-border))' }} strokeWidth={1} />
            <text x={L - 6} y={y(t) + 4} textAnchor="end" fontSize={12} style={{ fill: 'rgb(var(--color-muted-fg))' }}>${t.toFixed(2)}</text>
          </g>
        ))}
        {yearTicks.map((m) => (
          <text key={m} x={x(m)} y={H - 8} textAnchor="middle" fontSize={12} style={{ fill: 'rgb(var(--color-muted-fg))' }}>{m.slice(0, 4)}</text>
        ))}
        <path d={path(hist)} fill="none" style={{ stroke: 'rgb(var(--viz-2))' }} strokeWidth={2} />
        {fc.length > 0 && <path d={path(fc)} fill="none" style={{ stroke: 'rgb(var(--viz-1))' }} strokeWidth={2} strokeDasharray="6 4" />}
        {last && <circle cx={x(last.month)} cy={y(last.usd_lb)} r={4} style={{ fill: 'rgb(var(--viz-2))' }} />}
      </svg>
      <figcaption className="flex flex-wrap gap-4 text-xs text-muted-foreground mt-1">
        <span className="inline-flex items-center gap-1"><svg width="16" height="4" aria-hidden="true"><line x1="0" x2="16" y1="2" y2="2" style={{ stroke: 'rgb(var(--viz-2))' }} strokeWidth={2} /></svg>IMF monthly average (real)</span>
        {fc.length > 0 && <span className="inline-flex items-center gap-1"><svg width="16" height="4" aria-hidden="true"><line x1="0" x2="16" y1="2" y2="2" style={{ stroke: 'rgb(var(--viz-1))' }} strokeWidth={2} strokeDasharray="4 3" /></svg>Forecast {forecast?.model_version ? `(${forecast.model_version})` : ''}{forecast?.synthetic ? ' — synthetic' : ''}</span>}
      </figcaption>
    </figure>
  );
}

function LevelPicker({ name, value, onChange, a }: { name: string; value: Level; onChange: (l: Level) => void; a: Assumption }) {
  return (
    <div role="radiogroup" aria-label={name} className="inline-flex rounded border border-input overflow-hidden">
      {LEVELS.map((l) => {
        const v = a[l];
        const disabled = v == null;
        return (
          <button key={l} type="button" role="radio" aria-checked={value === l} disabled={disabled}
            onClick={() => onChange(l)}
            className={`px-2 py-1 text-xs ${value === l ? 'bg-secondary text-secondary-foreground' : 'bg-card text-foreground'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
            {LEVEL_LABEL[l]}
          </button>
        );
      })}
    </div>
  );
}

function SourceCell({ a }: { a: Assumption }) {
  if (a.source_url) return <CitationLink title={a.source_url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]} url={a.source_url} citation={a.comment?.slice(0, 120) || undefined} />;
  return <span className="ll-badge-synthetic" title={a.comment || undefined}>{(a.source_label || 'PARTNER INPUT').replace(/_/g, ' ')}</span>;
}

export function CommodityTab() {
  const [state, setState] = useState('ALL');
  const prices = useApi<PricePoint[]>('/api/commodity/prices?months=60');
  const forecast = useApi<Forecast>('/api/commodity/forecast');
  const assumptions = useApi<Assumption[]>('/api/commodity/assumptions');
  const value = useApi<ValueData>(`/api/commodity/value?state=${encodeURIComponent(state)}`);
  const contractors = useApi<Contractor[]>(`/api/commodity/contractors?state=${encodeURIComponent(state)}`);
  const filters = useApi<{ footprint: string[] }>('/api/commodity/filters');
  const footprint = filters.data?.footprint ?? ['CO', 'MN', 'WA', 'OR', 'ID', 'AZ']; // server FOOTPRINT_STATES env wins
  const [levels, setLevels] = useState<Record<string, Level>>(() => Object.fromEntries(INPUTS.map((i) => [i.code, 'base' as Level])));

  const byCode = useMemo(() => Object.fromEntries((assumptions.data ?? []).filter((a) => a.awg == null).map((a) => [a.code, a])) as Record<string, Assumption>, [assumptions.data]);
  const pick = (code: string): number | null => {
    const a = byCode[code]; if (!a) return null;
    return a[levels[code] ?? 'base'] ?? a.base;
  };

  const roi = useMemo(() => {
    const t = value.data?.totals; if (!t) return null;
    const rec = pick('salvage_recovery_rate'), price = pick('copper_price_usd_lb'), cost = pick('salvage_cost_usd_lb');
    const perLine = pick('opex_saved_per_line_year'), red = pick('opex_reduction_pct_fiber_vs_copper');
    if ([rec, price, cost, perLine, red].some((v) => v == null)) return null;
    const recoverable = t.copper_lbs * rec!;
    const gross = recoverable * price!;
    const salvageCost = recoverable * cost!;
    const net = gross - salvageCost;
    const opex = t.working_lines * perLine! * red!;
    const oneTime = t.migration_cost + t.decommission_cost; // ex fiber build, ex regulatory filing (DEC-ROI-FILING-COST)
    const payback = opex > 0 ? Math.max(0, (oneTime - net) / opex) : null;
    return { recoverable, gross, salvageCost, net, opex, oneTime, payback, fiveYear: net + 5 * opex - oneTime };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.data, byCode, levels]);

  const latest = prices.data?.[prices.data.length - 1];
  const fcNext = forecast.data?.points.find((p) => latest && p.month > latest.month) ?? forecast.data?.points[0];
  const filing = (assumptions.data ?? []).find((a) => a.code === 'regulatory_filing_cost_per_wc');

  return (
    <div>
      <TabHeader title="Commodity & Value" question="What is the recovered copper worth, and when should we sell?"
        badges={<><span className="text-xs text-muted-foreground">Price: real IMF data</span><SyntheticBadge label="SYNTHETIC PLANT + WORKFORCE" /></>} />

      <div className="flex flex-wrap items-end gap-3 mb-4">
        <label className="text-xs text-muted-foreground flex flex-col gap-1">
          State
          <select value={state} onChange={(e) => setState(e.target.value)} className="rounded border border-input bg-card px-2 py-1.5 text-sm text-foreground">
            <option value="ALL">All footprint states</option>
            {footprint.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 mb-4">
        <KpiCard label="Copper price (latest month)" value={latest?.usd_lb != null ? `$${latest.usd_lb.toFixed(2)}/lb` : prices.err ? '—' : '…'}
          sub={latest ? <CitationLink title={`IMF PCOPPUSDM ${latest.month.slice(0, 7)}`} url={latest.source_url} /> : undefined} />
        <KpiCard label="Forecast next month" value={fcNext?.usd_lb != null ? `$${fcNext.usd_lb.toFixed(2)}/lb` : forecast.err ? '—' : '…'}
          sub={forecast.data ? (forecast.data.synthetic ? 'SYNTHETIC forecaster output' : `model ${forecast.data.model_version ?? ''}`) : undefined} />
        <KpiCard label="Copper in place" value={value.data ? `${fmtInt(value.data.totals.copper_lbs)} lb` : '…'} sub={value.data ? `${value.data.totals.wire_centers} wire centers (synthetic plant)` : undefined} />
        <KpiCard label="Net salvage value" value={roi ? fmtUsd(roi.net) : '…'} sub="at selected ROI inputs" valueClass={roi && roi.net < 0 ? 'text-danger' : 'text-success'} />
        <KpiCard label="Annual O&M savings" value={roi ? fmtUsd(roi.opex) : '…'} sub={value.data ? `${fmtInt(value.data.totals.working_lines)} working copper lines` : undefined} valueClass="text-success" />
        <KpiCard label="Customers to migrate" value={value.data ? fmtInt(value.data.totals.customers_impacted - value.data.totals.customers_migrated) : '…'} sub={value.data ? `${fmtInt(value.data.totals.customers_migrated)} migrated so far` : undefined} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-3 mb-4">
        <div className="xl:col-span-3">
          <Card title="Copper price: 5-year history and forecast" badges={forecast.data?.synthetic ? <SyntheticBadge label="FORECAST SYNTHETIC" /> : undefined}>
            {prices.err ? <EmptyState title="Could not load copper prices"><p>{prices.err}</p></EmptyState>
              : prices.data ? <PriceChart history={prices.data} forecast={forecast.data} />
              : <p className="text-sm text-muted-foreground">Loading prices…</p>}
            {latest && <p className="text-xs text-muted-foreground mt-2">History: {latest.source}. <CitationLink title="FRED series PCOPPUSDM" url={latest.source_url} /></p>}
            {forecast.data?.synthetic && latest?.usd_lb != null && fcNext?.usd_lb != null && (
              <p className="text-xs text-warning mt-1">The forecast was trained on synthetic prices and sits {Math.round((1 - fcNext.usd_lb / latest.usd_lb) * 100)}% below the latest real price. Do not use it for sell/hold timing until it is retrained on real IMF data (DEC-COMMODITY-REAL-RETRAIN).</p>
            )}
            {forecast.err && <p className="text-xs text-danger mt-1">Forecast unavailable: {forecast.err}</p>}
          </Card>
        </div>
        <div className="xl:col-span-2">
          <Card title="ROI calculator" badges={<span className="text-xs text-muted-foreground">low / base / high</span>}>
            {assumptions.err ? <EmptyState title="Could not load ROI assumptions"><p>{assumptions.err}</p></EmptyState> : !assumptions.data ? <p className="text-sm text-muted-foreground">Loading assumptions…</p> : (
              <>
                <ul className="space-y-3">
                  {INPUTS.map((i) => {
                    const a = byCode[i.code];
                    if (!a) return <li key={i.code} className="text-xs text-danger">{i.label}: not found in roi_calculator_assumptions</li>;
                    const v = pick(i.code);
                    return (
                      <li key={i.code} className="flex flex-col gap-1">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-sm text-foreground">{i.label}: <strong>{v != null ? i.fmt(v) : '—'}</strong></span>
                          <LevelPicker name={i.label} a={a} value={levels[i.code]} onChange={(l) => setLevels({ ...levels, [i.code]: l })} />
                        </div>
                        <SourceCell a={a} />
                      </li>
                    );
                  })}
                </ul>
                {roi && (
                  <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-sm mt-4 border-t border-border pt-3">
                    <dt className="text-muted-foreground">Recoverable copper</dt><dd className="text-right">{fmtInt(roi.recoverable)} lb</dd>
                    <dt className="text-muted-foreground">Gross salvage</dt><dd className="text-right">{fmtUsd(roi.gross)}</dd>
                    <dt className="text-muted-foreground">Salvage cost</dt><dd className="text-right">{fmtUsd(-roi.salvageCost)}</dd>
                    <dt className="text-muted-foreground">One-time cost ex fiber build <SyntheticBadge /></dt><dd className="text-right">{fmtUsd(-roi.oneTime)}</dd>
                    <dt className="text-muted-foreground">5-year net value</dt><dd className={`text-right font-semibold ${roi.fiveYear < 0 ? 'text-danger' : 'text-success'}`}>{fmtUsd(roi.fiveYear)}</dd>
                    <dt className="text-muted-foreground">Simple payback</dt><dd className="text-right">{roi.payback == null ? '—' : `${roi.payback.toFixed(1)} yrs`}</dd>
                  </dl>
                )}
                {filing && (
                  <p className="text-xs text-muted-foreground mt-3">
                    Not included: regulatory compliance cost (partner discovery input). FCC filing fee reference only: {filing.low != null ? `$${fmtInt(filing.low)}` : '—'}–{filing.high != null ? `$${fmtInt(filing.high)}` : '—'} per wire center.{' '}
                    {filing.source_url && <CitationLink title="FCC fee schedule" url={filing.source_url} />}
                  </p>
                )}
              </>
            )}
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 mb-4">
        <Card title="Recovery by retirement wave" badges={<SyntheticBadge />}>
          {value.err ? <EmptyState title="Could not load value data"><p>{value.err}</p></EmptyState> : !value.data ? <p className="text-sm text-muted-foreground">Loading…</p> : (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-muted-foreground"><th className="py-1">Wave</th><th className="text-right">Wire centers</th><th className="text-right">Copper lb</th><th className="text-right">Net salvage</th><th className="text-right">Customers</th></tr></thead>
              <tbody>
                {value.data.waves.map((w) => {
                  const rec = pick('salvage_recovery_rate') ?? 0, p = pick('copper_price_usd_lb') ?? 0, c = pick('salvage_cost_usd_lb') ?? 0;
                  return (
                    <tr key={w.wave} className="border-t border-border">
                      <td className="py-1">{w.wave}</td><td className="text-right">{w.wcs}</td><td className="text-right">{fmtInt(w.copper_lbs)}</td>
                      <td className="text-right">{fmtUsd(w.copper_lbs * rec * (p - c))}</td><td className="text-right">{w.customers}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          <p className="text-xs text-muted-foreground mt-2">Copper lb = pair length x 2 conductors x lb/kft by gauge. <CitationLink title="NIST Handbook 100 copper wire tables" url="https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf" /></p>
        </Card>
        <Card title="Top wire centers by copper in place" badges={<SyntheticBadge />}>
          {value.data && (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-muted-foreground"><th className="py-1">Wire center</th><th>State</th><th>Wave</th><th className="text-right">Copper lb</th><th className="text-right">Lines</th><th>Fiber</th></tr></thead>
              <tbody>
                {value.data.wire_centers.map((w) => (
                  <tr key={w.id} className="border-t border-border">
                    <td className="py-1">{w.name}</td><td>{w.state}</td><td>{w.wave}</td><td className="text-right">{fmtInt(w.copper_lbs)}</td><td className="text-right">{w.lines}</td>
                    <td className={w.fiber_ready ? 'text-success' : 'text-warning'}>{w.fiber_ready ? 'Ready' : 'Not ready'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      <Card title="Who digs: top-rated contractors" badges={<SyntheticBadge />}>
        {contractors.err ? <EmptyState title="Could not load contractors"><p>{contractors.err}</p></EmptyState> : !contractors.data ? <p className="text-sm text-muted-foreground">Loading…</p> : contractors.data.length === 0 ? <EmptyState title="No contractors in this state" /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-muted-foreground"><th className="py-1">Contractor</th><th>Type</th><th>State</th><th className="text-right">Rating</th><th className="text-right">Safety</th><th className="text-right">SLA %</th><th className="text-right">Incidents</th><th>Flags</th><th>Dispatch</th></tr></thead>
              <tbody>
                {contractors.data.map((c) => (
                  <tr key={`${c.name}-${c.state}-${c.type}`} className="border-t border-border">
                    <td className="py-1">{c.name}</td><td>{c.type.replace(/_/g, ' ')}</td><td>{c.state}</td>
                    <td className="text-right">{c.rating ?? '—'}</td><td className="text-right">{c.safety ?? '—'}</td><td className="text-right">{c.sla ?? '—'}</td><td className="text-right">{c.incidents}</td>
                    <td className="text-danger">{[c.insurance_expired && 'Insurance expired', c.cert_risk && 'Cert risk'].filter(Boolean).join(', ') || <span className="text-muted-foreground">None</span>}</td>
                    <td>{c.dispatch}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
