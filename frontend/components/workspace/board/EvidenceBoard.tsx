"use client"

import React, { useState } from "react"
import {
  Network,
  Plus,
  Link2,
  Trash2,
  Pin,
  ExternalLink,
  Tag,
} from "lucide-react"
import { EvidenceBoardItem, EvidenceBoardRelation } from "@/lib/explore/workspace-types"

interface EvidenceBoardProps {
  items: EvidenceBoardItem[]
  relations: EvidenceBoardRelation[]
  onPinItem: (item: Partial<EvidenceBoardItem>) => Promise<any>
  onDeleteItem: (itemId: string) => Promise<any>
  onLinkItems: (sourceId: string, targetId: string, relType: string) => Promise<any>
}

export function EvidenceBoard({
  items,
  relations,
  onPinItem,
  onDeleteItem,
  onLinkItems,
}: EvidenceBoardProps) {
  const [pinModalOpen, setPinModalOpen] = useState(false)
  const [linkModalOpen, setLinkModalOpen] = useState(false)
  const [itemType, setItemType] = useState("FINDING")
  const [sourceId, setSourceId] = useState("")
  const [title, setTitle] = useState("")
  const [annotation, setAnnotation] = useState("")

  const [linkSrc, setLinkSrc] = useState("")
  const [linkTgt, setLinkTgt] = useState("")
  const [linkType, setLinkType] = useState("supports")

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceId.trim() || !title.trim()) return
    await onPinItem({
      type: itemType,
      source_id: sourceId.trim(),
      title: title.trim(),
      annotation: annotation.trim(),
    })
    setSourceId("")
    setTitle("")
    setAnnotation("")
    setPinModalOpen(false)
  }

  const handleLinkSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!linkSrc || !linkTgt || linkSrc === linkTgt) return
    await onLinkItems(linkSrc, linkTgt, linkType)
    setLinkSrc("")
    setLinkTgt("")
    setLinkModalOpen(false)
  }

  const getBadgeColor = (type: string) => {
    switch (type) {
      case "FINDING":
        return "bg-amber-950/60 text-amber-400 border-amber-800/60"
      case "EVENT":
        return "bg-sky-950/60 text-sky-400 border-sky-800/60"
      case "OBSERVATION":
        return "bg-emerald-950/60 text-emerald-400 border-emerald-800/60"
      default:
        return "bg-purple-950/60 text-purple-400 border-purple-800/60"
    }
  }

  return (
    <div className="p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            <Network size={15} className="text-sky-400" /> Interactive Evidence Board
          </h3>
          <p className="text-[11px] text-slate-400">Assemble verified observations, findings & explicit relationships</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLinkModalOpen(true)}
            disabled={items.length < 2}
            className="flex items-center gap-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded transition disabled:opacity-50"
          >
            <Link2 size={13} /> Link
          </button>
          <button
            onClick={() => setPinModalOpen(true)}
            className="flex items-center gap-1 text-xs bg-sky-600 hover:bg-sky-500 text-white px-2.5 py-1 rounded transition"
          >
            <Plus size={13} /> Pin Item
          </button>
        </div>
      </div>

      {/* Evidence Cards Grid */}
      {items.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-8 text-center text-xs text-slate-500 space-y-2">
          <Pin size={24} className="mx-auto text-slate-600 mb-1" />
          <p>No items pinned to the evidence board yet.</p>
          <p className="text-[11px] text-slate-600">
            Pin findings, satellite scenes, or analyst notes to establish traceable grounding.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2.5">
          {items.map((item) => {
            const outRelations = relations.filter((r) => r.source_item_id === item.item_id)
            const inRelations = relations.filter((r) => r.target_item_id === item.item_id)

            return (
              <div
                key={item.item_id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2 relative group hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono border uppercase ${getBadgeColor(item.type)}`}>
                      {item.type}
                    </span>
                    <h4 className="text-xs font-semibold text-slate-100">{item.title}</h4>
                  </div>
                  <button
                    onClick={() => onDeleteItem(item.item_id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>

                {item.annotation && (
                  <p className="text-xs text-slate-400 bg-slate-950/60 border border-slate-800/40 rounded p-2">
                    {item.annotation}
                  </p>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                  <span>Source: {item.source_id}</span>
                  <div className="flex items-center gap-1.5">
                    {outRelations.map((r) => (
                      <span key={r.relation_id} className="text-sky-400 bg-sky-950/40 px-1.5 py-0.5 rounded">
                        &rarr; {r.relation_type}
                      </span>
                    ))}
                    {inRelations.map((r) => (
                      <span key={r.relation_id} className="text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded">
                        &larr; {r.relation_type}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pin Item Modal */}
      {pinModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handlePinSubmit}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <Pin size={15} className="text-sky-400" /> Pin Item to Evidence Board
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Entity Type</label>
              <select
                value={itemType}
                onChange={(e) => setItemType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="FINDING">Finding</option>
                <option value="EVENT">Event</option>
                <option value="OBSERVATION">Observation</option>
                <option value="NOTE">Analyst Note</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Source Entity ID</label>
              <input
                type="text"
                required
                placeholder="e.g. finding-101 or obs_sentinel2_01"
                value={sourceId}
                onChange={(e) => setSourceId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Card Title</label>
              <input
                type="text"
                required
                placeholder="Descriptive title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Annotation Note (Optional)</label>
              <textarea
                rows={2}
                placeholder="Analyst observation..."
                value={annotation}
                onChange={(e) => setAnnotation(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setPinModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium rounded"
              >
                Pin Item
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Link Items Modal */}
      {linkModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form
            onSubmit={handleLinkSubmit}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <Link2 size={15} className="text-sky-400" /> Link Board Items
            </h4>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Source Item</label>
              <select
                value={linkSrc}
                onChange={(e) => setLinkSrc(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="">Select source...</option>
                {items.map((i) => (
                  <option key={i.item_id} value={i.item_id}>
                    [{i.type}] {i.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Relationship Type</label>
              <select
                value={linkType}
                onChange={(e) => setLinkType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="supports">supports</option>
                <option value="contradicts">contradicts</option>
                <option value="related_to">related_to</option>
                <option value="follow_up">follow_up</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Target Item</label>
              <select
                value={linkTgt}
                onChange={(e) => setLinkTgt(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="">Select target...</option>
                {items.filter((i) => i.item_id !== linkSrc).map((i) => (
                  <option key={i.item_id} value={i.item_id}>
                    [{i.type}] {i.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setLinkModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium rounded"
              >
                Create Relationship
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
