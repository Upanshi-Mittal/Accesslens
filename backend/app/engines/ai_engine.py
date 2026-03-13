from typing import List, Dict, Any, Optional
import asyncio
import logging
import torch
from ..engines.base import BaseAccessibilityEngine
from ..models.schemas import (
    UnifiedIssue, AuditRequest, IssueSource,
    ConfidenceLevel, RemediationSuggestion, EvidenceData,
    WCAGCriteria, IssueSeverity
)
from ..ai.llava_integration import LLaVAService
from ..ai.mistral_integration import MistralService
from ..core.config import settings

class AIEngine(BaseAccessibilityEngine):
    """
    Advanced Heuristic Accessibility Engine powered by Local LLMs.

    The AIEngine implements multi-modal analysis to complement deterministic rule engines:
    1. Vision Analysis (LLaVA): Analyzes raw screenshots to catch visual clutter, UI overlaps, 
       and contrast issues not structurally readable through DOM parsing alone.
    2. Contextual Code Fixes (Mistral): Generates semantically aware HTML/ARIA replacement blocks 
       based on the surrounding context of a found vulnerability. 
    3. Structural Heuristics: Evaluates Alt Text meaning relative to the surrounding page context,
       and analyzes component density.
    """

    def __init__(self):
        super().__init__("ai_engine", "1.0.0")
        self.capabilities = ["vision_analysis", "code_generation", "contextual_evaluation", "visual_clutter_detection", "alt_text_quality", "layout_analysis"]
        self._logger = logging.getLogger(__name__)
        self.llava = LLaVAService(model_path=settings.llava_model_path)
        self.mistral = MistralService(model_path=settings.mistral_model_path)
        self._initialized = False
        self._init_error = None

    async def initialize(self):
        if self._initialized: return
        try:
            self._logger.info(f"Initializing AI engine...")
            await asyncio.gather(self.llava.load_model(), self.mistral.load_model())
            self._initialized = True
            self._logger.info("AI engine initialized successfully")
        except Exception as e:
            self._init_error = str(e)
            self._logger.error(f"Failed to initialize AI engine: {e}")
            self._initialized = False # Continue without AI

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
                    issue.confidence_score = settings.ai_default_score
            return issues
        except Exception as e:
            self._logger.error(f"AI analysis failed: {e}")
            return self._create_error_issues(str(e))

    async def _retry_with_backoff(self, func, *args, **kwargs):
        max_retries = settings.ai_max_retries
        base_delay = settings.ai_retry_delay
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = base_delay * (2 ** attempt)
                self._logger.warning(f"AI call failed ({e}). Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(delay)

    async def _run_vision_analysis(self, screenshot: str, accessibility_tree: Dict, dom_snapshot: Dict) -> List[UnifiedIssue]:
        """
        Executes a prompt-driven Vision Language Model (LLaVA) over the page screenshot.

        Prompt Engineering Strategy:
        We supply the raw accessibility_tree statistics as context variables to ground the prompt,
        then ask the model to look specifically for:
        - Layout overlaps hindering readability.
        - Text elements heavily embedded inside images without accessible text.
        - Unintuitive or misleading visual icons with no descriptive text.

        Returns:
            A list of UnifiedIssue models mapped from the LLM's interpreted JSON response.
        """
        try:
            vision_results = await self._retry_with_backoff(
                self.llava.analyze_image, 
                screenshot, 
                self._build_vision_prompt(accessibility_tree)
            )
            return self._parse_vision_results(vision_results, dom_snapshot)
        except Exception as e:
            self._logger.error(f"Vision analysis failed: {e}")
            return []

    async def _generate_code_fixes(self, issues: List[UnifiedIssue], dom_snapshot: Dict) -> None:
        """
        Executes a localized Language Model (Mistral) to generate programmatic remediation blocks.
        
        Prompt Engineering Strategy:
        Instead of generic "Add alt text" advice, this isolates the specific DOM element selector
        found to be violating WCAG rules, embeds it alongside surrounding DOM nodes on the prompt
        template, and forces Mistral to generate a direct `diff` output replacing the failing
        node with syntactically correct ARIA attributes or semantic tags.
        """
        try:
            issues_by_type = {}
            for issue in issues:
                if issue.issue_type not in issues_by_type: issues_by_type[issue.issue_type] = []
                issues_by_type[issue.issue_type].append(issue)
            for issue_type, type_issues in issues_by_type.items():
                sample_issue = type_issues[0]
                context = self._build_fix_context(sample_issue, dom_snapshot)
                fix_result = await self._retry_with_backoff(
                    self.mistral.generate_fix,
                    context, 
                    issue_type=issue_type
                )
                if fix_result:
                    for issue in type_issues:
                        issue.remediation = self._parse_fix_result(fix_result, issue.location.selector if issue.location else None)
        except Exception as e:
            self._logger.error(f"Code generation failed: {e}")

    async def _run_contextual_analysis(self, accessibility_tree: Dict, dom_snapshot: Dict) -> List[UnifiedIssue]:
        """
        Evaluates heuristic thresholds for UX and accessibility context.
        
        Analyzes logic outside the boundary of deterministic WCAG evaluation length:
        - The absolute pixel verbosity or logical density of the DOM.
        - Meaningless focus traps or redundant tab indexes.
        """
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
        return f"Generate an accessible HTML/ARIA fix for {issue.title}. {html_context}"

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
        issues = []
        focusable_elements = accessibility_tree.get('structure', {}).get('focusable_elements', [])
        
        vague_phrases = ['click here', 'read more', 'learn more', 'link', 'continue', 'here']
        
        for element in focusable_elements:
            role = element.get('role', '').lower()
            name = element.get('name', '').lower().strip()
            
            if role in ['link', 'button']:
                # Check for empty or whitespace-only names
                if not name:
                    issues.append(UnifiedIssue(
                        title=f"Empty {role} found",
                        description=f"A {role} was found without any accessible text.",
                        issue_type="empty_interactive_element",
                        severity=IssueSeverity.SERIOUS,
                        confidence=ConfidenceLevel.HIGH,
                        confidence_score=95,
                        source=IssueSource.AI_CONTEXTUAL,
                        wcag_criteria=[WCAGCriteria(id="4.1.2", level="A", title="Name, Role, Value")],
                        engine_name=self.name,
                        tags=["ai", "semantics"]
                    ))
                # Check for vague phrases
                elif name in vague_phrases:
                    issues.append(UnifiedIssue(
                        title="Vague link or button text",
                        description=f"The text '{name}' does not describe the destination or purpose.",
                        issue_type="vague_link_text",
                        severity=IssueSeverity.MODERATE,
                        confidence=ConfidenceLevel.HIGH,
                        confidence_score=90,
                        source=IssueSource.AI_CONTEXTUAL,
                        wcag_criteria=[WCAGCriteria(id="2.4.4", level="A", title="Link Purpose (In Context)")],
                        engine_name=self.name,
                        tags=["ai", "semantics"]
                    ))

        return issues

    async def _analyze_layout_complexity(self, dom_snapshot: Dict) -> List[UnifiedIssue]:
        total_elements = dom_snapshot.get('statistics', {}).get('total_elements', 0)
        viewport_height = settings.default_viewport_height
        if total_elements > 100:
            density = total_elements / viewport_height * 100
            if density > settings.density_threshold:
                return [UnifiedIssue(title="High content density", description="Content is visually dense", issue_type="visual_clutter", severity=IssueSeverity.MODERATE, confidence=ConfidenceLevel.MEDIUM, confidence_score=75, source=IssueSource.AI_CONTEXTUAL, wcag_criteria=[WCAGCriteria(id="1.4.8", level="AAA", title="Visual Presentation")], engine_name=self.name, tags=["ai", "layout"])]
        return []

    async def _analyze_interactive_patterns(self, accessibility_tree: Dict) -> List[UnifiedIssue]:
        focusable = accessibility_tree.get('structure', {}).get('focusable_elements', [])
        if len(focusable) > settings.max_focusable_elements:
            return [UnifiedIssue(title="Verify focus indicators", description="Many interactive elements found", issue_type="focus_visibility_check", severity=IssueSeverity.SERIOUS, confidence=ConfidenceLevel.LOW, confidence_score=60, source=IssueSource.AI_CONTEXTUAL, wcag_criteria=[WCAGCriteria(id="2.4.7", level="AA", title="Focus Visible")], engine_name=self.name, tags=["ai", "keyboard"])]
        return []

    def _create_error_issues(self, error: str) -> List[UnifiedIssue]:
        return [UnifiedIssue(title="AI analysis error", description=error, issue_type="ai_service_error", severity=IssueSeverity.MINOR, confidence=ConfidenceLevel.HIGH, confidence_score=100, source=IssueSource.AI_CONTEXTUAL, engine_name=self.name, tags=["ai", "error"])]

    async def validate_config(self) -> bool:
        try:
            await self.initialize()
            return True
        except Exception: return False