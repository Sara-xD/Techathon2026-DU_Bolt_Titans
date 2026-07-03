// One room's device panel: header summary + a grid of device chips.
// Fans spin and lights glow when ON.
function FanIcon({ on }) {
  return (
    <svg viewBox="0 0 24 24" className={`dev-icon fan ${on ? 'on' : ''}`} width="22" height="22">
      <g className="blades">
        <path d="M12 12 C12 6, 16 4, 18 6 C20 8, 16 10, 12 12" />
        <path d="M12 12 C18 12, 20 16, 18 18 C16 20, 14 16, 12 12" />
        <path d="M12 12 C12 18, 8 20, 6 18 C4 16, 8 14, 12 12" />
        <path d="M12 12 C6 12, 4 8, 6 6 C8 4, 10 8, 12 12" />
      </g>
      <circle cx="12" cy="12" r="1.6" className="hub" />
    </svg>
  )
}

function LightIcon({ on }) {
  return (
    <svg viewBox="0 0 24 24" className={`dev-icon light ${on ? 'on' : ''}`} width="22" height="22">
      <circle cx="12" cy="10" r="6" className="bulb" />
      <rect x="9" y="16" width="6" height="3" rx="1" className="base" />
    </svg>
  )
}

export default function RoomPanel({ room }) {
  return (
    <div className="room-panel">
      <div className="room-head">
        <h3>{room.room_name}</h3>
        <span className="room-power">{room.power} W</span>
      </div>
      <div className="room-summary">
        <span>🌀 {room.fans_on}/{room.fans_total} fans</span>
        <span>💡 {room.lights_on}/{room.lights_total} lights</span>
      </div>

      <div className="device-grid">
        {room.devices.map((dev) => (
          <div key={dev.id} className={`device-chip ${dev.status ? 'on' : 'off'}`}>
            {dev.type === 'fan' ? <FanIcon on={dev.status} /> : <LightIcon on={dev.status} />}
            <div className="device-meta">
              <span className="device-label">{dev.label}</span>
              <span className="device-state">{dev.status ? `${dev.power} W` : 'off'}</span>
            </div>
            <span className={`state-dot ${dev.status ? 'on' : 'off'}`} />
          </div>
        ))}
      </div>
    </div>
  )
}
