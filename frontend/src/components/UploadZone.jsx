import React, { useRef } from 'react';
import { UploadCloud, Layers, Zap, Image as ImageIcon, CheckCircle, Sparkles } from 'lucide-react';

export default function UploadZone({
  inputMode,
  setInputMode,
  files,
  setFiles,
  query,
  setQuery,
  onAnalyze,
  loading,
  presets,
  onRunPreset
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const getSuggestedQueries = () => {
    if (inputMode === 'optical_sar') {
      return [
        "Use optical and SAR images together to identify built-up and water-covered regions.",
        "Extract complementary structural and spectral signatures from both sensors.",
        "Does SAR radar backscatter confirm building boundaries beneath cloud shadows?"
      ];
    } else if (inputMode === 'bi_temporal') {
      return [
        "What changed between these two dates, and where did the change occur?",
        "Has the built-up area increased, decreased, or remained unchanged?",
        "Highlight newly constructed parcels and quantify surface modifications."
      ];
    } else {
      return [
        "What are the predominant land-cover types and is there any water body present?",
        "Highlight the water body referred to in the query",
        "Describe the land-cover and major objects visible in this image.",
        "Locate the airport runway / transport corridor in this scene."
      ];
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">
          <Layers size={16} style={{ color: '#10B981' }} />
          Mission Ingestion
        </span>
      </div>

      {/* Input Mode Selector */}
      <div className="workflow-pills">
        <button
          className={`workflow-btn ${inputMode === 'single' ? 'active' : ''}`}
          onClick={() => { setInputMode('single'); setFiles([]); }}
        >
          <ImageIcon size={16} />
          Single Image
        </button>
        <button
          className={`workflow-btn ${inputMode === 'bi_temporal' ? 'active' : ''}`}
          onClick={() => { setInputMode('bi_temporal'); setFiles([]); }}
        >
          <Layers size={16} />
          Bi-Temporal
        </button>
        <button
          className={`workflow-btn ${inputMode === 'optical_sar' ? 'active' : ''}`}
          onClick={() => { setInputMode('optical_sar'); setFiles([]); }}
        >
          <Zap size={16} />
          Optical + SAR
        </button>
      </div>

      {/* Dropzone */}
      <div
        className="dropzone-box"
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple={inputMode !== 'single'}
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".tif,.tiff,.png,.jpg,.jpeg"
        />
        <UploadCloud size={32} style={{ color: '#10B981', margin: '0 auto' }} />
        <div className="dropzone-title">
          {inputMode === 'single'
            ? 'Select or Drop 1 Satellite Image'
            : inputMode === 'bi_temporal'
            ? 'Select 2 Temporal Images (T1 and T2)'
            : 'Select 2 Co-Registered Images (Optical + SAR)'}
        </div>
        <div className="dropzone-sub">
          Supported: GeoTIFF (.tif, .tiff), PNG, JPEG
        </div>

        {files.length > 0 && (
          <div style={{ marginTop: '14px', display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
            {files.map((f, i) => (
              <div key={i} style={{ textAlign: 'center', background: '#141C24', border: '1px solid #273747', padding: '6px', borderRadius: '6px' }}>
                <img
                  src={URL.createObjectURL(f)}
                  alt="thumbnail"
                  style={{ width: '64px', height: '64px', objectFit: 'cover', borderRadius: '4px', display: 'block', margin: '0 auto 4px' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
                <div className="mono" style={{ fontSize: '10px', color: '#10B981', maxWidth: '85px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  ✓ {f.name}
                </div>
                <div style={{ fontSize: '9px', color: '#64748B' }}>
                  {Math.round(f.size / 1024)} KB
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Natural Language Query Console */}
      <div className="query-box">
        <label style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Natural-Language Query
        </label>
        <textarea
          className="query-textarea"
          placeholder="e.g. What changed between these dates? or Highlight the water body..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {/* Suggested Prompts */}
      <div style={{ marginTop: '8px' }}>
        <div style={{ fontSize: '10px', color: '#64748B', marginBottom: '6px', textTransform: 'uppercase' }}>
          Suggested Inquiries:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {getSuggestedQueries().map((qText, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(qText)}
              style={{
                background: 'none',
                border: 'none',
                textAlign: 'left',
                fontSize: '11px',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '2px 0'
              }}
              onMouseEnter={(e) => (e.target.style.color = '#10B981')}
              onMouseLeave={(e) => (e.target.style.color = '#94A3B8')}
            >
              › {qText}
            </button>
          ))}
        </div>
      </div>

      {/* Execute Button */}
      <button
        className="action-btn"
        onClick={onAnalyze}
        disabled={loading || files.length === 0 || !query.trim()}
      >
        <Sparkles size={16} />
        {loading ? 'AGENT ORCHESTRATING...' : 'DISPATCH ANALYSIS'}
      </button>

      {/* 1-Click Evaluation Presets Showcase */}
      <div style={{ marginTop: '22px', borderTop: '1px solid #1E2934', paddingTop: '16px' }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: '#F59E0B', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Zap size={14} />
          1-Click SIH Benchmark Presets
        </div>
        <div className="preset-list">
          {presets.map((preset) => (
            <div
              key={preset.id}
              className="preset-item"
              onClick={() => onRunPreset(preset.id)}
            >
              <div className="preset-item-title">{preset.title}</div>
              <div className="preset-item-sub">&ldquo;{preset.query}&rdquo;</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
