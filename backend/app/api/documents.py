from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.policy import Policy
from app.models.policy_version import PolicyVersion
from app.models.policy_document import PolicyDocument
from app.schemas.policy_document import PolicyDocumentResponse


router = APIRouter(
    prefix="/policies",
    tags=["Policy Documents"],
)


# ============================================================
# STORAGE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

DOCUMENT_ROOT = BASE_DIR / "data" / "policy_documents"

DOCUMENT_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
}


def get_version(
    db: Session,
    policy_id: str,
    version_number: int,
):
    policy = (
        db.query(Policy)
        .filter(
            Policy.policy_id == policy_id
        )
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"Policy {policy_id} not found.",
        )

    version = (
        db.query(PolicyVersion)
        .filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.version_number == version_number,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Version V{version_number} "
                f"for {policy_id} not found."
            ),
        )

    return policy, version


def validate_file(file: UploadFile):

    if not file:
        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    filename = file.filename or ""

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF, TXT and Markdown files "
                "are allowed."
            ),
        )

    return extension


def build_document_path(
    policy_id: str,
    version_number: int,
    filename: str,
):
    version_directory = (
        DOCUMENT_ROOT
        / policy_id
        / f"V{version_number}"
    )

    version_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Generate a unique filename while preserving
    # the original extension.
    extension = Path(filename).suffix.lower()

    safe_filename = (
        f"{policy_id}_V{version_number}_"
        f"{uuid4().hex}{extension}"
    )

    return (
        version_directory,
        version_directory / safe_filename,
    )


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@router.post(
    "/{policy_id}/versions/{version_number}/document",
    response_model=PolicyDocumentResponse,
)
async def upload_document(
    policy_id: str,
    version_number: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate policy and version
    # --------------------------------------------------------

    policy, version = get_version(
        db,
        policy_id,
        version_number,
    )

    # --------------------------------------------------------
    # Validate uploaded file
    # --------------------------------------------------------

    extension = validate_file(file)

    # --------------------------------------------------------
    # Check whether a document already exists
    # --------------------------------------------------------

    existing = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.policy_id == policy_id,
            PolicyDocument.version_number == version_number,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A document already exists for "
                f"{policy_id} V{version_number}. "
                f"Use PUT to replace it."
            ),
        )

    # --------------------------------------------------------
    # Create storage location
    # --------------------------------------------------------

    version_directory, file_path = build_document_path(
        policy_id,
        version_number,
        file.filename,
    )

    # --------------------------------------------------------
    # Save physical file
    # --------------------------------------------------------

    try:

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save uploaded document: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Verify physical file
    # --------------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=500,
            detail="Document file was not created.",
        )

    file_size = file_path.stat().st_size

    # --------------------------------------------------------
    # Create database metadata
    # --------------------------------------------------------

    document_id = (
        f"DOC-{uuid4().hex}"
    )

    document = PolicyDocument(
        document_id=document_id,
        policy_id=policy_id,
        policy_version_id=version.policy_version_id,
        version_number=version_number,
        file_name=file.filename,
        file_path=str(file_path),
        content_type=(
            file.content_type
            or "application/octet-stream"
        ),
        file_size=file_size,
        synthetic=False,
    )

    try:

        db.add(document)

        db.commit()

        db.refresh(document)

    except Exception as exc:

        db.rollback()

        # Database insert failed, so don't leave
        # an orphaned physical file.
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document metadata could not be saved "
                f"to the database: {exc}"
            ),
        )

    return document


# ============================================================
# GET DOCUMENT METADATA
# ============================================================

@router.get(
    "/{policy_id}/versions/{version_number}/document",
    response_model=PolicyDocumentResponse,
)
def get_document(
    policy_id: str,
    version_number: int,
    db: Session = Depends(get_db),
):

    document = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.policy_id == policy_id,
            PolicyDocument.version_number == version_number,
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No uploaded document exists for "
                f"{policy_id} V{version_number}."
            ),
        )

    # --------------------------------------------------------
    # Also verify physical file exists
    # --------------------------------------------------------

    file_path = Path(document.file_path)

    if not file_path.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                "Document metadata exists in the database "
                "but the physical file is missing."
            ),
        )

    return document


# ============================================================
# VIEW / DOWNLOAD DOCUMENT
# ============================================================

@router.get(
    "/{policy_id}/versions/{version_number}/document/file"
)
def get_document_file(
    policy_id: str,
    version_number: int,
    db: Session = Depends(get_db),
):

    document = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.policy_id == policy_id,
            PolicyDocument.version_number == version_number,
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No document exists for "
                f"{policy_id} V{version_number}."
            ),
        )

    file_path = Path(document.file_path)

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="The document file does not exist on disk.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=document.content_type,
        filename=document.file_name,
        content_disposition_type="inline",
    )


# ============================================================
# REPLACE DOCUMENT
# ============================================================

@router.put(
    "/{policy_id}/versions/{version_number}/document",
    response_model=PolicyDocumentResponse,
)
async def replace_document(
    policy_id: str,
    version_number: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate policy/version
    # --------------------------------------------------------

    policy, version = get_version(
        db,
        policy_id,
        version_number,
    )

    validate_file(file)

    # --------------------------------------------------------
    # Find existing document
    # --------------------------------------------------------

    existing = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.policy_id == policy_id,
            PolicyDocument.version_number == version_number,
        )
        .first()
    )

    if not existing:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No document exists for "
                f"{policy_id} V{version_number}. "
                f"Use POST to upload a new document."
            ),
        )

    old_file_path = Path(
        existing.file_path
    )

    # --------------------------------------------------------
    # Create new file
    # --------------------------------------------------------

    version_directory, new_file_path = build_document_path(
        policy_id,
        version_number,
        file.filename,
    )

    try:

        with new_file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as exc:

        if new_file_path.exists():
            new_file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save replacement document: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Update database record
    # --------------------------------------------------------

    try:

        existing.file_name = file.filename
        existing.file_path = str(new_file_path)
        existing.content_type = (
            file.content_type
            or "application/octet-stream"
        )
        existing.file_size = new_file_path.stat().st_size

        db.commit()

        db.refresh(existing)

    except Exception as exc:

        db.rollback()

        if new_file_path.exists():
            new_file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update document metadata: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Delete old file after successful DB update
    # --------------------------------------------------------

    if (
        old_file_path.exists()
        and old_file_path != new_file_path
    ):
        try:
            old_file_path.unlink()
        except Exception:
            pass

    return existing


# ============================================================
# DELETE DOCUMENT
# ============================================================

@router.delete(
    "/{policy_id}/versions/{version_number}/document"
)
def delete_document(
    policy_id: str,
    version_number: int,
    db: Session = Depends(get_db),
):

    document = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.policy_id == policy_id,
            PolicyDocument.version_number == version_number,
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No document exists for "
                f"{policy_id} V{version_number}."
            ),
        )

    file_path = Path(
        document.file_path
    )

    # Delete physical file
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Could not delete document file: {exc}"
                ),
            )

    # Delete database row
    db.delete(document)

    db.commit()

    return {
        "message": (
            f"Document deleted successfully "
            f"from {policy_id} V{version_number}."
        )
    }