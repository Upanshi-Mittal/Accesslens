


import pytest


pytest.importorskip("torch")

import asyncio
from unittest.mock import Mock, patch
from playwright.async_api import async_playwright
from app.engines.ai_engine import AIEngine
from app.ai.ai_service import AIService, AIConfig
from app.models.schemas import UnifiedIssue, IssueSeverity

@pytest.mark.asyncio
async def test_ai_service_initialization():


    config = AIConfig(
        llava_endpoint="http://localhost:8001",
        mistral_endpoint="http://localhost:8002",
        use_local=True,
        confidence_threshold=0.7
    )

    service = AIService(config)
    assert service.config.confidence_threshold == 0.7
    assert service.config.use_local is True

@pytest.mark.asyncio
async def test_vision_prompt_building():


    engine = AIEngine()

    accessibility_tree = {
        "statistics": {
            "total_elements": 100,
            "images": {"total": 5}
        },
        "structure": {
            "focusable_elements": [1, 2, 3]
        }
    }

    prompt = engine._build_vision_prompt(accessibility_tree)

    assert "accessibility expert" in prompt
    assert "100" in prompt
    assert "5" in prompt

@pytest.mark.asyncio
async def test_fix_context_building():


    engine = AIEngine()


    issue = UnifiedIssue(
        title="Missing alt text",
        description="Image has no alt attribute",
        issue_type="missing_alt",
        severity=IssueSeverity.SERIOUS,
        confidence_score=95,
        wcag_criteria=[]
    )

    context = engine._build_fix_context(issue, {})

    assert "Missing alt text" in context
    assert "HTML/ARIA fix" in context

@pytest.mark.asyncio
async def test_vision_results_parsing():


    engine = AIEngine()

    mock_results = {
        "findings": [
            {
                "issue_type": "visual_clutter",
                "description": "Page appears cluttered",
                "severity": "moderate",
                "location": "main content",
                "confidence": 0.85,
                "wcag_ref": "1.4.8",
                "suggestion": "Add more whitespace"
            }
        ]
    }

    issues = engine._parse_vision_results(mock_results, {})

    assert len(issues) == 1
    issue = issues[0]
    assert "visual_clutter" in issue.issue_type
    assert issue.severity.value == "moderate"
    assert issue.confidence_score == 85

@pytest.mark.asyncio
async def test_ai_engine_with_mock_page():


    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()


        html = """
        <html>
        <body>
            <h1>AI Test Page</h1>
            <p>Test content for AI vision analysis.</p>
            <img src="test_img.jpg" alt="A test image">
        </body>
        </html>
        """

        await page.set_content(html)


        screenshot = await page.screenshot(type="jpeg")
        import base64
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')


        with patch.object(AIEngine, '_run_vision_analysis', return_value=[]):
            engine = AIEngine()


            issues = await engine.analyze(
                {
                    "page": page,
                    "screenshot": screenshot_b64,
                    "accessibility_tree": {
                        "statistics": {"total_elements": 10},
                        "structure": {}
                    }
                },
                {}
            )


            assert isinstance(issues, list)

        await browser.close()