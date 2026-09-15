"use client"

import React, { createContext, useContext, useEffect, useState, useMemo } from "react"
import { Session, User } from "@supabase/supabase-js"
import { supabase, signInWithGoogle as sbSignInWithGoogle, signInWithEmailOtp as sbSignInWithEmailOtp, signOut as sbSignOut } from "@/lib/supabase"

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  isAuthenticated: boolean
  displayName: string
  avatarUrl: string | null
  email: string | null
  signInWithGoogle: (redirectTo?: string) => Promise<any>
  signInWithEmail: (email: string) => Promise<any>
  signOut: () => Promise<void>
  bypassForDemo: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if demo bypass was active
    if (typeof window !== "undefined" && (localStorage.getItem("trinetra_demo_auth") === "true" || localStorage.getItem("satquery_demo_auth") === "true")) {
      const demoUser: any = {
        id: "isro-operator-01",
        email: "commander@isro.gov.in",
        user_metadata: {
          full_name: "ISRO Mission Commander",
          avatar_url: null,
        },
      }
      setUser(demoUser)
      setSession({ user: demoUser } as any)
      setLoading(false)
      return
    }

    // 1. Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    }).catch((err) => {
      console.error("[Auth] Initial session check failed:", err)
      setLoading(false)
    })

    // 2. Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const displayName = useMemo(() => {
    if (!user) return "Guest Operator"
    return (
      user.user_metadata?.full_name ||
      user.user_metadata?.name ||
      user.user_metadata?.user_name ||
      user.email?.split("@")[0] ||
      "Aerospace Specialist"
    )
  }, [user])

  const avatarUrl = useMemo(() => {
    if (!user) return null
    return user.user_metadata?.avatar_url || user.user_metadata?.picture || null
  }, [user])

  const email = useMemo(() => user?.email ?? null, [user])

  const signInWithGoogle = async (redirectTo?: string) => {
    return sbSignInWithGoogle(redirectTo)
  }

  const signInWithEmail = async (emailToUse: string) => {
    return sbSignInWithEmailOtp(emailToUse)
  }

  const signOut = async () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trinetra_demo_auth")
      localStorage.removeItem("satquery_demo_auth")
    }
    await sbSignOut()
    setSession(null)
    setUser(null)
  }

  const bypassForDemo = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("trinetra_demo_auth", "true")
    }
    const demoUser: any = {
      id: "isro-operator-01",
      email: "commander@isro.gov.in",
      user_metadata: {
        full_name: "ISRO Mission Commander",
        avatar_url: null,
      },
    }
    setUser(demoUser)
    setSession({ user: demoUser } as any)
  }

  const value: AuthContextType = {
    user,
    session,
    loading,
    isAuthenticated: Boolean(user),
    displayName,
    avatarUrl,
    email,
    signInWithGoogle,
    signInWithEmail,
    signOut,
    bypassForDemo,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
