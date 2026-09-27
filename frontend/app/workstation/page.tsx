import { Metadata } from "next"
import { WorkstationShell } from "@/components/workstation/WorkstationShell"

export const metadata: Metadata = {
  title: "Scientific Research Workstation • TRINETRA",
  description:
    "Enterprise-grade multimodal Earth Observation research workstation. Mission-centered, query-first geospatial intelligence with human-in-the-loop plan approval and verifiable scientific provenance.",
}

export default function WorkstationPage() {
  return <WorkstationShell />
}
