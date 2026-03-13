from typing import List, Dict, Any, Optional
import asyncio
import logging
import torch
from ..engines.base import BaseAccessibilityEngine
from ..models.schemas import (
    UnifiedIssue, AuditRequest, IssueSource,
    ConfidenceLevel, RemediationSuggestion, EvidenceData,
    WCAGCriteria
)
from ..ai.llava_integration import LLaVAService
from ..ai.mistral_integration import MistralService
from ..core.scoring import ConfidenceCalculator
from ..core.config import settings

class AIEngine(BaseAccessibilityEngine):

    def __init__(self):
        super().__init__("ai_engine", "1.0.0")
        self.capabilities = ["vision_analysis", "code_generation", "contextual_evaluation", "visual_clutter_detection", "alt_text_quality", "layout_analysis"]
        self._logger = logging.getLogger(__name__)
        self.llava = LLaVAService(model_path=settings.llava_model_path, device=self._get_device())
        self.mistral = MistralService(model_path=settings.mistral_model_path, device=self._get_device())
        self._initialized = False
        self._init_error = None

    def _get_device(self) -> str:
        if torch.cuda.is_available(): return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(): return "mps"
        else: return "cpu"

    async def initialize(self):
        if self._initialized: return
        try:
            self._logger.info(f"Initializing AI engine on {self._get_device()}...")
            await asyncio.gather(self.llava.load_model(), self.mistral.load_model())
            self._initialized = True
            self._logger.info("AI engine initialized successfully")
        except Exception as e:
            self._init_error = str(e)
            self._logger.error(f"Failed to initialize AI engine: {e}")
            raise RuntimeError(f"AI engine initialization failed - this is a required component: {e}")

    async def analyze(self, page_data: Dict[str, Any], request: AuditRequest) -> List[UnifiedIssue]:
        if not self._initialized: await self.initialize()
        issues = []
        try:
            screenshot = page_data.get("screenshot")
            accessibility_tree = page_data.get("accessibility_tree", {})
            dom_snapshot = page_data.get("dom_snapshot", {})
            if not screenshot:
                self._logger.error("No screenshot available for AI analysis")
                return self._create_error_issues("Screenshot missing")
            vision_issues = await self._run_vision_analysis(screenshot, accessibility_tree, dom_snapshot)
            issues.extend(vision_issues)
            if issues: await self._generate_code_fixes(issues, dom_snapshot)
            contextual_issues = await self._run_contextual_analysis(accessibility_tree, dom_snapshot)
            issues.extend(contextual_issues)
            for issue in issues:
                issue.source = IssueSource.AI_CONTEXTUAL
                if not issue.confidence:
                    issue.confidence = ConfidenceLevel.MEDIUM
                    issue.confidence_score = 85
            return issues
        except Exception as e:
            self._logger.error(f"AI analysis failed: {e}")
            return self._create_error_issues(str(e))

    async def _run_vision_analysis(self, screenshot: str, accessibility_tree: Dict, dom_snapshot: Dict) -> List[UnifiedIssue]:
        try:
            vision_results = await self.llava.analyze_image(screenshot, self._build_vision_prompt(accessibility_tree))
            return self._parse_vision_results(vision_results, dom_snapshot)
        except Exception as e:
            self._logger.error(f"Vision analysis failed: {e}")
            return []

    async def _generate_code_fixes(self, issues: List[UnifiedIssue], dom_snapshot: Dict) -> None:
        try:
            issues_by_type = {}
            for issue in issues:
                if issue.issue_type not in issues_by_type: issues_by_type[issue.issue_type] = []
                issues_by_type[issue.issue_type].append(issue)
            for issue_type, type_issues in issues_by_type.items():
                sample_issue = type_issues[0]
                context = self._build_fix_context(sample_issue, dom_snapshot)
                fix_result = await self.mistral.generate_fix(context, issue_type=issue_type)
                if fix_result:
                    for issue in type_issues:
                        issue.remediation = self._parse_fix_result(fix_result, issue.location.selector if issue.location else None)
        except Exception as e:
            self._logger.error(f"Code generation failed: {e}")

    async def _run_contextual_analysis(self, accessibility_tree: Dict, dom_snapshot: Dict) -> List[UnifiedIssue]:
        issues = []
        try:
            alt_issues = await self._analyze_alt_text_quality(accessibility_tree)
            issues.extend(alt_issues)
            layout_issues = await self._analyze_layout_complexity(dom_snapshot)
            issues.extend(layout_issues)
            interactive_issues = await self._analyze_interactive_patterns(accessibility_tree)
            issues.extend(interactive_issues)
        except Exception as e:
            self._logger.error(f"Contextual analysis failed: {e}")
        return issues

    def _build_vision_prompt(self, accessibility_tree: Dict) -> str:
        stats = accessibility_tree.get('statistics', {})
        return f"Analyze the screenshot for accessibility issues. Total elements: {stats.get('total_elements', 'unknown')}."

    def _build_fix_context(self, issue: UnifiedIssue, dom_snapshot: Dict) -> str:
        html_context = f"Selector: {issue.location.selector}\nHTML: {issue.location.html}" if issue.location and issue.location.selector else ""
        return f"Generate an accessible fix for {issue.title}. {html_context}"

    def _parse_vision_results(self, results: Dict, dom_snapshot: Dict) -> List[UnifiedIssue]:
        issues = []
        findings = results.get("findings", [])
        for finding in findings:
            severity_map = {"critical": IssueSeverity.CRITICAL, "serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
            issue = UnifiedIssue(
                title=f"[Vision] {finding.get('description', '')[:100]}",
                description=finding.get("description", ""),
                issue_type=f"vision_{finding.get('issue_type', 'unknown')}",
                severity=severity_map.get(finding.get("severity", "moderate"), IssueSeverity.MODERATE),
                confidence=ConfidenceLevel.MEDIUM,
                confidence_score=int(finding.get("confidence", 0.85) * 100),
                source=IssueSource.AI_CONTEXTUAL,
                remediation=RemediationSuggestion(description=finding.get("suggestion", "Review this element"), estimated_effort="medium"),
                engine_name=self.name,
                engine_version=self.version,
                tags=["ai", "vision"]
            )
            issues.append(issue)
        return issues

    def _parse_fix_result(self, result: Dict, selector: Optional[str]) -> RemediationSuggestion:
        return RemediationSuggestion(description=result.get("explanation", "Suggested accessibility fix"), code_before=result.get("code_before", ""), code_after=result.get("code_after", ""), estimated_effort="medium")

    async def _analyze_alt_text_quality(self, accessibility_tree: Dict) -> List[UnifiedIssue]:
        return []

    async def _analyze_layout_complexity(self, dom_snapshot: Dict) -> List[UnifiedIssue]:
        total_elements = dom_snapshot.get('statistics', {}).get('total_elements', 0)
        viewport_height = settings.default_viewport_height
        if total_elements > 100:
            density = total_elements / viewport_height * 100
            if density > 20:
                return [UnifiedIssue(title="High content density", description="Content is visually dense", issue_type="visual_clutter", severity=IssueSeverity.MODERATE, confidence=ConfidenceLevel.MEDIUM, confidence_score=75, source=IssueSource.AI_CONTEXTUAL, wcag_criteria=[WCAGCriteria(id="1.4.8", level="AAA", title="Visual Presentation")], engine_name=self.name, tags=["ai", "layout"])]
        return []

    async def _analyze_interactive_patterns(self, accessibility_tree: Dict) -> List[UnifiedIssue]:
        focusable = accessibility_tree.get('structure', {}).get('focusable_elements', [])
        if len(focusable) > 10:
            return [UnifiedIssue(title="Verify focus indicators", description="Many interactive elements found", issue_type="focus_visibility_check", severity=IssueSeverity.SERIOUS, confidence=ConfidenceLevel.LOW, confidence_score=60, source=IssueSource.AI_CONTEXTUAL, wcag_criteria=[WCAGCriteria(id="2.4.7", level="AA", title="Focus Visible")], engine_name=self.name, tags=["ai", "keyboard"])]
        return []

    def _create_error_issues(self, error: str) -> List[UnifiedIssue]:
        return [UnifiedIssue(title="AI analysis error", description=error, issue_type="ai_service_error", severity=IssueSeverity.MINOR, confidence=ConfidenceLevel.HIGH, confidence_score=100, source=IssueSource.AI_CONTEXTUAL, engine_name=self.name, tags=["ai", "error"])]

    async def validate_config(self) -> bool:
        try:
            await self.initialize()
            return True
        except Exception: return False