/**
 * TRINETRA / Shanetra Explore Architecture
 * Client Data Cache
 * Phase 2: In-memory client-side cache for discovery items and layer metadata.
 */

interface CacheEntry<T> {
  value: T
  expiry: number
}

class ClientDataCache {
  private store: Map<string, CacheEntry<any>> = new Map()

  get<T>(key: string): T | null {
    const entry = this.store.get(key)
    if (!entry) return null
    if (Date.now() > entry.expiry) {
      this.store.delete(key)
      return null
    }
    return entry.value as T
  }

  set<T>(key: string, value: T, ttlMs: number = 300000): void {
    this.store.set(key, {
      value,
      expiry: Date.now() + ttlMs,
    })
  }

  clear(): void {
    this.store.clear()
  }
}

export const clientDataCache = new ClientDataCache()
