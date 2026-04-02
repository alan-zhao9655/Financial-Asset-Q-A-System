import AnswerCard from './AnswerCard'

const Avatar = () => (
  <div style={{
    width: 28, height: 28, borderRadius: '50%', flexShrink: 0, marginTop: 2,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: '#050a14', border: '1px solid #2060a035',
  }}>
    <span style={{ color: '#60b4ff', fontSize: 12, lineHeight: 1 }}>◈</span>
  </div>
)

export default function ChatMessage({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="msg-enter" style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{
          maxWidth: '72%', padding: '10px 16px',
          borderRadius: '16px 16px 4px 16px',
          background: 'linear-gradient(135deg, #0d2040, #081428)',
          border: '1px solid #2060a025',
          fontSize: 14, color: '#c8e4f8', lineHeight: 1.6,
        }}>
          {msg.content}
        </div>
      </div>
    )
  }

  if (msg.role === 'assistant-clarify') {
    return (
      <div className="msg-enter" style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <Avatar />
        <div style={{
          maxWidth: '78%', padding: '12px 16px',
          borderRadius: '16px 16px 16px 4px',
          background: '#0a1828', border: '1px solid #122840',
          fontSize: 14, color: '#a8c8e8', lineHeight: 1.7,
        }}>
          {msg.content}
        </div>
      </div>
    )
  }

  if (msg.role === 'assistant-answer') {
    return (
      <div className="msg-enter" style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <Avatar />
        <div style={{ flex: 1, minWidth: 0 }}>
          <AnswerCard
            text={msg.content}
            queryType={msg.queryType}
            ticker={msg.ticker}
            chartData={msg.chartData}
          />
        </div>
      </div>
    )
  }

  return null
}
