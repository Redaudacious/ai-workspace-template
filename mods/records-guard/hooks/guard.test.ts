import { expect, test } from 'claude-code/testing'

import { isGuarded, judge } from './guard'

const INDEX = '/w/records/journal/INDEX.md'

test('isGuarded: the record indexes and the memory, nothing else', () => {
  expect(isGuarded(INDEX)).toBe(true)
  expect(isGuarded('/w/projects/p/records/pitfalls/INDEX.md')).toBe(true)
  expect(isGuarded('/w/records/memory/MEMORY.md')).toBe(true)
  expect(isGuarded('/w/docs/INDEX.md')).toBe(false)
  expect(isGuarded('/w/records/journal/2026-10-08-something.md')).toBe(false)
  expect(isGuarded('/w/STATE.md')).toBe(false)
})

test('judge: below half, the refusal names the file and the bytes', () => {
  expect(judge(INDEX, 1000, 499)).toBe(
    'This write would shrink `/w/records/journal/INDEX.md` from 1000 to 499 bytes. Edit the file in smaller pieces instead.')
})

test('judge: a longer file, a small shrink and exactly half all pass', () => {
  expect(judge(INDEX, 1000, 1200)).toBe(undefined)
  expect(judge(INDEX, 1000, 900)).toBe(undefined)
  expect(judge(INDEX, 1000, 500)).toBe(undefined)
})

test('judge: an unguarded file passes however much it shrinks', () => {
  expect(judge('/w/STATE.md', 1000, 10)).toBe(undefined)
})
