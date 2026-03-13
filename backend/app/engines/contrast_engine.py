from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import Page
import asyncio
import logging
from .base import BaseAccessibilityEngine
from ..models.schemas import (
    UnifiedIssue, IssueSeverity, IssueSource,
    ConfidenceLevel, ElementLocation, RemediationSuggestion,
    EvidenceData, WCAGCriteria
)
from ..core.color_utils import ColorParser, ContrastCalculator, RGBColor
from ..core.scoring import ConfidenceCalculator
from ..core.config import settings

class ContrastEngine(BaseAccessibilityEngine):

    def __init__(self):
        super().__init__("contrast_engine", "1.0.0")
        self.capabilities = ["contrast", "color", "visibility"]
        self._logger = logging.getLogger(__name__)
        self.THRESHOLDS = settings.contrast_thresholds

    async def analyze(
        self,
        page_data: Dict[str, Any],
        request: Dict[str, Any]
    ) -> List[UnifiedIssue]:
        """
        Coordinates the entire contrast analysis pipeline.
        Extracts text, UI elements, and interactive states from the Playwright page and returns UnifiedIssues for any contrast failures.
        """
        page = page_data.get("page")
        if not page:
            return []
        try:
            text_elements = await self._extract_text_elements(page)
            ui_elements = await self._extract_ui_elements(page)
            issues = []
            for element in text_elements:
                issue = await self._analyze_text_contrast(element, page)
                if issue:
                    issues.append(issue)
            for element in ui_elements:
                issue = await self._analyze_ui_contrast(element, page)
                if issue:
                    issues.append(issue)
            hover_issues = await self._analyze_interactive_states(page)
            issues.extend(hover_issues)
            return issues
        except Exception as e:
            self._logger.error(f"Contrast analysis failed: {e}")
            return []

    async def _extract_text_elements(self, page: Page) -> List[Dict[str, Any]]:
        """
        Injects a JavaScript TreeWalker into the Playwright page to identify all visible text nodes.
        Filters out scripts, styles, and hidden elements to build a map of actionable text.
        """
        js_code = """
        (function() {
            const elements = [];
            const textNodes = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                {
                    acceptNode: function(node) {
                        if (node.tagName === 'SCRIPT' ||
                            node.tagName === 'STYLE' ||
                            node.tagName === 'META' ||
                            node.tagName === 'LINK') {
                            return NodeFilter.FILTER_REJECT;
                        }
                        const text = node.textContent?.trim();
                        if (text && text.length > 0) {
                            return NodeFilter.FILTER_ACCEPT;
                        }
                        return NodeFilter.FILTER_SKIP;
                    }
                }
            );
            while (walker.nextNode()) {
                const el = walker.currentNode;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                // Defer computed style until we prove it is visually rendered
                const computed = window.getComputedStyle(el);
                if (computed.visibility === 'hidden' || computed.display === 'none' || computed.opacity === '0') continue;
                const fontSize = parseFloat(computed.fontSize);
                const fontWeight = computed.fontWeight;
                const isBold = parseInt(fontWeight) >= 700 || fontWeight === 'bold';
                const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && isBold);
                elements.push({
                    selector: getUniqueSelector(el),
                    tag: el.tagName.toLowerCase(),
                    id: el.id,
                    classes: Array.from(el.classList),
                    text: el.textContent.trim().substring(0, 100),
                    fontSize: fontSize,
                    fontWeight: fontWeight,
                    isLargeText: isLargeText,
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    position: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    }
                });
            }
            return elements;
            function getUniqueSelector(el) {
                if (el.id) return `#${el.id}`;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.className) {
                        const classes = Array.from(el.classList).join('.');
                        if (classes) selector += `.${classes}`;
                    }
                    const siblings = el.parentNode ?
                        Array.from(el.parentNode.children).filter(c => c.tagName === el.tagName) : [];
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(el) + 1;
                        selector += `:nth-child(${index})`;
                    }
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
            self._logger.warning(f"Failed to extract text elements: {e}")
            return []

    async def _extract_ui_elements(self, page: Page) -> List[Dict[str, Any]]:
        js_code = """
        (function() {
            const uiSelectors = [
                'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="checkbox"]', '[role="radio"]',
                '[role="switch"]', '[role="tab"]', '[role="menuitem"]',
                '.btn', '.button', '[type="submit"]', '[type="button"]'
            ];
            const elements = [];
            const uiElements = document.querySelectorAll(uiSelectors.join(','));
            uiElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                const computed = window.getComputedStyle(el);
                if (computed.visibility === 'hidden' || computed.display === 'none') return;
                elements.push({
                    selector: getUniqueSelector(el),
                    tag: el.tagName.toLowerCase(),
                    type: el.type,
                    role: el.getAttribute('role'),
                    text: el.textContent?.trim() || '',
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    borderColor: computed.borderColor,
                    isInteractive: true,
                    position: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    }
                });
            });
            return elements;
            function getUniqueSelector(el) {
                if (el.id) return `#${el.id}`;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.className) {
                        const classes = Array.from(el.classList).join('.');
                        if (classes) selector += `.${classes}`;
                    }
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
            self._logger.warning(f"Failed to extract UI elements: {e}")
            return []

    async def _analyze_text_contrast(self, element: Dict[str, Any], page: Page) -> Optional[UnifiedIssue]:
        """
        Calculates contrast between text foreground and background utilizing WCAG 2.0 formulas.
        Determines the appropriate threshold dynamically based on font size and weight.
        """
        fg_color = ColorParser.parse(element.get("color", ""))
        bg_color = ColorParser.parse(element.get("backgroundColor", ""))
        if not fg_color or not bg_color: return None
        ratio = ContrastCalculator.calculate_ratio(fg_color, bg_color)
        is_large = element.get("isLargeText", False)
        threshold = self.THRESHOLDS["large_text" if is_large else "body_text"]
        if ratio >= threshold: return None
        confidence_score = ConfidenceCalculator.calculate_confidence("contrast", settings.confidence_weights["contrast"])
        severity = IssueSeverity.SERIOUS
        if ratio < threshold * 0.5: severity = IssueSeverity.CRITICAL
        elif ratio >= threshold * 0.8: severity = IssueSeverity.MODERATE
        wcag_criteria = [WCAGCriteria(id="1.4.3", level="AA", title="Contrast (Minimum)", description="Text has sufficient contrast against background")]
        if is_large: wcag_criteria.append(WCAGCriteria(id="1.4.3", level="AA", title="Large Text Contrast", description="Large text has sufficient contrast (3:1 minimum)"))
        remediation = RemediationSuggestion(description=f"Improve text contrast from {ratio}:1 to at least {threshold}:1", code_before=f"color: {element['color']}; background: {element['backgroundColor']};", code_after=self._suggest_color_fix(fg_color, bg_color, threshold, ratio), estimated_effort="low")
        return UnifiedIssue(
            title=f"Low text contrast: {ratio}:1",
            description=f"Text has insufficient contrast ratio of {ratio}:1. Minimum required is {threshold}:1 for {'large' if is_large else 'normal'} text.",
            issue_type="low_contrast_text",
            severity=severity,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=confidence_score,
            source=IssueSource.CONTRAST,
            wcag_criteria=wcag_criteria,
            location=ElementLocation(selector=element.get("selector", ""), html=f"<{element['tag']}>{element['text']}</{element['tag']}>"),
            actual_value=f"{ratio}:1",
            expected_value=f">={threshold}:1",
            remediation=remediation,
            evidence=EvidenceData(computed_values={"foreground": element["color"], "background": element["backgroundColor"], "ratio": ratio, "font_size": element.get("fontSize"), "is_large_text": is_large}),
            engine_name=self.name,
            engine_version=self.version,
            tags=["contrast", "text", "wcag-1.4.3"]
        )

    async def _analyze_ui_contrast(self, element: Dict[str, Any], page: Page) -> Optional[UnifiedIssue]:
        bg_color = ColorParser.parse(element.get("backgroundColor", ""))
        if not bg_color: return None
        surrounding_bg = await self._get_surrounding_background(page, element.get("selector", ""))
        if not surrounding_bg: return None
        ratio = ContrastCalculator.calculate_ratio(bg_color, surrounding_bg)
        threshold = self.THRESHOLDS["ui_component"]
        if ratio >= threshold: return None
        confidence_score = ConfidenceCalculator.calculate_confidence("contrast", settings.confidence_weights["contrast"])
        return UnifiedIssue(
            title=f"Low UI component contrast: {ratio}:1",
            description=f"Interactive element has insufficient contrast ratio of {ratio}:1 against its background. Minimum required for UI components is {threshold}:1.",
            issue_type="low_contrast_ui",
            severity=IssueSeverity.SERIOUS,
            confidence=ConfidenceLevel.HIGH if confidence_score >= 95 else ConfidenceLevel.MEDIUM,
            confidence_score=confidence_score,
            source=IssueSource.CONTRAST,
            wcag_criteria=[WCAGCriteria(id="1.4.11", level="AA", title="Non-text Contrast", description="UI components have sufficient contrast")],
            location=ElementLocation(selector=element.get("selector", ""), html=f"<{element['tag']}>{element.get('text', '')}</{element['tag']}>"),
            actual_value=f"{ratio}:1",
            expected_value=f">={threshold}:1",
            evidence=EvidenceData(computed_values={"component_background": element["backgroundColor"], "surrounding_background": surrounding_bg.to_rgb_string(), "ratio": ratio}),
            engine_name=self.name,
            engine_version=self.version,
            tags=["contrast", "ui", "wcag-1.4.11"]
        )

    async def _get_surrounding_background(self, page: Page, selector: str) -> Optional[RGBColor]:
        js_code = """
        (selector) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            let parent = el.parentElement;
            while (parent) {
                const bg = window.getComputedStyle(parent).backgroundColor;
                if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                    return bg;
                }
                parent = parent.parentElement;
            }
            return window.getComputedStyle(document.body).backgroundColor;
        }
        """
        try:
            bg_str = await page.evaluate(js_code, selector)
            return ColorParser.parse(bg_str) if bg_str else None
        except Exception as e:
            self._logger.warning(f"Failed to get surrounding background: {e}")
            return None

    async def _analyze_interactive_states(self, page: Page) -> List[UnifiedIssue]:
        """
        Simulates mouse hover events on interactive elements to capture their dynamic 'hover' state styling.
        Verifies that the hover contrast remains WCAG compliant.
        """
        issues = []
        js_code = """
        (function() {
            const elements = document.querySelectorAll('a, button, [role="button"], input, select, textarea');
            const interactive = [];
            elements.forEach(el => {
                const computed = window.getComputedStyle(el);
                interactive.push({
                    selector: getUniqueSelector(el),
                    tag: el.tagName.toLowerCase(),
                    hasHover: true,
                    normalColor: computed.color,
                    normalBg: computed.backgroundColor
                });
            });
            return interactive;
            function getUniqueSelector(el) {
                if (el.id) return `#${el.id}`;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.className) {
                        const classes = Array.from(el.classList).join('.');
                        if (classes) selector += `.${classes}`;
                    }
                    path.unshift(selector);
                    el = el.parentNode;
                }
                return path.join(' > ');
            }
        })();
        """
        try:
            elements = await page.evaluate(js_code)
            for element in elements:
                hover_styles = await self._simulate_hover_state(page, element["selector"])
                if hover_styles:
                    fg_hover = ColorParser.parse(hover_styles.get("color", ""))
                    bg_hover = ColorParser.parse(hover_styles.get("backgroundColor", ""))
                    if fg_hover and bg_hover:
                        ratio = ContrastCalculator.calculate_ratio(fg_hover, bg_hover)
                        if ratio < self.THRESHOLDS["ui_component"]:
                            issues.append(await self._create_hover_contrast_issue(element, hover_styles, ratio))
            return issues
        except Exception as e:
            self._logger.warning(f"Failed to analyze interactive states: {e}")
            return []

    async def _simulate_hover_state(self, page: Page, selector: str) -> Optional[Dict[str, str]]:
        js_code = """
        async (selector) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            const originalTransition = el.style.transition;
            el.style.transition = 'none';
            const hoverEvent = new MouseEvent('mouseover', {view: window, bubbles: true, cancelable: true});
            el.dispatchEvent(hoverEvent);
            await new Promise(resolve => setTimeout(resolve, ${Math.round(settings.hover_simulation_delay * 1000)}));
            const computed = window.getComputedStyle(el);
            const styles = {color: computed.color, backgroundColor: computed.backgroundColor};
            el.style.transition = originalTransition;
            const mouseoutEvent = new MouseEvent('mouseout', {view: window, bubbles: true, cancelable: true});
            el.dispatchEvent(mouseoutEvent);
            return styles;
        }
        """
        try:
            return await page.evaluate(js_code, selector)
        except Exception as e:
            self._logger.warning(f"Failed to simulate hover: {e}")
            return None

    async def _create_hover_contrast_issue(self, element: Dict[str, Any], hover_styles: Dict[str, str], ratio: float) -> UnifiedIssue:
        threshold = self.THRESHOLDS["ui_component"]
        return UnifiedIssue(
            title=f"Insufficient hover state contrast: {ratio}:1",
            description=f"Hover state for {element['tag']} has insufficient contrast ratio of {ratio}:1. Minimum required is {threshold}:1.",
            issue_type="low_contrast_hover",
            severity=IssueSeverity.MODERATE,
            confidence=ConfidenceLevel.MEDIUM,
            confidence_score=85,
            source=IssueSource.CONTRAST,
            wcag_criteria=[WCAGCriteria(id="1.4.11", level="AA", title="Non-text Contrast", description="UI component states have sufficient contrast")],
            location=ElementLocation(selector=element["selector"], html=f"<{element['tag']}>"),
            actual_value=f"{ratio}:1",
            expected_value=f">={threshold}:1",
            evidence=EvidenceData(computed_values={"normal": {"color": element["normalColor"], "background": element["normalBg"]}, "hover": hover_styles, "ratio": ratio}),
            engine_name=self.name,
            engine_version=self.version,
            tags=["contrast", "hover", "interactive"]
        )

    def _suggest_color_fix(self, fg: RGBColor, bg: RGBColor, target_ratio: float, current_ratio: float) -> str:
        ratio_needed = target_ratio / current_ratio
        if ratio_needed > 1.2:
            fg_luminance = fg.to_luminance()
            bg_luminance = bg.to_luminance()
            suggestion = "Make text lighter or background darker" if fg_luminance > bg_luminance else "Make text darker or background lighter"
            suggested_fg = self._adjust_luminance(fg, bg, target_ratio)
            return f"{suggestion}\nSuggested text color: {suggested_fg.to_hex()}\nOr adjust background color to achieve {target_ratio}:1 ratio"
        return f"Adjust colors slightly to achieve {target_ratio}:1 ratio"

    def _adjust_luminance(self, fg: RGBColor, bg: RGBColor, target_ratio: float) -> RGBColor:
        bg_luminance = bg.to_luminance()
        required_luminance = (target_ratio * (bg_luminance + 0.05)) - 0.05
        required_luminance = max(0, min(1, required_luminance))
        current_luminance = fg.to_luminance()
        if required_luminance > current_luminance:
            factor = min(1, required_luminance / current_luminance)
            r = min(255, int(fg.r * (1 + factor) / 2))
            g = min(255, int(fg.g * (1 + factor) / 2))
            b = min(255, int(fg.b * (1 + factor) / 2))
        else:
            factor = required_luminance / current_luminance
            r = int(fg.r * factor)
            g = int(fg.g * factor)
            b = int(fg.b * factor)
        return RGBColor(r=max(0, min(255, r)), g=max(0, min(255, g)), b=max(0, min(255, b)))

    async def validate_config(self) -> bool:
        return True