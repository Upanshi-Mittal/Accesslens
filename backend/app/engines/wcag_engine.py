
import asyncio
import json
from typing import List, Dict, Any, Optional
from axe_playwright_python.async_playwright import Axe as AsyncAxe
from axe_playwright_python.sync_playwright import Axe as SyncAxe
from ..models.schemas import (
    UnifiedIssue, IssueSeverity, IssueSource,
    ConfidenceLevel, WCAGCriteria, ElementLocation,
    RemediationSuggestion, EvidenceData, AuditRequest
)
from .base import BaseAccessibilityEngine
from ..core.scoring import SeverityMapper, ConfidenceCalculator
from ..core.config import settings

class WCAGEngine(BaseAccessibilityEngine):



    IMPACT_MAPPING = {
        "critical": IssueSeverity.CRITICAL,
        "serious": IssueSeverity.SERIOUS,
        "moderate": IssueSeverity.MODERATE,
        "minor": IssueSeverity.MINOR
    }

    def __init__(self):
        super().__init__("wcag_deterministic", "4.8.2")
        self.capabilities = ["wcag", "aria", "keyboard"]
        self.axe = AsyncAxe()

    async def analyze(
        self,
        page_data: Dict[str, Any],
        request: AuditRequest
    ) -> List[UnifiedIssue]:

        page = page_data.get("page")
        if not page:
            return []

        try:

            results = await self.axe.run(page)

            issues = []


            for violation in results.violations:
                issue = await self._convert_violation(violation)
                issues.append(issue)


                for incomplete in results.incomplete:
                    if incomplete.id == violation.id:
                        issue.confidence = ConfidenceLevel.LOW
                        issue.confidence_score = 50

            return issues

        except Exception as e:
            self._logger.error(f"WCAG analysis failed: {e}")
            return []

    async def _convert_violation(self, violation: Dict[str, Any]) -> UnifiedIssue:



        first_node = violation.nodes[0] if violation.nodes else {}


        wcag_criteria = []
        for tag in violation.tags:
            if tag.startswith("wcag"):

                wcag_id = tag[4] + "." + tag[5] + "." + tag[6]
                wcag_criteria.append(WCAGCriteria(
                    id=wcag_id,
                    level=violation.impact or "AA",
                    title=violation.help,
                    url=violation.helpUrl
                ))


        confidence_score = ConfidenceCalculator.calculate_confidence(
            "wcag_deterministic",
            settings.confidence_weights.get("wcag_deterministic", {
                "detection_reliability": 0.99,
                "context_clarity": 0.95,
                "pattern_match": 1.0,
                "evidence_quality": 0.95
            })
        )


        remediation = None
        if first_node.get("html"):
            remediation = RemediationSuggestion(
                description=f"Fix {violation.id}: {violation.help}",
                code_before=first_node.get("html"),
                code_after=self._suggest_fix(violation.id, first_node)
            )

        return UnifiedIssue(
            title=violation.help,
            description=violation.description,
            issue_type=violation.id,
            severity=self.IMPACT_MAPPING.get(
                violation.impact,
                IssueSeverity.MODERATE
            ),
            confidence=ConfidenceLevel.HIGH,
            confidence_score=confidence_score,
            source=IssueSource.WCAG_DETERMINISTIC,
            wcag_criteria=wcag_criteria,
            location=ElementLocation(
                selector=first_node.get("target", [""])[0],
                html=first_node.get("html"),
                node_index=0
            ),
            actual_value=first_node.get("html"),
            expected_value=self._get_expected_value(violation.id),
            remediation=remediation,
            evidence=EvidenceData(
                stack_trace=first_node.get("failureSummary"),
                dom_snapshot=first_node
            ),
            engine_name=self.name,
            engine_version=self.version,
            tags=violation.tags
        )

    def _suggest_fix(self, rule_id: str, node: Dict) -> str:

        fixes = {
            "image-alt": f'<img src="{node.get("html", "").split("src=")[1].split(" ")[0] if "src=" in node.get("html", "") else ""}" alt="Descriptive text">',
            "button-name": f'<button>{node.get("html", "").replace("<button", "").replace(">", "").replace("</button>", "")}</button>',
            "link-name": f'<a href="{node.get("html", "").split("href=")[1].split(" ")[0] if "href=" in node.get("html", "") else "#"}">Link Text</a>'
        }
        return fixes.get(rule_id, "Review element structure")

    def _get_expected_value(self, rule_id: str) -> str:

        expectations = {
            "image-alt": "Image should have alt attribute with descriptive text",
            "button-name": "Button should have accessible name via text content, aria-label, or aria-labelledby",
            "link-name": "Link should have discernible text",
            "heading-order": "Headings should not skip levels"
        }
        return expectations.get(rule_id, "Follow WCAG guidelines")

    async def validate_config(self) -> bool:

        try:

            from axe_playwright_python import Axe
            return True
        except ImportError:
            return False