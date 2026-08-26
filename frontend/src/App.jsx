import { useState, useEffect, useRef, useCallback } from 'react'
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'
import {
  Fish, Droplets, Thermometer, Wind, Activity, Brain,
  AlertTriangle, CheckCircle, XCircle,
  Radio, Send, Bot, User, Zap, Eye, BellOff
} from 'lucide-react'
import './index.css'

// ─── sabitler ────────────────────────────────────────────────────────────────
const POLL_MS     = 2000
const HISTORY_URL = '/api/history'
const STATE_URL   = '/api/state'
const DECISION_URL= '/api/decision'
const DECISION_MS = 8000   // karar motoru daha az sıklıkta çağrılır
// 8sn'de bir karar → 450 karar ≈ 1 saat. Şerit 60 kare gösterir, sayım tümünü kullanır.
const DECISION_HISTORY_MAX = 500

// ─── yardımcı ────────────────────────────────────────────────────────────────
const fmtTime = iso => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`
}

const statusColors = {
  ok:       { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', icon: CheckCircle },
  warning:  { bg: 'bg-amber-500/15',   border: 'border-amber-500/40',   text: 'text-amber-400',   icon: AlertTriangle },
  critical: { bg: 'bg-red-500/15',     border: 'border-red-500/40',     text: 'text-red-400',     icon: XCircle },
}

// ─── bileşenler ──────────────────────────────────────────────────────────────

/* Kritik DO uyarısı — kapanabilir, 30 sn sonra yeniden açılır */
function useDismissable(resetMs = 30000) {
  const [dismissed, setDismissed] = useState(false)
  const timerRef = useRef(null)
  const dismiss = () => {
    setDismissed(true)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setDismissed(false), resetMs)
  }
  useEffect(() => () => clearTimeout(timerRef.current), [])
  return [dismissed, dismiss]
}

function CriticalAlertBanner({ do: doValue, onDismiss }) {
  return (
    <div className="relative mb-4 rounded-xl overflow-hidden border-2 border-red-500"
         role="alert"
         aria-live="assertive"
         style={{ boxShadow: '0 0 32px rgba(239,68,68,0.5), inset 0 0 20px rgba(239,68,68,0.08)' }}>
      <div className="absolute inset-0 bg-red-500/10 animate-pulse pointer-events-none" />
      <div className="relative flex items-center gap-3 px-4 py-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-full bg-red-500/20 border border-red-500/50 shrink-0">
          <AlertTriangle size={18} className="text-red-400 animate-bounce" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-black uppercase tracking-widest text-red-400">
            KRİTİK — Çözünmüş Oksijen Tehlikeli Düzeyde Düşük
          </div>
          <div className="text-xs text-red-300/80 mt-0.5">
            DO: <span className="font-bold font-mono">{doValue} mg/L</span>
            <span className="text-red-500 mx-2">|</span>
            Güvenli alt sınır: 6,0 mg/L
            <span className="text-red-500 mx-2">|</span>
            Havalandırmayı derhal artır, yemlemeyi durdur
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider text-red-400/60 hover:text-red-300 hover:bg-red-500/15 border border-red-500/20 transition-colors shrink-0"
          title="30 saniye sessize al"
        >
          <BellOff size={11} /> 30s
        </button>
      </div>
    </div>
  )
}

/* Bölüm başlığı */
function SectionLabel({ children }) {
  return (
    <div className="flex items-center gap-2 mb-0.5">
      <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-500/70">{children}</span>
      <div className="flex-1 h-px bg-gradient-to-r from-cyan-500/20 to-transparent" />
    </div>
  )
}

function StatCard({ icon: Icon, label, value, unit, color, sub, alert }) {
  return (
    <div className={`neon-card glow-border corner-tl corner-br p-4 flex flex-col gap-1.5 relative ${alert ? 'glow-border-critical' : ''}`}>
      <div className="scan-line" />
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-slate-500">
        <Icon size={12} className={color} />
        {label}
      </div>
      <div className={`text-3xl font-black tracking-tight ${color}`} style={{ fontVariantNumeric: 'tabular-nums' }}>
        {value ?? <span className="text-slate-700">—</span>}
        <span className="text-sm font-normal text-slate-500 ml-1">{unit}</span>
      </div>
      {sub && (
        <div className={`text-[11px] ${alert ? 'text-red-400 font-semibold' : 'text-slate-600'}`}>
          {sub}
        </div>
      )}
    </div>
  )
}

function SensorChart({ data, dataKey, label, color, unit, refLines = [] }) {
  const sliced = data.slice(-60)
  return (
    <div className="neon-card glow-border p-4">
      <div className="text-[11px] font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
        {label}
        <span className="text-slate-700 font-normal">/ {unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <AreaChart data={sliced} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
          <defs>
            <linearGradient id={`g-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 4" stroke="rgba(0,180,255,0.06)" />
          <XAxis dataKey="t" tick={{ fontSize: 8, fill: '#334155' }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 8, fill: '#334155' }} domain={['auto', 'auto']} />
          {refLines.map(r => (
            <ReferenceLine key={r.v} y={r.v} stroke={r.color} strokeDasharray="4 3" strokeWidth={1} />
          ))}
          <Tooltip
            contentStyle={{ background: 'rgba(2,5,16,0.95)', border: `1px solid ${color}40`, borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: '#64748b' }}
            itemStyle={{ color }}
            formatter={v => [`${v} ${unit}`, label]}
          />
          <Area type="monotone" dataKey={dataKey} stroke={color} fill={`url(#g-${dataKey})`} strokeWidth={2} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function FishActivityChart({ data }) {
  const sliced = data.slice(-60)
  return (
    <div className="neon-card glow-border p-4">
      <div className="text-[11px] font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 6px #22d3ee' }} />
          Balık Sayısı
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400" style={{ boxShadow: '0 0 6px #a78bfa' }} />
          Aktivite
        </span>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <LineChart data={sliced} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="rgba(0,180,255,0.06)" />
          <XAxis dataKey="t" tick={{ fontSize: 8, fill: '#334155' }} interval="preserveStartEnd" />
          <YAxis yAxisId="left"  tick={{ fontSize: 8, fill: '#334155' }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 8, fill: '#334155' }} />
          <Tooltip
            contentStyle={{ background: 'rgba(2,5,16,0.95)', border: '1px solid rgba(0,180,255,0.3)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: '#64748b' }}
          />
          <Line yAxisId="left"  type="monotone" dataKey="fish_count"   stroke="#22d3ee" strokeWidth={2}   dot={false} name="Balık"   isAnimationActive={false} />
          <Line yAxisId="right" type="monotone" dataKey="avg_activity" stroke="#a78bfa" strokeWidth={1.5} dot={false} name="Aktivite" isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function DecisionPanel({ decision, loading }) {
  const glowClass = { ok: 'glow-border-ok', warning: 'glow-border-warning', critical: 'glow-border-critical' }
  const bgClass   = { ok: 'rgba(52,211,153,0.05)', warning: 'rgba(251,191,36,0.05)', critical: 'rgba(239,68,68,0.07)' }

  if (loading && !decision) return (
    <div className="neon-card glow-border p-4 flex items-center gap-3 text-slate-500"
         role="status" aria-live="polite" aria-busy="true">
      <Brain size={16} className="text-violet-400 animate-pulse" />
      <span className="text-xs tracking-wider">AQUA LLM ANALİZ EDİYOR…</span>
      <span className="flex gap-1 ml-auto">
        {[0,150,300].map(d => <span key={d} className="w-1 h-1 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: `${d}ms` }} />)}
      </span>
    </div>
  )
  if (!decision) return null

  const s = statusColors[decision.status] ?? statusColors.ok
  const StatusIcon = s.icon
  const status = decision.status ?? 'ok'

  return (
    <div className={`neon-card ${glowClass[status] ?? 'glow-border'} p-5 relative overflow-hidden`}
         style={{ background: `linear-gradient(135deg, ${bgClass[status] ?? 'transparent'}, rgba(2,5,16,0.9))` }}>
      <div className="scan-line" />
      <div className="flex items-center gap-2 mb-4">
        <div className="relative w-6 h-6 flex items-center justify-center">
          <Brain size={14} className={s.text} />
          <span className={`pulse-ring relative ${s.text}`} />
        </div>
        <span className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Aqua LLM / Karar Motoru</span>
        <span className={`ml-auto text-[10px] px-2.5 py-1 rounded-full font-black uppercase tracking-widest ${s.text} border ${s.border}`}
              style={{ background: 'rgba(0,0,0,0.4)' }}>
          ● {status.toUpperCase()}
        </span>
      </div>
      <div className="flex items-start gap-2 mb-3">
        <StatusIcon size={14} className={`${s.text} mt-0.5 shrink-0`} />
        <p className="text-sm text-slate-300 leading-relaxed">{decision.reasoning}</p>
      </div>
      {decision.recommendations?.length > 0 && (
        <div className="space-y-1.5 mt-3 pt-3 border-t border-white/5">
          {decision.recommendations.map((r, i) => (
            <div key={i} className="flex gap-2 items-start">
              <Zap size={11} className={`${s.text} mt-0.5 shrink-0`} />
              <span className="text-xs text-slate-400">{r}</span>
            </div>
          ))}
        </div>
      )}
      <div className="mt-3 flex gap-3 text-[10px] text-slate-700 font-mono">
        <span>{decision.engine}</span>
        {decision.timestamp && <span>{fmtTime(decision.timestamp)}</span>}
        {decision.llm_error && <span className="text-amber-800">⚠ fallback</span>}
      </div>
    </div>
  )
}

// ─── Canlı Kamera Feed Paneli ──────────────────────────────────────────────────
function LiveFeedPanel({ visionState }) {
  const [hasStream, setHasStream] = useState(false)
  // MJPEG bağlantısı koparsa <img>'i yeni bir key ile yeniden kurmak için.
  const [streamKey, setStreamKey] = useState(0)
  const imgRef = useRef(null)

  // Polling yok: backend multipart/x-mixed-replace ile frame'leri PUSH eder,
  // tarayıcı tek bir bağlantıyı açık tutup <img>'i kendisi günceller.
  // (Eskiden 250ms'de bir /api/vision/frame.jpg isteniyordu.)
  const handleStreamError = useCallback(() => {
    setHasStream(false)
    // 2sn sonra yeniden bağlan — vision servisi geç açılmış olabilir.
    setTimeout(() => setStreamKey(k => k + 1), 2000)
  }, [])

  // Türetilmiş değer — ayrı state + effect gerekmiyordu (cascading render üretiyordu).
  const frameId   = visionState?.frame_id ?? 0
  const tracks    = visionState?.tracks ?? []
  const fishCount = visionState?.fish_count ?? 0
  const activity  = visionState?.avg_activity ?? 0

  return (
    <div className="neon-card glow-border overflow-hidden">
      {/* Başlık */}
      <div className="px-4 py-3 border-b border-cyan-500/10 flex items-center gap-2">
        <Radio size={12} className={hasStream ? 'text-red-400 animate-pulse' : 'text-slate-600'} />
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">
          Canlı Görüntü — YOLO / ByteTrack
        </span>
        <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded border ${
          hasStream
            ? 'text-red-400 border-red-500/40 bg-red-500/10'
            : 'text-slate-600 border-slate-700'
        }`}>
          {hasStream ? '● LIVE' : '○ BEKLENIYOR'}
        </span>
      </div>

      {/* Frame alanı */}
      <div className="relative bg-black" style={{ minHeight: 220 }}>
        {/* Backend MJPEG push stream — tarayıcı bağlantıyı açık tutar */}
        <img
          key={streamKey}
          ref={imgRef}
          src="/api/vision/stream"
          alt="Tank kamerası canlı görüntüsü, YOLO tespit kutularıyla işaretlenmiş"
          className="w-full object-contain"
          style={{ maxHeight: 300, display: hasStream ? 'block' : 'none' }}
          onLoad={() => setHasStream(true)}
          onError={handleStreamError}
        />

        {/* Vision servisi başlamadıysa animasyonlu tank simülasyonu */}
        {!hasStream && (
          <MockTankCanvas tracks={tracks} />
        )}

        {/* Üst sağ: frame sayacı */}
        {hasStream && frameId > 0 && (
          <div className="absolute top-2 right-2 text-[9px] font-mono bg-black/60 px-1.5 py-0.5 rounded text-slate-500">
            #{frameId}
          </div>
        )}

        {/* Alt sol: anlık metrikler */}
        {hasStream && (
          <div className="absolute bottom-2 left-2 flex gap-2 text-[10px] font-mono">
            <span className="bg-black/75 px-2 py-0.5 rounded text-cyan-400 border border-cyan-500/20">
              FISH {fishCount}
            </span>
            <span className={`bg-black/75 px-2 py-0.5 rounded border ${
              activity < 0.002
                ? 'text-red-400 border-red-500/30'
                : 'text-violet-400 border-violet-500/20'
            }`}>
              ACT {activity.toFixed(4)}
            </span>
          </div>
        )}
      </div>

      {/* Track rozetleri */}
      <div className="px-4 py-2.5 border-t border-slate-700/40">
        <div className="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-2 flex items-center gap-2">
          <Eye size={10} /> Aktif Takipler
          <span className="ml-auto font-mono text-cyan-600">{tracks.length} ID</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {tracks.length === 0 ? (
            <span className="text-[10px] text-slate-700">
              {hasStream ? 'Bu karede balık tespit edilmedi' : 'Vision servisi bekleniyor…'}
            </span>
          ) : (
            tracks.map(t => (
              <span key={t.id}
                    className="text-[10px] font-mono px-2 py-0.5 rounded border border-cyan-500/25 bg-cyan-500/8 text-cyan-400">
                #{t.id} {(t.conf * 100).toFixed(0)}%
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Simüle Tank Canvas (gerçek kamera yokken) ────────────────────────────────
function MockTankCanvas({ tracks }) {
  const canvasRef = useRef(null)
  const animRef   = useRef(null)

  // Her track için sanal konum (demo için rastgele ama sabit)
  const mockPositions = useRef({})

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const W = canvas.width
    const H = canvas.height

    function getPos(id) {
      if (!mockPositions.current[id]) {
        mockPositions.current[id] = {
          x: 60 + Math.random() * (W - 120),
          y: 40 + Math.random() * (H - 80),
          vx: (Math.random() - 0.5) * 0.6,
          vy: (Math.random() - 0.5) * 0.4,
          w: 80 + Math.random() * 40,
          h: 28 + Math.random() * 16,
        }
      }
      return mockPositions.current[id]
    }

    function draw() {
      // Arka plan: derin su gradyanı
      const bg = ctx.createLinearGradient(0, 0, 0, H)
      bg.addColorStop(0, '#010c14')
      bg.addColorStop(1, '#001a2c')
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, W, H)

      // Su yansıması efekti
      ctx.strokeStyle = 'rgba(0,180,255,0.04)'
      ctx.lineWidth = 1
      for (let y = 0; y < H; y += 18) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(W, y)
        ctx.stroke()
      }

      const now = Date.now() / 1000

      // Bounding box'ları çiz (gerçek track verisi varsa onu, yoksa mock)
      const items = tracks.length > 0
        ? tracks.map(t => ({ id: t.id, conf: t.conf }))
        : [{ id: 1, conf: 0.82 }, { id: 2, conf: 0.79 }, { id: 3, conf: 0.88 }]

      items.forEach(({ id, conf }) => {
        const p = getPos(id)

        // Hareket simülasyonu
        p.x += p.vx
        p.y += p.vy
        if (p.x < 20 || p.x + p.w > W - 20) p.vx *= -1
        if (p.y < 10 || p.y + p.h > H - 10) p.vy *= -1

        const alpha = 0.55 + 0.2 * Math.sin(now * 2 + id)
        const glow  = `rgba(0,220,180,${alpha})`

        // Dış glow
        ctx.shadowColor = glow
        ctx.shadowBlur  = 8

        // Kutu
        ctx.strokeStyle = glow
        ctx.lineWidth   = 1.5
        ctx.strokeRect(p.x, p.y, p.w, p.h)

        // Köşe süslemeleri
        const cs = 8
        ctx.strokeStyle = '#00ffcc'
        ctx.lineWidth   = 2
        ;[[p.x, p.y], [p.x + p.w, p.y], [p.x, p.y + p.h], [p.x + p.w, p.y + p.h]].forEach(([cx, cy], qi) => {
          const sx = qi % 2 === 0 ? 1 : -1
          const sy = qi < 2 ? 1 : -1
          ctx.beginPath()
          ctx.moveTo(cx, cy + sy * cs); ctx.lineTo(cx, cy); ctx.lineTo(cx + sx * cs, cy)
          ctx.stroke()
        })

        ctx.shadowBlur = 0

        // Label
        ctx.fillStyle = 'rgba(0,0,0,0.7)'
        ctx.fillRect(p.x, p.y - 18, 72, 16)
        ctx.fillStyle = '#00ffcc'
        ctx.font = 'bold 10px monospace'
        ctx.fillText(`ID:${id}  ${(conf * 100).toFixed(0)}%`, p.x + 4, p.y - 5)
      })

      // "SIMULATED" watermark
      ctx.fillStyle = 'rgba(255,255,255,0.06)'
      ctx.font = '10px monospace'
      ctx.fillText('SIMULATED — awaiting vision service', 8, H - 8)

      animRef.current = requestAnimationFrame(draw)
    }

    animRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(animRef.current)
  }, [tracks])

  return (
    <canvas
      ref={canvasRef}
      width={480}
      height={270}
      className="w-full"
      style={{ display: 'block' }}
    />
  )
}

// ─── Karar Geçmişi Zaman Şeridi ───────────────────────────────────────────────
const TIMELINE_SQUARES = 60   // ~8 dk canlı (DECISION_MS=8sn) + DB'den gelen geçmiş

function DecisionTimeline({ history }) {
  const colorMap = { ok: 'bg-emerald-500', warning: 'bg-amber-500', critical: 'bg-red-500' }
  const shown = history.slice(-TIMELINE_SQUARES)

  // "Son 1 saatte kaç uyarı aldım?" — şeridin kendisi 60 kare gösteriyor ama
  // sayım tüm geçmiş üzerinden, gerçek 1 saatlik pencereyle yapılır.
  // Referans zaman olarak wall-clock yerine EN SON kararın zamanı kullanılır:
  // render saf kalır (Date.now() render sırasında impure sayılır) ve backend
  // sustuğunda sayaç eski pencereyi saymaya devam etmez.
  const newest = history.length ? Date.parse(history[history.length - 1].timestamp) : NaN
  const hourAgo = Number.isFinite(newest) ? newest - 3600_000 : NaN
  const lastHour = Number.isFinite(hourAgo)
    ? history.filter(d => {
        const t = Date.parse(d.timestamp)
        return Number.isFinite(t) && t >= hourAgo
      })
    : []
  const warnings  = lastHour.filter(d => d.status === 'warning').length
  const criticals = lastHour.filter(d => d.status === 'critical').length

  const span = shown.length > 1
    ? `${fmtTime(shown[0].timestamp)} – ${fmtTime(shown[shown.length - 1].timestamp)}`
    : null

  return (
    <div className="flex items-center gap-3 min-w-0">
      <div
        className="flex items-center gap-1 min-w-0 overflow-hidden"
        role="img"
        aria-label={
          history.length === 0
            ? 'Karar geçmişi boş, ilk karar bekleniyor'
            : `Son ${shown.length} karar. Son 1 saatte ${criticals} kritik, ${warnings} uyarı.`
        }
        title={span ? `Gösterilen aralık: ${span}` : 'Son kararlar'}
      >
        {shown.length === 0
          ? <span className="text-[9px] text-slate-700 tracking-widest">— karar bekleniyor —</span>
          : shown.map((d, i) => (
              <span
                key={`${d.timestamp}-${i}`}
                className={`w-2.5 h-2.5 rounded-sm shrink-0 ${colorMap[d.status] ?? 'bg-slate-600'}`}
                title={`${fmtTime(d.timestamp)} — ${d.status}`}
              />
            ))
        }
      </div>

      {lastHour.length > 0 && (
        <span className="text-[9px] font-mono tracking-wider text-slate-600 shrink-0 whitespace-nowrap">
          son 1s:{' '}
          <span className={criticals ? 'text-red-400' : 'text-slate-600'}>{criticals} kritik</span>
          {' · '}
          <span className={warnings ? 'text-amber-400' : 'text-slate-600'}>{warnings} uyarı</span>
        </span>
      )}
    </div>
  )
}

// ─── Aqua LLM Chat Bar ─────────────────────────────────────────────────────────
function ChatBar() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Merhaba! Ben Aqua. Sistem hakkında sorularını yanıtlayabilirim.' }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState('')  // aktif stream token buffer
  const bottomRef = useRef(null)
  const abortRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  // Unmount olunca uçuşan stream isteğini iptal et.
  // (Burada EventSource yok: /api/chat/stream POST olduğu için fetch + reader
  // kullanılıyor; eski `esRef` hiçbir zaman atanmıyordu, ölü koddu.)
  useEffect(() => () => abortRef.current?.abort(), [])

  const send = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)
    setStreaming('')

    try {
      // SSE stream ile token alımı
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) throw new Error(res.statusText)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') break
          try {
            const { token } = JSON.parse(raw)
            fullText += token
            setStreaming(fullText)
          } catch { /* malformed chunk — skip */ }
        }
      }

      setMessages(prev => [...prev, { role: 'assistant', text: fullText || '…' }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Bağlantı hatası. Backend çalışıyor mu?' }])
    } finally {
      setLoading(false)
      setStreaming('')
    }
  }

  return (
    <div className="neon-card glow-border flex flex-col" style={{ minHeight: 320 }}>
      {/* Başlık */}
      <div className="px-4 py-3 border-b border-cyan-500/10 flex items-center gap-2 shrink-0">
        <Brain size={12} className="text-violet-400" />
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Aqua LLM — Sistem Asistanı</span>
        <span className="ml-auto w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Çevrimiçi" />
      </div>

      {/* Mesajlar */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3" style={{ maxHeight: 280 }}>
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.role === 'assistant' && (
              <div className="w-6 h-6 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={11} className="text-violet-400" />
              </div>
            )}
            <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-100'
                : 'bg-slate-700/60 border border-slate-600/40 text-slate-200'
            }`}>
              {m.text}
            </div>
            {m.role === 'user' && (
              <div className="w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center shrink-0 mt-0.5">
                <User size={11} className="text-cyan-400" />
              </div>
            )}
          </div>
        ))}
        {/* Aktif stream — token token büyüyen bubble */}
        {loading && (
          <div className="flex gap-2 justify-start">
            <div className="w-6 h-6 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center shrink-0 mt-0.5">
              <Bot size={11} className="text-violet-400" />
            </div>
            <div className="max-w-[80%] bg-slate-700/60 border border-slate-600/40 rounded-xl px-3 py-2 text-sm text-slate-200 leading-relaxed">
              {streaming
                ? <>{streaming}<span className="inline-block w-1.5 h-3.5 ml-0.5 bg-violet-400 animate-pulse rounded-sm" /></>
                : <span className="flex gap-1">
                    {[0,150,300].map(d => <span key={d} className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />)}
                  </span>
              }
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-700/60 shrink-0">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-black/40 border border-cyan-500/15 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-700 focus:outline-none focus:border-cyan-500/40 font-mono"
            placeholder="Oksijen neden düşük? Balıkların durumu nasıl?…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            disabled={loading}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="px-3 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 rounded-lg text-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Ana uygulama ─────────────────────────────────────────────────────────────
export default function App() {
  const [sensorHistory, setSensorHistory] = useState([])
  const [visionHistory, setVisionHistory]  = useState([])
  const [state, setState]   = useState({ vision: null, sensor: null })
  const [decision, setDecision] = useState(null)
  const [decisionLoading, setDecisionLoading] = useState(false)
  const [decisionHistory, setDecisionHistory] = useState([])
  const [connected, setConnected] = useState(false)

  const fetchHistory = useCallback(async () => {
    try {
      const [hist, st] = await Promise.all([
        fetch(HISTORY_URL).then(r => r.json()),
        fetch(STATE_URL).then(r => r.json()),
      ])
      setSensorHistory(hist.sensor.map(s => ({ ...s, t: fmtTime(s.timestamp) })))
      setVisionHistory(hist.vision.map(v => ({ ...v, t: fmtTime(v.timestamp) })))
      setState(st)
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }, [])

  const fetchDecision = useCallback(async () => {
    setDecisionLoading(true)
    try {
      const d = await fetch(DECISION_URL).then(r => r.json())
      setDecision(d)
      if (d.status) {
        setDecisionHistory(prev => [
          ...prev.slice(-(DECISION_HISTORY_MAX - 1)),
          { status: d.status, timestamp: d.timestamp ?? new Date().toISOString() },
        ])
      }
    } catch { /* ignore */ }
    finally { setDecisionLoading(false) }
  }, [])

  useEffect(() => {
    // Uygulama başladığında DB'den önceki karar geçmişini yükle
    // 1 saatlik özet için şeritte görünenden daha derin geçmiş çekilir.
    fetch(`/api/decision/history?limit=${DECISION_HISTORY_MAX}`)
      .then(r => r.json())
      .then(rows => setDecisionHistory(
        rows.filter(r => r.status).map(r => ({ status: r.status, timestamp: r.timestamp }))
      ))
      .catch(() => {})

    // fetchDecision ilk satırında setDecisionLoading(true) çağırıyor; async
    // gövde ilk await'e kadar SENKRON çalıştığı için bunu doğrudan effect
    // içinden çağırmak mount sırasında zincirleme render tetikliyordu.
    // Mikrotask'a alınca ilk render tamamlanmış oluyor.
    queueMicrotask(fetchHistory)
    queueMicrotask(fetchDecision)
    const histTimer = setInterval(fetchHistory, POLL_MS)
    const decTimer  = setInterval(fetchDecision, DECISION_MS)
    return () => { clearInterval(histTimer); clearInterval(decTimer) }
  }, [fetchHistory, fetchDecision])

  const s = state.sensor
  const v = state.vision

  const doAlert  = s?.dissolved_oxygen_mgl != null && s.dissolved_oxygen_mgl < 6
  const [alertDismissed, dismissAlert] = useDismissable(30000)
  const showBanner = doAlert && !alertDismissed

  return (
    <div
      className="min-h-screen text-slate-200 p-4 md:p-5 relative"
      style={{
        zIndex: 1,
        ...(showBanner && {
          outline: '3px solid rgba(239,68,68,0.7)',
          outlineOffset: '-3px',
          animation: 'critical-flash 1.2s ease-in-out infinite',
        })
      }}
    >
      <style>{`
        @keyframes critical-flash {
          0%, 100% { outline-color: rgba(239,68,68,0.7); box-shadow: inset 0 0 40px rgba(239,68,68,0.08); }
          50%       { outline-color: rgba(239,68,68,0.2); box-shadow: inset 0 0 40px rgba(239,68,68,0.02); }
        }
      `}</style>

      {/* ─── Header ─── */}
      <header className="flex items-center justify-between mb-5">
        {/* Logo + isim */}
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 flex items-center justify-center">
            <div className="absolute inset-0 rounded-lg border border-cyan-500/40 bg-cyan-500/5" />
            <div className="absolute inset-0 rounded-lg" style={{ boxShadow: '0 0 18px rgba(0,210,255,0.2)' }} />
            <Fish size={18} className="text-cyan-400 relative z-10" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black tracking-[0.15em] text-white">S.U.R.E.</span>
              <span className="text-[9px] font-bold text-cyan-500/60 uppercase tracking-widest border border-cyan-500/20 px-1.5 py-0.5 rounded">
                v1.0
              </span>
            </div>
            <p className="text-[10px] text-slate-600 tracking-widest uppercase">
              Autonomous Sturgeon Welfare Monitor
            </p>
          </div>
        </div>

        {/* Sağ: saat + bağlantı */}
        <div className="flex items-center gap-3">
          <LiveClock />
          <div role="status"
               aria-live="polite"
               aria-label={connected ? 'Backend bağlantısı aktif' : 'Backend bağlantısı kesik'}
               className={`flex items-center gap-1.5 text-[10px] font-bold px-3 py-1.5 rounded-full border tracking-wider ${
            connected
              ? 'text-emerald-400 bg-emerald-500/8 border-emerald-500/25'
              : 'text-red-400 bg-red-500/8 border-red-500/25'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
            {connected ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>
      </header>

      {/* ─── Karar geçmişi şeridi ─── */}
      <div className="flex items-center gap-3 mb-3 px-1">
        <span className="text-[9px] font-bold uppercase tracking-widest text-slate-700 shrink-0" id="karar-gecmisi-label">Karar Geçmişi</span>
        <DecisionTimeline history={decisionHistory} />
      </div>

      {/* ─── Kritik uyarı banner ─── */}
      {showBanner && (
        <CriticalAlertBanner
          do={s.dissolved_oxygen_mgl}
          onDismiss={dismissAlert}
        />
      )}

      {/* ─── Stat kartları ─── */}
      <SectionLabel>Anlık Durum</SectionLabel>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5 mb-4">
        <StatCard icon={Fish}        label="Aktif Balık"   color="text-cyan-400"   value={v?.fish_count ?? '—'}                              unit="adet" sub={v ? `frame #${v.frame_id}` : 'vision bekleniyor'} />
        <StatCard icon={Activity}    label="Aktivite"      color="text-violet-400" value={v?.avg_activity != null ? v.avg_activity.toFixed(4) : '—'} unit=""     sub={v?.avg_activity < 0.002 ? '↓ düşük' : 'normal'} alert={v?.avg_activity < 0.002} />
        <StatCard icon={Wind}        label="Çöz. O₂"       color="text-sky-400"    value={s?.dissolved_oxygen_mgl ?? '—'}                   unit="mg/L" sub={doAlert ? 'KRİTİK!' : '>6 mg/L'}   alert={doAlert} />
        <StatCard icon={Thermometer} label="Sıcaklık"      color="text-orange-400" value={s?.temperature_c ?? '—'}                           unit="°C"   sub="16–21°C" />
        <StatCard icon={Droplets}    label="pH"            color="text-teal-400"   value={s?.ph ?? '—'}                                      unit=""     sub="6.5–8.0" />
        <StatCard icon={Droplets}    label="TDS"           color="text-indigo-400" value={s?.tds_ppm ?? '—'}                                 unit="ppm"  sub="200–450" />
      </div>

      {/* ─── Ana içerik ─── */}
      <SectionLabel>Telemetri & Analiz</SectionLabel>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">

        {/* Sol: grafikler + karar */}
        <div className="xl:col-span-2 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <FishActivityChart data={visionHistory} />
            <SensorChart data={sensorHistory} dataKey="dissolved_oxygen_mgl" label="Çözünmüş Oksijen" color="#38bdf8" unit="mg/L" refLines={[{ v: 6, color: '#ef4444' }]} />
            <SensorChart data={sensorHistory} dataKey="temperature_c"        label="Sıcaklık"         color="#fb923c" unit="°C"   refLines={[{ v: 16, color: '#334155' }, { v: 21, color: '#334155' }]} />
            <SensorChart data={sensorHistory} dataKey="ph"                   label="pH"               color="#2dd4bf" unit=""     refLines={[{ v: 6.5, color: '#334155' }, { v: 8.0, color: '#334155' }]} />
          </div>
          <DecisionPanel decision={decision} loading={decisionLoading} />
        </div>

        {/* Sağ: canlı feed + chat */}
        <div className="space-y-3">
          <LiveFeedPanel visionState={state.vision} />
          <ChatBar />
        </div>
      </div>
    </div>
  )
}

function LiveClock() {
  const [t, setT] = useState('')
  useEffect(() => {
    const tick = () => setT(new Date().toLocaleTimeString('tr-TR', { hour12: false }))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])
  return <span className="text-xs font-mono text-slate-600 tracking-widest">{t}</span>
}
