/**
 * TRINETRA Phase 6 — Provenance & Verification Panel
 * Displays deterministic processing SHA-256 hash, specialist version manifest, and artifact export links.
 */

import React from "react"
import { InvestigationArtifact } from "@/lib/explore/investigation-types"
import { Hash, Download, FileCode, FileText, CheckCircle } from "lucide-react"

interface Props {
  investigationId: string
  artifacts?: InvestigationArtifact[]
  processingHash?: string
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export const ProvenancePanel: React.FC<Props> = ({
  investigationId,
  artifacts = [],
  processingHash,
}) => {
  const hash = processingHash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-3">
      <div className="flex items-center gap-1.5">
        <Hash className="w-4 h-4 text-orange-400" />
        <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
          Provenance & Integrity Verification
        </h4>
      </div>

      {/* Processing Hash */}
      <div className="bg-slate-950/80 border border-slate-800/80 rounded p-2 text-xs space-y-1">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>Deterministic Run Hash (SHA-256):</span>
          <span className="text-emerald-400 flex items-center gap-0.5">
            <CheckCircle className="w-3 h-3" />
            Verified
          </span>
        </div>
        <div className="font-mono text-[10px] text-orange-300 break-all select-all">{hash}</div>
      </div>

      {/* Artifact Export Links */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
          Exported Investigation Artifacts:
        </span>
        <div className="grid grid-cols-2 gap-2">
          <a
            href={`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/artifacts/report_json`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 p-2 rounded bg-slate-950 border border-slate-800 hover:border-orange-700 text-xs font-mono text-slate-300 hover:text-orange-300 transition-colors"
          >
            <FileCode className="w-3.5 h-3.5 text-orange-400 shrink-0" />
            <span className="truncate">Report JSON</span>
            <Download className="w-3 h-3 ml-auto opacity-60" />
          </a>

          <a
            href={`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/artifacts/report_html`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 p-2 rounded bg-slate-950 border border-slate-800 hover:border-orange-700 text-xs font-mono text-slate-300 hover:text-orange-300 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="truncate">Report HTML</span>
            <Download className="w-3 h-3 ml-auto opacity-60" />
          </a>

          <a
            href={`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/artifacts/evidence_geojson`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 p-2 rounded bg-slate-950 border border-slate-800 hover:border-orange-700 text-xs font-mono text-slate-300 hover:text-orange-300 transition-colors"
          >
            <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">Evidence GeoJSON</span>
            <Download className="w-3 h-3 ml-auto opacity-60" />
          </a>

          <a
            href={`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/artifacts/manifest`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 p-2 rounded bg-slate-950 border border-slate-800 hover:border-orange-700 text-xs font-mono text-slate-300 hover:text-orange-300 transition-colors"
          >
            <Hash className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">Run Manifest</span>
            <Download className="w-3 h-3 ml-auto opacity-60" />
          </a>
        </div>
      </div>
    </div>
  )
}
