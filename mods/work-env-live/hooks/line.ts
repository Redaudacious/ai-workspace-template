// The pure calculations of the mod, so tests can run them without the engine.
import type { Chat, Order, Part, State } from '../types'

export type Limit = { kind: string; percentUsed: number; resetsAt?: string }

export const thousands = (n: number) => `${Math.round(n / 1000)}K`
export const dollars = (x: number) => `${x.toFixed(2).replace('.', ',')} $`
export const euros = (x: number) => `${x.toFixed(2).replace('.', ',')} €`
// Share of the week: one decimal below 1%, a whole number from 1% up.
export const share = (x: number) => `${(x < 1 ? x.toFixed(1) : String(Math.round(x))).replace('.', ',')}%`

// Theme color for a value: green below the first threshold, yellow up to the second, red above.
export const colorFor = (v: number, warn: number, bad: number) => (v >= bad ? 'error' : v >= warn ? 'warning' : 'success')

// "opus-5-5" → "Opus".
export function shortModel(m: string): string {
  const f = m.split('-')[0] ?? m
  return f ? f.charAt(0).toUpperCase() + f.slice(1) : '?'
}

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const hhmm = (d: Date) => `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`

// "at 16:40" today, "Thursday at 10:00" on another day.
export function when(iso: string, now: Date): string {
  const d = new Date(iso)
  return d.toDateString() === now.toDateString() ? `at ${hhmm(d)}` : `${DAYS[d.getDay()]} at ${hhmm(d)}`
}

// "Thursday 2 Oct 10:00", for the ends of the window.
export function dayTime(iso: string): string {
  const d = new Date(iso)
  return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]} ${hhmm(d)}`
}

// A row above the input box, as text: the label, a space, then the parts split by " · ".
export const rowText = (p: Part[]) => p.map((x, i) => (i === 0 ? '' : i === 1 ? ' ' : ' · ') + x.text).join('')

// First row: the open chat, with its cost and how long the cache lasts.
export function chatRow(c: Chat | undefined, usd: number | undefined, context: number | undefined, threshold: number): Part[] {
  const parts: Part[] = [{ text: 'this chat:', color: 'subtle' }]
  const cost = c?.usd ?? usd
  if (cost !== undefined) parts.push({ text: `${dollars(cost)} at API prices`, color: colorFor(cost, 5, 20) })
  if (c?.model) parts.push({ text: `${shortModel(c.model)} ${c.effort}`.trim(), color: c.effort === 'max' ? 'error' : 'text' })
  const ctx = context ?? c?.context
  if (ctx) parts.push({ text: `context ${thousands(ctx)} of ${thousands(threshold)} (${Math.round((100 * ctx) / threshold)}%)`, color: colorFor((100 * ctx) / threshold, 50, 80) })
  if (c?.weekly != null) parts.push({ text: `${share(c.weekly)} of the week`, color: 'suggestion' })
  if (c && c.state !== 'cold' && c.warm_min != null) parts.push({ text: `cache warm for ${c.warm_min} more min`, color: c.warm_min < 10 ? 'warning' : 'success' })
  else if (c?.state === 'cold') parts.push({ text: `cache expired — the first message rewrites ~${dollars(c.rewrite_usd)}`, color: 'error' })
  return parts
}

// Second row: the limits of the Claude account, each with its reset time, then the sum of the month
// for Vibe, counted from its logs. A session on a model with no price in config.toml is counted apart.
export function accountRow(limits: Limit[], now: Date, vibe?: State['vibe']): Part[] {
  const parts: Part[] = [{ text: 'account:', color: 'subtle' }]
  for (const l of limits) {
    const name = l.kind === 'five_hour' ? '5 hours' : l.kind === 'seven_day' ? 'week' : l.kind
    const reset = l.resetsAt ? `, resets ${when(l.resetsAt, now)}` : ''
    parts.push({ text: `${name} ${Math.round(l.percentUsed)}%${reset}`, color: colorFor(l.percentUsed, 50, 80) })
  }
  if (vibe?.sessions) {
    const unpriced = vibe.no_price ? ` (+${vibe.no_price} without a price)` : ''
    parts.push({ text: `Vibe ${MONTHS[Number(vibe.month.slice(5)) - 1]} ${euros(vibe.eur)}${unpriced}`, color: 'text' })
  }
  return parts
}

// The "Now" view: the chats that are working, then the warm ones, by how long the cache lasts.
export const nowChats = (c: Chat[]) =>
  c.filter(x => x.state !== 'cold').sort((a, b) => Number(b.state === 'working') - Number(a.state === 'working') || (b.warm_min ?? 0) - (a.warm_min ?? 0))

// The "Week" view: the ten most expensive chats in the window, the ten used last, or all of them.
export function weekChats(c: Chat[], order: Order): Chat[] {
  const list = c.filter(x => x.usd_window > 0).sort((a, b) => b.usd_window - a.usd_window)
  if (order === 'latest') return [...list].sort((a, b) => b.last.localeCompare(a.last)).slice(0, 10)
  return order === 'all' ? list : list.slice(0, 10)
}

// What the chat cost without its agents: over its whole life, or only in the 7-day window.
export const withoutAgents = (c: Chat, inWindow: boolean) =>
  inWindow ? c.usd_window - c.agents.reduce((t, a) => t + a.usd_window, 0) : c.usd - c.agents.reduce((t, a) => t + a.usd, 0)

// The address that the desktop app opens to jump to a chat.
export const chatUrl = (local: string) => `claude://claude.ai/epitaxy/${local}`
export const chatName = (c: Chat) => c.title || c.code
export const chatLabel = (c: Chat) => (c.state === 'working' ? '▶ working' : `warm ${c.warm_min ?? 0} min`)

// "Opus 81% · Sonnet 14% · Haiku 5%", from sums by model or by role.
export function shares(sums: Record<string, number>, group: (k: string) => string = k => k): string {
  const g: Record<string, number> = {}
  for (const [k, v] of Object.entries(sums)) g[group(k)] = (g[group(k)] ?? 0) + v
  const total = Object.values(g).reduce((a, b) => a + b, 0)
  if (!total) return '—'
  return Object.entries(g)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${k} ${Math.round((100 * v) / total)}%`)
    .join(' · ')
}

export function windowText(s: State): string {
  const w = s.window
  const end = w.reset ? dayTime(w.reset) : 'now'
  return `window: ${dayTime(w.start)} → ${end} · ${w.percent != null ? `${Math.round(w.percent)}% used` : 'no limit percentage'}`
}

// The web pages that the main chat reads directly. Agents have their own rules.
export const PAGES = ['WebFetch', 'WebSearch', 'mcp__Claude_Browser__get_page_text', 'mcp__claude-in-chrome__get_page_text']
export const NOTE = 'rule: for more than two pages, use the reader'
export const isPage = (tool: string, agentId: string | undefined) => !agentId && PAGES.includes(tool)
// The note for the model starts at the third page. The notice for the person comes at the third page, then at every tenth.
export const shouldNotify = (n: number) => n === 3 || (n > 3 && n % 10 === 0)

// "-home-<user>-<workspace>-projects-<name>" → "<name>"; the workspace folder may have any name.
export const project = (folder: string) => folder.replace(/^-home-[^-]+-/, '').replace(/^(?:.*-)?projects-/, '') || folder

// usage.py is in bin/ of the workspace root. The root comes from the path of the mod,
// which the restore step puts in CLAUDE_CODE_PLUGIN_DIRS (a list split by ":").
export function usageFromDirs(dirs: string | undefined): string | undefined {
  const mod = (dirs ?? '').split(':').find(d => d.replace(/\/+$/, '').endsWith('/mods/work-env-live'))
  return mod ? mod.replace(/\/+$/, '').replace(/\/mods\/work-env-live$/, '/bin/usage.py') : undefined
}

// The command for usage.py: on every run, the state of all the chats, with the percent of the
// 7-day limit when the app gives it. With `weeks`, once a minute, it also writes the file of the window.
export function usageArgs(usage: string, limits: Limit[], weeks?: string): string[] {
  const a = ['python3', usage, '--state']
  const s = limits.find(l => l.kind === 'seven_day')
  if (s?.resetsAt) a.push('--week', String(s.percentUsed), '--reset', s.resetsAt)
  if (s?.resetsAt && weeks) a.push('--weeks', weeks)
  return a
}
