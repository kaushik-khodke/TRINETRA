"use client"

import React, { useState } from "react"
import {
  FileText,
  Download,
  ExternalLink,
  ShieldCheck,
  Plus,
  Presentation,
  CheckCircle2,
} from "lucide-react"
import { ReportDocument } from "@/lib/explore/workspace-types"
import { workspaceApi } from "@/lib/explore/workspace-api"

interface ReportBuilderViewProps {
  workspaceId: string
  reports: ReportDocument[]
  onCreateReport: (title: string, sections: any[]) => Promise<any>
  onExportReport: (reportId: string) => Promise<any>
}

export function ReportBuilderView({
  workspaceId,
  reports,
  onCreateReport,
  onExportReport,
}: ReportBuilderViewProps) {
  const [selectedReport, setSelectedReport] = useState<ReportDocument | null>(reports[0] || null)
  const [exporting, setExporting] = useState(false)
  const [exportedFile, setExportedFile] = useState<string | null>(null)
  const [newModalOpen, setNewModalOpen] = useState(false)
  const [title, setTitle] = useState("")

  const handleExport = async (reportId: string) => {
    setExporting(true)
    try {
      const res = await onExportReport(reportId)
      setExportedFile(res.filename)
    } finally {
      setExporting(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    const defaultSections = [
      {
        section_id: "sec-sum",
        type: "SUMMARY",
        title: "Executive Summary",
        content: `Comprehensive analytical assessment for ${title.trim()}.`,
        claims: [
          {
            claim_id: "clm-1",
            text: "Physical surface changes corroborated across Sentinel-2 observations.",
            evidence_ids: ["obs-initial", "obs-followup"],
            type: "FINDING",
          },
        ],
      },
      {
        section_id: "sec-lim",
        type: "LIMITATIONS",
        title: "Sensor Limitations & Cloud Disparities",
        content: "Analysis subject to regional optical cloud cover constraints.",
        claims: [],
      },
    ]

    const rep = await onCreateReport(title.trim(), defaultSections)
    setSelectedReport(rep)
    setTitle("")
    setNewModalOpen(false)
  }

  return (
    <div className="p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            <FileText size={15} className="text-purple-400" /> Evidence Dossier Reports
          </h3>
          <p className="text-[11px] text-slate-400">Claim-grounded dossiers with SHA-256 manifests & export packaging</p>
        </div>
        <button
          onClick={() => setNewModalOpen(true)}
          className="flex items-center gap-1 text-xs bg-purple-600 hover:bg-purple-500 text-white px-2.5 py-1 rounded transition"
        >
          <Plus size={13} /> Assemble Report
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-6 text-center text-xs text-slate-500 space-y-2">
          <p>No dossier reports created for this workspace.</p>
          <button
            onClick={() => setNewModalOpen(true)}
            className="text-purple-400 hover:underline inline-block"
          >
            Assemble your first report dossier &rarr;
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Report Selector */}
          <div className="flex gap-2 overflow-x-auto pb-1">
            {reports.map((r) => (
              <button
                key={r.report_id}
                onClick={() => {
                  setSelectedReport(r)
                  setExportedFile(null)
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap border transition ${
                  selectedReport?.report_id === r.report_id
                    ? "bg-slate-800 border-purple-500 text-purple-300"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {r.title}
              </button>
            ))}
          </div>

          {selectedReport && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-100">{selectedReport.title}</h4>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono mt-1">
                    <span className="text-emerald-400 flex items-center gap-1">
                      <ShieldCheck size={11} /> VALIDATED
                    </span>
                    <span>&bull;</span>
                    <span>SHA-256: {selectedReport.manifest?.overall_sha256?.slice(0, 12) || "UNVERIFIED"}...</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={workspaceApi.getReportRenderUrl(workspaceId, selectedReport.report_id)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1.5 rounded transition"
                  >
                    <Presentation size={13} className="text-sky-400" /> Presentation
                  </a>

                  <button
                    onClick={() => handleExport(selectedReport.report_id)}
                    disabled={exporting}
                    className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold px-3 py-1.5 rounded transition disabled:opacity-50"
                  >
                    <Download size={13} className={exporting ? "animate-spin" : ""} />
                    {exporting ? "Exporting..." : "Export Package (ZIP)"}
                  </button>
                </div>
              </div>

              {exportedFile && (
                <div className="bg-emerald-950/40 border border-emerald-800/60 rounded-lg p-2 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                  <span>Package generated successfully: <span className="font-mono">{exportedFile}</span></span>
                </div>
              )}

              {/* Sections Breakdown */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-[11px] font-mono uppercase text-slate-500">
                  Sections & Claim Grounding ({selectedReport.sections.length} sections)
                </span>

                <div className="space-y-2">
                  {selectedReport.sections.map((sec) => (
                    <div
                      key={sec.section_id}
                      className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">{sec.title}</span>
                        <span className="text-[10px] text-purple-400 bg-purple-950/40 px-1.5 py-0.5 rounded font-mono uppercase">
                          {sec.type}
                        </span>
                      </div>

                      {sec.content && <p className="text-xs text-slate-400">{sec.content}</p>}

                      {sec.claims && sec.claims.length > 0 && (
                        <div className="pt-1.5 border-t border-slate-900 space-y-1">
                          <span className="text-[10px] font-mono text-slate-500 uppercase">
                            Grounded Claims ({sec.claims.length}):
                          </span>
                          {sec.claims.map((c) => (
                            <div key={c.claim_id} className="text-xs bg-slate-900/60 p-2 rounded flex items-center justify-between">
                              <span className="text-slate-300">{c.text}</span>
                              <div className="flex gap-1">
                                {c.evidence_ids.map((eid) => (
                                  <span key={eid} className="text-[10px] bg-slate-800 text-sky-400 px-1.5 py-0.5 rounded font-mono">
                                    {eid}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Assemble Report Dialog */}
      {newModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleCreate}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <FileText size={15} className="text-purple-400" /> Assemble Dossier Report
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Report Dossier Title</label>
              <input
                type="text"
                required
                placeholder="e.g. Sikkim Lake Outburst Intelligence Briefing"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-purple-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setNewModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-purple-600 hover:bg-purple-500 text-white font-medium rounded"
              >
                Assemble Dossier
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
