/**
 * TRINETRA Phase 6 — Analyst Annotations & Notes Workspace
 * Enables human analysts to attach observations, field verification notes,
 * and comments to investigations or specific finding IDs.
 */

import React, { useState } from "react"
import { AnalystNote } from "@/lib/explore/investigation-types"
import { StickyNote, Send, Trash2, Tag, Clock, User } from "lucide-react"

interface Props {
  notes: AnalystNote[]
  onAddNote: (text: string, attachmentType?: string, attachmentId?: string) => Promise<void>
  onDeleteNote: (noteId: string) => Promise<void>
}

export const AnalystNotes: React.FC<Props> = ({ notes, onAddNote, onDeleteNote }) => {
  const [noteText, setNoteText] = useState("")
  const [tagId, setTagId] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!noteText.trim()) return
    setIsSubmitting(true)
    try {
      await onAddNote(noteText.trim(), tagId.trim() ? "finding" : undefined, tagId.trim() || undefined)
      setNoteText("")
      setTagId("")
    } catch (err) {
      console.error(err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* Input composer */}
      <form onSubmit={handleSubmit} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-2">
        <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold">
          <StickyNote className="w-3.5 h-3.5 text-orange-400" />
          <span>Add Analyst Note / Ground Truth Annotation</span>
        </div>

        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          placeholder="Record human analyst observations, field notes, or ground-truth verification..."
          rows={2}
          className="w-full bg-slate-950/80 border border-slate-800 rounded p-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-orange-500 resize-none font-sans"
        />

        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 flex-1 max-w-[200px]">
            <Tag className="w-3 h-3 text-slate-500 shrink-0" />
            <input
              type="text"
              value={tagId}
              onChange={(e) => setTagId(e.target.value)}
              placeholder="Tag Finding/Evidence ID (optional)"
              className="w-full bg-slate-950/80 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-300 placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>

          <button
            type="submit"
            disabled={!noteText.trim() || isSubmitting}
            className="inline-flex items-center gap-1 px-3 py-1 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-slate-950 font-bold rounded text-xs transition-colors"
          >
            <span>Save</span>
            <Send className="w-3 h-3" />
          </button>
        </div>
      </form>

      {/* Notes list */}
      <div className="space-y-2">
        {notes.length === 0 ? (
          <div className="text-center py-4 text-xs text-slate-500 font-mono">
            No analyst notes attached to this investigation.
          </div>
        ) : (
          notes.map((n, idx) => (
            <div
              key={n.note_id || idx}
              className="p-3 rounded bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs text-slate-300"
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3 text-orange-400" />
                  Analyst Annotation
                </span>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {(n.created_at || "").slice(0, 16).replace("T", " ")}
                  </span>
                  {n.note_id && (
                    <button
                      onClick={() => onDeleteNote(n.note_id!)}
                      className="text-slate-500 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>

              <p className="text-slate-200 leading-relaxed font-sans">{n.text}</p>

              {n.attachment_id && (
                <div className="pt-1 flex items-center gap-1 text-[10px] font-mono text-orange-400">
                  <Tag className="w-2.5 h-2.5" />
                  <span>Bound to: {n.attachment_id}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
