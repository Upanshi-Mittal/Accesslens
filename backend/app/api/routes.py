
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import List, Dict, Any, Optional
import asyncio
import logging
import uuid
from datetime import datetime

from ..models.schemas import AuditRequest, AuditReport, UnifiedIssue
from ..core.page_controller import PageController
from ..core.audit_orchestrator import AuditOrchestrator
from ..core.browser_manager import browser_manager

router = APIRouter()
logger = logging.getLogger(__name__)


audit_store: Dict[str, AuditReport] = {}

@router.post("/audit", response_model=Dict[str, str])
async def start_audit(
    request: AuditRequest,
    background_tasks: BackgroundTasks,
    req: Request
):

    audit_id = str(uuid.uuid4())

    logger.info(f"Starting audit {audit_id} for URL: {request.url}")


    orchestrator = AuditOrchestrator(
        engine_registry=req.app.state.engine_registry
    )


    background_tasks.add_task(
        run_audit_background,
        audit_id,
        request,
        orchestrator
    )

    return {
        "audit_id": audit_id,
        "status": "started",
        "url": request.url
    }

@router.get("/audit/{audit_id}", response_model=AuditReport)
async def get_audit_results(audit_id: str):

    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit not found")

    return audit_store[audit_id]

@router.get("/audit/{audit_id}/status")
async def get_audit_status(audit_id: str):

    if audit_id not in audit_store:

        return {"audit_id": audit_id, "status": "in_progress"}

    report = audit_store[audit_id]
    return {
        "audit_id": audit_id,
        "status": "completed",
        "summary": report.summary
    }

@router.get("/engines")
async def list_engines(request: Request):

    engines = request.app.state.engine_registry.get_all()
    return [
        {
            "name": engine.name,
            "version": engine.version,
            "capabilities": engine.capabilities
        }
        for engine in engines
    ]

@router.post("/audit/{audit_id}/cancel")
async def cancel_audit(audit_id: str):


    return {"status": "cancelled", "audit_id": audit_id}

async def run_audit_background(
    audit_id: str,
    request: AuditRequest,
    orchestrator: 'AuditOrchestrator'
):

    try:
        logger.info(f"Running audit {audit_id} in background")


        report = await orchestrator.run_audit(request)


        audit_store[audit_id] = report

        logger.info(f"Audit {audit_id} completed with {report.summary.total_issues} issues")

    except Exception as e:
        logger.error(f"Audit {audit_id} failed: {e}", exc_info=True)

        audit_store[audit_id] = AuditReport(
            request=request,
            summary={},
            issues=[],
            metadata={"error": str(e)}
        )