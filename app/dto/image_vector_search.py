from dataclasses import dataclass
from pathlib import Path


@dataclass
class VectorSearchRequest:
    image_id: int
    ora_path: Path

@dataclass
class VectorSearchResult:
    similar_path: Path
    vector_search_cost: float