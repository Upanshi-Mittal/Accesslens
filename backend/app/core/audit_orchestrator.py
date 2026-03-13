
from typing import List, Dict, Any, Optional
import asyncio
import logging
import time
from datetime import datetime

from ..models.schemas import (
    AuditRequest, AuditReport, UnifiedIssue, AuditSummary,
    IssueSeverity, IssueSource
)
from ..engines.registry import EngineRegistry
from .page_controller import PageController
from .accessibility_tree import AccessibilityTreeExtractor
from .browser_manager import browser_manager
from ..core.scoring import ConfidenceCalculator

class AuditOrchestrator:


    def __init__(self, engine_registry: EngineRegistry):
        self.engine_registry = engine_registry
        self.page_controller = PageController()
        self.tree_extractor = AccessibilityTreeExtractor()
        self._logger = logging.getLogger(__name__)

    async def run_audit(self, request: AuditRequest) -> AuditReport:

        start_time = time.time()

        self._logger.info(f"Starting audit for {request.url}")


        page_data = await self._setup_page(request)

        if "error" in page_data:
            return self._create_error_report(request, page_data["error"])


        engine_tasks = []
        for engine_name in request.engines:
            engine = self.engine_registry.get(engine_name)
            if engine:
                engine_tasks.append(
                    self._run_engine_safe(engine, page_data, request)
                )
            else:
                self._logger.warning(f"Engine {engine_name} not found")


        engine_results = await asyncio.gather(*engine_tasks, return_exceptions=True)


        all_issues = []
        for result in engine_results:
            if isinstance(result, Exception):
                self._logger.error(f"Engine failed: {result}")
            elif isinstance(result, list):
                all_issues.extend(result)


        if request.enable_ai:
            ai_issues = await self._run_ai_analysis(page_data, request)
            all_issues.extend(ai_issues)


        summary = self._generate_summary(all_issues, start_time)


        report = AuditReport(
            request=request,
            summary=summary,
            issues=all_issues,
            accessibility_tree=page_data.get("accessibility_tree"),
            metadata={
                "duration_seconds": round(time.time() - start_time, 2),
                "engines_run": request.engines
            }
        )

        self._logger.info(f"Audit complete: {summary.total_issues} issues found")

        return report

    async def _setup_page(self, request: AuditRequest) -> Dict[str, Any]:

        try:

            page_data = await self.page_controller.navigate_and_extract(
                request.url,
                {
                    "viewport": request.viewport,
                    "wait_for_network_idle": request.wait_for_network_idle,
                    "timeout": 30000
                }
            )


            if self.page_controller._current_page:
                page_data["page"] = self.page_controller._current_page

            return page_data

        except Exception as e:
            self._logger.error(f"Page setup failed: {e}")
            return {"error": str(e)}
        finally:

            pass

    async def _run_engine_safe(
        self,
        engine,
        page_data: Dict[str, Any],
        request: AuditRequest
    ) -> List[UnifiedIssue]:

        try:
            self._logger.debug(f"Running engine: {engine.name}")
            issues = await engine.analyze(page_data, request.dict())
            self._logger.debug(f"Engine {engine.name} found {len(issues)} issues")
            return issues
        except Exception as e:
            self._logger.error(f"Engine {engine.name} failed: {e}", exc_info=True)
            return []

    async def _run_ai_analysis(
        self,
        page_data: Dict[str, Any],
        request: AuditRequest
    ) -> List[UnifiedIssue]:



        return []

    def _generate_summary(
        self,
        issues: List[UnifiedIssue],
        start_time: float
    ) -> AuditSummary:

        by_severity = {severity: 0 for severity in IssueSeverity}
        by_source = {source: 0 for source in IssueSource}
        by_wcag_level = {"A": 0, "AA": 0, "AAA": 0}

        total_confidence = 0

        for issue in issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_source[issue.source] = by_source.get(issue.source, 0) + 1
            total_confidence += issue.confidence_score


            for wcag in issue.wcag_criteria:
                by_wcag_level[wcag.level] = by_wcag_level.get(wcag.level, 0) + 1



        if issues:
            severity_weights = {
                IssueSeverity.CRITICAL: 10,
                IssueSeverity.SERIOUS: 5,
                IssueSeverity.MODERATE: 2,
                IssueSeverity.MINOR: 1
            }

            total_weight = sum(
                severity_weights.get(issue.severity, 1)
                for issue in issues
            )


            max_possible = len(issues) * 10
            score = max(0, 100 - (total_weight / max_possible * 100))
        else:
            score = 100

        avg_confidence = total_confidence / len(issues) if issues else 100

        return AuditSummary(
            total_issues=len(issues),
            by_severity=by_severity,
            by_source=by_source,
            by_wcag_level=by_wcag_level,
            score=round(score, 2),
            confidence_avg=round(avg_confidence, 2)
        )

    def _create_error_report(self, request: AuditRequest, error: str) -> AuditReport:

        return AuditReport(
            request=request,
            summary=AuditSummary(
                total_issues=0,
                by_severity={},
                by_source={},
                by_wcag_level={},
                score=0,
                confidence_avg=0
            ),
            issues=[],
            metadata={"error": error}
        )