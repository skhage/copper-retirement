"""Copper Prioritization Map (P7-MAP)
LakeLink Fiber — Copper Retirement Program
Demo Beat 1: "Where is our copper / risk of touching it?"

Python/Dash implementation of the React/AppKit scaffold.
Uses mock data until FIX-COORDINATES + P2-H3 + P4-RISK land.
All data is SYNTHETIC.
"""
import os
import dash
from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ── Configuration ──────────────────────────────────────────────────────────────
APP_PORT = int(os.environ.get("DATABRICKS_APP_PORT", 8000))

# ── Mock Data (translated from client/src/mock/mockData.ts) ───────────────────
RISK_COLORS = {"critical": "#EB1600", "high": "#FF8C00", "medium": "#FFD700", "low": "#40D1F5"}

HEX_CELLS = [
    # California — high copper density, aging plant
    {"h3": "892a100d2c3ffff", "lat": 36.78, "lon": -119.42, "devices": 487, "risk": 78, "tier": "critical", "alarms": 4210, "crit": 1580, "state": "CA"},
    {"h3": "892a100d2c7ffff", "lat": 34.05, "lon": -118.24, "devices": 312, "risk": 65, "tier": "high",     "alarms": 2890, "crit": 890,  "state": "CA"},
    {"h3": "892a100d2cbffff", "lat": 37.77, "lon": -122.42, "devices": 198, "risk": 52, "tier": "high",     "alarms": 1650, "crit": 420,  "state": "CA"},
    # Texas — large footprint, mixed condition
    {"h3": "892a100d2cfffff", "lat": 31.97, "lon": -99.90,  "devices": 423, "risk": 71, "tier": "high",     "alarms": 3560, "crit": 1120, "state": "TX"},
    {"h3": "892a100d2d3ffff", "lat": 29.76, "lon": -95.37,  "devices": 278, "risk": 58, "tier": "high",     "alarms": 2340, "crit": 650,  "state": "TX"},
    {"h3": "892a100d2d7ffff", "lat": 32.78, "lon": -96.80,  "devices": 156, "risk": 42, "tier": "medium",   "alarms": 1120, "crit": 280,  "state": "TX"},
    # Florida — coastal exposure, moisture risk
    {"h3": "892a100d2dbffff", "lat": 27.66, "lon": -81.52,  "devices": 356, "risk": 82, "tier": "critical", "alarms": 3890, "crit": 1890, "state": "FL"},
    {"h3": "892a100d2dfffff", "lat": 25.76, "lon": -80.19,  "devices": 189, "risk": 73, "tier": "high",     "alarms": 2010, "crit": 780,  "state": "FL"},
    # New York — dense urban, old infrastructure
    {"h3": "892a100d2e3ffff", "lat": 40.71, "lon": -74.01,  "devices": 401, "risk": 88, "tier": "critical", "alarms": 4560, "crit": 2100, "state": "NY"},
    {"h3": "892a100d2e7ffff", "lat": 42.65, "lon": -73.76,  "devices": 134, "risk": 45, "tier": "medium",   "alarms": 980,  "crit": 210,  "state": "NY"},
    # Ohio — rust belt, aging
    {"h3": "892a100d2ebffff", "lat": 40.42, "lon": -82.91,  "devices": 267, "risk": 62, "tier": "high",     "alarms": 2230, "crit": 670,  "state": "OH"},
    {"h3": "892a100d2efffff", "lat": 41.50, "lon": -81.69,  "devices": 178, "risk": 55, "tier": "high",     "alarms": 1540, "crit": 410,  "state": "OH"},
    # Illinois — Chicago metro + downstate
    {"h3": "892a100d2f3ffff", "lat": 41.88, "lon": -87.63,  "devices": 345, "risk": 76, "tier": "critical", "alarms": 3120, "crit": 1340, "state": "IL"},
    {"h3": "892a100d2f7ffff", "lat": 39.78, "lon": -89.65,  "devices": 112, "risk": 38, "tier": "medium",   "alarms": 780,  "crit": 150,  "state": "IL"},
]

DEVICES = [
    {"id": 1001, "type": "CPE",         "serial": "CPE-NYC-001", "status": "active",   "installed": "2008-03-15", "state": "NY", "city": "New York",      "alarms": 12, "crit": 4, "risk": 92},
    {"id": 1002, "type": "ONT",         "serial": "ONT-NYC-002", "status": "active",   "installed": "2011-07-22", "state": "NY", "city": "New York",      "alarms": 8,  "crit": 2, "risk": 78},
    {"id": 1003, "type": "CPE",         "serial": "CPE-MIA-001", "status": "degraded", "installed": "2005-11-01", "state": "FL", "city": "Miami",          "alarms": 18, "crit": 7, "risk": 95},
    {"id": 1004, "type": "OLT",         "serial": "OLT-CHI-001", "status": "active",   "installed": "2013-02-10", "state": "IL", "city": "Chicago",        "alarms": 6,  "crit": 1, "risk": 55},
    {"id": 1005, "type": "Patch Panel", "serial": "PP-HOU-001",  "status": "active",   "installed": "2009-09-30", "state": "TX", "city": "Houston",        "alarms": 14, "crit": 5, "risk": 82},
    {"id": 1006, "type": "CPE",         "serial": "CPE-CLE-001", "status": "active",   "installed": "2010-06-14", "state": "OH", "city": "Cleveland",      "alarms": 9,  "crit": 3, "risk": 68},
    {"id": 1007, "type": "ONT",         "serial": "ONT-LA-001",  "status": "active",   "installed": "2012-01-20", "state": "CA", "city": "Los Angeles",    "alarms": 11, "crit": 4, "risk": 74},
    {"id": 1008, "type": "OLT",         "serial": "OLT-SF-001",  "status": "degraded", "installed": "2007-08-05", "state": "CA", "city": "San Francisco",  "alarms": 16, "crit": 6, "risk": 88},
]

KPIS = {
    "devices": 2672, "cpe": 688, "ont": 663, "olt": 661, "pp": 660,
    "alarms": 26943, "crit_alarms": 9978, "pct_crit": 37.3,
    "states": 6, "wire_centers": 200,
}

STATES = sorted(set(c["state"] for c in HEX_CELLS))
TIERS = ["critical", "high", "medium", "low"]
DEVICE_TYPES = sorted(set(d["type"] for d in DEVICES))

# ── Helpers ────────────────────────────────────────────────────────────────────

def kpi_card(label, value, color="#e2e8f0", sub=None):
    children = [
        html.P(label, className="mb-0",
               style={"fontSize": "0.75rem", "color": "#94a3b8",
                      "textTransform": "uppercase", "letterSpacing": "0.05em"}),
        html.H4(value, className="mb-0 mt-1",
                style={"color": color, "fontWeight": 700}),
    ]
    if sub:
        children.append(
            html.P(sub, className="mb-0",
                   style={"fontSize": "0.7rem", "color": "#64748b"})
        )
    return dbc.Card(
        dbc.CardBody(children),
        style={"backgroundColor": "#1e293b", "border": "1px solid #334155",
               "borderRadius": "8px"},
    )


def build_map(cells):
    """Build a plotly Scattergeo figure from hex cell data."""
    fig = go.Figure()
    for tier in TIERS:
        tier_cells = [c for c in cells if c["tier"] == tier]
        if not tier_cells:
            continue
        fig.add_trace(go.Scattergeo(
            lat=[c["lat"] for c in tier_cells],
            lon=[c["lon"] for c in tier_cells],
            text=[
                f"<b>{c['state']}</b><br>"
                f"{c['devices']} devices<br>"
                f"Risk score: {c['risk']}<br>"
                f"Alarms: {c['alarms']:,} ({c['crit']:,} critical)"
                for c in tier_cells
            ],
            hoverinfo="text",
            marker=dict(
                size=[max(10, c["devices"] / 12) for c in tier_cells],
                color=RISK_COLORS[tier],
                opacity=0.85,
                line=dict(width=1, color="#1e293b"),
                sizemode="diameter",
            ),
            name=tier.capitalize(),
        ))
    fig.update_layout(
        geo=dict(
            scope="usa",
            bgcolor="rgba(0,0,0,0)",
            lakecolor="#1e293b",
            landcolor="#1e293b",
            subunitcolor="#334155",
            countrycolor="#475569",
            showlakes=True,
            showsubunits=True,
            resolution=50,
        ),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        legend=dict(
            font=dict(color="#94a3b8", size=12),
            bgcolor="rgba(0,0,0,0)",
            x=0.01, y=0.99,
        ),
        hoverlabel=dict(
            bgcolor="#1e293b", font_size=13, font_color="#e2e8f0",
            bordercolor="#334155",
        ),
    )
    return fig


def filter_cells(state_val, tier_val):
    cells = HEX_CELLS
    if state_val:
        cells = [c for c in cells if c["state"] == state_val]
    if tier_val:
        cells = [c for c in cells if c["tier"] == tier_val]
    return cells


def filter_devices(state_val, type_val):
    devs = DEVICES
    if state_val:
        devs = [d for d in devs if d["state"] == state_val]
    if type_val:
        devs = [d for d in devs if d["type"] == type_val]
    return devs


# ── Layout ─────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SLATE],
    title="Copper Map — LakeLink Fiber",
)

app.layout = dbc.Container([
    # ── Header ──
    dbc.Row([
        dbc.Col([
            html.H3("Copper Prioritization Map", className="mb-0",
                    style={"fontWeight": 700}),
            html.P("LakeLink Fiber — Copper Retirement Program",
                   style={"fontSize": "0.85rem", "color": "#64748b",
                          "marginBottom": 0}),
        ], width="auto"),
        dbc.Col(
            dbc.Badge("SYNTHETIC DATA", color="warning",
                      style={"fontSize": "0.7rem", "verticalAlign": "middle"}),
            width="auto", className="d-flex align-items-center",
        ),
    ], className="mb-3 mt-2", justify="between"),

    # ── KPI Row ──
    dbc.Row([
        dbc.Col(kpi_card(
            "Total Copper Devices", f"{KPIS['devices']:,}", "#60a5fa",
            f"CPE {KPIS['cpe']}  |  ONT {KPIS['ont']}  |  OLT {KPIS['olt']}  |  PP {KPIS['pp']}",
        ), md=3),
        dbc.Col(kpi_card(
            "Critical Risk", f"{KPIS['pct_crit']}%", RISK_COLORS["critical"],
            f"{KPIS['crit_alarms']:,} critical alarms",
        ), md=3),
        dbc.Col(kpi_card("Total Alarms", f"{KPIS['alarms']:,}", "#fbbf24"), md=2),
        dbc.Col(kpi_card("States", str(KPIS["states"]), "#34d399"), md=2),
        dbc.Col(kpi_card(
            "Wire Centers", str(KPIS["wire_centers"]), "#a78bfa",
            "Pending generation",
        ), md=2),
    ], className="mb-3 g-2"),

    # ── Filters + Map ──
    dbc.Row([
        # Sidebar
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H6("Filters", className="mb-3",
                        style={"color": "#94a3b8", "textTransform": "uppercase",
                               "fontSize": "0.75rem", "letterSpacing": "0.05em"}),
                html.Label("State", style={"fontSize": "0.8rem", "color": "#94a3b8"}),
                dcc.Dropdown(
                    id="filter-state",
                    options=[{"label": s, "value": s} for s in STATES],
                    placeholder="All states", clearable=True,
                ),
                html.Label("Risk Tier", className="mt-2",
                           style={"fontSize": "0.8rem", "color": "#94a3b8"}),
                dcc.Dropdown(
                    id="filter-tier",
                    options=[{"label": t.capitalize(), "value": t} for t in TIERS],
                    placeholder="All tiers", clearable=True,
                ),
                html.Label("Device Type", className="mt-2",
                           style={"fontSize": "0.8rem", "color": "#94a3b8"}),
                dcc.Dropdown(
                    id="filter-dtype",
                    options=[{"label": t, "value": t} for t in DEVICE_TYPES],
                    placeholder="All types", clearable=True,
                ),
                html.Hr(style={"borderColor": "#334155"}),
                html.H6("Risk Legend", className="mb-2",
                        style={"color": "#94a3b8", "textTransform": "uppercase",
                               "fontSize": "0.75rem", "letterSpacing": "0.05em"}),
                *[
                    html.Div([
                        html.Span("", style={
                            "display": "inline-block", "width": 12, "height": 12,
                            "borderRadius": "50%", "backgroundColor": RISK_COLORS[t],
                            "marginRight": 8,
                        }),
                        html.Span(f"{t.capitalize()} (\u2265{th})",
                                  style={"fontSize": "0.8rem", "color": "#cbd5e1"}),
                    ], className="mb-1")
                    for t, th in [("critical", 75), ("high", 50), ("medium", 25), ("low", 0)]
                ],
                html.Hr(style={"borderColor": "#334155"}),
                html.P("Bubble size = device count",
                       style={"fontSize": "0.7rem", "color": "#64748b", "marginBottom": 4}),
                html.P("Hover for details",
                       style={"fontSize": "0.7rem", "color": "#64748b", "marginBottom": 0}),
            ]), style={"backgroundColor": "#1e293b", "border": "1px solid #334155",
                      "borderRadius": "8px"}),
        ], md=3),

        # Map
        dbc.Col([
            dbc.Card(
                dcc.Graph(id="map-graph", figure=build_map(HEX_CELLS),
                          config={"displayModeBar": False}),
                style={"backgroundColor": "#0f172a", "border": "1px solid #334155",
                       "borderRadius": "8px", "overflow": "hidden"},
            ),
        ], md=9),
    ], className="mb-3"),

    # ── Device Table ──
    dbc.Card([
        dbc.CardHeader(
            html.H6("Device Detail", className="mb-0",
                    style={"color": "#94a3b8", "fontSize": "0.85rem"}),
            style={"backgroundColor": "#1e293b", "borderBottom": "1px solid #334155"},
        ),
        dbc.CardBody(
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
                    "backgroundColor": "#1e293b", "color": "#94a3b8",
                    "fontWeight": 600, "borderBottom": "1px solid #334155",
                    "fontSize": "0.8rem",
                },
                style_cell={
                    "backgroundColor": "#0f172a", "color": "#e2e8f0",
                    "border": "1px solid #1e293b", "fontSize": "0.8rem",
                    "padding": "8px 12px",
                },
                style_data_conditional=[
                    {"if": {"filter_query": "{risk} >= 75"},
                     "color": RISK_COLORS["critical"], "fontWeight": 600},
                    {"if": {"filter_query": "{risk} >= 50 && {risk} < 75"},
                     "color": RISK_COLORS["high"]},
                    {"if": {"filter_query": "{status} eq 'degraded'"},
                     "backgroundColor": "rgba(235,22,0,0.1)"},
                ],
                sort_action="native",
                page_size=10,
            ),
            style={"padding": "0"},
        ),
    ], style={"backgroundColor": "#0f172a", "border": "1px solid #334155",
             "borderRadius": "8px"}, className="mb-4"),

    # ── Footer ──
    html.Div(
        html.P("All data is synthetic — generated for demo purposes only.",
               style={"fontSize": "0.7rem", "color": "#475569",
                      "textAlign": "center"}),
        className="mb-3",
    ),
], fluid=True, style={"backgroundColor": "#0f172a", "minHeight": "100vh"})


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("map-graph", "figure"),
    Output("device-table", "data"),
    Input("filter-state", "value"),
    Input("filter-tier", "value"),
    Input("filter-dtype", "value"),
)
def update_views(state_val, tier_val, dtype_val):
    """Re-render map and device table when any filter changes."""
    cells = filter_cells(state_val, tier_val)
    fig = build_map(cells)
    devs = filter_devices(state_val, dtype_val)
    return fig, devs


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
