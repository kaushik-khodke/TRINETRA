"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import { Activity, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react"

export default function AuthCallbackPage() {
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing")
  const [message, setMessage] = useState("Establishing secure mission clearance...")

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Exchange session / verify tokens in URL
        const { data, error } = await supabase.auth.getSession()
        if (error) throw error

        if (data.session) {
          setStatus("success")
          setMessage("Authentication verified. Redirecting to workspace...")
          setTimeout(() => {
            window.location.href = "/analysis"
          }, 800)
        } else {
          // If hash tokens or code are still resolving
          const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
            if (session) {
              setStatus("success")
              setMessage("Authentication verified. Redirecting to workspace...")
              setTimeout(() => {
                window.location.href = "/analysis"
              }, 800)
            }
          })

          // Timeout fallback
          setTimeout(() => {
            if (status === "processing") {
              window.location.href = "/analysis"
            }
          }, 2500)
        }
      } catch (err: any) {
        console.error("[AuthCallback] Error:", err)
        setStatus("error")
        setMessage(err.message || "Failed to finalize authentication session.")
      }
    }

    handleAuthCallback()
  }, [])

  return (
    <main className="page" style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <div
        style={{
          maxWidth: "440px",
          width: "100%",
          padding: "2.5rem 2rem",
          background: "rgba(10, 20, 26, 0.85)",
          border: "1px solid rgba(86, 215, 223, 0.25)",
          borderRadius: "16px",
          boxShadow: "0 0 50px rgba(86, 215, 223, 0.12)",
          textAlign: "center",
          backdropFilter: "blur(18px)",
        }}
      >
        <div style={{ marginBottom: "1.5rem" }}>
          {status === "processing" && (
            <div
              style={{
                width: "56px",
                height: "56px",
                margin: "0 auto",
                borderRadius: "50%",
                border: "2px solid rgba(86, 215, 223, 0.2)",
                borderTopColor: "var(--cyan-400, #00f0ff)",
                display: "grid",
                placeItems: "center",
                animation: "spin 1s linear infinite",
              }}
            >
              <Activity size={24} color="#00f0ff" />
            </div>
          )}
          {status === "success" && (
            <div
              style={{
                width: "56px",
                height: "56px",
                margin: "0 auto",
                borderRadius: "50%",
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid #10b981",
                display: "grid",
                placeItems: "center",
              }}
            >
              <CheckCircle2 size={28} color="#10b981" />
            </div>
          )}
          {status === "error" && (
            <div
              style={{
                width: "56px",
                height: "56px",
                margin: "0 auto",
                borderRadius: "50%",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                display: "grid",
                placeItems: "center",
              }}
            >
              <AlertTriangle size={28} color="#ef4444" />
            </div>
          )}
        </div>

        <span
          style={{
            fontFamily: "monospace",
            fontSize: "0.72rem",
            letterSpacing: "0.14em",
            color: "var(--cyan-400, #00f0ff)",
            textTransform: "uppercase",
          }}
        >
          TRINETRA AI Security Clearance
        </span>

        <h2 style={{ fontSize: "1.35rem", margin: "0.5rem 0 0.75rem", color: "#f1f5f9" }}>
          {status === "processing"
            ? "Authenticating Session"
            : status === "success"
            ? "Mission Clearance Granted"
            : "Authentication Notice"}
        </h2>

        <p style={{ fontSize: "0.85rem", color: "rgba(255, 255, 255, 0.6)", lineHeight: 1.5, margin: "0 0 1.5rem" }}>
          {message}
        </p>

        {status === "error" && (
          <button
            className="primary"
            onClick={() => (window.location.href = "/analysis")}
            style={{ width: "100%", padding: "0.75rem", fontSize: "0.85rem" }}
          >
            Return to Workspace <ArrowRight size={16} />
          </button>
        )}
      </div>
    </main>
  )
}
