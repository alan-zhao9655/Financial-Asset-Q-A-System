import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ChartPanel from './ChartPanel'

function parseSections(text) {
  const lines = text.split('\n')
  const sections = []
  let current = null
  for (const line of lines) {
    const m = line.match(/^#{1,3}\s+(.+)/)
    if (m) {
      if (current) sections.push(current)
      current = { heading: m[1].trim(), body: [] }
    } else if (current) {
      current.body.push(line)
    } else {
      if (!current) current = { heading: null, body: [] }
      current.body.push(line)
    }
  }
  if (current) sections.push(current)
  if (sections.length === 0) sections.push({ heading: null, body: lines })
  return sections
}

const SECTION_META = {
  'Objective Data': { color: '#60b4ff', bg: '#60b4ff0d', border: '#60b4ff22', delay: 'section-enter-delay-1' },
  'Analysis':       { color: '#4ad4b0', bg: '#4ad4b00d', border: '#4ad4b022', delay: 'section-enter-delay-2' },
  'Key Facts':      { color: '#60b4ff', bg: '#60b4ff0d', border: '#60b4ff22', delay: 'section-enter-delay-1' },
  'Explanation':    { color: '#4ad4b0', bg: '#4ad4b00d', border: '#4ad4b022', delay: 'section-enter-delay-2' },
  'Summary':        { color: '#8090b8', bg: '#8090b80d', border: '#8090b822', delay: 'section-enter-delay-3' },
  default:          { color: '#2a5070', bg: '#2a50700d', border: '#2a507022', delay: '' },
}

function getMeta(heading) {
  if (!heading) return SECTION_META.default
  for (const key of Object.keys(SECTION_META)) {
    if (key === 'default') continue
    if (heading.toLowerCase().includes(key.toLowerCase())) return SECTION_META[key]
  }
  return SECTION_META.default
}

export default function AnswerCard({ text, queryType, ticker, chartData }) {
  const [showChart, setShowChart] = useState(false)
  const sections = parseSections(text)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%' }}>
      {/* Header row: ticker badge + chart toggle */}
      {ticker && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              fontSize: 12, fontFamily: 'monospace', fontWeight: 700,
              letterSpacing: '0.1em', padding: '2px 8px', borderRadius: 4,
              color: '#60b4ff', background: '#60b4ff18', border: '1px solid #60b4ff35',
            }}>
              {ticker}
            </span>
            <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#2a5070' }}>
              {queryType === 'market' ? 'Market Analysis' : queryType === 'comparison' ? 'Comparison' : 'Knowledge Base'}
            </span>
          </div>
          {chartData && (
            <button
              onClick={() => setShowChart(s => !s)}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '4px 12px', borderRadius: 6, cursor: 'pointer',
                fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
                background: showChart ? '#2070c0'    : '#2070c018',
                color:      showChart ? '#e8f4ff'    : '#2070c0',
                border:     `1px solid ${showChart ? '#2070c0' : '#2070c040'}`,
                transition: 'background 0.2s, color 0.2s',
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <rect x="1" y="7" width="2" height="4" rx="0.5" fill="currentColor" opacity="0.6"/>
                <rect x="5" y="4" width="2" height="7" rx="0.5" fill="currentColor" opacity="0.8"/>
                <rect x="9" y="1" width="2" height="10" rx="0.5" fill="currentColor"/>
              </svg>
              {showChart ? 'Hide Chart' : 'View Chart'}
            </button>
          )}
        </div>
      )}

      {/* Chart panel */}
      {showChart && chartData && <ChartPanel chartData={chartData} />}

      {/* Answer sections */}
      {sections.map((sec, i) => {
        const meta = getMeta(sec.heading)
        const body = sec.body.join('\n').trim()
        if (!body) return null
        return (
          <div key={i} className={`section-enter ${meta.delay}`} style={{
            borderRadius: 10, padding: '14px 16px',
            background: meta.bg, border: `1px solid ${meta.border}`,
          }}>
            {sec.heading && (
              <div style={{
                fontSize: 12, fontWeight: 700, letterSpacing: '0.14em',
                textTransform: 'uppercase', color: meta.color, marginBottom: 10,
              }}>
                {sec.heading}
              </div>
            )}
            <div className="answer-body">
              <ReactMarkdown>{body}</ReactMarkdown>
            </div>
          </div>
        )
      })}
    </div>
  )
}
