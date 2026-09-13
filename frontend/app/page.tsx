"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { usePathname } from "next/navigation"
import { Activity, ArrowRight, BarChart3, Check, ChevronDown, Clock3, FileImage, GitCompareArrows, Globe, ImagePlus, Layers3, LogIn, LogOut, Menu, PanelTop, Radar, Search, Send, ShieldCheck, Sparkles, Upload, X } from "lucide-react"
import {
  analysisAPI,
  buildTrinetraUrl,
  checkBackendHealth,
  demoScenarios,
  formatBytes,
  formatDate,
  imagePresets,
  isReady,
  loadHistory,
  normalizeFile,
  saveHistory,
  type AnalysisMode,
  type AnalysisResponse,
  type ImageInput,
  type GeographicLocation,
} from "@/lib/types"
import { I18nProvider, useTranslation, type SupportedLanguage } from "@/lib/i18n"
import { useAuth } from "@/context/AuthContext"
import AuthGate from "@/components/AuthGate"

const Icon = ({ mode }: { mode: AnalysisMode }) =>
  mode === "single" ? <FileImage /> : mode === "temporal" ? <GitCompareArrows /> : <Layers3 />

function LanguageSelector() {
  const { language, setLanguage, languages, t } = useTranslation()
  return (
    <div className="lang-switch" role="group" aria-label={t("aria.language")}>
      <Globe size={13} style={{ color: "rgba(255,255,255,0.4)", marginLeft: "4px" }} />
      {languages.map((item) => (
        <button
          key={item.code}
          type="button"
          className={`lang-btn ${language === item.code ? "active" : ""}`}
          onClick={() => setLanguage(item.code)}
          title={item.label}
          aria-pressed={language === item.code}
        >
          {item.nativeName}
        </button>
      ))}
    </div>
  )
}

function Header({ path, navigate }: { path: string; navigate: (path: string) => void }) {
  const { isAuthenticated, displayName, avatarUrl, signOut } = useAuth()
  const { t } = useTranslation()
  const [health, setHealth] = useState<{ online: boolean; rawStatus?: string; model?: string; langfuse?: boolean }>({
    online: false,
  })

  useEffect(() => {
    checkBackendHealth()
      .then((h) => {
        if (h && h.status === "healthy") {
          const ollamaTag = h.ollama?.models?.[0] || h.llm_status?.roles?.planner?.active || "QWEN3.5"
          setHealth({
            online: true,
            model: ollamaTag.toUpperCase(),
            langfuse: Boolean(h.langfuse?.connected),
          })
        } else {
          setHealth({ online: false })
        }
      })
      .catch(() => {
        setHealth({ online: false })
      })
  }, [])

  const navItems = [
    { href: "/", label: t("nav.overview") },
    { href: "/analysis", label: t("nav.workspace") },
    { href: "/dashboard", label: t("nav.history") },
    { href: "/evaluation", label: t("nav.evaluation") },
  ]

  const statusText = health.online
    ? t("status.ready", {
        model: health.model || "LOCAL",
        trace: health.langfuse ? t("status.langfuse_on") : "",
      })
    : t("status.offline")

  return (
    <header className="topbar">
      <button className="brand" onClick={() => navigate("/")}>
        <span className="brandmark">
          <Radar />
        </span>
        <span>
          {t("brand.title")} <b>{t("brand.ai")}</b>
          <small>{t("brand.subtitle")}</small>
        </span>
      </button>
      <nav>
        {navItems.map((item) => (
          <button
            key={item.href}
            className={path === item.href ? "active" : ""}
            onClick={() => navigate(item.href)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <LanguageSelector />
      <div className="header-status">
        <i
          style={{
            backgroundColor: health.online ? "var(--cyan-400, #00f0ff)" : "var(--amber-400, #ffb300)",
          }}
        />{" "}
        <span>{statusText}</span>
      </div>

      {/* User Authentication & Profile Widget */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginLeft: "0.5rem" }}>
        {isAuthenticated ? (
          <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", background: "rgba(255, 255, 255, 0.04)", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "4px 10px 4px 6px", borderRadius: "99px" }}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                style={{ width: "26px", height: "26px", borderRadius: "50%", objectFit: "cover", border: "1px solid var(--cyan-400, #00f0ff)" }}
              />
            ) : (
              <div style={{ width: "26px", height: "26px", borderRadius: "50%", background: "linear-gradient(135deg, rgba(86, 215, 223, 0.8), rgba(0, 160, 255, 0.8))", color: "#081016", display: "grid", placeItems: "center", fontSize: "11px", fontWeight: 700 }}>
                {displayName ? displayName.charAt(0).toUpperCase() : "U"}
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", maxWidth: "120px" }}>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {displayName || "Operator"}
              </span>
              <span style={{ fontSize: "8px", color: "var(--cyan-400, #00f0ff)", fontFamily: "monospace", letterSpacing: "0.05em" }}>
                CLEARANCE ACTIVE
              </span>
            </div>
            <button
              onClick={() => signOut()}
              title="Sign Out"
              style={{ background: "none", border: "none", color: "rgba(255, 255, 255, 0.4)", padding: "4px", borderRadius: "6px", cursor: "pointer", display: "flex", alignItems: "center", marginLeft: "2px" }}
              onMouseOver={(e) => (e.currentTarget.style.color = "#f87171")}
              onMouseOut={(e) => (e.currentTarget.style.color = "rgba(255, 255, 255, 0.4)")}
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => navigate("/analysis")}
            className="primary compact"
            style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem", padding: "6px 14px", fontSize: "0.78rem" }}
          >
            <LogIn size={13} /> Sign In
          </button>
        )}
      </div>

      <button className="mobile-menu" aria-label={t("aria.menu")}>
        <Menu />
      </button>
    </header>
  )
}

function Pill({ children, tone = "cyan" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`pill ${tone}`}>{children}</span>
}

function SatelliteBackdrop() {
  return (
    <div className="backdrop">
      <div className="orb" />
      <div className="orbit orbit-one" />
      <div className="orbit orbit-two" />
      <div className="scanline" />
    </div>
  )
}

function Landing({ navigate }: { navigate: (path: string) => void }) {
  const { t } = useTranslation()

  const capabilities = [
    {
      id: "single" as const,
      eyebrow: t("cap.single.eyebrow"),
      title: t("cap.single.title"),
      desc: t("cap.single.desc"),
    },
    {
      id: "temporal" as const,
      eyebrow: t("cap.temporal.eyebrow"),
      title: t("cap.temporal.title"),
      desc: t("cap.temporal.desc"),
    },
    {
      id: "fusion" as const,
      eyebrow: t("cap.fusion.eyebrow"),
      title: t("cap.fusion.title"),
      desc: t("cap.fusion.desc"),
    },
  ]

  return (
    <main className="landing">
      <SatelliteBackdrop />
      <div className="hero">
        <Pill>
          <span className="pulse" />
          {t("landing.pill")}
        </Pill>
        <h1>
          {t("landing.hero.title1")}
          <br />
          <span>{t("landing.hero.title2")}</span>
        </h1>
        <p>{t("landing.hero.desc")}</p>
        <div className="hero-actions">
          <button className="primary" onClick={() => navigate("/analysis")}>
            {t("landing.hero.start")} <ArrowRight />
          </button>
          <button className="secondary" onClick={() => navigate("/analysis?demo=1")}>
            {t("landing.hero.demo")} <Sparkles />
          </button>
        </div>
        <div className="hero-stats">
          <div>
            <b>03</b>
            <span>{t("landing.stats.modes")}</span>
          </div>
          <div>
            <b>01</b>
            <span>{t("landing.stats.layer")}</span>
          </div>
          <div>
            <b>04</b>
            <span>{t("landing.stats.scenarios")}</span>
          </div>
        </div>
      </div>
      <div className="capabilities">
        {capabilities.map((cap) => (
          <div className="cap-card" key={cap.id}>
            <div className="cap-icon">
              <Icon mode={cap.id} />
            </div>
            <div>
              <span className="eyebrow">{cap.eyebrow}</span>
              <h3>{cap.title}</h3>
              <p>{cap.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </main>
  )
}

function UploadSlot({
  slot,
  image,
  onFile,
  onRemove,
}: {
  slot: { label: string; hint: string }
  image?: ImageInput
  onFile: (file: File) => void
  onRemove: () => void
}) {
  const { t } = useTranslation()
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div
      className={`upload-slot ${image ? "filled" : ""}`}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault()
        const file = e.dataTransfer.files[0]
        if (file) onFile(file)
      }}
      onClick={() => !image && ref.current?.click()}
    >
      {image ? (
        <>
          <img src={image.url} alt={t("aria.preview")} />
          <div className="slot-overlay">
            <Pill tone="dark">{slot.hint}</Pill>
            <strong>{image.name}</strong>
            <span>{formatBytes(image.size)}</span>
          </div>
          <button
            className="remove"
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
            aria-label={t("upload.remove_aria")}
          >
            <X />
          </button>
        </>
      ) : (
        <>
          <input
            ref={ref}
            type="file"
            accept="image/png,image/jpeg,image/tiff,.tif,.tiff"
            hidden
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          />
          <Upload />
          <strong>{slot.label}</strong>
          <span>{t("upload.drop_prompt")}</span>
          <small>{t("upload.formats", { hint: slot.hint })}</small>
        </>
      )}
    </div>
  )
}

function Workspace({ navigate, initialDemo = false }: { navigate: (path: string) => void; initialDemo?: boolean }) {
  const { t, language } = useTranslation()
  const [mode, setMode] = useState<AnalysisMode>(initialDemo ? "temporal" : "single")
  const [images, setImages] = useState<ImageInput[]>(
    initialDemo ? [imagePresets.before, imagePresets.after] : []
  )
  const [query, setQuery] = useState(
    initialDemo ? (t("scenario.urban.query" as any) || demoScenarios[0].query) : ""
  )
  const [result, setResult] = useState<AnalysisResponse>()
  const [running, setRunning] = useState(false)
  const [technical, setTechnical] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Localized slots
  const slots = useMemo(() => {
    if (mode === "single") {
      return [{ label: t("slot.single.label"), hint: t("slot.single.hint") }]
    }
    if (mode === "temporal") {
      return [
        { label: t("slot.temporal.before.label"), hint: t("slot.temporal.before.hint") },
        { label: t("slot.temporal.after.label"), hint: t("slot.temporal.after.hint") },
      ]
    }
    return [
      { label: t("slot.fusion.opt.label"), hint: t("slot.fusion.opt.hint") },
      { label: t("slot.fusion.sar.label"), hint: t("slot.fusion.sar.hint") },
    ]
  }, [mode, t])

  // Localized workflow options
  const workflowModes: { id: AnalysisMode; label: string; desc: string }[] = [
    { id: "single", label: t("mode.single.label"), desc: t("mode.single.desc") },
    { id: "temporal", label: t("mode.temporal.label"), desc: t("mode.temporal.desc") },
    { id: "fusion", label: t("mode.fusion.label"), desc: t("mode.fusion.desc") },
  ]

  // Localized query examples
  const currentExamples = useMemo(() => {
    if (mode === "single") {
      return [t("examples.single.0"), t("examples.single.1"), t("examples.single.2")]
    }
    if (mode === "temporal") {
      return [t("examples.temporal.0"), t("examples.temporal.1"), t("examples.temporal.2")]
    }
    return [t("examples.fusion.0"), t("examples.fusion.1")]
  }, [mode, t])

  const ready = isReady(mode, images, query)

  const setModeAndReset = (next: AnalysisMode) => {
    setMode(next)
    setImages([])
    setResult(undefined)
    setErrorMessage(null)
  }

  const addImage = (file: File, index: number) =>
    setImages((current) => {
      const next = [...current]
      next[index] = normalizeFile(
        file,
        slots[index]?.label || "Image",
        mode === "fusion" ? (index === 0 ? "OPTICAL" : "SAR") : undefined
      )
      return next
    })

  const run = async () => {
    if (!ready) return
    setRunning(true)
    setResult(undefined)
    setErrorMessage(null)
    try {
      const response = await analysisAPI.submitAnalysis({
        mode,
        images,
        query,
        response_language: language,
      })
      setResult(response)
      saveHistory(response)
    } catch (err: any) {
      setErrorMessage(err.message || "Satellite analysis failed on local backend.")
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    if (initialDemo && !result) {
      setTimeout(() => run(), 450)
    }
  }, [])

  return (
    <main className="workspace page">
      <div className="page-intro">
        <div>
          <Pill>
            <span className="pulse" />
            {t("workspace.pill")}
          </Pill>
          <h1>{t("workspace.title")}</h1>
          <p>{t("workspace.desc")}</p>
        </div>
        <button className="secondary compact" onClick={() => navigate("/dashboard")}>
          <Clock3 /> {t("workspace.history_btn")}
        </button>
      </div>
      <div className="workspace-grid">
        <section className="input-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">{t("section.workflow.eyebrow")}</span>
              <h2>{t("section.workflow.title")}</h2>
            </div>
            <Pill tone="muted">{t(`req.${mode}` as any)}</Pill>
          </div>
          <div className="mode-grid">
            {workflowModes.map((item) => (
              <button
                key={item.id}
                className={`mode-card ${mode === item.id ? "selected" : ""}`}
                onClick={() => setModeAndReset(item.id)}
              >
                <Icon mode={item.id} />
                <strong>{item.label}</strong>
                <span>{item.desc}</span>
              </button>
            ))}
          </div>
          <div className="section-heading upload-heading">
            <div>
              <span className="eyebrow">{t("section.imagery.eyebrow")}</span>
              <h2>{t("section.imagery.title")}</h2>
            </div>
            <span className="accepted">{t("upload.accepted")}</span>
          </div>
          <div className={`upload-grid ${mode === "single" ? "single" : ""}`}>
            {slots.map((slot, index) => (
              <UploadSlot
                key={slot.label + index}
                slot={slot}
                image={images[index]}
                onFile={(file) => addImage(file, index)}
                onRemove={() => setImages((current) => current.filter((_, i) => i !== index))}
              />
            ))}
          </div>
          <div className="supported">
            <ShieldCheck /> <span>{t("supported.satellites")}</span>
          </div>
          <div className="section-heading query-heading">
            <div>
              <span className="eyebrow">{t("section.intent.eyebrow")}</span>
              <h2>{t("section.intent.title")}</h2>
            </div>
            <span className="accepted">{query.length}/240</span>
          </div>
          <textarea
            value={query}
            maxLength={240}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
                e.preventDefault()
                run()
              }
            }}
            placeholder={t("query.placeholder")}
          />
          <div className="examples">
            <span>{t("examples.label")}</span>
            {currentExamples.map((example) => (
              <button key={example} onClick={() => setQuery(example)}>
                {example}
              </button>
            ))}
          </div>
          <button className="analyze primary" disabled={!ready || running} onClick={run}>
            {running ? (
              <>
                <Activity className="spin" /> {t("btn.processing")}
              </>
            ) : (
              <>
                {t("btn.analyze")} <ArrowRight />
              </>
            )}
          </button>
          <p className="local-note">
            <Sparkles /> {t("local.note")}
          </p>
        </section>
        <section className="result-panel">
          {running ? (
            <ExecutionTrace />
          ) : errorMessage ? (
            <div
              className="trace-card"
              style={{
                border: "1px solid rgba(239, 68, 68, 0.4)",
                background: "rgba(239, 68, 68, 0.08)",
              }}
            >
              <div className="trace-header">
                <div>
                  <span className="eyebrow" style={{ color: "#ef4444" }}>
                    {t("error.eyebrow")}
                  </span>
                  <h2 style={{ color: "#fca5a5" }}>{t("error.title")}</h2>
                </div>
              </div>
              <p style={{ color: "#fecaca", margin: "16px 0", fontSize: "14px", lineHeight: 1.6 }}>
                {errorMessage}
              </p>
              <small style={{ color: "#94a3b8" }}>{t("error.note")}</small>
            </div>
          ) : result ? (
            <ResultView result={result} technical={technical} setTechnical={setTechnical} />
          ) : (
            <EmptyResult />
          )}
        </section>
      </div>
    </main>
  )
}

function EmptyResult() {
  const { t } = useTranslation()
  return (
    <div className="empty-result">
      <div className="empty-orbit">
        <Radar />
      </div>
      <span className="eyebrow">{t("empty.eyebrow")}</span>
      <h2>
        {t("empty.title").split("\n").map((line, i) => (
          <span key={i}>
            {line}
            {i === 0 && <br />}
          </span>
        ))}
      </h2>
      <p>{t("empty.desc")}</p>
      <div className="empty-lines">
        <span />
        <span />
        <span />
      </div>
    </div>
  )
}

function ExecutionTrace() {
  const { t } = useTranslation()
  const traceSteps = [
    t("trace.step.loading"),
    t("trace.step.preprocess"),
    t("trace.step.mapping"),
    t("trace.step.composing"),
  ]

  return (
    <div className="trace-card">
      <div className="trace-header">
        <div>
          <span className="eyebrow">{t("trace.eyebrow")}</span>
          <h2>{t("trace.title")}</h2>
        </div>
        <Activity className="spin cyan" />
      </div>
      <div className="trace-steps">
        {traceSteps.map((step, index) => (
          <div className="trace-step" key={step}>
            <span className="trace-dot">{index < 2 ? <Check /> : <Activity className="spin" />}</span>
            <div>
              <strong>{step}</strong>
              <small>{index < 2 ? t("trace.step.complete") : t("trace.step.working")}</small>
            </div>
            <code>{index < 2 ? `${(index + 1) * 0.8}s` : "—"}</code>
          </div>
        ))}
      </div>
      <div className="progress">
        <span style={{ width: "62%" }} />
      </div>
      <p className="trace-foot">{t("trace.foot")}</p>
    </div>
  )
}

function EvidenceViewer({ result }: { result: AnalysisResponse }) {
  const { t } = useTranslation()
  const headEyebrow =
    result.mode === "fusion" ? t("evidence.eyebrow.fused") : t("evidence.eyebrow.grounded")

  return (
    <div className="evidence">
      <div className="evidence-head">
        <div>
          <span className="eyebrow">{headEyebrow}</span>
          <h3>{t("evidence.head.title")}</h3>
        </div>
        <div className="viewer-controls">
          <button>
            <PanelTop /> {t("viewer.side_by_side")}
          </button>
          <button>
            <Layers3 /> {t("viewer.overlay")}
          </button>
        </div>
      </div>
      <div className="viewer">
        <img src={result.images[0]?.url || "/satellite-optical.svg"} alt={t("aria.preview")} />
        {result.annotations.map((annotation) => (
          <div
            key={annotation.label}
            className={`annotation ${annotation.color}`}
            style={{
              left: `${annotation.x}%`,
              top: `${annotation.y}%`,
              width: `${annotation.width}%`,
              height: `${annotation.height}%`,
            }}
          >
            <span>{annotation.label}</span>
          </div>
        ))}
        <div className="viewer-badge">
          <Pill tone="dark">{result.imageType}</Pill>
          <span>10 m / px</span>
        </div>
      </div>
      <div className="evidence-legend">
        <span>
          <i className="cyan-dot" /> {t("legend.connected")}
        </span>
        <span>
          <i className="amber-dot" /> {t("legend.change")}
        </span>
        <span className="mono">{t("legend.active")}</span>
      </div>
    </div>
  )
}

function ResultView({
  result,
  technical,
  setTechnical,
}: {
  result: AnalysisResponse
  technical: boolean
  setTechnical: (value: boolean) => void
}) {
  const { t } = useTranslation()
  const parts = result.answer.split(/(\*\*.*?\*\*)/g)
  const confidenceKey = `confidence.${result.confidence}` as const
  const confidenceText = t(confidenceKey)

  return (
    <div className="result-view">
      <div className="result-top">
        <div>
          <span className="eyebrow">{t("result.eyebrow", { mode: result.mode.toUpperCase() })}</span>
          <h2>{t("result.title")}</h2>
        </div>
        <div className={`confidence ${result.confidence}`}>
          <span>{Math.round(result.confidenceScore * 100)}%</span>
          <small>{confidenceText}</small>
        </div>
      </div>
      <div className="answer">
        {parts.map((part, index) =>
          part.startsWith("**") ? (
            <strong key={index}>{part.slice(2, -2)}</strong>
          ) : (
            <span key={index}>{part}</span>
          )
        )}
      </div>
      <EvidenceViewer result={result} />
      <div className="evidence-list">
        {result.evidence.map((item, index) => (
          <div key={item}>
            <span>0{index + 1}</span>
            {item}
            <Check />
          </div>
        ))}
      </div>
      {/* Action Row: View on Globe (TRINETRA) & View Report */}
      <div className="action-row" style={{ marginTop: "1.2rem", marginBottom: "0.6rem", display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
        {result.geographicLocation?.has_location ? (
          <button
            type="button"
            id="view-on-globe-btn"
            className="primary compact"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.55rem",
              padding: "0.65rem 1.25rem",
              borderRadius: "8px",
              background: "linear-gradient(135deg, rgba(0, 240, 255, 0.22), rgba(0, 160, 255, 0.15))",
              border: "1px solid rgba(0, 240, 255, 0.5)",
              color: "#00f0ff",
              fontSize: "0.86rem",
              fontWeight: 600,
              boxShadow: "0 0 16px rgba(0, 240, 255, 0.15)",
              cursor: "pointer",
            }}
            onClick={() => {
              const url = buildTrinetraUrl(result.geographicLocation, result.images[0]?.name || "Analysis Target")
              if (url) window.open(url, "_blank", "noopener,noreferrer")
            }}
          >
            <Globe size={16} /> View on Globe (TRINETRA) <ArrowRight size={14} />
          </button>
        ) : (
          <div
            id="globe-disabled-notice"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.55rem 0.95rem",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "rgba(255, 255, 255, 0.45)",
              fontSize: "0.78rem",
            }}
            title="This raster contains no OGC GeoTIFF georeferencing metadata. Real coordinates cannot be fabricated."
          >
            <Globe size={14} style={{ opacity: 0.5 }} />
            <span>Georeferencing Unavailable (Non-geospatial image)</span>
          </div>
        )}

        {result.reportUrl && (
          <a
            href={result.reportUrl}
            target="_blank"
            rel="noreferrer"
            className="secondary compact"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.6rem 1.2rem",
              borderRadius: "8px",
              textDecoration: "none",
              background: "rgba(0, 240, 255, 0.1)",
              border: "1px solid rgba(0, 240, 255, 0.3)",
              color: "var(--cyan-400, #00f0ff)",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <PanelTop size={16} /> {t("btn.report")} <ArrowRight size={14} />
          </a>
        )}
      </div>

      <button className="technical-toggle" onClick={() => setTechnical(!technical)}>
        <span>
          <span className="eyebrow">{t("meta.eyebrow")}</span>
          <strong>{t("meta.title")}</strong>
        </span>
        <ChevronDown className={technical ? "rotate" : ""} />
      </button>
      {technical && (
        <div className="technical-grid">
          {[
            [t("meta.model"), result.model],
            [t("meta.resolution"), result.resolution],
            [t("meta.source"), result.imageType],
            [t("meta.processing"), result.processingTime],
            [
              "Georeferencing",
              result.geographicLocation?.has_location && result.geographicLocation?.lat != null
                ? `${result.geographicLocation.lat.toFixed(4)}°N, ${result.geographicLocation.lng?.toFixed(4)}°E (${result.geographicLocation.crs || "WGS84"})`
                : "None (Un-georeferenced)",
            ],
            ["Location Target", result.geographicLocation?.location_name || "N/A"],
          ].map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <b>{value}</b>
            </div>
          ))}
        </div>
      )}
      <p className="disclaimer">{t("result.disclaimer")}</p>
    </div>
  )
}

function Dashboard({ navigate }: { navigate: (path: string) => void }) {
  const { t } = useTranslation()
  const [history, setHistory] = useState<AnalysisResponse[]>([])
  useEffect(() => setHistory(loadHistory()), [])

  const metricCards = [
    { label: t("metric.analyses"), value: "24", delta: t("metric.analyses_delta") },
    { label: t("metric.images"), value: "58", delta: t("metric.images_delta") },
    { label: t("metric.confidence"), value: "93%", delta: t("metric.confidence_delta") },
  ]

  return (
    <main className="page dashboard">
      <div className="page-intro">
        <div>
          <Pill>
            <span className="pulse" />
            {t("dash.pill")}
          </Pill>
          <h1>{t("dash.title")}</h1>
          <p>{t("dash.desc")}</p>
        </div>
        <button className="primary compact" onClick={() => navigate("/analysis")}>
          <ImagePlus /> {t("dash.btn_new")}
        </button>
      </div>
      <div className="metric-grid">
        {metricCards.map((metric) => (
          <div className="metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.delta}</small>
          </div>
        ))}
      </div>
      <section className="history-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">{t("hist.eyebrow")}</span>
            <h2>{t("hist.title")}</h2>
          </div>
          <div className="search">
            <Search />
            <input placeholder={t("hist.search")} />
          </div>
        </div>
        {history.length === 0 ? (
          <div className="history-empty">
            <Clock3 />
            <p>{t("hist.empty_desc")}</p>
            <button className="secondary" onClick={() => navigate("/analysis?demo=1")}>
              {t("hist.demo_btn")} <ArrowRight />
            </button>
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => (
              <button className="history-row" key={item.id} onClick={() => navigate("/analysis")}>
                <span>{formatDate(item.createdAt)}</span>
                <strong>{t(`mode.${item.mode}.label` as any)}</strong>
                <p>{item.query}</p>
                <Pill tone={item.confidence}>{Math.round(item.confidenceScore * 100)}%</Pill>
                <ArrowRight />
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

function Evaluation({ navigate }: { navigate: (path: string) => void }) {
  const { t } = useTranslation()

  const evaluationMetrics = [
    { label: t("eval.metric1.label"), value: 96, note: t("eval.metric1.note") },
    { label: t("eval.metric2.label"), value: 100, note: t("eval.metric2.note") },
    { label: t("eval.metric3.label"), value: 94, note: t("eval.metric3.note") },
  ]

  return (
    <main className="page evaluation">
      <div className="page-intro">
        <div>
          <Pill>
            <span className="pulse" />
            {t("eval.pill")}
          </Pill>
          <h1>{t("eval.title")}</h1>
          <p>{t("eval.desc")}</p>
        </div>
        <button className="secondary compact" onClick={() => navigate("/analysis")}>
          <Radar /> {t("eval.workspace_btn")}
        </button>
      </div>
      <div className="eval-grid">
        <section className="evaluation-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">{t("eval.signals.eyebrow")}</span>
              <h2>{t("eval.signals.title")}</h2>
            </div>
            <BarChart3 />
          </div>
          {evaluationMetrics.map((metric) => (
            <div className="eval-metric" key={metric.label}>
              <div>
                <strong>{metric.label}</strong>
                <span>{metric.note}</span>
              </div>
              <b>{metric.value}%</b>
              <div className="metric-bar">
                <span style={{ width: `${metric.value}%` }} />
              </div>
            </div>
          ))}
        </section>
        <section className="evaluation-card architecture">
          <span className="eyebrow">{t("eval.arch.eyebrow")}</span>
          <h2>
            {t("eval.arch.title1")}
            <br />
            <em>{t("eval.arch.title2")}</em>
          </h2>
          <div className="arch-flow">
            <span>{t("eval.arch.flow.inputs")}</span>
            <ArrowRight />
            <span>{t("eval.arch.flow.agent")}</span>
            <ArrowRight />
            <span>{t("eval.arch.flow.evidence")}</span>
          </div>
          <p>{t("eval.arch.desc")}</p>
          <button className="secondary" onClick={() => navigate("/analysis")}>
            {t("eval.scenario_btn")} <ArrowRight />
          </button>
        </section>
      </div>
    </main>
  )
}

function PageContent() {
  const { isAuthenticated } = useAuth()
  const pathname = usePathname()
  const [path, setPath] = useState(pathname || "/")
  const [initialDemo, setInitialDemo] = useState(false)
  const { t } = useTranslation()

  const navigate = (next: string) => {
    const clean = next.split("?")[0]
    setPath(clean)
    window.history.pushState({}, "", next)
  }

  useEffect(() => {
    if (typeof window !== "undefined") {
      setPath(window.location.pathname)
      setInitialDemo(window.location.search.includes("demo=1"))
    }
    const sync = () => setPath(window.location.pathname)
    window.addEventListener("popstate", sync)
    return () => window.removeEventListener("popstate", sync)
  }, [pathname])

  const page = useMemo(() => {
    if (path === "/") {
      return <Landing navigate={navigate} />
    }

    // Security clearance gate: require authentication for operational workspace, history, and telemetry
    if (!isAuthenticated) {
      return <AuthGate />
    }

    if (path === "/analysis") {
      return <Workspace navigate={navigate} initialDemo={initialDemo} />
    }
    if (path === "/dashboard") {
      return <Dashboard navigate={navigate} />
    }
    if (path === "/evaluation") {
      return <Evaluation navigate={navigate} />
    }

    return <Landing navigate={navigate} />
  }, [path, isAuthenticated, initialDemo])

  return (
    <div className="app-shell">
      <Header path={path} navigate={navigate} />
      {page}
      <footer>
        <span>{t("footer.left")}</span>
        <span>{t("footer.right")}</span>
      </footer>
    </div>
  )
}

export default function Page() {
  return (
    <I18nProvider>
      <PageContent />
    </I18nProvider>
  )
}
