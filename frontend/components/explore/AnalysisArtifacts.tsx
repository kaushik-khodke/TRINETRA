/**
 * TRINETRA — Phase 5: Analysis Artifacts Panel
 * Downloadable vector GeoJSON, inspection manifests, and annotated previews.
 */

import React from "react"
import { AnalysisArtifact } from "@/lib/explore/types"
import { Download, FileCode2, FileText, Image as ImageIcon, Check, Copy } from "lucide-react"

interface Props {
  artifacts: AnalysisArtifact[]
  runId: string
}

export const AnalysisArtifacts: React.FC<Props> = ({ artifacts, runId }) => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null)

  if (!artifacts || artifacts.length === 0) {
    return (
      <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg text-center text-xs text-slate-400">
        No artifacts exported for this analysis run.
      </div>
    )
  }

  const handleCopy = (url: string, id: string) => {
    navigator.clipboard.writeText(url)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs font-semibold text-slate-300 font-mono">
        <span>Exported Artifacts ({artifacts.length})</span>
      </div>

      <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
        {artifacts.map((art) => {
          const isGeoJson = art.mime_type.includes("json") && art.name.includes("geojson")
          const isImage = art.mime_type.startsWith("image/")

          return (
            <div
              key={art.artifact_id}
              className="p-2.5 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center justify-between gap-2 text-xs font-mono hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                {isGeoJson ? (
                  <FileCode2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : isImage ? (
                  <ImageIcon className="w-4 h-4 text-orange-400 shrink-0" />
                ) : (
                  <FileText className="w-4 h-4 text-purple-400 shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="font-semibold text-slate-200 truncate">{art.name}</p>
                  <p className="text-[10px] text-slate-400 capitalize">
                    {art.artifact_type.replace(/_/g, " ")} •{" "}
                    {art.size_bytes ? `${Math.round(art.size_bytes / 1024)} KB` : "Dynamic"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => handleCopy(art.download_url, art.artifact_id)}
                  title="Copy URL"
                  className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                >
                  {copiedId === art.artifact_id ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
                <a
                  href={art.download_url}
                  download={art.name}
                  target="_blank"
                  rel="noreferrer"
                  title="Download Artifact"
                  className="p-1.5 bg-orange-600/20 hover:bg-orange-600/30 text-orange-300 border border-orange-500/30 rounded transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
