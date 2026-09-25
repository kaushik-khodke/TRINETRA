"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Copernicus-Style Multi-Spectral Presets Bar
 * Phase 4 / ISRO Advanced Earth Observation Features
 */

import React, { useState } from "react"
import { SPECTRAL_PRESETS, SpectralPreset } from "@/lib/explore/spectral-presets"
import { useGlobeState, globeState } from "@/lib/explore/globe-state"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { Info, Sparkles, Layers, Sliders, Check, ChevronDown } from "lucide-react"

export const SpectralPresetBar: React.FC = () => {
  const { activeBasemap } = useGlobeState()
  const [showInfo, setShowInfo] = useState<boolean>(false)

  // Current active preset (default to satellite / True Color)
  const currentPreset =
    SPECTRAL_PRESETS.find((p) => p.id === activeBasemap) || SPECTRAL_PRESETS[0]

  const handleSelectPreset = (preset: SpectralPreset) => {
    globeState.setActiveBasemap(preset.id)
    globeCommandBus.dispatch({
      type: "SET_BASEMAP",
      basemapId: preset.id,
      tileUrl: preset.tileUrl,
      label: preset.label,
    })
  }

  return (
    <div className="relative flex items-center" style={{ zIndex: 30 }}>
      {/* Main Floating Glass Bar */}
      <div className="flex items-center gap-1.5 bg-[#121620]/90 backdrop-blur-md border border-white/10 rounded-lg px-2.5 py-1.5 shadow-xl text-xs">
        {/* Header Icon / Title */}
        <div className="flex items-center gap-1.5 mr-1 pr-2 border-r border-white/10 text-slate-400">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-300 hidden sm:inline">
            Spectra
          </span>
        </div>

        {/* Preset Buttons */}
        <div className="flex items-center gap-1">
          {SPECTRAL_PRESETS.map((preset) => {
            const isActive = currentPreset.id === preset.id

            return (
              <button
                key={preset.id}
                onClick={() => handleSelectPreset(preset)}
                className={`px-2 py-1 rounded transition-all font-mono text-[11px] flex items-center gap-1.5 ${
                  isActive
                    ? "font-semibold shadow-md"
                    : "text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/5"
                }`}
                style={
                  isActive
                    ? {
                        backgroundColor: `${preset.colorAccent}25`,
                        color: preset.colorAccent,
                        borderColor: preset.colorAccent,
                        borderWidth: "1px",
                        boxShadow: `0 0 10px ${preset.colorAccent}30`,
                      }
                    : {}
                }
                title={`${preset.label} (${preset.bands})`}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: preset.colorAccent }}
                />
                <span>{preset.shortLabel}</span>
              </button>
            )
          })}
        </div>

        {/* Info & Scientific Details Toggle Button */}
        <button
          onClick={() => setShowInfo(!showInfo)}
          className={`ml-1 p-1 rounded transition border ${
            showInfo
              ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
              : "bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 border-white/10"
          }`}
          title="View Spectral Band Formula & Scientific Significance"
        >
          <Info className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Expandable Scientific Details & Legend Popover */}
      {showInfo && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-[#10141e]/98 backdrop-blur-xl border border-cyan-500/30 rounded-xl p-3 shadow-2xl space-y-2.5 text-xs text-slate-300 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <div className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-full animate-pulse"
                style={{ backgroundColor: currentPreset.colorAccent }}
              />
              <span className="font-bold text-white font-mono text-xs">
                {currentPreset.label}
              </span>
            </div>
            <span
              className="text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold uppercase tracking-wider"
              style={{
                backgroundColor: `${currentPreset.colorAccent}20`,
                color: currentPreset.colorAccent,
              }}
            >
              {currentPreset.badgeText}
            </span>
          </div>

          {/* Band Math & Formula */}
          <div className="bg-slate-900/80 rounded-lg p-2 border border-white/5 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider font-semibold">
              Spectral Bands / Formula
            </span>
            <div className="font-mono text-[11px] text-cyan-300 font-medium">
              {currentPreset.bands}
            </div>
          </div>

          {/* Scientific Description */}
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {currentPreset.description}
          </p>

          {/* Scientific Legend if defined */}
          {currentPreset.legend && (
            <div className="space-y-1.5 pt-1 border-t border-white/10">
              <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider font-semibold">
                Interpretation Gradient
              </span>
              <div
                className="w-full h-2 rounded-full"
                style={{
                  background: `linear-gradient(to right, ${currentPreset.legend.lowColor}, ${currentPreset.legend.highColor})`,
                }}
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>{currentPreset.legend.low}</span>
                <span>{currentPreset.legend.high}</span>
              </div>
              <div className="text-[10px] text-slate-400 italic">
                {currentPreset.legend.description}
              </div>
            </div>
          )}

          {/* Attribution */}
          <div className="text-[9px] text-slate-500 font-mono border-t border-white/10 pt-1.5">
            {currentPreset.attribution}
          </div>
        </div>
      )}
    </div>
  )
}
