"""Copper Prioritization Map (P7-MAP)
Lakelink Fiber — Copper Retirement Program
Demo Beat 1: "Where is our copper / risk of touching it?"

Python/Dash implementation with LIVE DATA from cdm_tmforum catalog.
Set LIVE_DATA=true to query real tables via SQL warehouse.
Fallback to mock data if SQL warehouse unavailable.
All underlying data is SYNTHETIC (generated for demo).

@app-developer 2026-09-12 — UPGRADE-COPPER-MAP-LIVE-DATA
Bugs fixed:
  - ga.city → ga.locality (column name mismatch)
  - customer.geographic_address_id doesn't exist → join via CFS
  - h3_res9 was 100% NULL → now using pre-populated h3_res8 via h3_toparent()
@app-developer 2026-09-13 — P7-MAP-LIVE-DATA-PREP
  - Switched to pre-populated h3_res8 columns (no more on-the-fly H3)
  - Fixed KPI key mismatch (copper_devices, critical_risk_pct aliases)
  - Added h3_h3tostring() for readable hex cell IDs
@app-developer 2026-09-14 — P7-MAP-GOLD-INTEGRATION
@app-developer 2026-09-15 — P7-DEMO-BEAT1-POLISH
  - Loading states: dcc.Loading wrappers on map, device table, Genie chat
  - Error boundaries: try/except in update_views callback with error figures
  - Data-empty guards: empty_state_card + build_empty_figure for zero-row states
  - Transition animations: CSS transitions on cards, uirevision on map
  - Gold tables now primary data source (wire_center_scorecard + executive_summary)
  - Map plots wire centers with retirement readiness scoring
  - New Wire Center Scorecard table with priority rank, readiness, fiber status
  - State-level Executive Summary table with program health
  - Richer KPIs: fiber readiness, wire centers, contractor capacity
  - Falls back to base-table queries if gold tables unavailable
"""
import os
import logging
import dash
from dash import html, dcc, dash_table, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
APP_PORT = int(os.environ.get("DATABRICKS_APP_PORT", 8000))
LIVE_DATA = os.environ.get("LIVE_DATA", "true").lower() in ("true", "1", "yes")

# ── Live data loading ───────────────────────────────────────────────────────────
_live_ok = False
if LIVE_DATA:
    try:
        from data import (
            load_hex_cells, load_kpis, load_devices, load_filter_options,
            load_gold_wire_centers, load_gold_kpis, load_gold_executive_summary,
        )
        _live_ok = True
        logger.info("[copper-map] Live data module loaded. Querying cdm_tmforum.")
    except Exception as e:
        logger.warning(f"[copper-map] Live data unavailable ({e}). Using mock data.")

# ── Mock Data (fallback when LIVE_DATA=false or SQL unavailable) ─────────────
LL_PRIMARY = "#FF3621"
LL_SECONDARY = "#1B3139"
LL_ACCENT = "#00A972"
LL_SURFACE = "#F9F7F4"
LL_SURFACE_ELEVATED = "#FFFFFF"
LL_SURFACE_DARK = "#1B3139"
LL_TEXT_PRIMARY = "#1B3139"
LL_TEXT_SECONDARY = "#6E8898"
LL_TEXT_INVERSE = "#FFFFFF"
LL_BORDER = "#E5E2DD"

RISK_COLORS = {"critical": LL_PRIMARY, "high": "#FF8C69", "medium": "#6E8898", "low": LL_ACCENT}

# ── CSS Transitions & Animation Constants ──────────────────────────────────────
CARD_TRANSITION = "box-shadow 0.25s ease, transform 0.2s ease"
CARD_STYLE_BASE = {
    "backgroundColor": LL_SURFACE_ELEVATED,
    "border": f"1px solid {LL_BORDER}",
    "borderRadius": "8px",
    "transition": CARD_TRANSITION,
}
LOADING_COLOR = LL_PRIMARY
LOADING_TYPE = "dot"  # dash loading spinner style

# ── Genie Agent Configuration ────────────────────────────────────────────────
GENIE_SPACE_ID = "01f1b0917b9b15a3a21cfa9d20cbba50"
GENIE_SUGGESTED = [
    "Show me high-risk devices in Oregon",
    "What is our EBITDA impact?",
    "Which states need immediate attention?",
    "How many customers are affected in Colorado?",
]

HEX_CELLS = [
    # Colorado — mountain west aging copper clusters
    {"h3": "892a100d2c3ffff", "lat": 39.74, "lon": -104.99, "devices": 487, "risk": 78, "tier": "critical", "alarms": 4210, "crit": 1580, "state": "CO"},
    {"h3": "892a100d2c7ffff", "lat": 38.83, "lon": -104.82, "devices": 312, "risk": 65, "tier": "high",     "alarms": 2890, "crit": 890,  "state": "CO"},
    # Minnesota — older metro and suburban plant
    {"h3": "892a100d2cbffff", "lat": 44.98, "lon": -93.27,  "devices": 198, "risk": 52, "tier": "high",     "alarms": 1650, "crit": 420,  "state": "MN"},
    {"h3": "892a100d2cfffff", "lat": 46.79, "lon": -92.10,  "devices": 423, "risk": 71, "tier": "high",     "alarms": 3560, "crit": 1120, "state": "MN"},
    # Washington — dense legacy footprint in wet climate
    {"h3": "892a100d2d3ffff", "lat": 47.61, "lon": -122.33, "devices": 278, "risk": 58, "tier": "high",     "alarms": 2340, "crit": 650,  "state": "WA"},
    {"h3": "892a100d2d7ffff", "lat": 47.66, "lon": -117.43, "devices": 156, "risk": 42, "tier": "medium",   "alarms": 1120, "crit": 280,  "state": "WA"},
    # Oregon — moisture and storm exposure
    {"h3": "892a100d2dbffff", "lat": 45.52, "lon": -122.68, "devices": 356, "risk": 82, "tier": "critical", "alarms": 3890, "crit": 1890, "state": "OR"},
    {"h3": "892a100d2dfffff", "lat": 44.94, "lon": -123.03, "devices": 189, "risk": 73, "tier": "high",     "alarms": 2010, "crit": 780,  "state": "OR"},
    # Idaho — long-haul rural plant
    {"h3": "892a100d2e3ffff", "lat": 43.62, "lon": -116.20, "devices": 401, "risk": 88, "tier": "critical", "alarms": 4560, "crit": 2100, "state": "ID"},
    {"h3": "892a100d2e7ffff", "lat": 47.68, "lon": -116.78, "devices": 134, "risk": 45, "tier": "medium",   "alarms": 980,  "crit": 210,  "state": "ID"},
    # Arizona — heat-stressed legacy copper zones
    {"h3": "892a100d2ebffff", "lat": 33.45, "lon": -112.07, "devices": 267, "risk": 62, "tier": "high",     "alarms": 2230, "crit": 670,  "state": "AZ"},
    {"h3": "892a100d2efffff", "lat": 32.22, "lon": -110.97, "devices": 178, "risk": 55, "tier": "high",     "alarms": 1540, "crit": 410,  "state": "AZ"},
]

DEVICES = [
    {"id": 1001, "type": "CPE",         "serial": "CPE-DEN-001", "status": "active",   "installed": "2008-03-15", "state": "CO", "city": "Denver",           "alarms": 12, "crit": 4, "risk": 92},
    {"id": 1002, "type": "ONT",         "serial": "ONT-COS-002", "status": "active",   "installed": "2011-07-22", "state": "CO", "city": "Colorado Springs", "alarms": 8,  "crit": 2, "risk": 78},
    {"id": 1003, "type": "CPE",         "serial": "CPE-MSP-001", "status": "degraded", "installed": "2005-11-01", "state": "MN", "city": "Minneapolis",      "alarms": 18, "crit": 7, "risk": 95},
    {"id": 1004, "type": "OLT",         "serial": "OLT-SEA-001", "status": "active",   "installed": "2013-02-10", "state": "WA", "city": "Seattle",          "alarms": 6,  "crit": 1, "risk": 55},
    {"id": 1005, "type": "Patch Panel", "serial": "PP-PDX-001",  "status": "active",   "installed": "2009-09-30", "state": "OR", "city": "Portland",         "alarms": 14, "crit": 5, "risk": 82},
    {"id": 1006, "type": "CPE",         "serial": "CPE-BOI-001", "status": "active",   "installed": "2010-06-14", "state": "ID", "city": "Boise",            "alarms": 9,  "crit": 3, "risk": 68},
    {"id": 1007, "type": "ONT",         "serial": "ONT-PHX-001", "status": "active",   "installed": "2012-01-20", "state": "AZ", "city": "Phoenix",          "alarms": 11, "crit": 4, "risk": 74},
    {"id": 1008, "type": "OLT",         "serial": "OLT-TUS-001", "status": "degraded", "installed": "2007-08-05", "state": "AZ", "city": "Tucson",           "alarms": 16, "crit": 6, "risk": 88},
]

KPIS = {
    "devices": 2672, "cpe": 688, "ont": 663, "olt": 661, "pp": 660,
    "alarms": 26943, "crit_alarms": 9978, "pct_crit": 37.3,
    "states": 6, "wire_centers": 200,
    # Converged KPIs (matches SummaryKPIs.tsx)
    "copper_devices": 975,
    "critical_risk_pct": 58.3,
    "revenue_at_risk_mrr": 297600,
    "services_affected": 2626,
}

# ── Bootstrap initial data (gold tables > base tables > mock) ────────────────
_gold_ok = False
GOLD_WIRE_CENTERS = []
GOLD_EXEC_SUMMARY = []

if _live_ok:
    # Try gold tables first (preferred)
    try:
        logger.info("[copper-map] Trying gold tables (primary source)...")
        GOLD_WIRE_CENTERS = load_gold_wire_centers()
        KPIS = load_gold_kpis()
        GOLD_EXEC_SUMMARY = load_gold_executive_summary()
        HEX_CELLS = GOLD_WIRE_CENTERS  # wire centers as map points
        DEVICES = load_devices()  # device detail still from base tables
        _filter_opts = load_filter_options()
        KPIS.setdefault("wire_centers", len(GOLD_WIRE_CENTERS))
        _gold_ok = True
        DATA_SOURCE = "LIVE (GOLD)"
        logger.info(f"[copper-map] Gold data loaded: {len(GOLD_WIRE_CENTERS)} wire centers, "
                    f"{len(GOLD_EXEC_SUMMARY)} state summaries, {len(DEVICES)} devices.")
    except Exception as e:
        logger.warning(f"[copper-map] Gold tables unavailable ({e}). Trying base tables...")
        _gold_ok = False

    # Fallback to base tables if gold failed
    if not _gold_ok:
        try:
            logger.info("[copper-map] Loading from base tables (fallback)...")
            HEX_CELLS = load_hex_cells()
            KPIS = load_kpis()
            DEVICES = load_devices()
            _filter_opts = load_filter_options()
            KPIS.setdefault("wire_centers", "TBD")
            DATA_SOURCE = "LIVE"
            logger.info(f"[copper-map] Loaded {len(HEX_CELLS)} hex cells, "
                        f"{len(DEVICES)} devices from base tables.")
        except Exception as e:
            logger.warning(f"[copper-map] Base table query failed ({e}). Falling back to mock.")
            _live_ok = False
            DATA_SOURCE = "MOCK"

if not _live_ok:
    DATA_SOURCE = "MOCK"
    _filter_opts = None
    logger.info("[copper-map] Using mock data.")

if _filter_opts:
    STATES = sorted(_filter_opts.get("state", []))
    DEVICE_TYPES = sorted(_filter_opts.get("device_type", []))
else:
    STATES = sorted(set(c["state"] for c in HEX_CELLS))
    DEVICE_TYPES = sorted(set(d["type"] for d in DEVICES))

TIERS = ["critical", "high", "medium", "low"]

# ── Helpers ────────────────────────────────────────────────────────────────────

def lakelink_header(subtitle, tagline=None, data_source="MOCK", show_synthetic=True):
    """Shared Lakelink Fiber nav header (BRAND_GUIDE §6 Nav Header).
    Equivalent to LakeLinkHeader.tsx for Dash apps.
    """
    badge_color = LL_ACCENT if data_source == "LIVE" else RISK_COLORS["medium"]
    badge_text = f"{data_source} DATA"
    if show_synthetic:
        badge_text += " \u00B7 SYNTHETIC"
    left = [
        html.P("Lakelink Fiber", className="mb-0",
               style={"fontSize": "1rem", "fontWeight": 600, "color": LL_SECONDARY,
                      "lineHeight": 1.2}),
        html.H3(subtitle, className="mb-0 mt-1",
                style={"fontWeight": 700, "color": LL_TEXT_PRIMARY}),
    ]
    if tagline:
        left.append(html.P(tagline, className="mb-0",
                           style={"fontSize": "0.8125rem", "color": LL_TEXT_SECONDARY}))
    return dbc.Row([
        dbc.Col(left, width="auto"),
        dbc.Col([
            dbc.Badge(
                badge_text,
                style={"fontSize": "0.6875rem", "backgroundColor": f"{badge_color}33",
                       "color": LL_SECONDARY, "border": f"1px solid {LL_BORDER}",
                       "padding": "4px 10px", "fontWeight": 500},
            ),
        ], width="auto", className="d-flex align-items-center"),
    ], justify="between", style={"background": LL_SURFACE, "borderBottom": f"1px solid {LL_BORDER}",
                                  "padding": "16px 24px 16px"})


def kpi_card(label, value, color=LL_TEXT_PRIMARY, sub=None):
    children = [
        html.P(label, className="mb-0",
               style={"fontSize": "0.75rem", "color": LL_TEXT_SECONDARY,
                      "textTransform": "uppercase", "letterSpacing": "0.05em"}),
        html.H4(value, className="mb-0 mt-1",
                style={"color": color, "fontWeight": 700}),
    ]
    if sub:
        children.append(
            html.P(sub, className="mb-0",
                   style={"fontSize": "0.7rem", "color": LL_TEXT_SECONDARY})
        )
    return dbc.Card(
        dbc.CardBody(children),
        style={**CARD_STYLE_BASE},
    )


def build_empty_figure(message="No data available", sub="Adjust filters or check data connection"):
    """Return a Scattergeo figure with a centered empty-state message."""
    fig = go.Figure(go.Scattergeo())
    fig.update_layout(
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", landcolor=LL_SURFACE,
                 subunitcolor=LL_BORDER, showsubunits=True, resolution=50),
        paper_bgcolor=LL_SURFACE, plot_bgcolor=LL_SURFACE,
        margin=dict(l=0, r=0, t=0, b=0), height=500,
        annotations=[dict(
            text=f"<b>{message}</b><br><span style='font-size:12px;color:{LL_TEXT_SECONDARY}'>{sub}</span>",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color=LL_TEXT_SECONDARY),
            align="center",
        )],
    )
    return fig


def build_error_figure(error_msg="Something went wrong"):
    """Return a Scattergeo figure showing an error state."""
    fig = go.Figure(go.Scattergeo())
    fig.update_layout(
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", landcolor=LL_SURFACE,
                 subunitcolor=LL_BORDER, showsubunits=True, resolution=50),
        paper_bgcolor=LL_SURFACE, plot_bgcolor=LL_SURFACE,
        margin=dict(l=0, r=0, t=0, b=0), height=500,
        annotations=[dict(
            text=f"<b>\u26A0 Error loading map</b><br><span style='font-size:11px;color:{LL_TEXT_SECONDARY}'>{error_msg[:120]}</span>",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=15, color=LL_PRIMARY),
            align="center",
        )],
    )
    return fig


def empty_state_card(message, icon="\U0001F4CB"):
    """Inline empty-state placeholder for tables/sections."""
    return html.Div([
        html.Div(icon, style={"fontSize": "2rem", "marginBottom": "8px"}),
        html.P(message, style={
            "fontSize": "0.85rem", "color": LL_TEXT_SECONDARY, "margin": 0}),
    ], style={
        "textAlign": "center", "padding": "48px 24px",
        "backgroundColor": LL_SURFACE, "borderRadius": "6px",
    })


def build_map(cells):
    """Build a plotly Scattergeo figure from hex cell data."""
    if not cells:
        return build_empty_figure(
            "No copper locations found",
            "Select different filters or verify data connectivity",
        )
    fig = go.Figure()
    for tier in TIERS:
        tier_cells = [c for c in cells if c["tier"] == tier]
        if not tier_cells:
            continue
        fig.add_trace(go.Scattergeo(
            lat=[c["lat"] for c in tier_cells],
            lon=[c["lon"] for c in tier_cells],
            text=[
                (f"<b>{c.get('wire_center', c['state'])}</b> ({c['state']})<br>"
                 f"{c['devices']} devices<br>"
                 f"Readiness: {c.get('readiness', 'N/A')}<br>"
                 f"Risk score: {c['risk']}<br>"
                 f"Services: {c.get('services', 0):,} | Customers: {c.get('customers', 0):,}<br>"
                 f"Rank: #{c.get('priority_rank', 'N/A')}")
                if _gold_ok else
                (f"<b>{c['state']}</b><br>"
                 f"{c['devices']} devices<br>"
                 f"Risk score: {c['risk']}<br>"
                 f"Alarms: {c['alarms']:,} ({c['crit']:,} critical)")
                for c in tier_cells
            ],
            hoverinfo="text",
            marker=dict(
                size=[max(10, c["devices"] / 12) for c in tier_cells],
                color=RISK_COLORS[tier],
                opacity=0.85,
                line=dict(width=1, color=LL_SURFACE),
                sizemode="diameter",
            ),
            name=tier.capitalize(),
        ))
    fig.update_layout(
        geo=dict(
            scope="usa",
            bgcolor="rgba(0,0,0,0)",
            lakecolor=LL_SECONDARY,
            landcolor=LL_SURFACE_DARK,
            subunitcolor=LL_BORDER,
            countrycolor=LL_TEXT_SECONDARY,
            showlakes=True,
            showsubunits=True,
            resolution=50,
        ),
        paper_bgcolor=LL_SURFACE,
        plot_bgcolor=LL_SURFACE,
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        uirevision="copper-map",  # preserve zoom/pan across filter changes
        transition=dict(duration=400, easing="cubic-in-out"),
        legend=dict(
            font=dict(color=LL_TEXT_SECONDARY, size=12),
            bgcolor="rgba(0,0,0,0)",
            x=0.01, y=0.99,
        ),
        hoverlabel=dict(
            bgcolor=LL_SURFACE_DARK, font_size=13, font_color=LL_TEXT_INVERSE,
            bordercolor=LL_BORDER,
        ),
    )
    return fig


def filter_cells(state_val, tier_val):
    """Filter map cells. Gold mode uses wire centers; base mode uses H3 hex cells."""
    if _gold_ok and state_val:
        try:
            cells = load_gold_wire_centers(state_filter=state_val)
        except Exception:
            cells = HEX_CELLS
    elif _live_ok and state_val and not _gold_ok:
        try:
            cells = load_hex_cells(state_filter=state_val)
        except Exception:
            cells = HEX_CELLS
    else:
        cells = HEX_CELLS
    if state_val and not _live_ok:
        cells = [c for c in cells if c.get("state") == state_val]
    if tier_val:
        cells = [c for c in cells if c.get("tier") == tier_val]
    return cells


def filter_devices(state_val, type_val):
    """Filter devices. In LIVE mode, re-queries with filters."""
    if _live_ok and (state_val or type_val):
        try:
            return load_devices(
                state_filter=state_val or "",
                device_type=type_val or "",
            )
        except Exception:
            pass
    devs = DEVICES
    if state_val:
        devs = [d for d in devs if d.get("state") == state_val]
    if type_val:
        devs = [d for d in devs if d.get("type") == type_val]
    return devs


# ── Genie API Helper ──────────────────────────────────────────────────────────

def query_genie(question, conversation_id=None):
    """Query the Genie Conversation API for copper retirement analytics."""
    import time as _t
    try:
        from databricks.sdk import WorkspaceClient
        gc = WorkspaceClient()
        if conversation_id:
            resp = gc.genie.create_message(
                space_id=GENIE_SPACE_ID,
                conversation_id=conversation_id,
                content=question,
            )
            conv_id = conversation_id
            msg_id = resp.message_id
        else:
            resp = gc.genie.start_conversation(
                space_id=GENIE_SPACE_ID,
                content=question,
            )
            conv_id = resp.conversation_id
            msg_id = resp.message_id

        # Poll for completion (max 90s)
        answer = sql = None
        for _ in range(45):
            _t.sleep(2)
            msg = gc.genie.get_message(GENIE_SPACE_ID, conv_id, msg_id)
            s = str(getattr(msg, 'status', ''))
            if 'COMPLETED' in s:
                if msg.attachments:
                    for att in msg.attachments:
                        if hasattr(att, 'text') and att.text:
                            answer = att.text.content if hasattr(att.text, 'content') else str(att.text)
                        if hasattr(att, 'query') and att.query:
                            sql = att.query.query if hasattr(att.query, 'query') else None
                if not answer and hasattr(msg, 'content'):
                    answer = msg.content
                break
            if 'FAILED' in s or 'CANCELLED' in s:
                return {"error": f"Query {s.lower()}", "conv_id": conv_id}

        # Try to get tabular results
        table_md = ""
        if sql:
            try:
                qr = gc.genie.get_message_query_result(GENIE_SPACE_ID, conv_id, msg_id)
                sr = qr.statement_response
                if sr and sr.result and sr.result.data_array:
                    cols = [c.name for c in sr.result.schema.columns] if sr.result.schema else []
                    rows = sr.result.data_array[:8]
                    if cols and rows:
                        table_md = "\n\n" + " | ".join(cols)
                        for r in rows:
                            table_md += "\n" + " | ".join(str(v or "") for v in r)
            except Exception:
                pass

        return {"answer": (answer or "Analysis complete.") + table_md, "sql": sql, "conv_id": conv_id}
    except Exception as e:
        logger.error(f"[genie] Error: {e}")
        return {"error": str(e), "conv_id": None}


# ── Layout ─────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Copper Map — Lakelink Fiber",
)

app.layout = dbc.Container([
    # ── Genie conversation state ──
    dcc.Store(id="genie-store", data={"conv_id": None, "history": []}),

    # ── Header (shared lakelink_header) ──
    lakelink_header(
        subtitle="Copper Prioritization Map",
        tagline="Copper Retirement Program",
        data_source=DATA_SOURCE,
    ),

    # ── KPI Row (6 metrics when gold data available) ──
    dbc.Row([
        dbc.Col(kpi_card(
            "Copper Devices", f"{KPIS['copper_devices']:,}",
            sub=f"{KPIS.get('wire_centers', 'TBD')} wire centers",
        )),
        dbc.Col(kpi_card(
            "Critical Risk", f"{KPIS['critical_risk_pct']}%",
            color=LL_PRIMARY if KPIS['critical_risk_pct'] >= 40 else LL_TEXT_PRIMARY,
            sub=f"{KPIS.get('critical_risk_devices', KPIS.get('crit_alarms', 0)):,} devices",
        )),
        dbc.Col(kpi_card(
            "Revenue at Risk",
            f"${KPIS['revenue_at_risk_mrr'] // 1000:,}K",
            color=LL_PRIMARY,
            sub=f"${KPIS['revenue_at_risk_mrr'] * 12 / 1_000_000:.1f}M annualized",
        )),
        dbc.Col(kpi_card(
            "Fiber Ready",
            f"{KPIS.get('fiber_ready_pct', 0):.0f}%" if _gold_ok else "N/A",
            color=LL_ACCENT if KPIS.get('fiber_ready_pct', 0) >= 50 else LL_TEXT_PRIMARY,
            sub=f"{KPIS.get('fiber_ready_devices', 0):,} devices" if _gold_ok else "Requires gold data",
        )),
        dbc.Col(kpi_card(
            "States", str(KPIS["states"]),
            sub="With copper plant",
        )),
        dbc.Col(kpi_card(
            "Services Affected", f"{KPIS['services_affected']:,}",
            sub=f"{KPIS.get('customers_on_copper', 0):,} customers",
        )),
    ], className="mb-3 g-2"),

    # ── Filters + Map ──
    dbc.Row([
        # Sidebar
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H6("Filters", className="mb-3",
                        style={"color": LL_TEXT_SECONDARY, "textTransform": "uppercase",
                               "fontSize": "0.75rem", "letterSpacing": "0.05em"}),
                html.Label("State", style={"fontSize": "0.8rem", "color": LL_TEXT_SECONDARY}),
                dcc.Dropdown(
                    id="filter-state",
                    options=[{"label": s, "value": s} for s in STATES],
                    placeholder="All states", clearable=True,
                ),
                html.Label("Risk Tier", className="mt-2",
                           style={"fontSize": "0.8rem", "color": LL_TEXT_SECONDARY}),
                dcc.Dropdown(
                    id="filter-tier",
                    options=[{"label": t.capitalize(), "value": t} for t in TIERS],
                    placeholder="All tiers", clearable=True,
                ),
                html.Label("Device Type", className="mt-2",
                           style={"fontSize": "0.8rem", "color": LL_TEXT_SECONDARY}),
                dcc.Dropdown(
                    id="filter-dtype",
                    options=[{"label": t, "value": t} for t in DEVICE_TYPES],
                    placeholder="All types", clearable=True,
                ),
                html.Hr(style={"borderColor": LL_BORDER}),
                html.H6("Risk Legend", className="mb-2",
                        style={"color": LL_TEXT_SECONDARY, "textTransform": "uppercase",
                               "fontSize": "0.75rem", "letterSpacing": "0.05em"}),
                *[
                    html.Div([
                        html.Span("", style={
                            "display": "inline-block", "width": 12, "height": 12,
                            "borderRadius": "50%", "backgroundColor": RISK_COLORS[t],
                            "marginRight": 8,
                        }),
                        html.Span(f"{t.capitalize()} (≥{th})",
                                  style={"fontSize": "0.8rem", "color": LL_TEXT_PRIMARY}),
                    ], className="mb-1")
                    for t, th in [("critical", 75), ("high", 50), ("medium", 25), ("low", 0)]
                ],
                html.Hr(style={"borderColor": LL_BORDER}),
                html.P("Bubble size = device count",
                       style={"fontSize": "0.7rem", "color": LL_TEXT_SECONDARY, "marginBottom": 4}),
                html.P("Hover for details",
                       style={"fontSize": "0.7rem", "color": LL_TEXT_SECONDARY, "marginBottom": 0}),
            ]), style={"backgroundColor": LL_SURFACE_ELEVATED, "border": f"1px solid {LL_BORDER}",
                      "borderRadius": "8px"}),
        ], md=3),

        # Map (with loading overlay)
        dbc.Col([
            dbc.Card(
                dcc.Loading(
                    dcc.Graph(id="map-graph", figure=build_map(HEX_CELLS),
                              config={"displayModeBar": False},
                              style={"transition": "opacity 0.3s ease"}),
                    type=LOADING_TYPE, color=LOADING_COLOR,
                    style={"minHeight": "500px"},
                ),
                style={**CARD_STYLE_BASE, "overflow": "hidden"},
            ),
        ], md=9),
    ], className="mb-3"),

    # ── Genie Q&A (Copper Analytics Agent) ─────────────────────────────────
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("\u25CF", style={"color": LL_ACCENT, "marginRight": "8px",
                                                    "fontSize": "0.7rem"}),
                        html.Span("Copper Analytics Agent", style={
                            "fontWeight": 600, "color": LL_TEXT_PRIMARY, "fontSize": "0.85rem"}),
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.P("Ask about copper inventory, risk, revenue impact, and retirement scenarios",
                           className="mb-0 mt-1",
                           style={"fontSize": "0.75rem", "color": LL_TEXT_SECONDARY}),
                ]),
                dbc.Col(
                    dbc.Badge("Genie-powered", style={
                        "fontSize": "0.65rem", "backgroundColor": f"{LL_ACCENT}22",
                        "color": LL_ACCENT, "border": f"1px solid {LL_BORDER}",
                        "padding": "3px 8px"}),
                    width="auto", className="d-flex align-items-center",
                ),
            ], justify="between", align="center"),
            style={"backgroundColor": LL_SURFACE, "borderBottom": f"1px solid {LL_BORDER}"},
        ),
        dbc.CardBody([
            # Messages area
            dcc.Loading(
                html.Div(id="genie-messages", children=[
                    html.Div(
                        html.Div([
                            html.Span("\U0001F50D ", style={"fontSize": "0.75rem"}),
                            html.Span(
                                "I can help you analyze copper retirement impact. "
                                "Ask about device risk, customer counts, revenue at risk, "
                                "or retirement readiness for any state or wire center."
                            ),
                        ], style={
                            "display": "inline-block",
                            "backgroundColor": f"{LL_SECONDARY}0F",
                            "padding": "10px 14px", "borderRadius": "14px 14px 14px 2px",
                            "fontSize": "0.85rem", "maxWidth": "85%", "color": LL_TEXT_PRIMARY,
                        }),
                        style={"textAlign": "left", "marginBottom": "8px"},
                    ),
                ], style={
                    "maxHeight": "360px", "overflowY": "auto", "marginBottom": "12px",
                    "padding": "12px", "backgroundColor": LL_SURFACE,
                    "borderRadius": "6px", "minHeight": "80px",
                }),
                type="dot", color=LL_PRIMARY,
            ),
            # Suggested questions
            html.Div([
                dbc.Button(q, size="sm", outline=True, color="secondary",
                           className="me-1 mb-1",
                           style={"fontSize": "0.7rem", "borderRadius": "16px"},
                           id=f"genie-chip-{i}")
                for i, q in enumerate(GENIE_SUGGESTED)
            ], id="genie-chips", className="mb-2"),
            # Input row
            dbc.InputGroup([
                dbc.Input(id="genie-input", placeholder="Ask about copper retirement...",
                          type="text", style={"fontSize": "0.85rem"}, debounce=True),
                dbc.Button("Ask", id="genie-submit", n_clicks=0,
                           style={"backgroundColor": LL_PRIMARY, "border": "none",
                                  "fontWeight": 600, "color": "#FFFFFF"}),
            ]),
        ]),
    ], style={**CARD_STYLE_BASE}, className="mb-4"),

    # ── Device Table (with loading + empty guard) ──
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H6("Device Detail", className="mb-0",
                        style={"color": LL_TEXT_SECONDARY, "fontSize": "0.85rem"})),
                dbc.Col(dbc.Badge(
                    f"{len(DEVICES)} devices" if DEVICES else "No devices",
                    style={"fontSize": "0.65rem", "backgroundColor": f"{LL_ACCENT}22",
                           "color": LL_ACCENT if DEVICES else LL_TEXT_SECONDARY,
                           "border": f"1px solid {LL_BORDER}", "padding": "3px 8px"},
                ), width="auto"),
            ], justify="between", align="center"),
            style={"backgroundColor": LL_SURFACE, "borderBottom": f"1px solid {LL_BORDER}"},
        ),
        dbc.CardBody(
          dcc.Loading(
            html.Div(id="device-table-container", children=[
              dash_table.DataTable(
                id="device-table",
                columns=[
                    {"name": "ID", "id": "id"},
                    {"name": "Type", "id": "type"},
                    {"name": "Serial", "id": "serial"},
                    {"name": "Status", "id": "status"},
                    {"name": "Installed", "id": "installed"},
                    {"name": "State", "id": "state"},
                    {"name": "City", "id": "city"},
                    {"name": "Alarms", "id": "alarms"},
                    {"name": "Critical", "id": "crit"},
                    {"name": "Risk Score", "id": "risk"},
                ],
                data=DEVICES,
                style_header={
                    "backgroundColor": LL_SURFACE, "color": LL_TEXT_SECONDARY,
                    "fontWeight": 600, "borderBottom": f"1px solid {LL_BORDER}",
                    "fontSize": "0.8rem",
                },
                style_cell={
                    "backgroundColor": LL_SURFACE_ELEVATED, "color": LL_TEXT_PRIMARY,
                    "border": f"1px solid {LL_BORDER}", "fontSize": "0.8rem",
                    "padding": "8px 12px",
                },
                style_data_conditional=[
                    {"if": {"filter_query": "{risk} >= 75"},
                     "color": RISK_COLORS["critical"], "fontWeight": 600},
                    {"if": {"filter_query": "{risk} >= 50 && {risk} < 75"},
                     "color": RISK_COLORS["high"]},
                    {"if": {"filter_query": "{status} eq 'degraded'"},
                     "backgroundColor": "rgba(255,54,33,0.10)"},
                ],
                sort_action="native",
                page_size=10,
              ) if DEVICES else empty_state_card("No devices match current filters", "\U0001F50C"),
            ]),
            type=LOADING_TYPE, color=LOADING_COLOR,
          ),
          style={"padding": "0"},
        ),
    ], style={**CARD_STYLE_BASE}, className="mb-4"),

    # ── Wire Center Scorecard (gold data only) ──
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H6("Wire Center Scorecard", className="mb-0",
                        style={"color": LL_TEXT_SECONDARY, "fontSize": "0.85rem"})),
                dbc.Col(dbc.Badge(
                    f"{len(GOLD_WIRE_CENTERS)} wire centers" if _gold_ok else "Requires gold tables",
                    style={"fontSize": "0.65rem", "backgroundColor": f"{LL_ACCENT}22",
                           "color": LL_ACCENT if _gold_ok else LL_TEXT_SECONDARY,
                           "border": f"1px solid {LL_BORDER}", "padding": "3px 8px"},
                ), width="auto"),
            ], justify="between", align="center"),
            style={"backgroundColor": LL_SURFACE, "borderBottom": f"1px solid {LL_BORDER}"},
        ),
        dbc.CardBody(
            dash_table.DataTable(
                id="wc-table",
                columns=[
                    {"name": "Rank", "id": "priority_rank"},
                    {"name": "Wire Center", "id": "wire_center"},
                    {"name": "CLLI", "id": "clli"},
                    {"name": "State", "id": "state"},
                    {"name": "Devices", "id": "devices"},
                    {"name": "Services", "id": "services"},
                    {"name": "Customers", "id": "customers"},
                    {"name": "Readiness", "id": "readiness"},
                    {"name": "Risk", "id": "risk"},
                    {"name": "Tier", "id": "tier"},
                    {"name": "Fiber Ready", "id": "fiber_ready"},
                ],
                data=[{
                    "priority_rank": c.get("priority_rank", ""),
                    "wire_center": c.get("wire_center", ""),
                    "clli": c.get("clli", ""),
                    "state": c.get("state", ""),
                    "devices": c.get("devices", 0),
                    "services": c.get("services", 0),
                    "customers": c.get("customers", 0),
                    "readiness": c.get("readiness", 0),
                    "risk": c.get("risk", 0),
                    "tier": c.get("tier", ""),
                    "fiber_ready": "Yes" if c.get("fiber_ready") else "No",
                } for c in GOLD_WIRE_CENTERS] if _gold_ok else [],
                style_header={
                    "backgroundColor": LL_SURFACE, "color": LL_TEXT_SECONDARY,
                    "fontWeight": 600, "borderBottom": f"1px solid {LL_BORDER}",
                    "fontSize": "0.8rem",
                },
                style_cell={
                    "backgroundColor": LL_SURFACE_ELEVATED, "color": LL_TEXT_PRIMARY,
                    "border": f"1px solid {LL_BORDER}", "fontSize": "0.8rem",
                    "padding": "8px 12px",
                },
                style_data_conditional=[
                    {"if": {"filter_query": "{tier} eq 'critical'"},
                     "color": RISK_COLORS["critical"], "fontWeight": 600},
                    {"if": {"filter_query": "{tier} eq 'high'"},
                     "color": RISK_COLORS["high"]},
                    {"if": {"filter_query": "{fiber_ready} eq 'Yes'"},
                     "backgroundColor": f"{LL_ACCENT}0D"},
                ],
                sort_action="native",
                page_size=15,
            ) if _gold_ok else html.P(
                "Wire Center Scorecard requires gold table data from the DLP pipeline.",
                style={"color": LL_TEXT_SECONDARY, "fontSize": "0.85rem", "padding": "16px"},
            ),
            style={"padding": "0"},
        ),
    ], style={**CARD_STYLE_BASE}, className="mb-4"),

    # ── Executive Summary by State (gold data only) ──
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H6("State Executive Summary", className="mb-0",
                        style={"color": LL_TEXT_SECONDARY, "fontSize": "0.85rem"})),
                dbc.Col(dbc.Badge(
                    "Program Health" if _gold_ok else "Requires gold tables",
                    style={"fontSize": "0.65rem", "backgroundColor": f"{LL_ACCENT}22",
                           "color": LL_ACCENT if _gold_ok else LL_TEXT_SECONDARY,
                           "border": f"1px solid {LL_BORDER}", "padding": "3px 8px"},
                ), width="auto"),
            ], justify="between", align="center"),
            style={"backgroundColor": LL_SURFACE, "borderBottom": f"1px solid {LL_BORDER}"},
        ),
        dbc.CardBody(
            dash_table.DataTable(
                id="exec-summary-table",
                columns=[
                    {"name": "State", "id": "state_code"},
                    {"name": "Copper Devices", "id": "total_copper_devices"},
                    {"name": "Active", "id": "active_devices"},
                    {"name": "Critical Risk", "id": "critical_risk_count"},
                    {"name": "High Risk", "id": "high_risk_count"},
                    {"name": "Wire Centers", "id": "wire_center_count"},
                    {"name": "Fiber Ready %", "id": "fiber_ready_pct"},
                    {"name": "Services at Risk", "id": "total_affected_services"},
                    {"name": "Customers", "id": "total_affected_customers"},
                    {"name": "Dig Incidents", "id": "total_dig_incidents"},
                    {"name": "Contractors", "id": "available_contractors"},
                    {"name": "Health", "id": "program_health_status"},
                ],
                data=GOLD_EXEC_SUMMARY if _gold_ok else [],
                style_header={
                    "backgroundColor": LL_SURFACE, "color": LL_TEXT_SECONDARY,
                    "fontWeight": 600, "borderBottom": f"1px solid {LL_BORDER}",
                    "fontSize": "0.8rem",
                },
                style_cell={
                    "backgroundColor": LL_SURFACE_ELEVATED, "color": LL_TEXT_PRIMARY,
                    "border": f"1px solid {LL_BORDER}", "fontSize": "0.8rem",
                    "padding": "8px 12px",
                },
                style_data_conditional=[
                    {"if": {"filter_query": "{program_health_status} eq 'red'"},
                     "color": RISK_COLORS["critical"], "fontWeight": 600},
                    {"if": {"filter_query": "{program_health_status} eq 'green'"},
                     "color": LL_ACCENT, "fontWeight": 600},
                    {"if": {"filter_query": "{program_health_status} eq 'amber'"},
                     "color": RISK_COLORS["medium"], "fontWeight": 600},
                ],
                sort_action="native",
                page_size=10,
            ) if _gold_ok else html.P(
                "Executive Summary requires gold table data from the DLP pipeline.",
                style={"color": LL_TEXT_SECONDARY, "fontSize": "0.85rem", "padding": "16px"},
            ),
            style={"padding": "0"},
        ),
    ], style={**CARD_STYLE_BASE}, className="mb-4"),

    # ── Footer ──
    html.Div(
        html.P("All data is synthetic — generated for demo purposes only.",
               style={"fontSize": "0.7rem", "color": LL_TEXT_SECONDARY,
                      "textAlign": "center"}),
        className="mb-3",
    ),
], fluid=True, style={"backgroundColor": LL_SURFACE, "minHeight": "100vh", "fontFamily": "Inter, system-ui, sans-serif"})


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("map-graph", "figure"),
    Output("device-table-container", "children"),
    Input("filter-state", "value"),
    Input("filter-tier", "value"),
    Input("filter-dtype", "value"),
)
def update_views(state_val, tier_val, dtype_val):
    """Re-render map and device table when any filter changes.
    Includes error boundary and empty-data guards for demo robustness.
    """
    # ── Map with error boundary ──
    try:
        cells = filter_cells(state_val, tier_val)
        fig = build_map(cells)  # build_map already handles empty cells
    except Exception as e:
        logger.error(f"[copper-map] Map error: {e}")
        fig = build_error_figure(str(e))

    # ── Device table with error boundary + empty guard ──
    try:
        devs = filter_devices(state_val, dtype_val)
        if not devs:
            table = empty_state_card(
                "No devices match current filters" if (state_val or dtype_val)
                else "No device data available",
                "\U0001F50C",
            )
        else:
            table = dash_table.DataTable(
                id="device-table",
                columns=[
                    {"name": "ID", "id": "id"},
                    {"name": "Type", "id": "type"},
                    {"name": "Serial", "id": "serial"},
                    {"name": "Status", "id": "status"},
                    {"name": "Installed", "id": "installed"},
                    {"name": "State", "id": "state"},
                    {"name": "City", "id": "city"},
                    {"name": "Alarms", "id": "alarms"},
                    {"name": "Critical", "id": "crit"},
                    {"name": "Risk Score", "id": "risk"},
                ],
                data=devs,
                style_header={
                    "backgroundColor": LL_SURFACE, "color": LL_TEXT_SECONDARY,
                    "fontWeight": 600, "borderBottom": f"1px solid {LL_BORDER}",
                    "fontSize": "0.8rem",
                },
                style_cell={
                    "backgroundColor": LL_SURFACE_ELEVATED, "color": LL_TEXT_PRIMARY,
                    "border": f"1px solid {LL_BORDER}", "fontSize": "0.8rem",
                    "padding": "8px 12px",
                },
                style_data_conditional=[
                    {"if": {"filter_query": "{risk} >= 75"},
                     "color": RISK_COLORS["critical"], "fontWeight": 600},
                    {"if": {"filter_query": "{risk} >= 50 && {risk} < 75"},
                     "color": RISK_COLORS["high"]},
                    {"if": {"filter_query": "{status} eq 'degraded'"},
                     "backgroundColor": "rgba(255,54,33,0.10)"},
                ],
                sort_action="native",
                page_size=10,
            )
    except Exception as e:
        logger.error(f"[copper-map] Device table error: {e}")
        table = empty_state_card(f"Error loading devices: {str(e)[:80]}", "\u26A0\uFE0F")

    return fig, table


# ── Genie chip callbacks (fill input from suggested questions) ─────────────

@app.callback(
    Output("genie-input", "value", allow_duplicate=True),
    [Input(f"genie-chip-{i}", "n_clicks") for i in range(len(GENIE_SUGGESTED))],
    prevent_initial_call=True,
)
def fill_from_chip(*clicks):
    """Populate input from suggested question chip."""
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        return no_update
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    idx = int(trigger_id.split("-")[-1])
    return GENIE_SUGGESTED[idx]


# ── Genie submit callback ───────────────────────────────────────────────────

@app.callback(
    Output("genie-messages", "children"),
    Output("genie-store", "data"),
    Output("genie-input", "value", allow_duplicate=True),
    Input("genie-submit", "n_clicks"),
    Input("genie-input", "n_submit"),
    State("genie-input", "value"),
    State("genie-store", "data"),
    prevent_initial_call=True,
)
def handle_genie_submit(n_clicks, n_submit, question, store):
    """Send user question to Genie agent and display response."""
    if not question or not question.strip():
        return no_update, no_update, no_update

    conv_id = store.get("conv_id") if store else None
    history = store.get("history", []) if store else []

    # Add user message
    history.append({"role": "user", "text": question.strip()})

    # Query Genie
    result = query_genie(question.strip(), conv_id)

    if "error" in result:
        # Sanitize error for demo — strip raw exceptions, hostnames, tokens
        raw_err = str(result['error'])
        if any(kw in raw_err.lower() for kw in ('traceback', 'exception', 'token', 'https://', 'connection')):
            safe_err = "The analytics agent is temporarily unavailable. Please try again in a moment."
        elif len(raw_err) > 120:
            safe_err = raw_err[:120] + "..."
        else:
            safe_err = raw_err
        history.append({"role": "agent", "text": f"\u26A0\uFE0F {safe_err}"})
    else:
        answer = result.get("answer", "Analysis complete.")
        if result.get("sql"):
            answer += f"\n\n\U0001F4CB SQL: {result['sql'][:200]}"
        history.append({"role": "agent", "text": answer})

    new_store = {"conv_id": result.get("conv_id", conv_id), "history": history}

    # Render all messages
    children = []
    for msg in history:
        if msg["role"] == "user":
            children.append(html.Div(
                html.Div(msg["text"], style={
                    "display": "inline-block", "backgroundColor": LL_PRIMARY,
                    "color": "#FFFFFF", "padding": "8px 14px",
                    "borderRadius": "14px 14px 2px 14px", "fontSize": "0.85rem",
                    "maxWidth": "85%",
                }),
                style={"textAlign": "right", "marginBottom": "8px"},
            ))
        else:
            children.append(html.Div(
                html.Div([
                    html.Span("\U0001F50D ", style={"fontSize": "0.75rem"}),
                    html.Span(msg["text"], style={"whiteSpace": "pre-wrap"}),
                ], style={
                    "display": "inline-block",
                    "backgroundColor": f"{LL_SECONDARY}0F",
                    "padding": "10px 14px", "borderRadius": "14px 14px 14px 2px",
                    "fontSize": "0.85rem", "maxWidth": "85%", "color": LL_TEXT_PRIMARY,
                    "lineHeight": "1.5",
                }),
                style={"textAlign": "left", "marginBottom": "8px"},
            ))

    return children, new_store, ""


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
