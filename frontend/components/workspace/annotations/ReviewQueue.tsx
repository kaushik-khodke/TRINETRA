"use client"

import React, { useState } from "react"
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Plus,
  ListTodo,
  CheckSquare,
} from "lucide-react"
import { ReviewRecord, ReviewStatus, FollowUp } from "@/lib/explore/workspace-types"

interface ReviewQueueProps {
  reviews: ReviewRecord[]
  followUps: FollowUp[]
  onSetReviewStatus: (type: string, id: string, status: ReviewStatus, note?: string) => Promise<any>
  onCreateFollowUp: (type: string, id: string, note: string) => Promise<any>
}

export function ReviewQueue({
  reviews,
  followUps,
  onSetReviewStatus,
  onCreateFollowUp,
}: ReviewQueueProps) {
  const [filter, setFilter] = useState<string>("ALL")
  const [followUpModal, setFollowUpModal] = useState(false)
  const [fuType, setFuType] = useState("FINDING")
  const [fuId, setFuId] = useState("")
  const [fuNote, setFuNote] = useState("")

  const filteredReviews = filter === "ALL" ? reviews : reviews.filter((r) => r.status === filter)

  const handleFollowUpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!fuId.trim() || !fuNote.trim()) return
    await onCreateFollowUp(fuType, fuId.trim(), fuNote.trim())
    setFuId("")
    setFuNote("")
    setFollowUpModal(false)
  }

  return (
    <div className="p-4 space-y-5 text-slate-200">
      {/* Reviews Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <CheckCircle2 size={15} className="text-amber-400" /> Analyst Verification & Review Queue
            </h3>
            <p className="text-[11px] text-slate-400">Audit status tracking for persistent findings and events</p>
          </div>

          <div className="flex gap-1 text-[11px] bg-slate-900 border border-slate-800 p-0.5 rounded">
            {["ALL", "UNREVIEWED", "REVIEWED", "NEEDS_FOLLOWUP"].map((st) => (
              <button
                key={st}
                onClick={() => setFilter(st)}
                className={`px-2 py-0.5 rounded transition ${
                  filter === st ? "bg-slate-800 text-sky-400 font-medium" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          {filteredReviews.length === 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-6 text-center text-xs text-slate-500">
              No items matching the "{filter}" review filter.
            </div>
          ) : (
            filteredReviews.map((rev) => (
              <div
                key={rev.review_id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 font-mono uppercase bg-slate-800 px-1.5 py-0.5 rounded">
                      {rev.entity_type}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">{rev.entity_id}</span>
                  </div>
                  {rev.review_note && (
                    <p className="text-[11px] text-slate-400 pl-1">{rev.review_note}</p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={rev.status}
                    onChange={(e) =>
                      onSetReviewStatus(
                        rev.entity_type,
                        rev.entity_id,
                        e.target.value as ReviewStatus,
                        rev.review_note
                      )
                    }
                    className={`text-xs px-2 py-1 rounded font-mono uppercase border outline-none ${
                      rev.status === "REVIEWED"
                        ? "bg-emerald-950/60 text-emerald-400 border-emerald-800/60"
                        : rev.status === "NEEDS_FOLLOWUP"
                        ? "bg-amber-950/60 text-amber-400 border-amber-800/60"
                        : "bg-slate-800 text-slate-300 border-slate-700"
                    }`}
                  >
                    <option value="UNREVIEWED">UNREVIEWED</option>
                    <option value="REVIEWED">REVIEWED</option>
                    <option value="NEEDS_FOLLOWUP">NEEDS_FOLLOWUP</option>
                    <option value="RESOLVED_BY_ANALYST">RESOLVED_BY_ANALYST</option>
                  </select>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Follow-ups Section */}
      <div className="space-y-3 pt-2 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 font-mono uppercase">
            <ListTodo size={14} className="text-sky-400" /> Analyst Follow-Up Queue ({followUps.length})
          </div>
          <button
            onClick={() => setFollowUpModal(true)}
            className="flex items-center gap-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-200 px-2 py-0.5 rounded transition"
          >
            <Plus size={11} /> Add Follow-up
          </button>
        </div>

        <div className="space-y-1.5">
          {followUps.length === 0 ? (
            <div className="bg-slate-900/40 border border-slate-800/60 rounded-lg p-4 text-center text-xs text-slate-500">
              No follow-up items pending.
            </div>
          ) : (
            followUps.map((fu) => (
              <div
                key={fu.follow_up_id}
                className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase mr-2">
                    [{fu.linked_entity_type}: {fu.linked_entity_id}]
                  </span>
                  <span className="text-slate-200">{fu.note}</span>
                </div>
                <span className="text-[10px] text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded font-mono">
                  {fu.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Follow-up Modal */}
      {followUpModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleFollowUpSubmit}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <Plus size={15} className="text-sky-400" /> Create Follow-Up Action
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Target Entity Type</label>
              <select
                value={fuType}
                onChange={(e) => setFuType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="FINDING">Finding</option>
                <option value="EVENT">Event</option>
                <option value="REGION">Region</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Target Entity ID</label>
              <input
                type="text"
                required
                placeholder="e.g. find-101"
                value={fuId}
                onChange={(e) => setFuId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Action Required / Question</label>
              <textarea
                rows={2}
                required
                placeholder="e.g. Re-evaluate with high-res optical pass"
                value={fuNote}
                onChange={(e) => setFuNote(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setFollowUpModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium rounded"
              >
                Create Task
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
