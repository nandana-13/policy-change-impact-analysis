
from datetime import datetime, timezone
from typing import Any, Dict, List


class ExplainableRAGService:
    """
    PolicyLens Phase 6: deterministic, evidence-grounded explanations.

    Reuses impact-engine classifications and retrieved evidence.
    No LLM, Ollama, or additional package is required.
    """

    TEXT_FIELDS = (
        "content",
        "evidence",
        "evidence_text",
        "text",
        "document_text",
        "page_content",
        "description",
        "reason",
    )

    def __init__(self):
        self.provider = "Rule-based"
        self.model = None

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value

        if hasattr(value, "model_dump"):
            return value.model_dump()

        if hasattr(value, "__dict__"):
            return {
                key: val
                for key, val in vars(value).items()
                if not key.startswith("_")
            }

        return {}

    @classmethod
    def _get_text(cls, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()

        data = cls._as_dict(value)

        for field in cls.TEXT_FIELDS:
            text = data.get(field)

            if isinstance(text, str) and text.strip():
                return text.strip()

        return ""

    @staticmethod
    def _get_list(value: Any) -> List[Any]:
        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        if isinstance(value, dict):
            for key in ("items", "results", "evidence", "documents"):
                if isinstance(value.get(key), list):
                    return value[key]

        return []

    @staticmethod
    def _first_value(data: Dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = data.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        return ""

    def _make_source(
        self,
        source_id: str,
        source_type: str,
        value: Any,
        default_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        data = self._as_dict(value)
        text = self._get_text(value)

        metadata = dict(default_metadata or {})

        for key in (
            "policy_id",
            "policy_name",
            "version",
            "version_number",
            "document_id",
            "passage_id",
            "act_title",
            "section",
            "clause",
            "relationship_type",
            "source",
        ):
            if data.get(key) is not None:
                metadata[key] = data[key]

        return {
            "evidence_id": source_id,
            "source_type": source_type,
            "text": text,
            "metadata": metadata,
        }

    def explain(self, impact_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich the existing impact-engine response without changing
        its original impact classifications.
        """
        if not isinstance(impact_result, dict):
            raise ValueError("Impact engine result must be a dictionary.")

        legal_evidence = self._get_list(
            impact_result.get("legal_evidence", [])
        )

        impact_items = self._get_list(
            impact_result.get("impact_items", [])
        )

        evidence_sources = []
        legal_source_ids = []

        # Register retrieved legal evidence.
        for index, evidence in enumerate(legal_evidence, start=1):
            source = self._make_source(
                source_id=f"LEGAL-{index:03d}",
                source_type="legal",
                value=evidence,
            )

            if source["text"]:
                evidence_sources.append(source)
                legal_source_ids.append(source["evidence_id"])

        explained_items = []

        for index, original_item in enumerate(impact_items, start=1):
            item = self._as_dict(original_item)

            # Copy the original result so classifications and scores
            # are retained unchanged.
            explained = dict(item)

            policy_id = self._first_value(item, "policy_id") or f"UNKNOWN-{index}"
            policy_name = (
                self._first_value(item, "policy_name", "name")
                or policy_id
            )

            classification = (
                self._first_value(
                    item,
                    "impact_classification",
                    "classification",
                )
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            reason = self._first_value(
                item,
                "reason",
                "impact_reason",
            )

            expected_action = self._first_value(
                item,
                "expected_action",
                "recommended_action",
            )

            item_evidence_ids = list(legal_source_ids)
            policy_evidence = self._get_list(
                item.get("policy_evidence", [])
            )

            # Register policy evidence for this impact item.
            for evidence_index, evidence in enumerate(
                policy_evidence, start=1
            ):
                source = self._make_source(
                    source_id=(
                        f"POL-{index:03d}-{evidence_index:03d}"
                    ),
                    source_type="policy",
                    value=evidence,
                    default_metadata={
                        "policy_id": policy_id,
                        "policy_name": policy_name,
                    },
                )

                if source["text"]:
                    evidence_sources.append(source)
                    item_evidence_ids.append(source["evidence_id"])

            relationships = self._get_list(
                item.get("relationships", [])
            )

            # Relationships may be structured records without a
            # standalone text field. Describe only their stored data.
            for relationship_index, relationship in enumerate(
                relationships, start=1
            ):
                relationship_data = self._as_dict(relationship)

                relationship_text = self._get_text(relationship)

                if not relationship_text:
                    relation_type = self._first_value(
                        relationship_data,
                        "relationship_type",
                        "relation_type",
                        "type",
                    )
                    source_policy = self._first_value(
                        relationship_data,
                        "source_policy_name",
                        "source_policy_id",
                        "from_policy",
                    )
                    target_policy = self._first_value(
                        relationship_data,
                        "target_policy_name",
                        "target_policy_id",
                        "to_policy",
                    )

                    parts = [
                        part
                        for part in (
                            f"Relationship type: {relation_type}"
                            if relation_type else "",
                            f"Source policy: {source_policy}"
                            if source_policy else "",
                            f"Target policy: {target_policy}"
                            if target_policy else "",
                        )
                        if part
                    ]

                    relationship_text = "; ".join(parts)

                if relationship_text:
                    source_id = (
                        f"REL-{index:03d}-{relationship_index:03d}"
                    )

                    evidence_sources.append({
                        "evidence_id": source_id,
                        "source_type": "relationship",
                        "text": relationship_text,
                        "metadata": {
                            "policy_id": policy_id,
                            "policy_name": policy_name,
                        },
                    })

                    item_evidence_ids.append(source_id)

            # Produce explanations from existing classifications.
            if classification == "direct":
                explanation = (
                    f"{policy_name} was classified as a DIRECT impact "
                    "by the existing impact engine. "
                )

                if reason:
                    explanation += f"Recorded reason: {reason} "

                if policy_evidence:
                    explanation += (
                        "Retrieved policy evidence is available for "
                        "review against the regulatory change."
                    )
                else:
                    explanation += (
                        "No policy evidence excerpt was supplied for "
                        "this result, so the direct-impact rationale "
                        "requires further evidence review."
                    )

            elif classification == "indirect":
                explanation = (
                    f"{policy_name} was classified as an INDIRECT "
                    "impact by the existing impact engine. "
                )

                if relationships:
                    explanation += (
                        f"The engine returned {len(relationships)} "
                        "dependency relationship record(s). "
                    )
                else:
                    explanation += (
                        "No dependency relationship records were "
                        "included in this result. "
                    )

                if reason:
                    explanation += f"Recorded reason: {reason} "

                explanation += (
                    "Review the referenced relationships and policy "
                    "evidence to verify the indirect impact."
                )

            elif classification in ("no_impact", "none", "unaffected"):
                explanation = (
                    f"{policy_name} was classified as NO IMPACT by "
                    "the existing impact engine. "
                )

                if reason:
                    explanation += f"Recorded reason: {reason} "
                else:
                    explanation += (
                        "The engine did not provide a specific reason "
                        "for this classification. "
                    )

                explanation += (
                    "This is the engine's assessment based on its "
                    "current retrieval and classification results; "
                    "it is not proof that no impact is possible."
                )

            else:
                explanation = (
                    f"The impact engine returned classification "
                    f"'{classification or 'unspecified'}' for "
                    f"{policy_name}. Review the original result and "
                    "supporting evidence before drawing a conclusion."
                )

            explained["explainability"] = {
                "method": "deterministic_rules",
                "explanation": explanation,
                "evidence_ids": item_evidence_ids,
                "recorded_reason": reason or None,
                "expected_action": expected_action or None,
                "limitations": [
                    "The explanation uses existing engine outputs "
                    "and retrieved evidence; it does not independently "
                    "verify legal applicability.",
                    "A classification is not changed or re-evaluated "
                    "by this explanation layer.",
                ],
            }

            explained_items.append(explained)

        direct_count = sum(
            1 for item in explained_items
            if str(item.get("impact_classification", "")).lower()
            == "direct"
        )

        indirect_count = sum(
            1 for item in explained_items
            if str(item.get("impact_classification", "")).lower()
            == "indirect"
        )

        no_impact_count = sum(
            1 for item in explained_items
            if str(item.get("impact_classification", "")).lower()
            in ("no_impact", "none", "unaffected")
        )

        response = dict(impact_result)
        response["impact_items"] = explained_items
        response["explainability"] = {
            "method": "deterministic_rules",
            "provider": "None",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_summary": (
                f"The existing impact engine analysed "
                f"{len(explained_items)} impact item(s): "
                f"{direct_count} direct, {indirect_count} indirect, "
                f"and {no_impact_count} classified as no impact."
            ),
            "evidence_sources": evidence_sources,
            "limitations": [
                "No LLM is used to generate these explanations.",
                "Explanations are template-based and depend on the "
                "quality of existing retrieval and classification.",
                "Missing evidence is not inferred or fabricated.",
            ],
        }

        return response
