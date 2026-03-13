
from typing import List, Dict, Any, Optional
import asyncio
import logging
import base64
from dataclasses import dataclass
import json

from ..models.schemas import (
    UnifiedIssue, IssueSource, ConfidenceLevel,
    RemediationSuggestion, EvidenceData, WCAGCriteria
)
from ..core.scoring import ConfidenceCalculator

@dataclass
class AIConfig:

    llava_endpoint: str = "http://localhost:8001"
    mistral_endpoint: str = "http://localhost:8002"
    use_local: bool = True
    model_path: Optional[str] = None
    confidence_threshold: float = 0.7

class AIService:


    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self._logger = logging.getLogger(__name__)

    async def analyze(
        self,
        screenshot: str,
        dom_snapshot: Dict[str, Any],
        existing_issues: List[UnifiedIssue]
    ) -> List[UnifiedIssue]:

        ai_issues = []

        try:

            vision_issues = await self._run_vision_analysis(
                screenshot,
                dom_snapshot
            )
            ai_issues.extend(vision_issues)


            all_issues = existing_issues + vision_issues


            if all_issues:
                await self._generate_code_fixes(all_issues, dom_snapshot)

            return ai_issues

        except Exception as e:
            self._logger.error(f"AI analysis failed: {e}")
            return []

    async def _run_vision_analysis(
        self,
        screenshot: str,
        dom_snapshot: Dict[str, Any]
    ) -> List[UnifiedIssue]:

        issues = []


        vision_prompt = self._build_vision_prompt(dom_snapshot)

        if self.config.use_local:

            vision_result = await self._call_local_llava(
                screenshot,
                vision_prompt
            )
        else:

            vision_result = await self._call_llava_api(
                screenshot,
                vision_prompt
            )

        if vision_result:

            vision_issues = self._parse_vision_results(vision_result)
            issues.extend(vision_issues)

        return issues

    async def _generate_code_fixes(
        self,
        issues: List[UnifiedIssue],
        dom_snapshot: Dict[str, Any]
    ) -> None:


        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)


        for issue_type, type_issues in issues_by_type.items():

            sample_issue = type_issues[0]


            context = self._build_fix_context(sample_issue, dom_snapshot)


            if self.config.use_local:
                fix_result = await self._call_local_mistral(context)
            else:
                fix_result = await self._call_mistral_api(context)

            if fix_result:

                for issue in type_issues:
                    issue.remediation = self._parse_fix_result(
                        fix_result,
                        sample_issue.location.selector if sample_issue.location else None
                    )

    def _build_vision_prompt(self, dom_snapshot: Dict) -> str:

        return f

    def _build_fix_context(
        self,
        issue: UnifiedIssue,
        dom_snapshot: Dict
    ) -> str:



        surrounding_html = ""
        if issue.location and issue.location.selector:

            surrounding_html = f"Element: {issue.location.html or 'unknown'}"

        return f

    async def _call_local_llava(
        self,
        screenshot: str,
        prompt: str
    ) -> Optional[Dict]:

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.llava_endpoint}/analyze",
                    json={
                        "image": screenshot,
                        "prompt": prompt,
                        "temperature": 0.1
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._logger.error(f"LLaVA error: {response.status}")
                        return None
        except Exception as e:
            self._logger.error(f"Failed to call LLaVA: {e}")
            return None

    async def _call_local_mistral(
        self,
        context: str
    ) -> Optional[Dict]:

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.mistral_endpoint}/generate",
                    json={
                        "prompt": context,
                        "max_tokens": 500,
                        "temperature": 0.3,
                        "format": "json"
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._logger.error(f"Mistral error: {response.status}")
                        return None
        except Exception as e:
            self._logger.error(f"Failed to call Mistral: {e}")
            return None

    async def _call_llava_api(self, screenshot: str, prompt: str) -> Optional[Dict]:


        self._logger.warning("Cloud LLaVA not implemented")
        return None

    async def _call_mistral_api(self, context: str) -> Optional[Dict]:


        self._logger.warning("Cloud Mistral not implemented")
        return None

    def _parse_vision_results(self, result: Dict) -> List[UnifiedIssue]:

        issues = []

        findings = result.get("findings", [])

        for finding in findings:

            severity_map = {
                "critical": IssueSeverity.CRITICAL,
                "serious": IssueSeverity.SERIOUS,
                "moderate": IssueSeverity.MODERATE,
                "minor": IssueSeverity.MINOR
            }


            confidence_score = int(finding.get("confidence", 0.7) * 100)


            if confidence_score >= 95:
                confidence = ConfidenceLevel.HIGH
            elif confidence_score >= 70:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW


            issue = UnifiedIssue(
                title=f"[AI Vision] {finding.get('description', '')[:50]}",
                description=finding.get("description", ""),
                issue_type=f"vision_{finding.get('issue_type', 'unknown')}",
                severity=severity_map.get(
                    finding.get("severity", "moderate"),
                    IssueSeverity.MODERATE
                ),
                confidence=confidence,
                confidence_score=confidence_score,
                source=IssueSource.AI_CONTEXTUAL,
                wcag_criteria=[
                    WCAGCriteria(
                        id=self._map_to_wcag(finding.get("issue_type", "")),
                        level="AA",
                        title="Visual Accessibility"
                    )
                ],
                evidence=EvidenceData(
                    ai_reasoning=finding.get("reasoning", ""),
                    computed_values={
                        "location_guess": finding.get("location_guess", ""),
                        "vision_analysis": finding.get("details", {})
                    }
                ),
                engine_name="llava-vision",
                engine_version="1.0",
                tags=["ai", "vision", "visual-analysis"]
            )

            issues.append(issue)

        return issues

    def _parse_fix_result(
        self,
        result: Dict,
        original_selector: Optional[str]
    ) -> RemediationSuggestion:


        return RemediationSuggestion(
            description=result.get("explanation", "Suggested fix"),
            code_before=result.get("code_before", ""),
            code_after=result.get("code_after", ""),
            estimated_effort=self._estimate_effort(result.get("code_after", ""))
        )

    def _map_to_wcag(self, issue_type: str) -> str:

        mapping = {
            "visual_clutter": "1.3.1",
            "color_reliance": "1.4.1",
            "focus_visibility": "2.4.7",
            "spacing": "1.4.12",
            "reflow": "1.4.10"
        }
        return mapping.get(issue_type, "1.3.1")

    def _estimate_effort(self, code: str) -> str:

        if not code:
            return "unknown"


        lines = code.count('\n')
        if lines < 3:
            return "low"
        elif lines < 10:
            return "medium"
        else:
            return "high"