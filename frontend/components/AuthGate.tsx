"use client"

import React, { useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { ShieldCheck, ArrowRight, Sparkles, Mail, AlertTriangle, CheckCircle2, Lock, Radar } from "lucide-react"

export function GoogleLogo() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
      />
    </svg>
  )
}

export default function AuthGate() {
  const { signInWithGoogle, signInWithEmail, bypassForDemo } = useAuth()
  const [emailInput, setEmailInput] = useState("")
  const [emailSent, setEmailSent] = useState(false)
  const [loadingGoogle, setLoadingGoogle] = useState(false)
  const [loadingEmail, setLoadingEmail] = useState(false)
  const [showEmailForm, setShowEmailForm] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleGoogleLogin = async () => {
    setLoadingGoogle(true)
    setErrorMessage(null)
    try {
      await signInWithGoogle()
    } catch (err: any) {
      console.error("[AuthGate] Google login failed:", err)
      if (err?.message?.includes("provider is not enabled")) {
        setErrorMessage(
          "Google OAuth provider is currently toggled OFF in your Supabase project dashboard. Go to Supabase Dashboard -> Authentication -> Providers -> Google -> Toggle Enabled -> Save."
        )
      } else {
        setErrorMessage(err.message || "Failed to initialize Google authentication.")
      }
      setLoadingGoogle(false)
    }
  }

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!emailInput.trim()) return
    setLoadingEmail(true)
    setErrorMessage(null)
    try {
      await signInWithEmail(emailInput.trim())
      setEmailSent(true)
    } catch (err: any) {
      console.error("[AuthGate] Email login failed:", err)
      setErrorMessage(err.message || "Failed to send magic authentication link.")
    } finally {
      setLoadingEmail(false)
    }
  }

  return (
    <div
      style={{
        width: "100%",
        minHeight: "75vh",
        display: "grid",
        placeItems: "center",
        padding: "2rem 1rem",
        position: "relative",
      }}
    >
      {/* Background glow orb */}
      <div
        style={{
          position: "absolute",
          width: "480px",
          height: "480px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(86, 215, 223, 0.12) 0%, rgba(8, 16, 22, 0) 70%)",
          filter: "blur(40px)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      <div
        style={{
          maxWidth: "480px",
          width: "100%",
          background: "rgba(28, 29, 28, 0.85)",
          border: "1px solid var(--line)",
          borderRadius: "4px",
          boxShadow: "0 16px 48px rgba(0, 0, 0, 0.55)",
          padding: "2.75rem 2.25rem",
          position: "relative",
          zIndex: 1,
          backdropFilter: "blur(24px)",
        }}
      >
        {/* Top Tag & Security Badge */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 10px",
              borderRadius: "2px",
              background: "rgba(199, 92, 64, 0.08)",
              border: "1px solid rgba(199, 92, 64, 0.35)",
              color: "var(--warm)",
              fontFamily: "monospace",
              fontSize: "0.72rem",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
            }}
          >
            <Lock size={12} /> RESTRICTED INTELLIGENCE CLEARANCE
          </span>
          <span
            style={{
              fontFamily: "monospace",
              fontSize: "0.68rem",
              color: "rgba(222, 221, 211, 0.4)",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
            }}
          >
            ISRO EO-PS26167
          </span>
        </div>

        {/* Branding & Mission Title */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              margin: "0 auto 1.25rem",
              borderRadius: "4px",
              background: "rgba(199, 92, 64, 0.12)",
              border: "1px solid var(--acid)",
              display: "grid",
              placeItems: "center",
              color: "var(--acid)",
              boxShadow: "0 0 25px rgba(199, 92, 64, 0.25)",
            }}
          >
            <Radar size={28} />
          </div>
          <h2
            style={{
              fontSize: "1.85rem",
              fontWeight: 600,
              letterSpacing: "-0.04em",
              color: "#fffdf6",
              margin: "0 0 0.5rem",
            }}
          >
            Sign in to <span style={{ color: "var(--acid)" }}>TRI•NETRA</span>
          </h2>
          <p
            style={{
              fontSize: "0.88rem",
              color: "var(--muted-ink)",
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            Authenticate your credentials to access the multimodal Earth observation reasoning workspace and 3D globe telemetry.
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              color: "#fca5a5",
              padding: "0.85rem 1rem",
              borderRadius: "10px",
              marginBottom: "1.5rem",
              fontSize: "0.8rem",
              lineHeight: 1.45,
              display: "flex",
              alignItems: "flex-start",
              gap: "0.75rem",
            }}
          >
            <AlertTriangle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: "2px" }} />
            <div>
              <strong style={{ color: "#f87171", display: "block", marginBottom: "3px" }}>Authentication Notice</strong>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Primary Action: Sign in with Google */}
        <button
          type="button"
          id="google-signin-btn"
          disabled={loadingGoogle}
          onClick={handleGoogleLogin}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.85rem",
            padding: "0.95rem 1.25rem",
            borderRadius: "2px",
            background: "#ffffff",
            color: "#1f2937",
            border: "none",
            fontSize: "0.95rem",
            fontWeight: 600,
            cursor: loadingGoogle ? "wait" : "pointer",
            boxShadow: "0 4px 18px rgba(0, 0, 0, 0.35)",
            transition: "all 0.15s ease",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)"
            e.currentTarget.style.boxShadow = "0 6px 24px rgba(255, 255, 255, 0.25)"
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "none"
            e.currentTarget.style.boxShadow = "0 4px 18px rgba(0, 0, 0, 0.35)"
          }}
        >
          <GoogleLogo />
          <span>{loadingGoogle ? "Connecting to Google..." : "Continue with Google"}</span>
        </button>

        {/* Divider */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            margin: "1.5rem 0",
            color: "rgba(222, 221, 211, 0.3)",
            fontFamily: "monospace",
            fontSize: "0.72rem",
            letterSpacing: "0.1em",
          }}
        >
          <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
          <span>OR SIGN IN WITH EMAIL</span>
          <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
        </div>

        {/* Email Magic Link Accordion */}
        {!showEmailForm ? (
          <button
            type="button"
            onClick={() => setShowEmailForm(true)}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.6rem",
              padding: "0.75rem 1rem",
              borderRadius: "2px",
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--line)",
              color: "var(--ink)",
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all 0.15s",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.07)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)")}
          >
            <Mail size={15} /> Use Magic Link / Email <ArrowRight size={14} />
          </button>
        ) : emailSent ? (
          <div
            style={{
              padding: "1rem",
              borderRadius: "2px",
              background: "rgba(16, 185, 129, 0.1)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              color: "#a7f3d0",
              textAlign: "center",
              fontSize: "0.85rem",
            }}
          >
            <CheckCircle2 size={24} color="#10b981" style={{ margin: "0 auto 0.5rem" }} />
            <strong>Magic link dispatched!</strong>
            <p style={{ margin: "0.35rem 0 0", color: "var(--muted-ink)", fontSize: "0.78rem" }}>
              Check your inbox for <b>{emailInput}</b> to complete authentication.
            </p>
          </div>
        ) : (
          <form onSubmit={handleEmailLogin} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <input
              type="email"
              placeholder="operator@organization.gov"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "2px",
                background: "rgba(15, 16, 15, 0.85)",
                border: "1px solid var(--line)",
                color: "var(--ink)",
                fontSize: "0.85rem",
                outline: "none",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--acid)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--line)")}
            />
            <button
              type="submit"
              className="primary"
              disabled={loadingEmail}
              style={{ width: "100%", padding: "0.75rem", fontSize: "0.82rem" }}
            >
              {loadingEmail ? "Sending Magic Link..." : "Send Secure Link"} <ArrowRight size={14} />
            </button>
          </form>
        )}

        {/* Demo Mission Clearance Bypass Option */}
        <div style={{ marginTop: "1.25rem", textAlign: "center" }}>
          <button
            type="button"
            id="demo-clearance-btn"
            onClick={() => bypassForDemo()}
            style={{
              background: "none",
              border: "none",
              color: "rgba(222, 221, 211, 0.45)",
              fontFamily: "monospace",
              fontSize: "0.74rem",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              cursor: "pointer",
              textDecoration: "underline",
              textUnderlineOffset: "3px",
              transition: "color 0.15s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "var(--warm)")}
            onMouseOut={(e) => (e.currentTarget.style.color = "rgba(222, 221, 211, 0.45)")}
          >
            ⚡ Immediate Mission Clearance (ISRO Commander Demo)
          </button>
        </div>

        {/* Telemetry Footer */}
        <div
          style={{
            marginTop: "2rem",
            paddingTop: "1.25rem",
            borderTop: "1px solid var(--line)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "0.72rem",
            color: "rgba(222, 221, 211, 0.4)",
            fontFamily: "monospace",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "var(--acid)",
                boxShadow: "0 0 8px var(--acid)",
              }}
            />
            <span>Supabase Auth Engine</span>
          </div>
          <span>v2.0.0</span>
        </div>
      </div>
    </div>
  )
}
