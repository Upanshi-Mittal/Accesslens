from app.models.schemas import AuditReport, AuditRequest, AuditSummary

def test_in_memory_audit_store():
    """Verify in-memory dictionary behavior for rapid updates."""
    from app.api.routes import audit_store
    
    test_id = "test-1234"
    request = AuditRequest(url="https://test.com")
    summary = AuditSummary(
        total_issues=0,
        by_severity={},
        by_source={},
        by_wcag_level={},
        score=100.0,
        confidence_avg=100.0
    )
    
    report = AuditReport(
        id=test_id,
        request=request,
        summary=summary,
        issues=[]
    )
    audit_store[test_id] = report
    
    assert audit_store[test_id].id == test_id
    assert audit_store[test_id].request.url == "https://test.com"
    
    # Update score in summary
    audit_store[test_id].summary.score = 50.0
    assert audit_store[test_id].summary.score == 50.0
    
    # Clean up
    del audit_store[test_id]
