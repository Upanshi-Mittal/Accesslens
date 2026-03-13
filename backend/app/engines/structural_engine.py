from typing import List, Dict, Any, Optional
from playwright.async_api import Page
import asyncio
import logging
from .base import BaseAccessibilityEngine
from ..models.schemas import (
    UnifiedIssue, IssueSeverity, IssueSource,
    ConfidenceLevel, ElementLocation, RemediationSuggestion,
    EvidenceData, WCAGCriteria
)
from ..core.heading_analyzer import HeadingHierarchyAnalyzer
from ..core.landmark_validator import LandmarkValidator
from ..core.scoring import ConfidenceCalculator
from ..core.config import settings

class StructuralEngine(BaseAccessibilityEngine):

    def __init__(self):
        super().__init__("structural_engine", "1.0.0")
        self.capabilities = ["structure", "headings", "landmarks", "semantics"]
        self._logger = logging.getLogger(__name__)
        self.heading_analyzer = HeadingHierarchyAnalyzer()
        self.landmark_validator = LandmarkValidator()

    async def analyze(
        self,
        page_data: Dict[str, Any],
        request: Dict[str, Any]
    ) -> List[UnifiedIssue]:
        page = page_data.get("page")
        accessibility_tree = page_data.get("accessibility_tree", {})
        if not page:
            return []
        try:
            issues = []
            headings = await self._extract_headings(page, accessibility_tree)
            if headings:
                heading_analysis = self.heading_analyzer.analyze(headings)
                heading_issues = await self._convert_heading_issues(heading_analysis.get("issues", []))
                issues.extend(heading_issues)
                if heading_analysis.get("outline"):
                    page_data["heading_outline"] = heading_analysis["outline"]
            landmarks = await self._extract_landmarks(page, accessibility_tree)
            if landmarks:
                landmark_analysis = self.landmark_validator.validate(landmarks)
                landmark_issues = await self._convert_landmark_issues(landmark_analysis.get("issues", []))
                issues.extend(landmark_issues)
                if landmark_analysis.get("structure"):
                    page_data["landmark_structure"] = landmark_analysis["structure"]
            outline_issues = await self._analyze_document_outline(page, headings, landmarks)
            issues.extend(outline_issues)
            semantic_issues = await self._analyze_semantic_structure(page, accessibility_tree)
            issues.extend(semantic_issues)
            nav_issues = await self._analyze_navigation_structure(page)
            issues.extend(nav_issues)
            return issues
        except Exception as e:
            self._logger.error(f"Structural analysis failed: {e}")
            return []

    async def _extract_headings(self, page: Page, accessibility_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        if accessibility_tree.get("structure", {}).get("headings"):
            headings_data = accessibility_tree["structure"]["headings"]
            if isinstance(headings_data, dict) and headings_data.get("headings"):
                return headings_data["headings"]
        js_code = """
        (function() {
            const headings = [];
            const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]');
            elements.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                let level = parseInt(el.tagName.substring(1));
                if (isNaN(level)) {
                    level = parseInt(el.getAttribute('aria-level')) || 2;
                }
                headings.push({
                    level: level,
                    text: el.textContent.trim(),
                    tagName: el.tagName.toLowerCase(),
                    selector: getUniqueSelector(el),
                    index: index,
                    isVisible: el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0
                });
            });
            return headings;
            function getUniqueSelector(el) {
                if (el.id) return `#${el.id}`;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    path.unshift(selector);
                    el = el.parentNode;
                }
                return path.join(' > ');
            }
        })();
        """
        try:
            return await page.evaluate(js_code)
        except Exception as e:
            self._logger.warning(f"Failed to extract headings: {e}")
            return []

    async def _extract_landmarks(self, page: Page, accessibility_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts ARIA landmark roles (main, nav, header, etc.) from the page structure.
        """
        if accessibility_tree.get("structure", {}).get("landmarks"):
            landmarks_data = accessibility_tree["structure"]["landmarks"]
            if isinstance(landmarks_data, dict) and landmarks_data.get("landmarks"):
                return landmarks_data["landmarks"]
        js_code = """
        (function() {
            const landmarks = [];
            const landmarkRoles = ['main', 'nav', 'navigation', 'header', 'banner', 'footer', 'contentinfo', 'aside', 'complementary', 'form', 'search', 'section', 'region'];
            const elements = document.querySelectorAll(landmarkRoles.map(r => `[role="${r}"], ${r}`).join(', '));
            elements.forEach(el => {
                const role = el.getAttribute('role') || el.tagName.toLowerCase();
                if (!landmarkRoles.includes(role)) return;
                landmarks.push({
                    role: role,
                    tag: el.tagName.toLowerCase(),
                    selector: getUniqueSelector(el),
                    label: el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || ''
                });
            });
            return landmarks;
            function getUniqueSelector(el) {
                if (el.id) return `#${el.id}`;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    path.unshift(selector);
                    el = el.parentNode;
                }
                return path.join(' > ');
            }
        })();
        """
        try:
            return await page.evaluate(js_code)
        except Exception as e:
            self._logger.warning(f"Failed to extract landmarks: {e}")
            return []

    async def _convert_heading_issues(self, issues: List[Dict]) -> List[UnifiedIssue]:
        unified_issues = []
        for issue in issues:
            severity_map = {"serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
            confidence_score = ConfidenceCalculator.calculate_confidence("structural", settings.confidence_weights["structural"])
            location = None
            if issue.get("location"):
                loc = issue["location"]
                location = ElementLocation(selector=loc.get("selector", ""), html=f"Heading at index {loc.get('index', 'unknown')}")
            remediation = self._get_heading_remediation(issue)
            unified_issues.append(UnifiedIssue(
                title=self._get_heading_title(issue),
                description=issue.get("description", "Heading structure issue"),
                issue_type=issue.get("type", "heading_issue"),
                severity=severity_map.get(issue.get("severity", "moderate"), IssueSeverity.MODERATE),
                confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else (ConfidenceLevel.MEDIUM if confidence_score >= 75 else ConfidenceLevel.LOW),
                confidence_score=confidence_score,
                source=IssueSource.STRUCTURAL,
                wcag_criteria=[WCAGCriteria(id=issue.get("wcag", "1.3.1"), level="AA", title="Info and Relationships", description="Structure and relationships are programmatically determined")],
                location=location,
                remediation=remediation,
                evidence=EvidenceData(computed_values=issue.get("location", {})),
                engine_name=self.name,
                engine_version=self.version,
                tags=["headings", "structure", "hierarchy"]
            ))
        return unified_issues

    def _get_heading_title(self, issue: Dict) -> str:
        titles = {"no_headings": "Page has no headings", "missing_h1": "Missing H1 heading", "multiple_h1": "Multiple H1 headings found", "heading_skip": "Heading levels skipped", "empty_heading": "Heading has no text content", "hidden_heading": "Heading is hidden from users", "deep_nesting": "Very deep heading nesting", "section_no_heading": "Section has subheadings but no main heading"}
        return titles.get(issue.get("type", ""), issue.get("description", "Heading issue"))

    def _get_heading_remediation(self, issue: Dict) -> Optional[RemediationSuggestion]:
        issue_type = issue.get("type", "")
        if issue_type == "missing_h1":
            return RemediationSuggestion(description="Add an H1 heading that describes the page content", code_after="<h1>Main page title</h1>", estimated_effort="low")
        elif issue_type == "heading_skip":
            return RemediationSuggestion(description="Avoid skipping heading levels. Use hierarchical order: H1  H2  H3", code_after="<!-- Good: -->\n<h1>Main title</h1>\n<h2>Section</h2>\n<h3>Subsection</h3>", estimated_effort="medium")
        elif issue_type == "empty_heading":
            return RemediationSuggestion(description="Add descriptive text to the heading or remove if not needed", code_after="<h2>Descriptive section title</h2>", estimated_effort="low")
        return None

    async def _convert_landmark_issues(self, issues: List[Dict]) -> List[UnifiedIssue]:
        unified_issues = []
        for issue in issues:
            severity_map = {"serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
            confidence_score = ConfidenceCalculator.calculate_confidence("structural", settings.confidence_weights["structural"])
            location = None
            if issue.get("landmark"):
                l = issue["landmark"] if isinstance(issue["landmark"], dict) else {}
                location = ElementLocation(selector=l.get("selector", ""), html=f"<{l.get('tag', 'div')}>")
            elif issue.get("landmarks") and len(issue["landmarks"]) > 0:
                l = issue["landmarks"][0]
                location = ElementLocation(selector=l.get("selector", ""), html=f"<{l.get('tag', 'div')}>")
            remediation = self._get_landmark_remediation(issue)
            unified_issues.append(UnifiedIssue(
                title=self._get_landmark_title(issue),
                description=issue.get("description", "Landmark structure issue"),
                issue_type=issue.get("type", "landmark_issue"),
                severity=severity_map.get(issue.get("severity", "moderate"), IssueSeverity.MODERATE),
                confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else (ConfidenceLevel.MEDIUM if confidence_score >= 75 else ConfidenceLevel.LOW),
                confidence_score=confidence_score,
                source=IssueSource.STRUCTURAL,
                wcag_criteria=[WCAGCriteria(id=issue.get("wcag", "1.3.1"), level="AA", title="Info and Relationships", description="Structure and relationships are programmatically determined")],
                location=location,
                remediation=remediation,
                evidence=EvidenceData(computed_values={"landmarks": issue.get("landmarks", [])}),
                engine_name=self.name,
                engine_version=self.version,
                tags=["landmarks", "structure", "aria"]
            ))
        return unified_issues

    def _get_landmark_title(self, issue: Dict) -> str:
        titles = {"no_landmarks": "Page has no landmark regions", "missing_landmark": f"Missing {issue.get('landmark', {}).get('role', 'required')} landmark", "duplicate_landmark": "Duplicate landmarks without unique labels", "nested_main": "Main landmark nested inside another main", "banner_in_main": "Banner landmark inside main content", "contentinfo_in_main": "Contentinfo landmark inside main content", "region_no_heading": "Region landmark has no heading", "navigation_unlabeled": "Navigation landmark lacks unique label", "main_under_banner": "Main landmark under banner"}
        return titles.get(issue.get("type", ""), issue.get("description", "Landmark issue"))

    def _get_landmark_remediation(self, issue: Dict) -> Optional[RemediationSuggestion]:
        issue_type = issue.get("type", "")
        if issue_type == "missing_landmark":
            role = issue.get("landmark", {}).get("role", "main")
            return RemediationSuggestion(description=f"Add a {role} landmark to identify the main content region", code_after=f'<main role="main">\n  <!-- Main content here -->\n</main>', estimated_effort="low")
        elif issue_type == "duplicate_landmark":
            return RemediationSuggestion(description="Add unique aria-label or aria-labelledby to distinguish landmarks", code_after='<nav aria-label="Main navigation">\n  <!-- Navigation -->\n</nav>\n<nav aria-label="Footer navigation">\n  <!-- Footer links -->\n</nav>', estimated_effort="low")
        elif issue_type == "region_no_heading":
            return RemediationSuggestion(description="Add a heading to describe the region content", code_after='<section>\n  <h2>Region title</h2>\n  <!-- Content -->\n</section>', estimated_effort="low")
        return None

    async def _analyze_document_outline(self, page: Page, headings: List[Dict], landmarks: List[Dict]) -> List[UnifiedIssue]:
        """
        Checks for logical document outline rules.
        (e.g., ensuring a 'main' landmark actually contains heading elements).
        """
        issues = []
        if not headings and not landmarks: return issues
        main_landmarks = [l for l in landmarks if l.get("role") == "main"]
        if main_landmarks:
            for main in main_landmarks:
                main_selector = main.get("selector", "")
                if main_selector:
                    js_code = "(selector) => { const el = document.querySelector(selector); return el && (el.querySelector('h1, h2, h3, h4, h5, h6') !== null); }"
                    try:
                        has_heading = await page.evaluate(js_code, main_selector)
                        if not has_heading:
                            issues.append(await self._create_outline_issue("main_no_heading", "Main content region has no heading", "serious", main))
                    except Exception as e:
                        self._logger.warning(f"Failed to check main heading: {e}")
        return issues

    async def _analyze_semantic_structure(self, page: Page, accessibility_tree: Dict[str, Any]) -> List[UnifiedIssue]:
        """
        Verifies semantic HTML rules, such as identifying clickable `div` elements
        that should semantically be `button` or `a` tags for keyboard accessibility.
        """
        issues = []
        js_code = "() => { return document.querySelectorAll('div[onclick], div[onmousedown], div[onmouseup]').length; }"
        try:
            clickable_divs = await page.evaluate(js_code)
            if clickable_divs > 0:
                issues.append(await self._create_semantic_issue("clickable_div", f"Found {clickable_divs} clickable divs that should be buttons", "moderate", clickable_divs))
        except Exception as e:
            self._logger.warning(f"Failed to analyze semantic structure: {e}")
        return issues

    async def _analyze_navigation_structure(self, page: Page) -> List[UnifiedIssue]:
        """
        Analyzes navigation block completeness.
        Specifically checks for bypass blocks like 'skip to main content' links.
        """
        issues = []
        js_code = "() => { const links = Array.from(document.querySelectorAll('a')); return { hasSkipLink: links.some(l => l.textContent.toLowerCase().includes('skip') || l.href.includes('#main')) }; }"
        try:
            result = await page.evaluate(js_code)
            if not result.get("hasSkipLink"):
                issues.append(await self._create_navigation_issue("no_skip_link", "No skip link found for keyboard users", "moderate", None))
        except Exception as e:
            self._logger.warning(f"Failed to analyze navigation: {e}")
        return issues

    async def _create_outline_issue(self, issue_type: str, description: str, severity: str, element: Optional[Dict]) -> UnifiedIssue:
        severity_map = {"serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
        confidence_score = ConfidenceCalculator.calculate_confidence("structural", settings.confidence_weights["structural"])
        location = ElementLocation(selector=element["selector"]) if element and element.get("selector") else None
        return UnifiedIssue(
            title=self._get_outline_title(issue_type),
            description=description,
            issue_type=issue_type,
            severity=severity_map.get(severity, IssueSeverity.MODERATE),
            confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else (ConfidenceLevel.MEDIUM if confidence_score >= 75 else ConfidenceLevel.LOW),
            confidence_score=confidence_score,
            source=IssueSource.STRUCTURAL,
            wcag_criteria=[WCAGCriteria(id="2.4.10", level="AAA", title="Section Headings", description="Section headings organize the content")],
            location=location,
            engine_name=self.name,
            engine_version=self.version,
            tags=["outline", "structure"]
        )

    def _get_outline_title(self, issue_type: str) -> str:
        titles = {"main_no_heading": "Main content lacks heading"}
        return titles.get(issue_type, "Document outline issue")

    async def _create_semantic_issue(self, issue_type: str, description: str, severity: str, count: int) -> UnifiedIssue:
        severity_map = {"serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
        confidence_score = ConfidenceCalculator.calculate_confidence("structural", settings.confidence_weights["structural"])
        return UnifiedIssue(
            title=f"Semantic HTML issue: {issue_type}",
            description=description,
            issue_type=issue_type,
            severity=severity_map.get(severity, IssueSeverity.MODERATE),
            confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else (ConfidenceLevel.MEDIUM if confidence_score >= 75 else ConfidenceLevel.LOW),
            confidence_score=confidence_score,
            source=IssueSource.STRUCTURAL,
            wcag_criteria=[WCAGCriteria(id="4.1.2", level="A", title="Name, Role, Value", description="Elements have appropriate roles")],
            evidence=EvidenceData(computed_values={"count": count}),
            engine_name=self.name,
            engine_version=self.version,
            tags=["semantic", "html"]
        )

    async def _create_navigation_issue(self, issue_type: str, description: str, severity: str, element: Optional[Dict]) -> UnifiedIssue:
        severity_map = {"serious": IssueSeverity.SERIOUS, "moderate": IssueSeverity.MODERATE, "minor": IssueSeverity.MINOR}
        confidence_score = ConfidenceCalculator.calculate_confidence("navigation", settings.confidence_weights["navigation"])
        remediation = RemediationSuggestion(description="Add a skip link to help keyboard users bypass navigation", code_after='<a href="#main" class="skip-link">Skip to main content</a>', estimated_effort="low") if issue_type == "no_skip_link" else None
        return UnifiedIssue(
            title="Navigation structure issue",
            description=description,
            issue_type=issue_type,
            severity=severity_map.get(severity, IssueSeverity.MODERATE),
            confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else (ConfidenceLevel.MEDIUM if confidence_score >= 75 else ConfidenceLevel.LOW),
            confidence_score=confidence_score,
            source=IssueSource.STRUCTURAL,
            wcag_criteria=[WCAGCriteria(id="2.4.1", level="A", title="Bypass Blocks", description="A mechanism to bypass blocks of content")],
            remediation=remediation,
            engine_name=self.name,
            engine_version=self.version,
            tags=["navigation", "keyboard"]
        )

    async def validate_config(self) -> bool:
        return True