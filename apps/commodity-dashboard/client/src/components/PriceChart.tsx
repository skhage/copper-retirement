/**
 * PriceChart.tsx
 * Copper price chart: historical LME spot + 3M/15M forwards + AI forecast.
 * Renders as an SVG area chart with forecast confidence bands.
 *
 * TODO: Replace SVG placeholder with recharts or visx once deps are installed.
 */
import { mockPriceHistory, mockForecast, USE_MOCK_DATA } from '../mock/mockData';
import type { CopperPrice, ForecastPoint } from '../mock/mockData';
import { formatPriceLb, formatDate } from '../lib/formatters';

const CHART_W = 800;
const CHART_H = 320;
const PAD = { top: 20, right: 60, bottom: 40, left: 60 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

export function PriceChart() {
  const prices: CopperPrice[] = USE_MOCK_DATA ? mockPriceHistory : mockPriceHistory;
  const forecast: ForecastPoint[] = USE_MOCK_DATA ? mockForecast : mockForecast;

  // Y range
  const allPrices = prices.map((p) => p.spot_usd_lb);
  const yMin = Math.floor(Math.min(...allPrices) * 10) / 10 - 0.2;
  const yMax = Math.ceil(Math.max(...allPrices) * 10) / 10 + 0.5;

  const scaleX = (i: number, total: number) => PAD.left + (i / (total - 1)) * INNER_W;
  const scaleY = (v: number) => PAD.top + INNER_H - ((v - yMin) / (yMax - yMin)) * INNER_H;

  // Build spot line path
  const spotPath = prices
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${scaleX(i, prices.length)},${scaleY(p.spot_usd_lb)}`)
    .join(' ');

  // Build 3M forward line path
  const fwd3mPath = prices
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${scaleX(i, prices.length)},${scaleY(p.forward_3m_usd_lb)}`)
    .join(' ');

  // Y-axis ticks
  const yTicks: number[] = [];
  for (let y = Math.ceil(yMin); y <= yMax; y += 0.5) yTicks.push(y);

  // X-axis year labels
  const yearLabels = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold">Copper Price History & Forecast</h2>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-600 inline-block" /> LME Spot
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-emerald-500 inline-block" /> 3M Forward
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-orange-500 inline-block border-dashed" /> AI Forecast
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="w-full" preserveAspectRatio="xMidYMid meet">
        {/* Grid lines */}
        {yTicks.map((y) => (
          <g key={y}>
            <line
              x1={PAD.left} y1={scaleY(y)} x2={CHART_W - PAD.right} y2={scaleY(y)}
              stroke="#e5e7eb" strokeWidth={1}
            />
            <text x={PAD.left - 8} y={scaleY(y) + 4} textAnchor="end" fontSize={10} fill="#6b7280">
              ${y.toFixed(2)}
            </text>
          </g>
        ))}

        {/* X-axis year labels */}
        {yearLabels.map((year, i) => (
          <text
            key={year}
            x={scaleX(i * 12, prices.length)}
            y={CHART_H - 8}
            textAnchor="middle" fontSize={10} fill="#6b7280"
          >
            {year}
          </text>
        ))}

        {/* Spot line */}
        <path d={spotPath} fill="none" stroke="#2563eb" strokeWidth={2} />

        {/* 3M forward line */}
        <path d={fwd3mPath} fill="none" stroke="#10b981" strokeWidth={1.5} strokeDasharray="4,2" />

        {/* Forecast region placeholder */}
        <rect
          x={CHART_W - PAD.right - 80}
          y={PAD.top}
          width={80}
          height={INNER_H}
          fill="#f97316" fillOpacity={0.08}
        />
        <text
          x={CHART_W - PAD.right - 40}
          y={PAD.top + INNER_H / 2}
          textAnchor="middle" fontSize={10} fill="#f97316" fontWeight="500"
        >
          AI Forecast
        </text>
        <text
          x={CHART_W - PAD.right - 40}
          y={PAD.top + INNER_H / 2 + 14}
          textAnchor="middle" fontSize={9} fill="#f97316"
        >
          12-mo horizon
        </text>

        {/* Current price annotation */}
        {prices.length > 0 && (
          <>
            <circle
              cx={scaleX(prices.length - 1, prices.length)}
              cy={scaleY(prices[prices.length - 1].spot_usd_lb)}
              r={4} fill="#2563eb"
            />
            <text
              x={scaleX(prices.length - 1, prices.length) + 8}
              y={scaleY(prices[prices.length - 1].spot_usd_lb) + 4}
              fontSize={11} fill="#2563eb" fontWeight="600"
            >
              {formatPriceLb(prices[prices.length - 1].spot_usd_lb)}
            </text>
          </>
        )}
      </svg>

      <p className="text-xs text-muted-foreground mt-2">
        Source: Synthetic LME data (modeled after SPEC_commodity_price.md). AI forecast from P4-COMMODITY model (mock).
      </p>
    </div>
  );
}
