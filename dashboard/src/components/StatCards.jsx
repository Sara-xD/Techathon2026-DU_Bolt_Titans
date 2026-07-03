// Four at-a-glance KPI cards across the top of the dashboard.
export default function StatCards({ usage, devicesOn, totalDevices, alertCount }) {
  const cards = [
    {
      label: 'Total Power Draw',
      value: `${usage.total_watts} W`,
      icon: '⚡',
      tone: 'blue',
    },
    {
      label: "Today's Usage",
      value: `${usage.today_kwh} kWh`,
      icon: '📊',
      tone: 'violet',
    },
    {
      label: 'Devices On',
      value: `${devicesOn} / ${totalDevices}`,
      icon: '💡',
      tone: 'green',
    },
    {
      label: 'Active Alerts',
      value: alertCount,
      icon: alertCount > 0 ? '⚠️' : '✅',
      tone: alertCount > 0 ? 'red' : 'green',
    },
  ]

  return (
    <div className="stat-cards">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card ${c.tone}`}>
          <span className="stat-icon">{c.icon}</span>
          <div className="stat-body">
            <span className="stat-value">{c.value}</span>
            <span className="stat-label">{c.label}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
