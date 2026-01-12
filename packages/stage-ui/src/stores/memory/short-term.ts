import { nanoid } from 'nanoid'
import { defineStore } from 'pinia'
import { computed } from 'vue'

import { createResettableLocalStorage } from '../../utils/resettable'
import type { MemoryEntry, MemorySnapshotOptions } from './types'

const SHORT_TERM_LIMIT = 80

function sanitizeContent(content: string, maxLength = 2000) {
  if (content.length <= maxLength)
    return content

  return `${content.slice(0, maxLength)}…`
}

export const useShortTermMemoryStore = defineStore('memory-short-term', () => {
  const [entries, resetEntries] = createResettableLocalStorage<MemoryEntry[]>('memory/short-term', [])

  const count = computed(() => entries.value.length)

  function remember(content: string, options?: { tags?: string[], metadata?: Record<string, unknown> }) {
    const now = Date.now()
    const entry: MemoryEntry = {
      id: nanoid(),
      content: sanitizeContent(content),
      createdAt: now,
      updatedAt: now,
      tags: options?.tags,
      metadata: options?.metadata,
    }

    entries.value = [...entries.value, entry].slice(-SHORT_TERM_LIMIT)
    return entry
  }

  function forget(entryId: string) {
    entries.value = entries.value.filter(entry => entry.id !== entryId)
  }

  function clear() {
    resetEntries()
  }

  function getSnapshot(options?: MemorySnapshotOptions) {
    const limit = options?.limit ?? SHORT_TERM_LIMIT
    return entries.value.slice(-limit)
  }

  return {
    entries,
    count,
    remember,
    forget,
    clear,
    getSnapshot,
  }
})
