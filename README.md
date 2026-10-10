# Win-Search

A super fast, low-footprint desktop search bar and application launcher for Windows.

Win-Search is engineered for ultra-low memory consumption and instant query latency. It couples a native C engine for contiguous memory-mapped indexing, heuristic ranking, and direct binary disk serialization with a lightweight Python/Tkinter GUI shell.

---

## Performance

Verified via Windows Task Manager (idle and active search across 27,000+ indexed items):

- **Query Latency:** < 2 ms across 27,000+ files and applications (100% in-memory C execution).
- **Memory Footprint:** ~30 MB steady-state RAM in Windows Task Manager (0.5 MB PyInstaller bootstrapper + 30.3 MB runtime; ~47 MB peak during active background re-indexing).
- **Executable Size:** 18.3 MB standalone single-file binary (`dist/win-search.exe`, zero external dependencies).
- **Cold Boot Time:** ~15 ms via 1-shot binary disk cache read from SSD.
- **Idle CPU:** 0.0%.

---

## Download (Release v1.0.1)

Pre-compiled standalone executables are available on the [GitHub Releases](https://github.com/govindjnair/win-search/releases/latest) page.

No installation, Python runtime, or external compilers required:
1. Download [**`win-search.exe`**](https://github.com/govindjnair/win-search/releases/latest/download/win-search.exe) (18.3 MB) from the [**v1.0.1 Release**](https://github.com/govindjnair/win-search/releases/tag/v1.0.1).
2. Double-click to launch. It runs quietly in the system tray.
3. Press **`<Ctrl>+<Space>`** from anywhere in Windows to summon the search bar.

---

## Architecture & Technical Design

### System Overview

```
                     ┌───────────────────────────┐
                     │   Global Hotkey Daemon    │  <Ctrl>+<Space>
                     │     (pynput listener)     │
                     └─────────────┬─────────────┘
                                   │ Virtual Event (Thread-safe)
                                   ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │                        Tkinter GUI Shell                          │
 │  - Frameless Win32 window (0.94 alpha, SetForegroundWindow focus) │
 │  - Real-time keystroke dispatcher & dynamic expansion (70px/470px)│
 └─────────────────┬───────────────────────────────────┬─────────────┘
                   │                                   │
         Keystroke │ ctypes FFI               Spawns   │ Background
         Queries   │ (< 2 ms latency)         Worker   │ Daemon Thread
                   ▼                                   ▼
 ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
 │     Active SearchIndex (RAM)      │   │     Worker SearchIndex (RAM)      │
 │ ───────────────────────────────── │   │ ───────────────────────────────── │
 │ • Memory: Process RAM (~30 MB)    │   │ • Memory: Staged secondary buffer │
 │ • Layout: Flat SearchEntry array  │◀──│ • Mutex: Thread-safe pointer swap │
 │   (672B contiguous struct blocks) │   │ • Cleanup: index_free() old buffer│
 │ • Engine: Word-boundary scoring   │   │ • Concurrency: Zero UI freeze     │
 │ • Sorting: In-memory C qsort()    │   │                                   │
 └─────────────────▲─────────────────┘   └─────────────────┬─────────────────┘
                   │                                       │
     Cold Boot     │ 1-Shot fread                          │ 1-Shot fwrite
     Cache Load    │ (~15 ms directly into RAM)            │ (Disk serialization)
                   │                                       ▼
 ┌─────────────────┴─────────────────────────────────────────────────────────┐
 │                       Persistent Storage (SSD / Disk)                     │
 │ ───────────────────────────────────────────────────────────────────────── │
 │ • Binary Cache: %LOCALAPPDATA%\win_search\search_index.bin                │
 │   - Header [WSRC] + Count [size_t] + Contiguous Struct Payload            │
 │ • Filesystem Indexing: Start Menu, ProgramData, Desktop, User Documents   │
 │ • Windows Subsystem: UWP Applications via PowerShell (CREATE_NO_WINDOW)   │
 │ • Portable Executable: dist\win-search.exe (18.3 MB standalone on disk)   │
 └───────────────────────────────────────────────────────────────────────────┘
```

### 1. Contiguous In-Memory Layout (C Engine)

The index backend is written in C (`c_src/engine.c`, `c_src/engine.h`) using flat, packed structs:

```c
typedef struct {
    char title[128];
    char path[512];
    char category[32];
} SearchEntry; // 672 bytes per entry

typedef struct {
    SearchEntry *entries; // Contiguous dynamic array
    size_t count;
    size_t capacity;
} SearchIndex;
```

- **Cache Locality:** All index records are packed sequentially in a single contiguous memory block. Full index traversal exhibits optimal CPU L1/L2 cache prefetching, eliminating pointer chasing and heap fragmentation.
- **Minimal Footprint:** 27,000 indexed entries consume ~18 MB of raw C struct memory, keeping the entire process footprint under 48 MB RAM.

### 2. Scoring & Ranking Pipeline

Queries execute through the Python `ctypes` foreign function interface (FFI) directly into compiled C code (`index_search`):

1. **Filtering & Scoring:** Evaluates candidate records using integer arithmetic heuristics:
   - **Prefix Match:** `+100` points if `title` begins with the query.
   - **Exact Match:** `+100` bonus points if `title` length equals query length.
   - **Word-Boundary Match:** `+80` bonus points if query matches after a space delimiter (`" <query>"`).
   - **Substring Match:** `+50` points if found anywhere within `title`.
   - **Application Priority:** `+30` bonus points for application shortcuts.
   - **Installer Penalty:** `-60` points for setup and installer executables.
   - **Path Fallback:** `+10` points if matched only within the file path.
2. **Sorting:** Matching items are populated into a temporary `ScoredEntry` array and sorted via C standard library `qsort()` with a descending score comparator.
3. **Bounded Output:** Only the top `N` results (e.g. 5) are returned to the caller, bounding UI rendering overhead.

### 3. Single-Shot Binary Serialization (`WSRC`)

To achieve instant cold startup without re-scanning the filesystem:

- **Format:** The index is written to `%LOCALAPPDATA%\win_search\search_index.bin` using a raw binary dump:
  - 4-byte magic signature: `WSRC` (`0x57 0x53 0x52 0x43`)
  - 8-byte entry count: `sizeof(size_t)`
  - Raw payload: `count * sizeof(SearchEntry)` bytes
- **Disk I/O:** Serialized via a single `fwrite` call and restored via a single `fread` call directly into pre-allocated memory. Deserialization completes in ~15 ms.

### 4. Double-Buffered Concurrency

Filesystem and application crawling can take several seconds. To prevent UI lockups:

- Re-indexing runs in an isolated background thread, populating a new `SearchIndex` instance.
- Once indexing and binary serialization complete, the worker acquires a mutex (`threading.Lock`) and performs an atomic pointer swap.
- The previous index instance is deallocated via `index_free()` to prevent memory leaks or use-after-free conditions.

### 5. Win32 Platform Integration

- **`CreateMutexW` & `CreateEventW`:** Enforces single-instance execution. If a secondary instance is launched, it signals the primary instance to wake up and display the search bar, then terminates silently in < 3 ms.
- **`SetForegroundWindow`:** Bypasses Windows focus stealing prevention to ensure immediate keyboard focus when summoned via hotkey or second launch.
- **`Shell_NotifyIconW`:** Maintains a persistent background presence in the Windows notification area (`pystray`).
- **`CREATE_NO_WINDOW`:** Suppresses terminal flash when querying installed UWP packages via background PowerShell (`Get-StartApps`).
- **`ShellExecuteW`:** Launches selected binaries with UAC elevation via the `runas` verb on demand.

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + Space`** | Toggle search bar (global) |
| **`Enter`** | Launch selected application or open file |
| **`Ctrl + Enter`** | Open File Explorer with the item selected (`explorer.exe /select`) |
| **`Ctrl + Shift + Enter`** | Launch application as Administrator (UAC elevation) |
| **`Up / Down`** | Navigate result list |
| **`Escape`** | Dismiss launcher |

---

## Building from Source

### Prerequisites

- Windows 10 or 11
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- MinGW-w64 (`x86_64-w64-mingw32-gcc`, for compiling C source)

### 1. Compile the C Engine (`search_engine.dll`)
From WSL or a MinGW shell:
```bash
x86_64-w64-mingw32-gcc -shared -O3 -o search_engine.dll c_src/matcher.c c_src/engine.c c_src/crawler.c
```

### 2. Run in Development
From Windows PowerShell:
```powershell
uv sync
uv run win-search
```

### 3. Package Standalone Binary (`win-search.exe`)
From Windows PowerShell:
```powershell
uv run pyinstaller --noconsole --onefile --icon "assets/app_icon.ico" --add-binary "search_engine.dll;." --add-data "assets;assets" --name win-search run.py
```

The compiled binary is output to `dist/win-search.exe`. This standalone executable is what gets packaged for GitHub Releases.

