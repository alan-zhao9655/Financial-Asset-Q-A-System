import { useState, useRef } from 'react'

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
  }

  function handleInput(e) {
    setValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const canSend = !!value.trim() && !disabled

  return (
    <div style={{ padding: '12px 16px 20px' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 8,
        borderRadius: 16, padding: '8px 8px 8px 16px',
        background: '#0a1828',
        border: `1px solid ${canSend ? '#2060a050' : '#122840'}`,
        boxShadow: canSend ? '0 0 0 1px #2060a018' : 'none',
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}>
        <textarea
          ref={ref}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask about a stock, concept, or market event…"
          rows={1}
          style={{
            flex: 1, resize: 'none', background: 'transparent',
            outline: 'none', border: 'none',
            color: '#c8e4f8',
            fontSize: 16,  /* 16px prevents iOS Safari auto-zoom */
            lineHeight: 1.5, fontFamily: 'inherit',
            padding: '6px 0', overflow: 'hidden',
          }}
        />
        <button
          onClick={submit}
          disabled={!canSend}
          style={{
            flexShrink: 0, width: 36, height: 36, marginBottom: 2,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderRadius: 10,
            background: canSend ? '#2070c0' : '#122840',
            color:      canSend ? '#e8f4ff' : '#1a3a60',
            border: 'none', cursor: canSend ? 'pointer' : 'not-allowed',
            boxShadow: canSend ? '0 0 14px #2070c055' : 'none',
            transition: 'background 0.2s, color 0.2s, box-shadow 0.2s',
          }}
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M1 7.5h13M8.5 2l6.5 5.5L8.5 13" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
      <p style={{
        textAlign: 'center', marginTop: 8,
        fontSize: 12, color: '#122840', letterSpacing: '0.05em',
      }}>
        FinQ · Claude Sonnet · Yahoo Finance · Tavily
      </p>
    </div>
  )
}
