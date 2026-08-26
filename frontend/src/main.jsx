import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import DemoBanner from './demo/DemoBanner.jsx'
import { installReplay, isDemo } from './demo/replay.js'

const root = createRoot(document.getElementById('root'))

function render(banner) {
  root.render(
    <StrictMode>
      {banner}
      <App />
    </StrictMode>,
  )
}

if (isDemo) {
  // The replay shim must be installed before App mounts, otherwise its first
  // fetch escapes to a backend that does not exist on Pages and the dashboard
  // renders its disconnected state for two seconds before recovering.
  installReplay()
    .then(() => render(<DemoBanner />))
    .catch(err => {
      console.error('demo fixture could not be loaded', err)
      render(null)
    })
} else {
  render(null)
}
