import pytest
from app.services.tree_extractor import extract_accessibility_tree
from app.engines.accessibility_structure_engine import A11yStructureEngine


@pytest.mark.asyncio
async def test_heading_structure():
    tree = await extract_accessibility_tree("https://example.com")
    engine = A11yStructureEngine()
    issues = engine.analyze(tree)

    print(issues)
    assert isinstance(issues, list)