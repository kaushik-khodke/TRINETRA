/**
 * TRINETRA Phase 6 — Investigation State Manager (React Hook)
 * Coordinates polling, active selection, evidence inspection, and analyst notes.
 */

import { useState, useEffect, useRef, useCallback } from "react"
import {
  InvestigationItem,
  InvestigationRequest,
  InvestigationValidationResponse,
  EvidenceCardData,
  StructuredFindingData,
  TimelineMilestone,
  AnalystNote,
} from "./investigation-types"
import { investigationApi } from "./investigation-api"

export function useInvestigationState() {
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null)
  const [currentInvestigation, setCurrentInvestigation] = useState<InvestigationItem | null>(null)
  const [investigationHistory, setInvestigationHistory] = useState<any[]>([])
  const [evidenceCards, setEvidenceCards] = useState<EvidenceCardData[]>([])
  const [evidenceRelationships, setEvidenceRelationships] = useState<any[]>([])
  const [evidenceConflicts, setEvidenceConflicts] = useState<any[]>([])
  const [findings, setFindings] = useState<StructuredFindingData[]>([])
  const [timeline, setTimeline] = useState<TimelineMilestone[]>([])
  const [notes, setNotes] = useState<AnalystNote[]>([])
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null)
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null)
  const [validation, setValidation] = useState<InvestigationValidationResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Refresh investigation history
  const refreshHistory = useCallback(async () => {
    try {
      const history = await investigationApi.listInvestigations(20)
      setInvestigationHistory(history)
    } catch (e) {
      console.warn("Failed to load investigation history", e)
    }
  }, [])

  useEffect(() => {
    refreshHistory()
  }, [refreshHistory])

  // Poll active investigation status
  useEffect(() => {
    if (!activeInvestigationId) return

    let isMounted = true

    const poll = async () => {
      try {
        const details = await investigationApi.getInvestigationDetails(activeInvestigationId)
        if (!isMounted) return

        setCurrentInvestigation(details)
        if (details.findings) setFindings(details.findings)

        if (details.status === "completed") {
          // Fetch evidence, timeline, notes
          try {
            const evData = await investigationApi.getInvestigationEvidence(activeInvestigationId)
            if (isMounted) {
              setEvidenceCards(evData.evidence_cards || [])
              setEvidenceRelationships(evData.relationships || [])
              setEvidenceConflicts(evData.conflicts || [])
            }
          } catch (err) {
            console.warn("Could not fetch evidence cards:", err)
          }

          try {
            const timeData = await investigationApi.getInvestigationTimeline(activeInvestigationId)
            if (isMounted) setTimeline(timeData.milestones || [])
          } catch (err) {
            console.warn("Could not fetch timeline:", err)
          }

          try {
            const notesData = await investigationApi.getAnalystNotes(activeInvestigationId)
            if (isMounted) setNotes(notesData)
          } catch (err) {
            console.warn("Could not fetch notes:", err)
          }

          refreshHistory()
        } else if (details.status === "running" || details.status === "queued") {
          pollingTimerRef.current = setTimeout(poll, 1500)
        }
      } catch (err: any) {
        if (isMounted) setError(err.message || "Polling error")
      }
    }

    poll()

    return () => {
      isMounted = false
      if (pollingTimerRef.current) clearTimeout(pollingTimerRef.current)
    }
  }, [activeInvestigationId, refreshHistory])

  // Actions
  const startInvestigation = async (req: InvestigationRequest) => {
    setIsSubmitting(true)
    setError(null)
    try {
      const res = await investigationApi.startInvestigation(req)
      setActiveInvestigationId(res.investigation_id)
      setSelectedEvidenceId(null)
      setSelectedFindingId(null)
      await refreshHistory()
      return res.investigation_id
    } catch (err: any) {
      setError(err.message || "Failed to launch investigation.")
      throw err
    } finally {
      setIsSubmitting(false)
    }
  }

  const cancelInvestigation = async () => {
    if (!activeInvestigationId) return
    try {
      await investigationApi.cancelInvestigation(activeInvestigationId)
      if (currentInvestigation) {
        setCurrentInvestigation({
          ...currentInvestigation,
          status: "cancelled",
        })
      }
      refreshHistory()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const loadInvestigation = (id: string) => {
    setActiveInvestigationId(id)
    setSelectedEvidenceId(null)
    setSelectedFindingId(null)
  }

  const validateEnquiry = async (req: InvestigationRequest) => {
    try {
      const res = await investigationApi.validateInvestigation(req)
      setValidation(res)
      return res
    } catch (err) {
      console.warn("Validation failed", err)
      return null
    }
  }

  const addNote = async (text: string, attachmentType?: string, attachmentId?: string) => {
    if (!activeInvestigationId) return
    const newNote: AnalystNote = {
      investigation_id: activeInvestigationId,
      text,
      attachment_type: attachmentType,
      attachment_id: attachmentId,
    }
    try {
      const created = await investigationApi.createAnalystNote(activeInvestigationId, newNote)
      setNotes((prev) => [...prev, created])
    } catch (err: any) {
      setError(err.message)
    }
  }

  const deleteNote = async (noteId: string) => {
    if (!activeInvestigationId) return
    try {
      await investigationApi.deleteAnalystNote(activeInvestigationId, noteId)
      setNotes((prev) => prev.filter((n) => n.note_id !== noteId))
    } catch (err: any) {
      setError(err.message)
    }
  }

  return {
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
    refreshHistory,
  }
}
