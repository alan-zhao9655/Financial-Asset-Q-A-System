import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts'

/* ── helpers ── */
function fmt(n, currency = 'USD') {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(2)}M`
  return n.toLocaleString()
}

/* ── Candlestick + Volume chart (lightweight-charts) ── */
function PriceChart({ priceHistory, ticker, currency }) {
  const containerRef = useRef(null)
  const chartRef     = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !priceHistory?.length) return

    const container = containerRef.current
    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#050a14' },
        textColor: '#4a7090',
      },
      grid: {
        vertLines: { color: '#0e2038' },
        horzLines: { color: '#0e2038' },
      },
      crosshair: {
        vertLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
        horzLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
      },
      rightPriceScale: { borderColor: '#0e2038' },
      timeScale: {
        borderColor: '#0e2038',
        timeVisible: true,
        secondsVisible: false,
      },
      width:  container.clientWidth,
      height: 260,
    })
    chartRef.current = chart

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor:         '#3ab87a',
      downColor:       '#e05050',
      borderUpColor:   '#3ab87a',
      borderDownColor: '#e05050',
      wickUpColor:     '#3ab87a',
      wickDownColor:   '#e05050',
    })
    candleSeries.setData(priceHistory)

    // Volume histogram — separate pane via priceScaleId
    const volSeries = chart.addSeries(HistogramSeries, {
      color:        '#2060a050',
      priceFormat:  { type: 'volume' },
      priceScaleId: 'volume',
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    })
    volSeries.setData(
      priceHistory.map(d => ({
        time:  d.time,
        value: d.volume,
        color: d.close >= d.open ? '#3ab87a30' : '#e0505030',
      }))
    )

    chart.timeScale().fitContent()

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth })
    })
    ro.observe(container)

    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [priceHistory])

  const last    = priceHistory?.[priceHistory.length - 1]
  const prev    = priceHistory?.[priceHistory.length - 2]
  const dayChg  = last && prev ? ((last.close - prev.close) / prev.close * 100) : null

  return (
    <div>
      {/* Mini stats bar */}
      {last && (
        <div style={{ display: 'flex', gap: 20, marginBottom: 12, flexWrap: 'wrap' }}>
          {[
            { label: 'Close',  value: `${last.close.toFixed(2)} ${currency}` },
            { label: '1D',     value: dayChg != null ? `${dayChg >= 0 ? '+' : ''}${dayChg.toFixed(2)}%` : null,
              color: dayChg >= 0 ? '#3ab87a' : '#e05050' },
            { label: 'High',   value: last.high.toFixed(2) },
            { label: 'Low',    value: last.low.toFixed(2) },
            { label: 'Volume', value: fmt(last.volume) },
          ].map(({ label, value, color }) => value && (
            <div key={label}>
              <div style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#2a5070', marginBottom: 2 }}>
                {label}
              </div>
              <div style={{ fontSize: 13, fontFamily: 'monospace', fontWeight: 700, color: color || '#c8e4f8' }}>
                {value}
              </div>
            </div>
          ))}
        </div>
      )}
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  )
}

/* ── Quarterly Revenue vs Net Income bar chart (pure SVG — no extra dep) ── */
function EarningsChart({ earnings, currency }) {
  if (!earnings?.length) return (
    <div style={{ color: '#2a5070', fontSize: 13, padding: '20px 0' }}>No quarterly earnings data available.</div>
  )

  const rows = [...earnings].reverse()  // oldest first
  const maxVal = Math.max(...rows.flatMap(r => [r.revenue ?? 0, r.net_income ?? 0]))

  const BAR_W   = 22
  const GAP     = 6
  const GROUP_W = BAR_W * 2 + GAP + 24   // two bars + gap + group spacing
  const H       = 160
  const PADDING = { top: 20, bottom: 36, left: 48, right: 12 }

  const svgW = PADDING.left + rows.length * GROUP_W + PADDING.right

  function barH(val) {
    if (!val || maxVal === 0) return 0
    return Math.max(2, (val / maxVal) * H)
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
        {[
          { color: '#2070c0', label: 'Revenue' },
          { color: '#3ab87a', label: 'Net Income' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            <span style={{ fontSize: 11, color: '#4a7090', letterSpacing: '0.06em' }}>{label}</span>
          </div>
        ))}
      </div>

      <svg width="100%" viewBox={`0 0 ${svgW} ${H + PADDING.top + PADDING.bottom}`}
           style={{ overflow: 'visible', display: 'block' }}>

        {/* Y-axis gridlines + labels */}
        {[0, 0.25, 0.5, 0.75, 1].map(pct => {
          const y = PADDING.top + H - pct * H
          const val = pct * maxVal
          return (
            <g key={pct}>
              <line x1={PADDING.left} x2={svgW - PADDING.right} y1={y} y2={y}
                    stroke="#0e2038" strokeWidth="1" />
              <text x={PADDING.left - 6} y={y + 4} textAnchor="end"
                    fontSize="9" fill="#2a5070" fontFamily="monospace">
                {fmt(val)}
              </text>
            </g>
          )
        })}

        {/* Bars */}
        {rows.map((row, i) => {
          const gx = PADDING.left + i * GROUP_W
          const revH = barH(row.revenue)
          const netH = barH(row.net_income)
          const label = row.period ? row.period.slice(0, 7) : `Q${i + 1}`
          return (
            <g key={row.period || i}>
              {/* Revenue bar */}
              <rect x={gx} y={PADDING.top + H - revH} width={BAR_W} height={revH}
                    fill="#2070c0" rx="2" opacity="0.85" />
              {/* Net Income bar */}
              <rect x={gx + BAR_W + GAP} y={PADDING.top + H - netH} width={BAR_W} height={netH}
                    fill="#3ab87a" rx="2" opacity="0.85" />
              {/* Period label */}
              <text x={gx + BAR_W + GAP / 2} y={PADDING.top + H + 14}
                    textAnchor="middle" fontSize="9" fill="#2a5070" fontFamily="monospace">
                {label}
              </text>
              {/* Revenue value tooltip on hover via title */}
              {row.revenue && (
                <title>{`Revenue: ${fmt(row.revenue)} | Net Income: ${fmt(row.net_income)}`}</title>
              )}
            </g>
          )
        })}

        {/* Baseline */}
        <line x1={PADDING.left} x2={svgW - PADDING.right}
              y1={PADDING.top + H} y2={PADDING.top + H}
              stroke="#122840" strokeWidth="1" />
      </svg>
    </div>
  )
}

/* ── Tab button ── */
function Tab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 14px',
        borderRadius: 6,
        border: 'none',
        cursor: 'pointer',
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        background: active ? '#2070c0' : 'transparent',
        color:      active ? '#e8f4ff'  : '#2a5070',
        transition: 'background 0.15s, color 0.15s',
      }}
    >
      {children}
    </button>
  )
}

/* ── Main export ── */
export default function ChartPanel({ chartData }) {
  const [tab, setTab] = useState('price')
  const { ticker, company_name, currency, price_history, quarterly_earnings } = chartData

  const hasEarnings = quarterly_earnings?.length > 0

  return (
    <div style={{
      marginTop: 10,
      borderRadius: 12,
      background: '#070e1c',
      border: '1px solid #0e2038',
      padding: '16px 18px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            fontSize: 11, fontFamily: 'monospace', fontWeight: 700,
            letterSpacing: '0.12em', color: '#60b4ff',
          }}>
            {ticker}
          </span>
          <span style={{ fontSize: 11, color: '#2a5070' }}>{company_name}</span>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <Tab active={tab === 'price'} onClick={() => setTab('price')}>Price</Tab>
          {hasEarnings && (
            <Tab active={tab === 'earnings'} onClick={() => setTab('earnings')}>Earnings</Tab>
          )}
        </div>
      </div>

      {/* Chart area */}
      {tab === 'price' && (
        <PriceChart priceHistory={price_history} ticker={ticker} currency={currency} />
      )}
      {tab === 'earnings' && hasEarnings && (
        <EarningsChart earnings={quarterly_earnings} currency={currency} />
      )}
    </div>
  )
}
