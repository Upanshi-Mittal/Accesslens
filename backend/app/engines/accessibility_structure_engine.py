from ..utils.tree_traversal import traverse


class A11yStructureEngine:
    def analyze(self, tree: dict) -> list:
        issues = []
        headings = []

        # Collect all heading nodes
        def collect_headings(node):
            if node.get("role") == "heading":
                headings.append(node)

        traverse(tree, collect_headings)

        # If no headings → optional warning
        if not headings:
            issues.append({
                "type": "structure",
                "code": "NO_HEADINGS",
                "message": "No headings found on page.",
                "severity": "medium"
            })
            return issues

        # Count H1
        h1_count = sum(1 for h in headings if h.get("level") == 1)

        if h1_count == 0:
            issues.append({
                "type": "structure",
                "code": "MISSING_H1",
                "message": "Page has no level 1 heading.",
                "severity": "high"
            })

        if h1_count > 1:
            issues.append({
                "type": "structure",
                "code": "MULTIPLE_H1",
                "message": f"Page has {h1_count} level 1 headings.",
                "severity": "medium"
            })

        # Check heading order
        previous_level = None

        for heading in headings:
            level = heading.get("level")

            if previous_level and level:
                if level > previous_level + 1:
                    issues.append({
                        "type": "structure",
                        "code": "HEADING_LEVEL_SKIP",
                        "message": f"Heading level jumps from h{previous_level} to h{level}.",
                        "severity": "medium"
                    })

            previous_level = level

        return issues