"use client"
import { useEffect, useMemo, useRef, useState } from "react"
import { Activity, AlertTriangle, ArrowRight, BarChart3, Check, ChevronDown, Clock3, Cpu, Database, FileImage, GitCompareArrows, Globe, ImagePlus, Layers, Layers3, LogIn, LogOut, Menu, PanelTop, Radar, RefreshCw, Search, Send, ShieldCheck, Sparkles, Upload, User as UserIcon, X } from "lucide-react"
import { analysisAPI, buildTrinetraUrl, checkBackendHealth, confidenceCopy, examples, formatBytes, formatDate, getDynamicMetrics, isReady, loadHistory, modeRequirements, modeSlots, modes, navItems, normalizeFile, saveHistory, type AnalysisMode, type AnalysisResponse, type BackendHealth, type ImageInput, type PresetSample } from "@/lib/types"
import { useAuth } from "@/context/AuthContext"
import AuthGate from "@/components/AuthGate"

const Icon = ({ mode }: { mode: AnalysisMode }) => mode === "single" ? <FileImage /> : mode === "temporal" ? <GitCompareArrows /> : <Layers3 />

function Header({ path, navigate }: { path: string; navigate: (path: string) => void }) {
  const { isAuthenticated, displayName, avatarUrl, signOut } = useAuth();
  const [health, setHealth] = useState<{ online: boolean; text: string }>({ online: false, text: "CONNECTING..." });

  useEffect(() => {
    checkBackendHealth().then((h) => {
      if (h && h.status === "healthy") {
        const engine = h.llm_status?.active_engine ? ` • ${h.llm_status.active_engine.toUpperCase()}` : h.llm_status?.model ? ` • ${h.llm_status.model.toUpperCase()}` : "";
        setHealth({ online: true, text: `FASTAPI ONLINE${engine}` });
      } else {
        setHealth({ online: false, text: "BACKEND OFFLINE" });
      }
    }).catch(() => {
      setHealth({ online: false, text: "BACKEND DISCONNECTED" });
    });
  }, []);

  return (
    <header className="topbar">
      <button className="brand" onClick={() => navigate("/")}>
        <span className="brandmark"><Radar /></span>
        <span>SatQuery <b>AI</b><small>EARTH OBSERVATION / 26167</small></span>
      </button>

      <nav>
        {navItems.map((item) => (
          <button key={item.href} className={path === item.href ? "active" : ""} onClick={() => navigate(item.href)}>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="header-status">
        <i style={{ backgroundColor: health.online ? "var(--cyan-400, #00f0ff)" : "var(--amber-400, #ffb300)" }} />
        <span>{health.text}</span>
      </div>

      {/* User Authentication & Profile Widget */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginLeft: "auto" }}>
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
                {displayName.charAt(0).toUpperCase()}
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", maxWidth: "120px" }}>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {displayName}
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

      <button className="mobile-menu" aria-label="Menu"><Menu /></button>
    </header>
  );
}

function Pill({ children, tone = "cyan" }: { children: React.ReactNode; tone?: string }) { return <span className={`pill ${tone}`}>{children}</span> }
function SatelliteBackdrop() { return <div className="backdrop"><div className="orb"/><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="scanline"/></div> }

function Landing({ navigate }: { navigate: (path: string) => void }) { 
  return <main className="landing"><SatelliteBackdrop/><div className="hero"><Pill><span className="pulse"/>AGENTIC VISION-LANGUAGE ANALYSIS</Pill><h1>Ask Earth.<br/><span>See evidence.</span></h1><p>SatQuery AI turns complex satellite imagery questions into grounded, inspectable answers — powered by multimodal remote-sensing neural networks and local LLM reasoning.</p><div className="hero-actions"><button className="primary" onClick={() => navigate("/analysis")}>Start Analysis <ArrowRight /></button><button className="secondary" onClick={() => navigate("/analysis?sample=1")}>Preloaded Mission Scenarios <Sparkles /></button></div><div className="hero-stats"><div><b>03</b><span>analysis modes</span></div><div><b>01</b><span>evidence layer</span></div><div><b>100%</b><span>live telemetry</span></div></div></div><div className="capabilities">{modes.map((mode) => <div className="cap-card" key={mode.id}><div className="cap-icon"><Icon mode={mode.id}/></div><div><span className="eyebrow">0{modes.indexOf(mode) + 1} / {mode.label}</span><h3>{mode.description}</h3><p>{mode.id === "single" ? "Ask about land use, vegetation, water, infrastructure, or conditions." : mode.id === "temporal" ? "Compare two dates to surface meaningful change and movement." : "Fuse visible context with radar signals for deeper evidence."}</p></div></div>)}</div></main> 
}

function UploadSlot({ slot, image, onFile, onRemove }: { slot: { label: string; hint: string }; image?: ImageInput; onFile: (file: File) => void; onRemove: () => void }) { 
  const ref = useRef<HTMLInputElement>(null); 
  const isTiff = Boolean(image?.name && (image.name.toLowerCase().endsWith(".tif") || image.name.toLowerCase().endsWith(".tiff")));
  return <div className={`upload-slot ${image ? "filled" : ""}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); const file = e.dataTransfer.files[0]; if (file) onFile(file) }} onClick={() => !image && ref.current?.click()}>{image ? <>{isTiff ? <div style={{ width: "100%", height: "100%", minHeight: "180px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "radial-gradient(circle at center, rgba(0,240,255,0.12), rgba(9,13,16,0.95))", color: "var(--cyan-400, #00f0ff)", gap: "0.6rem" }}><Layers size={36} /><span style={{ fontSize: "0.8rem", fontWeight: 700, letterSpacing: "0.08em", color: "#e2e8f0" }}>GEOTIFF RASTER READY</span><small style={{ color: "var(--cyan-400, #00f0ff)", fontSize: "0.72rem" }}>Multispectral / Scientific Bands</small></div> : <img src={image.url} alt="Uploaded satellite preview"/>}<div className="slot-overlay"><Pill tone="dark">{slot.hint}</Pill><strong>{image.name}</strong><span>{formatBytes(image.size)}</span></div><button className="remove" onClick={(e) => { e.stopPropagation(); onRemove() }} aria-label="Remove image"><X /></button></> : <><input ref={ref} type="file" accept="image/png,image/jpeg,image/tiff,.tif,.tiff" hidden onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}/><Upload/><strong>{slot.label}</strong><span>Drop image or click to browse</span><small>{slot.hint} · PNG, JPEG, GeoTIFF</small></>}</div> 
}

function Workspace({ navigate, initialSample = false }: { navigate: (path: string) => void; initialSample?: boolean }) { 
  const [mode, setMode] = useState<AnalysisMode>("single"); 
  const [images, setImages] = useState<ImageInput[]>([]); 
  const [query, setQuery] = useState(""); 
  const [result, setResult] = useState<AnalysisResponse>(); 
  const [running, setRunning] = useState(false); 
  const [technical, setTechnical] = useState(false); 
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [presetSamples, setPresetSamples] = useState<PresetSample[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");

  useEffect(() => {
    analysisAPI.fetchPresetSamples().then((data) => {
      setPresetSamples(data);
      if (initialSample && data.length > 0) {
        setSelectedPresetId(data[0].id);
        runPreset(data[0].id);
      }
    }).catch(() => {});
  }, [initialSample]);

  const slots = modeSlots(mode); 
  const ready = isReady(mode, images, query); 

  const setModeAndReset = (next: AnalysisMode) => { 
    setMode(next); 
    setImages([]); 
    setResult(undefined);
    setErrorMessage(null);
  }; 

  const addImage = (file: File, index: number) => {
    setErrorMessage(null);
    setImages((current) => { 
      const next = [...current]; 
      next[index] = normalizeFile(file, slots[index].label, mode === "fusion" ? (index === 0 ? "OPTICAL" : "SAR") : undefined); 
      return next;
    });
  };

  const run = async () => { 
    if (!ready) return; 
    setRunning(true); 
    setErrorMessage(null);
    setResult(undefined); 
    try {
      const response = await analysisAPI.submitAnalysis({ mode, images, query }); 
      setResult(response); 
      saveHistory(response); 
    } catch (err: any) {
      setErrorMessage(err.message || "Analysis request failed.");
    } finally {
      setRunning(false);
    }
  }; 

  const runPreset = async (presetId: string) => {
    if (!presetId) return;
    setRunning(true);
    setErrorMessage(null);
    setResult(undefined);
    try {
      const sample = presetSamples.find(s => s.id === presetId);
      if (sample) {
        setQuery(sample.query);
        const mappedMode: AnalysisMode = sample.mode === "bi_temporal" ? "temporal" : sample.mode === "optical_sar" ? "fusion" : "single";
        setMode(mappedMode);
      }
      const response = await analysisAPI.submitPreset(presetId);
      setResult(response);
      saveHistory(response);
      setMode(response.mode);
      setQuery(response.query);
    } catch (err: any) {
      setErrorMessage(err.message || "Preset mission execution failed.");
    } finally {
      setRunning(false);
    }
  };

  return <main className="workspace page"><div className="page-intro"><div><Pill><span className="pulse"/>WORKSPACE / LIVE</Pill><h1>Analysis workspace</h1><p>Choose a workflow, add real satellite imagery, and ask a question. The agent handles the rest.</p></div><button className="secondary compact" onClick={() => navigate("/dashboard")}><Clock3/> History</button></div>

  {errorMessage && <div className="error-banner" style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.4)", color: "#fca5a5", padding: "0.85rem 1.25rem", borderRadius: "8px", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.9rem" }}><AlertTriangle size={18} color="#ef4444" /><span>{errorMessage}</span><button onClick={() => setErrorMessage(null)} style={{ marginLeft: "auto", background: "none", border: "none", color: "#fca5a5", cursor: "pointer" }}><X size={16}/></button></div>}

  {presetSamples.length > 0 && <div className="preset-selector" style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", padding: "0.75rem 1rem", borderRadius: "10px", marginBottom: "1.5rem", display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.75rem" }}>
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "var(--cyan-400, #00f0ff)", fontWeight: 600 }}>
      <Database size={16} /> Preloaded GeoTIFF Datasets:
    </div>
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", flex: 1 }}>
      {presetSamples.map((ps) => (
        <button key={ps.id} disabled={running} onClick={() => { setSelectedPresetId(ps.id); runPreset(ps.id); }} style={{ background: selectedPresetId === ps.id ? "rgba(0, 240, 255, 0.2)" : "rgba(255, 255, 255, 0.05)", border: selectedPresetId === ps.id ? "1px solid var(--cyan-400, #00f0ff)" : "1px solid rgba(255, 255, 255, 0.1)", color: selectedPresetId === ps.id ? "var(--cyan-400, #00f0ff)" : "#e2e8f0", padding: "0.35rem 0.75rem", borderRadius: "6px", fontSize: "0.78rem", cursor: "pointer", transition: "all 0.15s" }}>
          {ps.title}
        </button>
      ))}
    </div>
  </div>}

  <div className="workspace-grid"><section className="input-panel"><div className="section-heading"><div><span className="eyebrow">01 / workflow</span><h2>What are you looking at?</h2></div><Pill tone="muted">{modeRequirements[mode]}</Pill></div><div className="mode-grid">{modes.map((item) => <button key={item.id} className={`mode-card ${mode === item.id ? "selected" : ""}`} onClick={() => setModeAndReset(item.id)}><Icon mode={item.id}/><strong>{item.label}</strong><span>{item.description}</span></button>)}</div><div className="section-heading upload-heading"><div><span className="eyebrow">02 / imagery</span><h2>Upload your evidence</h2></div><span className="accepted">PNG / JPEG / GeoTIFF · MAX 50MB</span></div><div className={`upload-grid ${mode === "single" ? "single" : ""}`}>{slots.map((slot, index) => <UploadSlot key={slot.label} slot={slot} image={images[index]} onFile={(file) => addImage(file, index)} onRemove={() => setImages((current) => current.filter((_, i) => i !== index))}/>)}</div><div className="supported"><ShieldCheck/> <span>Supports Landsat, Sentinel, MODIS, Planet, and custom GeoTIFF exports.</span></div><div className="section-heading query-heading"><div><span className="eyebrow">03 / intent</span><h2>What do you want to know?</h2></div><span className="accepted">{query.length}/240</span></div><textarea value={query} maxLength={240} onChange={(e) => { setQuery(e.target.value); setErrorMessage(null); }} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); run() } }} placeholder="Ask about land use, changes, infrastructure, damage, vegetation, water bodies..."/><div className="examples"><span>Try asking</span>{examples[mode].map((example) => <button key={example} onClick={() => { setQuery(example); setErrorMessage(null); }}>{example}</button>)}</div><button className="analyze primary" disabled={!ready || running} onClick={run}>{running ? <><Activity className="spin"/> Processing evidence...</> : <>Analyze <ArrowRight/></>}</button><p className="local-note"><Sparkles/> Connected to SatQuery Multi-Model Reasoning Engine + Local LLM</p></section><section className="result-panel">{running ? <ExecutionTrace/> : result ? <ResultView result={result} technical={technical} setTechnical={setTechnical}/> : <EmptyResult/>}</section></div></main> 
}

function EmptyResult() { return <div className="empty-result"><div className="empty-orbit"><Radar/></div><span className="eyebrow">READY FOR INPUT</span><h2>Your next answer<br/>will appear here.</h2><p>Upload imagery or select a preloaded mission scenario to begin an inspectable analysis.</p><div className="empty-lines"><span/><span/><span/></div></div> }

function ExecutionTrace() { return <div className="trace-card"><div className="trace-header"><div><span className="eyebrow">LIVE / OBSERVABLE</span><h2>Agent execution</h2></div><Activity className="spin cyan"/></div><div className="trace-steps">{["Loading imagery", "Preprocessing imagery", "Mapping visual evidence", "Composing answer"].map((step, index) => <div className="trace-step" key={step}><span className="trace-dot">{index < 2 ? <Check/> : <Activity className="spin"/>}</span><div><strong>{step}</strong><small>{index < 2 ? "Complete" : "Executing neural specialist inference..."}</small></div><code>{index < 2 ? `${(index + 1) * 0.8}s` : "—"}</code></div>)}</div><div className="progress"><span style={{ width: "62%" }}/></div><p className="trace-foot">The master agent controller is orchestrating specialists across radiometric and language layers.</p></div> }

function EvidenceViewer({ result }: { result: AnalysisResponse }) { 
  const displayUrl = result.images[0]?.url;
  return <div className="evidence"><div className="evidence-head"><div><span className="eyebrow">VISUAL EVIDENCE / {result.mode === "fusion" ? "FUSED VIEW" : "GROUNDED REGION"}</span><h3>Claims connected to imagery</h3></div><div className="viewer-controls"><button><PanelTop/> Side-by-side</button><button><Layers3/> Overlay</button></div></div><div className="viewer">{displayUrl ? <img src={displayUrl} alt="Satellite analysis evidence"/> : <div style={{ padding: "4rem", textAlign: "center", color: "#64748b" }}>Rendering evidence raster...</div>}{result.annotations.map((annotation) => <div key={annotation.label} className={`annotation ${annotation.color}`} style={{ left: `${annotation.x}%`, top: `${annotation.y}%`, width: `${annotation.width}%`, height: `${annotation.height}%` }}><span>{annotation.label}</span></div>)}<div className="viewer-badge"><Pill tone="dark">{result.imageType}</Pill><span>10 m / px</span></div></div><div className="evidence-legend"><span><i className="cyan-dot"/> Connected evidence</span><span><i className="amber-dot"/> Change / caution region</span><span className="mono">GROUNDING ACTIVE</span></div></div> 
}

function ResultView({ result, technical, setTechnical }: { result: AnalysisResponse; technical: boolean; setTechnical: (value: boolean) => void }) { 
  const parts = result.answer.split(/(\*\*.*?\*\*)/g); 
  const hasGeo = Boolean(result.geographicLocation?.has_location);
  const geo = result.geographicLocation;
  return <div className="result-view"><div className="result-top"><div><span className="eyebrow">ANALYSIS COMPLETE · {result.mode.toUpperCase()}</span><h2>Here is what the imagery shows</h2></div><div className={`confidence ${result.confidence}`}><span>{Math.round(result.confidenceScore * 100)}%</span><small>{confidenceCopy[result.confidence]}</small></div></div><div className="answer">{parts.map((part, index) => part.startsWith("**") ? <strong key={index}>{part.slice(2, -2)}</strong> : <span key={index}>{part}</span>)}</div><EvidenceViewer result={result}/><div className="evidence-list">{result.evidence.map((item, index) => <div key={item}><span>0{index + 1}</span>{item}<Check/></div>)}</div><div className="action-row" style={{ marginTop: "1.2rem", marginBottom: "0.6rem", display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>{hasGeo ? <button type="button" id="view-on-globe-btn" className="primary compact" style={{ display: "inline-flex", alignItems: "center", gap: "0.55rem", padding: "0.65rem 1.25rem", borderRadius: "8px", background: "linear-gradient(135deg, rgba(0, 240, 255, 0.22), rgba(0, 160, 255, 0.15))", border: "1px solid rgba(0, 240, 255, 0.5)", color: "#00f0ff", fontSize: "0.86rem", fontWeight: 600, boxShadow: "0 0 16px rgba(0, 240, 255, 0.15)", cursor: "pointer" }} onClick={() => { const url = buildTrinetraUrl(geo, result.images[0]?.name || "Analysis Target"); if (url) window.open(url, "_blank", "noopener,noreferrer"); }}><Globe size={16} /> View on Globe (TRINETRA) <ArrowRight size={14} /></button> : <div id="globe-disabled-notice" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.55rem 0.95rem", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", color: "rgba(255, 255, 255, 0.45)", fontSize: "0.78rem" }} title="This raster contains no OGC GeoTIFF georeferencing metadata. Real coordinates cannot be fabricated."><Globe size={14} style={{ opacity: 0.5 }} /><span>Georeferencing Unavailable (Non-geospatial image)</span></div>}{result.reportUrl && <a href={result.reportUrl} target="_blank" rel="noreferrer" className="secondary compact" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.65rem 1.2rem", borderRadius: "8px", textDecoration: "none", background: "rgba(255, 255, 255, 0.04)", border: "1px solid rgba(255, 255, 255, 0.12)", color: "rgba(255, 255, 255, 0.85)", fontSize: "0.85rem", fontWeight: 500 }}><PanelTop size={16} /> View Intelligence Report (HTML) <ArrowRight size={14} /></a>}</div><button className="technical-toggle" onClick={() => setTechnical(!technical)}><span><span className="eyebrow">TRACE / METADATA</span><strong>Technical details</strong></span><ChevronDown className={technical ? "rotate" : ""}/></button>{technical && <div className="technical-grid">{[["Model", result.model], ["Resolution", result.resolution], ["Source", result.imageType], ["Processing", result.processingTime], ["Georeferencing", hasGeo && geo?.lat != null ? `${geo.lat.toFixed(4)}°N, ${geo.lng?.toFixed(4)}°E (${geo.crs || "WGS84"})` : "None (Un-georeferenced)"], ["Location Target", geo?.location_name || "N/A"]].map(([label, value]) => <div key={label}><span>{label}</span><b>{value}</b></div>)}</div>}<p className="disclaimer">Confidence reflects image quality and evidence alignment, not certainty. Validate findings before operational decisions.</p></div> 
}

function Dashboard({ navigate }: { navigate: (path: string) => void }) { 
  const [history, setHistory] = useState<AnalysisResponse[]>([]); 
  useEffect(() => setHistory(loadHistory()), []); 
  const dynamicMetrics = useMemo(() => getDynamicMetrics(history), [history]);

  return <main className="page dashboard"><div className="page-intro"><div><Pill><span className="pulse"/>COMMAND CENTER</Pill><h1>Analysis history</h1><p>A concise view of your analysis trail and system signals.</p></div><button className="primary compact" onClick={() => navigate("/analysis")}><ImagePlus/> New analysis</button></div><div className="metric-grid">{dynamicMetrics.map((metric) => <div className="metric" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.delta}</small></div>)}</div><section className="history-card"><div className="section-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Evidence trail</h2></div><div className="search"><Search/><input placeholder="Filter analyses"/></div></div>{history.length === 0 ? <div className="history-empty"><Clock3/><p>No local analyses recorded yet. Run your first scene interpretation to build an evidence trail.</p><button className="secondary" onClick={() => navigate("/analysis")}><Radar size={16}/> Open workspace <ArrowRight/></button></div> : <div className="history-list">{history.map((item) => <button className="history-row" key={item.id} onClick={() => navigate("/analysis")}><span>{formatDate(item.createdAt)}</span><strong>{item.mode === "temporal" ? "Bi-temporal" : item.mode === "fusion" ? "Optical + SAR" : "Single image"}</strong><p>{item.query}</p><Pill tone={item.confidence}>{Math.round(item.confidenceScore * 100)}%</Pill><ArrowRight/></button>)}</div>}</section></main> 
}

function Evaluation({ navigate }: { navigate: (path: string) => void }) { 
  const [healthData, setHealthData] = useState<BackendHealth | null>(null);
  const [registryData, setRegistryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([checkBackendHealth(), analysisAPI.fetchRegistry()]).then(([health, reg]) => {
      setHealthData(health);
      setRegistryData(reg);
    }).finally(() => setLoading(false));
  }, []);

  const models = healthData?.models_status || {};
  const llm = healthData?.llm_status;
  const tools = registryData?.tools || [];

  return <main className="page evaluation"><div className="page-intro"><div><Pill><span className="pulse"/>EVALUATION COCKPIT</Pill><h1>System telemetry & inspection</h1><p>Inspect live multimodal specialist models, reasoning backends, and tool registry.</p></div><button className="secondary compact" onClick={() => navigate("/analysis")}><Radar/> Open workspace</button></div><div className="eval-grid"><section className="evaluation-card"><div className="section-heading"><div><span className="eyebrow">NEURAL & GEOSPATIAL SPECIALISTS</span><h2>Active Specialist Status</h2></div><Cpu size={20} color="var(--cyan-400, #00f0ff)" /></div><div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", marginTop: "1rem" }}>{Object.entries(models).map(([key, val]) => (<div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.6rem 0.8rem", borderRadius: "6px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}><div><strong style={{ fontSize: "0.85rem", color: "#f1f5f9" }}>{val.name}</strong><br/><small style={{ color: "var(--cyan-400, #00f0ff)", fontSize: "0.75rem" }}>{val.engine}</small></div><Pill tone="cyan"><Check size={12} style={{ display: "inline", marginRight: "4px" }}/>READY</Pill></div>))}</div></section><section className="evaluation-card architecture"><span className="eyebrow">LANGUAGE & MULTIMODAL REASONING</span><h2>Active Inference Engine</h2><div style={{ margin: "1rem 0", padding: "0.85rem", borderRadius: "8px", background: "rgba(0, 240, 255, 0.05)", border: "1px solid rgba(0, 240, 255, 0.2)" }}><strong style={{ color: "var(--cyan-400, #00f0ff)", fontSize: "1rem" }}>{llm?.active_engine || "Initializing..."}</strong><p style={{ fontSize: "0.82rem", color: "#94a3b8", marginTop: "0.35rem" }}>Mode: {llm?.engine_mode || "local"} · {llm?.ollama?.status_message || "Active"}</p></div><div className="arch-flow"><span>INPUT RASTERS</span><ArrowRight/><span>AGENT CONTROLLER</span><ArrowRight/><span>EVIDENCE & REPORT</span></div><p>Registered tools in master controller: <b>{tools.length || 6} specialist tools</b></p><button className="secondary" onClick={() => navigate("/analysis")}>Test live scenario <ArrowRight/></button></section></div></main> 
}

export default function Page() { 
  const { isAuthenticated, loading } = useAuth();
  const [path, setPath] = useState(() => typeof window === "undefined" ? "/" : window.location.pathname); 

  const navigate = (next: string) => { 
    const clean = next.split("?")[0]; 
    setPath(clean); 
    window.history.pushState({}, "", next);
  }; 

  useEffect(() => { 
    const sync = () => setPath(window.location.pathname); 
    sync(); 
    window.addEventListener("popstate", sync); 
    return () => window.removeEventListener("popstate", sync);
  }, []); 

  const page = useMemo(() => {
    if (path === "/") {
      return <Landing navigate={navigate}/>;
    }

    // Security Gate: require sign in for operational workspace, history, and telemetry
    if (!isAuthenticated) {
      return <AuthGate />;
    }

    if (path === "/analysis") {
      return <Workspace navigate={navigate} initialSample={typeof window !== "undefined" && window.location.search.includes("sample=1")}/>;
    }
    if (path === "/dashboard") {
      return <Dashboard navigate={navigate}/>;
    }
    if (path === "/evaluation") {
      return <Evaluation navigate={navigate}/>;
    }

    return <Landing navigate={navigate}/>;
  }, [path, isAuthenticated]); 

  return (
    <div className="app-shell">
      <Header path={path} navigate={navigate}/>
      {page}
      <footer>
        <span>SatQuery AI · SIH 2026 / PS 26167</span>
        <span>ISRO MULTIMODAL EARTH OBSERVATION INTELLIGENCE</span>
      </footer>
    </div>
  );
}

