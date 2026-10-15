import { expect, test } from 'claude-code/testing'

import type { Chat } from '../types'
import { accountRow, chatRow, chatUrl, colorFor, dollars, isPage, nowChats, project, rowText, shares, shortModel, shouldNotify, usageArgs, usageFromDirs, weekChats, withoutAgents } from './line'

const chat = (x: Partial<Chat>): Chat => ({
  code: 'aaaaaaaa', log: 'aaaaaaaa-1', local: 'local_1', title: '', project: '-home-user-workspace', cwd: '/r', work: '',
  role: 'other', model: 'opus-5-5', effort: 'high', usd: 0.93, usd_window: 0.93, weekly: 0.1, context: 113_000,
  state: 'warm', warm_min: 52, rewrite_usd: 3, last: '', agents: [], tool: 'claude', ...x,
})

test('chatRow: the row from the spec, for a warm chat', () => {
  expect(rowText(chatRow(chat({}), undefined, 113_000, 400_000))).toBe(
    'this chat: 0,93 $ at API prices · Opus high · context 113K of 400K (28%) · 0,1% of the week · cache warm for 52 more min')
})

test('chatRow: a cold chat shows what the first message rewrites, and effort max is red', () => {
  const p = chatRow(chat({ state: 'cold', warm_min: null, effort: 'max' }), undefined, undefined, 400_000)
  expect(p.at(-1)?.text).toBe('cache expired — the first message rewrites ~3,00 $')
  expect(p.at(-1)?.color).toBe('error')
  expect(p.find(x => x.text === 'Opus max')?.color).toBe('error')
})

test('chatRow: without usage.py, only the cost and the context of the session', () => {
  expect(rowText(chatRow(undefined, 1.5, 200_000, 400_000))).toBe('this chat: 1,50 $ at API prices · context 200K of 400K (50%)')
})

test('accountRow: both limits, with the reset time', () => {
  const now = new Date(2026, 9, 8, 12, 0)
  const today = new Date(2026, 9, 8, 16, 40).toISOString()
  const friday = new Date(2026, 9, 9, 10, 0).toISOString()
  expect(rowText(accountRow([{ kind: 'five_hour', percentUsed: 8.2, resetsAt: today }, { kind: 'seven_day', percentUsed: 12, resetsAt: friday }], now)))
    .toBe('account: 5 hours 8%, resets at 16:40 · week 12%, resets Friday at 10:00')
})

test('accountRow: the sum of the month for Vibe, after the Claude limits; with no sessions, nothing', () => {
  const now = new Date(2026, 9, 8, 12, 0)
  expect(rowText(accountRow([{ kind: 'five_hour', percentUsed: 8.2 }], now, { month: '2026-10', usd: 3.84, eur: 3.26, sessions: 3, no_price: 1 })))
    .toBe('account: 5 hours 8% · Vibe Oct 3,26 € (+1 without a price)')
  expect(accountRow([], now, { month: '2026-10', usd: 0, eur: 0, sessions: 0, no_price: 0 }).length).toBe(1)
})

test('nowChats: the working ones first, then by minutes of cache; the cold ones are left out', () => {
  const l = nowChats([chat({ code: 'a', warm_min: 8 }), chat({ code: 'b', state: 'cold', warm_min: null }),
    chat({ code: 'c', warm_min: 52 }), chat({ code: 'd', state: 'working', warm_min: 59 })])
  expect(l.map(c => c.code)).toEqual(['d', 'c', 'a'])
})

test('weekChats: the ten most expensive, the ten used last, or all those with a cost in the window', () => {
  const hour = (i: number) => new Date(Date.UTC(2026, 9, 8, 23 - i)).toISOString()
  const l = Array.from({ length: 12 }, (_, i) => chat({ code: String(i), usd_window: i, last: hour(i) }))
  expect(weekChats(l, 'costly').map(c => c.code)).toEqual(['11', '10', '9', '8', '7', '6', '5', '4', '3', '2'])
  expect(weekChats(l, 'latest').map(c => c.code)).toEqual(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
  expect(weekChats(l, 'all').length).toBe(11)
})

test('chatUrl: a click goes to the chat through the address of the app', () => {
  expect(chatUrl('local_0a1b2c3d')).toBe('claude://claude.ai/epitaxy/local_0a1b2c3d')
})

test('shares: by model family, in percent', () => {
  expect(shares({ 'opus-5-5': 81, 'opus-5': 0, 'sonnet-5-5': 14, 'haiku-5-5': 5 }, shortModel)).toBe('Opus 81% · Sonnet 14% · Haiku 5%')
  expect(shares({})).toBe('—')
})

test('pages: only the main chat, the note from the third', () => {
  expect(isPage('WebFetch', undefined)).toBe(true)
  expect(isPage('WebFetch', 'a1')).toBe(false)
  expect(isPage('Read', undefined)).toBe(false)
  expect([1, 2, 3, 4, 10, 20].map(shouldNotify)).toEqual([false, false, true, false, true, true])
})

test('money and color', () => {
  expect(dollars(94.1)).toBe('94,10 $')
  expect([colorFor(10, 50, 80), colorFor(50, 50, 80), colorFor(95, 50, 80)]).toEqual(['success', 'warning', 'error'])
})

test('project: the short name', () => {
  expect(project('-home-user-workspace-projects-my-project')).toBe('my-project')
})

test('usageFromDirs: usage.py from the path of the mod, among other folders', () => {
  expect(usageFromDirs('/other/plugin:/home/x/workspace/mods/work-env-live/')).toBe('/home/x/workspace/bin/usage.py')
  expect(usageFromDirs('/other/plugin')).toBe(undefined)
  expect(usageFromDirs(undefined)).toBe(undefined)
})

test('usageArgs: the percent on every run, the file of the window only with the given folder', () => {
  const lim = [{ kind: 'seven_day', percentUsed: 41.5, resetsAt: '2026-10-10T00:00:00Z' }]
  expect(usageArgs('/r/bin/usage.py', [])).toEqual(['python3', '/r/bin/usage.py', '--state'])
  expect(usageArgs('/r/bin/usage.py', lim)).toEqual(['python3', '/r/bin/usage.py', '--state',
    '--week', '41.5', '--reset', '2026-10-10T00:00:00Z'])
  expect(usageArgs('/r/bin/usage.py', lim, '/r/records/usage/weeks').slice(-2)).toEqual(['--weeks', '/r/records/usage/weeks'])
})

test('withoutAgents: the chat without its agents, over its whole life or only in the window', () => {
  const a = { id: 'x', type: 'executor', description: '', model: 'sonnet-5-5', usd: 2, usd_sonnet: 2, usd_window: 1, weekly: null, context: 0, working: false }
  const c = chat({ usd: 5, usd_window: 3, agents: [a, { ...a, usd: 1, usd_window: 0.5 }] })
  expect(withoutAgents(c, false)).toBe(2)
  expect(withoutAgents(c, true)).toBe(1.5)
})
