
import os
import ctypes
from pathlib import Path
from typing import List
from .search_interface import SearchEngine, SearchResult

#mirror C searchentry struct in python

class SearchEntryC(ctypes.Structure):
    _fields_ = [
        ("title", ctypes.c_char * 128),
        ("path", ctypes.c_char * 512),
        ("category", ctypes.c_char * 32)
    ]

class CSearchEngine(SearchEngine):
    def __init__(self):
        #locate our search_engine.dll in the project root
        dll_path = Path(__file__).resolve().parents[2]/"search_engine.dll"
        if not dll_path.exists():
            raise FileNotFoundError(f"Could not find DLL at: {dll_path}")
        
        # load the C shared library
        self.dll = ctypes.CDLL(str(dll_path))
        self._setup_c_signatures()

        # Create the in-memory C index
        self._idx = self.dll.index_create(2048)

        # 1. Index Microsoft Store and UWP packaged apps (Calculator, WhatsApp, Terminal, etc.)
        self._crawl_windows_store_apps()

        # 2. Crawl Start Menus, Desktop, and user directories into RAM!
        self._crawl_locations()
    
    def _setup_c_signatures(self):
        """Define C function arguments and return types for type safety"""

        # SearchIndex *index_create(size_t initial_capacity)
        self.dll.index_create.argtypes = [ctypes.c_size_t]
        self.dll.index_create.restype = ctypes.c_void_p

        # void index_free(SearchIndex *idx)
        self.dll.index_free.argtypes = [ctypes.c_void_p]
        self.dll.index_free.restype = None

        # int index_add(SearchIndex *idx, const char *title, const char *path, const char *category)
        self.dll.index_add.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.dll.index_add.restype = ctypes.c_int

        # int index_search(const SearchIndex *idx, const char *query, SearchEntry *results, int max_results)
        self.dll.index_search.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(SearchEntryC), ctypes.c_int]
        self.dll.index_search.restype = ctypes.c_int

        # int crawl_directory(SearchIndex *idx, const char *dir_path, int max_depth)
        self.dll.crawl_directory.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.dll.crawl_directory.restype = ctypes.c_int

    def _crawl_windows_store_apps(self):
        """Indexes Microsoft Store and UWP packaged apps (Calculator, WhatsApp, Settings, etc.)"""
        try:
            import subprocess
            import json
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0 and proc.stdout.strip():
                apps = json.loads(proc.stdout)
                if isinstance(apps, dict):
                    apps = [apps]

                count = 0
                for item in apps:
                    name = item.get("Name")
                    app_id = item.get("AppID")
                    if not name or not app_id:
                        continue

                    # If already an absolute path, use it directly; otherwise launch via shell:AppsFolder
                    path = app_id if ":\\" in app_id else f"shell:AppsFolder\\{app_id}"

                    self.dll.index_add(
                        self._idx,
                        name.encode("utf-8"),
                        path.encode("utf-8"),
                        b"App"
                    )
                    count += 1
                print(f"📦 Indexed {count} Windows Store & Packaged apps!")
        except Exception as e:
            print(f"Note: Could not query Get-StartApps: {e}")

    def _crawl_locations(self):
        """Crawls Windows Start Menus, Desktop, and common user folders into RAM."""
        locations = [
            # 1. Start Menus (Installed Apps)
            (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs", 3),
            (os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"), 3),

            # 2. Windows Store Execution Aliases (wt.exe, etc.)
            (os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps"), 1),

            # 3. Desktops (User & Public)
            (os.path.expandvars(r"%USERPROFILE%\Desktop"), 7),
            (r"C:\Users\Public\Desktop", 2),

            # 4. User Folders (Documents & Downloads)
            (os.path.expandvars(r"%USERPROFILE%\Documents"), 6),
            (os.path.expandvars(r"%USERPROFILE%\Downloads"), 2),
        ]

        total = 0
        for folder, depth in locations:
            if os.path.exists(folder):
                added = self.dll.crawl_directory(self._idx, folder.encode("utf-8"), depth)
                total += added

        print(f"⚡ C search engine indexed {total} files into RAM!")

    def search(self, query: str, limit: int = 8) -> List[SearchResult]:
        if not self._idx:
            return []

        # Request more raw results from C so we still have enough after deduplication
        raw_limit = limit * 2
        results_array = (SearchEntryC * raw_limit)()

        # Call the C search function
        count = self.dll.index_search(self._idx, query.encode("utf-8"), results_array, raw_limit)

        # Convert C structs back into Python SearchResult objects with deduplication
        py_results = []
        seen_titles = set()

        for i in range(count):
            c_entry = results_array[i]
            title = c_entry.title.decode("utf-8", errors="ignore")
            if title.endswith(".lnk"):
                title = title[:-4]

            # Deduplicate items with identical titles (e.g. Chrome on Desktop + Start Menu)
            norm_title = title.strip().lower()
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)

            py_results.append(SearchResult(
                title=title,
                path=c_entry.path.decode("utf-8", errors="ignore"),
                category=c_entry.category.decode("utf-8", errors="ignore")
            ))

            if len(py_results) >= limit:
                break

        return py_results

    def __del__(self):
        if hasattr(self, "_idx") and self._idx:
            self.dll.index_free(self._idx)
            self._idx = None
                    

        


    
