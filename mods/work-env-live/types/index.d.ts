// Shape of the JSON from `usage.py --state`. `tests/test-usage.py` fixes the fields.
export type Agent = {
  id: string; type: string; description: string; model: string; usd: number; usd_sonnet: number
  usd_window: number; weekly: number | null; context: number; working: boolean
}
export type Chat = {
  code: string; log: string; local: string | null; title: string; project: string; cwd: string; work: string
  role: string; model: string; effort: string; usd: number; usd_window: number; weekly: number | null
  context: number; state: 'working' | 'warm' | 'cold'; warm_min: number | null; rewrite_usd: number
  last: string; agents: Agent[]; tool: 'claude' | 'vibe'
}
export type State = {
  updated: string; app: boolean
  window: { start: string; reset: string | null; percent: number | null }
  chats: Chat[]
  totals: { usd: number; by_model: Record<string, number>; by_role: Record<string, number> }
  vibe: { month: string; usd: number; eur: number; sessions: number; no_price: number }
}
export type Part = { text: string; color: string }
export type View = 'now' | 'week'
export type Order = 'costly' | 'latest' | 'all'

declare module 'claude-code' {
  interface PluginState {
    'work-env-live': {
      state: State | null; threshold: number; loop: number; rows: Part[][]
      view: View; order: Order; expanded: string[]; pages: number
    }
  }
}
