import type { Register } from 'claude-code'

import { judge } from './guard'

// An agent that has read one part of an index and then writes only that part over it loses the rest.
// This hook refuses a full write that leaves a guarded file with less than half of its bytes.
// The hook follows the path to the real file, because the memory folder is linked from the
// Claude configuration folder. A file that does not exist yet passes: it has nothing to lose.
export const register: Register = on => {
  on('classic.PreToolUse', async ($, e, next) => {
    if (e.tool !== 'Write') return next(e)
    const stat = await $.fs.stat(e.file_path, { resolve: true }).catch(() => undefined)
    const reason = stat?.realPath === undefined
      ? undefined
      : judge(stat.realPath, stat.size, new TextEncoder().encode(e.content).length)
    return reason === undefined ? next(e) : { deny: reason }
  })
}
