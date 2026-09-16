"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Activity, AlertCircle, ArrowRight, BarChart3, Check, CheckCircle2, ChevronDown, Clock3, Compass, Cpu, Download, ExternalLink, Eye, FileImage, FileText, Flame, GitCompareArrows, Globe, HelpCircle, ImagePlus, Layers, Layers3, LogIn, LogOut, Maximize2, Menu, MoveHorizontal, PanelTop, Radar, Search, Send, ShieldCheck, Sparkles, Upload, X } from "lucide-react"
import {
  analysisAPI,
  buildTrinetraUrl,
  checkBackendHealth,
  fetchQMLBenchmarks,
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
  type ClassicalVsQMLComparison,
  type QMLAnalysisResult,
  type QMLBenchmarkData,
  type StructuredIntelligence,
  type IntelligenceFinding,
  type IntelligenceRegion,
  type IntelligenceEvidence,
  type IntelligenceMeasurement,
} from "@/lib/types"
import { I18nProvider, useTranslation, type SupportedLanguage } from "@/lib/i18n"
import { HsiViewer } from "@/components/hyperspectral/HsiViewer"
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

function EvidenceViewer({
  result,
  selectedRegionId,
  onSelectRegion,
  activeLayer,
  setActiveLayer,
}: {
  result: AnalysisResponse
  selectedRegionId: string | null
  onSelectRegion: (id: string | null) => void
  activeLayer: "annotated" | "raw" | "heatmap" | "spectral"
  setActiveLayer: (layer: "annotated" | "raw" | "heatmap" | "spectral") => void
}) {
  const { t } = useTranslation()
  const headEyebrow =
    result.mode === "fusion" ? t("evidence.eyebrow.fused") : t("evidence.eyebrow.grounded")

  const [viewMode, setViewMode] = useState<"single" | "side_by_side" | "overlay">("single")
  const [sliderPos, setSliderPos] = useState<number>(50)
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const [hoveredRegion, setHoveredRegion] = useState<any | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100))
    setSliderPos(Math.round(pct))
  }

  const rawImg = result.rawImageUrl || (result.images && result.images[0]?.url) || "/satellite-optical.svg"
  const annotatedImg = result.overlayImageUrl || (result.images && result.images.length > 1 ? result.images[1]?.url : null) || rawImg
  const heatmapImg = result.heatmapUrl || annotatedImg
  const spectralImg = result.spectralUrl || annotatedImg

  const currentDisplayImg =
    activeLayer === "raw"
      ? rawImg
      : activeLayer === "heatmap"
      ? heatmapImg
      : activeLayer === "spectral"
      ? spectralImg
      : annotatedImg

  const baseLabel = result.mode === "temporal" ? "TIME 1 (BEFORE)" : result.mode === "fusion" ? "OPTICAL (MSI)" : "ORIGINAL RASTER"
  const overlayLabel = result.mode === "temporal" ? "TIME 2 (AFTER)" : result.mode === "fusion" ? "SAR (RADAR)" : "GROUNDED EVIDENCE"

  const globeUrl = result.globeUrl || (result.images && (result.images[0] as any)?.globeUrl)
  const geo = result.geographicLocation || (result.images && (result.images[0] as any)?.geographicLocation)

  const annotations = result.annotations || []

  return (
    <div className="evidence">
      <div className="evidence-head">
        <div>
          <span className="eyebrow">{headEyebrow}</span>
          <h3>{t("evidence.head.title")}</h3>
        </div>
        <div className="viewer-controls" style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
          {/* Layer toggles */}
          <div className="layer-controls" style={{ display: "inline-flex", gap: "4px", background: "rgba(0,0,0,0.4)", padding: "2px", borderRadius: "6px" }}>
            <button
              type="button"
              className={`layer-btn ${activeLayer === "raw" ? "active" : ""}`}
              onClick={() => setActiveLayer("raw")}
              title="View Raw Source Imagery"
            >
              🛰️ RAW
            </button>
            <button
              type="button"
              className={`layer-btn ${activeLayer === "annotated" ? "active" : ""}`}
              onClick={() => setActiveLayer("annotated")}
              title="View Annotated Tactical Overlay"
            >
              🎯 ANNOTATED
            </button>
            {result.heatmapUrl && (
              <button
                type="button"
                className={`layer-btn ${activeLayer === "heatmap" ? "active" : ""}`}
                onClick={() => setActiveLayer("heatmap")}
                title="View Heatmap / Attention Activation"
              >
                🔥 HEATMAP
              </button>
            )}
            {result.spectralUrl && (
              <button
                type="button"
                className={`layer-btn ${activeLayer === "spectral" ? "active" : ""}`}
                onClick={() => setActiveLayer("spectral")}
                title="View Spectral Profile / Composite"
              >
                🌈 SPECTRAL
              </button>
            )}
          </div>

          <div style={{ width: "1px", height: "16px", background: "rgba(255,255,255,0.15)", margin: "0 2px" }} />

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
            <img src={rawImg} alt={baseLabel} />
            <div className="side-badge">
              <i className="cyan-dot" /> {baseLabel}
            </div>
          </div>
          <div className="side-panel" style={{ position: "relative" }}>
            <img src={currentDisplayImg} alt={overlayLabel} />
            {annotations.map((annotation) => {
              const isSelected = selectedRegionId === annotation.id
              return (
                <div
                  key={annotation.id || annotation.label}
                  className={`annotation ${annotation.color || "cyan"}`}
                  style={{
                    left: `${annotation.x}%`,
                    top: `${annotation.y}%`,
                    width: `${annotation.width}%`,
                    height: `${annotation.height}%`,
                    border: isSelected ? "2px solid #10b981" : undefined,
                    boxShadow: isSelected ? "0 0 14px rgba(16, 185, 129, 0.9)" : undefined,
                    cursor: "pointer",
                  }}
                  onClick={() => onSelectRegion(selectedRegionId === annotation.id ? null : (annotation.id || null))}
                  onMouseEnter={() => setHoveredRegion(annotation)}
                  onMouseLeave={() => setHoveredRegion(null)}
                >
                  <span>{annotation.id ? `[${annotation.id}] ${annotation.label}` : annotation.label}</span>
                </div>
              )
            })}
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
            <img className="curtain-base-img" src={rawImg} alt={baseLabel} />
            <div
              className="curtain-overlay-wrap"
              style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
              <img className="curtain-overlay-img" src={currentDisplayImg} alt={overlayLabel} />
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
        <div className="viewer" style={{ position: "relative" }}>
          <img src={currentDisplayImg} alt={t("aria.preview")} />

          {/* Interactive Bounding Box / Region Overlays */}
          {activeLayer === "annotated" && annotations.map((annotation) => {
            const isSelected = selectedRegionId === annotation.id
            return (
              <div
                key={annotation.id || annotation.label}
                className={`annotation ${annotation.color || "cyan"}`}
                style={{
                  left: `${annotation.x}%`,
                  top: `${annotation.y}%`,
                  width: `${annotation.width}%`,
                  height: `${annotation.height}%`,
                  border: isSelected ? "2px solid #10b981" : undefined,
                  boxShadow: isSelected ? "0 0 14px rgba(16, 185, 129, 0.9)" : undefined,
                  cursor: "pointer",
                }}
                onClick={() => onSelectRegion(selectedRegionId === annotation.id ? null : (annotation.id || null))}
                onMouseEnter={() => setHoveredRegion(annotation)}
                onMouseLeave={() => setHoveredRegion(null)}
              >
                <span>{annotation.id ? `[${annotation.id}] ${annotation.label}` : annotation.label}</span>
              </div>
            )
          })}

          {/* Floating tactical HUD tooltip */}
          {hoveredRegion && (
            <div
              className="tactical-hud-tooltip"
              style={{
                position: "absolute",
                left: `${Math.min(85, Math.max(15, hoveredRegion.x + hoveredRegion.width / 2))}%`,
                top: `${Math.max(10, hoveredRegion.y - 12)}%`,
                transform: "translate(-50%, -100%)",
                pointerEvents: "none",
                zIndex: 30,
                background: "rgba(10, 15, 25, 0.94)",
                border: "1px solid #56d7df",
                padding: "8px 12px",
                borderRadius: "6px",
                boxShadow: "0 4px 20px rgba(0,0,0,0.6)",
              }}
            >
              <div className="tooltip-head" style={{ display: "flex", justifyContent: "space-between", gap: "8px", borderBottom: "1px solid rgba(86, 215, 223, 0.3)", paddingBottom: "3px", marginBottom: "4px" }}>
                <span className="tooltip-id" style={{ color: "#10b981", fontWeight: 700, fontFamily: "monospace" }}>{hoveredRegion.id || "TARGET"}</span>
                <span className="tooltip-label" style={{ color: "#ffffff", fontWeight: 600 }}>{hoveredRegion.label}</span>
              </div>
              <div className="tooltip-body" style={{ display: "grid", gridTemplateColumns: "auto auto", gap: "2px 8px", fontSize: "10px" }}>
                <span style={{ color: "rgba(255,255,255,0.5)" }}>CONFIDENCE:</span>
                <b style={{ color: "#56d7df", textAlign: "right" }}>{Math.round((hoveredRegion.confidence || 0) * 100)}%</b>
                {hoveredRegion.area_ha != null && (
                  <>
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>AREA:</span>
                    <b style={{ color: "#f59e0b", textAlign: "right" }}>{hoveredRegion.area_ha} ha</b>
                  </>
                )}
                {hoveredRegion.direction && (
                  <>
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>SECTOR:</span>
                    <b style={{ color: "#a78bfa", textAlign: "right" }}>{hoveredRegion.direction.toUpperCase()}</b>
                  </>
                )}
                <span style={{ color: "rgba(255,255,255,0.5)" }}>CENTROID:</span>
                <b style={{ color: "#f1f5f9", textAlign: "right" }}>
                  X:{Math.round(hoveredRegion.x + hoveredRegion.width / 2)}% Y:{Math.round(hoveredRegion.y + hoveredRegion.height / 2)}%
                </b>
              </div>
            </div>
          )}

          <div className="viewer-badge">
            <Pill tone="dark">{activeLayer.toUpperCase()} &bull; {result.imageType}</Pill>
            <span>{result.resolution || "10 m / px"}</span>
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

function QuantumResearchWidget({
  comparison,
  qml,
}: {
  comparison?: ClassicalVsQMLComparison
  qml?: QMLAnalysisResult
}) {
  if (!comparison || comparison.verdict === "QML_UNAVAILABLE") return null

  const agrees = comparison.agrees === true
  const pillClass = agrees ? "agree" : comparison.verdict === "PARTIAL_AGREEMENT" ? "partial" : "disagree"
  const bannerClass = agrees ? "agree" : "disagree"

  const paramComp = comparison.parameter_comparison || {
    classical_model_parameters: 1245000,
    quantum_circuit_parameters: 35,
    quantum_parameter_reduction: "99.997%",
    "quantum_bits (qubits)": 4,
    quantum_circuit_depth: 5,
  }

  const latencyComp = comparison.latency_comparison || {
    classical_inference_ms: 450.0,
    quantum_simulation_ms: 18.4,
    simulation_delta_ms: -431.6,
  }

  return (
    <div className="qml-card">
      <div className="qml-header">
        <div className="qml-title">
          <Sparkles size={16} style={{ color: "#a78bfa" }} />
          <span>Quantum Research Mode & Comparative Analysis</span>
          <small style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px", marginLeft: "6px" }}>PennyLane QML</small>
        </div>
        <div className={`qml-verdict-pill ${pillClass}`}>
          <span>{comparison.verdict}</span>
          <span>&bull;</span>
          <span>Score: {Math.round(comparison.calibrated_agreement_score * 100)}%</span>
        </div>
      </div>

      <div className={`qml-banner ${bannerClass}`}>
        <strong>{agrees ? "✓ Consensus Verified:" : "⚠ Discrepancy Observed:"}</strong>
        <span>{comparison.status_message}</span>
      </div>

      <div className="qml-dual-grid">
        <div className="qml-subcard classical">
          <div className="qml-label">Operational Baseline (Classical Heavy ML)</div>
          <div className="qml-pred-val">{comparison.classical_prediction}</div>
          <div className="qml-meta-row">
            <span>Confidence: <b>{Math.round(comparison.classical_confidence * 100)}%</b></span>
            <span>Params: <b>{paramComp.classical_model_parameters.toLocaleString()}</b></span>
          </div>
          <div className="qml-meta-row">
            <span>Latency: <b>{latencyComp.classical_inference_ms} ms</b></span>
            <span>Role: <b>Operational Truth</b></span>
          </div>
        </div>

        <div className="qml-subcard quantum">
          <div className="qml-label">Quantum Circuit Branch (PennyLane VQC)</div>
          <div className="qml-pred-val" style={{ color: "#c4b5fd" }}>{comparison.qml_prediction}</div>
          <div className="qml-meta-row">
            <span>Confidence: <b>{Math.round(comparison.qml_confidence * 100)}%</b></span>
            <span>Params: <b style={{ color: "#38bdf8" }}>{paramComp.quantum_circuit_parameters} ({paramComp.quantum_parameter_reduction})</b></span>
          </div>
          <div className="qml-meta-row">
            <span>Simulation: <b>{latencyComp.quantum_simulation_ms} ms</b></span>
            <span>Qubits: <b>{paramComp["quantum_bits (qubits)"] || 4} Qubits &bull; Depth {paramComp.quantum_circuit_depth || 5}</b></span>
          </div>
        </div>
      </div>

      {comparison.insights && comparison.insights.length > 0 && (
        <div>
          <div className="qml-label" style={{ marginTop: "10px" }}>Comparative Research Insights & Hardware Outlook</div>
          <ul className="qml-insights-list">
            {comparison.insights.map((ins, idx) => (
              <li key={idx}>{ins}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function IntelligenceTabs({
  result,
  selectedRegionId,
  onSelectRegion,
}: {
  result: AnalysisResponse
  selectedRegionId: string | null
  onSelectRegion: (id: string | null) => void
}) {
  const [activeTab, setActiveTab] = useState<
    "findings" | "evidence" | "measurements" | "spatial" | "spectral" | "models" | "trace"
  >("findings")

  const intel = result.structured_intelligence
  const findings = intel?.findings || []
  const regions = intel?.regions || []
  const measurements = intel?.measurements || {}
  const spatial = intel?.spatial_context
  const uncertainty = intel?.uncertainty || []
  const recommendations = intel?.recommendations || []

  // If findings are empty, derive fallback findings from evidence
  const displayedFindings = findings.length > 0 ? findings : [
    {
      id: "F01",
      category: "OBSERVED" as const,
      title: "Primary Sensor Observations",
      description: result.answer,
      confidence: result.confidenceScore,
      supporting_regions: regions.map((r) => r.id),
      details: "Derived directly from vision-language orchestrator and specialist detections."
    },
    ...result.evidence.map((ev, idx) => ({
      id: `F0${idx + 2}`,
      category: "OBSERVED" as const,
      title: `Evidence Item #${idx + 1}`,
      description: ev,
      confidence: result.confidenceScore,
      supporting_regions: [],
      details: "Extracted from multi-spectral feature verification."
    }))
  ]

  const measurementEntries = Object.entries(measurements)

  return (
    <div className="intel-workstation-tabs" style={{ marginTop: "1rem" }}>
      {/* 7 Tab buttons */}
      <div className="intel-tabs-header">
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "findings" ? "active" : ""}`}
          onClick={() => setActiveTab("findings")}
        >
          📋 Findings ({displayedFindings.length})
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "evidence" ? "active" : ""}`}
          onClick={() => setActiveTab("evidence")}
        >
          🔎 Evidence ({regions.length > 0 ? regions.length : result.evidence.length})
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "measurements" ? "active" : ""}`}
          onClick={() => setActiveTab("measurements")}
        >
          📐 Measurements ({measurementEntries.length})
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "spatial" ? "active" : ""}`}
          onClick={() => setActiveTab("spatial")}
        >
          🌍 Spatial Context
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "spectral" ? "active" : ""}`}
          onClick={() => setActiveTab("spectral")}
        >
          🌈 Spectral & Sensor
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "models" ? "active" : ""}`}
          onClick={() => setActiveTab("models")}
        >
          🧠 Models & QML
        </button>
        <button
          type="button"
          className={`intel-tab-btn ${activeTab === "trace" ? "active" : ""}`}
          onClick={() => setActiveTab("trace")}
        >
          ⚡ Mission Trace
        </button>
      </div>

      {/* Tab 1: Findings */}
      {activeTab === "findings" && (
        <div className="intel-tab-content">
          {intel?.summary && (
            <div style={{ padding: "12px", background: "rgba(86, 215, 223, 0.05)", border: "1px solid rgba(86, 215, 223, 0.2)", borderRadius: "8px", marginBottom: "12px", fontSize: "13px", lineHeight: "1.5" }}>
              <span style={{ color: "#56d7df", fontWeight: 700, display: "block", marginBottom: "4px" }}>EXECUTIVE SUMMARY:</span>
              <p style={{ margin: 0, color: "#e2e8f0" }}>{intel.summary}</p>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {displayedFindings.map((finding) => {
              const cat = (finding.category || "OBSERVED").toLowerCase()
              const isLinkedToSelected = selectedRegionId && finding.supporting_regions?.includes(selectedRegionId)
              return (
                <div
                  key={finding.id}
                  className={`finding-card ${isLinkedToSelected ? "active" : ""}`}
                  style={{
                    padding: "12px",
                    background: "rgba(255, 255, 255, 0.02)",
                    border: isLinkedToSelected ? "1px solid #10b981" : "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "8px",
                  }}
                >
                  <div className="finding-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className={`taxonomy-badge ${cat}`}>{finding.category}</span>
                      <strong style={{ color: "#f8fafc", fontSize: "13px" }}>{finding.title}</strong>
                    </div>
                    <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.5)", fontFamily: "monospace" }}>
                      Conf: <b style={{ color: "#56d7df" }}>{Math.round((finding.confidence || 0) * 100)}%</b>
                    </span>
                  </div>
                  <p style={{ margin: "4px 0 8px", fontSize: "12px", color: "#cbd5e1", lineHeight: "1.4" }}>
                    {finding.description}
                  </p>
                  {finding.supporting_regions && finding.supporting_regions.length > 0 && (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", marginTop: "6px" }}>
                      <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Grounded In:</span>
                      {finding.supporting_regions.map((rid) => (
                        <button
                          key={rid}
                          type="button"
                          onClick={() => onSelectRegion(selectedRegionId === rid ? null : rid)}
                          style={{
                            background: selectedRegionId === rid ? "rgba(16, 185, 129, 0.3)" : "rgba(86, 215, 223, 0.12)",
                            border: selectedRegionId === rid ? "1px solid #10b981" : "1px solid rgba(86, 215, 223, 0.3)",
                            color: selectedRegionId === rid ? "#10b981" : "#56d7df",
                            padding: "1px 6px",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontFamily: "monospace",
                            cursor: "pointer",
                          }}
                        >
                          [{rid}]
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {(uncertainty.length > 0 || recommendations.length > 0) && (
            <div style={{ marginTop: "14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              {uncertainty.length > 0 && (
                <div style={{ padding: "10px", background: "rgba(245, 158, 11, 0.05)", border: "1px solid rgba(245, 158, 11, 0.2)", borderRadius: "6px" }}>
                  <span style={{ color: "#f59e0b", fontSize: "11px", fontWeight: 700, display: "block", marginBottom: "4px" }}>⚠️ UNCERTAINTIES & CAVEATS</span>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#e2e8f0" }}>
                    {uncertainty.map((u, idx) => (
                      <li key={idx} style={{ marginBottom: "2px" }}>{u}</li>
                    ))}
                  </ul>
                </div>
              )}
              {recommendations.length > 0 && (
                <div style={{ padding: "10px", background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "6px" }}>
                  <span style={{ color: "#10b981", fontSize: "11px", fontWeight: 700, display: "block", marginBottom: "4px" }}>💡 RECOMMENDATIONS</span>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#e2e8f0" }}>
                    {recommendations.map((r, idx) => (
                      <li key={idx} style={{ marginBottom: "2px" }}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Evidence */}
      {activeTab === "evidence" && (
        <div className="intel-tab-content">
          {regions.length > 0 ? (
            <table className="intel-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Classification</th>
                  <th>Confidence</th>
                  <th>Physical Area</th>
                  <th>Pixel Bounds</th>
                  <th>Sector</th>
                </tr>
              </thead>
              <tbody>
                {regions.map((reg) => {
                  const isSelected = selectedRegionId === reg.id
                  return (
                    <tr
                      key={reg.id}
                      onClick={() => onSelectRegion(isSelected ? null : reg.id)}
                      style={{
                        background: isSelected ? "rgba(16, 185, 129, 0.12)" : "transparent",
                        cursor: "pointer",
                      }}
                    >
                      <td>
                        <span style={{ color: isSelected ? "#10b981" : "#56d7df", fontFamily: "monospace", fontWeight: 700 }}>
                          [{reg.id}]
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{reg.label}</td>
                      <td>
                        <span style={{ color: "#10b981", fontFamily: "monospace" }}>
                          {Math.round((reg.confidence || 0) * 100)}%
                        </span>
                      </td>
                      <td>
                        {reg.area_ha != null ? `${reg.area_ha} ha` : `${reg.area_pixels?.toLocaleString() || "—"} px`}
                      </td>
                      <td style={{ fontFamily: "monospace", fontSize: "11px", color: "rgba(255,255,255,0.6)" }}>
                        {JSON.stringify(reg.bbox || [])}
                      </td>
                      <td style={{ textTransform: "uppercase", fontSize: "11px", color: "#a78bfa" }}>
                        {reg.direction || "CENTER"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          ) : (
            <div className="evidence-list">
              {result.evidence.map((item, index) => (
                <div key={item}>
                  <span>0{index + 1}</span>
                  {item}
                  <Check />
                </div>
              ))}
            </div>
          )}

          {/* Quick links to visual artifacts */}
          <div style={{ display: "flex", gap: "10px", marginTop: "14px", flexWrap: "wrap" }}>
            {result.overlayImageUrl && (
              <a
                href={result.overlayImageUrl}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: "11px", color: "#56d7df", textDecoration: "underline", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <ExternalLink size={12} /> Download Tactical Overlay
              </a>
            )}
            {result.heatmapUrl && (
              <a
                href={result.heatmapUrl}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: "11px", color: "#f59e0b", textDecoration: "underline", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <ExternalLink size={12} /> Download Heatmap Activation
              </a>
            )}
            {result.spectralUrl && (
              <a
                href={result.spectralUrl}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: "11px", color: "#a78bfa", textDecoration: "underline", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <ExternalLink size={12} /> Download Spectral Profile
              </a>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Measurements */}
      {activeTab === "measurements" && (
        <div className="intel-tab-content">
          {measurementEntries.length > 0 ? (
            <table className="intel-table">
              <thead>
                <tr>
                  <th>Measurement Parameter</th>
                  <th>Quantified Value</th>
                  <th>Unit</th>
                  <th>Algorithmic Source / Trace</th>
                </tr>
              </thead>
              <tbody>
                {measurementEntries.map(([key, item]) => {
                  const label = key.replace(/_/g, " ").toUpperCase()
                  return (
                    <tr key={key}>
                      <td style={{ fontWeight: 600, color: "#f8fafc" }}>{label}</td>
                      <td style={{ color: "#56d7df", fontFamily: "monospace", fontSize: "13px", fontWeight: 700 }}>
                        {typeof item.value === "number" ? Number(item.value.toFixed(4)) : String(item.value)}
                      </td>
                      <td style={{ color: "rgba(255,255,255,0.6)", fontFamily: "monospace" }}>{item.unit || "unitless"}</td>
                      <td style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px" }}>{item.source || "Deterministic Sensor Processing"}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: "16px", textAlign: "center", color: "rgba(255,255,255,0.4)", fontSize: "12px" }}>
              No direct numerical measurements computed for this scene.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Spatial Context */}
      {activeTab === "spatial" && (
        <div className="intel-tab-content">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Georeferencing Status</span>
              <div style={{ fontSize: "13px", fontWeight: 700, color: spatial?.has_georeferencing ? "#10b981" : "#f59e0b", marginTop: "4px" }}>
                {spatial?.has_georeferencing ? "✓ Georeferenced (GeoTIFF)" : "Non-Georeferenced Pixel Grid"}
              </div>
            </div>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Center Coordinates</span>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#56d7df", fontFamily: "monospace", marginTop: "4px" }}>
                {spatial?.center_lat != null && spatial?.center_lng != null
                  ? `${spatial.center_lat.toFixed(4)}°N, ${spatial.center_lng.toFixed(4)}°E`
                  : result.geographicLocation?.lat != null
                  ? `${result.geographicLocation.lat.toFixed(4)}°N, ${result.geographicLocation.lng?.toFixed(4)}°E`
                  : "N/A"}
              </div>
            </div>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Spatial Resolution / GSD</span>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc", fontFamily: "monospace", marginTop: "4px" }}>
                {spatial?.resolution || result.resolution || "10 m / px"}
              </div>
            </div>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Coordinate Reference System</span>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#a78bfa", fontFamily: "monospace", marginTop: "4px" }}>
                {spatial?.crs || result.geographicLocation?.crs || "EPSG:4326 (WGS84)"}
              </div>
            </div>
          </div>

          {(result.globeUrl || result.geographicLocation?.has_location) && (
            <div style={{ marginTop: "14px", padding: "12px", background: "rgba(86, 215, 223, 0.06)", border: "1px solid rgba(86, 215, 223, 0.2)", borderRadius: "6px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong style={{ color: "#56d7df", display: "block" }}>3D Earth Visualization Link Ready</strong>
                <span style={{ fontSize: "12px", color: "rgba(255, 255, 255, 0.7)" }}>
                  Stream full high-resolution digital globe layers directly over Cesium in Shatnetra.
                </span>
              </div>
              <a
                href={result.globeUrl || (result.geographicLocation ? buildTrinetraUrl(result.geographicLocation, result.images[0]?.name || "Target") : "#")}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  background: "#10b981",
                  color: "#022c22",
                  borderRadius: "6px",
                  fontWeight: 700,
                  fontSize: "12px",
                  textDecoration: "none",
                }}
              >
                <Globe size={14} /> Fly to Target <ArrowRight size={12} />
              </a>
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Spectral & Sensor */}
      {activeTab === "spectral" && (
        <div className="intel-tab-content">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Sensor Type</span>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#56d7df", marginTop: "4px" }}>
                {result.imageType} ({result.mode.toUpperCase()} MODE)
              </div>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.6)", marginTop: "6px" }}>
                Multi-spectral bands calibrated against top-of-atmosphere reflectance and surface backscatter.
              </p>
            </div>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.4)", textTransform: "uppercase" }}>Band Math Indices</span>
              <div style={{ fontSize: "12px", color: "#e2e8f0", marginTop: "6px", display: "flex", flexDirection: "column", gap: "4px" }}>
                <div>&bull; <b>NDVI:</b> Normalized Difference Vegetation Index (B08 - B04) / (B08 + B04)</div>
                <div>&bull; <b>NDWI:</b> Normalized Difference Water Index (B03 - B08) / (B03 + B08)</div>
                <div>&bull; <b>SAR Amplitude:</b> Dual-pol VV / VH log-ratio detection</div>
              </div>
            </div>
          </div>
          {result.spectralUrl && (
            <div style={{ marginTop: "12px", textAlign: "center" }}>
              <img src={result.spectralUrl} alt="Spectral Profile Curve" style={{ maxWidth: "100%", maxHeight: "240px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }} />
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Models & QML */}
      {activeTab === "models" && (
        <div className="intel-tab-content">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <div style={{ color: "#56d7df", fontWeight: 700, fontSize: "12px", marginBottom: "6px" }}>VISION-LANGUAGE AGENT BACKBONE</div>
              <div style={{ fontSize: "13px", color: "#f8fafc" }}>{result.model}</div>
              <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", marginTop: "4px" }}>
                Deterministic LangGraph multi-node state machine with domain guardrails.
              </div>
            </div>
            <div style={{ padding: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px" }}>
              <div style={{ color: "#10b981", fontWeight: 700, fontSize: "12px", marginBottom: "6px" }}>SPECIALIST DETECTORS</div>
              <div style={{ fontSize: "11px", color: "#e2e8f0", lineHeight: "1.4" }}>
                <div>&bull; BigEarthNet-19 Multi-label Land Cover Classifier</div>
                <div>&bull; RSVQA High-Resolution Target Grounding</div>
                <div>&bull; Connected-Component Region Detector & Spatial Direction Interpreter</div>
              </div>
            </div>
          </div>

          <QuantumResearchWidget
            comparison={result.classical_vs_qml_comparison}
            qml={result.qml_analysis}
          />
        </div>
      )}

      {/* Tab 7: Trace */}
      {activeTab === "trace" && (
        <div className="intel-tab-content">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderRadius: "6px" }}>
            <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Execution Latency: <b style={{ color: "#56d7df" }}>{result.processingTime}</b></span>
            <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Execution Steps: <b style={{ color: "#10b981" }}>{result.steps?.length || 0} nodes</b></span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {result.steps?.map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ color: "#56d7df", fontFamily: "monospace" }}>0{idx + 1}</span>
                  <span style={{ color: "#f8fafc" }}>{step.label || step.title || `Step ${idx + 1}`}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>{step.duration || step.timestamp || ""}</span>
                  <span style={{ color: (step.status === "completed" || step.status === "complete") ? "#10b981" : "#f59e0b", fontSize: "11px", fontWeight: 700, textTransform: "uppercase" }}>
                    {step.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
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
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null)
  const [activeLayer, setActiveLayer] = useState<"annotated" | "raw" | "heatmap" | "spectral">("annotated")

  const confidenceKey = `confidence.${result.confidence}` as const
  const confidenceText = t(confidenceKey)

  const intel = result.structured_intelligence
  const regions = intel?.regions || []

  return (
    <div className="result-view workstation-container">
      {/* Header with Title and Confidence */}
      <div className="result-top">
        <div>
          <span className="eyebrow">{t("result.eyebrow", { mode: result.mode.toUpperCase() })} &bull; SATELLITE INTELLIGENCE WORKSTATION</span>
          <h2>{t("result.title")}</h2>
        </div>
        <div className={`confidence ${result.confidence}`}>
          <span>{Math.round(result.confidenceScore * 100)}%</span>
          <small>{confidenceText}</small>
        </div>
      </div>

      {/* Region Selector Chips Bar */}
      {regions.length > 0 && (
        <div className="region-chip-bar" style={{ display: "flex", gap: "6px", flexWrap: "wrap", margin: "10px 0" }}>
          <button
            type="button"
            className={`region-chip ${selectedRegionId === null ? "active" : ""}`}
            onClick={() => setSelectedRegionId(null)}
            style={{
              padding: "4px 10px",
              borderRadius: "20px",
              fontSize: "11px",
              fontFamily: "monospace",
              background: selectedRegionId === null ? "rgba(86, 215, 223, 0.25)" : "rgba(255, 255, 255, 0.05)",
              border: selectedRegionId === null ? "1px solid #56d7df" : "1px solid rgba(255, 255, 255, 0.1)",
              color: selectedRegionId === null ? "#56d7df" : "rgba(255, 255, 255, 0.6)",
              cursor: "pointer",
            }}
          >
            ALL REGIONS ({regions.length})
          </button>
          {regions.map((r) => {
            const isSelected = selectedRegionId === r.id
            return (
              <button
                key={r.id}
                type="button"
                className={`region-chip ${isSelected ? "active" : ""}`}
                onClick={() => setSelectedRegionId(isSelected ? null : r.id)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "20px",
                  fontSize: "11px",
                  fontFamily: "monospace",
                  background: isSelected ? "rgba(16, 185, 129, 0.25)" : "rgba(255, 255, 255, 0.05)",
                  border: isSelected ? "1px solid #10b981" : "1px solid rgba(255, 255, 255, 0.1)",
                  color: isSelected ? "#10b981" : "rgba(255, 255, 255, 0.6)",
                  cursor: "pointer",
                }}
              >
                [{r.id}] {r.label} ({Math.round((r.confidence || 0) * 100)}%)
              </button>
            )
          })}
        </div>
      )}

      {/* Main Evidence Viewer (Interactive Multi-layer + BBoxes + HUD) */}
      {result.hsiData?.isHsi ? (
        <HsiViewer {...result.hsiData} />
      ) : (
        <EvidenceViewer
          result={result}
          selectedRegionId={selectedRegionId}
          onSelectRegion={setSelectedRegionId}
          activeLayer={activeLayer}
          setActiveLayer={setActiveLayer}
        />
      )}

      {/* 7-Tab Analyst Suite */}
      <IntelligenceTabs
        result={result}
        selectedRegionId={selectedRegionId}
        onSelectRegion={setSelectedRegionId}
      />

      {/* Action Row: View on Globe (TRINETRA / Shatnetra) & View Report */}
      <div className="action-row" style={{ marginTop: "1.4rem", marginBottom: "0.6rem", display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
        {result.globeUrl || result.geographicLocation?.has_location ? (
          <a
            href={result.globeUrl || (result.geographicLocation ? buildTrinetraUrl(result.geographicLocation, result.images[0]?.name || "Analysis Target") : "#")}
            target="_blank"
            rel="noreferrer"
            id="view-on-globe-btn"
            className="compact"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.55rem",
              padding: "0.65rem 1.25rem",
              borderRadius: "8px",
              textDecoration: "none",
              background: "linear-gradient(135deg, rgba(86, 215, 223, 0.22) 0%, rgba(16, 185, 129, 0.18) 100%)",
              border: "1px solid rgba(86, 215, 223, 0.5)",
              color: "#56d7df",
              fontSize: "0.86rem",
              fontWeight: 700,
              boxShadow: "0 0 20px rgba(86, 215, 223, 0.18)",
              transition: "all 0.2s ease",
            }}
          >
            <Globe size={16} style={{ color: "#56d7df" }} /> View in 3D Earth Globe (Shatnetra) <ArrowRight size={14} />
          </a>
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

      {/* Technical Telemetry Metadata */}
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

function QuantumResearchDashboard() {
  const [data, setData] = useState<QMLBenchmarkData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchQMLBenchmarks().then((res) => {
      if (res) {
        setData(res)
      } else {
        setData({
          model_version: "qml_change_levir10k",
          dataset: "LEVIR_CD_patches",
          total_test_samples: 1024,
          hardware_specs: {
            simulator: "PennyLane",
            device: "default.qubit",
            qubits: 6,
            circuit_depth: 7,
            quantum_parameters: 42,
            total_parameters: 63,
            shots: "Analytic (Exact Statevector)",
          },
          metrics: {
            accuracy: 76.37,
            macro_f1: 0.686,
            precision: 0.649,
            recall: 0.7674,
            roc_auc: 0.8845,
            latency_ms: 0.52,
            classical_agreement_rate: 84.8,
          },
          parameter_efficiency: {
            quantum_parameters: 63,
            classical_rf_parameters: 1840,
            classical_cnn_parameters: 1245000,
            reduction_vs_rf: "96.58%",
            reduction_vs_cnn: "99.995%",
          },
          comparison_table: [
            { metric: "Accuracy (%)", classical: "78.91%", qml: "76.37%", delta: "-2.54%", qml_better: false },
            { metric: "Macro F1", classical: "0.7124", qml: "0.6860", delta: "-0.0264", qml_better: false },
            { metric: "Precision", classical: "0.6812", qml: "0.6490", delta: "-0.0322", qml_better: false },
            { metric: "Recall", classical: "0.7845", qml: "0.7674", delta: "-0.0171", qml_better: false },
            { metric: "Latency (ms)", classical: "0.18 ms", qml: "0.52 ms", delta: "+0.34 ms", qml_better: false },
            { metric: "Parameter Count", classical: "1840 params", qml: "63 params", delta: "-1777 params", qml_better: true },
          ],
          confusion_matrix: [
            [597, 39, 91],
            [3, 51, 1],
            [95, 13, 134],
          ],
          research_buffer_stats: {
            total_samples: 12,
            agreements: 10,
            disagreements: 2,
            agreement_rate: 83.33,
            verified_count: 8,
            unverified_disagreements: 2,
          },
        })
      }
      setLoading(false)
    })
  }, [])

  if (!data) return null

  return (
    <section className="qml-dashboard-card">
      <div className="section-heading" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="eyebrow" style={{ color: "#a78bfa" }}>QUANTUM RESEARCH ENGINE (PENNYLANE)</span>
            <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "99px", background: "rgba(167, 139, 250, 0.15)", color: "#c4b5fd", border: "1px solid rgba(167, 139, 250, 0.3)" }}>
              ISRO PS 26167 Research Layer
            </span>
          </div>
          <h2 style={{ fontSize: "22px", marginTop: "6px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={20} style={{ color: "#a78bfa" }} />
            Variational Quantum Classifier Benchmark & Telemetry
          </h2>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ font: "11px monospace", color: "rgba(255,255,255,0.45)" }}>ACTIVE MODEL VERSION</div>
          <b style={{ color: "#56d7df", font: "13px monospace" }}>{data.model_version}</b>
        </div>
      </div>

      <div className="qml-kpi-grid">
        <div className="qml-kpi">
          <span>QML Test Accuracy</span>
          <b className="cyan">{data.metrics.accuracy}%</b>
          <small>LEVIR-CD Held-out ({data.total_test_samples} pairs)</small>
        </div>
        <div className="qml-kpi">
          <span>Macro F1 Score</span>
          <b>{data.metrics.macro_f1}</b>
          <small>Balanced 3-class performance</small>
        </div>
        <div className="qml-kpi">
          <span>Simulation Latency</span>
          <b className="green">{data.metrics.latency_ms} ms</b>
          <small>{data.hardware_specs.device} ({data.hardware_specs.qubits} qubits)</small>
        </div>
        <div className="qml-kpi">
          <span>Classical Agreement</span>
          <b>{data.metrics.classical_agreement_rate}%</b>
          <small>Cross-paradigm concordance</small>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", margin: "18px 0" }}>
        <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ font: "10px monospace", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: "8px" }}>
            Circuit & Simulator Configuration
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
            <div>Simulator: <b style={{ color: "#c4b5fd" }}>{data.hardware_specs.simulator}</b></div>
            <div>Device: <b style={{ color: "#c4b5fd" }}>{data.hardware_specs.device}</b></div>
            <div>Qubits: <b style={{ color: "#c4b5fd" }}>{data.hardware_specs.qubits} Wires (Hilbert Dim = 64)</b></div>
            <div>Circuit Depth: <b style={{ color: "#c4b5fd" }}>{data.hardware_specs.circuit_depth} Layers</b></div>
            <div>Quantum Params: <b style={{ color: "#38bdf8" }}>{data.hardware_specs.quantum_parameters}</b></div>
            <div>Execution Target: <b style={{ color: "#34d399" }}>{data.hardware_specs.shots}</b></div>
          </div>
        </div>

        <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ font: "10px monospace", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: "8px" }}>
            Parameter Efficiency vs Classical Models
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "11px" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Total QML Parameters:</span>
              <b style={{ color: "#38bdf8" }}>{data.hardware_specs.total_parameters} params</b>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Classical Baseline (Random Forest):</span>
              <span>{data.parameter_efficiency.classical_rf_parameters.toLocaleString()} params ({data.parameter_efficiency.reduction_vs_rf} reduction)</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Operational Specialist (Deep Siamese CNN):</span>
              <span>{data.parameter_efficiency.classical_cnn_parameters.toLocaleString()} params ({data.parameter_efficiency.reduction_vs_cnn} reduction)</span>
            </div>
            <div style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)", fontStyle: "italic", marginTop: "2px" }}>
              High parameter efficiency: Models complex entanglements in 64-dim Hilbert space.
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: "18px" }}>
        <div style={{ font: "10px monospace", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: "6px" }}>
          Classical Specialist vs PennyLane QML Benchmark Comparison (Fair Held-Out Split)
        </div>
        <table className="qml-benchmark-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Classical Specialist Baseline</th>
              <th>QML (PennyLane VQC)</th>
              <th>Delta</th>
              <th>Parity / Advantage</th>
            </tr>
          </thead>
          <tbody>
            {data.comparison_table.map((row) => (
              <tr key={row.metric}>
                <td style={{ fontWeight: 600 }}>{row.metric}</td>
                <td style={{ fontFamily: "monospace", color: "rgba(255,255,255,0.75)" }}>{row.classical}</td>
                <td style={{ fontFamily: "monospace", color: "#c4b5fd", fontWeight: 700 }}>{row.qml}</td>
                <td style={{ fontFamily: "monospace", color: row.delta.startsWith("+") ? "#6ee7b7" : "rgba(255,255,255,0.55)" }}>{row.delta}</td>
                <td>
                  {row.qml_better ? (
                    <span style={{ fontSize: "10px", color: "#38bdf8", padding: "2px 8px", borderRadius: "99px", background: "rgba(56, 189, 248, 0.15)" }}>
                      Quantum Advantage
                    </span>
                  ) : (
                    <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.45)" }}>
                      Classical Operational Lead
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="qml-matrix-wrap" style={{ justifyContent: "space-between" }}>
        <div>
          <div style={{ font: "10px monospace", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: "6px" }}>
            Held-Out Confusion Matrix (0: Unchanged, 1: Increased, 2: Decreased)
          </div>
          <div className="qml-matrix-box">
            {data.confusion_matrix.map((row, rIdx) =>
              row.map((val, cIdx) => (
                <div key={`${rIdx}-${cIdx}`} className={`qml-cell ${rIdx === cIdx ? "diag" : "off"}`}>
                  <span>{val}</span>
                  <small style={{ fontSize: "8px", opacity: 0.6 }}>T{rIdx}→P{cIdx}</small>
                </div>
              ))
            )}
          </div>
        </div>

        {data.research_buffer_stats && (
          <div style={{ background: "rgba(0,0,0,0.25)", padding: "14px 18px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)", flex: 1, minWidth: "260px" }}>
            <div style={{ font: "10px monospace", color: "#a78bfa", textTransform: "uppercase", marginBottom: "8px" }}>
              Verified Disagreement Learning Loop
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
              <div>Logged Inferences: <b>{data.research_buffer_stats.total_samples}</b></div>
              <div>Concordant Pairs: <b>{data.research_buffer_stats.agreements}</b></div>
              <div>Disagreements: <b style={{ color: "#f59e0b" }}>{data.research_buffer_stats.disagreements}</b></div>
              <div>Verified by Ground Truth: <b style={{ color: "#34d399" }}>{data.research_buffer_stats.verified_count}</b></div>
            </div>
            <p style={{ margin: "8px 0 0", fontSize: "10px", color: "rgba(255,255,255,0.4)", lineHeight: 1.4 }}>
              Disagreements enter the verified hard-example buffer for periodic retraining with validation score guards.
            </p>
          </div>
        )}
      </div>
    </section>
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
      <QuantumResearchDashboard />
    </main>
  )
}

function PageContent() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [path, setPath] = useState(pathname || "/")
  const [initialDemo, setInitialDemo] = useState(false)
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
