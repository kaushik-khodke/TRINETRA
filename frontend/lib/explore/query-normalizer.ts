/**
 * TRINETRA / Shanetra Explore Architecture
 * Query Normalizer (Frontend UX Helper)
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 */

export class QueryNormalizer {
  /**
   * Sanitizes input query string before sending to backend.
   */
  static cleanQuery(raw: string): string {
    if (!raw) return ""
    return raw.trim().replace(/\s+/g, " ")
  }

  /**
   * Checks if query looks like a simple command (for UI hints).
   */
  static isSimpleCommand(query: string): boolean {
    const q = query.toLowerCase().trim()
    const simplePatterns = [
      "reset",
      "home",
      "zoom in",
      "zoom out",
      "show boundaries",
      "hide boundaries",
      "show borders",
      "hide borders",
      "turn on boundaries",
      "turn off boundaries",
    ]
    return simplePatterns.includes(q)
  }
}
