import React from 'react';
import { ShieldCheck, Download, Activity, FileText } from 'lucide-react';

export default function ResultCard({ result }) {
  if (!result) return null;

  const resData = result.result || {};
  const confidence = Math.round((result.confidence || 0.85) * 100);
  const task = (result.task || 'ANALYSIS').replace('_', ' ');

  const answer =
    resData.answer ||
    resData.caption ||
    (resData.regions
      ? `Successfully localized ${resData.regions.length} feature region(s) matching the query phrase.`
      : 'Analysis completed successfully.');

  return (
    <div className="result-card">
      <div className="answer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className="task-tag">{task}</span>
          {resData.engine && (
            <span className="mono" style={{ fontSize: '11px', color: '#10B981', background: '#0F251E', border: '1px solid #10B98144', padding: '2px 8px', borderRadius: '4px' }}>
              ⚙ {resData.engine}
            </span>
          )}
          <span className="mono" style={{ fontSize: '11px', color: '#64748B' }}>
            ID: {result.request_id?.slice(0, 8)}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div className="confidence-gauge">
            <ShieldCheck size={16} />
            <span>CONFIDENCE {confidence}%</span>
          </div>

          <a
            href={result.reports?.html_report_url || `/api/v1/reports/${result.request_id}/html`}
            target="_blank"
            rel="noopener noreferrer"
            className="report-download-btn"
            title="Open printable mission report"
          >
            <Download size={14} />
            Mission Report
          </a>
        </div>
      </div>

      <div className="answer-text">&ldquo;{answer}&rdquo;</div>

      {/* Sensor Contributions (Optical-SAR) */}
      {resData.sensor_contributions && (
        <div style={{ background: '#0B1015', border: '1px solid #1E2934', borderRadius: '6px', padding: '12px', marginBottom: '14px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#10B981', textTransform: 'uppercase', marginBottom: '6px' }}>
            Complementary Sensor Contributions:
          </div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>
            <strong>Optical:</strong> {resData.sensor_contributions.optical}
          </div>
          <div style={{ fontSize: '12px', color: '#F59E0B' }}>
            <strong>SAR Radar:</strong> {resData.sensor_contributions.sar}
          </div>
        </div>
      )}

      {/* Change Statistics (Bi-Temporal) */}
      {resData.change_statistics && (
        <div className="indices-grid">
          <div className="index-box">
            <div className="index-label">Surface Shift Area</div>
            <div className="index-val" style={{ color: '#F59E0B' }}>
              {resData.change_statistics.changed_area_percentage}%
            </div>
          </div>
          <div className="index-box">
            <div className="index-label">Mean Difference Index</div>
            <div className="index-val">
              {resData.change_statistics.mean_difference}
            </div>
          </div>
          <div className="index-box">
            <div className="index-label">Temporal Drift Status</div>
            <div className="index-val mono" style={{ fontSize: '13px', textTransform: 'uppercase' }}>
              {resData.change_status || 'DETECTED'}
            </div>
          </div>
        </div>
      )}

      {/* Land-Cover Breakdown (Captioning) */}
      {resData.land_cover_breakdown && (
        <div className="indices-grid">
          {Object.entries(resData.land_cover_breakdown).map(([k, v], idx) => (
            <div key={idx} className="index-box">
              <div className="index-label">{k}</div>
              <div className="index-val">{v}</div>
            </div>
          ))}
        </div>
      )}

      {/* Remote-Sensing Spectral Metrics (VQA) */}
      {resData.evidence_metrics && (
        <div className="indices-grid">
          <div className="index-box">
            <div className="index-label">Mean NDVI (Vegetation)</div>
            <div className="index-val">{resData.evidence_metrics.mean_ndvi}</div>
          </div>
          <div className="index-box">
            <div className="index-label">Mean NDWI (Water)</div>
            <div className="index-val">{resData.evidence_metrics.mean_ndwi}</div>
          </div>
          <div className="index-box">
            <div className="index-label">Vegetation Cover</div>
            <div className="index-val">{resData.evidence_metrics.vegetation_cover_pct}%</div>
          </div>
          <div className="index-box">
            <div className="index-label">Built-Up Density</div>
            <div className="index-val">{resData.evidence_metrics.built_up_density_pct}%</div>
          </div>
        </div>
      )}
    </div>
  );
}
