import ReactMarkdown from 'react-markdown'

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

export default function AnswerCard({ text, queryType, ticker }) {
  const sections = parseSections(text)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%' }}>
      {ticker && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
          <span style={{
            fontSize: 12, fontFamily: 'monospace', fontWeight: 700,
            letterSpacing: '0.1em', padding: '2px 8px', borderRadius: 4,
            color: '#60b4ff', background: '#60b4ff18', border: '1px solid #60b4ff35',
          }}>
            {ticker}
          </span>
          <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#2a5070' }}>
            {queryType === 'market' ? 'Market Analysis' : 'Knowledge Base'}
          </span>
        </div>
      )}
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
