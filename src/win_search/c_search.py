
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

        #create the in-memory C index
        self._idx = self.dll.index_create(1024)

        # Crawl Start Menus, Desktop, and user directories into RAM!
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

    def _crawl_locations(self):
        """Crawls Windows Start Menus, Desktop, and common user folders into RAM."""
        locations = [
            # 1. Start Menus (Installed Apps)
            (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs", 3),
            (os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"), 3),

            # 2. Desktops (User & Public)
            (os.path.expandvars(r"%USERPROFILE%\Desktop"), 7),
            (r"C:\Users\Public\Desktop", 2),

            # 3. User Folders (Documents & Downloads)
            (os.path.expandvars(r"%USERPROFILE%\Documents"), 6),
            (os.path.expandvars(r"%USERPROFILE%\Downloads"), 2),
        ]

        total = 0
        for folder, depth in locations:
            if os.path.exists(folder):
                added = self.dll.crawl_directory(self._idx, folder.encode("utf-8"), depth)
                total += added

        print(f"⚡ C search engine indexed {total} items into RAM!")

    def search(self, query:str, limit:int = 8) -> List[SearchResult]:
        if not self._idx:
            return []

        #allocate a temp C array of SearchEntryC structs
        results_array = (SearchEntryC * limit)()

        #call the C search function
        count = self.dll.index_search(self._idx, query.encode("utf-8"), results_array, limit)

        #convert C structs back into Python SearchResult objects
        py_results = []
        for i in range(count):
            c_entry = results_array[i]
            #strip the .lnk shortcut extension from app titles for clean display
            title = c_entry.title.decode("utf-8", errors="ignore")
            if title.endswith(".lnk"):
                title = title[:-4]
            py_results.append(SearchResult(
                title=title,
                path=c_entry.path.decode("utf-8", errors="ignore"),
                category=c_entry.category.decode("utf-8", errors="ignore")
            ))
        return py_results
        
    def __del__(self):
        if hasattr(self, "_idx") and self._idx:
            self.dll.index_free(self._idx)
            self._idx = None
                    

        


    
