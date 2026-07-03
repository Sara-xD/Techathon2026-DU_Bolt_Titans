// BONUS: top-view office layout. Lights glow when ON, fans spin when running.
// Positions mirror the office floor plan (Drawing Room + two work rooms).

function FloorFan({ x, y, on }) {
  return (
    <g transform={`translate(${x}, ${y})`} className={`floor-fan ${on ? 'on' : ''}`}>
      <circle r="30" className="fan-ring" />
      <g className="fan-blades">
        <ellipse cx="0" cy="-14" rx="7" ry="15" />
        <ellipse cx="14" cy="0" rx="15" ry="7" />
        <ellipse cx="0" cy="14" rx="7" ry="15" />
        <ellipse cx="-14" cy="0" rx="15" ry="7" />
      </g>
      <circle r="4" className="fan-hub" />
    </g>
  )
}

function FloorLight({ x, y, on }) {
  return (
    <g transform={`translate(${x}, ${y})`} className={`floor-light ${on ? 'on' : ''}`}>
      <circle r="15" className="light-halo" />
      <circle r="9" className="light-bulb" />
    </g>
  )
}

function Room({ x, width, name, devices }) {
  const fans = devices.filter((d) => d.type === 'fan')
  const lights = devices.filter((d) => d.type === 'light')
  const fanY = 118
  const lightY = 250

  return (
    <g>
      <rect x={x} y={40} width={width} height={330} rx="6" className="room-rect" />
      <text x={x + width / 2} y={64} className="room-title">{name}</text>

      {fans.map((f, i) => (
        <FloorFan
          key={f.id}
          x={x + (width * (i + 1)) / (fans.length + 1)}
          y={fanY}
          on={f.status}
        />
      ))}
      {lights.map((l, i) => (
        <FloorLight
          key={l.id}
          x={x + (width * (i + 1)) / (lights.length + 1)}
          y={lightY}
          on={l.status}
        />
      ))}
    </g>
  )
}

export default function FloorPlan({ rooms }) {
  // Give the Drawing Room a little more width, like the real layout.
  const widths = { drawing: 340, work1: 275, work2: 275 }
  let cursor = 15
  const placed = rooms.map((room) => {
    const w = widths[room.room] || 275
    const node = { room, x: cursor, width: w }
    cursor += w + 10
    return node
  })

  return (
    <div className="card floorplan-card">
      <div className="floorplan-head">
        <h2>Office Layout — Top View</h2>
        <div className="legend">
          <span className="legend-item"><span className="legend-swatch fan-on" /> fan running</span>
          <span className="legend-item"><span className="legend-swatch light-on" /> light on</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${cursor} 400`} className="floorplan-svg" preserveAspectRatio="xMidYMid meet">
        <rect x="5" y="30" width={cursor - 10} height="350" rx="10" className="office-wall" />
        {placed.map(({ room, x, width }) => (
          <Room key={room.room} x={x} width={width} name={room.room_name} devices={room.devices} />
        ))}
      </svg>
    </div>
  )
}
