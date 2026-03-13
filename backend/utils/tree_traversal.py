def traverse(node, callback):
    if not node:
        return

    callback(node)

    for child in node.get("children", []):
        traverse(child, callback)