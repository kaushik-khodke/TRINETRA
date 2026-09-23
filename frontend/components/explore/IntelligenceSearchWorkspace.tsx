"use client"

/**
 * TRINETRA Phase 7 — Intelligence Semantic Search & Similarity Workspace
 * Search interface for natural-language spatial, temporal, semantic and modality queries,
 * paired with mathematical similarity scoring.
 */

import React, { useState } from "react"
import {
  IntelligenceSearchResultItem,
  SimilarityResultItem,
} from "@/lib/explore/intelligence-types"
import {
  Search,
  Sparkles,
  MapPin,
  ShieldCheck,
  Zap,
  Tag,
  Share2,
  X,
  Compass,
} from "lucide-react"

interface Props {
  searchQuery: string
  onQueryChange: (query: string) => void
  onExecuteSearch: (query?: string) => void
  results: IntelligenceSearchResultItem[]
  totalResults: number
  isLoading: boolean
  similarItems: SimilarityResultItem[]
  isSimilarLoading: boolean
  onFindSimilar: (entityId: string, entityType?: "finding" | "event") => void
  onFocusOnMap: (bbox: number[]) => void
}

const EXAMPLE_QUERIES = [
  "Show persistent built-up changes",
  "Vegetation loss with high confidence",
  "Water body expansion",
  "Optical and SAR agreement",
]

export const IntelligenceSearchWorkspace: React.FC<Props> = ({
  searchQuery,
  onQueryChange,
  onExecuteSearch,
  results,
  totalResults,
  isLoading,
  similarItems,
  isSimilarLoading,
  onFindSimilar,
  onFocusOnMap,
}) => {
  const [activeSimilarSourceId, setActiveSimilarSourceId] = useState<string | null>(null)

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onExecuteSearch()
  }

  const handleExampleClick = (query: string) => {
    onQueryChange(query)
    onExecuteSearch(query)
  }

  const handleTriggerSimilar = (entityId: string, entityType: "finding" | "event") => {
    setActiveSimilarSourceId(entityId)
    onFindSimilar(entityId, entityType)
  }

  return (
    <div className="flex flex-col gap-3 font-mono text-xs">
      {/* Search Input Form */}
      <form onSubmit={handleSearchSubmit} className="space-y-2">
        <div className="relative">
          <input
            type="text"
            placeholder="Search EO intelligence (e.g. 'vegetation loss in AOI')..."
            value={searchQuery}
            onChange={(e) => onQueryChange(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-8 pr-16 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-orange-500"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
          <button
            type="submit"
            disabled={isLoading}
            className="absolute right-1.5 top-1.5 px-2.5 py-1 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-slate-950 font-bold rounded text-[10px] transition-colors"
          >
            {isLoading ? "..." : "Search"}
          </button>
        </div>

        {/* Example Query Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-0.5">
          <span className="text-[10px] text-slate-500 shrink-0">Try:</span>
          {EXAMPLE_QUERIES.map((eq) => (
            <button
              key={eq}
              type="button"
              onClick={() => handleExampleClick(eq)}
              className="text-[10px] whitespace-nowrap bg-slate-900 hover:bg-slate-800 border border-slate-800 text-orange-400/90 px-2 py-0.5 rounded-full transition-colors"
            >
              {eq}
            </button>
          ))}
        </div>
      </form>

      {/* Results Header */}
      {totalResults > 0 && (
        <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>
            Found <strong className="text-orange-300">{totalResults}</strong> matching entities
          </span>
          <span className="text-[10px] text-slate-500">Ranked by relevance</span>
        </div>
      )}

      {/* Similar Entities Drawer (if triggered) */}
      {activeSimilarSourceId && (
        <div className="p-2.5 bg-slate-950 border border-indigo-800/80 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-[11px] font-bold text-indigo-300">
              <Share2 className="w-3.5 h-3.5" />
              <span>Similar EO Entities ({similarItems.length})</span>
            </div>
            <button
              onClick={() => setActiveSimilarSourceId(null)}
              className="text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="text-[10px] text-slate-400">
            Source entity: <code className="text-indigo-300">{activeSimilarSourceId}</code>
          </div>

          {isSimilarLoading ? (
            <div className="text-center py-3 text-[10px] text-indigo-400 animate-pulse">
              Computing multi-feature similarity...
            </div>
          ) : similarItems.length === 0 ? (
            <div className="text-[10px] text-slate-500 italic py-2">
              No entities exceeding similarity threshold.
            </div>
          ) : (
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {similarItems.map((item) => (
                <div
                  key={item.id}
                  className="p-1.5 bg-slate-900/80 border border-slate-800 rounded flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="text-[10px] font-semibold text-slate-200">{item.title}</div>
                    <div className="flex items-center gap-1.5 text-[9px] text-slate-400">
                      <span className="text-indigo-400">{item.semantic_class}</span>
                      <span>•</span>
                      <span className="text-emerald-400">{(item.score * 100).toFixed(0)}% match</span>
                    </div>
                  </div>
                  {item.bounding_box && (
                    <button
                      onClick={() => onFocusOnMap(item.bounding_box)}
                      title="Fly to match"
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-orange-300"
                    >
                      <Compass className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Results List */}
      <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
        {results.length === 0 && !isLoading && (
          <div className="text-center py-8 text-slate-500 text-xs">
            <Sparkles className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>Type a query to search canonical events & findings.</p>
          </div>
        )}

        {results.map((item) => (
          <div
            key={item.id}
            className="p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg hover:border-slate-700 transition-all space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 font-bold">
                    {item.type}
                  </span>
                  <span className="text-[9px] text-orange-400 bg-orange-950/60 border border-orange-800/60 px-1 py-0.5 rounded">
                    {item.semantic_class}
                  </span>
                  <span className="text-[9px] text-emerald-400 font-bold">
                    Score: {(item.score * 100).toFixed(0)}
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200">{item.title}</h4>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 shrink-0">
                {item.bounding_box && (
                  <button
                    onClick={() => onFocusOnMap(item.bounding_box)}
                    title="Center on Map"
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-orange-300 transition-colors"
                  >
                    <MapPin className="w-3 h-3" />
                  </button>
                )}
                <button
                  onClick={() =>
                    handleTriggerSimilar(item.id, item.type === "event" ? "event" : "finding")
                  }
                  title="Find Similar Entities"
                  className="p-1.5 rounded bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/60 text-indigo-300 transition-colors"
                >
                  <Share2 className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Match Reasons */}
            {item.match_reasons && item.match_reasons.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {item.match_reasons.map((reason, idx) => (
                  <span
                    key={idx}
                    className="text-[9px] bg-slate-900 text-slate-400 border border-slate-800/80 px-1.5 py-0.5 rounded"
                  >
                    {reason}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
