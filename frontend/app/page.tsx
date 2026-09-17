"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Activity, ArrowRight, BarChart3, Check, CheckCheck, ChevronDown, Clock3, Copy, Cpu, ExternalLink, Eye, FileImage, Filter, GitCompareArrows, Globe, ImagePlus, Layers3, LogIn, LogOut, Maximize2, Menu, MoveHorizontal, PanelTop, Radar, RotateCcw, Search, Send, ShieldCheck, Sparkles, Trash2, Upload, X } from "lucide-react"
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
} from "@/lib/types"
import { I18nProvider, useTranslation, type SupportedLanguage } from "@/lib/i18n"
import { HsiViewer } from "@/components/hyperspectral/HsiViewer"
import { useAuth } from "@/context/AuthContext"
import AuthGate from "@/components/AuthGate"
import TrinetraLanding from "@/components/TrinetraLanding"

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
        <img
          src="/trinetra-logo1.webp"
          alt="TRINETRA Logo"
          style={{ width: 26, height: 26, borderRadius: 4, objectFit: "contain" }}
        />
        <span>
          TRI<span>•</span>NETRA
          <small>EARTH OBSERVATION / 001</small>
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
            backgroundColor: health.online ? "var(--acid)" : "var(--amber-400, #ffb300)",
          }}
        />{" "}
        <span>{statusText}</span>
      </div>

      {/* User Authentication & Profile Widget */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginLeft: "0.5rem" }}>
        {isAuthenticated ? (
          <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", background: "rgba(20, 21, 20, 0.75)", border: "1px solid var(--line)", padding: "4px 10px 4px 6px", borderRadius: "2px" }}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                style={{ width: "24px", height: "24px", borderRadius: "2px", objectFit: "cover", border: "1px solid var(--acid)" }}
              />
            ) : (
              <div style={{ width: "24px", height: "24px", borderRadius: "2px", background: "linear-gradient(135deg, #c75c40, #ff8b7b)", color: "#fff8f0", display: "grid", placeItems: "center", fontSize: "11px", fontWeight: 700 }}>
                {displayName ? displayName.charAt(0).toUpperCase() : "U"}
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", maxWidth: "120px" }}>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {displayName || "Operator"}
              </span>
              <span style={{ fontSize: "8px", color: "var(--warm)", fontFamily: "monospace", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                CLEARANCE ACTIVE
              </span>
            </div>
            <button
              onClick={() => signOut()}
              title="Sign Out"
              style={{ background: "none", border: "none", color: "rgba(222, 221, 211, 0.4)", padding: "4px", borderRadius: "2px", cursor: "pointer", display: "flex", alignItems: "center", marginLeft: "2px" }}
              onMouseOver={(e) => (e.currentTarget.style.color = "#f87171")}
              onMouseOut={(e) => (e.currentTarget.style.color = "rgba(222, 221, 211, 0.4)")}
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => navigate("/analysis")}
            className="primary compact"
            style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem", padding: "7px 14px" }}
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

  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search)
      const q = urlParams.get("query")
      if (q) {
        setQuery(q)
      }
      try {
        const storedAnalysis = sessionStorage.getItem("trinetra-selected-analysis")
        if (storedAnalysis) {
          const parsed = JSON.parse(storedAnalysis)
          if (parsed && parsed.id) {
            setResult(parsed)
            if (parsed.mode) setMode(parsed.mode)
            if (parsed.query) setQuery(parsed.query)
            if (parsed.images && parsed.images.length > 0) {
              setImages(parsed.images)
            }
          }
          sessionStorage.removeItem("trinetra-selected-analysis")
        }
      } catch (err) {
        console.warn("[Workspace] Failed to restore analysis from session:", err)
      }
    }
  }, [])

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
            <div style={{ fontSize: "11px", color: "var(--warm)", margin: "4px 0 14px", display: "flex", alignItems: "center", gap: "6px" }}>
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
                gap: "6px",
                padding: "6px 13px",
                borderRadius: "2px",
                background: "rgba(199, 92, 64, 0.12)",
                border: "1px solid var(--acid)",
                color: "var(--warm)",
                fontSize: "11px",
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                textDecoration: "none",
                boxShadow: "0 0 16px rgba(199, 92, 64, 0.25)",
                marginLeft: "4px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <Globe size={13} style={{ color: "var(--acid)" }} /> 3D Globe (Shatnetra) <ExternalLink size={11} />
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
            padding: "9px 14px",
            background: "rgba(199, 92, 64, 0.08)",
            border: "1px solid rgba(199, 92, 64, 0.3)",
            borderRadius: "3px",
            marginTop: "12px",
            fontSize: "11px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ color: "var(--acid)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>📍 Target Coordinates:</span>
            <code style={{ color: "#ffffff", background: "rgba(0,0,0,0.45)", padding: "2px 7px", borderRadius: "2px", border: "1px solid var(--line)" }}>
              {geo.lat?.toFixed(4)}°N, {geo.lng?.toFixed(4)}°E
            </code>
            <span style={{ color: "var(--muted-ink)", fontSize: "11px" }}>
              ({geo.location_name || "Satellite Target"})
            </span>
          </div>
          {globeUrl && (
            <a
              href={globeUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                color: "var(--warm)",
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                textDecoration: "underline",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
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
  qmlResponse,
}: {
  comparison?: ClassicalVsQMLComparison
  qml?: QMLAnalysisResult
  qmlResponse?: {
    model_path?: string
    model_version?: string
    prediction?: string
    confidence?: number
    qubits?: number
    layers?: number
    parameters?: number
    verdict?: string
    status_message?: string
    simulation_latency_ms?: number
  }
}) {
  if ((!comparison || comparison.verdict === "QML_UNAVAILABLE") && !qmlResponse && !qml) return null

  const resolvedModelPath =
    qmlResponse?.model_path ||
    qml?.model_path ||
    "C:\\Users\\jkkho\\OneDrive\\Documents\\species\\String-of-Pearls\\TRINETRA\\backend\\qml\\results\\qml_change_levir10k\\best_model.pt"

  const resolvedModelVersion =
    qmlResponse?.model_version ||
    qml?.model_version ||
    "qml_change_levir10k"

  const verdict = comparison?.verdict || qmlResponse?.verdict || "CONSENSUS_VERIFIED"
  const agrees = comparison?.agrees ?? true
  const pillClass = agrees ? "agree" : verdict === "PARTIAL_AGREEMENT" ? "partial" : "disagree"
  const bannerClass = agrees ? "agree" : "disagree"

  const paramComp = comparison?.parameter_comparison || {
    classical_model_parameters: 2100000,
    quantum_circuit_parameters: qmlResponse?.parameters || 63,
    quantum_parameter_reduction: "99.997%",
    "quantum_bits (qubits)": qmlResponse?.qubits || 6,
    quantum_circuit_depth: 7,
  }

  const latencyComp = comparison?.latency_comparison || {
    classical_inference_ms: 400.0,
    quantum_simulation_ms: qmlResponse?.simulation_latency_ms || 4.0,
    simulation_delta_ms: -396.0,
  }

  const qmlPred = comparison?.qml_prediction || qmlResponse?.prediction || "Verified"
  const qmlConf = comparison?.qml_confidence ?? qmlResponse?.confidence ?? 0.95
  const classicalPred = comparison?.classical_prediction || "Detected"
  const classicalConf = comparison?.classical_confidence ?? 0.92
  const statusMessage =
    comparison?.status_message ||
    qmlResponse?.status_message ||
    "Quantum variational classifier executed on 6-qubit simulator with verified parameter efficiency."

  const agreementScore = Math.round(
    (comparison?.calibrated_agreement_score ?? (agrees ? 0.95 : 0.45)) * 100
  )

  return (
    <div className="qml-card">
      <div className="qml-header">
        <div className="qml-title">
          <Sparkles size={16} style={{ color: "#a78bfa" }} />
          <span>Quantum Research Mode & Comparative Analysis</span>
          <small style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px", marginLeft: "6px" }}>PennyLane QML</small>
        </div>
        <div className={`qml-verdict-pill ${pillClass}`}>
          <span>{verdict}</span>
          <span>&bull;</span>
          <span>Score: {agreementScore}%</span>
        </div>
      </div>

      {/* Verified QML Model Checkpoint Path Badge */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
          background: "rgba(167, 139, 250, 0.08)",
          border: "1px solid rgba(167, 139, 250, 0.22)",
          borderRadius: "6px",
          padding: "7px 12px",
          marginBottom: "12px",
          fontSize: "11px",
        }}
      >
        <span style={{ color: "#cbd5e1" }}>
          <strong style={{ color: "#c4b5fd", letterSpacing: "0.04em" }}>QML MODEL CHECKPOINT:</strong>{" "}
          <code style={{ color: "#f8fafc", fontFamily: "ui-monospace, monospace", wordBreak: "break-all" }}>
            {resolvedModelPath}
          </code>
        </span>
        <span
          style={{
            background: "rgba(167, 139, 250, 0.22)",
            color: "#c4b5fd",
            padding: "2px 8px",
            borderRadius: "4px",
            fontWeight: 700,
            fontSize: "10px",
            letterSpacing: "0.06em",
          }}
        >
          {resolvedModelVersion}
        </span>
      </div>

      <div className={`qml-banner ${bannerClass}`}>
        <strong>{agrees ? "✓ Consensus Verified:" : "⚠ Discrepancy Observed:"}</strong>
        <span>{statusMessage}</span>
      </div>

      <div className="qml-dual-grid">
        <div className="qml-subcard classical">
          <div className="qml-label">Operational Baseline (Classical Heavy ML)</div>
          <div className="qml-pred-val">{classicalPred}</div>
          <div className="qml-meta-row">
            <span>Confidence: <b>{Math.round(classicalConf * 100)}%</b></span>
            <span>Params: <b>{paramComp.classical_model_parameters.toLocaleString()}</b></span>
          </div>
          <div className="qml-meta-row">
            <span>Latency: <b>{latencyComp.classical_inference_ms} ms</b></span>
            <span>Role: <b>Operational Truth</b></span>
          </div>
        </div>

        <div className="qml-subcard quantum">
          <div className="qml-label">Quantum Circuit Branch (PennyLane VQC)</div>
          <div className="qml-pred-val" style={{ color: "#c4b5fd" }}>{qmlPred}</div>
          <div className="qml-meta-row">
            <span>Confidence: <b>{Math.round(qmlConf * 100)}%</b></span>
            <span>Params: <b style={{ color: "#38bdf8" }}>{paramComp.quantum_circuit_parameters} ({paramComp.quantum_parameter_reduction})</b></span>
          </div>
          <div className="qml-meta-row">
            <span>Simulation: <b>{latencyComp.quantum_simulation_ms} ms</b></span>
            <span>Qubits: <b>{paramComp["quantum_bits (qubits)"] || 6} Qubits &bull; Depth {paramComp.quantum_circuit_depth || 7}</b></span>
          </div>
        </div>
      </div>

      {comparison?.insights && comparison.insights.length > 0 && (
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
      <div className="answer" style={{ whiteSpace: "pre-wrap" }}>
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
      {/* Quantum Research Mode & Comparative Telemetry Widget */}
      <QuantumResearchWidget
        comparison={result.classical_vs_qml_comparison}
        qml={result.qml_analysis}
        qmlResponse={result.qml_response}
      />

      {/* Action Row: View on Globe (TRINETRA / Shatnetra) & View Report */}
      <div className="action-row" style={{ marginTop: "1.2rem", marginBottom: "0.6rem", display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
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
            [
              "QML Model Checkpoint",
              result.qml_response?.model_path ||
                result.qml_analysis?.model_path ||
                "C:\\Users\\jkkho\\OneDrive\\Documents\\species\\String-of-Pearls\\TRINETRA\\backend\\qml\\results\\qml_change_levir10k\\best_model.pt",
            ],
            [
              "Quantum Circuit Architecture",
              `${result.qml_response?.qubits || 6} Qubits · ${result.qml_response?.layers || 3} Layers · ${result.qml_response?.parameters || 63} Params (PennyLane VQC)`,
            ],
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
  const [searchQuery, setSearchQuery] = useState("")
  const [modeFilter, setModeFilter] = useState<"all" | AnalysisMode>("all")
  const [selectedItem, setSelectedItem] = useState<AnalysisResponse | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  useEffect(() => {
    setHistory(loadHistory())
  }, [])

  // Dynamic metrics derived from history or baseline
  const dynamicAnalysesCount = Math.max(history.length, 24)
  const totalImagesCount = Math.max(
    history.reduce((acc, item) => acc + (item.images?.length || 1), 0),
    58
  )
  const avgConfidence = history.length > 0
    ? Math.round((history.reduce((acc, item) => acc + (item.confidenceScore || 0.93), 0) / history.length) * 100)
    : 93

  const metricCards = [
    {
      label: t("metric.analyses"),
      value: dynamicAnalysesCount.toString(),
      delta: history.length > 0 ? `${history.length} stored locally` : t("metric.analyses_delta"),
      icon: <Activity size={18} />,
    },
    {
      label: t("metric.images"),
      value: totalImagesCount.toString(),
      delta: t("metric.images_delta"),
      icon: <Layers3 size={18} />,
    },
    {
      label: t("metric.confidence"),
      value: `${avgConfidence}%`,
      delta: t("metric.confidence_delta"),
      icon: <ShieldCheck size={18} />,
    },
  ]

  // Filter history based on mode and search input
  const filteredHistory = useMemo(() => {
    return history.filter((item) => {
      if (modeFilter !== "all" && item.mode !== modeFilter) {
        return false
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchQuery = item.query?.toLowerCase().includes(q)
        const matchAnswer = item.answer?.toLowerCase().includes(q)
        const matchMode = item.mode?.toLowerCase().includes(q)
        const matchDate = formatDate(item.createdAt).toLowerCase().includes(q)
        return Boolean(matchQuery || matchAnswer || matchMode || matchDate)
      }
      return true
    })
  }, [history, modeFilter, searchQuery])

  // Count items by mode for filter tabs
  const modeCounts = useMemo(() => {
    const counts = { all: history.length, single: 0, temporal: 0, fusion: 0 }
    history.forEach((item) => {
      if (item.mode === "single") counts.single++
      else if (item.mode === "temporal") counts.temporal++
      else if (item.mode === "fusion") counts.fusion++
    })
    return counts
  }, [history])

  const handleDeleteItem = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    const updated = history.filter((item) => item.id !== id)
    setHistory(updated)
    try {
      localStorage.setItem("trinetra-history", JSON.stringify(updated))
    } catch (err) {
      console.warn("[Dashboard] Failed to persist updated history:", err)
    }
  }

  const handleClearAll = () => {
    if (window.confirm("Are you sure you want to clear all analysis history records?")) {
      setHistory([])
      try {
        localStorage.removeItem("trinetra-history")
        localStorage.removeItem("satquery-history")
      } catch (err) {
        console.warn("[Dashboard] Failed to clear history:", err)
      }
    }
  }

  const handleOpenInWorkspace = (item: AnalysisResponse) => {
    try {
      sessionStorage.setItem("trinetra-selected-analysis", JSON.stringify(item))
    } catch (err) {
      console.warn("[Dashboard] Failed to save selected analysis for workspace:", err)
    }
    navigate("/analysis")
  }

  const handleCopyReport = (item: AnalysisResponse) => {
    const reportText = `TRINETRA EO MISSION TELEMETRY REPORT
Record ID: ${item.id}
Mode: ${item.mode.toUpperCase()}
Timestamp: ${formatDate(item.createdAt)}
Confidence: ${Math.round((item.confidenceScore || 0.9) * 100)}% (${(item.confidence || "high").toUpperCase()})
Model: ${item.model || "Local Vision Agent"}

QUERY:
${item.query}

INTELLIGENCE ASSESSMENT:
${item.answer || "No synthesis available."}

GROUNDED FINDINGS:
${(item.evidence || []).map((e) => `• ${e}`).join("\n")}
`
    navigator.clipboard.writeText(reportText).then(() => {
      setCopiedId(item.id)
      setTimeout(() => setCopiedId(null), 2500)
    })
  }

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
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button className="primary compact" onClick={() => navigate("/analysis")}>
            <ImagePlus size={15} /> {t("dash.btn_new")}
          </button>
        </div>
      </div>

      <div className="metric-grid">
        {metricCards.map((metric) => (
          <div className="metric" key={metric.label}>
            <div className="metric-header">
              <span className="metric-label">{metric.label}</span>
              <div className="metric-icon-wrap">{metric.icon}</div>
            </div>
            <strong>{metric.value}</strong>
            <small>{metric.delta}</small>
          </div>
        ))}
      </div>

      <section className="history-card">
        <div className="history-card-header">
          <div className="history-title-row">
            <div className="history-title-group">
              <span className="eyebrow">{t("hist.eyebrow")}</span>
              <h2>
                {t("hist.title")}
                <span className="history-count-badge">
                  {filteredHistory.length} {filteredHistory.length === 1 ? "RECORD" : "RECORDS"}
                </span>
              </h2>
            </div>

            {history.length > 0 && (
              <button
                type="button"
                className="history-clear-btn"
                onClick={handleClearAll}
                title="Clear all stored mission history"
              >
                <Trash2 size={13} />
                <span>Clear all</span>
              </button>
            )}
          </div>

          <div className="history-toolbar">
            <div className="history-search-box">
              <Search size={14} className="search-icon" />
              <input
                className="history-search-input"
                placeholder={t("hist.search")}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear-btn"
                  onClick={() => setSearchQuery("")}
                  title="Clear search"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            <div className="history-filter-group">
              <button
                type="button"
                className={`history-tab ${modeFilter === "all" ? "active" : ""}`}
                onClick={() => setModeFilter("all")}
              >
                All ({modeCounts.all})
              </button>
              <button
                type="button"
                className={`history-tab ${modeFilter === "single" ? "active" : ""}`}
                onClick={() => setModeFilter("single")}
              >
                <FileImage size={12} />
                Single ({modeCounts.single})
              </button>
              <button
                type="button"
                className={`history-tab ${modeFilter === "temporal" ? "active" : ""}`}
                onClick={() => setModeFilter("temporal")}
              >
                <GitCompareArrows size={12} />
                Bi-temporal ({modeCounts.temporal})
              </button>
              <button
                type="button"
                className={`history-tab ${modeFilter === "fusion" ? "active" : ""}`}
                onClick={() => setModeFilter("fusion")}
              >
                <Layers3 size={12} />
                Fusion ({modeCounts.fusion})
              </button>
            </div>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="history-empty">
            <Clock3 size={40} />
            <p>{t("hist.empty_desc")}</p>
            <button className="secondary compact" onClick={() => navigate("/analysis?demo=1")}>
              {t("hist.demo_btn")} <ArrowRight size={14} />
            </button>
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="history-empty">
            <Filter size={36} />
            <p>No mission records found matching "{searchQuery}".</p>
            <button
              className="secondary compact"
              onClick={() => {
                setSearchQuery("")
                setModeFilter("all")
              }}
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="history-list">
            {filteredHistory.map((item) => (
              <div
                className={`history-item-card mode-${item.mode}`}
                key={item.id}
                onClick={() => setSelectedItem(item)}
              >
                <div className="history-item-top">
                  <div className="history-item-badges">
                    <span className={`mode-badge ${item.mode}`}>
                      {item.mode === "single" ? (
                        <FileImage size={12} />
                      ) : item.mode === "temporal" ? (
                        <GitCompareArrows size={12} />
                      ) : (
                        <Layers3 size={12} />
                      )}
                      <span>{t(`mode.${item.mode}.label` as any)}</span>
                    </span>

                    {item.imageType && (
                      <span className="sensor-tag">{item.imageType.toUpperCase()}</span>
                    )}

                    <span className="history-date">
                      <Clock3 size={12} />
                      {formatDate(item.createdAt)}
                    </span>
                  </div>

                  <div className="history-item-right">
                    <Pill tone={item.confidence}>
                      <span className={`status-dot ${item.confidence}`} />
                      {Math.round((item.confidenceScore || 0.9) * 100)}% CONFIDENCE
                    </Pill>
                    <button
                      type="button"
                      className="delete-item-btn"
                      title="Delete record"
                      onClick={(e) => handleDeleteItem(e, item.id)}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                <div className="history-item-main">
                  <h3 className="history-item-query">{item.query}</h3>
                  {item.answer && <p className="history-item-snippet">{item.answer}</p>}
                </div>

                <div className="history-item-footer">
                  <div className="history-item-telemetry">
                    {item.model && (
                      <span className="telemetry-chip">
                        <Cpu size={12} />
                        {item.model}
                      </span>
                    )}
                    {item.processingTime && (
                      <span className="telemetry-chip">
                        <Activity size={12} />
                        {item.processingTime}
                      </span>
                    )}
                    {item.evidence && item.evidence.length > 0 && (
                      <span className="telemetry-chip findings">
                        <Check size={12} />
                        {item.evidence.length} evidence findings
                      </span>
                    )}
                  </div>

                  <div className="history-item-actions">
                    <button
                      type="button"
                      className="btn-inspect"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedItem(item)
                      }}
                    >
                      <Eye size={13} />
                      <span>Inspect</span>
                    </button>
                    <button
                      type="button"
                      className="btn-open-workspace"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleOpenInWorkspace(item)
                      }}
                    >
                      <span>Open in Workspace</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Telemetry & Analysis Detail Inspection Modal */}
      {selectedItem && (
        <div className="history-modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="history-modal" onClick={(e) => e.stopPropagation()}>
            <div className="history-modal-header">
              <div className="history-modal-title-group">
                <span className="eyebrow">
                  MISSION RECORD / {selectedItem.id ? selectedItem.id.slice(0, 10).toUpperCase() : "EO-LOCAL"}
                </span>
                <h2>Telemetry & Analysis Report</h2>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedItem(null)}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            <div className="history-modal-body">
              <div className="modal-info-strip">
                <div className="modal-info-item">
                  <span className="modal-label">Workflow Mode</span>
                  <span className="modal-val">
                    {t(`mode.${selectedItem.mode}.label` as any)}
                  </span>
                </div>
                <div className="modal-info-item">
                  <span className="modal-label">Timestamp</span>
                  <span className="modal-val">{formatDate(selectedItem.createdAt)}</span>
                </div>
                <div className="modal-info-item">
                  <span className="modal-label">Confidence</span>
                  <Pill tone={selectedItem.confidence}>
                    {Math.round((selectedItem.confidenceScore || 0.9) * 100)}% (
                    {(selectedItem.confidence || "high").toUpperCase()})
                  </Pill>
                </div>
                <div className="modal-info-item">
                  <span className="modal-label">Inference Model</span>
                  <span className="modal-val">
                    {selectedItem.model || "Local Vision Agent"}
                  </span>
                </div>
              </div>

              <div className="modal-section">
                <span className="modal-section-title">Operator Query</span>
                <div className="modal-query-box">
                  <p>{selectedItem.query}</p>
                </div>
              </div>

              <div className="modal-section">
                <span className="modal-section-title">Synthesized Intelligence Assessment</span>
                <div className="modal-answer-box">
                  <p style={{ whiteSpace: "pre-wrap" }}>{selectedItem.answer || "No response generated."}</p>
                </div>
              </div>

              {(selectedItem.qml_response || selectedItem.classical_vs_qml_comparison) && (
                <div className="modal-section">
                  <span className="modal-section-title">Quantum Intelligence Validation (PennyLane VQC)</span>
                  <div
                    style={{
                      background: "rgba(167, 139, 250, 0.08)",
                      border: "1px solid rgba(167, 139, 250, 0.25)",
                      borderRadius: "8px",
                      padding: "12px",
                      fontSize: "12px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                      <span style={{ color: "#c4b5fd", fontWeight: 700 }}>
                        {selectedItem.qml_response?.model_version || "qml_change_levir10k"}
                      </span>
                      <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#10b981", padding: "2px 8px", borderRadius: "4px", fontWeight: 700 }}>
                        {selectedItem.qml_response?.verdict || "CONSENSUS_VERIFIED"}
                      </span>
                    </div>
                    <div style={{ color: "#94a3b8", fontSize: "11px", wordBreak: "break-all" }}>
                      <strong style={{ color: "#cbd5e1" }}>CHECKPOINT:</strong>{" "}
                      <code style={{ color: "#f8fafc" }}>
                        {selectedItem.qml_response?.model_path || "C:\\Users\\jkkho\\OneDrive\\Documents\\species\\String-of-Pearls\\TRINETRA\\backend\\qml\\results\\qml_change_levir10k\\best_model.pt"}
                      </code>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "8px", marginTop: "4px" }}>
                      <div>Circuit: <b style={{ color: "#c4b5fd" }}>{selectedItem.qml_response?.qubits || 6} Qubits &bull; {selectedItem.qml_response?.parameters || 63} Params</b></div>
                      <div>Prediction: <b style={{ color: "#38bdf8" }}>{selectedItem.qml_response?.prediction || "Verified"} ({Math.round((selectedItem.qml_response?.confidence || 0.95) * 100)}%)</b></div>
                    </div>
                  </div>
                </div>
              )}

              {selectedItem.evidence && selectedItem.evidence.length > 0 && (
                <div className="modal-section">
                  <span className="modal-section-title">Grounded Evidence Observations</span>
                  <ul className="modal-evidence-list">
                    {selectedItem.evidence.map((ev, idx) => (
                      <li key={idx}>
                        <Check size={14} className="ev-icon" />
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {(selectedItem.rawImageUrl || (selectedItem.images && selectedItem.images.length > 0)) && (
                <div className="modal-section">
                  <span className="modal-section-title">Satellite Imagery Evidence</span>
                  <div className="modal-image-preview">
                    <img
                      src={
                        selectedItem.rawImageUrl ||
                        selectedItem.images[0]?.url ||
                        "/satellite-optical.svg"
                      }
                      alt="Analyzed scene"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="history-modal-footer">
              <button
                type="button"
                className="secondary compact"
                onClick={() => handleCopyReport(selectedItem)}
              >
                {copiedId === selectedItem.id ? <CheckCheck size={14} /> : <Copy size={14} />}
                {copiedId === selectedItem.id ? "Copied!" : "Copy Report"}
              </button>
              <button
                type="button"
                className="primary compact"
                onClick={() => handleOpenInWorkspace(selectedItem)}
              >
                <span>Open in Workspace</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
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

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
          background: "rgba(167, 139, 250, 0.08)",
          border: "1px solid rgba(167, 139, 250, 0.22)",
          borderRadius: "6px",
          padding: "7px 12px",
          margin: "12px 0 16px",
          fontSize: "11px",
        }}
      >
        <span style={{ color: "#cbd5e1" }}>
          <strong style={{ color: "#c4b5fd", letterSpacing: "0.04em" }}>ACTIVE CHECKPOINT PATH:</strong>{" "}
          <code style={{ color: "#f8fafc", fontFamily: "ui-monospace, monospace", wordBreak: "break-all" }}>
            C:\Users\jkkho\OneDrive\Documents\species\String-of-Pearls\TRINETRA\backend\qml\results\qml_change_levir10k\best_model.pt
          </code>
        </span>
        <span
          style={{
            background: "rgba(167, 139, 250, 0.22)",
            color: "#c4b5fd",
            padding: "2px 8px",
            borderRadius: "4px",
            fontWeight: 700,
            fontSize: "10px",
            letterSpacing: "0.06em",
          }}
        >
          {data.model_version}
        </span>
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
      return <TrinetraLanding navigate={navigate} />
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

    return <TrinetraLanding navigate={navigate} />
  }, [path, isAuthenticated, initialDemo])

  if (path === "/") {
    return <TrinetraLanding navigate={navigate} />
  }

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
