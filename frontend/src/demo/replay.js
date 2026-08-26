/**
 * Replay a recorded session in place of the backend.
 *
 * GitHub Pages serves static files only, so the published demo has no FastAPI,
 * no AQUA-1B and no pgvector behind it. This intercepts `fetch` and answers the
 * same five endpoints from `public/demo-session.json`, advancing a cursor
 * through the recording on the same 2 s cadence the real sensor loop uses.
 *
 * The interception sits at the fetch layer on purpose: no component knows it is
 * in demo mode, so the code path the demo exercises is the code path that ships.
 *
 * Nothing here invents data. Every value was produced by the real detector, the
 * real rule engine and the real retrieval — see scripts/build_demo_fixture.py.
 * The one thing the replay cannot do is answer a question it has no recording
 * of, so chat returns an explicit refusal rather than a plausible-looking reply.
 */

const POLL_MS = 2000
const WINDOW = 60 // readings kept in the rolling history, matching the dashboard

let session = null
let startedAt = 0

export const isDemo = import.meta.env.VITE_DEMO === '1'

function cursor() {
  if (!session) return 0
  const elapsed = Date.now() - startedAt
  return Math.floor(elapsed / POLL_MS) % session.steps.length
}

function json(body) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

function sliceUpTo(i) {
  const from = Math.max(0, i - WINDOW + 1)
  return session.steps.slice(from, i + 1)
}

function handle(url) {
  const i = cursor()
  const step = session.steps[i]
  const window = sliceUpTo(i)

  if (url.startsWith('/api/history')) {
    return json({
      sensor: window.map(s => s.sensor).filter(Boolean),
      vision: window.map(s => s.vision).filter(Boolean),
    })
  }

  if (url.startsWith('/api/state')) {
    return json({ sensor: step.sensor ?? null, vision: step.vision ?? null })
  }

  if (url.startsWith('/api/decision/history')) {
    return json(
      window.map(s => ({ status: s.decision.status, timestamp: s.timestamp })),
    )
  }

  if (url.startsWith('/api/decision')) {
    return json(step.decision)
  }

  if (url.startsWith('/api/chat')) {
    // An honest refusal. Generating a reply here would be inventing model output.
    const body =
      'Bu sayfa kayıtlı bir oturumu oynatıyor; sohbet için modelin çalışıyor ' +
      'olması gerekiyor. Gerçek sistemi çalıştırmak için depodaki kurulum ' +
      'adımlarını izleyebilir veya Codespaces ile açabilirsin.'
    return Promise.resolve(
      new Response(
        `data: ${JSON.stringify({ token: body })}\n\ndata: [DONE]\n\n`,
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
      ),
    )
  }

  return null
}

export async function installReplay() {
  if (!session) {
    const base = import.meta.env.BASE_URL || '/'
    const res = await fetch(`${base}demo-session.json`)
    session = await res.json()
    startedAt = Date.now()
  }

  const original = window.fetch.bind(window)
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : input?.url ?? ''
    if (url.startsWith('/api/')) {
      const answer = handle(url)
      if (answer) return answer
    }
    return original(input, init)
  }

  return session.meta
}

export function sessionMeta() {
  return session?.meta ?? null
}

export function progress() {
  if (!session) return { index: 0, total: 0 }
  return { index: cursor() + 1, total: session.steps.length }
}
