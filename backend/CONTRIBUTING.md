# Contributing to AccessLens

Thank you for contributing to our deterministic and AI-powered accessibility auditor!

## Adding a New Accessibility Engine
Our architecture uses an interface-based Engine Registry.

### Step 1: Subclass `BaseAccessibilityEngine`
Create a new file in `app/engines/new_engine.py`

```python
from .base import BaseAccessibilityEngine

class CustomEngine(BaseAccessibilityEngine):
    def __init__(self):
        super().__init__("custom_engine", "1.0.0")

    async def analyze(self, page_data, request):
        return []

    async def validate_config(self):
        return True
```

### Step 2: Register in `dependencies.py`
Inside `app/core/dependencies.py` add:
```python
registry.register(CustomEngine())
```

### Step 3: Write Tests
Create a dedicated unit test stringing up Mock Page outputs inside `tests/` asserting the correct deterministic `UnifiedIssue` serialization.

### Running Pytest
Make sure all existing suites pass locally before submitting MRs. We run 40/40 strict integration tests utilizing asynchronous contexts.

```bash
pytest backend/tests/
```
