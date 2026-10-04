from typing import List
from .search_interface import SearchResult, SearchEngine

class MockSearchEngine(SearchEngine):
    """
    A temporary mock search engine with common Windows apps and demo files.
    This will be replaced by the high-performance C engine!
    """
    def __init__(self):
        self._sample_data = [
            SearchResult(title="Notepad", path=r"C:\Windows\System32\notepad.exe", category="App"),
            SearchResult(title="Calculator", path=r"calc.exe", category="App"),
            SearchResult(title="Command Prompt", path=r"C:\Windows\System32\cmd.exe", category="App"),
            SearchResult(title="PowerShell", path=r"powershell.exe", category="App"),
            SearchResult(title="File Explorer", path=r"explorer.exe", category="App"),
            SearchResult(title="Task Manager", path=r"taskmgr.exe", category="App"),
            SearchResult(title="Registry Editor", path=r"regedit.exe", category="App"),
            SearchResult(title="Projects Folder", path=r"C:\Users\Govind J Nair\Documents\projects", category="Folder"),
            SearchResult(title="Search Project Source", path=r"C:\Users\Govind J Nair\Documents\projects\win_search", category="Folder"),
        ]

    def search(self, query: str, limit: int = 8) -> List[SearchResult]:
        if not query.strip():
            # If query is empty, return top default items
            return self._sample_data[:limit]

        query_lower = query.lower()
        matches = [
            item for item in self._sample_data
            if query_lower in item.title.lower() or query_lower in item.path.lower()
        ]
        return matches[:limit]
