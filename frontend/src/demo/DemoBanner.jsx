import { useEffect, useState } from 'react'
import { progress, sessionMeta } from './replay'

/**
 * States plainly that the page is a replay.
 *
 * This is not a disclaimer bolted on at the end — it is the reason the demo is
 * publishable at all. A dashboard that looks live while replaying a recording,
 * without saying so, misrepresents what the system did. The banner is always
 * visible, never dismissible, and names where each number came from.
 */
export default function DemoBanner() {
  const meta = sessionMeta()
  const [pos, setPos] = useState(progress())
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const id = setInterval(() => setPos(progress()), 1000)
    return () => clearInterval(id)
  }, [])

  if (!meta) return null
  const p = meta.provenance ?? {}

  return (
    <div className="w-full bg-amber-500/10 border-b border-amber-500/30 text-amber-100">
      <div className="max-w-7xl mx-auto px-4 py-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="font-semibold tracking-wide text-amber-300">KAYIT TEKRARI</span>
        <span className="text-amber-100/80">
          Bu sayfa canlı çıkarım yapmıyor — kaydedilmiş bir oturumu oynatıyor.
        </span>
        <span className="font-mono text-xs text-amber-200/70">
          adım {pos.index}/{pos.total}
        </span>
        <button
          onClick={() => setOpen(v => !v)}
          className="ml-auto text-xs underline underline-offset-2 text-amber-200 hover:text-amber-100"
        >
          {open ? 'gizle' : 'veri nereden geliyor?'}
        </button>
      </div>

      {open && (
        <div className="max-w-7xl mx-auto px-4 pb-3 text-xs text-amber-100/85 space-y-1">
          <p>
            GitHub Pages yalnızca statik dosya sunar; FastAPI, AQUA-1B ve pgvector
            burada çalışmaz. Aşağıdaki değerlerin tamamı gerçek bileşenlerle
            önceden üretildi (<code className="font-mono">scripts/build_demo_fixture.py</code>):
          </p>
          <ul className="list-disc pl-5 space-y-0.5">
            <li><b>Sensörler:</b> {p.sensors}</li>
            <li><b>Görü:</b> {p.vision}</li>
            <li><b>Kararlar:</b> {p.decisions}</li>
            <li><b>Gerekçe:</b> {p.narration}</li>
            <li><b>Alıntılar:</b> {p.citations}</li>
          </ul>
          <p className="pt-1">
            Kamera görüntüsü tek bir kaydedilmiş karedir, canlı akış değildir.
            Sohbet yanıt vermez — modelin çalışıyor olması gerekir.
          </p>
        </div>
      )}
    </div>
  )
}
