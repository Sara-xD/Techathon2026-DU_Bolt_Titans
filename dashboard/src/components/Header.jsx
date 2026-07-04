// Top bar: branding, live simulated clock, office-hours badge, connection state.
export default function Header({ simTime, connected }) {
  const d = new Date(simTime)
  const hour = d.getHours()
  const officeHours = hour >= 9 && hour < 17
  const time = d.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const date = d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })

  return (
    <header className="topbar">
      <div className="brand">
        <span className="logo">⚡</span>
        <div>
          <h1>Office Energy Monitor</h1>
          <p>Live device &amp; power monitoring · 3 rooms · 15 devices</p>
        </div>
      </div>

      <div className="topbar-right">
        <div className={`badge ${officeHours ? 'open' : 'closed'}`}>
          {officeHours ? '🟢 Office Hours' : '🌙 After Hours'}
        </div>
        <div className="clock">
          <span className="clock-time">{time}</span>
          <span className="clock-date">{date}</span>
        </div>
        <div className={`conn ${connected ? 'on' : 'off'}`}>
          <span className="dot" />
          {connected ? 'Live' : 'Reconnecting…'}
        </div>
      </div>
    </header>
  )
}
