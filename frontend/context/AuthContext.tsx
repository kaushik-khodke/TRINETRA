"use client"

import React, { createContext, useContext, useMemo } from "react"
import { Session, User } from "@supabase/supabase-js"

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

const defaultUser: any = {
  id: "isro-operator-01",
  email: "commander@isro.gov.in",
  user_metadata: {
    full_name: "ISRO Mission Commander",
    avatar_url: null,
  },
}

const defaultSession: any = {
  user: defaultUser,
  access_token: "local-operator-clearance",
  token_type: "bearer",
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const value: AuthContextType = useMemo(
    () => ({
      user: defaultUser,
      session: defaultSession,
      loading: false,
      isAuthenticated: true,
      displayName: "ISRO Mission Commander",
      avatarUrl: null,
      email: "commander@isro.gov.in",
      signInWithGoogle: async () => {},
      signInWithEmail: async () => {},
      signOut: async () => {},
      bypassForDemo: () => {},
    }),
    []
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

