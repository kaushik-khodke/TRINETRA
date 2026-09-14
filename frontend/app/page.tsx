"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Activity, ArrowRight, BarChart3, Check, ChevronDown, Clock3, ExternalLink, FileImage, GitCompareArrows, Globe, ImagePlus, Layers3, Maximize2, Menu, MoveHorizontal, PanelTop, Radar, Search, Send, ShieldCheck, Sparkles, Upload, X } from "lucide-react"
import {
  analysisAPI,
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
} from "@/lib/types"
import { I18nProvider, useTranslation, type SupportedLanguage } from "@/lib/i18n"
import { HsiViewer } from "@/components/hyperspectral/HsiViewer"

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
          {image.name.toLowerCase().endsWith(".mat") ||
          image.name.toLowerCase().endsWith(".hdr") ||
          image.name.toLowerCase().endsWith(".dat") ? (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                background: "linear-gradient(135deg, #064e3b 0%, #022c22 100%)",
                color: "#10b981",
                gap: "8px",
              }}
            >
              <Layers3 size={40} />
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 600,
                  letterSpacing: "1px",
                  textTransform: "uppercase",
                }}
              >
                Hyperspectral Cube
              </span>
            </div>
          ) : image.name.toLowerCase().endsWith(".tif") ||
            image.name.toLowerCase().endsWith(".tiff") ? (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                background: "linear-gradient(135deg, #0c2d38 0%, #071920 100%)",
                color: "#56d7df",
                gap: "8px",
              }}
            >
              <Globe size={40} />
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 600,
                  letterSpacing: "1px",
                  textTransform: "uppercase",
                }}
              >
                GeoTIFF Satellite Raster
              </span>
            </div>
          ) : (
            <img src={image.url} alt={t("aria.preview")} onError={(e) => { (e.target as HTMLElement).style.display = "none" }} />
          )}
          <div className="slot-overlay">
            <Pill tone="dark">{slot.hint}</Pill>
            <strong>{image.name}</strong>
            <span>{formatBytes(image.size)}</span>
            {image.geographicLocation?.has_location && (
              <span style={{ fontSize: "10px", color: "#56d7df", marginTop: "2px", fontFamily: "monospace" }}>
                📍 {image.geographicLocation.lat?.toFixed(3)}°N, {image.geographicLocation.lng?.toFixed(3)}°E
              </span>
            )}
          </div>
          {image.globeUrl && (
            <a
              href={image.globeUrl}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              title="View in Shatnetra 3D Earth Globe"
              style={{
                position: "absolute",
                top: "8px",
                right: "38px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "4px 9px",
                borderRadius: "6px",
                background: "linear-gradient(135deg, rgba(86, 215, 223, 0.25) 0%, rgba(16, 185, 129, 0.25) 100%)",
                border: "1px solid #56d7df",
                color: "#56d7df",
                fontSize: "11px",
                fontWeight: 700,
                textDecoration: "none",
                zIndex: 10,
                backdropFilter: "blur(4px)",
                boxShadow: "0 0 12px rgba(86, 215, 223, 0.35)",
              }}
            >
              <Globe size={12} /> 3D Globe <ArrowRight size={10} />
            </a>
          )}
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
            accept="image/png,image/jpeg,image/tiff,.tif,.tiff,.mat,.hdr,.dat"
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

  const addImage = async (file: File, index: number) => {
    const norm = normalizeFile(
      file,
      slots[index]?.label || "Image",
      mode === "fusion" ? (index === 0 ? "OPTICAL" : "SAR") : undefined
    )
    setImages((current) => {
      const next = [...current]
      next[index] = norm
      return next
    })

    // Pre-inspect raster asynchronously to extract coordinates and 3D globe link immediately
    if (file.name.match(/\.(tif|tiff|mat|hdr|png|jpe?g)$/i)) {
      try {
        const inspectRes = await analysisAPI.inspectImage(file)
        if (inspectRes.globeUrl || inspectRes.geographicLocation?.has_location) {
          setImages((current) => {
            const next = [...current]
            if (next[index]) {
              next[index] = {
                ...next[index],
                globeUrl: inspectRes.globeUrl,
                geographicLocation: inspectRes.geographicLocation,
              }
            }
            return next
          })
        }
      } catch (err) {
        console.warn("[Workspace] Pre-inspect error:", err)
      }
    }
  }

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
      try {
        saveHistory(response)
      } catch (storageErr) {
        console.warn("[Workspace] Failed to persist history in localStorage:", storageErr)
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Satellite analysis failed on local backend.")
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    const isDemo = initialDemo || (typeof window !== "undefined" && window.location.search.includes("demo=1"))
    if (isDemo && !result) {
      setTimeout(() => run(), 450)
    }
  }, [initialDemo])

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
          {!query.trim() && images.filter(Boolean).length > 0 && (
            <div style={{ fontSize: "11px", color: "rgba(86, 215, 223, 0.75)", margin: "4px 0 14px", display: "flex", alignItems: "center", gap: "6px" }}>
              <Sparkles size={13} style={{ flexShrink: 0 }} />
              <span>Type your question above or click one of the suggested prompts to enable analysis.</span>
            </div>
          )}
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

  const [viewMode, setViewMode] = useState<"single" | "side_by_side" | "overlay">("single")
  const [sliderPos, setSliderPos] = useState<number>(50)
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100))
    setSliderPos(Math.round(pct))
  }

  const baseImg = result.rawImageUrl || (result.images && result.images[0]?.url) || "/satellite-optical.svg"
  const overlayImg = result.overlayImageUrl || (result.images && result.images.length > 1 ? result.images[1]?.url : null) || baseImg
  const baseLabel = result.mode === "temporal" ? "TIME 1 (BEFORE)" : result.mode === "fusion" ? "OPTICAL (MSI)" : "ORIGINAL RASTER"
  const overlayLabel = result.mode === "temporal" ? "TIME 2 (AFTER)" : result.mode === "fusion" ? "SAR (RADAR)" : "GROUNDED EVIDENCE"

  const globeUrl = result.globeUrl || (result.images && (result.images[0] as any)?.globeUrl)
  const geo = result.geographicLocation || (result.images && (result.images[0] as any)?.geographicLocation)

  return (
    <div className="evidence">
      <div className="evidence-head">
        <div>
          <span className="eyebrow">{headEyebrow}</span>
          <h3>{t("evidence.head.title")}</h3>
        </div>
        <div className="viewer-controls" style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
          <button
            type="button"
            className={viewMode === "single" ? "active" : ""}
            onClick={() => setViewMode("single")}
            title="Single primary raster view"
          >
            <Maximize2 size={13} /> Single
          </button>
          <button
            type="button"
            className={viewMode === "side_by_side" ? "active" : ""}
            onClick={() => setViewMode(viewMode === "side_by_side" ? "single" : "side_by_side")}
            title="Side-by-side comparison"
          >
            <PanelTop size={13} /> {t("viewer.side_by_side")}
          </button>
          <button
            type="button"
            className={viewMode === "overlay" ? "active" : ""}
            onClick={() => setViewMode(viewMode === "overlay" ? "single" : "overlay")}
            title="Curtain swipe overlay comparison"
          >
            <Layers3 size={13} /> {t("viewer.overlay")}
          </button>
          {globeUrl && (
            <a
              href={globeUrl}
              target="_blank"
              rel="noreferrer"
              title="Fly directly to this satellite scene in Shatnetra 3D Earth Globe"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "6px 12px",
                borderRadius: "6px",
                background: "linear-gradient(135deg, rgba(86, 215, 223, 0.25) 0%, rgba(16, 185, 129, 0.25) 100%)",
                border: "1px solid #56d7df",
                color: "#56d7df",
                fontSize: "12px",
                fontWeight: 700,
                textDecoration: "none",
                boxShadow: "0 0 16px rgba(86, 215, 223, 0.35)",
                marginLeft: "4px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <Globe size={14} style={{ color: "#56d7df" }} /> 3D Globe (Shatnetra) <ExternalLink size={11} />
            </a>
          )}
        </div>
      </div>

      {viewMode === "side_by_side" ? (
        <div className="side-by-side-grid">
          <div className="side-panel">
            <img src={baseImg} alt={baseLabel} />
            <div className="side-badge">
              <i className="cyan-dot" /> {baseLabel}
            </div>
          </div>
          <div className="side-panel">
            <img src={overlayImg} alt={overlayLabel} />
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
            <div className="side-badge">
              <i className="amber-dot" /> {overlayLabel}
            </div>
          </div>
        </div>
      ) : viewMode === "overlay" ? (
        <div>
          <div
            ref={containerRef}
            className="curtain-viewer"
            onPointerDown={(e) => {
              setIsDragging(true)
              if (containerRef.current) {
                const rect = containerRef.current.getBoundingClientRect()
                const pct = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
                setSliderPos(Math.round(pct))
              }
            }}
            onPointerMove={handlePointerMove}
            onPointerUp={() => setIsDragging(false)}
            onPointerCancel={() => setIsDragging(false)}
          >
            <img className="curtain-base-img" src={baseImg} alt={baseLabel} />
            <div
              className="curtain-overlay-wrap"
              style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
              <img className="curtain-overlay-img" src={overlayImg} alt={overlayLabel} />
            </div>
            <div className="curtain-divider" style={{ left: `${sliderPos}%` }}>
              <div className="curtain-handle">
                <MoveHorizontal size={14} />
              </div>
            </div>
            <div className="curtain-tag left">{baseLabel} ({sliderPos}%)</div>
            <div className="curtain-tag right">{overlayLabel}</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "10px", padding: "0 4px" }}>
            <span style={{ fontSize: "11px", color: "#56d7df", fontFamily: "monospace", minWidth: "75px" }}>
              {sliderPos}% Split
            </span>
            <input
              type="range"
              min="0"
              max="100"
              value={sliderPos}
              onChange={(e) => setSliderPos(Number(e.target.value))}
              style={{ flex: 1, accentColor: "#56d7df", cursor: "ew-resize" }}
            />
            <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.5)", fontFamily: "monospace" }}>
              100% Overlay
            </span>
          </div>
        </div>
      ) : (
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
      )}

      {geo?.has_location && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 12px",
            background: "rgba(86, 215, 223, 0.08)",
            border: "1px solid rgba(86, 215, 223, 0.25)",
            borderRadius: "6px",
            marginTop: "10px",
            fontSize: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ color: "#56d7df", fontWeight: 700 }}>📍 Geospatial Target:</span>
            <code style={{ color: "#ffffff", background: "rgba(0,0,0,0.4)", padding: "2px 6px", borderRadius: "4px" }}>
              {geo.lat?.toFixed(4)}°N, {geo.lng?.toFixed(4)}°E
            </code>
            <span style={{ color: "rgba(255, 255, 255, 0.7)", fontSize: "11px" }}>
              ({geo.location_name || "Satellite Target"})
            </span>
          </div>
          {globeUrl && (
            <a
              href={globeUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                color: "#56d7df",
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                textDecoration: "underline",
              }}
            >
              Launch Cesium 3D Flight <ArrowRight size={12} />
            </a>
          )}
        </div>
      )}

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
      {result.hsiData?.isHsi ? (
        <HsiViewer {...result.hsiData} />
      ) : (
        <EvidenceViewer result={result} />
      )}
      <div className="evidence-list">
        {result.evidence.map((item, index) => (
          <div key={item}>
            <span>0{index + 1}</span>
            {item}
            <Check />
          </div>
        ))}
      </div>
      <div style={{ marginTop: "1.2rem", marginBottom: "0.8rem", display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
        {result.globeUrl && (
          <a
            href={result.globeUrl}
            target="_blank"
            rel="noreferrer"
            className="compact"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.65rem 1.2rem",
              borderRadius: "8px",
              textDecoration: "none",
              background: "linear-gradient(135deg, rgba(86, 215, 223, 0.18) 0%, rgba(16, 185, 129, 0.18) 100%)",
              border: "1px solid rgba(86, 215, 223, 0.5)",
              color: "#56d7df",
              fontSize: "0.85rem",
              fontWeight: 700,
              boxShadow: "0 0 20px rgba(86, 215, 223, 0.18)",
              transition: "all 0.2s ease",
            }}
          >
            <Globe size={16} style={{ color: "#56d7df" }} /> View in 3D Earth Globe (Shatnetra) <ArrowRight size={14} />
          </a>
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
              padding: "0.65rem 1.2rem",
              borderRadius: "8px",
              textDecoration: "none",
              background: "rgba(0, 240, 255, 0.08)",
              border: "1px solid rgba(0, 240, 255, 0.25)",
              color: "var(--cyan-400, #00f0ff)",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <PanelTop size={16} /> {t("btn.report")} <ArrowRight size={14} />
          </a>
        )}
        {result.geographicLocation?.has_location && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              fontFamily: "monospace",
              fontSize: "11px",
              color: "rgba(86, 215, 223, 0.8)",
              background: "rgba(0, 0, 0, 0.35)",
              border: "1px solid rgba(86, 215, 223, 0.2)",
              padding: "5px 9px",
              borderRadius: "6px",
            }}
          >
            📍 {result.geographicLocation.lat?.toFixed(4)}°N, {result.geographicLocation.lng?.toFixed(4)}°E
          </span>
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
  const pathname = usePathname()
  const router = useRouter()
  const [path, setPath] = useState(pathname || "/")
  const { t } = useTranslation()

  useEffect(() => {
    if (pathname) {
      setPath(pathname)
    }
  }, [pathname])

  const navigate = (next: string) => {
    const clean = next.split("?")[0]
    setPath(clean)
    router.push(next)
  }

  useEffect(() => {
    const sync = () => setPath(window.location.pathname)
    window.addEventListener("popstate", sync)
    return () => window.removeEventListener("popstate", sync)
  }, [])

  const page = useMemo(
    () =>
      path === "/analysis" ? (
        <Workspace navigate={navigate} initialDemo={false} />
      ) : path === "/dashboard" ? (
        <Dashboard navigate={navigate} />
      ) : path === "/evaluation" ? (
        <Evaluation navigate={navigate} />
      ) : (
        <Landing navigate={navigate} />
      ),
    [path]
  )

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
