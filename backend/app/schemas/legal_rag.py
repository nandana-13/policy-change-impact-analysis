from typing import List

from pydantic import BaseModel


class LegalRAGStatsResponse(BaseModel):
    total_chunks: int
    total_acts: int
    total_documents: int
    total_point_in_time_versions: int
    unique_version_dates: int
    total_chunk_ids: int
    acts: List[str]
    documents: List[str]
    version_dates: List[str]

class LegalRAGStatusResponse(BaseModel):
    status: str
    phase: str
    total_chunks: int
    embeddings_status: str
    vector_database_status: str


class LegalRAGSourceResponse(BaseModel):
    category: str
    act_title: str
    chunk_count: int
    document_count: int
    version_count: int
    earliest_version: str
    latest_version: str