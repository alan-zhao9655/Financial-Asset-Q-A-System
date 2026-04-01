const TICKERS = [
  { sym: 'AAPL',  val: '213.49', chg: '+1.24%', up: true  },
  { sym: 'TSLA',  val: '248.71', chg: '-0.83%', up: false },
  { sym: 'NVDA',  val: '875.32', chg: '+3.11%', up: true  },
  { sym: 'AMZN',  val: '192.68', chg: '+0.57%', up: true  },
  { sym: 'GOOGL', val: '178.40', chg: '-0.41%', up: false },
  { sym: 'MSFT',  val: '415.23', chg: '+0.93%', up: true  },
  { sym: 'META',  val: '529.14', chg: '+2.05%', up: true  },
  { sym: 'BABA',  val: '88.62',  chg: '-1.32%', up: false },
  { sym: 'BTC',   val: '68,420', chg: '+4.20%', up: true  },
  { sym: 'SPY',   val: '524.88', chg: '+0.34%', up: true  },
  { sym: 'GLD',   val: '224.15', chg: '-0.18%', up: false },
  { sym: 'TLT',   val: '92.40',  chg: '+0.11%', up: true  },
]

export default function TickerTape() {
  const items = [...TICKERS, ...TICKERS]
  return (
    <div style={{
      height: 34, flexShrink: 0,
      background: '#070e1c',
      borderBottom: '1px solid #0e2038',
      overflow: 'hidden',
      display: 'flex', alignItems: 'center',
    }}>
      <div className="ticker-track" style={{ alignItems: 'center' }}>
        {items.map((t, i) => (
          <span key={i} style={{
            display: 'inline-flex', alignItems: 'center',
            fontSize: 12, fontFamily: 'monospace',
          }}>
            <span style={{ color: '#5090c0', fontWeight: 700, letterSpacing: '0.06em', marginRight: 5 }}>
              {t.sym}
            </span>
            <span style={{ color: '#2a5070', marginRight: 5 }}>{t.val}</span>
            <span style={{ color: t.up ? '#4aa870' : '#a05050', fontWeight: 600 }}>
              {t.chg}
            </span>
            <span style={{ color: '#0e2038', margin: '0 12px' }}>|</span>
          </span>
        ))}
      </div>
    </div>
  )
}
