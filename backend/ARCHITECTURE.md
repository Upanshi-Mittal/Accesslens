# AccessLens Backend Architecture

The AccessLens backend handles the deterministic headless execution of a web accessibility evaluation pipeline. This document outlines the system modules.

## High Level Overview

1. **API Layer (`app/api/`)**: Built on FastAPI. Handles rate limiting (SlowAPI), inputs parsing (Pydantic), synchronous routing, and metrics exposure (Prometheus).
2. **Core Controllers (`app/core/`)**:
   - `page_controller`: Interfaces directly with Playwright to extract DOM Snapshots and Accessibility Trees.
   - `browser_manager`: Maintains an active asynchronous pool of Playwright chromium contexts to optimize startup costs per request.
   - `audit_orchestrator`: Manages concurrency and routes DOM traces through the requested Engines.
3. **Engines (`app/engines/`)**: Pluggable evaluation interfaces that adhere to `BaseAccessibilityEngine`.
   - `WCAGEngine`: Wraps axe-core into python objects.
   - `ContrastEngine`: Advanced RGB/Hex heuristic logic using DOM layout computations.
   - `StructuralEngine`: Verifies non-visual landmarks and header structures.
   - `AIEngine`: Multi-modal engine routing to localized endpoints.
4. **Data Layer (`app/models/`)**: Unified pydantic definitions serialized safely out to PostgreSQL or `in_memory` storage. 

## Data Flow Diagram
\`\`\`mermaid
sequenceDiagram
    Client->>+API: POST /api/v1/audit
    API->>Orchestrator: run_audit(url)
    Orchestrator->>BrowserPool: navigate_and_extract()
    BrowserPool-->>Orchestrator: [DOM Snapshot, A11y Tree]
    par Engine Execution
        Orchestrator->>WCAGEngine: analyze()
        Orchestrator->>StructuralEngine: analyze()
        Orchestrator->>ContrastEngine: analyze()
    end
    Orchestrator->>ReportStorage: save_report(issues)
    Orchestrator-->>-API: AuditReport
    API-->>-Client: JSON Report
\`\`\`
