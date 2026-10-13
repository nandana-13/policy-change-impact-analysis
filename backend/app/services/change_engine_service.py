from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.models.policy_document import PolicyDocument
from app.models.policy_version import PolicyVersion


class ChangeEngineService:
    """
    PolicyLens Phase 4 - Policy Change Engine.

    Responsibilities
    ----------------
    1. Load two versions of the same policy.
    2. Locate their uploaded policy documents.
    3. Extract document text.
    4. Parse the documents into logical sections.
    5. Compare sections between versions.
    6. Classify changes as:
         - added
         - removed
         - modified
         - unchanged
    7. Return structured, evidence-backed comparison results.

    This service does NOT:
        - analyze regulatory changes
        - determine direct/indirect impact
        - traverse policy dependencies
        - retrieve legal evidence
        - generate LLM explanations

    Those belong to later phases.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".md",
        ".markdown",
    }

    # A section is considered unchanged if its normalized similarity
    # is at or above this value.
    UNCHANGED_THRESHOLD = 0.98

    # Very small text fragments are treated as unchanged when their
    # normalized content is identical.
    MIN_SECTION_LENGTH = 5

    def __init__(self) -> None:
        pass

    # ==============================================================
    # DATABASE
    # ==============================================================

    def get_policy(
        self,
        db: Session,
        policy_id: str,
    ) -> Optional[Policy]:
        return (
            db.query(Policy)
            .filter(
                Policy.policy_id == policy_id
            )
            .first()
        )

    def get_version(
        self,
        db: Session,
        policy_id: str,
        version_number: int,
    ) -> Optional[PolicyVersion]:
        return (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.version_number == version_number,
            )
            .first()
        )

    def get_document(
        self,
        db: Session,
        policy_id: str,
        version_number: int,
    ) -> Optional[PolicyDocument]:
        return (
            db.query(PolicyDocument)
            .filter(
                PolicyDocument.policy_id == policy_id,
                PolicyDocument.version_number == version_number,
            )
            .first()
        )

    # ==============================================================
    # FILE PATH
    # ==============================================================

    @staticmethod
    def resolve_file_path(
        file_path: str,
    ) -> Path:
        """
        Resolve the stored document path.

        The document API may store either an absolute path or a path
        relative to the project root.
        """

        path = Path(file_path)

        if path.is_absolute():
            return path

        candidates = [
            path,
            Path.cwd() / path,
            Path.cwd() / "backend" / path,
            Path.cwd().parent / path,
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        # Return the first sensible path even when it does not exist.
        return (Path.cwd() / path).resolve()

    # ==============================================================
    # DOCUMENT EXTRACTION
    # ==============================================================

    def extract_document_text(
        self,
        document: PolicyDocument,
    ) -> str:
        """
        Extract plain text from a stored policy document.
        """

        file_path = self.resolve_file_path(
            document.file_path
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"Policy document file was not found: "
                f"{file_path}"
            )

        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported policy document format: "
                f"{suffix}"
            )

        if suffix == ".pdf":
            return self._extract_pdf_text(file_path)

        return self._extract_text_file(file_path)

    @staticmethod
    def _extract_text_file(
        file_path: Path,
    ) -> str:
        """
        Read TXT or Markdown files.
        """

        encodings = [
            "utf-8",
            "utf-8-sig",
            "cp1252",
        ]

        last_error: Optional[Exception] = None

        for encoding in encodings:
            try:
                return file_path.read_text(
                    encoding=encoding
                )
            except UnicodeDecodeError as exc:
                last_error = exc

        raise ValueError(
            f"Unable to decode policy document: "
            f"{file_path}"
        ) from last_error

    @staticmethod
    def _extract_pdf_text(
        file_path: Path,
    ) -> str:
        """
        Extract text from PDF using pypdf.
        """

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "PDF support requires pypdf. "
                "Install it using: pip install pypdf"
            ) from exc

        reader = PdfReader(
            str(file_path)
        )

        pages: List[str] = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)

    # ==============================================================
    # TEXT NORMALIZATION
    # ==============================================================

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:
        """
        Normalize text for comparison without destroying the
        original evidence.
        """

        if not text:
            return ""

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        # Remove excessive whitespace.
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Normalize excessive blank lines.
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    @staticmethod
    def comparison_text(
        text: str,
    ) -> str:
        """
        More aggressive normalization used only for similarity
        calculation.
        """

        text = ChangeEngineService.normalize_text(
            text
        )

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ==============================================================
    # SECTION DETECTION
    # ==============================================================

    @staticmethod
    def _is_markdown_heading(
        line: str,
    ) -> Optional[str]:
        """
        Detect Markdown headings:

            # Purpose
            ## Scope
            ### Policy Requirements
        """

        match = re.match(
            r"^\s{0,3}#{1,6}\s+(.+?)\s*$",
            line,
        )

        if not match:
            return None

        return match.group(1).strip()

    @staticmethod
    def _is_numbered_heading(
        line: str,
    ) -> Optional[str]:
        """
        Detect common policy heading formats:

            1. Purpose
            2. Scope
            4. Policy Requirements
            10. Document Control
        """

        match = re.match(
            r"^\s*(\d{1,3}(?:\.\d{1,3})*)\s*[.)-]\s+(.+?)\s*$",
            line,
        )

        if not match:
            return None

        number = match.group(1)
        title = match.group(2).strip()

        # Avoid treating numbered list items as headings.
        if len(title) > 120:
            return None

        return f"{number}. {title}"

    @staticmethod
    def _is_plain_heading(
        line: str,
    ) -> Optional[str]:
        """
        Detect simple standalone policy headings.

        Examples:
            Purpose
            Scope
            Definitions
            Roles and Responsibilities
        """

        stripped = line.strip()

        if not stripped:
            return None

        if len(stripped) > 100:
            return None

        known_headings = {
            "purpose",
            "scope",
            "definitions",
            "policy requirements",
            "roles and responsibilities",
            "records and evidence",
            "exceptions and escalation",
            "monitoring and review",
            "related policies and controls",
            "version change summary",
            "document control",
            "policy owner",
            "responsibilities",
        }

        if stripped.lower() in known_headings:
            return stripped

        return None

    def parse_sections(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:
        """
        Convert a policy document into ordered sections.

        The parser supports:
            - Markdown headings
            - numbered headings
            - known standalone policy headings

        If no headings are detected, the complete document is
        represented as one section called "Document Content".
        """

        text = self.normalize_text(text)

        if not text:
            return []

        lines = text.splitlines()

        sections: List[Dict[str, Any]] = []

        current_title: Optional[str] = None
        current_lines: List[str] = []

        def flush_section() -> None:
            nonlocal current_title
            nonlocal current_lines

            if current_title is None:
                return

            content = self.normalize_text(
                "\n".join(current_lines)
            )

            sections.append(
                {
                    "title": current_title,
                    "text": content,
                    "index": len(sections) + 1,
                }
            )

            current_title = None
            current_lines = []

        for line in lines:
            heading = (
                self._is_markdown_heading(line)
                or self._is_numbered_heading(line)
                or self._is_plain_heading(line)
            )

            if heading:
                flush_section()

                current_title = heading
                current_lines = []

                continue

            if current_title is None:
                # Content before the first heading.
                current_title = "Document Introduction"

            current_lines.append(line)

        flush_section()

        # If parsing somehow produced nothing, preserve the
        # document as a single section.
        if not sections:
            sections.append(
                {
                    "title": "Document Content",
                    "text": text,
                    "index": 1,
                }
            )

        # Remove completely empty sections.
        sections = [
            section
            for section in sections
            if section["text"].strip()
            or section["title"].strip()
        ]

        return sections

    # ==============================================================
    # SECTION SIMILARITY
    # ==============================================================

    @classmethod
    def calculate_similarity(
        cls,
        old_text: str,
        new_text: str,
    ) -> float:
        old_normalized = cls.comparison_text(
            old_text
        )

        new_normalized = cls.comparison_text(
            new_text
        )

        if not old_normalized and not new_normalized:
            return 1.0

        if old_normalized == new_normalized:
            return 1.0

        return round(
            SequenceMatcher(
                None,
                old_normalized,
                new_normalized,
            ).ratio(),
            4,
        )

    # ==============================================================
    # SECTION MATCHING
    # ==============================================================

    @staticmethod
    def _section_key(
        title: str,
    ) -> str:
        """
        Normalize section titles for matching.
        """

        title = title.lower().strip()

        # Normalize numbered prefixes.
        title = re.sub(
            r"^\d+(?:\.\d+)*[.)-]?\s*",
            "",
            title,
        )

        title = re.sub(
            r"[^a-z0-9]+",
            " ",
            title,
        )

        title = re.sub(
            r"\s+",
            " ",
            title,
        )

        return title.strip()

    def match_sections(
        self,
        old_sections: List[Dict[str, Any]],
        new_sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Match sections primarily by normalized title.

        This makes the engine robust when section ordering changes.
        """

        old_by_key: Dict[
            str,
            Dict[str, Any],
        ] = {}

        new_by_key: Dict[
            str,
            Dict[str, Any],
        ] = {}

        for section in old_sections:
            old_by_key[
                self._section_key(
                    section["title"]
                )
            ] = section

        for section in new_sections:
            new_by_key[
                self._section_key(
                    section["title"]
                )
            ] = section

        all_keys = list(
            dict.fromkeys(
                list(old_by_key.keys())
                + list(new_by_key.keys())
            )
        )

        matches: List[Dict[str, Any]] = []

        for key in all_keys:
            old_section = old_by_key.get(key)
            new_section = new_by_key.get(key)

            if old_section and new_section:
                matches.append(
                    {
                        "match_key": key,
                        "old": old_section,
                        "new": new_section,
                    }
                )

            elif old_section:
                matches.append(
                    {
                        "match_key": key,
                        "old": old_section,
                        "new": None,
                    }
                )

            elif new_section:
                matches.append(
                    {
                        "match_key": key,
                        "old": None,
                        "new": new_section,
                    }
                )

        return matches

    # ==============================================================
    # CHANGE CLASSIFICATION
    # ==============================================================

    def classify_change(
        self,
        old_section: Optional[Dict[str, Any]],
        new_section: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if old_section is None and new_section is not None:
            return {
                "change_type": "added",
                "similarity": 0.0,
                "old_text": None,
                "new_text": new_section["text"],
            }

        if old_section is not None and new_section is None:
            return {
                "change_type": "removed",
                "similarity": 0.0,
                "old_text": old_section["text"],
                "new_text": None,
            }

        if old_section is None or new_section is None:
            return {
                "change_type": "modified",
                "similarity": 0.0,
                "old_text": (
                    old_section["text"]
                    if old_section
                    else None
                ),
                "new_text": (
                    new_section["text"]
                    if new_section
                    else None
                ),
            }

        similarity = self.calculate_similarity(
            old_section["text"],
            new_section["text"],
        )

        old_comparison = self.comparison_text(
            old_section["text"]
        )

        new_comparison = self.comparison_text(
            new_section["text"]
        )

        if (
            old_comparison == new_comparison
            or similarity >= self.UNCHANGED_THRESHOLD
        ):
            change_type = "unchanged"
        else:
            change_type = "modified"

        return {
            "change_type": change_type,
            "similarity": similarity,
            "old_text": old_section["text"],
            "new_text": new_section["text"],
        }

    # ==============================================================
    # COMPLETE COMPARISON
    # ==============================================================

    def compare_versions(
        self,
        db: Session,
        policy_id: str,
        old_version_number: int,
        new_version_number: int,
    ) -> Dict[str, Any]:
        """
        Compare two versions of a policy.
        """

        if (
            old_version_number
            == new_version_number
        ):
            raise ValueError(
                "Old and new versions must be different."
            )

        policy = self.get_policy(
            db,
            policy_id,
        )

        if policy is None:
            raise LookupError(
                f"Policy '{policy_id}' was not found."
            )

        old_version = self.get_version(
            db,
            policy_id,
            old_version_number,
        )

        if old_version is None:
            raise LookupError(
                f"Version V{old_version_number} "
                f"was not found for policy "
                f"'{policy_id}'."
            )

        new_version = self.get_version(
            db,
            policy_id,
            new_version_number,
        )

        if new_version is None:
            raise LookupError(
                f"Version V{new_version_number} "
                f"was not found for policy "
                f"'{policy_id}'."
            )

        old_document = self.get_document(
            db,
            policy_id,
            old_version_number,
        )

        if old_document is None:
            raise LookupError(
                f"No uploaded document exists for "
                f"{policy_id} V{old_version_number}."
            )

        new_document = self.get_document(
            db,
            policy_id,
            new_version_number,
        )

        if new_document is None:
            raise LookupError(
                f"No uploaded document exists for "
                f"{policy_id} V{new_version_number}."
            )

        old_text = self.extract_document_text(
            old_document
        )

        new_text = self.extract_document_text(
            new_document
        )

        old_sections = self.parse_sections(
            old_text
        )

        new_sections = self.parse_sections(
            new_text
        )

        matches = self.match_sections(
            old_sections,
            new_sections,
        )

        changes: List[Dict[str, Any]] = []

        counts = {
            "added": 0,
            "removed": 0,
            "modified": 0,
            "unchanged": 0,
        }

        for match in matches:
            old_section = match["old"]
            new_section = match["new"]

            result = self.classify_change(
                old_section,
                new_section,
            )

            change_type = result[
                "change_type"
            ]

            counts[change_type] += 1

            title = (
                new_section["title"]
                if new_section
                else old_section["title"]
            )

            changes.append(
                {
                    "section": title,
                    "old_section": (
                        old_section["title"]
                        if old_section
                        else None
                    ),
                    "new_section": (
                        new_section["title"]
                        if new_section
                        else None
                    ),
                    "change_type": change_type,
                    "similarity": result[
                        "similarity"
                    ],
                    "old_text": result[
                        "old_text"
                    ],
                    "new_text": result[
                        "new_text"
                    ],
                }
            )

        total_sections = len(changes)

        changed_sections = (
            counts["added"]
            + counts["removed"]
            + counts["modified"]
        )

        if total_sections:
            change_percentage = round(
                (
                    changed_sections
                    / total_sections
                )
                * 100,
                2,
            )
        else:
            change_percentage = 0.0

        return {
            "policy": {
                "policy_id": policy.policy_id,
                "policy_name": getattr(
                    policy,
                    "policy_name",
                    None,
                )
                or getattr(
                    policy,
                    "name",
                    None,
                ),
            },
            "comparison": {
                "old_version": {
                    "version_number": (
                        old_version.version_number
                    ),
                    "policy_version_id": (
                        old_version.policy_version_id
                    ),
                    "effective_date": (
                        old_version.effective_date
                    ),
                    "status": (
                        old_version.status
                    ),
                    "document_id": (
                        old_document.document_id
                    ),
                    "file_name": (
                        old_document.file_name
                    ),
                },
                "new_version": {
                    "version_number": (
                        new_version.version_number
                    ),
                    "policy_version_id": (
                        new_version.policy_version_id
                    ),
                    "effective_date": (
                        new_version.effective_date
                    ),
                    "status": (
                        new_version.status
                    ),
                    "document_id": (
                        new_document.document_id
                    ),
                    "file_name": (
                        new_document.file_name
                    ),
                },
            },
            "summary": {
                "total_sections": total_sections,
                "added": counts["added"],
                "removed": counts["removed"],
                "modified": counts["modified"],
                "unchanged": counts["unchanged"],
                "changed_sections": changed_sections,
                "change_percentage": change_percentage,
            },
            "changes": changes,
        }


# Singleton service instance.

_change_engine_service: Optional[
    ChangeEngineService
] = None


def get_change_engine_service() -> ChangeEngineService:
    global _change_engine_service

    if _change_engine_service is None:
        _change_engine_service = (
            ChangeEngineService()
        )

    return _change_engine_service