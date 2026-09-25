import dynamic from "next/dynamic"

const ExploreShell = dynamic(
  () => import("@/components/explore/ExploreShell").then((mod) => mod.ExploreShell),
  {
    ssr: false,
    loading: () => (
      <div className="w-screen h-screen bg-[#030712] flex items-center justify-center text-slate-400 font-mono text-xs select-none">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-ping" />
          <span className="tracking-wider uppercase">INITIALIZING SHANETRA EXPLORE WORKSTATION...</span>
        </div>
      </div>
    ),
  }
)

/**
 * TRINETRA / Shanetra Explore Route Entry Point
 * Phase 1 Foundation
 */
export default function ExplorePage() {
  return <ExploreShell />
}
