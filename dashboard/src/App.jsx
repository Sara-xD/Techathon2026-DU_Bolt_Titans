import { useLiveState } from './useLiveState'
import Header from './components/Header'
import StatCards from './components/StatCards'
import FloorPlan from './components/FloorPlan'
import RoomPanel from './components/RoomPanel'
import PowerBreakdown from './components/PowerBreakdown'
import AlertsPanel from './components/AlertsPanel'

export default function App() {
  const { state, connected } = useLiveState()

  if (!state) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Connecting to the office backend…</p>
        <small>Make sure the backend is running on port 8000.</small>
      </div>
    )
  }

  const devicesOn = state.devices.filter((d) => d.status).length

  return (
    <div className="app">
      <Header simTime={state.sim_time} connected={connected} />

      <StatCards
        usage={state.usage}
        devicesOn={devicesOn}
        totalDevices={state.devices.length}
        alertCount={state.alerts.length}
      />

      <div className="main-grid">
        <section className="col-left">
          <FloorPlan rooms={state.rooms} />
          <div className="rooms-row">
            {state.rooms.map((room) => (
              <RoomPanel key={room.room} room={room} />
            ))}
          </div>
        </section>

        <aside className="col-right">
          <PowerBreakdown usage={state.usage} rooms={state.rooms} />
          <AlertsPanel alerts={state.alerts} />
        </aside>
      </div>
    </div>
  )
}
