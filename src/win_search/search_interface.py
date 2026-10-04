from dataclasses import dataclass
from typing import Protocol, List

@dataclass
class SearchResult:
    title: str
    path: str
    category: str = "File"

    def display_text(self) -> str:
        return f"[{self.category.upper()}]  {self.title}  —  {self.path}"

class SearchEngine(Protocol):
    """Protocol that any search backend (Python mock or C shared library) must implement."""
    def search(self, query: str, limit: int = 8) -> List[SearchResult]:
        ...
