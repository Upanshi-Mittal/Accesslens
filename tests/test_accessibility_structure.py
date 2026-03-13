from backend.services.tree_extractor import extract_accessibility_tree
from backend.services.engines.accessibility_structure_engine import A11yStructureEngine


def test_heading_structure():
    tree = extract_accessibility_tree("https://example.com")
    engine = A11yStructureEngine()
    issues = engine.analyze(tree)

    print(issues)
    assert isinstance(issues, list)