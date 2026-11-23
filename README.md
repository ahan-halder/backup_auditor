# backup_auditor

> Know exactly what changed in your folder since your last backup, before you copy anything.

`backup_auditor` is a small command-line tool that compares a local folder against its backup on an external drive and tells you which files are **new**, **modified**, **deleted**, **moved/renamed**, or **unchanged**. It can also keep a snapshot (manifest) of every backup, so you can audit changes even when the drive isn't plugged in.

---

## The problem

Backing up to an external HDD is easy. Knowing *what actually changed* since the last backup is not:

- Did I add new files I haven't backed up yet?
- Which files did I edit after the last backup?
- Did I rename or move folders, and will that cause duplicates?
- Did something get deleted locally that still exists on the drive (or vice versa)?
- Is any file on the drive corrupted or silently different?

Copy-pasting the whole folder is slow, and "replace if newer" prompts hide the real picture.

---

## Core idea

```
 Local folder  ─┐
                ├──►  scan + compare  ──►  audit report  ──►  (optional) sync
 Backup drive  ─┘          ▲
                           │
                  manifest snapshot (works offline)
```

1. **Scan** a folder and record each file's path, size, modified time, and content hash.
2. **Compare** two scans (local vs. backup, or local vs. last saved manifest).
3. **Report** the differences in a clear, readable summary.
4. **(Optional)** copy only what changed.

---

## Features

### MVP (v0.1)
- [ ] Recursive folder scan
- [ ] Compare local folder vs. backup folder
- [ ] Classify files: `NEW`, `MODIFIED`, `DELETED`, `UNCHANGED`
- [ ] Two comparison modes:
  - **fast**: size + modified time
  - **deep**: SHA-256 content hash
- [ ] Ignore rules (`.backupignore`: e.g. `node_modules/`, `*.tmp`, `.git/`)
- [ ] Terminal summary with counts and file lists

### v0.2: Manifests
- [ ] Save a manifest (JSON or SQLite) after each backup
- [ ] Audit local changes against the manifest **without the drive connected**
- [ ] Manifest history: see what changed between backup #3 and #4

### v0.3: Smarter detection
- [ ] **Move/rename detection** via matching hashes (avoids "deleted + new" noise)
- [ ] **Duplicate finder** (same hash, different paths)
- [ ] **Integrity check**: detect bit-rot or corruption on the drive by re-hashing

### v0.4: Action and reporting
- [ ] `sync` command: copy only new/modified files (with `--dry-run` by default)
- [ ] Export reports to HTML / CSV / Markdown
- [ ] Size summary: "1.2 GB to copy, 340 MB freed if deleted files are removed"
- [ ] Safe mode: never delete from the backup unless `--mirror` is passed

### Ideas for later
- Multiple backup targets (HDD 1, HDD 2, cloud folder)
- Simple GUI or web dashboard
- Scheduled audits and a reminder: "It's been 30 days since your last backup"
- Windows / macOS / Linux drive detection by volume label
- Versioning: keep old copies of modified files in an `_archive/` folder

---

## Proposed usage

```bash
# Compare a local folder against the backup drive
backup_auditor audit ~/Documents /media/me/MyHDD/Documents

# Use content hashes instead of timestamps (slower, more accurate)
backup_auditor audit ~/Documents /media/me/MyHDD/Documents --deep

# Save a snapshot after you finish a backup
backup_auditor snapshot ~/Documents --name "2026-11-backup"

# Audit against the last snapshot (drive not required)
backup_auditor audit ~/Documents --against-last-snapshot

# Preview what a sync would copy
backup_auditor sync ~/Documents /media/me/MyHDD/Documents --dry-run

# Export a report
backup_auditor audit ~/Documents /media/me/MyHDD/Documents --report report.html
```

### Example output

```
Backup Audit: ~/Documents  vs  /media/me/MyHDD/Documents
Mode: fast (size + mtime)

  NEW         14 files    (212 MB)
  MODIFIED     6 files    (38 MB)
  DELETED      2 files    (present on backup, missing locally)
  MOVED        3 files
  UNCHANGED  1,942 files

NEW
  + projects/resume_2026.pdf
  + photos/trip/IMG_0412.jpg
  ...

MODIFIED
  ~ notes/todo.md            (local newer by 2 days)
  ~ projects/budget.xlsx
  ...

MOVED
  > old_notes/ideas.txt  ->  notes/ideas.txt
```

---

## How it works

| Concept | Details |
|---|---|
| **File record** | `relative_path`, `size`, `mtime`, `sha256` (lazy; computed only when needed) |
| **Fast mode** | Compare size and mtime. Quick, but can miss edits that preserve both. |
| **Deep mode** | Compare SHA-256 hashes. Slow on large folders, but reliable. |
| **Hash cache** | Hashes are cached by `(path, size, mtime)` so repeated scans are fast. |
| **Manifest** | A snapshot of all file records plus a timestamp, stored locally and optionally on the drive in `.backup_auditor/`. |
| **Move detection** | A file "deleted" at path A and "new" at path B with the same hash is reported as moved. |

**Tip:** modified time on FAT32/exFAT drives has coarser precision (about 2 seconds on FAT). Allow a small tolerance when comparing timestamps.

---

## Suggested tech stack

- **Language:** Python 3.10+
- **CLI:** `argparse` or [`typer`](https://typer.tiangolo.com/)
- **Hashing:** `hashlib` (SHA-256, read in chunks)
- **Storage:** JSON to start, SQLite as the manifest grows
- **Output:** [`rich`](https://github.com/Textualize/rich) for colored terminal tables
- **Testing:** `pytest` with temporary directories

### Suggested project layout

```
backup_auditor/
├── README.md
├── pyproject.toml
├── .backupignore.example
├── src/
│   └── backup_auditor/
│       ├── __init__.py
│       ├── cli.py          # command-line entry point
│       ├── scanner.py      # walks folders, builds file records
│       ├── hasher.py       # chunked hashing + cache
│       ├── comparer.py     # diff logic (new/modified/deleted/moved)
│       ├── manifest.py     # save/load snapshots
│       ├── ignore.py       # .backupignore parsing
│       ├── report.py       # terminal / HTML / CSV output
│       └── sync.py         # optional copy of changed files
└── tests/
    ├── test_scanner.py
    ├── test_comparer.py
    └── test_manifest.py
```

---

## Installation (planned)

```bash
git clone https://github.com/<your-username>/backup_auditor.git
cd backup_auditor
pip install -e .
```

---

## Ignore file

Create a `.backupignore` in the folder you're auditing:

```
# comments are allowed
node_modules/
.git/
*.tmp
*.log
Thumbs.db
.DS_Store
```

---

## Safety principles

1. **Read-only by default.** `audit` never modifies anything.
2. **Dry run first.** `sync` previews changes unless you explicitly confirm.
3. **No silent deletes.** Files are only removed from the backup with an explicit `--mirror` flag.
4. **Hash before trust.** Deep mode exists so you can verify, not assume.

---

## Roadmap

| Version | Goal |
|---|---|
| 0.1 | Scan + compare + terminal report |
| 0.2 | Manifests and offline auditing |
| 0.3 | Move detection, duplicates, integrity checks |
| 0.4 | Sync, HTML/CSV reports |
| 1.0 | Stable CLI, tests, packaged release |

---

## Contributing

This is a personal project for now, but ideas and issues are welcome.

## License

MIT (or your choice)