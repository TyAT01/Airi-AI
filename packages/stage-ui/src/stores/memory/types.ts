export interface MemoryEntry {
  id: string
  content: string
  createdAt: number
  updatedAt?: number
  tags?: string[]
  metadata?: Record<string, unknown>
}

export interface MemorySnapshotOptions {
  limit?: number
}
