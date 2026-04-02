import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts'

/* ── colour palette for comparison lines ── */
const PALETTE = ['#60b4ff', '#4ad4b0', '#f0a050', '#e07090', '#a080e0']

/* ── helpers ── */
function fmtLarge(n) {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e12) return `${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9)  return `${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6)  return `${(n / 1e6).toFixed(2)}M`
  return n.toLocaleString()
}

function fmtPct(n, plus = true) {
  if (n == null) return 'N/A'
  const s = n.toFixed(2) + '%'
  return plus && n > 0 ? '+' + s : s
}

/* ══════════════════════════════════════════════════════════════
   SINGLE STOCK — Candlestick + Volume
══════════════════════════════════════════════════════════════ */
function PriceChart({ priceHistory, ticker, currency }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !priceHistory?.length) return
    const container = containerRef.current

    const chart = createChart(container, {
      layout:  { background: { type: ColorType.Solid, color: '#050a14' }, textColor: '#4a7090' },
      grid:    { vertLines: { color: '#0e2038' }, horzLines: { color: '#0e2038' } },
      crosshair: {
        vertLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
        horzLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
      },
      rightPriceScale: { borderColor: '#0e2038' },
      timeScale: { borderColor: '#0e2038', timeVisible: true, secondsVisible: false },
      width:  container.clientWidth,
      height: 260,
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#3ab87a', downColor: '#e05050',
      borderUpColor: '#3ab87a', borderDownColor: '#e05050',
      wickUpColor: '#3ab87a', wickDownColor: '#e05050',
    })
    candleSeries.setData(priceHistory)

    const volSeries = chart.addSeries(HistogramSeries, {
      color: '#2060a050', priceFormat: { type: 'volume' }, priceScaleId: 'volume',
    })
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
    volSeries.setData(priceHistory.map(d => ({
      time: d.time, value: d.volume,
      color: d.close >= d.open ? '#3ab87a30' : '#e0505030',
    })))

    chart.timeScale().fitContent()
    const ro = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth }))
    ro.observe(container)
    return () => { ro.disconnect(); chart.remove() }
  }, [priceHistory])

  const last   = priceHistory?.[priceHistory.length - 1]
  const prev   = priceHistory?.[priceHistory.length - 2]
  const dayChg = last && prev ? ((last.close - prev.close) / prev.close * 100) : null

  return (
    <div>
      {last && (
        <div style={{ display: 'flex', gap: 20, marginBottom: 12, flexWrap: 'wrap' }}>
          {[
            { label: 'Close',  value: `${last.close.toFixed(2)} ${currency}` },
            { label: '1D',     value: fmtPct(dayChg), color: dayChg >= 0 ? '#3ab87a' : '#e05050' },
            { label: 'High',   value: last.high.toFixed(2) },
            { label: 'Low',    value: last.low.toFixed(2) },
            { label: 'Volume', value: fmtLarge(last.volume) },
          ].map(({ label, value, color }) => value && (
            <div key={label}>
              <div style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#2a5070', marginBottom: 2 }}>{label}</div>
              <div style={{ fontSize: 13, fontFamily: 'monospace', fontWeight: 700, color: color || '#c8e4f8' }}>{value}</div>
            </div>
          ))}
        </div>
      )}
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   SINGLE STOCK — Quarterly Earnings bars (pure SVG)
══════════════════════════════════════════════════════════════ */
function EarningsChart({ earnings }) {
  if (!earnings?.length) return (
    <div style={{ color: '#2a5070', fontSize: 13, padding: '20px 0' }}>No quarterly earnings data available.</div>
  )
  const rows   = [...earnings].reverse()
  const maxVal = Math.max(...rows.flatMap(r => [r.revenue ?? 0, r.net_income ?? 0]))
  const BAR_W = 22, GAP = 6, GROUP_W = BAR_W * 2 + GAP + 24, H = 160
  const PAD   = { top: 20, bottom: 36, left: 52, right: 12 }
  const svgW  = PAD.left + rows.length * GROUP_W + PAD.right

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
        {[{ color: '#2070c0', label: 'Revenue' }, { color: '#3ab87a', label: 'Net Income' }].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            <span style={{ fontSize: 11, color: '#4a7090', letterSpacing: '0.06em' }}>{label}</span>
          </div>
        ))}
      </div>
      <svg width="100%" viewBox={`0 0 ${svgW} ${H + PAD.top + PAD.bottom}`} style={{ overflow: 'visible', display: 'block' }}>
        {[0, 0.25, 0.5, 0.75, 1].map(pct => {
          const y = PAD.top + H - pct * H
          return (
            <g key={pct}>
              <line x1={PAD.left} x2={svgW - PAD.right} y1={y} y2={y} stroke="#0e2038" strokeWidth="1" />
              <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="#2a5070" fontFamily="monospace">{fmtLarge(pct * maxVal)}</text>
            </g>
          )
        })}
        {rows.map((row, i) => {
          const gx   = PAD.left + i * GROUP_W
          const revH = maxVal ? Math.max(2, (row.revenue ?? 0) / maxVal * H) : 0
          const netH = maxVal ? Math.max(2, (row.net_income ?? 0) / maxVal * H) : 0
          return (
            <g key={row.period || i}>
              <rect x={gx} y={PAD.top + H - revH} width={BAR_W} height={revH} fill="#2070c0" rx="2" opacity="0.85" />
              <rect x={gx + BAR_W + GAP} y={PAD.top + H - netH} width={BAR_W} height={netH} fill="#3ab87a" rx="2" opacity="0.85" />
              <text x={gx + BAR_W + GAP / 2} y={PAD.top + H + 14} textAnchor="middle" fontSize="9" fill="#2a5070" fontFamily="monospace">
                {(row.period || '').slice(0, 7)}
              </text>
            </g>
          )
        })}
        <line x1={PAD.left} x2={svgW - PAD.right} y1={PAD.top + H} y2={PAD.top + H} stroke="#122840" strokeWidth="1" />
      </svg>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   COMPARISON — Normalised % return line chart
══════════════════════════════════════════════════════════════ */
function ComparisonLineChart({ stocks }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !stocks?.length) return
    const container = containerRef.current

    const chart = createChart(container, {
      layout:  { background: { type: ColorType.Solid, color: '#050a14' }, textColor: '#4a7090' },
      grid:    { vertLines: { color: '#0e2038' }, horzLines: { color: '#0e2038' } },
      crosshair: {
        vertLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
        horzLine: { color: '#2060a060', labelBackgroundColor: '#0d2040' },
      },
      rightPriceScale: {
        borderColor: '#0e2038',
        // Format as % return
        mode: 0,
      },
      timeScale: { borderColor: '#0e2038', timeVisible: true, secondsVisible: false },
      width:  container.clientWidth,
      height: 260,
    })

    stocks.forEach((stock, idx) => {
      if (!stock.price_history?.length) return
      const color = PALETTE[idx % PALETTE.length]
      const series = chart.addSeries(LineSeries, {
        color,
        lineWidth: 2,
        priceFormat: { type: 'custom', formatter: v => v.toFixed(2) + '%' },
        title: stock.ticker,
      })

      // Normalise to % return from first close
      const firstClose = stock.price_history[0].close
      series.setData(
        stock.price_history.map(d => ({
          time:  d.time,
          value: ((d.close - firstClose) / firstClose) * 100,
        }))
      )
    })

    chart.timeScale().fitContent()
    const ro = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth }))
    ro.observe(container)
    return () => { ro.disconnect(); chart.remove() }
  }, [stocks])

  return (
    <div>
      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
        {stocks.map((stock, i) => (
          <div key={stock.ticker} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 20, height: 3, borderRadius: 2, background: PALETTE[i % PALETTE.length] }} />
            <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 700, color: PALETTE[i % PALETTE.length] }}>
              {stock.ticker}
            </span>
            <span style={{ fontSize: 11, color: '#2a5070' }}>{stock.company_name}</span>
          </div>
        ))}
      </div>
      <div ref={containerRef} style={{ width: '100%' }} />
      <div style={{ fontSize: 10, color: '#1a3a60', marginTop: 6, letterSpacing: '0.04em' }}>
        Y-axis: % return from start of period (all stocks start at 0%)
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   COMPARISON — Metrics table
══════════════════════════════════════════════════════════════ */
function MetricsTable({ stocks }) {
  const rows = [
    { label: 'Price',       key: s => s.metrics.current_price?.toFixed(2) + ' ' + (s.currency || '') },
    { label: '1D Change',   key: s => fmtPct(s.metrics.day_change_pct),
      color: s => s.metrics.day_change_pct >= 0 ? '#3ab87a' : '#e05050' },
    { label: '7D Change',   key: s => fmtPct(s.metrics.change_7d_pct),
      color: s => (s.metrics.change_7d_pct ?? 0) >= 0 ? '#3ab87a' : '#e05050' },
    { label: '30D Change',  key: s => fmtPct(s.metrics.change_30d_pct),
      color: s => (s.metrics.change_30d_pct ?? 0) >= 0 ? '#3ab87a' : '#e05050' },
    { label: 'Market Cap',  key: s => fmtLarge(s.metrics.market_cap) },
    { label: 'P/E Ratio',   key: s => s.metrics.pe_ratio?.toFixed(1) ?? 'N/A' },
    { label: 'Div Yield',   key: s => s.metrics.dividend_yield ? fmtPct(s.metrics.dividend_yield * 100, false) : 'N/A' },
    { label: '52W High',    key: s => s.metrics.price_52w_high?.toFixed(2) ?? 'N/A' },
    { label: 'From High',   key: s => fmtPct(s.metrics.pct_from_52w_high),
      color: s => (s.metrics.pct_from_52w_high ?? 0) >= 0 ? '#3ab87a' : '#e05050' },
  ]

  const COL = 120

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '6px 10px', color: '#2a5070', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', width: 90 }} />
            {stocks.map((s, i) => (
              <th key={s.ticker} style={{ padding: '6px 10px', textAlign: 'right', minWidth: COL }}>
                <div style={{ fontFamily: 'monospace', fontWeight: 700, color: PALETTE[i % PALETTE.length], fontSize: 12, letterSpacing: '0.08em' }}>{s.ticker}</div>
                <div style={{ color: '#2a5070', fontSize: 10, fontWeight: 400, marginTop: 1 }}>{s.company_name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, key, color }) => (
            <tr key={label} style={{ borderTop: '1px solid #0e2038' }}>
              <td style={{ padding: '7px 10px', color: '#2a5070', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</td>
              {stocks.map((s, i) => (
                <td key={s.ticker} style={{ padding: '7px 10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: color ? color(s) : '#c8e4f8', fontSize: 12 }}>
                  {key(s)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   COMPARISON — Revenue comparison bars (SVG)
══════════════════════════════════════════════════════════════ */
function ComparisonEarningsChart({ stocks }) {
  // Only stocks that have earnings data
  const withEarnings = stocks.filter(s => s.quarterly_earnings?.length)
  if (!withEarnings.length) return (
    <div style={{ color: '#2a5070', fontSize: 13, padding: '20px 0' }}>No quarterly earnings data available.</div>
  )

  // Collect all unique periods across all stocks (sorted oldest → newest)
  const periodsSet = new Set()
  withEarnings.forEach(s => s.quarterly_earnings.forEach(r => periodsSet.add(r.period)))
  const periods = Array.from(periodsSet).sort()

  const maxVal = Math.max(
    ...withEarnings.flatMap(s => s.quarterly_earnings.map(r => r.revenue ?? 0))
  )

  const BAR_W    = 16
  const GAP      = 4
  const GROUP_W  = (BAR_W + GAP) * withEarnings.length + 20
  const H        = 160
  const PAD      = { top: 20, bottom: 36, left: 52, right: 12 }
  const svgW     = PAD.left + periods.length * GROUP_W + PAD.right

  return (
    <div>
      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
        {withEarnings.map((s, i) => (
          <div key={s.ticker} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: PALETTE[stocks.indexOf(s) % PALETTE.length] }} />
            <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 700, color: PALETTE[stocks.indexOf(s) % PALETTE.length] }}>{s.ticker}</span>
            <span style={{ fontSize: 11, color: '#4a7090' }}>Revenue</span>
          </div>
        ))}
      </div>
      <svg width="100%" viewBox={`0 0 ${svgW} ${H + PAD.top + PAD.bottom}`} style={{ overflow: 'visible', display: 'block' }}>
        {[0, 0.25, 0.5, 0.75, 1].map(pct => {
          const y = PAD.top + H - pct * H
          return (
            <g key={pct}>
              <line x1={PAD.left} x2={svgW - PAD.right} y1={y} y2={y} stroke="#0e2038" strokeWidth="1" />
              <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="#2a5070" fontFamily="monospace">{fmtLarge(pct * maxVal)}</text>
            </g>
          )
        })}
        {periods.map((period, pi) => {
          const gx = PAD.left + pi * GROUP_W
          return (
            <g key={period}>
              {withEarnings.map((stock, si) => {
                const stockIdx = stocks.indexOf(stock)
                const row   = stock.quarterly_earnings.find(r => r.period === period)
                const barH  = row?.revenue && maxVal ? Math.max(2, row.revenue / maxVal * H) : 0
                const x     = gx + si * (BAR_W + GAP)
                return (
                  <rect key={stock.ticker} x={x} y={PAD.top + H - barH} width={BAR_W} height={barH}
                    fill={PALETTE[stockIdx % PALETTE.length]} rx="2" opacity="0.85" />
                )
              })}
              <text x={gx + ((BAR_W + GAP) * withEarnings.length) / 2} y={PAD.top + H + 14}
                textAnchor="middle" fontSize="9" fill="#2a5070" fontFamily="monospace">
                {period.slice(0, 7)}
              </text>
            </g>
          )
        })}
        <line x1={PAD.left} x2={svgW - PAD.right} y1={PAD.top + H} y2={PAD.top + H} stroke="#122840" strokeWidth="1" />
      </svg>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Tab button
══════════════════════════════════════════════════════════════ */
function Tab({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: '5px 14px', borderRadius: 6, border: 'none', cursor: 'pointer',
      fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
      background: active ? '#2070c0' : 'transparent',
      color:      active ? '#e8f4ff' : '#2a5070',
      transition: 'background 0.15s, color 0.15s',
    }}>
      {children}
    </button>
  )
}

/* ══════════════════════════════════════════════════════════════
   Main export — detects single vs comparison automatically
══════════════════════════════════════════════════════════════ */
export default function ChartPanel({ chartData }) {
  const isComparison = chartData.type === 'comparison'
  const [tab, setTab] = useState(isComparison ? 'performance' : 'price')

  /* ── Single stock ── */
  if (!isComparison) {
    const { ticker, company_name, currency, price_history, quarterly_earnings } = chartData
    const hasEarnings = quarterly_earnings?.length > 0
    return (
      <div style={{ marginTop: 10, borderRadius: 12, background: '#070e1c', border: '1px solid #0e2038', padding: '16px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.12em', color: '#60b4ff' }}>{ticker}</span>
            <span style={{ fontSize: 11, color: '#2a5070' }}>{company_name}</span>
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <Tab active={tab === 'price'} onClick={() => setTab('price')}>Price</Tab>
            {hasEarnings && <Tab active={tab === 'earnings'} onClick={() => setTab('earnings')}>Earnings</Tab>}
          </div>
        </div>
        {tab === 'price'    && <PriceChart priceHistory={price_history} ticker={ticker} currency={currency} />}
        {tab === 'earnings' && hasEarnings && <EarningsChart earnings={quarterly_earnings} />}
      </div>
    )
  }

  /* ── Comparison ── */
  const { stocks } = chartData
  const hasEarnings = stocks.some(s => s.quarterly_earnings?.length)
  const tickers     = stocks.map(s => s.ticker).join(' vs ')

  return (
    <div style={{ marginTop: 10, borderRadius: 12, background: '#070e1c', border: '1px solid #0e2038', padding: '16px 18px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.08em', color: '#8090b8' }}>
          {tickers}
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          <Tab active={tab === 'performance'} onClick={() => setTab('performance')}>Performance</Tab>
          <Tab active={tab === 'metrics'}     onClick={() => setTab('metrics')}>Metrics</Tab>
          {hasEarnings && <Tab active={tab === 'earnings'} onClick={() => setTab('earnings')}>Earnings</Tab>}
        </div>
      </div>
      {tab === 'performance' && <ComparisonLineChart stocks={stocks} />}
      {tab === 'metrics'     && <MetricsTable stocks={stocks} />}
      {tab === 'earnings'    && hasEarnings && <ComparisonEarningsChart stocks={stocks} />}
    </div>
  )
}
