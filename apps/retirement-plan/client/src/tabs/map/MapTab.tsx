/**
 * tabs/map/MapTab.tsx — Map & Risk tab of the unified Copper Retirement Accelerator (ACC-APP-PORT-MAP).
 * Ported 2026-10-25 from the retired standalone copper-map Dash app. Answers: "Where is our copper, and which plant is most at risk?"
 *   KPIs        -> /api/map/kpis          (gold_retirement_executive_summary footprint + copper_risk_predictions)
 *   Map         -> /api/map/devices       (2,672 model-scored devices) + /api/map/wire-centers (103 wire centers)
 *   Scorecards  -> /api/map/states, /api/map/wire-centers (retirement priority rank)
 * Dependency-free SVG map (no map library / tiles) so the partner build needs no extra npm packages or API keys.
 * Colors from styles/tokens.css only (risk tiers use --risk-* fills; text uses text-safe tokens).
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { MapPin, Radio } from 'lucide-react';
import { TabHeader, KpiCard, EmptyState, SyntheticBadge, getFootprintLabel } from '../../components/shared';

interface Kpis {
  footprint_devices: number; wire_centers: number; customers_affected: number; fiber_ready_pct: number;
  footprint_critical: number; footprint_high: number; footprint_states: number; scored_devices: number;
  scored_critical: number; scored_high: number; model_version: string | null; footprint: string[];
  serving_endpoint: string | null; // ACC-APP-SERVING-ENDPOINT-VAR: from server env SERVING_ENDPOINT
}
interface Device { id: string; type: string; status: string; tier: Tier; confidence: number | null; state: string; lat: number | null; lon: number | null }
interface WireCenter {
  id: string; name: string; clli: string; state: string; fiber_ready: boolean; puc_filing_required: boolean; puc_name: string;
  devices: number; critical: number; high: number; customers: number; readiness: number; priority_rank: number; lat: number | null; lon: number | null;
}
interface StateRow { state: string; devices: number; critical: number; high: number; wire_centers: number; fiber_ready_pct: number; customers: number; dig_incidents: number; regulatory_violations: number; health: string }
type Tier = 'critical' | 'high' | 'medium' | 'low';
type Selection = { kind: 'device'; d: Device } | { kind: 'wc'; w: WireCenter } | null;

const TIERS: Tier[] = ['critical', 'high', 'medium', 'low'];
const TIER_FILL: Record<Tier, string> = {
  critical: 'rgb(var(--risk-critical))', high: 'rgb(var(--risk-high))', medium: 'rgb(var(--risk-medium))', low: 'rgb(var(--risk-low))',
};
const TIER_LABEL: Record<Tier, string> = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' };
const TIER_SHAPE: Record<Tier, string> = { critical: 'large circle', high: 'triangle', medium: 'small circle', low: 'small square' };

/** Tier marker with a NON-COLOR cue per tier (WCAG 1.4.1, ACC-DES-DEF-MAP-RISK-CONTRAST):
 *  critical = large circle + 1px navy stroke, high = triangle, medium = small circle, low = small square. */
function TierMarker({ tier, x, y, scale = 1, selected = false, opacity = 1 }: { tier: Tier; x: number; y: number; scale?: number; selected?: boolean; opacity?: number }) {
  const style = {
    fill: TIER_FILL[tier], stroke: 'rgb(var(--color-secondary))', opacity,
    strokeWidth: selected ? 2 : tier === 'critical' ? 1 : 0.4,
  };
  const r = (selected ? 6 : tier === 'critical' ? 4 : 2.75) * scale;
  if (tier === 'high') {
    const s = (selected ? 7 : 3.75) * scale;
    return <polygon points={`${x},${y - s} ${x + s},${y + s * 0.8} ${x - s},${y + s * 0.8}`} style={style} />;
  }
  if (tier === 'low') {
    const s = (selected ? 5.5 : 2.4) * scale;
    return <rect x={x - s} y={y - s} width={2 * s} height={2 * s} style={style} />;
  }
  return <circle cx={x} cy={y} r={r} style={style} />;
}
const fmt = (n: number | null | undefined) => (n == null ? '—' : n.toLocaleString('en-US'));

// Equirectangular projection over the lower 48 (AK/HI devices stay in the tables, not plotted).
const W = 960, H = 520, PAD = 16;
const BOUNDS = { minLon: -125, maxLon: -66.5, minLat: 24.3, maxLat: 49.5 };
const inLower48 = (lat: number | null, lon: number | null): lat is number =>
  lat != null && lon != null && lat >= BOUNDS.minLat && lat <= BOUNDS.maxLat && lon >= BOUNDS.minLon && lon <= BOUNDS.maxLon;
const px = (lon: number) => PAD + ((lon - BOUNDS.minLon) / (BOUNDS.maxLon - BOUNDS.minLon)) * (W - 2 * PAD);
const py = (lat: number) => PAD + ((BOUNDS.maxLat - lat) / (BOUNDS.maxLat - BOUNDS.minLat)) * (H - 2 * PAD);

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

function Legend() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground" aria-label="Map legend">
      {TIERS.map((t) => (
        <span key={t} className="inline-flex items-center gap-1">
          <svg width="14" height="14" aria-hidden="true"><TierMarker tier={t} x={7} y={7} scale={1.4} /></svg>
          {TIER_LABEL[t]} risk device ({TIER_SHAPE[t]})
        </span>
      ))}
      <span className="inline-flex items-center gap-1">
        <svg width="12" height="12" aria-hidden="true"><rect x="2" y="2" width="8" height="8" transform="rotate(45 6 6)" style={{ fill: 'rgb(var(--color-card))', stroke: 'rgb(var(--color-secondary))', strokeWidth: 1.5 }} /></svg>
        Wire center (footprint)
      </span>
    </div>
  );
}

function RiskMap({ devices, wcs, selected, onSelect }: { devices: Device[]; wcs: WireCenter[]; selected: Selection; onSelect: (s: Selection) => void }) {
  const plotted = devices.filter((d) => inLower48(d.lat, d.lon));
  // draw low -> critical so the riskiest plant sits on top
  const ordered = [...plotted].sort((a, b) => TIERS.indexOf(b.tier) - TIERS.indexOf(a.tier));
  const wcPlotted = wcs.filter((w) => inLower48(w.lat, w.lon));
  const grid = [];
  for (let lon = -120; lon <= -70; lon += 10) grid.push(<line key={`lo${lon}`} x1={px(lon)} x2={px(lon)} y1={PAD} y2={H - PAD} />);
  for (let lat = 25; lat <= 45; lat += 5) grid.push(<line key={`la${lat}`} y1={py(lat)} y2={py(lat)} x1={PAD} x2={W - PAD} />);
  return (
    <figure className="rounded-lg border border-border bg-card p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="group" /* not role=img: it would hide the focusable wire-center buttons from AT */
        aria-label={`Map of ${plotted.length} model-scored copper devices and ${wcPlotted.length} wire centers across the lower 48 states, colored by predicted risk tier`}>
        <rect x="0" y="0" width={W} height={H} style={{ fill: 'rgb(var(--color-bg))' }} />
        <g style={{ stroke: 'rgb(var(--color-border))', strokeWidth: 1 }} aria-hidden="true">{grid}</g>
        <g>
          {ordered.map((d) => {
            const isSel = selected?.kind === 'device' && selected.d.id === d.id;
            // Device dots stay out of the tab order (2,672 of them); keyboard users use the
            // 'Highest-risk devices' table below (ACC-DES-DEF-MAP-KEYBOARD b).
            return (
              <g key={d.id} style={{ cursor: 'pointer' }} onClick={() => onSelect({ kind: 'device', d })}>
                <TierMarker tier={d.tier} x={px(d.lon as number)} y={py(d.lat as number)} selected={isSel} opacity={0.9} />
                <title>{`Device ${d.id} (${d.type}, ${d.state}) — ${TIER_LABEL[d.tier]} risk`}</title>
              </g>
            );
          })}
        </g>
        <g>
          {wcPlotted.map((w) => {
            const x = px(w.lon as number), y = py(w.lat as number);
            const isSel = selected?.kind === 'wc' && selected.w.id === w.id;
            const s = isSel ? 7 : 4.5;
            const label = `${w.name} (${w.state}) — priority #${w.priority_rank}, readiness ${w.readiness}`;
            return (
              <rect key={w.id} x={x - s} y={y - s} width={2 * s} height={2 * s} transform={`rotate(45 ${x} ${y})`}
                style={{ fill: 'rgb(var(--color-card))', stroke: 'rgb(var(--color-secondary))', strokeWidth: isSel ? 2.5 : 1.5, cursor: 'pointer' }}
                tabIndex={0} role="button" aria-label={`Wire center ${label}`} aria-pressed={isSel}
                onClick={() => onSelect({ kind: 'wc', w })}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'wc', w }); } }}>
                <title>{label}</title>
              </rect>
            );
          })}
        </g>
      </svg>
      <figcaption className="flex flex-wrap items-center justify-between gap-2 px-1 pt-2">
        <Legend />
        <span className="text-xs text-muted-foreground">{fmt(plotted.length)} of {fmt(devices.length)} devices plotted (lower 48). Click a marker, or Tab to a wire center and press Enter, for detail.</span>
      </figcaption>
    </figure>
  );
}

function DetailPanel({ sel, servingEndpoint }: { sel: Selection; servingEndpoint?: string | null }) {
  if (!sel) {
    return (
      <div className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
        <MapPin size={20} strokeWidth={1.5} className="text-muted-foreground mb-2" aria-hidden="true" />
        Select a device or wire center on the map, or a row in the priority table, to see its risk and retirement detail.
      </div>
    );
  }
  const row = (k: string, v: ReactNode) => (
    <div key={k} className="flex justify-between gap-3 border-t border-border py-1.5"><dt className="text-muted-foreground">{k}</dt><dd className="font-medium text-secondary text-right">{v}</dd></div>
  );
  if (sel.kind === 'device') {
    const d = sel.d;
    return (
      <div className="rounded-lg border border-border bg-card p-4" aria-live="polite">
        <h3 className="text-base font-semibold text-secondary flex items-center gap-2"><Radio size={16} strokeWidth={1.5} aria-hidden="true" />Device {d.id}</h3>
        <dl className="mt-2 text-sm">
          {row('Predicted risk tier', <span className="inline-flex items-center gap-1"><svg width="14" height="14" aria-hidden="true"><TierMarker tier={d.tier} x={7} y={7} scale={1.4} /></svg>{TIER_LABEL[d.tier]}</span>)}
          {row('Model confidence', d.confidence != null ? `${Math.round(d.confidence * 100)}%` : '—')}
          {row('Device type', d.type.replace(/_/g, ' '))}
          {row('Status', d.status)}
          {row('State', d.state)}
          {row('Location', d.lat != null && d.lon != null ? `${d.lat.toFixed(2)}, ${d.lon.toFixed(2)}` : '—')}
        </dl>
        <p className="text-xs text-muted-foreground mt-2">Scored by the champion risk model{servingEndpoint ? <> served on <code>{servingEndpoint}</code></> : null}.</p>
      </div>
    );
  }
  const w = sel.w;
  return (
    <div className="rounded-lg border border-border bg-card p-4" aria-live="polite">
      <h3 className="text-base font-semibold text-secondary">{w.name}</h3>
      <p className="text-xs text-muted-foreground">{w.id} · CLLI {w.clli}</p>
      <dl className="mt-2 text-sm">
        {row('Retirement priority', `#${w.priority_rank}`)}
        {row('Readiness score', `${w.readiness} / 100`)}
        {row('Copper devices', fmt(w.devices))}
        {row('Critical / high risk', `${fmt(w.critical)} / ${fmt(w.high)}`)}
        {row('Customers affected', fmt(w.customers))}
        {row('Fiber ready', w.fiber_ready ? 'Yes' : 'No')}
        {row('State PUC filing', w.puc_filing_required ? 'Required' : 'Not required')}
        {row('Regulator', w.puc_name || '—')}
      </dl>
      {w.puc_filing_required && (
        <a href="#regulatory" className="inline-block mt-2 text-xs text-primary-strong underline underline-offset-2 hover:no-underline">
          See cited {w.state} requirements in the Regulatory tab
        </a>
      )}
    </div>
  );
}

export function MapTab() {
  const [state, setState] = useState('ALL');
  const [tier, setTier] = useState('ALL');
  const [sel, setSel] = useState<Selection>(null);
  const kpis = useApi<Kpis>('/api/map/kpis');
  const states = useApi<StateRow[]>('/api/map/states');
  const devices = useApi<Device[]>(`/api/map/devices?state=${encodeURIComponent(state)}&tier=${encodeURIComponent(tier)}`);
  const wcs = useApi<WireCenter[]>(`/api/map/wire-centers?state=${encodeURIComponent(state)}`);
  const footprint = kpis.data?.footprint ?? ['CO', 'MN', 'WA', 'OR', 'ID', 'AZ'];
  const deviceStates = useMemo(() => Array.from(new Set((devices.data ?? []).map((d) => d.state))).sort(), [devices.data]);
  const [allStates, setAllStates] = useState<string[]>([]);
  useEffect(() => { if (state === 'ALL' && tier === 'ALL' && deviceStates.length) setAllStates(deviceStates); }, [state, tier, deviceStates]);
  useEffect(() => setSel(null), [state, tier]);
  const k = kpis.data;
  // ACC-DES-DEF-MAP-KEYBOARD (b): keyboard-reachable list of the highest-risk devices (critical first, then confidence).
  const topDevices = useMemo(() => [...(devices.data ?? [])]
    .sort((a, b) => TIERS.indexOf(a.tier) - TIERS.indexOf(b.tier) || (b.confidence ?? 0) - (a.confidence ?? 0))
    .slice(0, 25), [devices.data]);
  // ACC-DES-DEF-MAP-KEYBOARD (d): persistent live region announces every selection.
  const announce = sel?.kind === 'device' ? `Selected device ${sel.d.id}, ${TIER_LABEL[sel.d.tier]} risk. Details shown beside the map.`
    : sel?.kind === 'wc' ? `Selected wire center ${sel.w.name}, priority ${sel.w.priority_rank}. Details shown beside the map.` : '';
  const pick = (s: Selection) => (e: { key: string; preventDefault: () => void }) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSel(s); } };

  return (
    <section aria-labelledby="map-title">
      <TabHeader
        title="Map & Risk"
        question="Where is our copper, and which plant is most at risk?"
        badges={<SyntheticBadge label="SYNTHETIC NETWORK DATA" />}
      />

      <p className="sr-only" role="status" aria-live="polite">{announce}</p>
      {kpis.err && <EmptyState title="Could not load Map & Risk data"><p>{kpis.err}</p></EmptyState>}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 mb-4">
        <KpiCard label="Copper devices (footprint)" value={k ? fmt(k.footprint_devices) : '…'} sub={k ? `${k.footprint_states} states: ${footprint.join(', ')}` : undefined} />
        <KpiCard label="Wire centers" value={k ? fmt(k.wire_centers) : '…'} sub="scored for retirement readiness" />
        <KpiCard label="Customers affected" value={k ? fmt(k.customers_affected) : '…'} sub="on copper in the footprint" />
        <KpiCard label="Fiber ready" value={k ? `${k.fiber_ready_pct}%` : '…'} sub="of footprint copper devices" valueClass="text-success" />
        <KpiCard label="Critical + high risk" value={k ? fmt(k.footprint_critical + k.footprint_high) : '…'} sub={k ? `${fmt(k.footprint_critical)} critical in footprint` : undefined} valueClass="text-danger" />
        <KpiCard label="Devices scored by model" value={k ? fmt(k.scored_devices) : '…'} sub={k ? `${fmt(k.scored_critical)} critical · model v${k.model_version ?? '?'}` : undefined} />
      </div>

      <div className="flex flex-wrap items-end gap-3 mb-3">
        <label className="text-xs text-muted-foreground flex flex-col gap-1">
          State
          <select value={state} onChange={(e) => setState(e.target.value)} className="rounded border border-input bg-card px-2 py-1.5 text-sm text-foreground">
            <option value="ALL">All states</option>
            <optgroup label={getFootprintLabel()}>{footprint.map((s) => <option key={s} value={s}>{s}</option>)}</optgroup>
            <optgroup label="Other states">{allStates.filter((s) => !footprint.includes(s)).map((s) => <option key={s} value={s}>{s}</option>)}</optgroup>
          </select>
        </label>
        <label className="text-xs text-muted-foreground flex flex-col gap-1">
          Risk tier
          <select value={tier} onChange={(e) => setTier(e.target.value)} className="rounded border border-input bg-card px-2 py-1.5 text-sm text-foreground">
            <option value="ALL">All tiers</option>
            {TIERS.map((t) => <option key={t} value={t}>{TIER_LABEL[t]}</option>)}
          </select>
        </label>
        <span className="text-xs text-muted-foreground pb-2">
          {devices.data ? `${fmt(devices.data.length)} devices` : 'Loading devices…'} · {wcs.data ? `${fmt(wcs.data.length)} wire centers` : 'Loading wire centers…'}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-4">
        <div className="lg:col-span-2">
          {devices.err || wcs.err ? (
            <EmptyState title="Could not load the risk map"><p>{devices.err || wcs.err}</p></EmptyState>
          ) : devices.data && wcs.data ? (
            <RiskMap devices={devices.data} wcs={wcs.data} selected={sel} onSelect={setSel} />
          ) : (
            <div className="rounded-lg border border-border bg-card p-8 text-sm text-muted-foreground">Loading risk map…</div>
          )}
        </div>
        <DetailPanel sel={sel} servingEndpoint={k?.serving_endpoint} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full text-sm">
            <caption className="text-left p-3 text-sm font-semibold text-secondary">Wire centers by retirement priority</caption>
            <thead className="bg-muted text-left text-xs text-muted-foreground">
              <tr><th scope="col" className="p-2">Rank</th><th scope="col" className="p-2">Wire center</th><th scope="col" className="p-2">State</th><th scope="col" className="p-2 text-right">Readiness</th><th scope="col" className="p-2 text-right">Devices</th><th scope="col" className="p-2 text-right">Crit/High</th><th scope="col" className="p-2">Fiber</th></tr>
            </thead>
            <tbody>
              {(wcs.data ?? []).slice(0, 25).map((w) => {
                const isSel = sel?.kind === 'wc' && sel.w.id === w.id;
                return (
                <tr key={w.id} className={`border-t border-border cursor-pointer hover:bg-muted ${isSel ? 'bg-muted font-semibold' : ''}`}
                  aria-current={isSel ? 'true' : undefined}
                  onClick={() => setSel({ kind: 'wc', w })} tabIndex={0} onKeyDown={pick({ kind: 'wc', w })}>
                  <td className="p-2">#{w.priority_rank}</td>
                  <td className="p-2 font-medium text-secondary">{w.name}</td>
                  <td className="p-2">{w.state}</td>
                  <td className="p-2 text-right">{w.readiness}</td>
                  <td className="p-2 text-right">{fmt(w.devices)}</td>
                  <td className="p-2 text-right">{w.critical}/{w.high}</td>
                  <td className="p-2">{w.fiber_ready ? <span className="text-success">Ready</span> : <span className="text-muted-foreground">Not yet</span>}</td>
                </tr>
                );
              })}
            </tbody>
          </table>
          {wcs.data && wcs.data.length > 25 && <p className="text-xs text-muted-foreground p-2">Top 25 of {wcs.data.length}. Full sequencing is in the Plan tab.</p>}
          {wcs.data && !wcs.data.length && <p className="text-xs text-muted-foreground p-3">No wire centers in this state (outside the {getFootprintLabel().toLowerCase()}).</p>}
        </div>

        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full text-sm">
            <caption className="text-left p-3 text-sm font-semibold text-secondary">Footprint state scorecard</caption>
            <thead className="bg-muted text-left text-xs text-muted-foreground">
              <tr><th scope="col" className="p-2">State</th><th scope="col" className="p-2 text-right">Devices</th><th scope="col" className="p-2 text-right">Critical</th><th scope="col" className="p-2 text-right">High</th><th scope="col" className="p-2 text-right">Fiber ready</th><th scope="col" className="p-2 text-right">Customers</th><th scope="col" className="p-2 text-right">Dig incidents</th><th scope="col" className="p-2">Health</th></tr>
            </thead>
            <tbody>
              {(states.data ?? []).map((s) => (
                <tr key={s.state} className="border-t border-border">
                  <td className="p-2 font-medium text-secondary">{s.state}</td>
                  <td className="p-2 text-right">{fmt(s.devices)}</td>
                  <td className="p-2 text-right text-danger">{fmt(s.critical)}</td>
                  <td className="p-2 text-right">{fmt(s.high)}</td>
                  <td className="p-2 text-right">{s.fiber_ready_pct}%</td>
                  <td className="p-2 text-right">{fmt(s.customers)}</td>
                  <td className="p-2 text-right">{fmt(s.dig_incidents)}</td>
                  <td className="p-2 capitalize">{s.health === 'green' ? <span className="text-success">On track</span> : s.health === 'red' ? <span className="text-danger">At risk</span> : <span className="text-warning">Watch</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {states.err && <p className="text-xs text-danger p-3">{states.err}</p>}
        </div>

        <div className="overflow-x-auto rounded-lg border border-border bg-card xl:col-span-2">
          <table className="w-full text-sm">
            <caption className="text-left p-3 text-sm font-semibold text-secondary">Highest-risk devices (top 25, critical first) — press Enter on a row for detail</caption>
            <thead className="bg-muted text-left text-xs text-muted-foreground">
              <tr><th scope="col" className="p-2">Device</th><th scope="col" className="p-2">Risk tier</th><th scope="col" className="p-2 text-right">Confidence</th><th scope="col" className="p-2">Type</th><th scope="col" className="p-2">State</th><th scope="col" className="p-2">Status</th></tr>
            </thead>
            <tbody>
              {topDevices.map((d) => {
                const isSel = sel?.kind === 'device' && sel.d.id === d.id;
                return (
                  <tr key={d.id} className={`border-t border-border cursor-pointer hover:bg-muted ${isSel ? 'bg-muted font-semibold' : ''}`}
                    aria-current={isSel ? 'true' : undefined}
                    onClick={() => setSel({ kind: 'device', d })} tabIndex={0} onKeyDown={pick({ kind: 'device', d })}>
                    <td className="p-2 font-medium text-secondary">{d.id}</td>
                    <td className="p-2"><span className="inline-flex items-center gap-1"><svg width="14" height="14" aria-hidden="true"><TierMarker tier={d.tier} x={7} y={7} scale={1.4} /></svg>{TIER_LABEL[d.tier]}</span></td>
                    <td className="p-2 text-right">{d.confidence != null ? `${Math.round(d.confidence * 100)}%` : '—'}</td>
                    <td className="p-2">{d.type.replace(/_/g, ' ')}</td>
                    <td className="p-2">{d.state}</td>
                    <td className="p-2">{d.status}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {devices.data && !devices.data.length && <p className="text-xs text-muted-foreground p-3">No devices match these filters.</p>}
        </div>
      </div>

      <p className="text-xs text-muted-foreground mt-3">
        Network, device and customer records are synthetic demo data (tables labeled SYNTHETIC in Unity Catalog). Device risk tiers are predictions from the
        registered champion model; wire-center readiness comes from <code>gold_wire_center_scorecard</code>.
      </p>
    </section>
  );
}
