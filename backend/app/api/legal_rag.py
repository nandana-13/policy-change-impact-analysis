from fastapi import APIRouter, HTTPException

from app.schemas.legal_rag import (
    LegalRAGStatsResponse,
    LegalRAGStatusResponse,
    LegalRAGSourceResponse,
)

from app.services.legal_rag_service import (
    get_stats,
    get_status,
    get_sources,
)


router = APIRouter(
    prefix="/legal-rag",
    tags=["Legal RAG"],
)


@router.get(
    "/stats",
    response_model=LegalRAGStatsResponse,
)
def legal_rag_stats():
    """
    Return statistics about the processed legal corpus.
    """

    try:
        return get_stats()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/status",
    response_model=LegalRAGStatusResponse,
)
def legal_rag_status():
    """
    Return current Legal RAG processing status.
    """

    try:
        return get_status()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/sources",
    response_model=list[LegalRAGSourceResponse],
)
def legal_rag_sources():
    """
    Return statistics grouped by legal Act.
    """

    try:
        return get_sources()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )