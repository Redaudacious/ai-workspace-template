// The guard's decision logic. It uses nothing from Claude Code, so `claude plugin test` can try it without a real `Write`.

/** Guarded files: an `INDEX.md` under `records/`, and any `MEMORY.md`. */
export const isGuarded = (path: string): boolean => {
  const parts = path.split('/')
  const name = parts.at(-1)
  return name === 'MEMORY.md' || (name === 'INDEX.md' && parts.includes('records'))
}

/** The reason to refuse when a write leaves a guarded file with less than half its bytes. Otherwise nothing. */
export const judge = (path: string, oldSize: number, newSize: number): string | undefined =>
  isGuarded(path) && newSize * 2 < oldSize
    ? `This write would shrink \`${path}\` from ${oldSize} to ${newSize} bytes. Edit the file in smaller pieces instead.`
    : undefined
