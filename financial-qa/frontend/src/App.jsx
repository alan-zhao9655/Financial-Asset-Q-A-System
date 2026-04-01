import { useState, useRef, useEffect, useCallback, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { motion, AnimatePresence } from 'framer-motion'
import FinancialGlobe from './components/FinancialGlobe'
import ChatMessage    from './components/ChatMessage'
import InputBar       from './components/InputBar'
import TickerTape     from './components/TickerTape'

const HISTORY_COMPRESS_AT = 12
const HISTORY_KEEP_RECENT = 6
const SCROLL_THRESHOLD    = 120
const TICKER_H   = 34   // TickerTape height px
const GLOBE_CHAT = 172  // Globe height when chat is open px

const WELCOME = {
  role: 'assistant-clarify',
  content: "Hello! I'm FinQ — your financial intelligence assistant. Ask me about any stock's performance, or ask me to explain a financial concept. You don't need to know the ticker symbol — just describe the company or topic.",
  id: 'welcome',
}

export default function App() {
  const [isChatActive, setIsChatActive] = useState(false)
  const [messages, setMessages]             = useState([WELCOME])
  const [history, setHistory]               = useState([])
  const [historySummary, setHistorySummary] = useState(null)
  const [orbState, setOrbState]             = useState('idle')
  const [isLoading, setIsLoading]           = useState(false)
  const [showScrollBtn, setShowScrollBtn]   = useState(false)

  /* Measure actual viewport so we always animate between two concrete pixel heights */
  const [vpHeight, setVpHeight] = useState(window.innerHeight)
  useEffect(() => {
    const onResize = () => setVpHeight(window.innerHeight)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const inputBarRef = useRef(null)
  const [inputBarH, setInputBarH] = useState(80)
  useEffect(() => {
    if (!inputBarRef.current) return
    const ro = new ResizeObserver(entries => {
      setInputBarH(entries[0].contentRect.height)
    })
    ro.observe(inputBarRef.current)
    return () => ro.disconnect()
  }, [])

  /* Landing globe height = full viewport minus ticker minus input bar */
  const globeLandingH = vpHeight - TICKER_H - inputBarH

  const chatRef   = useRef(null)
  const bottomRef = useRef(null)

  const scrollToBottom = useCallback((force = false) => {
    const el = chatRef.current
    if (!el) return
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight
    if (force || dist < SCROLL_THRESHOLD) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      setShowScrollBtn(false)
    } else {
      setShowScrollBtn(true)
    }
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, isLoading, scrollToBottom])

  function handleScroll() {
    const el = chatRef.current
    if (!el) return
    if (el.scrollHeight - el.scrollTop - el.clientHeight < SCROLL_THRESHOLD)
      setShowScrollBtn(false)
  }

  async function compressHistoryIfNeeded(hist, summary) {
    if (hist.length <= HISTORY_COMPRESS_AT) return { hist, summary }
    const toCompress = hist.slice(0, -HISTORY_KEEP_RECENT)
    const recent     = hist.slice(-HISTORY_KEEP_RECENT)
    try {
      const res  = await fetch('/api/summarize-history', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: toCompress }),
      })
      const data = await res.json()
      return { hist: recent, summary: data.summary }
    } catch {
      return { hist, summary }
    }
  }

  async function handleSend(text) {
    if (!isChatActive) setIsChatActive(true)
    setMessages(prev => [...prev, { role: 'user', content: text, id: Date.now() }])
    setIsLoading(true)
    setOrbState('thinking')

    const { hist: compressedHist, summary: compressedSummary } =
      await compressHistoryIfNeeded(history, historySummary)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text, history: compressedHist, history_summary: compressedSummary,
        }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()

      setHistory([
        ...compressedHist,
        { role: 'user',      content: text },
        { role: 'assistant', content: data.message },
      ])
      setHistorySummary(compressedSummary)

      if (data.type === 'clarify') {
        setOrbState('idle')
        setMessages(prev => [...prev, {
          role: 'assistant-clarify', content: data.message, id: Date.now() + 1,
        }])
      } else {
        const qType = data.query_type || 'knowledge'
        setOrbState(qType)
        setMessages(prev => [...prev, {
          role: 'assistant-answer', content: data.message,
          queryType: qType, ticker: data.ticker, id: Date.now() + 1,
        }])
        setTimeout(() => setOrbState('idle'), 4000)
      }
    } catch (err) {
      setOrbState('idle')
      setMessages(prev => [...prev, {
        role: 'assistant-clarify',
        content: `Something went wrong: ${err.message}. Please try again.`,
        id: Date.now() + 1,
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const statusLabel = orbState === 'thinking'    ? 'Analysing...'
                    : orbState === 'market'       ? 'Market Data'
                    : orbState === 'knowledge'    ? 'Knowledge'
                    : 'Ready'

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: '#050a14',
      overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* ── Ticker tape ── */}
      <TickerTape />

      {/* ── Globe panel — Canvas NEVER unmounts.
           Animates between two concrete pixel heights so the Canvas
           always knows exactly how tall it is. ── */}
      <motion.div
        animate={{ height: isChatActive ? GLOBE_CHAT : globeLandingH }}
        transition={{ type: 'spring', stiffness: 68, damping: 20 }}
        style={{
          flexShrink: 0,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Radial glow behind the globe */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none',
          background: 'radial-gradient(ellipse 60% 55% at 50% 50%, #0d2848 0%, #050a14 72%)',
        }} />

        {/* Canvas fills the container absolutely — no ambiguity about its size */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 1 }}>
          <Canvas
            camera={{ position: [0, 0.3, 4.5], fov: 44 }}
            style={{ width: '100%', height: '100%' }}
            gl={{ antialias: true, alpha: true }}
          >
            <Suspense fallback={null}>
              <FinancialGlobe
                onQuestionClick={text => handleSend(text)}
                showQuestions={!isChatActive}
              />
            </Suspense>
          </Canvas>
        </div>

        {/* Landing: brand + hint */}
        <AnimatePresence>
          {!isChatActive && (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.38 }}
              style={{
                position: 'absolute', bottom: 28, left: 0, right: 0,
                textAlign: 'center', pointerEvents: 'none', zIndex: 2,
              }}
            >
              <div style={{
                fontSize: 11, fontFamily: 'monospace', fontWeight: 700,
                letterSpacing: '0.32em', textTransform: 'uppercase',
                color: '#60b4ff', marginBottom: 10,
                textShadow: '0 0 16px #2080c060',
              }}>
                FinQ
              </div>
              <h1 style={{
                fontSize: 24, fontWeight: 300, color: '#c8e4f8',
                letterSpacing: '0.07em', margin: '0 0 8px',
              }}>
                Financial Intelligence
              </h1>
              <p style={{ fontSize: 13, color: '#2a5070', letterSpacing: '0.04em', margin: 0 }}>
                Type a question below to begin
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat state: compact status bar */}
        <AnimatePresence>
          {isChatActive && (
            <motion.div
              key="chat-header"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute', bottom: 8, left: 0, right: 0,
                textAlign: 'center', pointerEvents: 'none', zIndex: 2,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
              }}
            >
              <span style={{
                fontSize: 12, fontFamily: 'monospace', fontWeight: 700,
                color: '#60b4ff', letterSpacing: '0.26em', textTransform: 'uppercase',
                textShadow: '0 0 10px #2080c050',
              }}>
                FinQ
              </span>
              <span style={{ width: 1, height: 10, background: '#122840', display: 'inline-block' }} />
              <span style={{ fontSize: 12, color: '#2a5070', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                {statusLabel}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Landing input bar — sits below the globe, never overlaps ── */}
      {!isChatActive && (
        <div ref={inputBarRef} style={{ flexShrink: 0, zIndex: 20 }}>
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <InputBar onSend={handleSend} disabled={isLoading} />
          </div>
        </div>
      )}

      {/* ── Chat panel ── */}
      <AnimatePresence>
        {isChatActive && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            style={{
              flex: 1, minHeight: 0,
              display: 'flex', flexDirection: 'column',
              maxWidth: 720, width: '100%',
              margin: '0 auto', position: 'relative', zIndex: 10,
            }}
          >
            <div style={{
              height: 1, flexShrink: 0,
              background: 'linear-gradient(90deg, transparent, #2060a020, transparent)',
            }} />

            <div
              ref={chatRef}
              onScroll={handleScroll}
              className="chat-scroll"
              style={{
                flex: 1, minHeight: 0, overflowY: 'auto',
                padding: '20px 16px 16px',
                display: 'flex', flexDirection: 'column', gap: 16,
              }}
            >
              {messages.map(msg => (
                <ChatMessage key={msg.id} msg={msg} />
              ))}

              {isLoading && (
                <div className="msg-enter" style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%', flexShrink: 0, marginTop: 2,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: '#050a14', border: '1px solid #2060a030',
                  }}>
                    <span style={{ color: '#60b4ff', fontSize: 12 }}>◈</span>
                  </div>
                  <div style={{
                    display: 'flex', alignItems: 'flex-end', gap: 4,
                    borderRadius: 14, padding: '12px 16px',
                    background: '#0a1828', border: '1px solid #122840',
                  }}>
                    {[10, 16, 11, 14, 9].map((h, i) => (
                      <div key={i} className="candle-bar" style={{
                        width: 3, height: h, borderRadius: 2, background: '#3a90d0',
                      }} />
                    ))}
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {showScrollBtn && (
              <button
                onClick={() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); setShowScrollBtn(false) }}
                style={{
                  position: 'absolute', bottom: 92, left: '50%', transform: 'translateX(-50%)',
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: '#2070c0', color: '#e8f4ff',
                  fontSize: 12, fontWeight: 700, letterSpacing: '0.04em',
                  padding: '6px 16px', borderRadius: 20,
                  border: 'none', cursor: 'pointer', zIndex: 20,
                  boxShadow: '0 4px 16px rgba(32,112,192,0.45)',
                }}
              >
                ↓ New message
              </button>
            )}

            <div style={{ flexShrink: 0 }}>
              <InputBar onSend={handleSend} disabled={isLoading} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
