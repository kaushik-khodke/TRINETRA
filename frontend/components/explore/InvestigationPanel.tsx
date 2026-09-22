/**
 * TRINETRA Phase 6 — Investigation Analyst Workspace Panel
 * Root workstation container hosting multi-modal evidence fusion, semantic hypotheses,
 * object tracking, multi-temporal timeline, and analyst annotations.
 */

import React, { useState } from "react"
import { useInvestigationState } from "@/lib/explore/investigation-state"
import { InvestigationComposer } from "./InvestigationComposer"
import { InvestigationProgress } from "./InvestigationProgress"
import { FindingsDashboard } from "./FindingsDashboard"
import { EvidenceCard } from "./EvidenceCard"
import { EvidenceGraph } from "./EvidenceGraph"
import { InvestigationTimeline } from "./InvestigationTimeline"
import { ObjectTrackPanel } from "./ObjectTrackPanel"
import { ProvenancePanel } from "./ProvenancePanel"
import { AnalystNotes } from "./AnalystNotes"
import { InvestigationHistory } from "./InvestigationHistory"
import { SemanticLegend } from "./SemanticLegend"
import {
  FileText,
  Share2,
  Calendar,
  Box,
  StickyNote,
  Hash,
  History,
  XCircle,
  PlusCircle,
  Filter,
} from "lucide-react"

interface Props {
  availableObservationIds?: string[]
  aoiGeometry?: Record<string, any> | null
  onFocusEvidenceOnMap?: (evidenceId: string) => void
}

type WorkspaceTab =
  | "findings"
  | "evidence"
  | "timeline"
  | "objects"
  | "notes"
  | "provenance"
  | "history"

export const InvestigationPanel: React.FC<Props> = ({
  availableObservationIds = [],
  aoiGeometry,
  onFocusEvidenceOnMap,
}) => {
  const {
    activeInvestigationId,
    currentInvestigation,
    investigationHistory,
    evidenceCards,
    evidenceRelationships,
    evidenceConflicts,
    findings,
    timeline,
    notes,
    selectedEvidenceId,
    selectedFindingId,
    validation,
    isSubmitting,
    error,
    startInvestigation,
    cancelInvestigation,
    loadInvestigation,
    validateEnquiry,
    setSelectedEvidenceId,
    setSelectedFindingId,
    addNote,
    deleteNote,
  } = useInvestigationState()

  const [activeTab, setActiveTab] = useState<WorkspaceTab>("findings")
  const [showComposer, setShowComposer] = useState<boolean>(!currentInvestigation)
  const [evidenceFilter, setEvidenceFilter] = useState<string>("ALL")

  const handleLaunch = async (question: string, observationIds: string[]) => {
    try {
      await startInvestigation({
        question,
        observation_ids: observationIds,
        aoi: aoiGeometry || undefined,
      })
      setShowComposer(false)
      setActiveTab("findings")
    } catch (e) {
      console.error(e)
    }
  }

  const handleFocusEvidence = (eid: string) => {
    setSelectedEvidenceId(eid)
    onFocusEvidenceOnMap?.(eid)
  }

  const filteredEvidenceCards = evidenceCards.filter((card) => {
    if (evidenceFilter === "ALL") return true
    if (evidenceFilter === "CONFLICTS") return card.has_conflict
    return card.type === evidenceFilter
  })

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 space-y-3 p-3 overflow-y-auto">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
        <div className="flex flex-col">
          <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-wider">
            TRINETRA Phase 6
          </span>
          <h2 className="text-sm font-bold text-slate-100">Analyst Investigation Workspace</h2>
        </div>

        <div className="flex items-center gap-1.5">
          {currentInvestigation && (
            <button
              onClick={() => setShowComposer(!showComposer)}
              className="inline-flex items-center gap-1 px-2 py-1 bg-slate-800 hover:bg-slate-700 text-[11px] font-mono rounded text-slate-200 transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5 text-cyan-400" />
              <span>{showComposer ? "Hide Composer" : "New Enquiry"}</span>
            </button>
          )}

          {currentInvestigation?.status === "running" && (
            <button
              onClick={cancelInvestigation}
              className="inline-flex items-center gap-1 px-2 py-1 bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-[11px] font-mono rounded text-rose-300 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Query Composer (Collapsible) */}
      {showComposer && (
        <InvestigationComposer
          isSubmitting={isSubmitting}
          validation={validation}
          availableObservationIds={availableObservationIds}
          onSubmit={handleLaunch}
          onValidate={(q, obs) => validateEnquiry({ question: q, observation_ids: obs, aoi: aoiGeometry || undefined })}
        />
      )}

      {/* Real-time Progress Bar */}
      {currentInvestigation && currentInvestigation.status !== "completed" && (
        <InvestigationProgress
          progress={currentInvestigation.progress}
          status={currentInvestigation.status}
        />
      )}

      {/* Workspace Navigation Tabs */}
      {currentInvestigation && (
        <>
          <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-slate-800 text-xs font-mono">
            {[
              { id: "findings" as WorkspaceTab, label: "Findings", icon: FileText, count: findings.length },
              { id: "evidence" as WorkspaceTab, label: "Evidence Graph", icon: Share2, count: evidenceCards.length },
              { id: "timeline" as WorkspaceTab, label: "Timeline", icon: Calendar, count: timeline.length },
              { id: "objects" as WorkspaceTab, label: "Objects", icon: Box },
              { id: "notes" as WorkspaceTab, label: "Notes", icon: StickyNote, count: notes.length },
              { id: "provenance" as WorkspaceTab, label: "Provenance", icon: Hash },
              { id: "history" as WorkspaceTab, label: "History", icon: History },
            ].map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-all shrink-0 ${
                    isActive
                      ? "bg-cyan-950 text-cyan-300 font-bold border border-cyan-700/80 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && tab.count > 0 && (
                    <span className="text-[10px] px-1 rounded-full bg-slate-800 text-slate-300">
                      {tab.count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Active Tab Views */}
          <div className="space-y-3">
            {activeTab === "findings" && (
              <FindingsDashboard
                investigation={currentInvestigation}
                selectedFindingId={selectedFindingId}
                onSelectFinding={setSelectedFindingId}
                onFocusEvidence={handleFocusEvidence}
              />
            )}

            {activeTab === "evidence" && (
              <div className="space-y-3">
                <EvidenceGraph
                  evidenceCards={evidenceCards}
                  relationships={evidenceRelationships}
                  selectedEvidenceId={selectedEvidenceId}
                  onSelectEvidence={handleFocusEvidence}
                />

                {/* Filter pills */}
                <div className="flex items-center gap-1 text-[10px] font-mono overflow-x-auto pb-1">
                  <Filter className="w-3 h-3 text-slate-500" />
                  {["ALL", "CONFLICTS", "CHANGE", "SAR", "OPTICAL", "OBJECT", "SPECTRAL"].map((f) => (
                    <button
                      key={f}
                      onClick={() => setEvidenceFilter(f)}
                      className={`px-2 py-0.5 rounded transition-all shrink-0 ${
                        evidenceFilter === f
                          ? "bg-cyan-900 text-cyan-200 font-bold border border-cyan-700"
                          : "bg-slate-900 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>

                {/* Evidence Cards list */}
                <div className="space-y-2">
                  {filteredEvidenceCards.map((card) => (
                    <EvidenceCard
                      key={card.id}
                      evidence={card}
                      isSelected={card.id === selectedEvidenceId}
                      onSelect={handleFocusEvidence}
                    />
                  ))}
                </div>
              </div>
            )}

            {activeTab === "timeline" && (
              <InvestigationTimeline
                milestones={timeline}
                onSelectEvidence={handleFocusEvidence}
              />
            )}

            {activeTab === "objects" && (
              <ObjectTrackPanel
                onFocusTrack={(trk) => {
                  if (trk.track_id) handleFocusEvidence(trk.track_id)
                }}
              />
            )}

            {activeTab === "notes" && (
              <AnalystNotes
                notes={notes}
                onAddNote={addNote}
                onDeleteNote={deleteNote}
              />
            )}

            {activeTab === "provenance" && (
              <ProvenancePanel
                investigationId={currentInvestigation.investigation_id}
                artifacts={currentInvestigation.artifacts}
                processingHash={currentInvestigation.result_data?.artifacts?.find((a: any) => a.name === "investigation_manifest.json")?.processing_hash}
              />
            )}

            {activeTab === "history" && (
              <InvestigationHistory
                history={investigationHistory}
                activeInvestigationId={activeInvestigationId}
                onSelectInvestigation={loadInvestigation}
              />
            )}

            {/* Always visible legend at bottom of findings/evidence tabs */}
            {(activeTab === "findings" || activeTab === "evidence") && <SemanticLegend />}
          </div>
        </>
      )}

      {/* If no investigation selected yet, show history directly */}
      {!currentInvestigation && (
        <InvestigationHistory
          history={investigationHistory}
          activeInvestigationId={activeInvestigationId}
          onSelectInvestigation={loadInvestigation}
        />
      )}
    </div>
  )
}
