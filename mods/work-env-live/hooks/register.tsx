import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Agent, Chat, Order, Part, State, View } from '../types'
import {
  accountRow, chatLabel, chatName, chatRow, chatUrl, colorFor, dollars, isPage, nowChats, NOTE, project, shares, shortModel,
  shouldNotify, thousands, usageArgs, usageFromDirs, weekChats, when, windowText, withoutAgents,
} from './line'

const PANE = 'work-env-sessions'
const TITLE = 'Usage'
const state = atom({ plugin: 'work-env-live', key: 'state' } as const, null as State | null)
const threshold = atom({ plugin: 'work-env-live', key: 'threshold' } as const, 0)
// Each load takes a number. A loop left over from the previous load sees a different number and stops.
const loop = atom({ plugin: 'work-env-live', key: 'loop' } as const, 0)
// The two colored rows above the input box. The hook draws them on `AbovePrompt`.
const rows = atom({ plugin: 'work-env-live', key: 'rows' } as const, [] as Part[][])
const view = atom({ plugin: 'work-env-live', key: 'view' } as const, 'now' as View)
const order = atom({ plugin: 'work-env-live', key: 'order' } as const, 'costly' as Order)
const expanded = atom({ plugin: 'work-env-live', key: 'expanded' } as const, [] as string[])
// The web pages that this chat read directly, for the reminder of the reader rule.
const pages = atom({ plugin: 'work-env-live', key: 'pages' } as const, 0)
const STEP_MS = 10_000
const SLOW = 6 // every 6th run also writes the window file: once a minute

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'sessions', description: 'Usage panel: the chats that are warm now, and the week' })
    await update($, loop, n => n + 1)
    const mine = await read($, loop)
    const id = await $.session.id()
    // Without a restore (the session where the mod was written), usage.py is searched under the session root.
    const fromRoot = `${await $.session.root()}/bin/usage.py`
    const usage = usageFromDirs(await $.env.get('CLAUDE_CODE_PLUGIN_DIRS')) ??
      ((await $.fs.exists(fromRoot)) ? fromRoot : undefined)
    // The window files are in the personal layer, only where it exists.
    const records = usage?.replace(/\/bin\/usage\.py$/, '/records')
    const weeks = records && (await $.fs.exists(records)) ? `${records}/usage/weeks` : undefined
    $.ui.status(undefined) // the plain row from before, without colors, goes away
    void $.ui.open({ id: PANE, title: TITLE })
    void (async () => {
      // ponytail: refresh every 10 s, a local run without tokens. The loop of an old load stops through `loop`.
      for (let i = 0; ; i++) {
        try {
          if ((await read($, loop)) !== mine) return
          const u = await $.session.usage()
          const settings = (await $.settings.read()) as { autoCompactWindow?: number }
          const t = settings.autoCompactWindow ?? u.context.window
          await update($, threshold, () => t)
          let s = await read($, state)
          if (usage) {
            const r = await $.process.run(usageArgs(usage, u.rateLimits, i % SLOW === 0 ? weeks : undefined), { timeoutMs: 20_000 })
            if (r.exitCode === 0) {
              const fresh = JSON.parse(r.stdout) as State
              await update($, state, () => fresh)
              s = fresh
            }
          }
          const thisChat = s?.chats.find(c => c.log === id)
          const now = new Date(await $.clock.now())
          const parts = [chatRow(thisChat, u.cost?.usd, u.context.tokens, t), accountRow(u.rateLimits, now, s?.vibe)]
          await update($, rows, () => parts)
          await $.clock.sleep(STEP_MS)
        } catch {
          return
        }
      }
    })()
    return next(e)
  })

  // The reminder for research: from the third web page read directly in the chat, a note for the
  // model next to the tool result and, rarely, a notice for the person. Nothing is blocked.
  on('tool.call', async ($, e, next) => {
    const r = await next(e)
    if (!isPage(e.tool, e.agentId) || r.deny !== undefined) return r
    const n = await update($, pages, x => x + 1)
    if (n < 3) return r
    if (shouldNotify(n)) $.ui.toast(`${n} web pages read directly in the chat. ${NOTE}`)
    return { ...r, context: [...(r.context ?? []), NOTE] }
  })

  on('command.run', { command: 'sessions' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    return { text: 'The usage panel is open.' }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const r = (await read($, rows)).filter(parts => parts.length > 1)
    if (e.props.hasSurvey || r.length === 0) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        {r.map(parts => (
          <Text>
            {parts.map((p, i) => (
              <Text color={p.color}>
                {i > 1 ? <Text color="subtle"> · </Text> : i === 1 ? ' ' : ''}
                {p.text}
              </Text>
            ))}
          </Text>
        ))}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const s = await read($, state)
    const v = await read($, view)
    const ord = await read($, order)
    const open = await read($, expanded)
    const t = (await read($, threshold)) || 400_000

    // A chat row: the state or the place, the name as a button that goes to the chat, the project, the cost, the share.
    const row = (c: Chat, left: string, usd: number) => (
      <Box>
        <Text color={c.state === 'working' ? 'success' : c.state === 'warm' ? 'claude' : 'inactive'}>{left} </Text>
        {c.local ? (
          <Button key={`chat-${c.code}`} label={chatName(c)} onPress={() => void $.process.run(['xdg-open', chatUrl(c.local ?? '')], { timeoutMs: 10_000 })} />
        ) : (
          <Text bold>{chatName(c)}</Text>
        )}
        <Text color="subtle"> · {project(c.project)} · </Text>
        <Text color={colorFor(usd, 5, 20)}>{dollars(usd)}</Text>
        <Text color="suggestion"> · {c.weekly != null ? `${c.weekly}%` : '—'}</Text>
      </Box>
    )
    // Expanded, a chat shows its cost without agents, then each agent on its own row. `inWindow` picks the cost in the window.
    const agentRow = (a: Agent, inWindow: boolean) => (
      <Text color={a.working ? 'text' : 'inactive'}>
        {'    '}<Text color={a.working ? 'success' : 'inactive'}>{a.working ? '▶' : '·'}</Text> {a.type} · {a.description} ·{' '}
        {shortModel(a.model)} · {dollars(inWindow ? a.usd_window : a.usd)}{a.weekly != null ? ` · ${a.weekly}%` : ''}
      </Text>
    )
    const breakdown = (c: Chat, inWindow: boolean) =>
      open.includes(c.code) ? (
        <Box flexDirection="column">
          <Text color="subtle">{'    '}the chat alone · {shortModel(c.model)} · {dollars(withoutAgents(c, inWindow))}</Text>
          {c.agents.map(a => agentRow(a, inWindow))}
        </Box>
      ) : ''
    const toggle = (c: Chat) =>
      c.agents.length ? (
        <Button
          key={`expand-${c.code}`}
          label={`${open.includes(c.code) ? '▾' : '▸'} ${c.agents.length} agents`}
          onPress={() => void update($, expanded, d => (d.includes(c.code) ? d.filter(x => x !== c.code) : [...d, c.code]))}
        />
      ) : ''
    const expandAll = (l: Chat[]) => {
      const withAgents = l.filter(c => c.agents.length).map(c => c.code)
      const all = withAgents.length > 0 && withAgents.every(x => open.includes(x))
      return withAgents.length ? (
        <Button key="expand-all" label={all ? 'collapse all' : 'expand all'} onPress={() => void update($, expanded, () => (all ? [] : withAgents))} />
      ) : ''
    }
    const buttons = (
      <Box>
        <Button key="view-now" label="Now" variant={v === 'now' ? 'primary' : 'secondary'} onPress={() => void update($, view, () => 'now')} />
        <Text> </Text>
        <Button key="view-week" label="Week" variant={v === 'week' ? 'primary' : 'secondary'} onPress={() => void update($, view, () => 'week')} />
        <Text color="subtle">{'   '}{s ? `updated ${new Date(s.updated).toTimeString().slice(0, 8)}` : 'reading…'}</Text>
      </Box>
    )
    if (!s) return <Box flexDirection="column">{buttons}</Box>
    const note = s.app ? '' : <Text color="warning">The app files are missing: chats show with their code, without a click.</Text>

    if (v === 'now') {
      const l = nowChats(s.chats)
      return (
        <Box flexDirection="column">
          {buttons}
          {note}
          {l.length === 0 && <Text color="inactive">No chat is warm now: any chat would rewrite its whole context at the first message.</Text>}
          {expandAll(l)}
          {l.map(c => (
            <Box flexDirection="column" marginTop={1}>
              {row(c, chatLabel(c), c.usd)}
              <Box>
                <Text color="subtle">
                  {'    '}{c.tool === 'vibe' ? `Vibe ${c.model}` : `${shortModel(c.model)} ${c.effort} · context ${thousands(c.context)} (${Math.round((100 * c.context) / t)}%)`}{' '}
                </Text>
                {toggle(c)}
              </Box>
              {breakdown(c, false)}
            </Box>
          ))}
        </Box>
      )
    }

    const l = weekChats(s.chats, ord)
    const now = new Date(s.updated)
    const ORDERS: [Order, string][] = [['costly', 'the 10 most expensive'], ['latest', 'the last 10'], ['all', 'all']]
    return (
      <Box flexDirection="column">
        {buttons}
        <Text color="subtle">{windowText(s)}</Text>
        {note}
        <Box marginTop={1}>
          {ORDERS.map(([o, text]) => (
            <Box>
              <Button key={`order-${o}`} label={text} variant={ord === o ? 'primary' : 'secondary'} onPress={() => void update($, order, () => o)} />
              <Text> </Text>
            </Box>
          ))}
          {expandAll(l)}
        </Box>
        {l.map((c, i) => (
          <Box flexDirection="column">
            <Box>
              {row(c, ord === 'latest' ? when(c.last, now) : `${i + 1}.`, c.usd_window)}
              <Text> </Text>
              {toggle(c)}
            </Box>
            {breakdown(c, true)}
          </Box>
        ))}
        <Box marginTop={1} flexDirection="column">
          <Text>by model: {shares(s.totals.by_model, shortModel)}</Text>
          <Text>by role:  {shares(s.totals.by_role)}</Text>
        </Box>
      </Box>
    )
  })
}
