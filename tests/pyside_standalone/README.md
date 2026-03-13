# Standalone test vault

Mock data for testing the Fern UI. Open this folder as a vault via **Vault > Open...** (or from the welcome page).

Testy

## Structure

```
pyside_standalone/
├── Welcome.md                          (root page)
├── Scratch.md                          (root page)
├── Inbox/                              (database — tasks with Priority + Done)
│   ├── database.json
│   ├── Buy groceries.md
│   ├── Schedule dentist.md
│   ├── Fix leaky faucet.md
│   └── Reply to Alex.md
├── Projects/
│   ├── Roadmap.md                      (loose page)
│   ├── Website Redesign/               (database — Status + Assigned + Done)
│   │   ├── database.json
│   │   ├── Design mockups.md
│   │   ├── Migrate to new CMS.md
│   │   └── Update color palette.md
│   └── Mobile App/                     (database — Status + Platform + Done)
│       ├── database.json
│       ├── Push notifications.md
│       ├── Onboarding flow.md
│       └── Offline sync.md
├── Reading List/                       (database — Author + Genre + Read)
│   ├── database.json
│   ├── Designing Data-Intensive Applications.md
│   ├── The Pragmatic Programmer.md
│   ├── Project Hail Mary.md
│   └── Atomic Habits.md
└── Journal/                            (folder with loose daily notes)
    ├── 2026-03-10.md
    ├── 2026-03-11.md
    └── 2026-03-12.md
```

Any folder containing a `database.json` file is treated as a database.
Regular `.md` files open in the markdown editor.