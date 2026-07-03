// Active alerts, timestamped. Shows a friendly "all clear" when empty.
function formatTime(iso) {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function AlertsPanel({ alerts }) {
  return (
    <div className="card alerts-card">
      <h2>
        Active Alerts
        {alerts.length > 0 && <span className="alert-count">{alerts.length}</span>}
      </h2>

      {alerts.length === 0 ? (
        <div className="all-clear">
          <span className="all-clear-icon">✅</span>
          <p>All clear — nothing left running out of hours.</p>
        </div>
      ) : (
        <ul className="alert-list">
          {alerts.map((a) => (
            <li key={a.id} className={`alert-item ${a.severity}`}>
              <span className="alert-badge">{a.severity === 'critical' ? '🔴' : '⚠️'}</span>
              <div className="alert-body">
                <p className="alert-message">{a.message}</p>
                <span className="alert-time">{a.room_name} · {formatTime(a.timestamp)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
