import React, { useState, useEffect } from 'react';
import { Eye, Layers, Compass, Crosshair, Sparkles, CheckCircle2 } from 'lucide-react';

export default function ImageViewer({ result, loading, stagedFiles }) {
  const [activeLayer, setActiveLayer] = useState('evidence'); // 'evidence', 'raw', 'fused', 'split'
  const [stagedUrls, setStagedUrls] = useState([]);

  // Generate object URLs for staged local files
  useEffect(() => {
    if (stagedFiles && stagedFiles.length > 0) {
      const urls = stagedFiles.map((f) => URL.createObjectURL(f));
      setStagedUrls(urls);
      return () => {
        urls.forEach((u) => URL.revokeObjectURL(u));
      };
    } else {
      setStagedUrls([]);
    }
  }, [stagedFiles]);

  if (loading) {
    return (
      <div className="viewport-container" style={{ flexDirection: 'column', gap: '16px' }}>
        <div className="radar-pulse" style={{ width: '28px', height: '28px' }}></div>
        <div className="mono" style={{ fontSize: '13px', color: '#10B981', letterSpacing: '0.05em' }}>
          AGENT INFERENCE &amp; EVIDENCE GENERATION IN PROGRESS...
        </div>
        <div style={{ fontSize: '11px', color: '#64748B' }}>
          Computing spectral indices, spatial contours, and vision-language synthesis...
        </div>
      </div>
    );
  }

  // Case 1: Active Analysis Result Available
  if (result && result.result) {
    const task = result.task;
    const resData = result.result || {};
    const isBiTemporal = task === 'change_analysis';
    const isOpticalSar = task === 'optical_sar_fusion';

    // Bi-Temporal Dual Viewport
    if (isBiTemporal && resData.evidence) {
      const { t1_preview, t2_preview, change_heatmap } = resData.evidence;
      return (
        <div className="viewport-container" style={{ flexDirection: 'column', padding: '10px' }}>
          <div className="dual-viewport-grid">
            <div className="dual-cell">
              <div className="dual-cell-badge">T1 (BASELINE DATE)</div>
              <img src={t1_preview} alt="T1 Baseline" style={{ width: '100%', height: 'auto', display: 'block' }} />
            </div>
            <div className="dual-cell">
              <div className="dual-cell-badge" style={{ color: '#F59E0B' }}>
                {activeLayer === 'evidence' ? 'T2 + CHANGE HEATMAP' : 'T2 (MONITORING DATE)'}
              </div>
              <img
                src={activeLayer === 'evidence' ? change_heatmap : t2_preview}
                alt="T2 Monitoring"
                style={{ width: '100%', height: 'auto', display: 'block' }}
              />
            </div>
          </div>

          <div className="viewport-toolbar">
            <button
              className={`overlay-toggle-btn ${activeLayer === 'evidence' ? 'active' : ''}`}
              onClick={() => setActiveLayer('evidence')}
            >
              Solar Amber Change Heatmap
            </button>
            <button
              className={`overlay-toggle-btn ${activeLayer === 'raw' ? 'active' : ''}`}
              onClick={() => setActiveLayer('raw')}
            >
              Raw T2 Observation
            </button>
            <span className="mono" style={{ fontSize: '11px', color: '#10B981', marginLeft: 'auto' }}>
              ✓ DIFFERENTIAL SHIFT OVERLAY
            </span>
          </div>
        </div>
      );
    }

    // Optical + SAR Cross-Modal Viewport
    if (isOpticalSar && resData.evidence) {
      const { optical_preview, sar_preview, fused_composite } = resData.evidence;
      return (
        <div className="viewport-container" style={{ flexDirection: 'column', padding: '10px' }}>
          {activeLayer === 'fused' ? (
            <div style={{ position: 'relative', textAlign: 'center', width: '100%' }}>
              <div className="dual-cell-badge" style={{ color: '#10B981' }}>
                CROSS-MODAL FUSED COMPOSITE (OPTICAL + SAR)
              </div>
              <img src={fused_composite} alt="Fused Composite" className="viewport-display-img" />
            </div>
          ) : (
            <div className="dual-viewport-grid">
              <div className="dual-cell">
                <div className="dual-cell-badge">OPTICAL MULTI-SPECTRAL</div>
                <img src={optical_preview} alt="Optical Sensor" style={{ width: '100%', height: 'auto', display: 'block' }} />
              </div>
              <div className="dual-cell">
                <div className="dual-cell-badge" style={{ color: '#F59E0B' }}>
                  SAR MICROWAVE RADAR
                </div>
                <img src={sar_preview} alt="SAR Sensor" style={{ width: '100%', height: 'auto', display: 'block' }} />
              </div>
            </div>
          )}

          <div className="viewport-toolbar">
            <button
              className={`overlay-toggle-btn ${activeLayer === 'fused' ? 'active' : ''}`}
              onClick={() => setActiveLayer('fused')}
            >
              Cross-Modal Fused Composite
            </button>
            <button
              className={`overlay-toggle-btn ${activeLayer !== 'fused' ? 'active' : ''}`}
              onClick={() => setActiveLayer('split')}
            >
              Side-By-Side Sensors (Dual Lens)
            </button>
            <span className="mono" style={{ fontSize: '11px', color: '#10B981', marginLeft: 'auto' }}>
              ✓ DUAL-SENSOR CO-REGISTRATION
            </span>
          </div>
        </div>
      );
    }

    // Single Image Viewport (VQA, Captioning, Grounding)
    const evidenceImg = resData.evidence_image;
    const rawImg = resData.raw_preview || (result.image_previews && result.image_previews[0]);
    const displaySrc = (activeLayer === 'evidence' && evidenceImg) ? evidenceImg : (rawImg || evidenceImg);

    const meta = (result.inputs_metadata && result.inputs_metadata[0]) || {};
    const dimInfo = meta.width && meta.height ? `${meta.width}x${meta.height}` : 'OBSERVATION';
    const modInfo = (meta.modality || 'optical').toUpperCase();

    return (
      <div className="viewport-container" style={{ flexDirection: 'column' }}>
        {displaySrc ? (
          <img
            src={displaySrc}
            alt="Analyzed User Imagery"
            className="viewport-display-img"
          />
        ) : (
          <div style={{ color: '#64748B', padding: '40px' }}>Raster preview unavailable.</div>
        )}

        <div className="viewport-toolbar">
          {evidenceImg && (
            <button
              className={`overlay-toggle-btn ${activeLayer === 'evidence' ? 'active' : ''}`}
              onClick={() => setActiveLayer('evidence')}
            >
              {task === 'grounding' ? 'Tactical Bounding Overlay' : 'Feature Saliency Heatmap'}
            </button>
          )}
          {rawImg && (
            <button
              className={`overlay-toggle-btn ${activeLayer === 'raw' ? 'active' : ''}`}
              onClick={() => setActiveLayer('raw')}
            >
              Raw {modInfo} Raster
            </button>
          )}
          <span className="mono" style={{ fontSize: '11px', color: '#94A3B8', marginLeft: '6px' }}>
            [{dimInfo}]
          </span>
          <span className="mono" style={{ fontSize: '11px', color: '#10B981', marginLeft: 'auto' }}>
            ✓ GROUNDED EVIDENCE
          </span>
        </div>
      </div>
    );
  }

  // Case 2: New files staged by user, awaiting analysis
  if (stagedFiles && stagedFiles.length > 0 && stagedUrls.length > 0) {
    if (stagedFiles.length === 1) {
      return (
        <div className="viewport-container" style={{ flexDirection: 'column' }}>
          <div style={{ position: 'relative', width: '100%', textAlign: 'center' }}>
            <div className="dual-cell-badge" style={{ color: '#10B981' }}>
              STAGED OBSERVATION: {stagedFiles[0].name}
            </div>
            <img
              src={stagedUrls[0]}
              alt="Staged Target"
              className="viewport-display-img"
            />
          </div>
          <div className="viewport-toolbar">
            <span className="mono" style={{ fontSize: '11px', color: '#F59E0B' }}>
              READY FOR ANALYSIS • CLICK &ldquo;EXECUTE MULTIMODAL ANALYSIS&rdquo;
            </span>
          </div>
        </div>
      );
    } else {
      return (
        <div className="viewport-container" style={{ flexDirection: 'column', padding: '10px' }}>
          <div className="dual-viewport-grid">
            <div className="dual-cell">
              <div className="dual-cell-badge">INPUT 1: {stagedFiles[0].name}</div>
              <img src={stagedUrls[0]} alt="Input 1" style={{ width: '100%', height: 'auto', display: 'block' }} />
            </div>
            <div className="dual-cell">
              <div className="dual-cell-badge" style={{ color: '#F59E0B' }}>
                INPUT 2: {stagedFiles[1]?.name || 'Secondary'}
              </div>
              {stagedUrls[1] && (
                <img src={stagedUrls[1]} alt="Input 2" style={{ width: '100%', height: 'auto', display: 'block' }} />
              )}
            </div>
          </div>
          <div className="viewport-toolbar">
            <span className="mono" style={{ fontSize: '11px', color: '#F59E0B' }}>
              PAIRED RASTERS STAGED • CLICK &ldquo;EXECUTE MULTIMODAL ANALYSIS&rdquo;
            </span>
          </div>
        </div>
      );
    }
  }

  // Case 3: Idle state
  return (
    <div className="viewport-container" style={{ flexDirection: 'column', color: '#64748B' }}>
      <Compass size={48} style={{ opacity: 0.3, marginBottom: '12px' }} />
      <div style={{ fontSize: '14px', fontWeight: 500 }}>No Active Geospatial Target</div>
      <div style={{ fontSize: '12px', marginTop: '4px' }}>
        Upload remote-sensing imagery (.tif, .png) or select a 1-click benchmark preset to begin.
      </div>
    </div>
  );
}
