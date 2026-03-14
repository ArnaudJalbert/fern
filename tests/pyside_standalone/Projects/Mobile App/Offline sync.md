---
id: 302
properties:
- id: status
  name: Status
  type: string
  value: Not Started
- id: platform
  name: Platform
  type: string
  value: iOS + Android
- id: done
  name: Done
  type: boolean
  value: false
- id: fast
  name: fast
  type: boolean
  value: true
---

# Offline sync

Allow users to edit pages offline and sync when back online.

## Approach

- Use SQLite for local storage
- CRDT-based conflict resolution
- Background sync service
- Visual indicator for sync status